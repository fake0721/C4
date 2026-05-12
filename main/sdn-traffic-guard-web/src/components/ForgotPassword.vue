<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50">
    <div class="w-full max-w-4xl px-4">
      <div class="flex flex-col md:flex-row bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden">
        <!-- 左侧品牌/介绍 -->
        <div class="hidden md:flex md:w-1/2 flex-col justify-between bg-gradient-to-b from-white to-slate-50 p-10">
          <div class="space-y-4">
            <p class="text-xs font-semibold text-primary tracking-[0.25em] uppercase">SDN 平台</p>
            <h1 class="text-3xl xl:text-4xl font-black text-dark leading-snug">流量检测与监控系统</h1>
            <p class="text-sm text-dark-2 leading-relaxed">
              找回或修改密码，保持账号安全。界面与登录保持一致，减少操作成本。
            </p>
          </div>
          <div class="mt-8 space-y-2 text-xs text-dark-2">
            <p class="font-medium text-dark">· 自助找回/重置 ·</p>
            <p>· 统一体验，快速完成 ·</p>
          </div>
        </div>

        <!-- 右侧表单 -->
        <div class="w-full md:w-1/2 p-7 md:p-10">
          <!-- 顶部标题（移动端） -->
          <div class="md:hidden mb-6">
            <p class="text-[10px] font-semibold text-primary tracking-[0.25em] uppercase">SDN 平台</p>
            <h1 class="mt-2 text-2xl font-black text-dark leading-snug">流量检测与监控系统</h1>
            <p class="text-sm text-dark-2 mt-2">密码管理</p>
          </div>

          <!-- 找回 / 修改 切换 -->
          <div class="mb-6">
            <div class="inline-flex bg-slate-100 rounded-full p-1">
              <button
                type="button"
                class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
                :class="activeTab === 'recover' ? 'bg-white shadow-sm text-dark' : 'text-dark-2'"
                @click="activeTab = 'recover'"
              >
                找回密码
              </button>
              <button
                type="button"
                class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
                :class="activeTab === 'change' ? 'bg-white shadow-sm text-dark' : 'text-dark-2'"
                @click="activeTab = 'change'"
              >
                修改密码
              </button>
            </div>
            <p class="mt-4 text-sm text-dark-2">
              {{ activeTab === 'recover' ? '找回已有账号的密码' : '修改已登录账号的密码' }}
            </p>
          </div>

          <!-- 提示信息 -->
          <div v-if="recoverError || changeError" class="mb-4">
            <div class="flex items-start space-x-2 text-sm rounded-2xl px-4 py-3 bg-red-50 text-red-600">
              <svg class="w-5 h-5 mt-0.5" viewBox="0 0 24 24" fill="none">
                <path d="M12 9v4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                <circle cx="12" cy="16" r="1" fill="currentColor" />
                <path d="M12 4L3 20h18L12 4z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
              </svg>
              <p>{{ recoverError || changeError }}</p>
            </div>
          </div>

          <div v-if="recoverSuccess || changeSuccess" class="mb-4">
            <div class="flex items-start space-x-2 text-sm rounded-2xl px-4 py-3 bg-emerald-50 text-emerald-600">
              <svg class="w-5 h-5 mt-0.5" viewBox="0 0 24 24" fill="none">
                <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <p>{{ recoverSuccess || changeSuccess }}</p>
            </div>
          </div>

          <!-- 找回密码表单 -->
          <form v-if="activeTab === 'recover'" class="space-y-5" @submit.prevent="handleGetPassword">
            <div>
              <label for="recover-username" class="flex items-center text-xs font-medium text-dark mb-1.5">用户名</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <path d="M12 12a4 4 0 100-8 4 4 0 000 8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M4 20c0-3.314 3.134-6 7-6h2c3.866 0 7 2.686 7 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <input
                  id="recover-username"
                  v-model="recoverUsername"
                  type="text"
                  required
                  :disabled="resetComplete"
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入用户名"
                />
              </div>
            </div>

            <div v-if="resetToken" class="space-y-3">
              <div class="rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                <p class="font-medium">重置令牌（演示环境直接显示，生产环境应通过邮件发送）</p>
                <p class="mt-1 break-all text-xs text-amber-900">{{ resetToken }}</p>
              </div>

              <div>
                <label for="new-reset-password" class="flex items-center text-xs font-medium text-dark mb-1.5">
                  输入新密码
                </label>
                <input
                  id="new-reset-password"
                  v-model="newResetPassword"
                  type="password"
                  :disabled="resetComplete"
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入新密码"
                />
              </div>

              <button
                type="button"
                :disabled="loading || resetComplete"
                class="w-full flex justify-center items-center rounded-2xl bg-emerald-600 text-white text-sm font-semibold py-2.5 shadow-sm hover:bg-emerald-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
                @click="handleResetWithToken"
              >
                <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin border-2 border-white/50 border-t-transparent rounded-full"></span>
                <span v-if="resetComplete">已重置，请稍候跳转 ({{ redirectSeconds }}s)</span>
                <span v-else>{{ loading ? '重置中...' : '确认重置密码' }}</span>
              </button>
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full flex justify-center items-center rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 shadow-sm hover:bg-primary/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin border-2 border-white/50 border-t-transparent rounded-full"></span>
              <span>{{ loading ? '查询中...' : '找回密码' }}</span>
            </button>
          </form>

          <!-- 修改密码表单 -->
          <form v-else class="space-y-5" @submit.prevent="handleChangePassword">
            <div>
              <label for="change-username" class="flex items-center text-xs font-medium text-dark mb-1.5">用户名</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <path d="M12 12a4 4 0 100-8 4 4 0 000 8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                    <path d="M4 20c0-3.314 3.134-6 7-6h2c3.866 0 7 2.686 7 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <input
                  id="change-username"
                  v-model="changeUsername"
                  type="text"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入用户名"
                />
              </div>
            </div>

            <div>
              <label for="old-password" class="flex items-center text-xs font-medium text-dark mb-1.5">原密码</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <rect x="4" y="9" width="16" height="11" rx="2" stroke="currentColor" stroke-width="1.5" />
                    <path d="M9 9V7a3 3 0 013-3v0a3 3 0 013 3v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                  </svg>
                </div>
                <input
                  id="old-password"
                  v-model="oldPassword"
                  type="password"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入原密码"
                />
              </div>
            </div>

            <div>
              <label for="new-password" class="flex items-center text-xs font-medium text-dark mb-1.5">新密码</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <rect x="4" y="9" width="16" height="11" rx="2" stroke="currentColor" stroke-width="1.5" />
                    <path d="M9 9V7a3 3 0 013-3v0a3 3 0 013 3v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                  </svg>
                </div>
                <input
                  id="new-password"
                  v-model="newPassword"
                  type="password"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入新密码"
                />
              </div>
            </div>

            <button
              type="submit"
              :disabled="loading || redirecting"
              class="w-full flex justify-center items-center rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 shadow-sm hover:bg-primary/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin border-2 border-white/50 border-t-transparent rounded-full"></span>
              <span v-if="redirecting">即将跳转登录 ({{ redirectSeconds }}s)</span>
              <span v-else>{{ loading ? '修改中...' : '修改密码' }}</span>
            </button>
          </form>

          <div class="mt-4 flex justify-center">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-primary border border-primary/40 rounded-xl hover:bg-primary/5 transition disabled:opacity-60 disabled:cursor-not-allowed"
              :disabled="redirecting"
              @click="goLogin"
            >
              返回登录
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const activeTab = ref<'recover' | 'change'>('recover')

const recoverUsername = ref('')
const recoverError = ref('')
const recoverSuccess = ref('')
const resetToken = ref('')
const newResetPassword = ref('')
const resetComplete = ref(false)
const redirectSeconds = ref(3)
const redirecting = ref(false)
let redirectTimer: number | null = null

const changeUsername = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const changeError = ref('')
const changeSuccess = ref('')

const loading = ref(false)

const handleGetPassword = async () => {
  loading.value = true
  recoverError.value = ''
  recoverSuccess.value = ''
  resetToken.value = ''
  newResetPassword.value = ''
  resetComplete.value = false
  redirecting.value = false
  if (redirectTimer) {
    clearInterval(redirectTimer)
    redirectTimer = null
  }

  if (!recoverUsername.value.trim()) {
    recoverError.value = '请输入用户名'
    loading.value = false
    return
  }

  try {
    // 请求后端生成重置令牌（演示环境直接返回 token）
    const result = await userStore.forgotPassword(recoverUsername.value.trim(), '')

    if (result.success && result.resetToken) {
      resetToken.value = result.resetToken
      recoverSuccess.value = '重置链接已生成，请设置新密码'
    } else {
      recoverError.value = result.message || '生成重置链接失败'
    }
  } catch (err) {
    recoverError.value = '生成重置链接失败，请检查网络连接后重试'
  } finally {
    loading.value = false
  }
}

const handleResetWithToken = async () => {
  recoverError.value = ''
  recoverSuccess.value = ''

  if (!resetToken.value) {
    recoverError.value = '请先点击“找回密码”生成重置链接'
    return
  }
  if (!newResetPassword.value.trim()) {
    recoverError.value = '请输入新的密码'
    return
  }

  loading.value = true
  try {
    const result = await userStore.resetPassword(resetToken.value, newResetPassword.value.trim())
    if (result.success) {
      recoverSuccess.value = '密码已重置成功，即将跳转到登录页'
      resetComplete.value = true
      startRedirect()
    } else {
      recoverError.value = result.message || '密码重置失败'
    }
  } catch (err) {
    recoverError.value = '密码重置失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const startRedirect = () => {
  redirecting.value = true
  redirectSeconds.value = 3
  if (redirectTimer) {
    clearInterval(redirectTimer)
  }
  redirectTimer = window.setInterval(() => {
    redirectSeconds.value -= 1
    if (redirectSeconds.value <= 0) {
      clearInterval(redirectTimer!)
      router.push('/login')
    }
  }, 1000)
}

const goLogin = () => {
  if (redirectTimer) {
    clearInterval(redirectTimer)
  }
  router.push('/login')
}

// 清理倒计时
onUnmounted(() => {
  if (redirectTimer) {
    clearInterval(redirectTimer)
  }
})

const handleChangePassword = async () => {
  loading.value = true
  changeError.value = ''
  changeSuccess.value = ''

  if (!changeUsername.value.trim()) {
    changeError.value = '请输入用户名'
    loading.value = false
    return
  }

  if (!oldPassword.value.trim()) {
    changeError.value = '请输入原密码'
    loading.value = false
    return
  }

  if (!newPassword.value.trim()) {
    changeError.value = '请输入新密码'
    loading.value = false
    return
  }

  if (newPassword.value === oldPassword.value) {
    changeError.value = '新密码不能与原密码相同'
    loading.value = false
    return
  }

  try {
    const result = await userStore.changePassword(
      changeUsername.value.trim(),
      oldPassword.value.trim(),
      newPassword.value.trim()
    )
    
    if (result.success) {
      changeSuccess.value = '密码修改成功！即将跳转到登录页，请使用新密码登录'
      oldPassword.value = ''
      newPassword.value = ''
      startRedirect()
    } else {
      changeError.value = result.message || '密码修改失败'
      if (result.message?.includes('用户名或原密码错误')) {
        changeError.value = '用户名或原密码错误，请检查后重试'
      }
    }
  } catch (err) {
    changeError.value = '密码修改失败，请检查网络连接后重试'
  } finally {
    loading.value = false
  }
}
</script>
