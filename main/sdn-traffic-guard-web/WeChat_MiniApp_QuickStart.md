# 微信小程序快速开发指南

## 🎯 一句话总结

为 SDN 网络管理平台开发微信小程序，让管理员通过手机随时查看网络状态、处理异常、分析流量。

---

## 📱 核心功能（6 大模块）

| 模块 | 功能 | 优先级 |
|------|------|--------|
| **认证** | 微信登录、账号密码登录、Token 管理 | 🔴 必须 |
| **异常处理** | 异常列表、详情、一键标记已处理 | 🔴 必须 |
| **流量分析** | TOP 10 流表、流量趋势、协议分布 | 🟡 重要 |
| **攻击监控** | 攻击会话列表、快速操作 | 🟡 重要 |
| **设备管理** | 设备列表、设备详情、异常统计 | 🟢 可选 |
| **个人中心** | 用户信息、设置、通知管理 | 🟢 可选 |

---

## 🏗️ 技术栈（一页纸版本）

### 前端
```
uni-app 3.0+ (Vue 3 + TypeScript)
├── Pinia (状态管理)
├── uni-ui (UI 组件)
├── axios (HTTP 请求)
├── echarts (图表)
└── dayjs (时间处理)
```

### 后端
```
FastAPI 0.104+
├── PyJWT (认证)
├── wechat-sdk (微信集成)
├── websockets (实时推送)
├── SQLAlchemy (数据库)
└── PyMySQL (MySQL 驱动)
```

### 数据库
```
MySQL 8.0+
├── wechat_users (微信用户绑定)
├── push_subscriptions (推送订阅)
├── operation_logs (操作日志)
└── notification_history (通知历史)
```

---

## 🚀 快速开发步骤

### 第 1 步：后端准备（第 1 周）

#### 1.1 安装依赖
```bash
pip install wechat-sdk PyJWT python-jose websockets python-socketio
```

#### 1.2 创建微信认证模块
```python
# backend/auth/wechat.py
class WeChatClient:
    def verify_code(self, code: str) -> dict:
        """验证授权码"""
        # 调用微信 API
        pass
    
    def get_user_info(self, openid: str) -> dict:
        """获取用户信息"""
        pass
```

#### 1.3 创建 JWT 处理
```python
# backend/auth/jwt_handler.py
def create_token(user_id: int) -> str:
    """生成 JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

#### 1.4 创建数据库表
```sql
CREATE TABLE wechat_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 1.5 新增 API 路由
```python
# backend/miniapp/routes.py

@router.post("/auth/wechat-login")
async def wechat_login(request: WeChatLoginRequest):
    """微信登录"""
    # 1. 验证 code
    # 2. 获取 openid
    # 3. 查询或创建用户
    # 4. 生成 token
    # 5. 返回响应

@router.get("/device-anomalies")
async def get_anomalies(current_user = Depends(get_current_user)):
    """获取异常列表"""
    # 从数据库查询
    # 返回分页结果

@router.put("/device-anomalies/{anomaly_id}")
async def update_anomaly(anomaly_id: int, current_user = Depends(get_current_user)):
    """标记异常为已处理"""
    # 更新数据库
    # 返回成功响应
```

### 第 2 步：前端开发（第 2 周）

#### 2.1 项目初始化
```bash
# 使用 HBuilderX 创建 uni-app 项目
# 或使用 CLI
npm create vite@latest miniapp -- --template vue-ts
cd miniapp
npm install
```

#### 2.2 创建登录页面
```vue
<!-- pages/login/index.vue -->
<template>
  <view class="login-container">
    <button @click="wechatLogin">微信登录</button>
    <button @click="accountLogin">账号登录</button>
  </view>
</template>

<script setup lang="ts">
async function wechatLogin() {
  const { code } = await uni.login()
  const response = await api.auth.wechatLogin({ code })
  uni.setStorageSync('token', response.token)
  uni.navigateTo({ url: '/pages/index/index' })
}
</script>
```

#### 2.3 创建首页仪表板
```vue
<!-- pages/index/index.vue -->
<template>
  <view class="dashboard">
    <view class="stat-card">
      <text>活跃流表: {{ stats.activeFlows }}</text>
    </view>
    <view class="stat-card">
      <text>异常数量: {{ stats.anomalies }}</text>
    </view>
    <view class="stat-card">
      <text>攻击会话: {{ stats.attacks }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAnomalyStore } from '@/stores/anomaly'

const stats = ref({
  activeFlows: 0,
  anomalies: 0,
  attacks: 0
})

onMounted(async () => {
  const anomalyStore = useAnomalyStore()
  await anomalyStore.fetchAnomalies()
  stats.value.anomalies = anomalyStore.anomalies.length
})
</script>
```

#### 2.4 创建异常列表页面
```vue
<!-- pages/anomalies/list.vue -->
<template>
  <view class="anomaly-list">
    <view 
      v-for="anomaly in anomalies" 
      :key="anomaly.id"
      class="anomaly-card"
      @click="goDetail(anomaly.id)"
    >
      <text>{{ anomaly.anomaly_type }}</text>
      <text>{{ anomaly.device_id }}</text>
      <text :class="`severity-${anomaly.severity}`">
        {{ anomaly.severity }}
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAnomalyStore } from '@/stores/anomaly'

const anomalies = ref([])
const anomalyStore = useAnomalyStore()

onMounted(async () => {
  await anomalyStore.fetchAnomalies()
  anomalies.value = anomalyStore.anomalies
})

function goDetail(anomalyId: number) {
  uni.navigateTo({ 
    url: `/pages/anomalies/detail?id=${anomalyId}` 
  })
}
</script>
```

#### 2.5 创建异常详情页面
```vue
<!-- pages/anomalies/detail.vue -->
<template>
  <view class="detail-container">
    <view class="detail-info">
      <text>异常类型: {{ anomaly.anomaly_type }}</text>
      <text>设备ID: {{ anomaly.device_id }}</text>
      <text>描述: {{ anomaly.description }}</text>
      <text>严重程度: {{ anomaly.severity }}</text>
      <text>检测时间: {{ formatTime(anomaly.detected_at) }}</text>
      <text>状态: {{ anomaly.status }}</text>
    </view>
    
    <button 
      v-if="anomaly.status === 'pending'"
      @click="markAsResolved"
      class="btn-primary"
    >
      标记为已处理
    </button>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAnomalyStore } from '@/stores/anomaly'
import { formatTime } from '@/utils/format'

const route = useRoute()
const anomalyStore = useAnomalyStore()
const anomaly = ref(null)

onMounted(async () => {
  const id = route.query.id
  anomaly.value = await anomalyStore.getAnomalyDetail(id)
})

async function markAsResolved() {
  await anomalyStore.markAsResolved(anomaly.value.id)
  uni.showToast({ title: '已标记为已处理' })
  uni.navigateBack()
}
</script>
```

#### 2.6 创建状态管理
```typescript
// stores/anomaly.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useAnomalyStore = defineStore('anomaly', () => {
  const anomalies = ref([])
  const loading = ref(false)
  
  async function fetchAnomalies() {
    loading.value = true
    try {
      const response = await api.anomaly.getList()
      anomalies.value = response.data
    } finally {
      loading.value = false
    }
  }
  
  async function getAnomalyDetail(id: number) {
    const response = await api.anomaly.getDetail(id)
    return response.data
  }
  
  async function markAsResolved(id: number) {
    await api.anomaly.update(id, { status: 'handled' })
    anomalies.value = anomalies.value.filter(a => a.id !== id)
  }
  
  return {
    anomalies,
    loading,
    fetchAnomalies,
    getAnomalyDetail,
    markAsResolved
  }
})
```

#### 2.7 创建 API 模块
```typescript
// api/index.ts
import axios from 'axios'

const instance = axios.create({
  baseURL: 'http://localhost:8001/v1'
})

// 请求拦截器
instance.interceptors.request.use((config) => {
  const token = uni.getStorageSync('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default instance

// api/anomaly.ts
import instance from './index'

export const anomaly = {
  getList: (params?: any) => instance.get('/device-anomalies', { params }),
  getDetail: (id: number) => instance.get(`/device-anomalies/${id}`),
  update: (id: number, data: any) => instance.put(`/device-anomalies/${id}`, data)
}
```

### 第 3 步：WebSocket 实时推送（第 3 周）

#### 3.1 后端 WebSocket 实现
```python
# backend/notifications/websocket_manager.py
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        del self.active_connections[user_id]
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

# backend/miniapp/routes.py
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = verify_token(token)
    await manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id)
```

#### 3.2 前端 WebSocket 连接
```typescript
// services/websocket.ts
export class WebSocketService {
  private ws: WebSocket | null = null
  
  connect(token: string) {
    this.ws = new WebSocket(
      `wss://api.example.com/ws/notifications?token=${token}`
    )
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.handleMessage(message)
    }
  }
  
  private handleMessage(message: any) {
    if (message.type === 'anomaly_detected') {
      // 推送通知
      uni.showToast({ title: '检测到新异常' })
      // 更新状态
      useAnomalyStore().fetchAnomalies()
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close()
    }
  }
}
```

---

## 📊 API 速查表

### 认证
```
POST /v1/auth/wechat-login
POST /v1/auth/login
POST /v1/auth/refresh-token
```

### 异常
```
GET /v1/device-anomalies
GET /v1/device-anomalies/{id}
PUT /v1/device-anomalies/{id}
```

### 流量
```
GET /v1/flowstats/top10
GET /v1/flowstats/trend
```

### 攻击
```
GET /v1/attack-sessions
GET /v1/attack-sessions/{id}
```

### 设备
```
GET /v1/devices
GET /v1/devices/{id}
```

### 实时
```
WebSocket /ws/notifications
```

---

## 🎨 UI 布局参考

### 首页仪表板
```
┌─────────────────────────────┐
│  活跃流表 │ 异常数量 │ 攻击  │
│   1,234   │   12    │  5   │
├─────────────────────────────┤
│  流量趋势图 (24小时)         │
├─────────────────────────────┤
│  异常类型分布 (饼图)         │
├─────────────────────────────┤
│  最近异常                    │
│  - IP配置异常 (192.168.1.100)│
│  - MAC冲突 (00:00:00:00:00:04)│
└─────────────────────────────┘
```

### 异常列表
```
┌─────────────────────────────┐
│ 筛选: 状态 ▼ 严重程度 ▼     │
├─────────────────────────────┤
│ ▶ IP配置异常                │
│   192.168.1.100 | 高 | 待处理│
│   2025-11-17 03:19          │
├─────────────────────────────┤
│ ▶ MAC冲突                   │
│   00:00:00:00:00:04 | 中 | 待处理│
│   2025-11-17 02:45          │
└─────────────────────────────┘
```

---

## ⏱️ 时间表

| 周 | 任务 | 交付物 |
|----|------|--------|
| 第 1 周 | 后端 API | 微信登录、异常 API、WebSocket |
| 第 2 周 | 前端页面 | 登录、首页、异常、流表、个人中心 |
| 第 3 周 | 集成测试 | 功能测试、性能测试、安全测试 |
| 第 4 周 | 上线发布 | 微信审核、修复问题、正式发布 |

---

## ✅ 检查清单

### 后端
- [ ] 微信 SDK 集成
- [ ] JWT token 实现
- [ ] 异常 API 完成
- [ ] 流表 API 完成
- [ ] WebSocket 实现
- [ ] 数据库表创建
- [ ] 错误处理完善
- [ ] 日志记录完善

### 前端
- [ ] 登录页面完成
- [ ] 首页仪表板完成
- [ ] 异常列表完成
- [ ] 异常详情完成
- [ ] 流表页面完成
- [ ] 个人中心完成
- [ ] WebSocket 连接完成
- [ ] 推送通知处理完成

### 测试
- [ ] 功能测试
- [ ] 性能测试
- [ ] 安全测试
- [ ] 兼容性测试

### 上线
- [ ] 代码审查
- [ ] 提交微信审核
- [ ] 修复审核问题
- [ ] 发布上线

---

## 🔗 相关文档

- 📄 `WeChat_MiniApp_Requirements_Part1.md` - 详细需求文档（第一部分）
- 📄 `WeChat_MiniApp_Requirements_Part2.md` - 详细需求文档（第二部分）
- 📄 `WeChat_MiniApp_TechStack.md` - 技术栈详解

---

**祝开发顺利！** 🚀
