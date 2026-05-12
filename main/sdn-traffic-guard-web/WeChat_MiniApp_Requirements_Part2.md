# SDN 网络管理平台 - 微信小程序需求文档（第二部分）

## 9. 项目结构

### 9.1 小程序前端目录结构
```
miniapp/
├── pages/
│   ├── index/index.vue         # 首页/仪表板
│   ├── anomalies/list.vue      # 异常列表
│   ├── anomalies/detail.vue    # 异常详情
│   ├── flowstats/list.vue      # 流表列表
│   ├── attacks/list.vue        # 攻击会话列表
│   ├── devices/list.vue        # 设备列表
│   ├── profile/index.vue       # 个人中心
│   └── login/index.vue         # 登录页
├── components/
│   ├── AnomalyCard.vue         # 异常卡片
│   ├── FlowCard.vue            # 流表卡片
│   ├── StatCard.vue            # 统计卡片
│   ├── Loading.vue             # 加载组件
│   └── EmptyState.vue          # 空状态
├── stores/
│   ├── auth.ts                 # 认证状态
│   ├── anomaly.ts              # 异常状态
│   ├── flow.ts                 # 流量状态
│   ├── attack.ts               # 攻击状态
│   └── device.ts               # 设备状态
├── api/
│   ├── index.ts                # API 实例
│   ├── auth.ts                 # 认证 API
│   ├── anomaly.ts              # 异常 API
│   ├── flow.ts                 # 流量 API
│   └── types.ts                # 类型定义
├── services/
│   ├── websocket.ts            # WebSocket 服务
│   ├── notification.ts         # 通知服务
│   └── storage.ts              # 本地存储
├── utils/
│   ├── format.ts               # 格式化工具
│   ├── request.ts              # 请求工具
│   └── constants.ts            # 常量定义
├── App.vue
├── main.ts
└── package.json
```

### 9.2 后端新增模块结构
```
backend/
├── auth/
│   ├── wechat.py               # 微信认证
│   ├── jwt_handler.py          # JWT 处理
│   ├── models.py               # 认证模型
│   └── dependencies.py         # 依赖注入
├── notifications/
│   ├── websocket_manager.py    # WebSocket 管理
│   ├── push_service.py         # 推送服务
│   ├── models.py               # 通知模型
│   └── events.py               # 事件处理
├── miniapp/
│   ├── routes.py               # 小程序路由
│   ├── schemas.py              # 数据模型
│   └── utils.py                # 工具函数
└── config/
    └── wechat_config.py        # 微信配置
```

---

## 10. 核心功能实现

### 10.1 微信登录流程

**前端**:
```typescript
// 1. 调用 wx.login() 获取 code
// 2. 发送 code 到后端
// 3. 后端验证 code，返回 token
// 4. 保存 token 到本地存储
// 5. 跳转到首页
```

**后端**:
```python
# 1. 接收 code
# 2. 调用微信 API 验证 code，获取 openid
# 3. 查询数据库，匹配管理员账户
# 4. 生成 JWT token
# 5. 返回 token 和用户信息
```

### 10.2 异常处理流程

**前端**:
```typescript
// 1. 显示异常列表
// 2. 用户点击"标记为已处理"
// 3. 发送 PUT 请求到后端
// 4. 后端更新数据库
// 5. 从列表中移除异常
```

**后端**:
```python
# 1. 接收 PUT 请求
# 2. 验证 token
# 3. 更新数据库：
#    - status: pending → handled
#    - handled_by: admin
#    - handled_at: NOW()
# 4. 返回成功响应
```

### 10.3 实时通知流程

**WebSocket 连接**:
```
1. 小程序连接到 /ws/notifications?token={token}
2. 后端验证 token
3. 建立连接，保存连接对象
4. 当有新异常时，后端推送通知
5. 小程序接收通知，更新 UI
```

**推送内容**:
```json
{
  "type": "anomaly_detected",
  "data": {
    "id": 1,
    "anomaly_type": "IP配置异常",
    "device_id": "192.168.1.100",
    "severity": "high"
  }
}
```

---

## 11. 关键技术点

### 11.1 前端技术

#### uni-app 框架
- 跨平台开发（iOS、Android、小程序）
- 一套代码多端运行
- 丰富的原生 API 调用

#### Pinia 状态管理
```typescript
// 示例：异常状态管理
export const useAnomalyStore = defineStore('anomaly', {
  state: () => ({
    anomalies: [],
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchAnomalies() {
      this.loading = true
      try {
        const response = await api.anomaly.getList()
        this.anomalies = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    
    async markAsResolved(anomalyId: number) {
      await api.anomaly.update(anomalyId, { status: 'handled' })
      this.anomalies = this.anomalies.filter(a => a.id !== anomalyId)
    }
  }
})
```

#### WebSocket 实时通知
```typescript
// 示例：WebSocket 连接
class WebSocketService {
  private ws: WebSocket
  
  connect(token: string) {
    this.ws = new WebSocket(`wss://api.example.com/ws/notifications?token=${token}`)
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.handleNotification(message)
    }
  }
  
  private handleNotification(message: any) {
    if (message.type === 'anomaly_detected') {
      // 推送通知
      uni.showToast({ title: '检测到新异常' })
      // 更新状态
      useAnomalyStore().fetchAnomalies()
    }
  }
}
```

### 11.2 后端技术

#### FastAPI WebSocket 支持
```python
from fastapi import WebSocket

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    # 验证 token
    user = verify_token(token)
    # 添加到连接管理器
    manager.connect(user.id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息
    except WebSocketDisconnect:
        manager.disconnect(user.id)
```

#### 异常检测事件推送
```python
# 当 RYU 检测到异常时
def on_anomaly_detected(anomaly_data):
    # 保存到数据库
    db.device_anomalies.insert(anomaly_data)
    
    # 推送到所有连接的管理员
    notification = {
        "type": "anomaly_detected",
        "data": anomaly_data
    }
    manager.broadcast(notification)
```

---

## 12. 实现步骤

### 第一阶段：后端 API 开发（2-3 周）

**第 1 周**:
- [ ] 设置微信 SDK 和配置
- [ ] 实现微信登录 API
- [ ] 实现 JWT token 生成和验证
- [ ] 创建数据库表（wechat_users、push_subscriptions）

**第 2 周**:
- [ ] 实现异常 API（GET、PUT）
- [ ] 实现流表 API（GET）
- [ ] 实现攻击会话 API（GET）
- [ ] 实现设备 API（GET）

**第 3 周**:
- [ ] 实现 WebSocket 连接管理
- [ ] 实现推送服务
- [ ] 实现仪表板 API（统计数据）
- [ ] API 测试和优化

### 第二阶段：小程序前端开发（2-3 周）

**第 1 周**:
- [ ] 项目初始化和配置
- [ ] 实现登录页面
- [ ] 实现首页仪表板
- [ ] 实现状态管理（Pinia）

**第 2 周**:
- [ ] 实现异常列表和详情页
- [ ] 实现流表列表和详情页
- [ ] 实现攻击会话列表
- [ ] 实现设备列表

**第 3 周**:
- [ ] 实现个人中心
- [ ] 实现 WebSocket 连接
- [ ] 实现推送通知处理
- [ ] UI 优化和适配

### 第三阶段：集成和测试（1-2 周）

- [ ] 前后端集成测试
- [ ] 功能测试
- [ ] 性能测试
- [ ] 安全测试

### 第四阶段：微信审核和发布（1 周）

- [ ] 提交小程序代码
- [ ] 等待微信审核
- [ ] 修复审核问题
- [ ] 发布上线

---

## 13. 成本估算

### 人力成本
- 后端开发：1 人 × 3 周 = 3 人周
- 前端开发：1 人 × 3 周 = 3 人周
- 测试：1 人 × 2 周 = 2 人周
- **总计**: 8 人周

### 服务成本
- 微信小程序认证：¥300（一次性）
- 服务器升级（支持 WebSocket）：¥50/月
- 数据库扩容：¥20/月
- **总计**: ¥370 + ¥70/月

---

## 14. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|--------|
| 微信审核不通过 | 中 | 高 | 提前了解审核规则，准备备选方案 |
| 网络延迟导致推送延迟 | 低 | 中 | 实现重试机制和本地缓存 |
| 数据库性能瓶颈 | 低 | 中 | 实现缓存和数据库优化 |
| 安全漏洞 | 低 | 高 | 进行安全审计和渗透测试 |

---

## 15. 成功指标

- ✅ 小程序成功上线
- ✅ 异常处理响应时间 < 2 秒
- ✅ WebSocket 连接稳定率 > 99%
- ✅ 用户满意度 > 4.5 星
- ✅ 日活跃用户 > 50%

---

## 16. 后续优化方向

### 短期（1-2 个月）
- 添加更多图表和数据可视化
- 实现离线模式
- 优化加载速度

### 中期（3-6 个月）
- 添加数据导出功能
- 实现自定义告警规则
- 添加多语言支持

### 长期（6-12 个月）
- 开发 iOS 原生应用
- 开发 Android 原生应用
- 实现 AI 异常预测

---

## 17. 总结

这份需求文档提供了一个完整的微信小程序开发方案，包括：

✅ **清晰的功能需求** - 涵盖认证、异常处理、流量分析、攻击监控等
✅ **完整的技术架构** - 前后端分离，支持实时通知
✅ **详细的 API 设计** - RESTful + WebSocket
✅ **可行的实现计划** - 分阶段开发，时间可控
✅ **风险评估** - 提前识别和规避风险

**建议立即启动第一阶段后端开发，预计 11 月底完成全部功能。**

---

**文档完成！** 两部分合计共 30+ 页详细需求文档。
