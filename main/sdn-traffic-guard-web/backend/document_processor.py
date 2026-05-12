"""
文档处理模块 - 处理用户上传的文档
支持TXT、PDF、CSV等格式的文本提取和分块
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class DocumentProcessor:
    """文档处理器 - 提取和分块文本"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 0):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 每个块的大小（字符数，默认500防止内存溢出）
            chunk_overlap: 块之间的重叠大小（字符数，默认0防止无限循环）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = min(chunk_overlap, chunk_size - 1)  # 防止无限循环
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """从TXT文件提取文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"[✅] TXT文件提取成功: {file_path}")
            return content
        except Exception as e:
            print(f"[❌] TXT文件提取失败: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """从PDF文件提取文本"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            print(f"[✅] PDF文件提取成功: {file_path}")
            return text
        except ImportError:
            print(f"[⚠️] PyPDF2未安装，请运行: pip install PyPDF2")
            raise
        except Exception as e:
            print(f"[❌] PDF文件提取失败: {e}")
            raise
    
    def extract_text_from_csv(self, file_path: str) -> str:
        """从CSV文件提取文本"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path, encoding='utf-8')
            # 将CSV转换为可读的文本格式
            text = "【CSV数据表】\n"
            text += f"列名: {', '.join(df.columns)}\n\n"
            for idx, row in df.iterrows():
                text += f"记录 {idx + 1}: "
                text += " | ".join([f"{col}: {val}" for col, val in row.items()])
                text += "\n"
            print(f"[✅] CSV文件提取成功: {file_path}")
            return text
        except ImportError:
            print(f"[⚠️] pandas未安装，请运行: pip install pandas")
            raise
        except Exception as e:
            print(f"[❌] CSV文件提取失败: {e}")
            raise
    
    def extract_text(self, file_path: str) -> str:
        """
        根据文件类型自动提取文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.txt':
            return self.extract_text_from_txt(file_path)
        elif file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext == '.csv':
            return self.extract_text_from_csv(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    def chunk_text(self, text: str, source: str = "unknown") -> List[Dict[str, str]]:
        """
        将文本分块（简化版，防止超时）
        
        Args:
            text: 要分块的文本
            source: 文本来源（文件名等）
            
        Returns:
            分块列表，每个块包含content、source、start_pos、end_pos
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        print(f"[📊] 开始分块，文本大小: {text_len} 字符，块大小: {self.chunk_size}")
        
        chunk_count = 0
        while start < text_len:
            # 计算块的结束位置
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # 只添加非空块
                chunks.append({
                    'content': chunk_text,
                    'source': source,
                    'start_pos': start,
                    'end_pos': end
                })
                chunk_count += 1
                if chunk_count % 10 == 0:
                    print(f"[📦] 已分块 {chunk_count} 个...")
            
            # 移动到下一块（考虑重叠）
            start = end - self.chunk_overlap
        
        print(f"[✅] 文本分块完成: {len(chunks)} 个块 (来源: {source})")
        return chunks
    
    def process_document(self, file_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        处理单个文档：提取文本 → 分块
        
        Args:
            file_path: 文件路径
            
        Returns:
            (原始文本, 分块列表)
        """
        print(f"[📄] 开始处理文档: {file_path}")
        
        # 提取文本
        text = self.extract_text(file_path)
        
        # 获取文件名作为来源
        source = Path(file_path).name
        
        # 分块
        chunks = self.chunk_text(text, source)
        
        return text, chunks


class KnowledgeBaseManager:
    """知识库管理器 - 管理上传的文档"""
    
    def __init__(self, knowledge_base_dir: str = None):
        """
        初始化知识库管理器
        
        Args:
            knowledge_base_dir: 知识库目录路径
        """
        if knowledge_base_dir is None:
            # 默认使用项目的docs/knowledge_base目录
            project_root = Path(__file__).parent.parent
            knowledge_base_dir = project_root / "docs" / "knowledge_base"
        
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        self.processor = DocumentProcessor()
        
        print(f"[📚] 知识库目录: {self.knowledge_base_dir}")
    
    def save_document(self, file_path: str, filename: str = None) -> str:
        """
        保存文档到知识库目录
        
        Args:
            file_path: 源文件路径
            filename: 保存的文件名（如果为None，使用原文件名）
            
        Returns:
            保存后的文件路径
        """
        if filename is None:
            filename = Path(file_path).name
        
        # 添加时间戳避免重名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_without_ext = Path(filename).stem
        file_ext = Path(filename).suffix
        filename = f"{name_without_ext}_{timestamp}{file_ext}"
        
        save_path = self.knowledge_base_dir / filename
        
        try:
            # 复制文件
            with open(file_path, 'rb') as src:
                with open(save_path, 'wb') as dst:
                    dst.write(src.read())
            
            print(f"[✅] 文档已保存: {save_path}")
            return str(save_path)
        except Exception as e:
            print(f"[❌] 文档保存失败: {e}")
            raise
    
    def list_documents(self) -> List[Dict[str, str]]:
        """
        列出知识库中的所有文档
        
        Returns:
            文档列表
        """
        documents = []
        for file_path in self.knowledge_base_dir.glob('*'):
            if file_path.is_file():
                documents.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return sorted(documents, key=lambda x: x['modified'], reverse=True)
    
    def delete_document(self, filename: str) -> bool:
        """
        删除知识库中的文档
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        file_path = self.knowledge_base_dir / filename
        
        if not file_path.exists():
            print(f"[❌] 文档不存在: {filename}")
            return False
        
        try:
            file_path.unlink()
            print(f"[✅] 文档已删除: {filename}")
            return True
        except Exception as e:
            print(f"[❌] 文档删除失败: {e}")
            return False
    
    def get_document_info(self, filename: str) -> Dict[str, str]:
        """
        获取文档信息
        
        Args:
            filename: 文件名
            
        Returns:
            文档信息
        """
        file_path = self.knowledge_base_dir / filename
        
        if not file_path.exists():
            return None
        
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
