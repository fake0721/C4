# 统一 AI 助手编排系统设计

## 背景

当前项目已经具备三部分基础能力，但实现仍然分散：

- `backend/ai_routes.py` 提供通用 AI 聊天、流式输出、对话持久化。
- `backend/agent_routes.py` 和 `backend/v1_routes.py` 各自维护一套工具调用入口与工具分发逻辑。
- `src/components/AIAssistant/AIAssistant.vue` 直接依赖 `/v1/chat/with-tools`，并通过 `__AGENT_ANALYSIS__`、`__INTERACTIVE_DATA__` 等字符串前缀做前端特判渲染。

这导致“任务一”和“任务二”虽然描述角度不同，但最终会落到同一条链路上：

1. 用户用自然语言提出查询、分析、执行、导出请求。
2. 系统识别意图并抽取参数。
3. 系统调用具体平台工具。
4. 系统将调用过程、执行结果、风险确认与最终答案结构化返回给前端。

因此，本次建设应合并为一个正式能力：`统一 AI 助手编排系统`。

## 目标

### 业务目标

- 让用户通过自然语言完成查询、分析、执行、导出四类任务。
- 让前端可以展示真实的工具调用链路，而不是只展示大段自然语言文本。
- 让高风险动作具备确认、权限校验、日志审计与追溯能力。
- 让多轮会话支持“这个 IP”“刚才那个异常”之类上下文引用。

### 技术目标

- 建立单一 AI 编排入口，避免 `ai_routes.py`、`agent_routes.py`、`v1_routes.py` 继续平行演化。
- 建立统一工具注册中心，统一工具元数据、参数模式、风险级别、权限模型与执行方式。
- 建立统一响应协议，前端仅依赖标准结构，不再依赖字符串前缀协议。
- 以渐进式改造方式落地，首期保留现有路由与工具实现，逐步迁移到底座之上。

### 非目标

- 本期不追求接入新的 Agent runtime 或完全替换现有 `security_agent.py`。
- 本期不重写所有历史前端页面，只聚焦 AI 助手主流程与相关高风险交互。
- 本期不要求一次替换所有旧接口，可保留兼容层。

## 当前系统问题

### 后端问题

- `backend/agent_routes.py` 与 `backend/v1_routes.py` 都在做工具分发，职责重复。
- 工具定义分散在路由分支和 `security_agent.py` 方法中，没有统一元数据中心。
- 工具调用日志、执行结果、异常信息没有标准模型，不利于前端展示与审计。
- 多轮上下文没有真正统一的 memory 层，导致自然语言追问能力不稳定。

### 前端问题

- `src/components/AIAssistant/AIAssistant.vue` 过于集中，既承担页面展示，也承担协议解析、会话缓存、交互式动作处理。
- 会话当前主要保存在 `localStorage`，与后端的 `AIConversation` / `AIMessage` 模型没有形成闭环。
- 结构化回答、调用链路、风险确认还没有统一协议支撑。

### 数据模型问题

- `backend/models.py` 中已有 `AIConversation`、`AIMessage`，但缺少意图类型、上下文快照、工具调用映射等字段。
- `database/init.sql` 已有导出任务与导出审计表，但缺少 AI 工具调用与执行审计主表。

## 设计原则

1. 单一编排入口：自然语言理解和工具调用必须收口到一条主链路。
2. 工具优先注册：所有可调用能力先注册，再由编排层选择与执行。
3. 响应协议前后端解耦：前端看结构，不看后端内部实现。
4. 高风险动作显式化：执行类动作必须经历权限校验、确认与审计。
5. 渐进式迁移：先兼容现状，再替换老分支逻辑。

## 目标架构

```text
AIAssistant.vue
  -> ai_routes.py / 新统一聊天接口
    -> AI Orchestrator
      -> Conversation Memory Service
      -> Intent Resolver
      -> Tool Registry
      -> Tool Executors
      -> Audit Logger
    -> 结构化响应
  -> 前端展示：状态 / 工具链 / 结论 / 建议 / 已执行动作
```

### 分层职责

#### 1. 聊天入口层

建议继续以 `backend/ai_routes.py` 为主入口，新增统一接口，例如：

- `POST /api/ai-assistant/chat`
- `POST /api/ai-assistant/chat/stream`
- `GET /api/ai-assistant/conversations/{id}/tool-calls`

该层只做：

- 用户身份接入
- 请求体校验
- 调用编排层
- 返回标准结构

不再直接承担工具选择、参数抽取、日志落库等业务逻辑。

#### 2. AI 编排层

建议新增：

- `backend/ai_orchestrator.py`

主要职责：

1. 读取对话上下文。
2. 识别意图类别：`query` / `analysis` / `execute` / `export` / `clarify`
3. 抽取参数：IP、时间范围、攻击类型、交换机、持续时间等。
4. 判断是否存在歧义或参数不足。
5. 选择工具并组织调用计划。
6. 对执行类操作做权限校验与确认控制。
7. 顺序执行工具，归并结果。
8. 生成结构化答案。
9. 记录对话与工具调用审计日志。

#### 3. 工具注册中心

建议新增：

- `backend/tool_registry.py`
- `backend/tool_schemas.py`

注册中心负责维护统一工具定义：

```python
ToolDefinition(
    name="apply_rate_limit",
    category="execute",
    description="对指定 IP 应用限速策略",
    risk_level="high",
    permission="admin",
    requires_confirmation=True,
    params_schema={
        "ip": {"type": "string", "required": True},
        "level": {"type": "string", "required": True},
        "duration_seconds": {"type": "integer", "required": True},
        "reason": {"type": "string", "required": True},
    },
    executor="rate_limit_executor.apply",
)
```

首期工具建议按四类收口：

- 查询类：异常、流量、拓扑、主机状态、交换机状态、黑白名单状态、限速状态
- 分析类：异常摘要、趋势分析、高风险解释
- 执行类：限速、黑名单、白名单、流表下发
- 导出类：异常报告导出、AI 研判导出

#### 4. 工具执行层

建议新增目录：

- `backend/tool_executors/query_tools.py`
- `backend/tool_executors/analysis_tools.py`
- `backend/tool_executors/execute_tools.py`
- `backend/tool_executors/export_tools.py`

该层不感知自然语言，只接受标准化参数。

首期可以复用现有实现：

- 从 `security_agent.py` 包装查询/执行工具。
- 从 `export_service.py` 包装导出工具。
- 从 `v1_routes.py` 中抽离确实属于平台能力的查询/控制函数。

#### 5. 上下文记忆层

建议新增：

- `backend/conversation_memory_service.py`

能力包括：

- 最近几轮消息摘要
- 最近一次已识别对象，如 `current_ip`, `current_attack_type`
- 最近一次待确认动作，如 `pending_action`
- 最近一次工具结果引用，如 `last_query_result`

设计上不要求长期保存完整推理过程，但要保存足够的引用上下文，避免长对话全量重放。

#### 6. 审计与日志层

建议新增：

- `backend/tool_call_logging_service.py`

记录内容包括：

- 用户 ID
- 对话 ID
- 消息 ID
- 意图类型
- 工具名称
- 输入参数
- 返回摘要
- 状态
- 异常信息
- 风险级别
- 是否确认
- 执行耗时
- 时间戳

## 标准响应协议

前端必须从“字符串特判渲染”切到统一对象协议。建议响应结构如下：

```json
{
  "success": true,
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "intent": {
    "type": "execute",
    "confidence": 0.93,
    "requires_clarification": false
  },
  "clarification": null,
  "confirmation": {
    "required": true,
    "status": "pending",
    "action_label": "将 192.168.1.8 限速 10 分钟",
    "risk_level": "high"
  },
  "tool_calls": [
    {
      "id": "call_1",
      "name": "query_attack_history",
      "category": "query",
      "status": "success",
      "summary": "查询到 3 条历史攻击记录"
    },
    {
      "id": "call_2",
      "name": "apply_rate_limit",
      "category": "execute",
      "status": "pending_confirmation",
      "summary": "等待用户确认后执行"
    }
  ],
  "result": {
    "query_result": [],
    "analysis_conclusion": "该 IP 在最近 10 分钟内表现出明显的 SYN Flood 特征",
    "execution_result": null,
    "recommended_actions": [
      "限速 10 分钟",
      "继续观察 30 分钟"
    ]
  },
  "answer": "已完成攻击历史查询，并为你准备了限速动作，等待确认。",
  "errors": []
}
```

### 前端展示映射

前端建议固定展示四块：

- 当前状态 / 查询结果
- 异常解释 / 分析结论
- 建议处置
- 已执行动作

同时展示调用过程时间线：

- 工具名称
- 调用顺序
- 执行状态
- 摘要
- 查看详情入口

## 歧义消解与确认流

### 歧义消解

当请求缺少关键信息时，不应直接失败，而应返回澄清结构：

```json
{
  "intent": {
    "type": "clarify",
    "requires_clarification": true
  },
  "clarification": {
    "question": "你是要查看最近 1 小时异常，还是今天全部异常？",
    "missing_fields": ["time_range"]
  }
}
```

### 高风险确认

执行类操作分级：

- `low`: 普通查询，无需确认
- `medium`: 可逆配置操作，可根据角色决定是否确认
- `high`: 限速、黑名单、流表下发，必须确认

确认流设计：

1. 首次请求只生成待确认动作，不直接执行。
2. 前端弹窗展示动作、对象、时长、原因、风险说明。
3. 用户确认后调用确认接口执行。
4. 后端写入确认日志与执行日志。

## 数据库与模型调整

### 现有模型扩展

修改 `backend/models.py`：

- `AIConversation`
  - 增加 `context_summary`
  - 增加 `last_intent_type`
  - 增加 `last_referenced_object`

- `AIMessage`
  - 增加 `intent_type`
  - 增加 `structured_payload`
  - 增加 `tool_call_group_id`
  - 增加 `confirmation_status`

### 新增模型

建议新增：

- `AIToolCallLog`
- `AIPendingAction`

其中 `AIToolCallLog` 为核心追溯表，`AIPendingAction` 用于高风险操作确认。

## 文件落位建议

### 后端新增

- `backend/ai_orchestrator.py`
- `backend/tool_registry.py`
- `backend/tool_schemas.py`
- `backend/conversation_memory_service.py`
- `backend/tool_call_logging_service.py`
- `backend/tool_executors/query_tools.py`
- `backend/tool_executors/analysis_tools.py`
- `backend/tool_executors/execute_tools.py`
- `backend/tool_executors/export_tools.py`

### 后端修改

- `backend/ai_routes.py`
- `backend/agent_routes.py`
- `backend/v1_routes.py`
- `backend/models.py`
- `database/init.sql`

### 前端新增

- `src/services/aiAssistantApi.ts`
- `src/types/aiAssistant.ts`
- `src/components/AIAssistant/ToolCallTimeline.vue`
- `src/components/AIAssistant/StructuredAnswerCard.vue`
- `src/components/AIAssistant/ConfirmationDialog.vue`

### 前端修改

- `src/components/AIAssistant/AIAssistant.vue`

## 渐进式迁移策略

### 阶段 1：底座成型

- 建工具注册中心
- 建编排层
- 建日志模型
- 先接查询类与部分执行类工具

### 阶段 2：前端协议切换

- 新聊天接口返回统一结构
- AI 助手页切到统一协议渲染
- 加入调用链展示、结构化答案、确认弹窗

### 阶段 3：会话与确认闭环

- 上下文记忆
- 歧义追问
- 高风险待确认动作
- 确认后二次执行

### 阶段 4：老逻辑收口

- 将重复工具分发逻辑从旧路由中迁出
- 保留兼容接口
- 后续逐步下线重复分支

## 测试策略

### 后端测试

- 意图分类测试
- 参数抽取测试
- 工具选择测试
- 权限测试
- 高风险确认测试
- 工具失败兜底测试
- 多轮上下文测试

### 前端测试

- 工具时间线展示测试
- 结构化结果卡片测试
- 歧义追问展示测试
- 高风险确认弹窗测试
- 对话历史查看调用链测试

### 联调测试

- 查询异常 -> 生成分析 -> 限速确认 -> 执行限速
- 查询异常 -> 导出报告
- 歧义问题 -> 追问 -> 再次输入 -> 生成结果

## 风险与控制

### 风险 1：旧逻辑分叉继续扩大

控制方式：

- 新功能只接统一编排层
- 旧路由只保留兼容或适配职责

### 风险 2：前端协议切换成本高

控制方式：

- 首期保留兼容解析层
- 后端同时返回 `answer` 与 `structured_payload`

### 风险 3：执行类操作误触发

控制方式：

- 明确高风险确认状态机
- 强制记录确认人与确认时间

### 风险 4：多轮上下文混乱

控制方式：

- 不全量复用历史文本
- 只保留摘要、引用对象、待确认动作三类关键信息

## 结论

“任务一”和“任务二”应合并为一个正式能力来建设，最佳路径是：

- 以 `ai_routes.py` 为统一入口
- 新增编排层与工具注册中心
- 复用现有 `agent_routes.py`、`v1_routes.py`、`security_agent.py`、`export_service.py` 的可用能力
- 用统一响应协议驱动 `AIAssistant.vue` 的结构化展示
- 通过上下文记忆、确认机制和审计日志完成从自然语言到真实平台动作的闭环

这套设计既能指导首期落地，也能支撑后续继续扩展更多网络安全与 SDN 控制能力。
