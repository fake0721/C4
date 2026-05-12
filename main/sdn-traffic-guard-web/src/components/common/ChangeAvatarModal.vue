<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
      <!-- 标题 -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">修改头像</h3>
        <button 
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <!-- 内容 -->
      <div class="p-6">
        <!-- 当前头像预览 -->
        <div class="text-center mb-6">
          <p class="text-sm text-gray-600 mb-4">当前头像</p>
          <div class="flex justify-center">
            <div v-if="!currentAvatar || currentAvatar.startsWith('bg-')" 
              :class="[
                'w-32 h-32 rounded-full flex items-center justify-center text-white font-bold text-3xl',
                currentAvatar || 'bg-gradient-to-r from-indigo-500 to-purple-600'
              ]"
            >
              {{ currentUsername?.charAt(0).toUpperCase() || 'U' }}
            </div>
            <img v-else 
              :src="currentAvatar.startsWith('http') || currentAvatar.startsWith('data:') ? currentAvatar : 'http://localhost:8001' + currentAvatar" 
              alt="当前头像" 
              class="w-32 h-32 rounded-full object-cover border-2 border-gray-300"
              @error="handleImageError"
            />
          </div>
        </div>
        
        <!-- 文件上传 -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            选择新头像
          </label>
          <input 
            type="file" 
            ref="fileInput"
            accept="image/*"
            @change="handleFileSelect"
            class="hidden"
          />
          <div class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
            <div v-if="!previewImage" class="space-y-2">
              <i class="fas fa-cloud-upload-alt text-3xl text-gray-400"></i>
              <p class="text-sm text-gray-600">
                点击选择图片或拖拽图片到此处
              </p>
              <p class="text-xs text-gray-500">
                支持 JPG、PNG、GIF 格式，最大 2MB
              </p>
            </div>
            <div v-else class="space-y-2">
              <img 
                :src="previewImage" 
                alt="预览" 
                class="w-40 h-40 rounded-full object-cover mx-auto border-2 border-gray-300"
              />
              <button 
                @click="clearPreview"
                class="text-sm text-red-600 hover:text-red-800"
              >
                重新选择
              </button>
            </div>
          </div>
          <button 
            @click="triggerFileInput"
            class="w-full mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            选择图片
          </button>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-sm text-red-600">{{ error }}</p>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex space-x-3">
          <button 
            @click="$emit('close')"
            class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
          <button 
            @click="uploadAvatar"
            :disabled="!previewImage || uploading"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ uploading ? '上传中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useUserStore } from '../../stores/user';

const emit = defineEmits<{
  close: [];
  'avatar-updated': [];
}>();

const userStore = useUserStore() as ReturnType<typeof useUserStore>;
const fileInput = ref<HTMLInputElement>();

// 状态
const previewImage = ref<string>('');
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const error = ref<string>('');

// 计算属性
const currentAvatar = computed(() => userStore.user?.avatar);
const currentUsername = computed(() => userStore.user?.username);

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
  // 强制刷新用户数据
  userStore.getUserInfo();
};

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click();
};

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;
  
  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片文件';
    return;
  }
  
  // 验证文件大小 (2MB)
  if (file.size > 2 * 1024 * 1024) {
    error.value = '图片大小不能超过2MB';
    return;
  }
  
  selectedFile.value = file;
  error.value = '';
  
  // 创建预览
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);
};

// 清除预览
const clearPreview = () => {
  previewImage.value = '';
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 上传头像
const uploadAvatar = async () => {
  if (!selectedFile.value) return;
  
  uploading.value = true;
  error.value = '';
  
  try {
    const formData = new FormData();
    formData.append('avatar', selectedFile.value);
    
    await userStore.updateAvatar(formData);
    
    // 关闭弹窗并通知父组件
    emit('close');
    emit('avatar-updated');
  } catch (err: any) {
    error.value = err.message || '上传失败，请重试';
  } finally {
    uploading.value = false;
  }
};
</script>