<template>
  <div class="knowledge-upload-container">
    <div class="upload-section">
      <h2>📚 知识库文档管理</h2>
      
      <!-- 上传区域 -->
      <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
        <div class="upload-box">
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".txt,.pdf,.csv,.docx"
            @change="handleFileSelect"
            style="display: none"
          />
          
          <div class="upload-icon">📤</div>
          <p class="upload-text">拖拽文件到此处或点击选择</p>
          <p class="upload-hint">支持格式: TXT、PDF、CSV、DOCX (最大10MB)</p>
          
          <button class="upload-btn" @click="openFileSelector">
            选择文件
          </button>
        </div>
      </div>
      
      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p>上传中... {{ uploadProgress }}%</p>
      </div>
      
      <!-- 上传结果 -->
      <div v-if="uploadMessage" :class="['upload-message', uploadSuccess ? 'success' : 'error']">
        {{ uploadMessage }}
      </div>
    </div>
    
    <!-- 文档列表 -->
    <div class="documents-section">
      <h3>📋 已上传的文档</h3>
      
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="documents.length === 0" class="empty">
        暂无文档
      </div>
      
      <div v-else class="documents-list">
        <div v-for="doc in documents" :key="doc.name" class="document-item">
          <div class="doc-info">
            <div class="doc-name">
              <span class="doc-icon">📄</span>
              {{ doc.name }}
            </div>
            <div class="doc-meta">
              <span class="doc-size">{{ formatFileSize(doc.size) }}</span>
              <span class="doc-time">{{ formatDate(doc.modified) }}</span>
            </div>
          </div>
          
          <button 
            class="delete-btn" 
            @click="deleteDocument(doc.name)"
            :disabled="deleting === doc.name"
          >
            {{ deleting === doc.name ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Document {
  name: string
  path: string
  size: number
  modified: string
}

const fileInput = ref<HTMLInputElement | null>(null)
const documents = ref<Document[]>([])
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')
const uploadSuccess = ref(false)
const deleting = ref('')

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await axios.get('/v1/knowledge/documents')
    if (response.data.success) {
      documents.value = response.data.documents
      console.log('[✅] 文档列表加载成功:', documents.value.length, '个文档')
    }
  } catch (error) {
    console.error('[❌] 加载文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理文件选择
const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    await uploadFiles(Array.from(input.files))
    input.value = '' // 重置input
  }
}

// 打开文件选择器
const openFileSelector = () => {
  fileInput.value?.click()
}

// 处理拖拽
const handleDrop = async (event: DragEvent) => {
  if (event.dataTransfer?.files) {
    await uploadFiles(Array.from(event.dataTransfer.files))
  }
}

// 上传文件
const uploadFiles = async (files: File[]) => {
  if (files.length === 0) return
  
  uploading.value = true
  uploadProgress.value = 0
  uploadMessage.value = ''
  
  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      
      // 验证文件类型
      const allowedExtensions = ['.txt', '.pdf', '.csv', '.docx']
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
      
      if (!allowedExtensions.includes(fileExt)) {
        uploadMessage.value = `❌ 不支持的文件格式: ${fileExt}`
        uploadSuccess.value = false
        continue
      }
      
      // 验证文件大小
      if (file.size > 10 * 1024 * 1024) {
        uploadMessage.value = `❌ 文件过大: ${file.name} (最大10MB)`
        uploadSuccess.value = false
        continue
      }
      
      // 上传文件
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        console.log(`[📤] 开始上传文件: ${file.name}`)
        const response = await axios.post('/v1/knowledge/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.success) {
          uploadMessage.value = `✅ 文件上传成功: ${file.name} (${response.data.chunks_count} 个块)`
          uploadSuccess.value = true
          console.log('[✅] 文件上传成功:', response.data)
        } else {
          uploadMessage.value = `❌ 上传失败: ${response.data.message}`
          uploadSuccess.value = false
        }
      } catch (error: any) {
        uploadMessage.value = `❌ 上传失败: ${error.response?.data?.detail || error.message}`
        uploadSuccess.value = false
        console.error('[❌] 上传失败:', error)
      }
      
      // 更新进度
      uploadProgress.value = Math.round(((i + 1) / files.length) * 100)
    }
    
    // 重新加载文档列表
    await loadDocuments()
  
  } finally {
    uploading.value = false
  }
}

// 删除文档
const deleteDocument = async (filename: string) => {
  if (!confirm(`确定要删除文档 "${filename}" 吗？`)) {
    return
  }
  
  deleting.value = filename
  try {
    console.log(`[🗑️] 删除文档: ${filename}`)
    const response = await axios.delete(`/v1/knowledge/documents/${filename}`)
    
    if (response.data.success) {
      uploadMessage.value = `✅ 文档已删除: ${filename}`
      uploadSuccess.value = true
      console.log('[✅] 文档删除成功')
      
      // 重新加载文档列表
      await loadDocuments()
    } else {
      uploadMessage.value = `❌ 删除失败: ${response.data.message}`
      uploadSuccess.value = false
    }
  } catch (error: any) {
    uploadMessage.value = `❌ 删除失败: ${error.response?.data?.detail || error.message}`
    uploadSuccess.value = false
    console.error('[❌] 删除失败:', error)
  } finally {
    deleting.value = ''
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 页面加载时获取文档列表
onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.knowledge-upload-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

/* 上传区域 */
.upload-section {
  margin-bottom: 40px;
}

.upload-section h2 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #333;
}

.upload-area {
  border: 2px dashed #4a90e2;
  border-radius: 8px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: #2e5c8a;
  background: linear-gradient(135deg, #e8ecf1 0%, #b3c6d9 100%);
}

.upload-box {
  text-align: center;
  padding: 40px 20px;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 10px 0;
}

.upload-hint {
  font-size: 12px;
  color: #666;
  margin: 5px 0 20px 0;
}

.upload-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 10px 30px;
  border-radius: 5px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* 上传进度 */
.upload-progress {
  margin-top: 20px;
  padding: 15px;
  background: #f0f4ff;
  border-radius: 5px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.upload-progress p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

/* 上传消息 */
.upload-message {
  margin-top: 15px;
  padding: 12px 15px;
  border-radius: 5px;
  font-size: 14px;
  animation: slideIn 0.3s ease;
}

.upload-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 文档列表 */
.documents-section {
  margin-top: 40px;
}

.documents-section h3 {
  font-size: 18px;
  margin-bottom: 15px;
  color: #333;
}

.loading,
.empty {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
  transition: all 0.3s ease;
}

.document-item:hover {
  background: #f5f5f5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.doc-info {
  flex: 1;
}

.doc-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  font-size: 16px;
}

.doc-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 15px;
}

.delete-btn {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 6px 15px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.delete-btn:hover:not(:disabled) {
  background: #ff5252;
  transform: translateY(-1px);
}

.delete-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
