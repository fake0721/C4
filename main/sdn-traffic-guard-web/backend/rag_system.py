"""
RAG系统 - 网络安全知识库检索增强生成
支持文档加载、向量化、相似度检索、LLM增强生成
"""

import os
import json
import requests
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    from langchain_community.document_loaders import TextLoader, DirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain未安装，RAG功能受限")


class NetworkSecurityRAG:
    """网络安全知识库RAG系统"""
    
    def __init__(self, 
                 ollama_url: str = "http://192.168.126.1:11435/api/generate",
                 model: str = "mistral",
                 persist_dir: str = "./chroma_db"):
        """
        初始化RAG系统
        
        Args:
            ollama_url: Ollama服务地址
            model: 使用的模型名称
            persist_dir: 向量数据库持久化目录
        """
        self.ollama_url = ollama_url
        self.model = model
        self.persist_dir = persist_dir
        
        # 初始化向量模型和数据库
        if LANGCHAIN_AVAILABLE:
            try:
                import os
                # 尝试优先使用阿里云DashScope DashScopeEmbeddings
                api_key = os.getenv("DASHSCOPE_API_KEY", "")
                if api_key:
                    from langchain_community.embeddings import DashScopeEmbeddings
                    print(f"[🔄] 初始化 DashScopeEmbeddings...")
                    self.embeddings = DashScopeEmbeddings(
                        model=os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"),
                        dashscope_api_key=api_key
                    )
                else:
                    print(f"[🔄] 未找到 DASHSCOPE_API_KEY，降级使用 HuggingFaceEmbeddings...")
                    # 临时强制走国内镜像以防卡死
                    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                    self.embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                        model_kwargs={'device': 'cpu'},  # 使用CPU避免显存占用过大
                        encode_kwargs={'normalize_embeddings': True}
                    )
                
                print(f"[✅] Embeddings初始化成功")
                
                print(f"[🔄] 初始化Chroma向量数据库...")
                self.vectorstore = Chroma(
                    collection_name="network_security",
                    embedding_function=self.embeddings,
                    persist_directory=persist_dir
                )
                print("✅ RAG系统初始化成功")
            except ImportError as e:
                print(f"❌ 缺少依赖: {e}")
                print(f"[💡] 请运行: pip install sentence-transformers torch")
                self.embeddings = None
                self.vectorstore = None
            except Exception as e:
                print(f"❌ RAG初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self.embeddings = None
                self.vectorstore = None
        else:
            print("⚠️ LangChain不可用，RAG功能受限")
            self.embeddings = None
            self.vectorstore = None
    
    def build_knowledge_base(self, docs_dir: str) -> int:
        """
        构建知识库
        
        Args:
            docs_dir: 文档目录路径
            
        Returns:
            添加的文档块数量
        """
        if not LANGCHAIN_AVAILABLE or not self.vectorstore:
            print("❌ LangChain未可用，无法构建知识库")
            return 0
        
        try:
            # 加载文档
            loader = DirectoryLoader(
                docs_dir,
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            if not documents:
                print(f"⚠️ 在 {docs_dir} 中未找到文档")
                return 0
            
            # 分块
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                separators=["\n\n", "\n", "。", "，", " ", ""]
            )
            chunks = splitter.split_documents(documents)
            
            # 存储到向量数据库
            self.vectorstore.add_documents(chunks)
            self.vectorstore.persist()
            
            print(f"✅ 知识库构建完成，共 {len(chunks)} 个文档块")
            return len(chunks)
        
        except Exception as e:
            print(f"❌ 知识库构建失败: {e}")
            return 0
    
    def add_documents(self, chunks: List[Dict[str, str]]) -> int:
        """
        动态添加文档块到知识库
        
        Args:
            chunks: 文档块列表，每个块是一个字典，包含'content'和'source'等字段
            
        Returns:
            添加的文档块数量
        """
        if not LANGCHAIN_AVAILABLE or not self.vectorstore:
            print("❌ LangChain未可用，无法添加文档")
            return 0
        
        try:
            print(f"[📝] 开始添加 {len(chunks)} 个文档块到知识库")
            
            # 将字典格式的chunks转换为LangChain Document格式
            from langchain_core.documents import Document
            
            documents = []
            for i, chunk in enumerate(chunks):
                content = chunk.get('content', '')
                if not content:
                    print(f"[⚠️] 块 {i+1} 的内容为空，跳过")
                    continue
                    
                doc = Document(
                    page_content=content,
                    metadata={
                        'source': chunk.get('source', 'unknown'),
                        'start_pos': chunk.get('start_pos', 0),
                        'end_pos': chunk.get('end_pos', 0)
                    }
                )
                documents.append(doc)
            
            if not documents:
                print("❌ 没有有效的文档块可以添加")
                return 0
            
            print(f"[🔄] 向量化 {len(documents)} 个文档块...")
            
            # 批量添加文档（分批处理防止超时）
            batch_size = 5
            added_count = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                print(f"[📦] 处理批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} ({len(batch)} 个块)")
                
                try:
                    self.vectorstore.add_documents(batch)
                    added_count += len(batch)
                    print(f"[✅] 批次添加成功，已添加 {added_count}/{len(documents)}")
                except Exception as e:
                    print(f"[⚠️] 批次添加失败: {e}，继续处理下一批")
                    continue
            
            print(f"[💾] 持久化向量数据库...")
            self.vectorstore.persist()
            
            print(f"✅ 已成功添加 {added_count} 个文档块到知识库")
            return added_count
        
        except Exception as e:
            import traceback
            print(f"❌ 添加文档失败: {e}")
            print(f"[DEBUG] 错误详情:")
            traceback.print_exc()
            return 0
    
    def retrieve_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回的最相关文档数
            
        Returns:
            相关知识列表
        """
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search(query, k=top_k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"❌ 知识库检索失败: {e}")
            return []

    # 兼容 agent_routes.py 中异步调用的名称
    async def search_similar_documents(self, query: str, k: int = 3) -> List[str]:
        """
        异步检索相关文档 (兼容接口)
        """
        return self.retrieve_knowledge(query, top_k=k)
    
    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        """
        调用Ollama LLM
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            
        Returns:
            LLM生成的文本
        """
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            print(f"❌ Ollama调用失败: {e}")
            return ""
    
    def generate_with_rag(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        使用RAG生成回答
        
        Args:
            query: 查询文本
            top_k: 检索的文档数
            
        Returns:
            包含回答和知识源的字典
        """
        # 1. 检索相关知识
        knowledge_list = self.retrieve_knowledge(query, top_k)
        
        # 2. 构建增强Prompt
        context = "\n".join([f"- {k}" for k in knowledge_list])
        
        prompt = f"""基于以下网络安全知识库信息，回答问题。

【知识库信息】
{context if context else "（暂无相关知识）"}

【问题】
{query}

【回答】"""
        
        # 3. 调用LLM
        response = self._call_ollama(prompt)
        
        return {
            "query": query,
            "answer": response,
            "knowledge_sources": knowledge_list,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_attack_with_rag(self, attack_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用RAG分析攻击
        
        Args:
            attack_info: 攻击信息字典
                - type: 攻击类型
                - src_ip: 源IP
                - features: 攻击特征
                
        Returns:
            分析结果
        """
        query = f"""
攻击类型: {attack_info.get('type', '未知')}
源IP: {attack_info.get('src_ip', '未知')}
特征: {attack_info.get('features', '无')}

请基于知识库分析这个攻击的：
1. 风险等级（低/中/高/严重）
2. 可能的防御策略
3. 建议的处置方式
"""
        
        result = self.generate_with_rag(query)
        
        return {
            "attack_type": attack_info.get('type'),
            "src_ip": attack_info.get('src_ip'),
            "analysis": result['answer'],
            "knowledge_sources": result['knowledge_sources'],
            "timestamp": datetime.now().isoformat()
        }
    
    def search_knowledge(self, keyword: str, top_k: int = 5) -> List[Dict[str, str]]:
        """
        搜索知识库
        
        Args:
            keyword: 搜索关键词
            top_k: 返回的结果数
            
        Returns:
            搜索结果列表
        """
        knowledge_list = self.retrieve_knowledge(keyword, top_k)
        return [
            {"content": k, "relevance": i + 1}
            for i, k in enumerate(knowledge_list)
        ]


# 初始化全局RAG实例
_rag_instance = None

def get_rag_instance() -> NetworkSecurityRAG:
    """获取RAG实例（单例）"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = NetworkSecurityRAG()
    return _rag_instance


# 示例：创建初始知识库文档
def create_sample_knowledge_base():
    """创建示例知识库"""
    docs_dir = "docs/knowledge_base"
    os.makedirs(docs_dir, exist_ok=True)
    
    # 攻击特征文档
    attack_patterns = """
# 网络攻击特征库

## DDoS攻击
DDoS（分布式拒绝服务）攻击是指攻击者利用多个受控的计算机同时向目标发送大量请求，导致目标服务器无法正常服务。

特征：
- 源IP多样化，来自不同地域
- 流量突增，超过正常流量的10倍以上
- 目标端口集中，通常针对特定服务端口
- 包大小相似，表明来自同一类型的僵尸网络

防御策略：
1. 限速处理：将异常流量限制在可接受范围内
2. 黑名单：对已知的攻击源IP进行永久封禁
3. 流量清洗：使用CDN或专业清洗服务
4. 速率限制：基于源IP的限速规则

## Port Scan（端口扫描）
端口扫描是攻击者探测目标主机开放端口的行为，通常是发动进一步攻击的前奏。

特征：
- 单个源IP向多个目标端口发送连接请求
- 端口号跨度大，覆盖常见服务端口
- 连接建立失败率高
- 扫描速率快，短时间内大量连接尝试

防御策略：
1. 限速处理：降低可疑IP的带宽
2. 端口隐藏：关闭不必要的服务端口
3. 防火墙规则：限制特定IP的访问
4. 入侵检测：监控异常连接模式

## ARP欺骗
ARP欺骗是指攻击者发送虚假的ARP应答，将自己的MAC地址与目标IP关联，从而拦截网络流量。

特征：
- 单个IP对应多个MAC地址
- ARP应答频率异常高
- MAC地址频繁变化
- 网络连接中断或延迟增加

防御策略：
1. ARP绑定：将重要设备的IP-MAC绑定固定
2. 静态ARP表：在交换机上配置静态ARP条目
3. 动态ARP检测：启用DAI功能
4. 网络隔离：使用VLAN隔离不同的网络段

## 僵尸网络（Botnet）
僵尸网络是由大量被恶意软件感染的计算机组成的网络，可被攻击者远程控制。

特征：
- 多个源IP向同一目标发送相似流量
- 流量模式规律，表明受到统一控制
- 目标端口多样化
- 通信协议固定，通常使用特定的C&C协议

防御策略：
1. 端点防护：部署反病毒软件和EDR解决方案
2. 网络隔离：隔离被感染的主机
3. 流量分析：监控异常的出站连接
4. 威胁情报：使用已知的C&C服务器IP黑名单

## SYN Flood
SYN Flood是一种利用TCP三次握手漏洞的攻击，攻击者发送大量SYN包但不完成握手。

特征：
- 大量SYN包，SYN包占比超过80%
- 源IP多样化或集中
- 目标端口固定（通常是常见服务端口）
- 连接建立失败率高

防御策略：
1. SYN Cookie：启用TCP SYN Cookie保护
2. 连接限制：限制单个IP的并发连接数
3. 限速处理：对异常流量进行限速
4. 防火墙规则：在防火墙层面进行过滤
"""
    
    # 防御策略文档
    defense_strategies = """
# 网络安全防御策略

## 限速策略
限速是一种有效的流量管理手段，可以在不完全阻断流量的情况下缓解攻击。

### 限速等级
- 低速（256Kbps）：用于严重攻击，仅允许基本通信
- 中速（1024Kbps）：用于中等攻击，保留部分服务可用性
- 高速（2048Kbps）：用于轻微异常，基本保持正常服务

### 限速时长
- 短期限速（5分钟）：用于临时异常
- 中期限速（30分钟）：用于可疑行为
- 长期限速（24小时）：用于重复攻击

## 黑名单策略
黑名单是最严厉的防御措施，直接丢弃来自黑名单IP的所有流量。

### 何时使用黑名单
1. 确认的恶意IP
2. 多次重复攻击的IP
3. 已知的僵尸网络IP
4. 管理员手动确认的攻击源

### 黑名单管理
- 定期审查：每周检查黑名单有效性
- 误报处理：及时移除误加的IP
- 备份维护：定期备份黑名单数据

## 白名单策略
白名单用于保护合法的流量，白名单中的IP永不限速或阻断。

### 白名单对象
- 公司内部IP段
- 重要合作伙伴IP
- 关键服务提供商IP
- 管理员IP

## 异常隔离
对于无法确定的异常，应该进行隔离而不是直接阻断。

### 隔离措施
1. 限速处理：降低异常IP的带宽
2. 流量镜像：复制流量用于深度分析
3. 告警通知：立即通知安全团队
4. 日志记录：详细记录异常特征

## 应急响应流程
1. 检测异常 → 2. 初步分析 → 3. 隔离处理 → 4. 深度调查 → 5. 处置决策 → 6. 恢复验证
"""
    
    # 历史案例文档
    historical_cases = """
# 历史攻击案例分析

## 案例1：UDP Flood攻击
### 背景
2024年1月，某公司遭受大规模UDP Flood攻击，导致服务中断。

### 攻击特征
- 源IP：来自全球50+个国家
- 流量大小：单个包512字节
- 目标端口：53（DNS）和123（NTP）
- 流量速率：突增到正常流量的50倍

### 防御措施
1. 立即启用限速：将异常IP限制在256Kbps
2. 启用DNS防护：在防火墙层面过滤异常DNS查询
3. 使用CDN清洗：将流量转发到CDN进行清洗
4. 加入黑名单：对重复攻击的IP进行永久封禁

### 结果
- 恢复时间：30分钟
- 损失：约50万元
- 改进：部署了更强大的DDoS防护系统

## 案例2：Port Scan检测
### 背景
某公司的入侵检测系统发现异常的端口扫描活动。

### 扫描特征
- 源IP：192.168.1.100
- 扫描范围：1-65535全端口
- 扫描速率：每秒100个端口
- 持续时间：2小时

### 分析结果
- 初步判断：内网设备被入侵
- 风险等级：高

### 处置措施
1. 立即隔离该设备
2. 对设备进行深度检查
3. 发现恶意软件：Mirai僵尸网络
4. 清除恶意软件并加固系统

### 经验教训
- 需要更快的异常检测机制
- 内网隔离策略需要加强
- 终端安全防护需要升级

## 案例3：误报处理
### 背景
某公司的自动防御系统误判了合法的备份流量。

### 误报原因
- 备份系统进行大文件传输
- 流量特征与DDoS相似
- 自动防御系统误判为攻击

### 影响
- 备份中断
- 数据恢复延迟
- 业务受到影响

### 改进措施
1. 将备份系统IP加入白名单
2. 优化异常检测算法
3. 建立人工审核机制
4. 定期测试防御系统

### 经验教训
- 白名单管理的重要性
- 需要人工审核机制
- 防御系统需要持续优化
"""
    
    # 写入文件
    with open(os.path.join(docs_dir, "attack_patterns.txt"), "w", encoding="utf-8") as f:
        f.write(attack_patterns)
    
    with open(os.path.join(docs_dir, "defense_strategies.txt"), "w", encoding="utf-8") as f:
        f.write(defense_strategies)
    
    with open(os.path.join(docs_dir, "historical_cases.txt"), "w", encoding="utf-8") as f:
        f.write(historical_cases)
    
    print(f"✅ 示例知识库已创建在 {docs_dir}")


if __name__ == "__main__":
    # 创建示例知识库
    create_sample_knowledge_base()
    
    # 初始化RAG
    rag = get_rag_instance()
    
    # 构建知识库
    rag.build_knowledge_base("docs/knowledge_base")
    
    # 测试查询
    result = rag.generate_with_rag("什么是DDoS攻击？如何防御？")
    print("\n【查询结果】")
    print(result['answer'])
    print("\n【知识源】")
    for source in result['knowledge_sources']:
        print(f"- {source[:100]}...")
