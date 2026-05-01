import importlib.util
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


class ImageGeneratePromptInputTests(unittest.TestCase):
    def test_generate_nodes_preserve_legacy_required_widget_order(self):
        module = load_gpt_img_node()

        expected_prefixes = {
            module.GPTImgOAuthGenerate: [
                "prompt",
                "model",
                "quality",
                "size",
                "moderation",
                "n",
                "oauth_port",
                "auto_start_oauth",
                "timeout_sec",
            ],
            module.GPTImgOAuthGenerateAdvanced: [
                "design_request",
                "generation_instructions",
                "reference_instructions",
                "hard_constraints",
                "model",
                "quality",
                "size",
                "moderation",
                "n",
                "oauth_port",
                "auto_start_oauth",
                "timeout_sec",
            ],
            module.GPTImgAPIGenerate: [
                "prompt",
                "api_key",
                "model",
                "quality",
                "size",
                "moderation",
                "n",
                "timeout_sec",
            ],
            module.GPTImgAPIGenerateAdvanced: [
                "design_request",
                "generation_instructions",
                "reference_instructions",
                "hard_constraints",
                "api_key",
                "model",
                "quality",
                "size",
                "moderation",
                "n",
                "timeout_sec",
            ],
        }

        for node_class, expected_prefix in expected_prefixes.items():
            with self.subTest(node_class=node_class.__name__):
                required_order = list(node_class.INPUT_TYPES()["required"])

                self.assertEqual(required_order[: len(expected_prefix)], expected_prefix)
                self.assertEqual(required_order[-1], "system_prompt")

    def test_generate_nodes_expose_system_and_user_prompt_input_sockets(self):
        module = load_gpt_img_node()

        for node_class in (
            module.GPTImgOAuthGenerate,
            module.GPTImgOAuthGenerateAdvanced,
            module.GPTImgAPIGenerate,
            module.GPTImgAPIGenerateAdvanced,
        ):
            with self.subTest(node_class=node_class.__name__):
                inputs = node_class.INPUT_TYPES()

                self.assertIn("system_prompt", inputs["required"])
                self.assertIn("system_prompt_input", inputs["optional"])
                self.assertIn("user_prompt_input", inputs["optional"])
                self.assertTrue(inputs["optional"]["system_prompt_input"][1]["forceInput"])
                self.assertTrue(inputs["optional"]["user_prompt_input"][1]["forceInput"])

    def test_generate_one_uses_custom_system_prompt_in_payload(self):
        module = load_gpt_img_node()
        captured = {}

        def fake_post(auth_value, payload, timeout_sec):
            captured["auth_value"] = auth_value
            captured["payload"] = payload
            captured["timeout_sec"] = timeout_sec
            return "image_b64", ""

        module._generate_one(
            prompt="make a catalog coat",
            system_prompt="custom image system prompt",
            model="gpt-5.4",
            quality="medium",
            size="1024x1024",
            moderation="low",
            references=[],
            auth_value="auth",
            post_func=fake_post,
            timeout_sec=30,
        )

        self.assertEqual(captured["payload"]["input"][0]["content"], "custom image system prompt")
        self.assertIn("make a catalog coat", captured["payload"]["input"][1]["content"])

    def test_api_generate_prefers_connected_prompt_inputs_over_widgets(self):
        module = load_gpt_img_node()

        with mock.patch.object(module, "_generate_one", return_value=("image_b64", "")) as generate_one:
            with mock.patch.object(module, "_return_images", return_value=("image", "")):
                module.GPTImgAPIGenerate().generate(
                    system_prompt="widget system",
                    prompt="widget user",
                    api_key="key",
                    model="gpt-5.5",
                    quality="medium",
                    size="1024x1024",
                    moderation="low",
                    n=1,
                    timeout_sec=30,
                    reference_image=None,
                    system_prompt_input="socket system",
                    user_prompt_input="socket user",
                )

        args = generate_one.call_args.args
        self.assertEqual(args[0], "socket user")
        self.assertEqual(args[1], "socket system")

    def test_api_generate_falls_back_to_widget_prompts_when_inputs_unconnected(self):
        module = load_gpt_img_node()

        with mock.patch.object(module, "_generate_one", return_value=("image_b64", "")) as generate_one:
            with mock.patch.object(module, "_return_images", return_value=("image", "")):
                module.GPTImgAPIGenerate().generate(
                    system_prompt="widget system",
                    prompt="widget user",
                    api_key="key",
                    model="gpt-5.5",
                    quality="medium",
                    size="1024x1024",
                    moderation="low",
                    n=1,
                    timeout_sec=30,
                    reference_image=None,
                    system_prompt_input=None,
                    user_prompt_input=None,
                )

        args = generate_one.call_args.args
        self.assertEqual(args[0], "widget user")
        self.assertEqual(args[1], "widget system")


if __name__ == "__main__":
    unittest.main()
