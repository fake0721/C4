import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.llms import Tongyi
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import httpx
import asyncio
from datetime import datetime

class RAGService:
    def __init__(self):
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.dashscope_base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.embedding_model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
        self.chat_model = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus-v3")
        
        # 检查API Key是否配置
        self.enabled = bool(self.dashscope_api_key and self.dashscope_api_key.strip())
        
        # 初始化embedding模型和LLM
        if self.enabled:
            # 使用DashScope的嵌入模型
            self.embeddings = DashScopeEmbeddings(
                model=self.embedding_model,
                dashscope_api_key=self.dashscope_api_key
            )
            # 使用DashScope的通义千问作为RAG的LLM（因为Kimi没有RAG专用API）
            self.llm = Tongyi(
                model_name=self.chat_model,
                dashscope_api_key=self.dashscope_api_key,
                temperature=0.7,
                max_tokens=2000
            )
        else:
            self.embeddings = None
            self.llm = None
        
        # 初始化向量存储
        self.vector_store = None
        self.vector_store_path = Path(__file__).parent / "vector_store"
        
        # 尝试加载已保存的向量索引
        if self.enabled and self.vector_store_path.exists():
            try:
                print("🔄 加载已保存的向量索引...")
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ 向量索引加载成功")
            except Exception as e:
                print(f"⚠️  无法加载向量索引: {e}")
                print("💡 将在需要时创建新的向量索引")
                self.vector_store = None
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        
        # 定义RAG提示模板
        self.rag_prompt_template = """基于以下提供的上下文信息，请回答用户的问题。

上下文信息：
{context}

用户问题：{question}

请根据提供的上下文信息给出准确、详细的回答。如果上下文中没有相关信息，请明确说明。

回答："""
        
        self.prompt = PromptTemplate(
            template=self.rag_prompt_template,
            input_variables=["context", "question"]
        )

    async def create_embeddings_from_text(self, text: str, source: str = "user_input") -> List[Dict]:
        """从文本创建embedding向量"""
        if not self.enabled:
            raise ValueError("RAG功能未启用，请配置有效的DashScope API Key。获取方式：https://dashscope.console.aliyun.com/")
        try:
            # 分割文本
            documents = self.text_splitter.create_documents([text])
            
            # 为每个文档添加元数据
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
            
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "chunk_id": doc.metadata["chunk_id"]
                }
                for doc in documents
            ]
            
        except Exception as e:
            raise Exception(f"创建embedding失败: {str(e)}")

    async def create_embeddings_from_file(self, file_content: str, filename: str) -> List[Dict]:
        """从文件内容创建embedding向量"""
        if not self.enabled:
            raise ValueError("RAG功能未启用，请先配置Dashscope API Key")
        return await self.create_embeddings_from_text(file_content, f"file_{filename}")

    async def search_similar_documents(self, query: str, k: int = 5) -> List[Dict]:
        """搜索相似文档"""
        if not self.enabled:
            raise ValueError("RAG功能未启用，请先配置Dashscope API Key")
            
        if self.vector_store is None:
            return []
        
        try:
            similar_docs = self.vector_store.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in similar_docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"搜索文档失败: {str(e)}")

    async def generate_rag_response(self, query: str, context: str = None) -> Dict:
        """生成RAG增强的回答"""
        if not self.enabled:
            return {
                "answer": "RAG功能未启用，请先配置Dashscope API Key",
                "context_used": "",
                "source_documents": [],
                "rag_enabled": False,
                "error": "RAG功能未启用"
            }
        try:
            # 如果没有提供上下文，则搜索相关文档
            if not context:
                similar_docs = await self.search_similar_documents(query, k=3)
                if similar_docs:
                    context = "\n\n".join([doc["content"] for doc in similar_docs])
                else:
                    context = "没有相关的上下文信息"
            
            # 创建RAG链
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever() if self.vector_store else None,
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt}
            )
            
            # 生成回答
            if self.vector_store:
                result = qa_chain({"query": query})
                answer = result["result"]
                source_docs = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in result.get("source_documents", [])
                ]
            else:
                # 如果没有向量存储，直接使用LLM
                answer = await self.llm.agenerate([self.rag_prompt_template.format(
                    context=context,
                    question=query
                )])
                source_docs = []
            
            return {
                "answer": answer,
                "context_used": context,
                "source_documents": source_docs,
                "rag_enabled": self.vector_store is not None
            }
            
        except Exception as e:
            raise Exception(f"生成RAG回答失败: {str(e)}")

    async def clear_vector_store(self):
        """清空向量存储"""
        self.vector_store = None

    async def get_vector_store_stats(self) -> Dict:
        """获取向量存储统计信息"""
        if self.vector_store is None:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "is_empty": True
            }
        
        try:
            # 获取文档数量（近似）
            index = self.vector_store.index
            total_vectors = index.ntotal
            
            return {
                "total_documents": total_vectors,
                "total_chunks": total_vectors,
                "is_empty": total_vectors == 0
            }
            
        except Exception as e:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "is_empty": True,
                "error": str(e)
            }

# 创建全局RAG服务实例
rag_service = RAGService()