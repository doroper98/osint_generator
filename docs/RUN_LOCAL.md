<!--
tier: 3
last_synced_with: v0.15.1
ssot_for: [local-run-guide]
depends_on: [../CHANGELOG.md]
last_review: 2026-05-24
-->

# 로컬에서 대본+음성 영상 테스트 (ElevenLabs)

이 문서는 **이미 만들어진 샘플 프로젝트**(`samples/hualien2024/` — 2024 대만 화롄
지진 브리핑의 research/script/scene JSON)로, 본인 PC에서 **나레이션 음성을 입히고
영상까지** 뽑아보는 최소 절차입니다. 전체 파이프라인(research/script 생성)을 다시
돌릴 필요 없이 voice + render 만 테스트합니다.

> 클라우드 세션에서 만든 `projects/hualien2024/` 는 그 세션 안에만 있어 본인 PC엔
> 없습니다. 그래서 동일 산출물을 `samples/` 로 커밋해 두었습니다.

## 0. 준비물

- Python 3.11+, Node.js 18+ (Remotion 렌더용)
- **ElevenLabs API 키** — elevenlabs.io 가입 → 프로필 → API Keys 에서 발급.
  (외부 API 라 텍스트가 ElevenLabs 로 전송됩니다 — 로컬 프라이버시는 깨짐. opt-in.)

## 1. 저장소 준비

```bash
git clone <repo> osint_generator        # 또는 git pull
cd osint_generator
git checkout claude/eager-hopper-wdBT5
pip install -r requirements.txt
```

## 2. 샘플을 projects 로 복사

```bash
# Windows (PowerShell)
Copy-Item -Recurse samples\hualien2024 projects\hualien2024

# macOS/Linux
mkdir -p projects && cp -r samples/hualien2024 projects/hualien2024
```

## 3. 음성 입히기 (ElevenLabs)

```bash
# Windows:  set ELEVENLABS_API_KEY=sk_...   /  PowerShell: $env:ELEVENLABS_API_KEY="sk_..."
export ELEVENLABS_API_KEY=sk_...           # macOS/Linux
python -m orchestrator.main build-audio hualien2024 --backend elevenlabs
```

- 목소리를 따로 안 정하면 계정의 **첫 목소리가 자동 선택**됩니다. 특정 목소리를 쓰려면
  `ELEVENLABS_VOICE_ID` 환경변수 지정.
- 결과: `projects/hualien2024/08_audio/narration/*.wav` (세그먼트별 음성) +
  `08_audio/audio_manifest.json`. wav 를 바로 재생해 음성만 먼저 확인해도 됩니다.

## 4. 음성 입힌 영상 렌더

```bash
cd remotion && npm install && cd ..        # 최초 1회
python -m orchestrator.main render-debug hualien2024
```

- 본인 PC 는 네트워크 제한이 없으면 Remotion 이 chrome-headless-shell 을 자동 다운로드
  합니다(최초 1회). 사내망 등으로 막히면 `--browser-executable <경로>` 로 지정.
- 결과: `projects/hualien2024/09_render/draft_debug.mp4` — 나레이션 음성이 슬라이드
  타이밍에 맞춰 들어간 영상. 미검증/추론/주장 라벨 배지도 표시됩니다.

## 5. 다른 주제로 처음부터 (선택)

`new-project → plan-intake → submit-intake → build-source-registry →
build-research-dossier → build-script → build-scene → build-audio → render-debug`.
research/script 단계는 `claude` CLI(구독 로그인)가 필요합니다.

## 백엔드 바꾸기

- 로컬 무료/프라이버시: `--backend local` (`OSINT_TTS_CMD` 에 로컬 TTS 명령) 또는
  `--backend voicebox` (Voicebox 앱 실행 후 `OSINT_VOICEBOX_PROFILE` 지정).
- 테스트용 무음: `--backend stub`.
