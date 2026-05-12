<template>
  <div class="min-h-screen bg-slate-50 p-4">
    <div class="max-w-5xl mx-auto">
      <!-- 标题 -->
      <div class="text-center mb-8">
        <div
          class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 mb-4"
        >
          <i class="fas fa-user-cog text-blue-600 text-2xl"></i>
        </div>
        <h2 class="text-3xl font-bold text-slate-900 mb-1">
          个人信息
        </h2>
        <p class="text-sm text-slate-500">
          管理您的账号信息和安全设置
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：个人信息 + 安全设置 -->
        <div class="lg:col-span-2 space-y-6">
          <!-- 个人信息卡片 -->
          <div class="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-lg font-semibold text-slate-900">
                  个人信息
                </h3>
                <p class="text-xs text-slate-500 mt-1">
                  查看您的基础账号信息
                </p>
              </div>
            </div>

            <div class="space-y-5">
              <!-- 用户名 -->
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  用户名
                </label>
                <input
                  :value="userInfo.username"
                  class="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-900 cursor-not-allowed"
                  readonly
                />
                <p class="mt-1 text-xs text-slate-500">
                  用户名不可修改
                </p>
              </div>

              <!-- 账号类型 -->
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  账号类型
                </label>
                <div class="px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50">
                  <span
                    class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                    :class="
                      userInfo.role === 'admin'
                        ? 'bg-red-50 text-red-700'
                        : 'bg-blue-50 text-blue-700'
                    "
                  >
                    <span
                      class="w-1.5 h-1.5 rounded-full mr-2"
                      :class="
                        userInfo.role === 'admin'
                          ? 'bg-red-500'
                          : 'bg-blue-500'
                      "
                    ></span>
                    {{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </div>
              </div>

              <!-- 注册时间 -->
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  注册时间
                </label>
                <div class="px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-900">
                  {{ formatDateTime(userInfo.createdAt) || '—' }}
                </div>
              </div>
            </div>
          </div>

          <!-- 安全设置卡片（已去掉登录历史） -->
          <div class="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center">
                <div class="w-9 h-9 rounded-full bg-blue-500/10 flex items-center justify-center mr-3">
                  <i class="fas fa-shield-alt text-blue-600 text-sm"></i>
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-slate-900">
                    安全设置
                  </h3>
                  <p class="text-xs text-slate-500 mt-0.5">
                    建议定期检查和更新安全配置
                  </p>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <!-- 修改密码 -->
              <div
                class="flex items-center justify-between p-4 border border-slate-200 rounded-xl"
              >
                <div>
                  <h4 class="font-medium text-slate-900">
                    修改密码
                  </h4>
                  <p class="text-xs text-slate-500 mt-1">
                    定期更新密码可以提高账号安全性
                  </p>
                </div>
                <button
                  @click="navigateTo('/change-password')"
                  class="px-4 py-2 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
                >
                  修改
                </button>
              </div>

              <!-- 这里原本有“登录历史”，已按要求移除 -->
            </div>
          </div>
        </div>

        <!-- 右侧：头像 + 快捷操作 -->
        <div class="lg:col-span-1 space-y-6">
          <!-- 头像卡片 -->
          <div class="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 flex flex-col items-center">
            <div class="w-24 h-24 rounded-full overflow-hidden border-4 border-white shadow-md mb-4 bg-slate-100 flex items-center justify-center">
              <img
                v-if="userInfo.avatar"
                :src="userInfo.avatar"
                alt="头像"
                class="w-full h-full object-cover"
                @error="handleImageError"
              />
              <span
                v-else
                class="text-2xl font-semibold text-slate-500"
              >
                {{ userInfo.username ? userInfo.username[0].toUpperCase() : 'U' }}
              </span>
            </div>
            <p class="text-sm font-medium text-slate-900 mb-1">
              {{ userInfo.username || '未登录用户' }}
            </p>
            <p class="text-xs text-slate-500 mb-4">
              当前账号
            </p>
            <button
              class="px-4 py-2 rounded-full text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors"
              @click="showAvatarModal = true"
            >
              修改头像
            </button>
          </div>

          <!-- 快捷操作卡片 -->
          <div class="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
            <h3 class="text-sm font-semibold text-slate-900 mb-3">
              快捷操作
            </h3>
            <div class="space-y-2">
              <button
                @click="navigateTo('/dashboard')"
                class="w-full px-4 py-2 text-left text-slate-700 hover:bg-slate-50 rounded-lg transition-colors flex items-center text-sm"
              >
                <i class="fas fa-home mr-2"></i>
                返回首页
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="error"
        class="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
      >
        <p class="text-sm text-red-600">
          {{ error }}
        </p>
      </div>

      <!-- 成功提示 -->
      <div
        v-if="success"
        class="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg"
      >
        <p class="text-sm text-emerald-700">
          {{ success }}
        </p>
      </div>

      <!-- 修改头像弹窗 -->
      <ChangeAvatarModal
        v-if="showAvatarModal"
        @close="showAvatarModal = false"
        @avatar-updated="handleAvatarUpdated"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import ChangeAvatarModal from './common/ChangeAvatarModal.vue'

const userStore = useUserStore()

interface UserInfo {
  username: string
  role: string
  createdAt: string
  avatar: string
}

const userInfo = ref<UserInfo>({
  username: '',
  role: 'user',
  createdAt: '',
  avatar: ''
})

const loading = ref(false)
const error = ref<string>('')
const success = ref<string>('')
const showAvatarModal = ref(false)

// 头像加载失败时的处理（简单隐藏图片，保留首字母占位）
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// 格式化日期时间
const formatDateTime = (value: string) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载用户信息
const loadUserInfo = () => {
  if (userStore.user) {
    userInfo.value = {
      username: userStore.user.username,
      role: userStore.user.role,
      createdAt: userStore.user.createdAt,
      avatar: userStore.user.avatar || ''
    }
  }
}

// 页面导航
const navigateTo = (path: string) => {
  window.location.href = path
}

// 头像更新完成
const handleAvatarUpdated = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    await userStore.getUserInfo()
    loadUserInfo()
    showAvatarModal.value = false
    success.value = '头像更新成功！'
  } catch (err) {
    console.error(err)
    error.value = '头像更新失败，请重试'
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadUserInfo()
})
</script>
