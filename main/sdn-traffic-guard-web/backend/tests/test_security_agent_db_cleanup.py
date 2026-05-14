import os
import sys
import types
import unittest
import importlib
from unittest.mock import patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class SecurityAgentDbCleanupTest(unittest.TestCase):
    def _install_fake_rag_service(self):
        fake_rag_service = types.ModuleType("backend.rag_service")
        fake_rag_service.rag_service = object()
        sys.modules["backend.rag_service"] = fake_rag_service

    def test_security_agent_db_config_uses_env_password(self):
        self._install_fake_rag_service()
        sys.modules.pop("backend.security_agent", None)

        with patch.dict(os.environ, {"DB_PASSWORD": "env-secret", "DB_HOST": "10.0.0.8"}, clear=False):
            security_agent = importlib.import_module("backend.security_agent")

        self.assertEqual(security_agent.DB_CONFIG["password"], "env-secret")
        self.assertEqual(security_agent.DB_CONFIG["host"], "10.0.0.8")

    def test_query_acl_blacklist_returns_connect_error_when_db_connect_fails(self):
        self._install_fake_rag_service()
        sys.modules.pop("backend.security_agent", None)

        from backend.security_agent import SecurityAgent

        agent = SecurityAgent.__new__(SecurityAgent)

        with patch("backend.security_agent.pymysql.connect", side_effect=RuntimeError("db down")):
            result = agent._tool_query_acl_blacklist()

        self.assertFalse(result["success"])
        self.assertEqual(result["tool"], "query_acl_blacklist")
        self.assertIn("db down", result["error"])
        self.assertNotIn("conn", result["error"])

    def test_call_kimi_llm_retries_after_read_timeout(self):
        self._install_fake_rag_service()
        sys.modules.pop("backend.security_agent", None)

        from backend.security_agent import SecurityAgent
        from requests import exceptions as requests_exceptions

        agent = SecurityAgent.__new__(SecurityAgent)
        agent.kimi_api_key = "test-key"
        agent.kimi_api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        agent.dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        agent.model = "kimi/kimi-k2.5"
        agent.kimi_connect_timeout = 5
        agent.kimi_read_timeout = 45
        agent.kimi_max_retries = 1

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

        with patch(
            "backend.security_agent.requests.post",
            side_effect=[requests_exceptions.ReadTimeout("slow"), FakeResponse()],
        ) as mock_post:
            with patch("backend.security_agent.time.sleep") as mock_sleep:
                result = agent._call_kimi_llm("查看黑名单")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_post.call_args.kwargs["timeout"], (5, 45))
        mock_sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
