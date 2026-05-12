# 微信小程序技术方案总结

## 📱 项目概览

**目标**: 为 SDN 网络管理平台开发微信小程序，让管理员可以随时随地查看网络状态、处理异常。

**核心价值**:
- 🎯 移动端实时监控
- 🎯 一键处理异常
- 🎯 实时推送通知
- 🎯 与 Web 端数据同步

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────┐
│        微信小程序 (uni-app)             │
│  - Vue 3 + TypeScript                   │
│  - Pinia 状态管理                       │
│  - uni-ui 组件库                        │
└──────────────────┬──────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────┐
│      FastAPI 后端 (localhost:8001)      │
│  - 微信认证                             │
│  - JWT Token 管理                       │
│  - WebSocket 实时推送                   │
│  - 数据代理和聚合                       │
└──────────────────┬──────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────┐
│   RYU 控制器 (192.168.126.128:8080)    │
│  - 异常检测                             │
│  - 流表统计                             │
│  - 攻击监控                             │
│  - 设备管理                             │
└──────────────────┬──────────────────────┘
                   │ MySQL
┌──────────────────▼──────────────────────┐
│           数据库                        │
│  - device_anomalies                    │
│  - flow_statistics                     │
│  - attack_sessions                     │
│  - wechat_users (新)                   │
│  - push_subscriptions (新)             │
│  - operation_logs (新)                 │
│  - notification_history (新)           │
└─────────────────────────────────────────┘
```

---

## 🛠️ 技术栈详解

### 前端技术栈

#### 核心框架
| 技术 | 版本 | 说明 |
|------|------|------|
| **uni-app** | 3.0+ | 跨平台小程序框架 |
| **Vue 3** | 3.3+ | 渐进式 UI 框架 |
| **TypeScript** | 5.0+ | 类型安全编程 |
| **Pinia** | 2.1+ | 轻量级状态管理 |

#### UI 和工具库
| 库 | 版本 | 用途 |
|----|------|------|
| **uni-ui** | 1.4+ | 官方 UI 组件库 |
| **axios** | 1.6+ | HTTP 请求库 |
| **dayjs** | 1.11+ | 轻量级时间库 |
| **echarts** | 5.4+ | 图表库 |
| **crypto-js** | 4.1+ | 加密库 |

#### 开发工具
| 工具 | 版本 | 用途 |
|------|------|------|
| **HBuilderX** | 4.0+ | 官方 IDE |
| **微信开发者工具** | 最新 | 调试工具 |
| **npm** | 9.0+ | 包管理器 |
| **Vite** | 5.0+ | 构建工具 |

### 后端技术栈

#### 核心框架
| 库 | 版本 | 用途 |
|----|------|------|
| **FastAPI** | 0.104+ | 高性能 Web 框架 |
| **Pydantic** | 2.5+ | 数据验证 |
| **SQLAlchemy** | 2.0+ | ORM 框架 |
| **PyMySQL** | 1.1+ | MySQL 驱动 |

#### 新增依赖
| 库 | 版本 | 用途 |
|----|------|------|
| **wechat-sdk** | 1.8+ | 微信 SDK |
| **PyJWT** | 2.8+ | JWT 处理 |
| **python-jose** | 3.3+ | 加密算法 |
| **websockets** | 12.0+ | WebSocket 支持 |
| **python-socketio** | 5.9+ | Socket.IO 库 |

---

## 📋 功能模块

### 1️⃣ 认证模块

#### 微信登录
```
流程:
  用户点击"微信登录"
    ↓
  调用 wx.login() 获取 code
    ↓
  发送 code 到后端
    ↓
  后端调用微信 API 验证 code
    ↓
  获取 openid，查询数据库
    ↓
  生成 JWT token
    ↓
  返回 token 和用户信息
    ↓
  小程序保存 token，跳转首页
```

#### Token 管理
- 自动刷新过期 token
- 请求拦截器自动添加 Authorization header
- 登出时清除本地 token

### 2️⃣ 异常处理模块

#### 异常列表
- 显示所有未处理的异常
- 支持按状态、严重程度筛选
- 支持搜索和排序
- 下拉刷新、上拉加载更多

#### 异常详情
- 显示异常的完整信息
- 一键标记为已处理
- 操作日志记录

#### 实时通知
- WebSocket 推送新异常
- 本地通知提醒
- 点击通知跳转详情页

### 3️⃣ 流量分析模块

#### 流表统计
- TOP 10 流表显示
- 按数据量排序
- 显示源/目标 IP、端口、协议等

#### 流量趋势
- 过去 24 小时流量曲线
- 协议分布饼图
- 源 IP 分布

### 4️⃣ 攻击监控模块

#### 攻击会话列表
- 显示所有攻击会话
- 按状态筛选（active、blocked、resolved）
- 显示攻击类型、源/目标 IP

#### 快速操作
- 阻止攻击源
- 隔离受害设备
- 标记为已处理

### 5️⃣ 设备管理模块

#### 设备列表
- 显示所有设备
- 按类型筛选（host、switch、router）
- 显示在线状态和异常数量

#### 设备详情
- 基本信息（IP、MAC、类型）
- 在线状态和心跳时间
- 相关异常列表
- 流量统计

### 6️⃣ 个人中心模块

#### 用户信息
- 头像、用户名、邮箱
- 角色和权限
- 最后登录时间

#### 设置
- 修改密码
- 通知设置（推送、声音、震动）
- 数据刷新频率
- 清除缓存

---

## 🔌 API 接口设计

### 认证相关

#### POST /v1/auth/wechat-login
微信登录
```json
请求:
{
  "code": "string",
  "user_info": {
    "nickName": "string",
    "avatarUrl": "string"
  }
}

响应:
{
  "success": true,
  "token": "eyJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  },
  "expires_in": 86400
}
```

#### POST /v1/auth/login
账号密码登录
```json
请求:
{
  "username": "admin",
  "password": "password123"
}

响应:
{
  "success": true,
  "token": "eyJhbGc...",
  "user": {...},
  "expires_in": 86400
}
```

#### POST /v1/auth/refresh-token
刷新 token
```json
请求:
{
  "refresh_token": "string"
}

响应:
{
  "success": true,
  "token": "eyJhbGc...",
  "expires_in": 86400
}
```

### 异常相关

#### GET /v1/device-anomalies
获取异常列表
```
查询参数:
  - status: pending | handled
  - severity: low | medium | high
  - page: 1
  - limit: 20

响应:
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### PUT /v1/device-anomalies/{anomaly_id}
标记异常为已处理
```json
请求:
{
  "status": "handled"
}

响应:
{
  "success": true,
  "message": "异常已标记为已处理",
  "data": {
    "id": 1,
    "status": "handled",
    "handled_by": "admin",
    "handled_at": "2025-11-17T03:25:00Z"
  }
}
```

### 流量相关

#### GET /v1/flowstats/top10
获取流表统计
```
查询参数:
  - limit: 10

响应:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "src_ip": "192.168.1.10",
      "dst_ip": "8.8.8.8",
      "bytes": 1288490188,
      "packets": 1234567,
      "duration": 9000
    }
  ]
}
```

#### GET /v1/flowstats/trend
获取流量趋势
```
查询参数:
  - hours: 24

响应:
{
  "success": true,
  "data": {
    "timestamps": ["2025-11-16T03:00:00Z", ...],
    "bytes": [1024000, 2048000, ...],
    "packets": [1000, 2000, ...]
  }
}
```

### 实时通知

#### WebSocket /ws/notifications
实时推送通知
```
连接: wss://api.example.com/ws/notifications?token={token}

推送消息:
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

## 📊 数据库设计

### 新增表

#### wechat_users（微信用户绑定）
```sql
CREATE TABLE wechat_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### push_subscriptions（推送订阅）
```sql
CREATE TABLE push_subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    device_token VARCHAR(500),
    device_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### operation_logs（操作日志）
```sql
CREATE TABLE operation_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    operation_type VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id INT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### notification_history（通知历史）
```sql
CREATE TABLE notification_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_type VARCHAR(100),
    title VARCHAR(255),
    content TEXT,
    data JSON,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🚀 开发计划

### 第一阶段：后端 API（2-3 周）
- [ ] 微信认证集成
- [ ] JWT token 管理
- [ ] 异常 API 开发
- [ ] 流表 API 开发
- [ ] WebSocket 实现
- [ ] 数据库表创建

### 第二阶段：前端开发（2-3 周）
- [ ] 项目初始化
- [ ] 登录页面
- [ ] 首页仪表板
- [ ] 异常管理页面
- [ ] 流量分析页面
- [ ] 个人中心

### 第三阶段：集成测试（1-2 周）
- [ ] 前后端集成
- [ ] 功能测试
- [ ] 性能测试
- [ ] 安全测试

### 第四阶段：上线发布（1 周）
- [ ] 代码审查
- [ ] 提交微信审核
- [ ] 修复审核问题
- [ ] 正式发布

**总计**: 7-11 周

---

## 💰 成本估算

### 人力成本
- 后端开发：1 人 × 3 周 = 3 人周
- 前端开发：1 人 × 3 周 = 3 人周
- 测试：1 人 × 2 周 = 2 人周
- **总计**: 8 人周

### 服务成本
- 微信小程序认证：¥300（一次性）
- 服务器升级：¥50/月
- 数据库扩容：¥20/月
- **总计**: ¥370 + ¥70/月

---

## ⚠️ 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|-----|
| 微信审核不通过 | 中 | 高 | 提前了解规则 |
| 网络延迟 | 低 | 中 | 实现重试机制 |
| 数据库性能 | 低 | 中 | 缓存优化 |
| 安全漏洞 | 低 | 高 | 安全审计 |

---

## ✅ 成功指标

- ✅ 小程序成功上线
- ✅ 异常处理响应 < 2 秒
- ✅ WebSocket 稳定率 > 99%
- ✅ 用户满意度 > 4.5 星
- ✅ 日活跃用户 > 50%

---

## 📝 总结

这是一个完整的微信小程序开发方案，包括：

✅ **清晰的功能需求** - 覆盖认证、异常、流量、攻击、设备等
✅ **完整的技术架构** - 前后端分离，支持实时通知
✅ **详细的 API 设计** - RESTful + WebSocket
✅ **可行的实现计划** - 分阶段开发，时间可控
✅ **风险评估** - 提前识别和规避

**建议立即启动后端开发，预计 11 月底完成全部功能。**

---

**生成时间**: 2025-11-17 03:30 UTC+08:00
