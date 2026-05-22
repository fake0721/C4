import sys
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.v1_routes import resolve_frontend_action, router


def call_chat_with_fake_agent(monkeypatch, message, intent_response):
    class FakeAgent:
        def __init__(self):
            self.prompts = []

        def _call_llm(self, prompt, temperature=0.3):
            self.prompts.append(prompt)
            if "请直接回答" in prompt:
                return intent_response
            if "系统操作执行结果" in prompt:
                return "好呀，已经帮你打开首页看板啦 😊"
            raise AssertionError(f"unexpected prompt: {prompt[:80]}")

    fake_agent = FakeAgent()
    monkeypatch.setitem(
        sys.modules,
        "security_agent",
        SimpleNamespace(get_agent_instance=lambda: fake_agent),
    )

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    return (
        client.post(
            "/v1/chat/with-tools",
            json={"username": "tester", "user": message},
        ),
        fake_agent,
    )


def test_dashboard_navigation_is_frontend_action_not_data_query():
    action = resolve_frontend_action("跳转到首页看板")

    assert action == {
        "type": "navigate",
        "tool": "navigate_to_page",
        "page": "dashboard",
        "path": "/dashboard",
        "reason": "用户要求跳转到首页看板",
    }


def test_export_panel_request_is_frontend_action():
    action = resolve_frontend_action("打开导出面板")

    assert action["type"] == "open_export_dialog"
    assert action["tool"] == "open_export_dialog"


def test_anomaly_report_export_uses_business_report_not_ai_analysis():
    action = resolve_frontend_action("导出异常与攻击报告")

    assert action["type"] == "execute_report_export"
    assert action["tool"] == "export_report_file"
    assert action["export_type"] == "anomalies"
    assert action["title"] == "导出异常与攻击报告"
    assert action["hours"] == 24
    assert action["format"] == "pdf"
    assert action["export_type"] != "ai_analysis"


def test_anomaly_report_export_can_parse_optional_range_and_format():
    action = resolve_frontend_action("帮我导出最近三天的异常与攻击报告 docx")

    assert action["type"] == "execute_report_export"
    assert action["export_type"] == "anomalies"
    assert action["hours"] == 72
    assert action["format"] == "docx"


def test_security_status_question_is_not_frontend_action():
    assert resolve_frontend_action("帮我分析一下当前安全态势") is None


def test_broader_system_operation_phrases_are_detected():
    cases = [
        ("返回主页", "/dashboard"),
        ("带我去账号详情页面", "/account-details"),
        ("我要上传知识库文档", "/knowledge"),
        ("切换到流表管理", "/flowtable"),
    ]

    for message, path in cases:
        action = resolve_frontend_action(message)
        assert action is not None
        assert action["type"] == "navigate"
        assert action["path"] == path


def test_chat_with_tools_decides_frontend_action_after_intent_recognition(monkeypatch):
    response, fake_agent = call_chat_with_fake_agent(
        monkeypatch,
        "跳转到首页看板",
        "【系统操作】",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tools_called"] == ["navigate_to_page"]
    assert data["frontend_actions"][0]["path"] == "/dashboard"
    assert data["response"] == "好呀，已经帮你打开首页看板啦 😊"
    assert "【系统操作】" in fake_agent.prompts[0]
    assert "系统操作执行结果" in fake_agent.prompts[1]
    assert "【调用工具】" not in data["response"]


def test_chat_with_tools_calibrates_page_operation_when_llm_says_data_query(monkeypatch):
    response, fake_agent = call_chat_with_fake_agent(
        monkeypatch,
        "跳转到首页看板",
        "【数据查询】",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tools_called"] == ["navigate_to_page"]
    assert data["frontend_actions"][0]["path"] == "/dashboard"
    assert data["response"] == "好呀，已经帮你打开首页看板啦 😊"
    assert len(fake_agent.prompts) == 2


def test_chat_with_tools_returns_direct_export_action(monkeypatch):
    response, _fake_agent = call_chat_with_fake_agent(
        monkeypatch,
        "导出异常与攻击报告",
        "【系统操作】",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tools_called"] == ["export_report_file"]
    assert data["frontend_actions"][0]["type"] == "execute_report_export"
    assert data["frontend_actions"][0]["export_type"] == "anomalies"
    assert data["frontend_actions"][0]["hours"] == 24
    assert data["frontend_actions"][0]["format"] == "pdf"


def test_show_command_list_is_frontend_action():
    action = resolve_frontend_action("展示一下你能操作系统的功能列表")

    assert action["type"] == "show_command_list"
    assert action["tool"] == "show_command_list"
