<template>
  <div class="auth-page">
    <div class="w-full max-w-lg space-y-6">
      <div class="space-y-3 text-left">
        <div class="flex items-center space-x-3">
          <span class="w-1.5 h-10 rounded-full bg-primary"></span>
          <div>
            <p class="text-xs font-semibold text-primary uppercase tracking-[0.2em]">SDN 平台</p>
            <h1 class="text-4xl md:text-5xl font-black text-dark tracking-tight leading-tight">流量检测与监控系统</h1>
          </div>
        </div>
        <p class="text-lg text-dark-2">重置密码</p>
      </div>

      <div class="auth-panel">
        <div class="flex items-start justify-between mb-4">
          <div>
            <p class="auth-subtitle">密码管理</p>
            <h2 class="auth-title mt-1">重置密码</h2>
          </div>
          <router-link to="/login" class="auth-link text-sm">返回登录</router-link>
        </div>

        <form class="space-y-6" @submit.prevent="handleResetPassword">
          <div class="space-y-5">
            <div>
              <label for="new-password" class="block text-sm font-medium text-dark mb-2">
                新密码
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-dark-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                  </svg>
                </div>
                <input
                  id="new-password"
                  v-model="newPassword"
                  name="new-password"
                  type="password"
                  required
                  class="auth-input"
                  placeholder="请输入新密码"
                />
              </div>
            </div>
            
            <div>
              <label for="confirm-password" class="block text-sm font-medium text-dark mb-2">
                确认密码
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg class="h-5 w-5 text-dark-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                  </svg>
                </div>
                <input
                  id="confirm-password"
                  v-model="confirmPassword"
                  name="confirm-password"
                  type="password"
                  required
                  class="auth-input"
                  placeholder="请再次输入新密码"
                />
              </div>
            </div>
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm text-center">
            <div class="flex items-center justify-center">
              <svg class="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              {{ error }}
            </div>
          </div>
          
          <div v-if="success" class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm text-center">
            <div class="flex items-center justify-center">
              <svg class="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              {{ success }}
            </div>
          </div>

          <button
            type="submit"
            :disabled="loading || !!error && !success"
            class="auth-button"
          >
            <span class="flex items-center space-x-2">
              <svg class="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>{{ loading ? '重置中...' : '重置密码' }}</span>
            </span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const newPassword = ref('')
const confirmPassword = ref('')
const token = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  loading.value = true
  token.value = (route.query.token as string) || ''
  
  if (!token.value) {
    error.value = '无效的重置链接'
    loading.value = false
    return
  }

  try {
    const result = await userStore.verifyResetToken(token.value)
    if (!result.success) {
      error.value = result.message
    }
  } catch (err) {
    error.value = '验证失败，请稍后重试'
  } finally {
    loading.value = false
  }
})

const handleResetPassword = async () => {
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  if (newPassword.value.length < 6) {
    error.value = '密码长度至少需要6位'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const result = await userStore.resetPassword(token.value, newPassword.value)
    
    if (result.success) {
      success.value = result.message || '密码重置成功，正在跳转到登录...'
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      error.value = result.message || '密码重置失败，请重试'
    }
  } catch (err) {
    error.value = '密码重置失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
