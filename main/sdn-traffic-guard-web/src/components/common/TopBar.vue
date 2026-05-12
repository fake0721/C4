<template>
  <header :class="[
    'h-16 shadow-sm flex items-center justify-between px-6 sticky top-0 z-20 transition-colors duration-300',
    darkMode ? 'bg-gray-900 border-b border-gray-700' : 'bg-white'
  ]">
    <div class="flex items-center">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white">
          <i class="fas fa-server text-xl"></i>
        </div>
        <h1 class="text-xl font-bold text-gray-800">基于SDN的流量检测与监控系统</h1>
      </div>
      
      <!-- 导航菜单 -->
      <nav class="ml-8">
        <ul class="flex space-x-6">
          <li>
            <router-link 
              to="/dashboard"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/dashboard' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-tachometer-alt text-lg mr-2"></i>
              <span>数据总览</span>
            </router-link>
          </li>
          
          <li>
            <router-link 
              to="/anomalies"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/anomalies' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-exclamation-triangle text-lg mr-2"></i>
              <span>异常检测</span>
            </router-link>
          </li>
          
          <li>
            <router-link 
              to="/ratelimit"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/ratelimit' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-tachometer-alt text-lg mr-2"></i>
              <span>限速中心</span>
            </router-link>
          </li>
          
          <li>
            <router-link 
              to="/flowtable"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/flowtable' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-table text-lg mr-2"></i>
              <span>流表管理</span>
            </router-link>
          </li>
          
          <li>
            <router-link 
              to="/ai-assistant"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/ai-assistant' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-robot text-lg mr-2"></i>
              <span>AI助手</span>
            </router-link>
          </li>
          
          <li>
            <router-link 
              to="/knowledge"
              class="flex items-center px-3 py-2 text-gray-600 hover:text-blue-600 transition-colors duration-300"
              :class="$route.path === '/knowledge' ? 'text-blue-600 border-b-2 border-blue-600' : ''"
            >
              <i class="fas fa-book text-lg mr-2"></i>
              <span>知识库</span>
            </router-link>
          </li>
        </ul>
      </nav>
    </div>
    
    <div class="flex items-center space-x-6">
      
      <!-- 声音开关 -->
      <button 
        @click="toggleSound"
        :class="[
          'relative text-xl transition-all duration-300 transform hover:scale-110',
          soundEnabled ? 'text-green-500 hover:text-green-600' : 'text-gray-400 hover:text-red-500'
        ]"
        :title="soundEnabled ? '关闭声音' : '开启声音'"
      >
        <i :class="soundEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute'"></i>
        <div v-if="soundEnabled" class="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
      </button>
      
      <!-- 深色模式切换 -->
      <button 
        @click="toggleDarkMode"
        :class="[
          'relative text-xl transition-all duration-300 transform hover:scale-110',
          darkMode ? 'text-yellow-400 hover:text-yellow-300' : 'text-gray-600 hover:text-blue-600'
        ]"
        :title="darkMode ? '切换到浅色模式' : '切换到深色模式'"
      >
        <i :class="darkMode ? 'fas fa-sun' : 'fas fa-moon'"></i>
        <div v-if="darkMode" class="absolute inset-0 rounded-full animate-ping bg-yellow-400 opacity-20"></div>
      </button>
      
      <!-- 设置按钮和下拉菜单 -->
      <div class="relative">
        <button 
          @click="toggleSettingsMenu"
          :class="[
            'relative transition-colors duration-300',
            darkMode ? 'text-gray-300 hover:text-blue-400' : 'text-gray-600 hover:text-blue-600'
          ]"
        >
          <i class="fas fa-cog text-xl"></i>
        </button>
        
        <!-- 设置下拉菜单 -->
        <div 
          v-if="showSettingsMenu"
          :class="[
            'absolute right-0 mt-2 w-64 rounded-lg shadow-lg border z-50 transition-colors duration-300',
            darkMode 
              ? 'bg-gray-800 border-gray-600' 
              : 'bg-white border-gray-200'
          ]"
        >
          <!-- 用户信息 -->
          <div :class="[
            'p-4 border-b transition-colors duration-300',
            darkMode ? 'border-gray-600' : 'border-gray-200'
          ]">
            <div class="flex items-center space-x-3">
              <div v-if="!user?.avatar || user.avatar.startsWith('bg-')" 
                :class="[
                  'w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl',
                  user?.avatar || 'bg-gradient-to-r from-indigo-500 to-purple-600'
                ]"
              >
                {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
              </div>
              <img v-else 
                :src="user.avatar.startsWith('http') || user.avatar.startsWith('data:') ? user.avatar : 'http://localhost:8000' + user.avatar" 
                alt="用户头像" 
                class="w-14 h-14 rounded-full object-cover border-2 border-gray-300"
                @error="handleImageError"
              />
              <div>
                <p :class="[
                  'font-medium transition-colors duration-300',
                  darkMode ? 'text-gray-100' : 'text-gray-900'
                ]">{{ user?.username || '用户' }}</p>
                <p :class="[
                  'text-sm transition-colors duration-300',
                  darkMode ? 'text-gray-400' : 'text-gray-600'
                ]">{{ user?.email || '' }}</p>
              </div>
            </div>
          </div>
          
          <!-- 设置选项 -->
          <div class="py-2">
            <button 
              @click="openChangeAvatar"
              :class="[
                'w-full px-4 py-2 text-left text-sm flex items-center transition-colors duration-300',
                darkMode 
                  ? 'text-gray-300 hover:bg-gray-700' 
                  : 'text-gray-700 hover:bg-gray-50'
              ]"
            >
              <i :class="[
                'fas fa-user-circle mr-3',
                darkMode ? 'text-gray-500' : 'text-gray-400'
              ]"></i>
              修改头像
            </button>
            
            <button 
              @click="openChangePassword"
              :class="[
                'w-full px-4 py-2 text-left text-sm flex items-center transition-colors duration-300',
                darkMode 
                  ? 'text-gray-300 hover:bg-gray-700' 
                  : 'text-gray-700 hover:bg-gray-50'
              ]"
            >
              <i :class="[
                'fas fa-key mr-3',
                darkMode ? 'text-gray-500' : 'text-gray-400'
              ]"></i>
              修改密码
            </button>
            
            <button 
              @click="openAccountDetails"
              :class="[
                'w-full px-4 py-2 text-left text-sm flex items-center transition-colors duration-300',
                darkMode 
                  ? 'text-gray-300 hover:bg-gray-700' 
                  : 'text-gray-700 hover:bg-gray-50'
              ]"
            >
              <i :class="[
                'fas fa-user-cog mr-3',
                darkMode ? 'text-gray-500' : 'text-gray-400'
              ]"></i>
              账号详情
            </button>
            
            <div :class="[
              'border-t my-2 transition-colors duration-300',
              darkMode ? 'border-gray-600' : 'border-gray-200'
            ]"></div>
            
            <button 
              @click="handleLogout"
              class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center transition-colors duration-300"
            >
              <i class="fas fa-sign-out-alt mr-3"></i>
              退出登录
            </button>
          </div>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <div v-if="!user?.avatar || user.avatar.startsWith('bg-')" 
          :class="[
            'w-10 h-10 rounded-full flex items-center justify-center text-white font-bold',
            user?.avatar || 'bg-gradient-to-r from-indigo-500 to-purple-600'
          ]"
        >
          {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
        </div>
        <img v-else 
          :src="user.avatar.startsWith('http') || user.avatar.startsWith('data:') ? user.avatar : 'http://localhost:8000' + user.avatar" 
          alt="用户头像" 
          class="w-10 h-10 rounded-full object-cover border-2 border-gray-300"
          @error="handleImageError"
        >
        <span :class="[
          'text-sm font-medium transition-colors duration-300',
          darkMode ? 'text-gray-200' : 'text-gray-700'
        ]">{{ user?.username || '用户' }}</span>
      </div>
    </div>
    
    <!-- 修改头像弹窗 -->
    <ChangeAvatarModal 
      v-if="showChangeAvatarModal" 
      @close="showChangeAvatarModal = false"
      @avatar-updated="handleAvatarUpdated"
    />
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../stores/user';
import ChangeAvatarModal from './ChangeAvatarModal.vue';

// 定义 emits
defineEmits<{
  toggleSidebar: []
}>();

const router = useRouter();
const userStore = useUserStore();

// 状态管理
const showSettingsMenu = ref(false);
const showChangeAvatarModal = ref(false);

// 全局控制状态
const soundEnabled = ref(true);
const darkMode = ref(false);

// 获取用户信息
const user = userStore.user;

// 切换设置菜单
const toggleSettingsMenu = () => {
  showSettingsMenu.value = !showSettingsMenu.value;
};

// 切换声音开关
const toggleSound = () => {
  soundEnabled.value = !soundEnabled.value;
  localStorage.setItem('soundEnabled', soundEnabled.value.toString());
  
  // 广播声音状态变化
  window.dispatchEvent(new CustomEvent('soundToggle', { 
    detail: { enabled: soundEnabled.value } 
  }));
  
  // 播放切换音效
  if (soundEnabled.value) {
    playToggleSound();
  }
};

// 切换深色模式
const toggleDarkMode = () => {
  darkMode.value = !darkMode.value;
  localStorage.setItem('darkMode', darkMode.value.toString());
  
  // 应用深色模式到根元素
  if (darkMode.value) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  
  // 广播深色模式状态变化
  window.dispatchEvent(new CustomEvent('darkModeToggle', { 
    detail: { enabled: darkMode.value } 
  }));
  
  // 播放切换音效
  if (soundEnabled.value) {
    playToggleSound();
  }
};

// 播放切换音效
const playToggleSound = () => {
  try {
    const audio = new Audio();
    audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
    audio.volume = 0.3;
    audio.play().catch(() => {});
  } catch (error) {
    console.log('音效播放失败');
  }
};

// 点击外部关闭菜单
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.relative')) {
    showSettingsMenu.value = false;
  }
};

// 打开修改头像
const openChangeAvatar = () => {
  showSettingsMenu.value = false;
  showChangeAvatarModal.value = true;
};

// 打开修改密码
const openChangePassword = () => {
  showSettingsMenu.value = false;
  router.push('/change-password');
};

// 打开账号详情
const openAccountDetails = () => {
  showSettingsMenu.value = false;
  router.push('/account-details');
};

// 退出登录
const handleLogout = () => {
  showSettingsMenu.value = false;
  userStore.logout();
  router.push('/login');
};

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
  // 强制刷新用户数据
  userStore.getUserInfo();
};

// 头像更新处理
const handleAvatarUpdated = () => {
  // 可以在这里添加头像更新后的处理逻辑
  console.log('头像已更新');
};

// 初始化设置
const initializeSettings = () => {
  // 从localStorage恢复设置
  const savedSoundEnabled = localStorage.getItem('soundEnabled');
  const savedDarkMode = localStorage.getItem('darkMode');
  
  if (savedSoundEnabled !== null) {
    soundEnabled.value = savedSoundEnabled === 'true';
  }
  
  if (savedDarkMode !== null) {
    darkMode.value = savedDarkMode === 'true';
    if (darkMode.value) {
      document.documentElement.classList.add('dark');
    }
  }
};

// 生命周期钩子
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  initializeSettings();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
/* 顶部导航栏样式已通过Tailwind工具类实现 */
</style>
