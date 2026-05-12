"""
统一的AI服务 - 集成Kimi大模型和DashScope嵌入模型
提供对话、文件分析、RAG功能
"""

import os
import json
import requests
import httpx
import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# 导入速率限制配置
from config.api_config import kimi_rate_limiter
# 导入错误处理器
from utils.error_handler import error_handler

load_dotenv()

class UnifiedAIService:
    """统一的AI服务类"""
    
    def __init__(self):
        self.kimi_api_key = os.getenv("KIMI_API_KEY", "")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.kimi_api_url = os.getenv("KIMI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
        self.deepseek_api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
        
        # 初始化嵌入模型
        if self.dashscope_api_key:
            self.embeddings = DashScopeEmbeddings(
                model=os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4"),
                dashscope_api_key=self.dashscope_api_key
            )
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
            )
            self.vector_store = None
        else:
            self.embeddings = None
            self.vector_store = None
    
    async def chat_with_deepseek(self, message: str, context: Optional[Dict[str, Any]] = None, stream: bool = False) -> Dict[str, Any]:
        """使用DeepSeek大模型进行对话"""
        try:
            if not self.deepseek_api_key:
                return {
                    "response": "DeepSeek API未配置，请联系管理员设置DEEPSEEK_API_KEY环境变量",
                    "tools_used": ["deepseek"],
                    "timestamp": datetime.now().isoformat(),
                    "stream": False
                }
            
            # 检查速率限制
            estimated_tokens = len(message) // 4  # 粗略估计token数量
            
            # 重试机制
            max_retries = 3
            for retry_count in range(max_retries):
                if not kimi_rate_limiter.can_make_request(estimated_tokens):
                    wait_time = kimi_rate_limiter.get_wait_time()
                    if retry_count == max_retries - 1:
                        error_info = error_handler.handle_api_error(429)
                        return error_handler.format_error_response({
                            "tools_used": ["deepseek"],
                            "model": "deepseek-chat",
                            "stream": False
                        }, error_info)
                    await asyncio.sleep(wait_time)
                    continue
                
                # 记录请求
                kimi_rate_limiter.record_request(estimated_tokens)
                
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                }
                
                # 构建系统提示词
                system_prompt = """你是一个专业的网络管理AI助手，具备以下能力：
1. 网络设备配置分析
2. 网络安全诊断
3. 性能优化建议
4. 故障排查指导
5. 数据分析与可视化

请用中文回答用户的问题，提供准确、专业的建议。"""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                # 添加上下文信息
                if context:
                    context_str = json.dumps(context, ensure_ascii=False, indent=2)
                    messages[1]["content"] += f"\n\n相关上下文：\n{context_str}"
                
                data = {
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": stream
                }
            
            if stream:
                # 流式响应 - 返回生成器
                return {
                    "stream": True,
                    "generator": self._generate_deepseek_stream_response(data, headers)
                }
            else:
                # 非流式响应
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.deepseek_api_url,
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        error_info = error_handler.handle_api_error(response.status_code)
                        return error_handler.format_error_response({
                            "tools_used": ["deepseek"],
                            "model": "deepseek-chat",
                            "stream": False
                        }, error_info)
                
                    response.raise_for_status()
                
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，我无法处理您的请求")
                
                return {
                    "response": ai_response,
                    "tools_used": ["deepseek"],
                    "model": "deepseek-chat",
                    "timestamp": datetime.now().isoformat(),
                    "stream": False
                }
            
        except Exception as e:
            return {
                "response": f"AI服务暂时不可用：{str(e)}",
                "tools_used": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "stream": False
            }

    async def chat_with_kimi(self, message: str, context: Optional[Dict[str, Any]] = None, stream: bool = False) -> Dict[str, Any]:
        """使用Kimi大模型进行对话"""
        try:
            if not self.kimi_api_key:
                return {
                    "response": "Kimi API未配置，请联系管理员设置KIMI_API_KEY环境变量",
                    "tools_used": ["kimi"],
                    "timestamp": datetime.now().isoformat(),
                    "stream": False
                }
            
            # 检查速率限制
            estimated_tokens = len(message) // 4  # 粗略估计token数量
            
            # 重试机制
            max_retries = 3
            for retry_count in range(max_retries):
                if not kimi_rate_limiter.can_make_request(estimated_tokens):
                    wait_time = kimi_rate_limiter.get_wait_time()
                    if retry_count == max_retries - 1:
                        error_info = error_handler.handle_api_error(429)
                        return error_handler.format_error_response({
                            "tools_used": ["kimi"],
                            "model": "moonshot-v1-8k",
                            "stream": False
                        }, error_info)
                    await asyncio.sleep(wait_time)
                    continue
                
                # 记录请求
                kimi_rate_limiter.record_request(estimated_tokens)
                
                headers = {
                    "Authorization": f"Bearer {self.kimi_api_key}",
                    "Content-Type": "application/json"
                }
                
                # 构建系统提示词
                system_prompt = """你是一个专业的网络管理AI助手，具备以下能力：
1. 网络设备配置分析
2. 网络安全诊断
3. 性能优化建议
4. 故障排查指导
5. 数据分析与可视化

请用中文回答用户的问题，提供准确、专业的建议。"""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                
                # 添加上下文信息
                if context:
                    context_str = json.dumps(context, ensure_ascii=False, indent=2)
                    messages[1]["content"] += f"\n\n相关上下文：\n{context_str}"
                
                data = {
                    "model": "moonshot-v1-8k",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": stream
                }
            
            if stream:
                # 流式响应 - 返回生成器
                return {
                    "stream": True,
                    "generator": self._generate_stream_response(data, headers)
                }
            else:
                # 非流式响应
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.kimi_api_url,
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        error_info = error_handler.handle_api_error(response.status_code)
                        return error_handler.format_error_response({
                            "tools_used": ["kimi"],
                            "model": "moonshot-v1-8k",
                            "stream": False
                        }, error_info)
                
                    response.raise_for_status()
                
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，我无法处理您的请求")
                
                return {
                    "response": ai_response,
                    "tools_used": ["kimi"],
                    "model": "moonshot-v1-8k",
                    "timestamp": datetime.now().isoformat(),
                    "stream": False
                }
            
        except Exception as e:
            return {
                "response": f"AI服务暂时不可用：{str(e)}",
                "tools_used": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "stream": False
            }

    async def _generate_deepseek_stream_response(self, data: Dict[str, Any], headers: Dict[str, str]):
        """生成DeepSeek流式响应"""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.deepseek_api_url,
                headers=headers,
                json=data,
                timeout=30
            ) as response:
                # 检查HTTP状态码
                if response.status_code >= 400:
                    error_info = error_handler.handle_api_error(response.status_code)
                    yield f"[ERROR] {error_info['response']}"
                    return
                
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            json_data = json.loads(line[6:])
                            if "choices" in json_data and json_data["choices"]:
                                delta = json_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    async def _generate_stream_response(self, data: Dict[str, Any], headers: Dict[str, str]):
        """生成Kimi流式响应"""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.kimi_api_url,
                headers=headers,
                json=data,
                timeout=30
            ) as response:
                # 检查HTTP状态码
                if response.status_code >= 400:
                    error_info = error_handler.handle_api_error(response.status_code)
                    yield f"[ERROR] {error_info['response']}"
                    return
                
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            json_data = json.loads(line[6:])
                            if "choices" in json_data and json_data["choices"]:
                                delta = json_data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def add_to_knowledge_base(self, text: str, source: str = "user_input") -> Dict[str, Any]:
        """添加文本到知识库"""
        if not self.embeddings:
            return {
                "success": False,
                "message": "嵌入模型未配置"
            }
        
        try:
            # 分割文本
            documents = self.text_splitter.create_documents([text])
            
            # 添加元数据
            for doc in documents:
                doc.metadata = {
                    "source": source,
                    "created_at": datetime.now().isoformat(),
                    "chunk_id": f"{source}_{hash(doc.page_content) % 10000}"
                }
            
            # 创建或更新向量存储
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
            else:
                self.vector_store.add_documents(documents)
            
            return {
                "success": True,
                "message": f"成功添加{len(documents)}个文档片段到知识库",
                "chunks": len(documents),
                "source": source
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"添加知识库失败：{str(e)}"
            }
    
    async def rag_query(self, query: str, k: int = 3, documents: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """使用RAG查询知识库"""
        if not self.vector_store:
            return {
                "response": "知识库为空，请先上传文件",
                "source_documents": [],
                "rag_enabled": False
            }
        
        try:
            # 搜索相关文档
            similar_docs = self.vector_store.similarity_search_with_score(query, k=k)
            
            # 如果指定了文档，过滤结果只包含这些文档的内容
            if documents and similar_docs:
                # 提取文档名称列表
                target_document_names = [doc['name'] for doc in documents]
                # 过滤文档，只保留源文档名称匹配的结果
                filtered_docs = []
                for doc, score in similar_docs:
                    # 检查文档元数据中的source是否匹配目标文档名称
                    doc_source = doc.metadata.get('source', '')
                    if any(target_name in doc_source for target_name in target_document_names):
                        filtered_docs.append((doc, score))
                
                # 如果过滤后没有结果，使用原始结果
                similar_docs = filtered_docs if filtered_docs else similar_docs
            
            if not similar_docs:
                return {
                    "response": "未找到相关信息",
                    "source_documents": [],
                    "rag_enabled": True
                }
            
            # 构建上下文
            context_parts = []
            source_documents = []
            
            for doc, score in similar_docs:
                context_parts.append(doc.page_content)
                source_documents.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            context = "\n\n".join(context_parts)
            
            # 使用Kimi基于上下文回答问题
            rag_prompt = f"""基于以下知识库内容，请回答用户的问题：

知识库内容：
{context}

用户问题：{query}

请根据提供的知识库内容给出准确、详细的回答。如果知识库中没有相关信息，请明确说明。"""
            
            kim_result = await self.chat_with_kimi(rag_prompt)
            
            return {
                "response": kim_result["response"],
                "source_documents": source_documents,
                "rag_enabled": True,
                "context_used": context
            }
            
        except Exception as e:
            return {
                "response": f"RAG查询失败：{str(e)}",
                "source_documents": [],
                "error": str(e)
            }
    
    async def clear_knowledge_base(self, user_id: int = None) -> Dict[str, Any]:
        """清空知识库"""
        if user_id:
            # 如果有用户ID，清空该用户的知识库（需要实现用户特定的知识库）
            # 当前实现为全局知识库，这里保持兼容
            self.vector_store = None
            return {
                "success": True,
                "message": f"用户 {user_id} 的知识库已清空"
            }
        else:
            self.vector_store = None
            return {
                "success": True,
                "message": "知识库已清空"
            }
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        if self.vector_store is None:
            return {
                "total_documents": 0,
                "is_empty": True,
                "rag_enabled": False
            }
        
        try:
            # 获取索引统计
            index = self.vector_store.index
            return {
                "total_documents": index.ntotal,
                "is_empty": False,
                "rag_enabled": True,
                "embedding_model": os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4"),
                "llm_model": os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus-v3")
            }
        except:
            return {
                "total_documents": 0,
                "is_empty": True,
                "rag_enabled": False
            }
    
    async def query_document_content(self, filename: str, query: str) -> Dict[str, Any]:
        """查询特定文档的内容"""
        if not self.vector_store:
            return {
                "found": False,
                "content": "",
                "message": "知识库为空"
            }
        
        try:
            # 直接搜索所有文档，然后按文件名筛选
            all_docs = self.vector_store.similarity_search_with_score(
                query, 
                k=20  # 增加搜索数量
            )
            
            if not all_docs:
                return {
                    "found": False,
                    "content": "",
                    "message": f"知识库中没有文档"
                }
            
            # 筛选出与目标文件名相关的文档
            relevant_docs = []
            for doc, score in all_docs:
                doc_source = doc.metadata.get("source", "")
                if doc_source == filename or filename in doc_source:
                    relevant_docs.append(doc)
            
            # 如果没有找到，尝试更宽松的匹配
            if not relevant_docs:
                # 获取所有文档，按文件名匹配
                all_docs_wide = self.vector_store.similarity_search_with_score(
                    " ",  # 搜索所有内容
                    k=100  # 获取更多文档
                )
                
                for doc, score in all_docs_wide:
                    doc_source = doc.metadata.get("source", "")
                    if filename in doc_source or doc_source in filename:
                        relevant_docs.append(doc)
            
            if not relevant_docs:
                # 列出所有可用的文档源
                available_sources = []
                all_docs_list = self.vector_store.similarity_search_with_score(" ", k=50)
                for doc, score in all_docs_list:
                    source = doc.metadata.get("source", "unknown")
                    if source not in available_sources:
                        available_sources.append(source)
                
                return {
                    "found": False,
                    "content": "",
                    "message": f"未找到文档: {filename}",
                    "available_sources": available_sources
                }
            
            # 合并相关内容
            full_content = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # 生成摘要
            summary_prompt = f"请为以下文档内容生成一个简洁的摘要，突出关键信息：\n\n{full_content[:2000]}"
            summary_result = await self.chat_with_kimi(summary_prompt)
            
            # 提取关键点
            key_points_prompt = f"请从以下文档中提取5-8个关键要点：\n\n{full_content[:2000]}"
            key_points_result = await self.chat_with_kimi(key_points_prompt)
            
            # 解析关键点
            key_points = []
            if key_points_result.get("response"):
                lines = key_points_result["response"].split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.')):
                        key_points.append(line.lstrip('-•1234567890. ').strip())
            
            return {
                "found": True,
                "content": full_content,
                "summary": summary_result.get("response", ""),
                "key_points": key_points[:8],
                "word_count": len(full_content)
            }
            
        except Exception as e:
            return {
                "found": False,
                "content": "",
                "message": f"查询失败: {str(e)}"
            }

    async def chat_with_local_model(self, message: str, context: Optional[Dict[str, Any]] = None, stream: bool = False) -> Dict[str, Any]:
        """使用本地模型进行对话（备用方案）"""
        return {
            "response": "当前AI服务暂时不可用，请稍后再试或联系管理员配置API密钥",
            "tools_used": ["local"],
            "timestamp": datetime.now().isoformat(),
            "stream": False
        }

    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None, stream: bool = False, use_rag: bool = False) -> Dict[str, Any]:
        """统一聊天接口，优先使用DeepSeek，其次Kimi，最后本地模型"""
        try:
            # 优先使用DeepSeek API
            if self.deepseek_api_key:
                result = await self.chat_with_deepseek(message, context, stream)
                if "暂时不可用" not in result.get("response", "") and "未配置" not in result.get("response", ""):
                    return result
            
            # 其次使用Kimi API
            if self.kimi_api_key:
                result = await self.chat_with_kimi(message, context, stream)
                if "暂时不可用" not in result.get("response", "") and "未配置" not in result.get("response", ""):
                    return result
            
            # 如果API不可用，使用本地RAG或本地模型
            if use_rag and self.vector_store:
                rag_result = await self.rag_query(message, context)
                if rag_result:
                    return rag_result
            
            # 最后使用本地模型
            return await self.chat_with_local_model(message, context, stream)
            
        except Exception as e:
            return {
                "response": f"所有AI服务暂时不可用：{str(e)}",
                "tools_used": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "stream": False
            }

# 创建全局实例
ai_service = UnifiedAIService()