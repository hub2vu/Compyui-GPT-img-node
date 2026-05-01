# GPT img for ComfyUI

Languages: [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

ComfyUI custom nodes for GPT image generation and ChatGPT LLM text responses
through either OpenAI API keys or Codex/ChatGPT OAuth.

This node pack is ComfyUI-only. It does not run a separate web UI, Express API,
gallery, session store, or local database.

## Nodes

- `GPT img OAuth Generate`
- `GPT img OAuth Generate Advanced`
- `GPT img OAuth Edit`
- `GPT img OAuth ChatGPT LLM`
- `GPT img API Generate`
- `GPT img API Generate Advanced`
- `GPT img API Edit`
- `GPT img API ChatGPT LLM`

Image nodes return:

- `image`
- `revised_prompt`

ChatGPT LLM nodes return:

- `text`
- `raw_response_json`

## Current Registry Status

As of 2026-04-25, this node pack is published to the Comfy Registry as:

```text
node_id: gpt-img-node
publisher: hub2vu
version: 0.1.0
status: NodeVersionStatusPending
extract_status: success
```

This repository is now `0.1.6`. Re-run the publish workflow to submit the newer
version to the Registry. Because the published version is still `Pending`, it may
not appear in ComfyUI Manager search yet. Manual Git installation works now.
Manager installation should become available after a Registry version becomes
`NodeVersionStatusActive`.

You can check the live Registry status with:

```powershell
Invoke-RestMethod "https://api.comfy.org/nodes/gpt-img-node/versions?include_status_reason=true" | ConvertTo-Json -Depth 8
```

## Manual Install

Clone this repository into `ComfyUI/custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hub2vu/Comfyui-GPT-img-node.git GPT-img
```

Restart ComfyUI after installing.

## API Nodes

Use `GPT img API Generate`, `GPT img API Edit`, or `GPT img API ChatGPT LLM`.

Enter an OpenAI API key in the node's `api_key` field, or leave it empty and set
`OPENAI_API_KEY` in your environment.

API usage is billed to the API key owner by OpenAI.

## ChatGPT LLM Nodes

Use `GPT img OAuth ChatGPT LLM` or `GPT img API ChatGPT LLM` when you want a text
response from a ChatGPT model inside a ComfyUI workflow.

ChatGPT LLM inputs:

- `system_prompt`: developer/system-style instructions for the assistant
- `prompt`: the user request
- `model`: the ChatGPT model to call
- `reasoning_effort`: `minimal`, `low`, `medium`, `high`, or `xhigh`
- `max_output_tokens`: maximum text output budget
- `timeout_sec`: request timeout

The API node also has `api_key`. The OAuth node also has `oauth_port` and
`auto_start_oauth`.

ChatGPT LLM nodes also expose optional prompt input sockets:

- `system_prompt_input`: optional STRING socket that overrides `system_prompt`
  when connected
- `user_prompt_input`: optional STRING socket that overrides `prompt` when
  connected

If a prompt socket is not connected, the node uses the text entered directly in
the node widget. The `system_prompt` widget is appended after the original image
generation widgets so older saved workflows keep their existing widget order.

ChatGPT LLM model choices include `gpt-5.5-pro`. The image generation nodes keep
their separate model list because pro models can have different streaming support.

## Image Generate Prompt Inputs

Image generate nodes now expose both direct prompt widgets and optional prompt
input sockets.

Prompt inputs:

- `system_prompt`: direct widget input for generation instructions
- `prompt` or advanced prompt fields: direct widget input for the user request
- `system_prompt_input`: optional STRING socket that overrides `system_prompt`
  when connected
- `user_prompt_input`: optional STRING socket that overrides the direct user
  prompt when connected

If a prompt socket is not connected, the node uses the text entered directly in
the node widget.

## Advanced Generate Nodes

Use `GPT img OAuth Generate Advanced` or `GPT img API Generate Advanced` when you
want to separate the user's design request from reusable generation rules.

Advanced generate inputs:

- `design_request`: the authoritative garment/design request, in any language
- `generation_instructions`: reusable output format and quality instructions
- `reference_instructions`: how reference images should be interpreted
- `hard_constraints`: negative constraints such as no model, no logo, no text

The node automatically adds a conflict rule so `design_request` wins if another
instruction conflicts with it.

## OAuth Nodes

Use `GPT img OAuth Generate`, `GPT img OAuth Edit`, or
`GPT img OAuth ChatGPT LLM`.

Requirements:

- Node.js with `npx`
- Codex/ChatGPT OAuth login

Login once if needed:

```powershell
npx @openai/codex login
```

The OAuth nodes can auto-start the OAuth proxy on port `10531`. Logs are written
to:

```text
custom_nodes/GPT-img/logs/openai-oauth.log
```

## Notes

- No Python package install is required for this node pack.
- Do not commit API keys into workflows or repositories.
- The OAuth and API nodes use the same ComfyUI category: `GPT img`.
