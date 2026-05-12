import { Ref } from 'vue'

export interface User {
  id: string
  username: string
  password: string
  email?: string
  avatar?: string
  role: string
  createdAt: string
}

export interface UserStore {
  user: Ref<User | null>
  token: Ref<string | null>
  isAuthenticated: Ref<boolean>
  initializeAuth: () => void
  validateToken: () => Promise<boolean>
  login: (username: string, password: string) => Promise<{ success: boolean; message: string }>
  register: (username: string, password: string, email?: string, avatar?: string) => Promise<{ success: boolean; message: string }>
  logout: () => void
  forgotPassword: (username: string, email: string) => Promise<{ success: boolean; message: string; resetToken?: string }>
  resetPassword: (token: string, newPassword: string) => Promise<{ success: boolean; message: string }>
  verifyResetToken: (token: string) => Promise<{ success: boolean; message: string; userId?: string }>
  getPassword: (username: string) => Promise<{ success: boolean; message: string; password?: string }>
  changePassword: (username: string, oldPassword: string, newPassword: string) => Promise<{ success: boolean; message: string }>
  updateAvatar: (formData: FormData) => Promise<{ success: boolean; message: string }>
  getUserInfo: () => Promise<{ success: boolean; message: string }>
}