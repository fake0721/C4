import os
import sys
import unittest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class DashScopeKimiConfigTest(unittest.TestCase):
    def test_legacy_kimi_alias_uses_compatible_chat_endpoint(self):
        from backend.dashscope_kimi import build_kimi_request_config

        config = build_kimi_request_config(
            api_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="kimi-2.5",
        )

        self.assertEqual(
            config["url"],
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        )
        self.assertEqual(config["model"], "kimi/kimi-k2.5")
        self.assertEqual(config["api_style"], "openai_compatible")

    def test_native_dashscope_payload_wraps_messages_in_input(self):
        from backend.dashscope_kimi import build_kimi_payload

        payload = build_kimi_payload(
            api_style="dashscope_native",
            model="kimi-k2-thinking",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "你好"},
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=False,
        )

        self.assertEqual(payload["model"], "kimi-k2-thinking")
        self.assertIn("input", payload)
        self.assertEqual(payload["input"]["messages"][1]["content"], "你好")
        self.assertEqual(payload["parameters"]["result_format"], "message")

    def test_post_kimi_request_ignores_environment_proxies(self):
        from backend import dashscope_kimi

        sessions = []

        class FakeSession:
            def __init__(self):
                self.trust_env = True
                self.post_kwargs = None
                sessions.append(self)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, url, **kwargs):
                self.post_url = url
                self.post_kwargs = kwargs
                return "response"

        original_session = dashscope_kimi.requests.Session
        dashscope_kimi.requests.Session = FakeSession
        try:
            response = dashscope_kimi.post_kimi_request(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": "Bearer test"},
                json={"model": "kimi/kimi-k2.5"},
                timeout=30,
            )
        finally:
            dashscope_kimi.requests.Session = original_session

        self.assertEqual(response, "response")
        self.assertEqual(len(sessions), 1)
        self.assertFalse(sessions[0].trust_env)
        self.assertEqual(sessions[0].post_kwargs["timeout"], 30)


if __name__ == "__main__":
    unittest.main()
