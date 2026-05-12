# SDN 网络管理平台 - 微信小程序需求文档（第一部分）

## 📋 文档信息
- **项目名称**: SDN 网络管理平台微信小程序
- **版本**: 1.0
- **创建日期**: 2025-11-17
- **目标用户**: 网络管理员
- **主要功能**: 移动端实时监控、异常处理、流量分析

---

## 1. 项目概述

### 1.1 项目背景
现有的 SDN 网络管理平台是一个 Web 应用，管理员需要在电脑前才能进行操作。为了提高管理效率，需要开发微信小程序版本，让管理员可以随时随地通过手机查看网络状态、处理异常。

### 1.2 项目目标
- ✅ 提供移动端实时网络监控
- ✅ 支持异常处理（标记为已处理）
- ✅ 实时流量统计和分析
- ✅ 攻击会话监控
- ✅ 设备状态查看
- ✅ 消息推送通知

### 1.3 核心价值
- 🎯 **随时随地管理**: 不受地点限制
- 🎯 **实时通知**: 异常发生时立即推送
- 🎯 **快速响应**: 一键处理异常
- 🎯 **数据同步**: 与 Web 端数据实时同步

---

## 2. 功能需求

### 2.1 用户认证模块

#### 2.1.1 微信授权登录
```
功能: 使用微信授权快速登录
流程:
  1. 用户点击"微信登录"
  2. 调用 wx.login() 获取 code
  3. 将 code 发送到后端
  4. 后端调用微信服务器验证 code，获取 openid
  5. 后端查询数据库，匹配管理员账户
  6. 返回 token 和用户信息
  7. 小程序保存 token 到本地存储
```

#### 2.1.2 账号密码登录
```
功能: 备用登录方式
流程:
  1. 输入用户名和密码
  2. 发送到后端验证
  3. 验证成功返回 token
  4. 保存 token 到本地存储
```

#### 2.1.3 Token 管理
- 自动刷新过期 token
- 登出时清除本地 token
- 请求拦截器自动添加 Authorization header

---

### 2.2 首页 - 仪表板（Dashboard）

#### 2.2.1 实时数据卡片
```
显示内容:
  ┌─────────────────────────────────┐
  │ 📊 网络概览                      │
  ├─────────────────────────────────┤
  │ 活跃流表数: 1,234               │
  │ 异常数量: 12                    │
  │ 攻击会话: 5                     │
  │ 在线设备: 45                    │
  └─────────────────────────────────┘
```

#### 2.2.2 实时图表
- 流量趋势图（折线图）
- 异常类型分布（饼图）
- 攻击会话时间分布（柱状图）

#### 2.2.3 刷新机制
- 下拉刷新: 手动刷新数据
- 自动刷新: 每 30 秒自动更新一次
- WebSocket: 实时推送关键指标变化

---

### 2.3 设备异常模块（Device Anomalies）

#### 2.3.1 异常列表
```
显示字段:
  - 异常类型: IP配置异常、MAC冲突、黑名单等
  - 设备类型: host、switch 等
  - 设备ID: IP 地址或 MAC 地址
  - 严重程度: high、medium、low
  - 检测时间: 2025-11-17 03:19:00
  - 状态: pending、handled
  - 处理人: admin
  - 处理时间: 2025-11-17 03:25:00

列表操作:
  - 上拉加载更多
  - 按状态筛选（pending/handled）
  - 按严重程度筛选
  - 搜索异常
```

#### 2.3.2 异常详情页
```
显示内容:
  ┌─────────────────────────────────┐
  │ 异常详情                        │
  ├─────────────────────────────────┤
  │ 异常类型: IP配置异常            │
  │ 设备ID: 192.168.1.100           │
  │ 描述: 主机IP不在合法网段        │
  │ 严重程度: 高                    │
  │ 检测时间: 2025-11-17 03:19:00   │
  │ 状态: pending                   │
  │                                 │
  │ [标记为已处理] [删除]            │
  └─────────────────────────────────┘

操作:
  - 标记为已处理: 更新 status=handled, handled_by=admin, handled_at=NOW()
  - 删除异常: 从数据库删除记录
  - 返回列表
```

#### 2.3.3 实时通知
- 新异常产生时推送通知
- 通知内容: "检测到新异常: IP配置异常 (192.168.1.100)"
- 点击通知跳转到异常详情页

---

### 2.4 流量分析模块（Flow Statistics）

#### 2.4.1 流表统计
```
显示内容:
  ┌─────────────────────────────────┐
  │ 流表统计 (TOP 10)               │
  ├─────────────────────────────────┤
  │ 1. 192.168.1.10 → 8.8.8.8       │
  │    数据量: 1.2 GB               │
  │    包数: 1,234,567              │
  │    持续时间: 2h 30m             │
  │                                 │
  │ 2. 192.168.1.20 → 1.1.1.1       │
  │    数据量: 890 MB               │
  │    包数: 987,654                │
  │    持续时间: 1h 45m             │
  │ ...                             │
  └─────────────────────────────────┘

操作:
  - 下拉刷新
  - 点击流表查看详情
  - 按数据量排序
```

#### 2.4.2 流表详情
```
显示内容:
  - 源IP/端口
  - 目标IP/端口
  - 协议类型
  - 数据量
  - 包数
  - 持续时间
  - 最后更新时间
```

---

### 2.5 攻击会话模块（Attack Sessions）

#### 2.5.1 会话列表
```
显示字段:
  - 攻击类型: DDoS、端口扫描、暴力破解等
  - 源IP: 攻击者IP
  - 目标IP: 被攻击目标
  - 检测时间: 2025-11-17 03:19:00
  - 状态: active、blocked、resolved
  - 处理措施: 已阻止、已隔离等

列表操作:
  - 上拉加载更多
  - 按状态筛选
  - 搜索攻击会话
```

---

### 2.6 设备管理模块（Devices）

#### 2.6.1 设备列表
```
显示字段:
  - 设备名称/IP
  - 设备类型: switch、host、router
  - MAC 地址
  - 在线状态: online、offline
  - 最后心跳时间
  - 异常数量

列表操作:
  - 上拉加载更多
  - 按设备类型筛选
  - 按在线状态筛选
  - 搜索设备
```

---

### 2.7 个人中心模块（Profile）

#### 2.7.1 用户信息
```
显示内容:
  - 头像
  - 用户名
  - 邮箱
  - 角色: 管理员
  - 最后登录时间
```

#### 2.7.2 设置
- 修改密码
- 通知设置（推送、声音、震动）
- 数据刷新频率设置
- 清除缓存

---

## 3. 技术架构

### 3.1 整体架构图
```
┌─────────────────────────────────────────────────────────┐
│                  微信小程序前端                          │
│  Pages: Dashboard, Anomalies, FlowStats, Attacks, etc   │
│  State: Pinia Store (auth, anomaly, flow, etc)          │
│  Network: HTTP + WebSocket                              │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│              FastAPI 后端 (localhost:8001)              │
│  新增端点:                                              │
│  - POST /v1/auth/wechat-login                          │
│  - GET /v1/auth/user-info                              │
│  - PUT /v1/device-anomalies/{id}                       │
│  - GET /v1/device-anomalies                            │
│  - GET /v1/flowstats                                   │
│  - GET /v1/attack-sessions                             │
│  - GET /v1/devices                                     │
│  - WebSocket /ws/notifications                         │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│         RYU 控制器 (192.168.126.128:8080)              │
│  - 异常检测和存储                                      │
│  - 流表统计                                            │
│  - 攻击会话检测                                        │
│  - 设备管理                                            │
└─────────────────────────────────────────────────────────┘
```

### 3.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **uni-app** | 3.0+ | 跨平台小程序框架 |
| **Vue 3** | 3.3+ | UI 框架 |
| **TypeScript** | 5.0+ | 类型安全 |
| **Pinia** | 2.1+ | 状态管理 |
| **uni-ui** | 1.4+ | UI 组件库 |
| **axios** | 1.6+ | HTTP 请求 |
| **dayjs** | 1.11+ | 时间处理 |
| **echarts** | 5.4+ | 图表库 |

### 3.3 后端技术栈

#### 3.3.1 新增依赖
```python
wechat-sdk==1.8.0          # 微信 SDK
requests==2.31.0           # HTTP 请求
PyJWT==2.8.0               # JWT token
python-jose==3.3.0         # 加密
websockets==12.0           # WebSocket 支持
python-socketio==5.9.0     # Socket.IO
```

#### 3.3.2 新增模块结构
```
backend/
├── auth/
│   ├── wechat.py           # 微信认证逻辑
│   ├── jwt_handler.py      # JWT 处理
│   └── models.py           # 认证模型
├── notifications/
│   ├── websocket_manager.py # WebSocket 管理
│   ├── push_service.py      # 推送服务
│   └── models.py            # 通知模型
└── miniapp/
    ├── routes.py            # 小程序专用路由
    └── schemas.py           # 小程序数据模型
```

---

## 4. 数据库扩展

### 4.1 新增表

```sql
-- 微信用户绑定表
CREATE TABLE wechat_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 设备推送订阅表
CREATE TABLE push_subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    device_token VARCHAR(500),
    device_type VARCHAR(50),  -- 'ios', 'android', 'wechat'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 操作日志表
CREATE TABLE operation_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    operation_type VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id INT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 通知历史表
CREATE TABLE notification_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_type VARCHAR(100),
    title VARCHAR(255),
    content TEXT,
    data JSON,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 5. API 接口设计

### 5.1 认证相关

#### 5.1.1 微信登录
```
POST /v1/auth/wechat-login
Content-Type: application/json

请求体:
{
  "code": "string",
  "user_info": {
    "nickName": "string",
    "avatarUrl": "string"
  }
}

响应 (200):
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  },
  "expires_in": 86400
}
```

### 5.2 设备异常相关

#### 5.2.1 获取异常列表
```
GET /v1/device-anomalies?status=pending&severity=high&page=1&limit=20
Authorization: Bearer {token}

响应 (200):
{
  "success": true,
  "data": [
    {
      "id": 1,
      "anomaly_type": "IP配置异常",
      "device_type": "host",
      "device_id": "192.168.1.100",
      "description": "主机IP不在合法网段",
      "severity": "high",
      "detected_at": "2025-11-17T03:19:00Z",
      "status": "pending"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### 5.2.2 标记异常为已处理
```
PUT /v1/device-anomalies/{anomaly_id}
Authorization: Bearer {token}
Content-Type: application/json

请求体:
{
  "status": "handled"
}

响应 (200):
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

---

## 6. 开发时间表

| 阶段 | 任务 | 时间 |
|------|------|------|
| 第一阶段 | 后端 API 开发（认证、异常、流表） | 2-3 周 |
| 第二阶段 | 小程序前端开发（页面、组件） | 2-3 周 |
| 第三阶段 | WebSocket 实时通知 | 1-2 周 |
| 第四阶段 | 测试和优化 | 1-2 周 |
| 第五阶段 | 微信审核和发布 | 1 周 |

**总计**: 7-11 周

---

## 7. 部署方案

### 7.1 后端部署
```
1. 安装依赖: pip install -r requirements.txt
2. 配置微信 AppID 和 AppSecret
3. 配置数据库连接
4. 启动 FastAPI: uvicorn app:app --host 0.0.0.0 --port 8001
```

### 7.2 小程序部署
```
1. 在微信公众平台注册小程序
2. 获取 AppID 和 AppSecret
3. 配置服务器域名白名单
4. 上传小程序代码到微信
5. 提交审核
```

---

## 8. 安全考虑

- ✅ 使用 HTTPS 加密传输
- ✅ JWT Token 认证
- ✅ 请求签名验证
- ✅ 速率限制防止滥用
- ✅ 操作日志记录
- ✅ 敏感数据加密存储

---

**文档完成！** 详见第二部分（项目结构和详细设计）。
