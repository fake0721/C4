#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库初始化脚本
使用新的 DashScope embedding 模型构建向量索引
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import DashScopeEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    from PyPDF2 import PdfReader
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请先安装: pip install langchain langchain-community dashscope faiss-cpu PyPDF2")
    sys.exit(1)


class KnowledgeBaseInitializer:
    """知识库初始化器"""
    
    def __init__(self):
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.embedding_model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
        self.docs_dir = Path(__file__).parent.parent / "docs" / "knowledge_base"
        self.vector_store_dir = Path(__file__).parent / "vector_store"
        self.vector_store_dir.mkdir(exist_ok=True)
        
        if not self.dashscope_api_key:
            raise ValueError("❌ 未配置 DASHSCOPE_API_KEY")
        
        print(f"🔄 初始化知识库...")
        print(f"📁 文档目录: {self.docs_dir}")
        print(f"🏢 向量存储目录: {self.vector_store_dir}")
        print(f"🧠 Embedding 模型: {self.embedding_model}")
        
        try:
            self.embeddings = DashScopeEmbeddings(
                model=self.embedding_model,
                dashscope_api_key=self.dashscope_api_key
            )
            print(f"✅ Embedding 模型初始化成功")
        except Exception as e:
            print(f"❌ Embedding 模型初始化失败: {e}")
            raise
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        self.vector_store = None
    
    def load_text_file(self, file_path: Path) -> str:
        """加载文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return ""
    
    def load_pdf_file(self, file_path: Path) -> str:
        """加载 PDF 文件"""
        try:
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n[第 {page_num + 1} 页]\n{page_text}"
                    except Exception as e:
                        print(f"⚠️  无法提取第 {page_num + 1} 页: {e}")
            return text
        except Exception as e:
            print(f"❌ 读取 PDF 失败 {file_path}: {e}")
            return ""
    
    def load_documents(self) -> list:
        """加载所有知识库文档"""
        documents = []
        
        if not self.docs_dir.exists():
            print(f"❌ 知识库目录不存在: {self.docs_dir}")
            return documents
        
        print(f"\n📂 扫描知识库文件...")
        
        # 扫描所有文件
        for file_path in sorted(self.docs_dir.iterdir()):
            if file_path.is_file():
                try:
                    if file_path.suffix.lower() == '.txt':
                        print(f"📄 加载: {file_path.name}")
                        content = self.load_text_file(file_path)
                    elif file_path.suffix.lower() == '.pdf':
                        print(f"📕 加载: {file_path.name}")
                        content = self.load_pdf_file(file_path)
                    else:
                        print(f"⏭️  跳过: {file_path.name} (不支持的格式)")
                        continue
                    
                    if content.strip():
                        # 分割文本
                        doc_chunks = self.text_splitter.create_documents([content])
                        
                        # 添加元数据
                        for chunk in doc_chunks:
                            chunk.metadata = {
                                "source": file_path.name,
                                "loaded_at": datetime.now().isoformat(),
                                "chunk_size": len(chunk.page_content)
                            }
                        
                        documents.extend(doc_chunks)
                        print(f"   ✅ {file_path.name}: {len(doc_chunks)} 个块")
                    else:
                        print(f"   ⚠️  {file_path.name}: 文件为空")
                        
                except Exception as e:
                    print(f"   ❌ 处理失败: {e}")
        
        return documents
    
    def build_index(self):
        """构建向量索引"""
        print(f"\n🔨 构建向量索引...")
        
        documents = self.load_documents()
        if not documents:
            print("❌ 没有文档可加载")
            return False
        
        print(f"\n📊 总共加载 {len(documents)} 个文档块")
        print(f"🧬 开始创建向量嵌入 (使用模型: {self.embedding_model})...")
        
        try:
            # DashScope 有批处理限制，分批处理
            batch_size = 10
            max_retries = 3
            retry_delay = 5
            print(f"⚙️  分批处理 (每批 {batch_size} 个)...")
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                print(f"   处理批次 {batch_num}/{total_batches} ({len(batch)} 个文档)...", end='', flush=True)
                
                # 带重试的处理
                success = False
                for attempt in range(max_retries):
                    try:
                        if self.vector_store is None:
                            self.vector_store = FAISS.from_documents(batch, self.embeddings)
                        else:
                            self.vector_store.add_documents(batch)
                        success = True
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"\n     ⚠️  重试 ({attempt+1}/{max_retries-1}), 等待 {retry_delay}s...")
                            time.sleep(retry_delay)
                        else:
                            raise
                
                if success:
                    print(" ✅")
            
            print(f"✅ 向量索引创建成功")
            
            # 保存向量索引
            self.vector_store.save_local(str(self.vector_store_dir))
            print(f"✅ 向量索引已保存到: {self.vector_store_dir}")
            
            # 打印统计信息
            print(f"\n📈 索引统计:")
            print(f"   - 文档块数: {len(documents)}")
            print(f"   - 向量维度: {self.vector_store.index.d if hasattr(self.vector_store.index, 'd') else 'N/A'}")
            print(f"   - Embedding 模型: {self.embedding_model}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 向量索引创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_retrieval(self, query: str = "什么是 SDN 防护?"):
        """测试检索功能"""
        if not self.vector_store:
            print("❌ 向量存储未初始化")
            return
        
        try:
            print(f"\n🔍 测试检索: '{query}'")
            results = self.vector_store.similarity_search(query, k=3)
            
            print(f"\n📌 检索结果 (前 3 条):")
            for i, doc in enumerate(results, 1):
                source = doc.metadata.get('source', '未知')
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"\n   {i}. 来源: {source}")
                print(f"      内容: {content_preview}...")
            
        except Exception as e:
            print(f"❌ 检索测试失败: {e}")


def main():
    """主函数"""
    try:
        initializer = KnowledgeBaseInitializer()
        success = initializer.build_index()
        
        if success:
            # 测试检索
            initializer.test_retrieval()
            print(f"\n✅ 知识库初始化完成!")
            return 0
        else:
            print(f"\n❌ 知识库初始化失败")
            return 1
            
    except Exception as e:
        print(f"\n❌ 初始化过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
