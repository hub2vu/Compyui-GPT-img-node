import base64
import io
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image


ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / "logs"
OAUTH_PROCESS = None

NODE_CATEGORY = "GPT img"
OAUTH_MODELS = ["gpt-5.4", "gpt-5.4-mini", "gpt-5.5"]
API_MODELS = ["gpt-5.5", "gpt-5", "gpt-5.4", "gpt-5.4-mini"]
OAUTH_LLM_MODELS = ["gpt-5.5-pro", "gpt-5.5", "gpt-5.4", "gpt-5.4-mini"]
API_LLM_MODELS = ["gpt-5.5-pro", "gpt-5.5", "gpt-5", "gpt-5.4", "gpt-5.4-mini"]
REASONING_EFFORT_VALUES = ["minimal", "low", "medium", "high", "xhigh"]
QUALITY_VALUES = ["low", "medium", "high"]
MODERATION_VALUES = ["low", "auto"]
SIZE_VALUES = [
    "1024x1024",
    "1536x1024",
    "1024x1536",
    "1360x1024",
    "1024x1360",
    "1824x1024",
    "1024x1824",
    "2048x2048",
    "2048x1152",
    "1152x2048",
    "3824x2160",
    "2160x3824",
    "auto",
]

GENERATE_DEVELOPER_PROMPT = (
    "You are an image generation assistant. Use the image_generation tool to "
    "create the requested image. Preserve the user's prompt, requested style, "
    "language, subject, and composition as closely as possible. Return image "
    "output, not explanatory text."
)

EDIT_DEVELOPER_PROMPT = (
    "You are an image editing assistant. Use the image_generation tool to edit "
    "the provided image according to the user's prompt. Preserve unchanged "
    "areas unless the user asks for a broader transformation. Return image "
    "output, not explanatory text."
)

PROMPT_SUFFIX = (
    "\n\nKeep the image prompt close to the user's original text. Do not translate "
    "or restyle it unless the user requested that."
)
PROMPT_INPUT_SOCKET = ("STRING", {"forceInput": True})

DEFAULT_GENERATION_INSTRUCTIONS = (
    "Create a product-only apparel design image for fashion planning.\n\n"
    "Output format:\n"
    "Show exactly two views of the same garment in one image:\n"
    "- front view on the left\n"
    "- back view on the right\n\n"
    "The garment must be shown alone on a clean white or very light gray background. "
    "The result should look like a professional e-commerce product catalog image "
    "or a fashion technical presentation image.\n\n"
    "The front and back views must represent the same garment design. Use the same "
    "color, fabric, sleeve shape, collar type, hem shape, and overall silhouette "
    "in both views."
)

DEFAULT_REFERENCE_INSTRUCTIONS = (
    "Use the first reference image, if provided, as a layout reference only for "
    "the front/back side-by-side composition.\n"
    "Use the other reference images only for garment category, silhouette, color, "
    "material feel, fabric texture, collar, sleeve, button, pocket, seam, and hem details.\n"
    "Do not copy the exact product design, brand, logo, text, watermark, person, "
    "pose, background, or photography artifacts.\n"
    "If reference images contain a human model, ignore the person and use only "
    "the garment design cues.\n"
    "The user design request has priority over the reference images if there is any conflict."
)

DEFAULT_HARD_CONSTRAINTS = (
    "No human model. No mannequin. No hanger. No body parts. No face. No arms. "
    "No legs. No person wearing the garment. No lifestyle background. No studio props. "
    "No table. No folded garment. No flat lay. No extra accessories. No text labels. "
    "No logo. No watermark."
)


def _oauth_url(oauth_port):
    return f"http://127.0.0.1:{int(oauth_port)}"


def _read_error(err):
    body = err.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {"error": body}
    message = data.get("error") or data.get("message") or str(err)
    code = data.get("code")
    if code:
        message = f"{message} ({code})"
    return message


def _oauth_ready(oauth_port):
    req = urllib.request.Request(
        f"{_oauth_url(oauth_port)}/v1/models",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as res:
            return 200 <= res.status < 300
    except Exception:
        return False


def _resolve_npx():
    candidates = ["npx.cmd", "npx"] if os.name == "nt" else ["npx"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError("npx was not found. Install Node.js, then restart ComfyUI.")


def _start_oauth(oauth_port):
    global OAUTH_PROCESS

    if _oauth_ready(oauth_port):
        return
    if OAUTH_PROCESS is not None and OAUTH_PROCESS.poll() is None:
        return

    LOG_DIR.mkdir(exist_ok=True)
    log_file = open(LOG_DIR / "openai-oauth.log", "a", encoding="utf-8")
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    OAUTH_PROCESS = subprocess.Popen(
        [_resolve_npx(), "-y", "openai-oauth", "--port", str(int(oauth_port))],
        cwd=str(ROOT_DIR),
        env=os.environ.copy(),
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    deadline = time.time() + 45
    while time.time() < deadline:
        if OAUTH_PROCESS.poll() is not None:
            raise RuntimeError(
                "openai-oauth exited while starting. Check custom_nodes/GPT-img/logs/openai-oauth.log."
            )
        if _oauth_ready(oauth_port):
            return
        time.sleep(1)

    raise RuntimeError(
        "openai-oauth did not become ready. Run `npx @openai/codex login`, then retry."
    )


def _ensure_oauth(oauth_port, auto_start_oauth):
    if _oauth_ready(oauth_port):
        return
    if auto_start_oauth:
        _start_oauth(oauth_port)
        return
    raise RuntimeError(
        f"openai-oauth is not reachable on port {oauth_port}. Enable auto_start_oauth or start it manually."
    )


def _tensor_to_png_b64(image):
    if image.ndim == 4:
        image = image[0]
    array = image.detach().cpu().numpy()
    array = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    pil = Image.fromarray(array).convert("RGB")
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _tensor_batch_to_refs(images, limit=5):
    if images is None:
        return []
    if images.ndim == 3:
        images = images.unsqueeze(0)
    refs = []
    for i in range(min(int(images.shape[0]), limit)):
        refs.append(_tensor_to_png_b64(images[i]))
    return refs


def _b64_to_tensor(image_b64):
    import torch

    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    raw = base64.b64decode(image_b64)
    pil = Image.open(io.BytesIO(raw)).convert("RGB")
    array = np.asarray(pil).astype(np.float32) / 255.0
    return torch.from_numpy(array)[None,]


def _parse_sse_image(res, provider_label):
    image_b64 = None
    revised_prompt = ""
    buffer = ""

    while True:
        chunk = res.read(8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        buffer = buffer.replace("\r\n", "\n")

        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            data_lines = []
            for line in block.splitlines():
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
            if not data_lines:
                continue
            event_data = "".join(data_lines)
            if event_data == "[DONE]":
                continue
            try:
                event = json.loads(event_data)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "error":
                err = event.get("error") or {}
                raise RuntimeError(err.get("message") or err.get("code") or f"{provider_label} stream returned an error.")

            item = event.get("item") or {}
            if event.get("type") == "response.output_item.done" and item.get("type") == "image_generation_call":
                if item.get("result"):
                    image_b64 = item["result"]
                if item.get("revised_prompt"):
                    revised_prompt = item["revised_prompt"]

    if not image_b64:
        raise RuntimeError(f"No image data received from {provider_label}.")
    return image_b64, revised_prompt


def _parse_json_image(res, provider_label):
    data = json.loads(res.read().decode("utf-8"))
    for item in data.get("output", []):
        if item.get("type") == "image_generation_call" and item.get("result"):
            return item["result"], item.get("revised_prompt") or ""
    raise RuntimeError(f"No image data received from {provider_label}.")


def _extract_response_text(data):
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text

    parts = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    return "".join(parts)


def _parse_json_text(res, provider_label):
    data = json.loads(res.read().decode("utf-8"))
    text = _extract_response_text(data)
    if not text:
        raise RuntimeError(f"No text data received from {provider_label}.")
    return text


def _post_response(url, payload, timeout_sec, headers, provider_label):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "X-GPT-Img-Client": "comfyui",
            **headers,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=int(timeout_sec)) as res:
            content_type = res.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                return _parse_sse_image(res, provider_label)
            return _parse_json_image(res, provider_label)
    except urllib.error.HTTPError as err:
        raise RuntimeError(_read_error(err)) from err


def _post_llm_response(url, payload, timeout_sec, headers, provider_label):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-GPT-Img-Client": "comfyui",
            **headers,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=int(timeout_sec)) as res:
            data = json.loads(res.read().decode("utf-8"))
            text = _extract_response_text(data)
            if not text:
                raise RuntimeError(f"No text data received from {provider_label}.")
            return text, data
    except urllib.error.HTTPError as err:
        raise RuntimeError(_read_error(err)) from err


def _post_oauth(oauth_port, payload, timeout_sec):
    return _post_response(
        f"{_oauth_url(oauth_port)}/v1/responses",
        payload,
        timeout_sec,
        {},
        "openai-oauth",
    )


def _post_llm_oauth(oauth_port, payload, timeout_sec):
    return _post_llm_response(
        f"{_oauth_url(oauth_port)}/v1/responses",
        payload,
        timeout_sec,
        {},
        "openai-oauth",
    )


def _resolve_api_key(api_key):
    key = (api_key or "").strip()
    if key:
        return key
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    raise RuntimeError("OpenAI API key is missing. Enter api_key or set OPENAI_API_KEY.")


def _post_api(api_key, payload, timeout_sec):
    return _post_response(
        "https://api.openai.com/v1/responses",
        payload,
        timeout_sec,
        {"Authorization": f"Bearer {_resolve_api_key(api_key)}"},
        "OpenAI API",
    )


def _post_llm_api(api_key, payload, timeout_sec):
    return _post_llm_response(
        "https://api.openai.com/v1/responses",
        payload,
        timeout_sec,
        {"Authorization": f"Bearer {_resolve_api_key(api_key)}"},
        "OpenAI API",
    )


def _llm_one(
    system_prompt,
    prompt,
    model,
    reasoning_effort,
    max_output_tokens,
    auth_value,
    post_func,
    timeout_sec,
):
    input_items = []
    system_prompt = (system_prompt or "").strip()
    if system_prompt:
        input_items.append({"role": "developer", "content": system_prompt})
    input_items.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "input": input_items,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": int(max_output_tokens),
        "stream": False,
    }
    return post_func(auth_value, payload, timeout_sec)


def _resolve_prompt_value(widget_value, connected_value=None):
    if connected_value is None:
        return widget_value
    return connected_value


def _generate_one(
    prompt,
    system_prompt,
    model,
    quality,
    size,
    moderation,
    references,
    auth_value,
    post_func,
    timeout_sec,
):
    content = f"Generate an image: {prompt}{PROMPT_SUFFIX}"
    developer_prompt = (system_prompt or "").strip() or GENERATE_DEVELOPER_PROMPT
    if references:
        user_content = [
            *[
                {"type": "input_image", "image_url": f"data:image/png;base64,{ref}"}
                for ref in references
            ],
            {"type": "input_text", "text": content},
        ]
    else:
        user_content = content

    payload = {
        "model": model,
        "input": [
            {"role": "developer", "content": developer_prompt},
            {"role": "user", "content": user_content},
        ],
        "tools": [
            {
                "type": "image_generation",
                "quality": quality,
                "size": size,
                "moderation": moderation,
                "action": "generate",
            }
        ],
        "tool_choice": {"type": "image_generation"},
        "stream": True,
    }
    return post_func(auth_value, payload, timeout_sec)


def _edit_one(
    image_b64,
    prompt,
    model,
    quality,
    size,
    moderation,
    auth_value,
    post_func,
    timeout_sec,
):
    payload = {
        "model": model,
        "input": [
            {"role": "developer", "content": EDIT_DEVELOPER_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}"},
                    {"type": "input_text", "text": f"Edit this image: {prompt}{PROMPT_SUFFIX}"},
                ],
            },
        ],
        "tools": [
            {
                "type": "image_generation",
                "quality": quality,
                "size": size,
                "moderation": moderation,
                "action": "edit",
            }
        ],
        "tool_choice": {"type": "image_generation"},
        "stream": True,
    }
    return post_func(auth_value, payload, timeout_sec)


def _return_images(results):
    import torch

    tensors = [_b64_to_tensor(image_b64) for image_b64, _ in results]
    revised = next((text for _, text in results if text), "")
    return torch.cat(tensors, dim=0), revised


def _section(title, value):
    value = (value or "").strip()
    if not value:
        return ""
    return f"{title}:\n{value}"


def _compose_advanced_generate_prompt(
    design_request,
    generation_instructions,
    reference_instructions,
    hard_constraints,
):
    sections = [
        _section("Authoritative user design request", design_request),
        (
            "Conflict rule:\n"
            "If any instruction conflicts with the user design request above, "
            "follow the user design request."
        ),
        _section("Generation instructions", generation_instructions),
        _section("Reference image instructions", reference_instructions),
        _section("Hard constraints", hard_constraints),
    ]
    return "\n\n".join(section for section in sections if section)


class GPTImgOAuthLLM:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a helpful assistant."}),
                "prompt": ("STRING", {"multiline": True, "default": "Write a short answer."}),
                "model": (OAUTH_LLM_MODELS, {"default": "gpt-5.5"}),
                "reasoning_effort": (REASONING_EFFORT_VALUES, {"default": "medium"}),
                "max_output_tokens": ("INT", {"default": 2048, "min": 16, "max": 128000}),
                "oauth_port": ("INT", {"default": 10531, "min": 1024, "max": 65535}),
                "auto_start_oauth": ("BOOLEAN", {"default": True}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "raw_response_json")
    FUNCTION = "chat"
    CATEGORY = NODE_CATEGORY

    def chat(
        self,
        system_prompt,
        prompt,
        model,
        reasoning_effort,
        max_output_tokens,
        oauth_port,
        auto_start_oauth,
        timeout_sec,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        _ensure_oauth(oauth_port, auto_start_oauth)
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        text, data = _llm_one(
            system_prompt,
            prompt,
            model,
            reasoning_effort,
            max_output_tokens,
            oauth_port,
            _post_llm_oauth,
            timeout_sec,
        )
        return text, json.dumps(data, ensure_ascii=False)


class GPTImgAPILLM:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a helpful assistant."}),
                "prompt": ("STRING", {"multiline": True, "default": "Write a short answer."}),
                "api_key": ("STRING", {"default": ""}),
                "model": (API_LLM_MODELS, {"default": "gpt-5.5"}),
                "reasoning_effort": (REASONING_EFFORT_VALUES, {"default": "medium"}),
                "max_output_tokens": ("INT", {"default": 2048, "min": 16, "max": 128000}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "raw_response_json")
    FUNCTION = "chat"
    CATEGORY = NODE_CATEGORY

    def chat(
        self,
        system_prompt,
        prompt,
        api_key,
        model,
        reasoning_effort,
        max_output_tokens,
        timeout_sec,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        text, data = _llm_one(
            system_prompt,
            prompt,
            model,
            reasoning_effort,
            max_output_tokens,
            api_key,
            _post_llm_api,
            timeout_sec,
        )
        return text, json.dumps(data, ensure_ascii=False)


class GPTImgOAuthGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": GENERATE_DEVELOPER_PROMPT}),
                "prompt": ("STRING", {"multiline": True, "default": "a cinematic image"}),
                "model": (OAUTH_MODELS, {"default": "gpt-5.4"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 8}),
                "oauth_port": ("INT", {"default": 10531, "min": 1024, "max": 65535}),
                "auto_start_oauth": ("BOOLEAN", {"default": True}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
                "reference_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY

    def generate(
        self,
        system_prompt,
        prompt,
        model,
        quality,
        size,
        moderation,
        n,
        oauth_port,
        auto_start_oauth,
        timeout_sec,
        reference_image=None,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        _ensure_oauth(oauth_port, auto_start_oauth)
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        references = _tensor_batch_to_refs(reference_image)
        results = [
            _generate_one(
                prompt,
                system_prompt,
                model,
                quality,
                size,
                moderation,
                references,
                oauth_port,
                _post_oauth,
                timeout_sec,
            )
            for _ in range(int(n))
        ]
        return _return_images(results)


class GPTImgOAuthGenerateAdvanced:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": GENERATE_DEVELOPER_PROMPT}),
                "design_request": ("STRING", {"multiline": True, "default": "Men's navy summer suit."}),
                "generation_instructions": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_GENERATION_INSTRUCTIONS},
                ),
                "reference_instructions": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_REFERENCE_INSTRUCTIONS},
                ),
                "hard_constraints": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_HARD_CONSTRAINTS},
                ),
                "model": (OAUTH_MODELS, {"default": "gpt-5.4"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 8}),
                "oauth_port": ("INT", {"default": 10531, "min": 1024, "max": 65535}),
                "auto_start_oauth": ("BOOLEAN", {"default": True}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
                "reference_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY

    def generate(
        self,
        system_prompt,
        design_request,
        generation_instructions,
        reference_instructions,
        hard_constraints,
        model,
        quality,
        size,
        moderation,
        n,
        oauth_port,
        auto_start_oauth,
        timeout_sec,
        reference_image=None,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        _ensure_oauth(oauth_port, auto_start_oauth)
        prompt = _compose_advanced_generate_prompt(
            design_request,
            generation_instructions,
            reference_instructions,
            hard_constraints,
        )
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        references = _tensor_batch_to_refs(reference_image)
        results = [
            _generate_one(
                prompt,
                system_prompt,
                model,
                quality,
                size,
                moderation,
                references,
                oauth_port,
                _post_oauth,
                timeout_sec,
            )
            for _ in range(int(n))
        ]
        return _return_images(results)


class GPTImgOAuthEdit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": "edit this image"}),
                "model": (OAUTH_MODELS, {"default": "gpt-5.4"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "oauth_port": ("INT", {"default": 10531, "min": 1024, "max": 65535}),
                "auto_start_oauth": ("BOOLEAN", {"default": True}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "edit"
    CATEGORY = NODE_CATEGORY

    def edit(
        self,
        image,
        prompt,
        model,
        quality,
        size,
        moderation,
        oauth_port,
        auto_start_oauth,
        timeout_sec,
    ):
        _ensure_oauth(oauth_port, auto_start_oauth)
        image_b64 = _tensor_to_png_b64(image)
        result = _edit_one(image_b64, prompt, model, quality, size, moderation, oauth_port, _post_oauth, timeout_sec)
        return _return_images([result])


class GPTImgAPIGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": GENERATE_DEVELOPER_PROMPT}),
                "prompt": ("STRING", {"multiline": True, "default": "a cinematic image"}),
                "api_key": ("STRING", {"default": ""}),
                "model": (API_MODELS, {"default": "gpt-5.5"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 8}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
                "reference_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY

    def generate(
        self,
        system_prompt,
        prompt,
        api_key,
        model,
        quality,
        size,
        moderation,
        n,
        timeout_sec,
        reference_image=None,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        references = _tensor_batch_to_refs(reference_image)
        results = [
            _generate_one(
                prompt,
                system_prompt,
                model,
                quality,
                size,
                moderation,
                references,
                api_key,
                _post_api,
                timeout_sec,
            )
            for _ in range(int(n))
        ]
        return _return_images(results)


class GPTImgAPIGenerateAdvanced:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "system_prompt": ("STRING", {"multiline": True, "default": GENERATE_DEVELOPER_PROMPT}),
                "design_request": ("STRING", {"multiline": True, "default": "Men's navy summer suit."}),
                "generation_instructions": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_GENERATION_INSTRUCTIONS},
                ),
                "reference_instructions": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_REFERENCE_INSTRUCTIONS},
                ),
                "hard_constraints": (
                    "STRING",
                    {"multiline": True, "default": DEFAULT_HARD_CONSTRAINTS},
                ),
                "api_key": ("STRING", {"default": ""}),
                "model": (API_MODELS, {"default": "gpt-5.5"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 8}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            },
            "optional": {
                "system_prompt_input": PROMPT_INPUT_SOCKET,
                "user_prompt_input": PROMPT_INPUT_SOCKET,
                "reference_image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY

    def generate(
        self,
        system_prompt,
        design_request,
        generation_instructions,
        reference_instructions,
        hard_constraints,
        api_key,
        model,
        quality,
        size,
        moderation,
        n,
        timeout_sec,
        reference_image=None,
        system_prompt_input=None,
        user_prompt_input=None,
    ):
        prompt = _compose_advanced_generate_prompt(
            design_request,
            generation_instructions,
            reference_instructions,
            hard_constraints,
        )
        system_prompt = _resolve_prompt_value(system_prompt, system_prompt_input)
        prompt = _resolve_prompt_value(prompt, user_prompt_input)
        references = _tensor_batch_to_refs(reference_image)
        results = [
            _generate_one(
                prompt,
                system_prompt,
                model,
                quality,
                size,
                moderation,
                references,
                api_key,
                _post_api,
                timeout_sec,
            )
            for _ in range(int(n))
        ]
        return _return_images(results)


class GPTImgAPIEdit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": "edit this image"}),
                "api_key": ("STRING", {"default": ""}),
                "model": (API_MODELS, {"default": "gpt-5.5"}),
                "quality": (QUALITY_VALUES, {"default": "medium"}),
                "size": (SIZE_VALUES, {"default": "1024x1024"}),
                "moderation": (MODERATION_VALUES, {"default": "low"}),
                "timeout_sec": ("INT", {"default": 300, "min": 30, "max": 3600}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "revised_prompt")
    FUNCTION = "edit"
    CATEGORY = NODE_CATEGORY

    def edit(
        self,
        image,
        prompt,
        api_key,
        model,
        quality,
        size,
        moderation,
        timeout_sec,
    ):
        image_b64 = _tensor_to_png_b64(image)
        result = _edit_one(image_b64, prompt, model, quality, size, moderation, api_key, _post_api, timeout_sec)
        return _return_images([result])
