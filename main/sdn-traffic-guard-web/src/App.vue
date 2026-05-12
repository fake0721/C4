<template>
  <div class="h-screen bg-gray-50">
    <!-- 未认证时显示路由视图（登录、注册、忘记密码等） -->
    <div v-if="!isAuthenticated" class="h-screen bg-gray-50">
      <router-view />
    </div>
    
    <!-- 已认证时显示主界面 -->
    <div v-else class="flex flex-col h-screen bg-gray-50 overflow-hidden">
      <!-- 主内容区 -->
      <main class="flex-1 overflow-y-auto">
        <TopBar @toggle-sidebar="toggleSidebar" />
        
        <!-- 路由视图 -->
        <router-view class="p-6" />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUserStore } from './stores/user';
import TopBar from './components/common/TopBar.vue';

// 状态管理
const userStore = useUserStore();

const isAuthenticated = computed(() => userStore.isAuthenticated);

// 侧边栏切换（保留函数以避免错误，但不再使用）
const toggleSidebar = () => {
  // 不再需要切换侧边栏
};

// 登出处理 - 在TopBar组件中使用
const handleLogout = () => {
  userStore.logout();
};
// 导出给其他组件使用
defineExpose({ handleLogout });
</script>

<style scoped>
/* 根组件样式 */
</style>
