<template>
  <aside 
    :class="[
      'bg-white h-full transition-all duration-300 fixed left-0 top-0 z-20',
      isOpen ? 'w-64' : 'w-16'
    ]"
  >
    <!-- 品牌Logo -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white">
          <i class="fas fa-server text-xl"></i>
        </div>
        <h1 v-if="isOpen" class="text-xl font-bold text-gray-800">基于SDN的流量检测与监控系统</h1>
      </div>
      <button 
        class="text-gray-600 hover:text-blue-600 p-2 transition-colors duration-300"
        @click="$emit('toggle-sidebar')"
      >
        <i class="fas fa-bars"></i>
      </button>
    </div>
    
    <!-- 导航菜单 -->
    <nav class="py-4">
      <ul>
        <li class="mb-1">
          <router-link 
            to="/flowmaster"
            class="flex items-center px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors duration-300"
            :class="$route.path === '/flowmaster' ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600' : ''"
          >
            <i class="fas fa-network-wired text-lg w-6 text-center"></i>
            <span v-if="isOpen" class="ml-3">流量监控</span>
          </router-link>
        </li>
        
        <li class="mb-1">
          <router-link 
            to="/dashboard"
            class="flex items-center px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors duration-300"
            :class="$route.path === '/dashboard' ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600' : ''"
          >
            <i class="fas fa-tachometer-alt text-lg w-6 text-center"></i>
            <span v-if="isOpen" class="ml-3">数据总览</span>
          </router-link>
        </li>
        
        <li class="mb-1">
          <router-link 
            to="/anomalies"
            class="flex items-center px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors duration-300"
            :class="$route.path === '/anomalies' ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600' : ''"
          >
            <i class="fas fa-exclamation-triangle text-lg w-6 text-center"></i>
            <span v-if="isOpen" class="ml-3">异常检测</span>
          </router-link>
        </li>
        
        <li class="mb-1">
          <router-link 
            to="/ratelimit"
            class="flex items-center px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors duration-300"
            :class="$route.path === '/ratelimit' ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600' : ''"
          >
            <i class="fas fa-tachometer-alt text-lg w-6 text-center"></i>
            <span v-if="isOpen" class="ml-3">限速中心</span>
          </router-link>
        </li>
        
        <li class="mb-1">
          <router-link 
            to="/ai-assistant"
            class="flex items-center px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 transition-colors duration-300"
            :class="$route.path === '/ai-assistant' ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600' : ''"
          >
            <i class="fas fa-robot text-lg w-6 text-center"></i>
            <span v-if="isOpen" class="ml-3">AI助手</span>
          </router-link>
        </li>
      </ul>
    </nav>
    
    <!-- 底部 - 已清空，用户信息移至右上角 -->
    <div class="absolute bottom-0 w-full border-t border-gray-200">
      <!-- 空白区域，保持布局一致性 -->
    </div>
  </aside>
</template>

<script setup lang="ts">
import { defineEmits, defineProps } from 'vue';

defineProps<{
  isOpen: boolean;
}>();

defineEmits<{
  'toggle-sidebar': [];
  logout: [];
}>();
</script>

<style scoped>
/* 侧边栏样式已通过Tailwind工具类实现 */
</style>
