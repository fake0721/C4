# Unified AI Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified AI assistant orchestration system that supports natural-language queries, analysis, execution confirmation, tool-call logging, and structured frontend rendering without breaking existing routes.

**Architecture:** Keep `backend/ai_routes.py` as the primary chat entry, add a new orchestration layer plus tool registry beneath it, and progressively wrap existing capabilities from `agent_routes.py`, `v1_routes.py`, `security_agent.py`, and `export_service.py`. The frontend `AIAssistant.vue` moves from string-prefix parsing to a typed response contract with tool timelines, structured answer sections, and confirmation dialogs.

**Tech Stack:** FastAPI, SQLAlchemy, existing MySQL/SQLite models, Vue 3 + TypeScript, existing export and SDN service modules

---

### Task 1: Data Model And Persistence Foundation

**Files:**
- Modify: `backend/models.py`
- Modify: `database/init.sql`
- Create: `backend/tests/test_ai_assistant_models.py`

- [ ] **Step 1: Write the failing model and schema tests**

```python
def test_ai_tool_call_log_has_required_columns():
    columns = {
        "conversation_id",
        "message_id",
        "tool_name",
        "intent_type",
        "status",
        "risk_level",
    }
    assert columns.issubset(set(AIToolCallLog.__table__.columns.keys()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_ai_assistant_models.py -v`
Expected: FAIL because `AIToolCallLog` and related fields do not exist yet.

- [ ] **Step 3: Add the persistence layer**

Add new SQLAlchemy models and extend existing ones:

```python
class AIToolCallLog(Base):
    __tablename__ = "ai_tool_call_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("ai_conversations.id"), nullable=False)
    message_id = Column(String(36), ForeignKey("ai_messages.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    intent_type = Column(String(20), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_category = Column(String(20), nullable=False)
    risk_level = Column(String(20), nullable=False, default="low")
    input_params = Column(Text, nullable=False)
    result_summary = Column(Text, nullable=True)
    raw_result = Column(Text, nullable=True)
    status = Column(String(30), nullable=False)
    error_message = Column(Text, nullable=True)
    requires_confirmation = Column(Boolean, default=False)
    confirmed_by = Column(String(36), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

Also extend `AIConversation` and `AIMessage` with:

- `context_summary`
- `last_intent_type`
- `last_referenced_object`
- `intent_type`
- `structured_payload`
- `tool_call_group_id`
- `confirmation_status`

- [ ] **Step 4: Add SQL initialization / migration SQL**

Add matching SQL in `database/init.sql` for:

- `ai_tool_call_logs`
- `ai_pending_actions`
- additional AI conversation / message columns where schema initialization is used

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest backend/tests/test_ai_assistant_models.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/models.py database/init.sql backend/tests/test_ai_assistant_models.py
git commit -m "feat: add ai assistant persistence models"
```

### Task 2: Tool Registry And Executor Abstractions

**Files:**
- Create: `backend/tool_schemas.py`
- Create: `backend/tool_registry.py`
- Create: `backend/tool_executors/query_tools.py`
- Create: `backend/tool_executors/analysis_tools.py`
- Create: `backend/tool_executors/execute_tools.py`
- Create: `backend/tool_executors/export_tools.py`
- Create: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Write failing registry tests**

```python
def test_registry_exposes_required_tool_metadata():
    registry = build_tool_registry()
    tool = registry.get("apply_rate_limit")
    assert tool.requires_confirmation is True
    assert tool.permission == "admin"
    assert "ip" in tool.params_schema
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_tool_registry.py -v`
Expected: FAIL because the registry and definitions do not exist yet.

- [ ] **Step 3: Create the shared tool definition schema**

Define a typed tool model:

```python
@dataclass
class ToolDefinition:
    name: str
    category: str
    description: str
    risk_level: str
    permission: str
    requires_confirmation: bool
    params_schema: dict[str, dict[str, Any]]
    executor: Callable[..., dict[str, Any]]
```

- [ ] **Step 4: Build the registry**

Create `build_tool_registry()` that registers at least:

- `query_anomalies`
- `query_host_status`
- `query_switch_status`
- `query_attack_history`
- `query_network_topology`
- `summarize_anomalies`
- `apply_rate_limit`
- `add_to_blacklist`
- `add_to_whitelist`
- `export_anomaly_report`
- `export_ai_analysis`

- [ ] **Step 5: Wrap existing implementations in executor modules**

Use thin wrappers around existing code instead of rewriting behavior:

- call `security_agent` methods for ACL / limit / topology / attack history
- call `export_service.py` for report generation
- move reusable query logic out of `v1_routes.py` when needed

- [ ] **Step 6: Run tests to verify the registry passes**

Run: `pytest backend/tests/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/tool_schemas.py backend/tool_registry.py backend/tool_executors backend/tests/test_tool_registry.py
git commit -m "feat: add unified ai tool registry"
```

### Task 3: Conversation Memory And Audit Services

**Files:**
- Create: `backend/conversation_memory_service.py`
- Create: `backend/tool_call_logging_service.py`
- Create: `backend/tests/test_conversation_memory_service.py`
- Create: `backend/tests/test_tool_call_logging_service.py`

- [ ] **Step 1: Write failing tests for memory and logging**

```python
def test_memory_service_tracks_latest_referenced_ip():
    service = ConversationMemoryService()
    state = service.build_state(
        messages=[{"role": "user", "content": "把 192.168.1.8 限速十分钟"}],
        stored_summary=None,
    )
    assert state["current_ip"] == "192.168.1.8"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/test_conversation_memory_service.py backend/tests/test_tool_call_logging_service.py -v`
Expected: FAIL because services do not exist yet.

- [ ] **Step 3: Implement the memory service**

Support:

- extracting recent referenced object
- keeping a short context summary
- tracking pending action IDs
- resolving follow-up language like `这个 IP`

Use a compact state shape:

```python
{
    "summary": "...",
    "current_ip": "192.168.1.8",
    "current_attack_type": "SYN Flood",
    "pending_action_id": "action_xxx",
}
```

- [ ] **Step 4: Implement the logging service**

Support:

- writing each tool call row
- updating final status
- attaching error messages and summaries
- linking logs to conversation and message IDs

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest backend/tests/test_conversation_memory_service.py backend/tests/test_tool_call_logging_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/conversation_memory_service.py backend/tool_call_logging_service.py backend/tests/test_conversation_memory_service.py backend/tests/test_tool_call_logging_service.py
git commit -m "feat: add conversation memory and audit services"
```

### Task 4: AI Orchestrator Core

**Files:**
- Create: `backend/ai_orchestrator.py`
- Create: `backend/tests/test_ai_orchestrator.py`

- [ ] **Step 1: Write failing orchestrator tests**

```python
def test_execute_request_returns_pending_confirmation_for_high_risk_action():
    orchestrator = build_test_orchestrator()
    result = orchestrator.handle_message(
        message="把 192.168.1.8 限速十分钟",
        user_role="admin",
        conversation_id="conv-1",
    )
    assert result["confirmation"]["required"] is True
    assert result["tool_calls"][0]["status"] == "pending_confirmation"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_ai_orchestrator.py -v`
Expected: FAIL because the orchestrator does not exist yet.

- [ ] **Step 3: Implement the intent and parameter pipeline**

Support at minimum:

- intent classification: `query`, `analysis`, `execute`, `export`, `clarify`
- parameter extraction: IP, duration, time range, switch ID, attack type
- ambiguity handling when required parameters are missing

Use a predictable internal contract:

```python
{
    "intent_type": "execute",
    "confidence": 0.93,
    "entities": {"ip": "192.168.1.8", "duration_minutes": 10},
    "missing_fields": [],
}
```

- [ ] **Step 4: Implement the orchestration flow**

Core flow:

1. load conversation state
2. resolve intent and entities
3. ask clarification if missing data
4. select registered tools
5. enforce permission
6. stop on required confirmation
7. execute tools
8. build standard response
9. persist memory and logs

- [ ] **Step 5: Add fallback behavior**

When tools fail:

- keep the assistant response readable
- populate `errors`
- preserve partial success results

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest backend/tests/test_ai_orchestrator.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/ai_orchestrator.py backend/tests/test_ai_orchestrator.py
git commit -m "feat: add unified ai orchestrator"
```

### Task 5: Route Integration And Backward Compatibility

**Files:**
- Modify: `backend/ai_routes.py`
- Modify: `backend/agent_routes.py`
- Modify: `backend/v1_routes.py`
- Create: `backend/tests/test_ai_routes_orchestrator_integration.py`

- [ ] **Step 1: Write failing integration tests**

```python
def test_chat_endpoint_returns_structured_response(client, auth_headers):
    response = client.post(
        "/api/ai-assistant/chat",
        headers=auth_headers,
        json={"message": "最近哪个主机最异常？", "conversation_id": "conv-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "tool_calls" in data
    assert "result" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_ai_routes_orchestrator_integration.py -v`
Expected: FAIL because the new route contract is not implemented yet.

- [ ] **Step 3: Add new orchestrated endpoints in `ai_routes.py`**

Add:

- `POST /api/ai-assistant/chat`
- `POST /api/ai-assistant/chat/confirm`
- `GET /api/ai-assistant/conversations/{conversation_id}/tool-calls`

- [ ] **Step 4: Keep old entry points compatible**

Compatibility approach:

- preserve existing `/chat` and `/chat/stream` behavior
- preserve `/v1/chat/with-tools` temporarily
- internally adapt old handlers to new orchestrator result shape where feasible

- [ ] **Step 5: Reduce duplicate route logic**

In `agent_routes.py` and `v1_routes.py`:

- keep direct tool-test endpoints only as thin wrappers
- stop expanding new orchestration branches there

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest backend/tests/test_ai_routes_orchestrator_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/ai_routes.py backend/agent_routes.py backend/v1_routes.py backend/tests/test_ai_routes_orchestrator_integration.py
git commit -m "feat: integrate ai routes with orchestrator"
```

### Task 6: Frontend Structured Rendering And Confirmation UX

**Files:**
- Create: `src/types/aiAssistant.ts`
- Create: `src/services/aiAssistantApi.ts`
- Create: `src/components/AIAssistant/ToolCallTimeline.vue`
- Create: `src/components/AIAssistant/StructuredAnswerCard.vue`
- Create: `src/components/AIAssistant/ConfirmationDialog.vue`
- Modify: `src/components/AIAssistant/AIAssistant.vue`

- [ ] **Step 1: Write the component-level contract assumptions**

Document the TypeScript payloads first:

```ts
export interface ToolCallItem {
  id: string
  name: string
  category: 'query' | 'analysis' | 'execute' | 'export'
  status: 'success' | 'failed' | 'pending_confirmation' | 'running'
  summary: string
}
```

- [ ] **Step 2: Run a focused frontend typecheck to capture failures**

Run: `npm run build`
Expected: FAIL or show missing type / component imports while the new API contract is being introduced.

- [ ] **Step 3: Add API and type wrappers**

Move request/response logic out of `AIAssistant.vue` into `src/services/aiAssistantApi.ts`.

- [ ] **Step 4: Add dedicated UI components**

Build:

- `ToolCallTimeline.vue` for call chain display
- `StructuredAnswerCard.vue` for four response zones
- `ConfirmationDialog.vue` for high-risk confirmation

- [ ] **Step 5: Refactor `AIAssistant.vue`**

Change the page so it:

- consumes typed orchestrator responses
- displays recommended prompts and follow-up prompts
- shows call chain and structured result blocks
- uses backend conversations instead of local-only state as the source of truth over time

Keep a compatibility branch for old `__AGENT_ANALYSIS__` / `__INTERACTIVE_DATA__` messages until migration finishes.

- [ ] **Step 6: Run frontend verification**

Run: `npm run build`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/types/aiAssistant.ts src/services/aiAssistantApi.ts src/components/AIAssistant
git commit -m "feat: add structured ai assistant frontend"
```

### Task 7: End-To-End Tests, Rollout Guards, And Cleanup

**Files:**
- Create: `backend/tests/test_ai_assistant_end_to_end.py`
- Modify: `backend/ai_routes.py`
- Modify: `src/components/AIAssistant/AIAssistant.vue`
- Modify: `docs/` as needed for API notes

- [ ] **Step 1: Write end-to-end scenario tests**

Cover at least:

- query anomalies
- ask why a host is high risk
- request rate limit and receive confirmation
- confirm and execute
- export today’s anomaly report

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest backend/tests/test_ai_assistant_end_to_end.py -v`
Expected: FAIL until the full path is wired up.

- [ ] **Step 3: Add rollout guards**

Add configuration flags such as:

- `AI_ASSISTANT_STRUCTURED_RESPONSE_ENABLED`
- `AI_ASSISTANT_CONFIRMATION_ENABLED`

Use them to support partial rollout and quick rollback.

- [ ] **Step 4: Add regression coverage**

Verify:

- ordinary users cannot execute admin tools
- failed tools still return readable answers
- frontend timeline matches backend tool log sequence

- [ ] **Step 5: Run verification**

Run: `pytest backend/tests/test_ai_assistant_end_to_end.py -v`
Expected: PASS

Run: `npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/tests/test_ai_assistant_end_to_end.py backend/ai_routes.py src/components/AIAssistant/AIAssistant.vue docs
git commit -m "test: verify unified ai assistant end to end"
```

### Task 8: Migration Review And Legacy Branch Decommission Plan

**Files:**
- Modify: `docs/superpowers/specs/2026-05-14-unified-ai-assistant-design.md`
- Modify: `docs/superpowers/plans/2026-05-14-unified-ai-assistant.md`

- [ ] **Step 1: Review old and new entry points**

Checklist:

- is new traffic entering `ai_routes.py` orchestrator path
- are `agent_routes.py` and `v1_routes.py` now thin wrappers
- is the frontend using the structured response path by default

- [ ] **Step 2: Document the removal candidates**

Identify legacy logic to remove in a later cleanup PR:

- duplicated tool lists
- string-prefix response rendering
- localStorage-only conversation truth
- direct route-branch tool dispatch

- [ ] **Step 3: Final verification**

Run:

- `pytest backend/tests -v`
- `npm run build`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-05-14-unified-ai-assistant-design.md docs/superpowers/plans/2026-05-14-unified-ai-assistant.md
git commit -m "docs: finalize ai assistant migration plan"
```
