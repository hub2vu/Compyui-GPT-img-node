# ComfyUI용 GPT img

언어: [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

OpenAI API 키 또는 Codex/ChatGPT OAuth로 GPT 이미지 생성을 사용할 수 있는
ComfyUI 커스텀 노드입니다.

이 노드팩은 ComfyUI 전용입니다. 별도 웹 UI, Express API, 갤러리, 세션 저장소,
로컬 데이터베이스를 실행하지 않습니다.

## 노드

- `GPT img OAuth Generate`
- `GPT img OAuth Generate Advanced`
- `GPT img OAuth Edit`
- `GPT img API Generate`
- `GPT img API Generate Advanced`
- `GPT img API Edit`

모든 노드는 다음을 반환합니다:

- `image`
- `revised_prompt`

## 현재 Registry 상태

2026-04-25 기준, 이 노드팩은 Comfy Registry에 다음 상태로 등록되어 있습니다:

```text
node_id: gpt-img-node
publisher: hub2vu
version: 0.1.0
status: NodeVersionStatusPending
extract_status: success
```

이 저장소의 현재 버전은 `0.1.1`입니다. 새 버전을 Registry에 올리려면 publish
workflow를 다시 실행해야 합니다. 공개된 Registry 버전 상태가 아직 `Pending`이므로
ComfyUI Manager 검색에 바로 보이지 않을 수 있습니다. 현재는 수동 Git 설치가
가능합니다. Registry 버전 상태가 `NodeVersionStatusActive`가 되면 Manager 설치도
가능해질 예정입니다.

실시간 Registry 상태는 다음 명령으로 확인할 수 있습니다:

```powershell
Invoke-RestMethod "https://api.comfy.org/nodes/gpt-img-node/versions?include_status_reason=true" | ConvertTo-Json -Depth 8
```

## 수동 설치

이 저장소를 `ComfyUI/custom_nodes` 안에 clone하세요:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hub2vu/Compyui-GPT-img-node.git GPT-img
```

설치 후 ComfyUI를 재시작하세요.

## API 노드

`GPT img API Generate` 또는 `GPT img API Edit`를 사용하세요.

노드의 `api_key` 입력칸에 OpenAI API 키를 넣거나, 비워둔 상태에서 환경변수
`OPENAI_API_KEY`를 설정할 수 있습니다.

API 사용 요금은 API 키 소유자의 OpenAI 계정에 청구됩니다.

## Advanced Generate 노드

사용자의 디자인 요청과 재사용 가능한 생성 규칙을 분리하고 싶을 때
`GPT img OAuth Generate Advanced` 또는 `GPT img API Generate Advanced`를 사용하세요.

Advanced generate 입력:

- `design_request`: 최우선으로 따를 의상/디자인 요청. 어떤 언어로 작성해도 됩니다.
- `generation_instructions`: 출력 형식과 품질 규칙 같은 재사용 템플릿
- `reference_instructions`: reference image를 해석하는 방법
- `hard_constraints`: 모델 없음, 로고 없음, 텍스트 없음 같은 금지 조건

노드는 자동으로 conflict rule을 추가합니다. 다른 지시가 `design_request`와
충돌하면 `design_request`를 우선합니다.

## OAuth 노드

`GPT img OAuth Generate` 또는 `GPT img OAuth Edit`를 사용하세요.

필요한 것:

- `npx`를 사용할 수 있는 Node.js
- Codex/ChatGPT OAuth 로그인

필요하면 한 번 로그인하세요:

```powershell
npx @openai/codex login
```

OAuth 노드는 `10531` 포트에서 OAuth proxy를 자동 시작할 수 있습니다. 로그는
다음 위치에 기록됩니다:

```text
custom_nodes/GPT-img/logs/openai-oauth.log
```

## 참고

- 이 노드팩에는 별도 Python 패키지 설치가 필요하지 않습니다.
- API 키를 workflow나 repository에 커밋하지 마세요.
- OAuth/API 노드는 모두 ComfyUI 카테고리 `GPT img` 아래에 표시됩니다.
