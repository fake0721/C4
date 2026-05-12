<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-50">
    <div class="w-full max-w-4xl px-4">
      <div
        class="flex flex-col md:flex-row bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden"
      >
        <!-- 左侧品牌/介绍 -->
        <div
          class="hidden md:flex md:w-1/2 flex-col justify-between bg-gradient-to-b from-white to-slate-50 p-10"
        >
          <div class="space-y-4">
            <p class="text-xs font-semibold text-primary tracking-[0.25em] uppercase">
              SDN 平台
            </p>
            <h1 class="text-3xl xl:text-4xl font-black text-dark leading-snug">
              流量检测与监控系统
            </h1>
            <p class="text-sm text-dark-2 leading-relaxed">
              面向 SDN 网络的可视化流量检测与监控平台，支持多维度流量分析、
              实时监控与告警，让网络状态一目了然。
            </p>
          </div>

          <div class="mt-8 space-y-2 text-xs text-dark-2">
            <p class="font-medium text-dark">· 安全可靠的身份认证</p>
            <p>· 高校/实验室项目友好 · 支持后期功能扩展</p>
          </div>
        </div>

        <!-- 右侧表单 -->
        <div class="w-full md:w-1/2 p-7 md:p-10">
          <!-- 顶部标题（移动端） -->
          <div class="md:hidden mb-6">
            <p class="text-[10px] font-semibold text-primary tracking-[0.25em] uppercase">
              SDN 平台
            </p>
            <h1 class="mt-2 text-2xl font-black text-dark leading-snug">
              流量检测与监控系统
            </h1>
          </div>

          <!-- 登录 / 注册 切换 -->
          <div class="mb-6">
            <div class="inline-flex bg-slate-100 rounded-full p-1">
              <button
                type="button"
                class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
                :class="isLogin ? 'bg-white shadow-sm text-dark' : 'text-dark-2'"
                @click="switchMode('login')"
              >
                登录
              </button>
              <button
                type="button"
                class="px-4 py-1.5 text-xs font-medium rounded-full transition-all"
                :class="!isLogin ? 'bg-white shadow-sm text-dark' : 'text-dark-2'"
                @click="switchMode('register')"
              >
                注册
              </button>
            </div>

            <p class="mt-4 text-sm text-dark-2">
              {{ isLogin ? '欢迎回来，请登录以继续使用系统' : '创建一个新账号，开始使用系统' }}
            </p>
          </div>

          <!-- 已有头像预览（登录时根据用户名获取到的头像） -->
          <div v-if="isLogin && userAvatar" class="mb-4 flex justify-center">
            <img
              :src="userAvatar"
              alt="用户头像"
              class="w-16 h-16 rounded-full border-2 border-primary shadow-sm object-cover"
            />
          </div>

          <!-- 提示信息 -->
          <div v-if="error" class="mb-4">
            <div
              class="flex items-start space-x-2 text-sm rounded-2xl px-4 py-3 bg-red-50 text-red-600"
            >
              <svg class="w-5 h-5 mt-0.5" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 9v4"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
                <circle cx="12" cy="16" r="1" fill="currentColor" />
                <path
                  d="M12 4L3 20h18L12 4z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                />
              </svg>
              <p>{{ error }}</p>
            </div>
          </div>

          <div v-if="success" class="mb-4">
            <div
              class="flex items-start space-x-2 text-sm rounded-2xl px-4 py-3 bg-emerald-50 text-emerald-600"
            >
              <svg class="w-5 h-5 mt-0.5" viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 13l4 4L19 7"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <p>{{ success }}</p>
            </div>
          </div>

          <!-- 表单 -->
          <form class="space-y-4" @submit.prevent="handleSubmit">
            <!-- 用户名 -->
            <div>
              <label for="username" class="flex items-center text-xs font-medium text-dark mb-1.5">
                用户名
              </label>
              <div class="relative">
                <div
                  class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 12a4 4 0 100-8 4 4 0 000 8z"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      d="M4 20c0-3.314 3.134-6 7-6h2c3.866 0 7 2.686 7 6"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </div>
                <input
                  id="username"
                  v-model="form.username"
                  type="text"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请输入用户名"
                />
              </div>
            </div>

            <!-- 密码 -->
            <div>
              <label for="password" class="flex items-center text-xs font-medium text-dark mb-1.5">
                密码
              </label>
              <div class="relative">
                <div
                  class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <rect
                      x="4"
                      y="9"
                      width="16"
                      height="11"
                      rx="2"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path
                      d="M9 9V7a3 3 0 013-3v0a3 3 0 013 3v2"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                    />
                  </svg>
                </div>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  :placeholder="isLogin ? '请输入密码' : '请设置登录密码'"
                />
              </div>
            </div>

            <!-- 确认密码（仅注册） -->
            <div v-if="!isLogin">
              <label
                for="confirmPassword"
                class="flex items-center text-xs font-medium text-dark mb-1.5"
              >
                确认密码
              </label>
              <div class="relative">
                <div
                  class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <rect
                      x="4"
                      y="9"
                      width="16"
                      height="11"
                      rx="2"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path
                      d="M9 9V7a3 3 0 013-3v0a3 3 0 013 3v2"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                    />
                  </svg>
                </div>
                <input
                  id="confirmPassword"
                  v-model="form.confirmPassword"
                  type="password"
                  required
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="请再次输入密码"
                />
              </div>
            </div>

            <!-- 头像上传（仅注册） -->
            <div v-if="!isLogin">
              <label class="flex items-center text-xs font-medium text-dark mb-1.5">
                头像（可选）
              </label>
              <div class="flex items-center space-x-4">
                <div class="relative">
                  <div
                    class="w-16 h-16 rounded-full border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center overflow-hidden"
                  >
                    <span v-if="!previewAvatar" class="text-[10px] text-dark-2">预览</span>
                    <img
                      v-else
                      :src="previewAvatar"
                      alt="头像预览"
                      class="w-full h-full object-cover"
                    />
                  </div>
                </div>

                <div class="flex space-x-2">
                  <label class="cursor-pointer">
                    <input
                      ref="avatarInputRef"
                      type="file"
                      accept="image/*"
                      class="hidden"
                      @change="handleAvatarChange"
                    />
                    <div
                      class="px-4 py-2 text-xs rounded-xl bg-primary text-white font-medium hover:bg-primary/90 transition"
                    >
                      选择头像
                    </div>
                  </label>

                  <button
                    v-if="previewAvatar"
                    type="button"
                    class="px-3 py-2 text-xs rounded-xl border border-slate-200 text-dark-2 hover:bg-slate-50 transition"
                    @click="removeAvatar"
                  >
                    清除
                  </button>
                </div>
              </div>
            </div>

            <!-- 底部按钮与辅助链接 -->
            <div class="pt-2 space-y-3">
              <button
                type="submit"
                class="w-full flex justify-center items-center rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 shadow-sm hover:bg-primary/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="loading"
              >
                <span
                  v-if="loading"
                  class="mr-2 inline-block h-4 w-4 animate-spin border-2 border-white/50 border-t-transparent rounded-full"
                ></span>
                <span>
                  {{
                    loading
                      ? (isLogin ? '登录中...' : '创建中...')
                      : (isLogin ? '安全登录' : '创建账号')
                  }}
                </span>
              </button>

              <div v-if="isLogin" class="flex items-center justify-between text-xs text-dark-2">
                <router-link to="/forgot-password" class="hover:text-primary transition">
                  忘记密码？
                </router-link>
                <button
                  type="button"
                  class="hover:text-primary transition"
                  @click="switchMode('register')"
                >
                  还没有账号？去注册 →
                </button>
              </div>

              <div v-else class="text-right text-xs text-dark-2">
                <button
                  type="button"
                  class="hover:text-primary transition"
                  @click="switchMode('login')"
                >
                  已有账号？去登录 →
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')
const success = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  avatar: null as string | null,
})

const userAvatar = ref<string>('') // 登录时，根据用户名获取到的头像
const previewAvatar = ref<string>('') // 注册时，上传头像的预览
const avatarInputRef = ref<HTMLInputElement | null>(null)

const isLogin = computed(() => mode.value === 'login')

const resetMessages = () => {
  error.value = ''
  success.value = ''
}

const switchMode = (target: 'login' | 'register') => {
  if (mode.value === target) return
  mode.value = target
  resetMessages()
  if (target === 'register') {
    userAvatar.value = ''
  }
}

/**
 * 根据用户名获取已有用户头像（用于登录界面）
 * 加了：
 * 1. 只在“返回时用户名仍然是当前值 & 仍是登录模式”时更新头像，避免旧请求覆盖新结果
 */
const fetchUserAvatar = async (username: string) => {
  if (!username) {
    userAvatar.value = ''
    return
  }

  // 记录这次请求对应的用户名
  const requestedUsername = username

  try {
    const response = await fetch(`/api/auth/user-avatar/${encodeURIComponent(username)}`)
    const data = await response.json()

    // 返回时如果用户名变了，或者已经切换到注册模式，就丢弃这次结果
    if (requestedUsername !== form.username || !isLogin.value) {
      return
    }

    if (data.success && data.avatar) {
      userAvatar.value = data.avatar
    } else {
      userAvatar.value = ''
    }
  } catch (e) {
    console.error('获取用户头像失败:', e)
    if (requestedUsername === form.username && isLogin.value) {
      userAvatar.value = ''
    }
  }
}

// 防抖定时器（非响应式）
let avatarDebounceTimer: number | undefined

// 监听用户名输入，登录模式下自动拉取头像（300ms 防抖）
watch(
  () => form.username,
  (newUsername) => {
    if (!isLogin.value) {
      userAvatar.value = ''
      return
    }

    if (avatarDebounceTimer) {
      clearTimeout(avatarDebounceTimer)
    }

    avatarDebounceTimer = window.setTimeout(() => {
      fetchUserAvatar(newUsername)
    }, 300)
  }
)

const handleAvatarChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result as string
    previewAvatar.value = result
    form.avatar = result // 使用 Base64 作为头像
  }
  reader.readAsDataURL(file)
}

const removeAvatar = () => {
  previewAvatar.value = ''
  form.avatar = null
  if (avatarInputRef.value) {
    avatarInputRef.value.value = ''
  }
}

const handleSubmit = async () => {
  if (loading.value) return

  resetMessages()

  if (mode.value === 'register') {
    if (!form.username || !form.password || !form.confirmPassword) {
      error.value = '请完整填写注册信息'
      return
    }

    if (form.password !== form.confirmPassword) {
      error.value = '两次输入的密码不一致'
      return
    }

    loading.value = true
    try {
      const result = await userStore.register(
        form.username,
        form.password,
        undefined,
        form.avatar || undefined
      )

      if (result.success) {
        success.value = '注册成功，正在为你跳转到登录界面...'
        setTimeout(() => {
          mode.value = 'login'
          success.value = ''
        }, 1500)
      } else {
        error.value = result.message || '注册失败，请稍后重试'
      }
    } catch (e) {
      console.error(e)
      error.value = '注册失败，请稍后重试'
    } finally {
      loading.value = false
    }
  } else {
    // 登录
    if (!form.username || !form.password) {
      error.value = '请输入用户名和密码'
      return
    }

    loading.value = true
    try {
      const result = await userStore.login(form.username, form.password)
      if (result.success) {
        router.push('/dashboard')
      } else {
        error.value = result.message || '登录失败，请稍后重试'
      }
    } catch (e) {
      console.error(e)
      error.value = '登录失败，请稍后重试'
    } finally {
      loading.value = false
    }
  }
}
</script>
