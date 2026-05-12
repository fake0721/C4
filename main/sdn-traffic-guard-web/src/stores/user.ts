import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserStore, User } from './types'

// API基础路径配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// 认证状态接口定义

export const useUserStore = defineStore('user', (): UserStore => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!user.value)

  // 初始化时从本地存储加载用户数据
  const initializeAuth = () => {
    const savedUser = localStorage.getItem('currentUser')
    const savedToken = localStorage.getItem('authToken')
    
    console.log('=== 初始化认证状态 ===')
    console.log('存储的token:', savedToken)
    console.log('存储的用户:', savedUser)
    console.log('localStorage完整内容:', {
      currentUser: localStorage.getItem('currentUser'),
      authToken: localStorage.getItem('authToken'),
      user: localStorage.getItem('user')
    })
    
    if (savedUser && savedToken) {
      try {
        user.value = JSON.parse(savedUser)
        token.value = savedToken
        console.log('✅ 认证状态已初始化')
        console.log('用户对象:', user.value)
        console.log('token值:', token.value)
      } catch (error) {
        console.error('❌ 解析存储的用户数据失败:', error)
        logout()
      }
    } else {
      console.log('❌ 未找到认证信息')
      user.value = null
      token.value = null
    }
  }

  // 验证token有效性
  const validateToken = async (): Promise<boolean> => {
    if (!token.value) return false
    
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.status === 401) {
        console.log('Token无效，清理认证信息')
        logout()
        return false
      }
      
      return response.ok
    } catch (error) {
      console.error('验证token时出错:', error)
      return false
    }
  }

  // 登录
  const login = async (username: string, password: string): Promise<{ success: boolean; message: string }> => {
    try {
      // 调用后端API登录
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      // 检查响应是否为空或无效
      if (!response.ok) {
        return { success: false, message: '登录失败，请检查网络连接' }
      }

      let data
      try {
        const text = await response.text()
        if (!text.trim()) {
          return { success: false, message: '服务器响应为空' }
        }
        data = JSON.parse(text)
      } catch (jsonError) {
        console.error('JSON解析错误:', jsonError)
        return { success: false, message: '服务器响应格式错误' }
      }
      
      if (!data.success) {
        return { success: false, message: data.message || '用户名或密码错误' }
      }

      // 设置用户状态和token
      user.value = {
        id: data.user.id,
        username: data.user.username,
        password: password, // 注意：实际项目中不应该存储明文密码
        email: data.user.email,
        avatar: data.user.avatar || 'bg-blue-500',
        role: data.user.role,
        createdAt: new Date().toISOString()
      }
      // 使用后端返回的token或用户ID作为临时token
      token.value = data.token || data.user.id
        
        // 保存到本地存储（用于保持登录状态）
        localStorage.setItem('currentUser', JSON.stringify(user.value))
        if (token.value) {
          localStorage.setItem('authToken', token.value)
        }
      
      return { success: true, message: '登录成功' }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, message: '登录失败，请重试' }
    }
  }

  // 注册
  const register = async (username: string, password: string, email?: string, avatar?: string): Promise<{ success: boolean; message: string }> => {
    try {
      // 构建注册数据，只包含非空值
      const registerData: any = { username, password }
      if (email && email.trim() !== '') {
        registerData.email = email
      }
      if (avatar && avatar.trim() !== '') {
        registerData.avatar = avatar
      }

      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData)
      })

      // 检查响应状态
      if (!response.ok) {
        let errorMessage = '注册失败'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || '注册失败'
        } catch (e) {
          // 如果响应不是JSON，使用状态文本
          errorMessage = response.statusText || '注册失败'
        }
        return { success: false, message: errorMessage }
      }

      const data = await response.json()
      
      if (!data.success) {
        return { success: false, message: data.message || data.detail || '注册失败' }
      }
      
      return { success: true, message: '注册成功' }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, message: '网络错误，请检查网络连接后重试' }
    }
  }

  // 登出
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('currentUser')
    localStorage.removeItem('authToken')
    // 强制刷新页面到登录页
    window.location.href = '/login'
  }

  // 忘记密码
  const forgotPassword = async (username: string, email: string): Promise<{ success: boolean; message: string; resetToken?: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email })
      })

      const data = await response.json()
      
      if (!response.ok || !data.success) {
        return { success: false, message: data.detail || '重置请求失败' }
      }
      
      return { 
        success: true, 
        message: data.message || '重置邮件已发送',
        resetToken: data.reset_token // 演示用，实际应该通过邮件
      }
    } catch (error) {
      console.error('Forgot password error:', error)
      return { success: false, message: '重置请求失败，请重试' }
    }
  }

  // 重置密码
  const resetPassword = async (token: string, newPassword: string): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, new_password: newPassword })
      })

      const data = await response.json()
      
      if (!response.ok || !data.success) {
        return { success: false, message: data.detail || '密码重置失败' }
      }
      
      return { success: true, message: data.message || '密码重置成功' }
    } catch (error) {
      console.error('Reset password error:', error)
      return { success: false, message: '密码重置失败，请重试' }
    }
  }

  // 验证重置token
  const verifyResetToken = async (token: string): Promise<{ success: boolean; message: string; userId?: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-reset-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
      })

      const data = await response.json()
      
      if (!response.ok || !data.success) {
        return { success: false, message: data.detail || '无效的或已过期的重置链接' }
      }
      
      return { 
        success: true, 
        message: data.message || '重置链接有效',
        userId: data.user_id
      }
    } catch (error) {
      console.error('Verify reset token error:', error)
      return { success: false, message: '验证失败，请重试' }
    }
  }

  // 获取原密码
  const getPassword = async (username: string): Promise<{ success: boolean; message: string; password?: string }> => {
    try {
      const response = await fetch('/api/auth/get-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username })
      })

      const data = await response.json()
      
      if (!response.ok || !data.success) {
        return { success: false, message: data.detail || '获取密码失败' }
      }
      
      return { 
        success: true, 
        message: data.message || '密码获取成功',
        password: data.password
      }
    } catch (error) {
      console.error('Get password error:', error)
      return { success: false, message: '获取密码失败，请重试' }
    }
  }

  // 修改密码
  const changePassword = async (username: string, oldPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, old_password: oldPassword, new_password: newPassword })
      })

      const data = await response.json()
      
      if (!response.ok) {
        return { success: false, message: data.detail || '密码修改失败' }
      }
      
      return { success: true, message: data.message || '密码修改成功' }
    } catch (error) {
      console.error('Change password error:', error)
      return { success: false, message: '密码修改失败，请重试' }
    }
  }

  // 获取用户信息
  const getUserInfo = async (): Promise<{ success: boolean; message: string }> => {
    if (!token.value) {
      return { success: false, message: '用户未登录' }
    }
    try {
      const response = await fetch('/api/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token.value}`,
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        return { success: false, message: '获取用户信息失败' }
      }

      let data
      try {
        const text = await response.text()
        if (!text.trim()) {
          return { success: false, message: '服务器响应为空' }
        }
        data = JSON.parse(text)
      } catch (jsonError) {
        console.error('获取用户头像失败:', jsonError)
        return { success: false, message: '服务器响应格式错误' }
      }
      
      // 更新本地用户信息
      user.value = data.user
      localStorage.setItem('currentUser', JSON.stringify(data.user))
      
      return { success: true, message: data.message || '获取用户信息成功' }
    } catch (error) {
      console.error('Get user info error:', error)
      return { success: false, message: '获取用户信息失败，请重试' }
    }
  }

  // 更新头像
  const updateAvatar = async (formData: FormData): Promise<{ success: boolean; message: string }> => {
    try {
      // 添加用户名到formData
      if (user.value?.username) {
        formData.append('username', user.value.username);
      }
      
      const response = await fetch('/api/auth/update-avatar', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
        body: formData
      })

      const data = await response.json()
      
      if (!response.ok) {
        return { success: false, message: data.detail || '头像更新失败' }
      }
      
      // 更新本地用户信息
      if (user.value) {
        user.value.avatar = data.avatar || data.avatar_url
        localStorage.setItem('currentUser', JSON.stringify(user.value))
      }
      
      return { success: true, message: data.message || '头像更新成功' }
    } catch (error) {
      console.error('Update avatar error:', error)
      return { success: false, message: '头像更新失败，请重试' }
    }
  }


  // 初始化
  initializeAuth()

  return {
    user,
    token,
    isAuthenticated,
    initializeAuth,
    validateToken,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    verifyResetToken,
    getPassword,
    changePassword,
    updateAvatar,
    getUserInfo,
  }
})