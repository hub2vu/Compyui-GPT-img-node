# GPT img for ComfyUI

ComfyUI custom nodes for GPT image generation through either OpenAI API keys or
Codex/ChatGPT OAuth.

This node pack is ComfyUI-only. It does not run a separate web UI, Express API,
gallery, session store, or local database.

## Nodes

- `GPT img OAuth Generate`
- `GPT img OAuth Edit`
- `GPT img API Generate`
- `GPT img API Edit`

All nodes return:

- `image`
- `revised_prompt`

## Current Registry Status

As of 2026-04-25, this node pack is published to the Comfy Registry as:

```text
node_id: gpt-img-node
publisher: hub2vu
version: 0.1.0
status: NodeVersionStatusPending
extract_status: success
```

Because the version is still `Pending`, it may not appear in ComfyUI Manager
search yet. Manual Git installation works now. Manager installation should become
available after the Registry version becomes `NodeVersionStatusActive`.

You can check the live Registry status with:

```powershell
Invoke-RestMethod "https://api.comfy.org/nodes/gpt-img-node/versions?include_status_reason=true" | ConvertTo-Json -Depth 8
```

## Manual Install

Clone this repository into `ComfyUI/custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hub2vu/Compyui-GPT-img-node.git GPT-img
```

Restart ComfyUI after installing.

## API Nodes

Use `GPT img API Generate` or `GPT img API Edit`.

Enter an OpenAI API key in the node's `api_key` field, or leave it empty and set
`OPENAI_API_KEY` in your environment.

API usage is billed to the API key owner by OpenAI.

## OAuth Nodes

Use `GPT img OAuth Generate` or `GPT img OAuth Edit`.

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
