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


if __name__ == "__main__":
    unittest.main()
