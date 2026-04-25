# GPT img for ComfyUI

语言: [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

这是一个 ComfyUI 自定义节点包，可通过 OpenAI API Key 或 Codex/ChatGPT
OAuth 使用 GPT 图像生成。

本节点包仅用于 ComfyUI。它不会运行独立的 Web UI、Express API、图库、会话存储
或本地数据库。

## 节点

- `GPT img OAuth Generate`
- `GPT img OAuth Edit`
- `GPT img API Generate`
- `GPT img API Edit`

所有节点都会返回:

- `image`
- `revised_prompt`

## 当前 Registry 状态

截至 2026-04-25，本节点包已发布到 Comfy Registry，状态如下:

```text
node_id: gpt-img-node
publisher: hub2vu
version: 0.1.0
status: NodeVersionStatusPending
extract_status: success
```

由于版本状态仍为 `Pending`，它可能暂时不会出现在 ComfyUI Manager 搜索结果中。
目前可以手动通过 Git 安装。等 Registry 版本状态变为
`NodeVersionStatusActive` 后，应该就可以通过 Manager 安装。

可以用以下命令查看实时 Registry 状态:

```powershell
Invoke-RestMethod "https://api.comfy.org/nodes/gpt-img-node/versions?include_status_reason=true" | ConvertTo-Json -Depth 8
```

## 手动安装

将本仓库 clone 到 `ComfyUI/custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hub2vu/Compyui-GPT-img-node.git GPT-img
```

安装后重启 ComfyUI。

## API 节点

使用 `GPT img API Generate` 或 `GPT img API Edit`。

可以在节点的 `api_key` 输入框中填写 OpenAI API Key；如果留空，则会使用环境变量
`OPENAI_API_KEY`。

API 调用费用会由 OpenAI 向 API Key 所属账号计费。

## OAuth 节点

使用 `GPT img OAuth Generate` 或 `GPT img OAuth Edit`。

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
