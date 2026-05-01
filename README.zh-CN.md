# GPT img for ComfyUI

语言: [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

这是一个 ComfyUI 自定义节点包，可通过 OpenAI API Key 或 Codex/ChatGPT
OAuth 使用 GPT 图像生成和 ChatGPT LLM 文本回复。

本节点包仅用于 ComfyUI。它不会运行独立的 Web UI、Express API、图库、会话存储
或本地数据库。

## 节点

- `GPT img OAuth Generate`
- `GPT img OAuth Generate Advanced`
- `GPT img OAuth Edit`
- `GPT img OAuth ChatGPT LLM`
- `GPT img API Generate`
- `GPT img API Generate Advanced`
- `GPT img API Edit`
- `GPT img API ChatGPT LLM`

图像节点会返回:

- `image`
- `revised_prompt`

ChatGPT LLM 节点会返回:

- `text`
- `raw_response_json`

## 当前 Registry 状态

截至 2026-04-25，本节点包已发布到 Comfy Registry，状态如下:

```text
node_id: gpt-img-node
publisher: hub2vu
version: 0.1.0
status: NodeVersionStatusPending
extract_status: success
```

当前仓库版本为 `0.1.6`。如需把新版本提交到 Registry，请重新运行 publish
workflow。由于已发布的 Registry 版本状态仍为 `Pending`，它可能暂时不会出现在
ComfyUI Manager 搜索结果中。目前可以手动通过 Git 安装。等 Registry 版本状态变为
`NodeVersionStatusActive` 后，应该就可以通过 Manager 安装。

可以用以下命令查看实时 Registry 状态:

```powershell
Invoke-RestMethod "https://api.comfy.org/nodes/gpt-img-node/versions?include_status_reason=true" | ConvertTo-Json -Depth 8
```

## 手动安装

将本仓库 clone 到 `ComfyUI/custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hub2vu/Comfyui-GPT-img-node.git GPT-img
```

安装后重启 ComfyUI。

## API 节点

使用 `GPT img API Generate`、`GPT img API Edit` 或 `GPT img API ChatGPT LLM`。

可以在节点的 `api_key` 输入框中填写 OpenAI API Key；如果留空，则会使用环境变量
`OPENAI_API_KEY`。

API 调用费用会由 OpenAI 向 API Key 所属账号计费。

## ChatGPT LLM 节点

当你想在 ComfyUI workflow 中获得 ChatGPT 模型的文本回复时，可以使用
`GPT img OAuth ChatGPT LLM` 或 `GPT img API ChatGPT LLM`。

ChatGPT LLM 输入:

- `system_prompt`: 传给 assistant 的 developer/system 风格指令
- `prompt`: 用户请求
- `model`: 要调用的 ChatGPT 模型
- `reasoning_effort`: `minimal`、`low`、`medium`、`high` 或 `xhigh`
- `max_output_tokens`: 最大文本输出 token 数
- `timeout_sec`: 请求超时时间

API 节点还包含 `api_key`。OAuth 节点还包含 `oauth_port` 和 `auto_start_oauth`。

ChatGPT LLM 节点也提供可选的提示词输入 socket:

- `system_prompt_input`: 连接后会覆盖 `system_prompt` 的可选 STRING socket
- `user_prompt_input`: 连接后会覆盖 `prompt` 的可选 STRING socket

如果提示词 socket 没有连接，节点会使用直接在节点控件中输入的文本。
`system_prompt` 控件会追加在原有图像生成控件之后，因此旧 workflow 的原有控件顺序会保持不变。

ChatGPT LLM 模型选项包含 `gpt-5.5-pro`。图像生成节点保留独立模型列表，因为 pro
模型的 streaming 支持可能不同。

## 图像 Generate 提示词输入

图像生成节点现在同时提供直接输入的提示词控件和可选的提示词输入 socket。

提示词输入:

- `system_prompt`: 直接输入生成指令的控件
- `prompt` 或 advanced 提示词字段: 直接输入用户请求的控件
- `system_prompt_input`: 连接后会覆盖 `system_prompt` 的可选 STRING socket
- `user_prompt_input`: 连接后会覆盖直接输入的用户提示词的可选 STRING socket

如果提示词 socket 没有连接，节点会使用直接在节点控件中输入的文本。

## Advanced Generate 节点

当你想把用户的设计需求和可复用的生成规则分开时，可以使用
`GPT img OAuth Generate Advanced` 或 `GPT img API Generate Advanced`。

Advanced generate 输入:

- `design_request`: 最优先遵循的服装/设计需求，可使用任意语言
- `generation_instructions`: 输出格式和质量要求等可复用模板
- `reference_instructions`: reference image 的使用和解释方式
- `hard_constraints`: 例如不要模特、不要 logo、不要文字等限制

节点会自动加入 conflict rule。如果其他指令与 `design_request` 冲突，
会优先遵循 `design_request`。

## OAuth 节点

使用 `GPT img OAuth Generate`、`GPT img OAuth Edit` 或 `GPT img OAuth ChatGPT LLM`。

要求:

- 安装 Node.js，并可使用 `npx`
- 完成 Codex/ChatGPT OAuth 登录

如有需要，先登录一次:

```powershell
npx @openai/codex login
```

OAuth 节点可以在 `10531` 端口自动启动 OAuth proxy。日志会写入:

```text
custom_nodes/GPT-img/logs/openai-oauth.log
```

## 备注

- 本节点包不需要额外安装 Python 包。
- 不要把 API Key 提交到 workflow 或 repository 中。
- OAuth 和 API 节点都会显示在同一个 ComfyUI 分类 `GPT img` 下。
