"""
知识库集成模块 - 将上传的文档集成到RAG系统
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
from document_processor import DocumentProcessor, KnowledgeBaseManager


class KnowledgeIntegrator:
    """知识库集成器 - 将新文档集成到RAG系统"""
    
    def __init__(self, rag_instance=None):
        """
        初始化知识库集成器
        
        Args:
            rag_instance: RAG实例（如果为None，会在需要时从security_agent获取）
        """
        self.rag = rag_instance
        self.processor = DocumentProcessor()
        self.kb_manager = KnowledgeBaseManager()
    
    def _get_rag_instance(self):
        """获取RAG实例"""
        if self.rag is None:
            try:
                # 优先使用rag_system（支持add_documents方法）
                from rag_system import get_rag_instance
                self.rag = get_rag_instance()
                print(f"[✅] 使用rag_system实例")
            except Exception as e:
                print(f"[⚠️] rag_system获取失败: {e}，尝试从agent获取")
                try:
                    from security_agent import get_agent_instance
                    agent = get_agent_instance()
                    self.rag = agent.rag
                    print(f"[✅] 使用agent的rag实例")
                except Exception as e2:
                    print(f"[❌] 无法获取RAG实例: {e2}")
                    raise
        return self.rag
    
    async def add_document_async(self, file_path: str, filename: str = None) -> Dict:
        """
        异步添加文档到RAG知识库
        
        Args:
            file_path: 文件路径
            filename: 保存的文件名
            
        Returns:
            操作结果
        """
        try:
            print(f"[📄] 开始处理上传的文档: {file_path}")
            
            # 1. 处理文档（提取文本和分块）
            text, chunks = self.processor.process_document(file_path)
            
            # 2. 保存文档到知识库目录
            saved_path = self.kb_manager.save_document(file_path, filename)
            
            # 3. 获取RAG实例
            rag = self._get_rag_instance()
            
            # 4. 将文档添加到RAG知识库
            print(f"[🔄] 将文档添加到RAG知识库...")
            
            # 如果RAG支持异步添加
            if hasattr(rag, 'add_documents_async'):
                await rag.add_documents_async(chunks)
            else:
                # 否则在线程池中运行
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, rag.add_documents, chunks)
            
            print(f"[✅] 文档已成功添加到RAG知识库")
            
            return {
                'success': True,
                'message': '文档上传成功',
                'filename': Path(saved_path).name,
                'chunks_count': len(chunks),
                'text_length': len(text)
            }
        
        except Exception as e:
            print(f"[❌] 文档添加失败: {e}")
            return {
                'success': False,
                'message': f'文档添加失败: {str(e)}',
                'error': str(e)
            }
    
    def add_document_sync(self, file_path: str, filename: str = None) -> Dict:
        """
        同步添加文档到RAG知识库
        
        Args:
            file_path: 文件路径
            filename: 保存的文件名
            
        Returns:
            操作结果
        """
        try:
            print(f"[📄] 开始处理上传的文档: {file_path}")
            
            # 1. 处理文档（提取文本和分块）
            print(f"[1️⃣] 提取文本和分块...")
            text, chunks = self.processor.process_document(file_path)
            print(f"[✅] 提取完成: {len(chunks)} 个块，共 {len(text)} 字符")
            
            # 2. 保存文档到知识库目录
            print(f"[2️⃣] 保存文档到知识库目录...")
            saved_path = self.kb_manager.save_document(file_path, filename)
            print(f"[✅] 保存完成: {saved_path}")
            
            # 3. 获取RAG实例
            print(f"[3️⃣] 获取RAG实例...")
            rag = self._get_rag_instance()
            print(f"[✅] RAG实例获取成功")
            
            # 4. 将文档添加到RAG知识库
            print(f"[4️⃣] 将文档添加到RAG知识库...")
            
            if hasattr(rag, 'add_documents'):
                result = rag.add_documents(chunks)
                print(f"[✅] RAG添加结果: {result} 个块")
            else:
                print(f"[⚠️] RAG实例不支持add_documents方法")
                return {
                    'success': False,
                    'message': 'RAG实例不支持add_documents方法',
                    'error': 'Method not found'
                }
            
            print(f"[✅] 文档已成功添加到RAG知识库")
            
            return {
                'success': True,
                'message': '文档上传成功',
                'filename': Path(saved_path).name,
                'chunks_count': len(chunks),
                'text_length': len(text)
            }
        
        except Exception as e:
            import traceback
            print(f"[❌] 文档添加失败: {e}")
            print(f"[DEBUG] 错误堆栈:")
            traceback.print_exc()
            return {
                'success': False,
                'message': f'文档添加失败: {str(e)}',
                'error': str(e)
            }
    
    def list_documents(self) -> List[Dict]:
        """
        列出知识库中的所有文档
        
        Returns:
            文档列表
        """
        return self.kb_manager.list_documents()
    
    def delete_document(self, filename: str) -> Dict:
        """
        删除知识库中的文档
        
        Args:
            filename: 文件名
            
        Returns:
            操作结果
        """
        try:
            success = self.kb_manager.delete_document(filename)
            if success:
                return {
                    'success': True,
                    'message': '文档删除成功'
                }
            else:
                return {
                    'success': False,
                    'message': '文档删除失败'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'文档删除失败: {str(e)}',
                'error': str(e)
            }


# 全局知识库集成器实例
_knowledge_integrator = None


def get_knowledge_integrator():
    """获取知识库集成器单例"""
    global _knowledge_integrator
    if _knowledge_integrator is None:
        _knowledge_integrator = KnowledgeIntegrator()
    return _knowledge_integrator
