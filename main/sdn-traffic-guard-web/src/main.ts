import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createDiscreteApi } from 'naive-ui'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

// 创建Naive UI的离散API
const { message, notification, dialog, loadingBar } = createDiscreteApi([
  'message',
  'notification',
  'dialog',
  'loadingBar'
])

// 将API挂载到全局属性
app.config.globalProperties.$message = message
app.config.globalProperties.$notification = notification
app.config.globalProperties.$dialog = dialog
app.config.globalProperties.$loadingBar = loadingBar

app.use(pinia)
app.use(router)

// 确保应用挂载
app.mount('#app')

console.log('Vue app mounted successfully')
