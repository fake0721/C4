# 文档上传 + RAG知识库动态更新 实现指南

## 📋 概述

本方案实现了用户文档上传功能，支持将TXT、PDF、CSV、DOCX等格式的文档动态添加到RAG知识库中。上传后的文档会被自动处理、分块、向量化，并集成到现有的RAG系统中，使得AI助手能够基于用户上传的文档进行准确回答。

---

## 🏗️ 架构设计

### 整体流程

```
用户上传文档
    ↓
后端接收文件 (验证类型和大小)
    ↓
文档处理 (提取文本 → 分块)
    ↓
保存到知识库目录
    ↓
向量化 (Embedding)
    ↓
存入向量数据库 (Chroma)
    ↓
后续查询自动使用新文档
```

### 核心模块

#### 1. **document_processor.py** - 文档处理模块
- `DocumentProcessor`: 文档处理器
  - `extract_text()`: 从各种格式提取文本
  - `chunk_text()`: 将文本分块
  - `process_document()`: 完整处理流程

- `KnowledgeBaseManager`: 知识库管理器
  - `save_document()`: 保存文档到知识库目录
  - `list_documents()`: 列出所有文档
  - `delete_document()`: 删除文档

#### 2. **knowledge_integration.py** - 知识库集成模块
- `KnowledgeIntegrator`: 知识库集成器
  - `add_document_sync()`: 同步添加文档到RAG
  - `add_document_async()`: 异步添加文档到RAG
  - `list_documents()`: 列出文档
  - `delete_document()`: 删除文档

- `get_knowledge_integrator()`: 获取单例实例

#### 3. **rag_system.py** - 修改现有RAG系统
- 新增 `add_documents()` 方法
  - 支持动态添加文档块
  - 自动向量化和存储

#### 4. **v1_routes.py** - 后端API端点
- `POST /v1/knowledge/upload`: 上传文档
- `GET /v1/knowledge/documents`: 列出文档
- `DELETE /v1/knowledge/documents/{filename}`: 删除文档

#### 5. **KnowledgeUpload.vue** - 前端组件
- 文件拖拽上传
- 上传进度显示
- 文档列表管理
- 文档删除功能

---

## 🚀 使用流程

### 后端使用

#### 1. 上传文档（通过API）

```bash
curl -X POST "http://localhost:8001/v1/knowledge/upload" \
  -F "file=@my_document.txt"
```

响应：
```json
{
  "success": true,
  "message": "文档上传成功",
  "filename": "my_document_20240101_120000.txt",
  "chunks_count": 12,
  "text_length": 5432
}
```

#### 2. 列出文档

```bash
curl "http://localhost:8001/v1/knowledge/documents"
```

响应：
```json
{
  "success": true,
  "documents": [
    {
      "name": "my_document_20240101_120000.txt",
      "path": "/path/to/docs/knowledge_base/my_document_20240101_120000.txt",
      "size": 5432,
      "modified": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

#### 3. 删除文档

```bash
curl -X DELETE "http://localhost:8001/v1/knowledge/documents/my_document_20240101_120000.txt"
```

### 前端使用

1. 在主应用中导入 `KnowledgeUpload.vue` 组件
2. 在合适的位置添加组件标签

```vue
<template>
  <div>
    <KnowledgeUpload />
  </div>
</template>

<script setup>
import KnowledgeUpload from '@/components/KnowledgeUpload/KnowledgeUpload.vue'
</script>
```

3. 用户可以：
   - 拖拽文件到上传区域
   - 点击"选择文件"按钮选择文件
   - 查看已上传的文档列表
   - 删除不需要的文档

---

## 📝 文档处理细节

### 支持的文件格式

| 格式 | 提取方式 | 依赖库 |
|------|---------|--------|
| TXT | 直接读取 | 无 |
| PDF | PyPDF2 | `pip install PyPDF2` |
| CSV | pandas | `pip install pandas` |
| DOCX | python-docx | `pip install python-docx` |

### 文本分块策略

- **块大小**: 800字符（可配置）
- **重叠**: 200字符（保持上下文连贯）
- **分割点**: 优先在句子边界（。！？\n）分割

```python
processor = DocumentProcessor(chunk_size=800, chunk_overlap=200)
text, chunks = processor.process_document("document.txt")
```

### 向量化和存储

- **Embedding模型**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **向量数据库**: Chroma
- **持久化**: 自动保存到 `./chroma_db` 目录

---

## 🔍 查询流程

当用户询问关于上传文档的问题时：

```
用户: "我上传的文档中关于DDoS防御有什么内容？"
    ↓
意图识别: 【数据查询】
    ↓
调用MCP工具: query_network_topology (如果相关)
    ↓
RAG检索: 从向量数据库中搜索相似内容
    ↓
LLM生成: 基于检索结果和用户问题生成回答
    ↓
回答: "根据您上传的文档，DDoS防御包括..."
```

### 关键点

1. **RAG检索自动使用新文档**: 上传后的文档会被自动添加到向量数据库，后续查询会自动检索
2. **依据文档回答**: LLM会基于检索到的文档内容生成回答，确保准确性
3. **文档来源追踪**: 每个检索结果都包含文档来源信息

---

## 🛠️ 测试

运行测试脚本验证功能：

```bash
python test_knowledge_upload.py
```

测试内容：
1. 文档处理器测试
2. 知识库管理器测试
3. 知识库集成器测试

---

## ⚙️ 配置

### 知识库目录

默认位置: `docs/knowledge_base/`

修改位置：
```python
from knowledge_integration import KnowledgeIntegrator

integrator = KnowledgeIntegrator()
# 修改知识库目录
integrator.kb_manager.knowledge_base_dir = "/custom/path"
```

### 文本分块参数

```python
from document_processor import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1000,      # 块大小
    chunk_overlap=300     # 重叠大小
)
```

### 向量数据库持久化

```python
from rag_system import NetworkSecurityRAG

rag = NetworkSecurityRAG(persist_dir="./custom_chroma_db")
```

---

## 🐛 故障排除

### 问题1: 上传失败 - "不支持的文件格式"

**原因**: 文件格式不在支持列表中

**解决**:
- 确保文件扩展名是 `.txt`, `.pdf`, `.csv`, `.docx`
- 检查文件是否真的是声称的格式

### 问题2: PDF提取失败 - "PyPDF2未安装"

**原因**: 缺少PDF处理库

**解决**:
```bash
pip install PyPDF2
```

### 问题3: CSV提取失败 - "pandas未安装"

**原因**: 缺少CSV处理库

**解决**:
```bash
pip install pandas
```

### 问题4: 文档上传后查询不到

**原因**: 向量数据库未正确更新

**解决**:
1. 检查后端日志是否有错误信息
2. 确认文档已保存到知识库目录
3. 重启后端服务，重新初始化RAG

---

## 📊 性能考虑

### 文件大小限制

- **单文件**: 10MB
- **建议**: 5MB以内，以获得最佳性能

### 处理时间

| 文件大小 | 处理时间 |
|---------|---------|
| 100KB | < 1秒 |
| 1MB | 1-3秒 |
| 5MB | 3-10秒 |
| 10MB | 10-20秒 |

### 向量数据库大小

- 每个块约占用 1-2KB 空间
- 1000个块约占用 1-2MB

---

## 🔐 安全考虑

1. **文件类型验证**: 只允许特定格式
2. **文件大小限制**: 防止大文件攻击
3. **文件名处理**: 添加时间戳避免覆盖
4. **访问控制**: 建议添加用户认证（后续实现）

---

## 🚀 后续改进

### 第二阶段

- [ ] 支持DOCX格式
- [ ] 批量上传
- [ ] 文档预览
- [ ] 文档搜索功能

### 第三阶段

- [ ] 用户权限管理
- [ ] 文档版本控制
- [ ] 文档分类标签
- [ ] 自动文档更新

### 第四阶段

- [ ] 文档OCR识别（图片转文字）
- [ ] 多语言支持
- [ ] 文档相似度检测
- [ ] 知识库备份和恢复

---

## 📚 相关文件

- `backend/document_processor.py` - 文档处理模块
- `backend/knowledge_integration.py` - 知识库集成模块
- `backend/rag_system.py` - RAG系统（已修改）
- `backend/v1_routes.py` - API端点（已修改）
- `src/components/KnowledgeUpload/KnowledgeUpload.vue` - 前端组件
- `test_knowledge_upload.py` - 测试脚本

---

## 📞 支持

如有问题或建议，请联系开发团队。

---

**最后更新**: 2024年1月
**版本**: 1.0
