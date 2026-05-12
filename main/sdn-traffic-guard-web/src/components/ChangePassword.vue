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
              修改登录密码，提升账号安全。与登录页面统一的布局，更易操作。
            </p>
          </div>
          <div class="mt-8 space-y-2 text-xs text-dark-2">
            <p class="font-medium text-dark">· 强密码建议 ·</p>
            <p>· 保持定期修改，避免重复使用 ·</p>
          </div>
        </div>

        <!-- 右侧表单 -->
        <div class="w-full md:w-1/2 p-7 md:p-10">
          <!-- 顶部标题（移动端） -->
          <div class="md:hidden mb-6">
            <p class="text-[10px] font-semibold text-primary tracking-[0.25em] uppercase">SDN 平台</p>
            <h1 class="mt-2 text-2xl font-black text-dark leading-snug">流量检测与监控系统</h1>
            <p class="text-sm text-dark-2 mt-2">修改密码</p>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleChangePassword" class="space-y-5">
            <div>
              <label class="flex items-center text-xs font-medium text-dark mb-1.5">原密码</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <i class="fas fa-lock text-[14px]"></i>
                </div>
                <input
                  v-model="oldPassword"
                  :type="showOldPassword ? 'text' : 'password'"
                  placeholder="请输入原密码"
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 pr-10 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  required
                />
                <button
                  type="button"
                  @click="showOldPassword = !showOldPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-dark-2 hover:text-dark transition"
                >
                  <i :class="showOldPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
            </div>

            <div>
              <label class="flex items-center text-xs font-medium text-dark mb-1.5">新密码</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <i class="fas fa-key text-[14px]"></i>
                </div>
                <input
                  v-model="newPassword"
                  :type="showNewPassword ? 'text' : 'password'"
                  placeholder="请输入新密码"
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 pr-10 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  required
                  @input="validatePassword"
                />
                <button
                  type="button"
                  @click="showNewPassword = !showNewPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-dark-2 hover:text-dark transition"
                >
                  <i :class="showNewPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
              <div v-if="newPassword" class="mt-2 space-y-1">
                <div class="text-xs flex items-center" :class="passwordValid.length ? 'text-emerald-600' : 'text-red-500'">
                  <i :class="passwordValid.length ? 'fas fa-check-circle' : 'fas fa-times-circle'" class="mr-1"></i>
                  至少6个字符
                </div>
              </div>
            </div>

            <div>
              <label class="flex items-center text-xs font-medium text-dark mb-1.5">确认新密码</label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-dark-2">
                  <i class="fas fa-shield-alt text-[14px]"></i>
                </div>
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="请再次输入新密码"
                  class="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 pl-9 pr-10 text-sm text-dark outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  required
                />
                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-dark-2 hover:text-dark transition"
                >
                  <i :class="showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </button>
              </div>
            </div>

            <div v-if="error" class="p-3 rounded-2xl bg-red-50 text-red-600 text-sm flex items-start space-x-2">
              <i class="fas fa-exclamation-circle mt-0.5"></i>
              <span>{{ error }}</span>
            </div>

            <div v-if="success" class="p-3 rounded-2xl bg-emerald-50 text-emerald-600 text-sm flex items-start space-x-2">
              <i class="fas fa-check-circle mt-0.5"></i>
              <span>{{ success }}</span>
            </div>

            <button
              type="submit"
              :disabled="loading || !isFormValid"
              class="w-full flex justify-center items-center rounded-2xl bg-primary text-white text-sm font-semibold py-2.5 shadow-sm hover:bg-primary/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin border-2 border-white/50 border-t-transparent rounded-full"></span>
              <span>{{ loading ? '修改中...' : '确认修改' }}</span>
            </button>

            <div class="text-right text-xs text-dark-2">
              <button type="button" class="hover:text-primary transition" @click="goBack">
                返回
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const passwordValid = ref({
  length: false,
  uppercase: true,
  lowercase: true,
  number: true
})

const isFormValid = computed(() => {
  return (
    oldPassword.value.trim() &&
    newPassword.value.trim() &&
    confirmPassword.value.trim() &&
    newPassword.value === confirmPassword.value &&
    passwordValid.value.length
  )
})

const validatePassword = () => {
  const password = newPassword.value
  passwordValid.value = {
    length: password.length >= 6,
    uppercase: true,
    lowercase: true,
    number: true
  }
}

const handleChangePassword = async () => {
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的新密码不一致'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const result = await userStore.changePassword(
      userStore.user?.username || '',
      oldPassword.value,
      newPassword.value
    )

    if (result.success) {
      success.value = result.message || '密码修改成功'
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    } else {
      error.value = result.message || '密码修改失败'
    }
  } catch (err) {
    error.value = '修改密码时发生错误，请重试'
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}
</script>
