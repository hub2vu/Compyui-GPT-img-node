import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_gpt_img_node():
    spec = importlib.util.spec_from_file_location("gpt_img_node", ROOT / "gpt_img_node.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self.payload = payload

    def read(self, _size=-1):
        return json.dumps(self.payload).encode("utf-8")


class LLMNodeTests(unittest.TestCase):
    def test_parse_json_text_extracts_output_text_from_response(self):
        module = load_gpt_img_node()
        response = FakeResponse(
            {
                "output": [
                    {"type": "reasoning", "summary": []},
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "Hello"},
                            {"type": "output_text", "text": " world"},
                        ],
                    },
                ],
            }
        )

        self.assertEqual(module._parse_json_text(response, "provider"), "Hello world")

    def test_oauth_llm_node_sends_reasoning_effort_and_returns_text_and_raw_json(self):
        module = load_gpt_img_node()
        captured = {}

        def fake_post(auth_value, payload, timeout_sec):
            captured["auth_value"] = auth_value
            captured["payload"] = payload
            captured["timeout_sec"] = timeout_sec
            return "answer", {"id": "resp_123", "output": []}

        with mock.patch.object(module, "_ensure_oauth") as ensure_oauth:
            with mock.patch.object(module, "_post_llm_oauth", side_effect=fake_post):
                text, raw_json = module.GPTImgOAuthLLM().chat(
                    system_prompt="Be terse.",
                    prompt="Say hi.",
                    model="gpt-5.4",
                    reasoning_effort="high",
                    max_output_tokens=256,
                    oauth_port=10531,
                    auto_start_oauth=True,
                    timeout_sec=90,
                )

        ensure_oauth.assert_called_once_with(10531, True)
        self.assertEqual(text, "answer")
        self.assertEqual(json.loads(raw_json)["id"], "resp_123")
        self.assertEqual(captured["auth_value"], 10531)
        self.assertEqual(captured["timeout_sec"], 90)
        self.assertEqual(captured["payload"]["reasoning"], {"effort": "high"})
        self.assertEqual(captured["payload"]["max_output_tokens"], 256)
        self.assertEqual(captured["payload"]["input"][0]["role"], "developer")
        self.assertEqual(captured["payload"]["input"][1]["role"], "user")

    def test_api_llm_node_contract_includes_api_key_and_reasoning_effort(self):
        module = load_gpt_img_node()
        inputs = module.GPTImgAPILLM.INPUT_TYPES()
        required = inputs["required"]
        optional = inputs["optional"]

        self.assertIn("api_key", required)
        self.assertIn("reasoning_effort", required)
        self.assertIn("gpt-5.5-pro", required["model"][0])
        self.assertIn("system_prompt_input", optional)
        self.assertIn("user_prompt_input", optional)
        self.assertTrue(optional["system_prompt_input"][1]["forceInput"])
        self.assertTrue(optional["user_prompt_input"][1]["forceInput"])
        self.assertEqual(required["reasoning_effort"][1]["default"], "medium")
        self.assertEqual(module.GPTImgAPILLM.RETURN_TYPES, ("STRING", "STRING"))
        self.assertEqual(module.GPTImgAPILLM.RETURN_NAMES, ("text", "raw_response_json"))

    def test_oauth_llm_node_contract_includes_prompt_input_sockets(self):
        module = load_gpt_img_node()
        inputs = module.GPTImgOAuthLLM.INPUT_TYPES()
        optional = inputs["optional"]

        self.assertIn("gpt-5.5-pro", inputs["required"]["model"][0])
        self.assertIn("system_prompt_input", optional)
        self.assertIn("user_prompt_input", optional)
        self.assertTrue(optional["system_prompt_input"][1]["forceInput"])
        self.assertTrue(optional["user_prompt_input"][1]["forceInput"])

    def test_api_llm_prefers_connected_prompt_inputs_over_widgets(self):
        module = load_gpt_img_node()
        captured = {}

        def fake_post(auth_value, payload, timeout_sec):
            captured["auth_value"] = auth_value
            captured["payload"] = payload
            captured["timeout_sec"] = timeout_sec
            return "answer", {"id": "resp_456", "output": []}

        with mock.patch.object(module, "_post_llm_api", side_effect=fake_post):
            text, raw_json = module.GPTImgAPILLM().chat(
                system_prompt="widget system",
                prompt="widget user",
                api_key="key",
                model="gpt-5.5",
                reasoning_effort="medium",
                max_output_tokens=512,
                timeout_sec=120,
                system_prompt_input="socket system",
                user_prompt_input="socket user",
            )

        self.assertEqual(text, "answer")
        self.assertEqual(json.loads(raw_json)["id"], "resp_456")
        self.assertEqual(captured["payload"]["input"][0]["content"], "socket system")
        self.assertEqual(captured["payload"]["input"][1]["content"], "socket user")

    def test_api_llm_falls_back_to_widget_prompts_when_inputs_unconnected(self):
        module = load_gpt_img_node()
        captured = {}

        def fake_post(auth_value, payload, timeout_sec):
            captured["payload"] = payload
            return "answer", {"id": "resp_789", "output": []}

        with mock.patch.object(module, "_post_llm_api", side_effect=fake_post):
            module.GPTImgAPILLM().chat(
                system_prompt="widget system",
                prompt="widget user",
                api_key="key",
                model="gpt-5.5",
                reasoning_effort="medium",
                max_output_tokens=512,
                timeout_sec=120,
                system_prompt_input=None,
                user_prompt_input=None,
            )

        self.assertEqual(captured["payload"]["input"][0]["content"], "widget system")
        self.assertEqual(captured["payload"]["input"][1]["content"], "widget user")


if __name__ == "__main__":
    unittest.main()
