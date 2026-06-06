# NEXT SESSION PROMPT — v0.34.14 시작점

> 본 파일은 **다음 Claude Code 세션 시작 시 첫 메시지로 paste** 해 사용한다.
> v0.34.13 (2026-06-06, 옵션 B 1차 완료) 이후 작업을 이어 받을 컨텍스트.
> SSOT: HANDOFF.md, docs/PROFESSIONAL_REBUILD_PLAN.md, DEVLOG.md (append-only).

## v0.34.13 완료 요약 (옵션 B 1차)

- **차트 컴포넌트 라이브러리** `hyperframes/lib/charts/{candle,line,bar,donut}.html` 신설.
  각각 `<template>` sub-composition + `data-*` 변수 주입 + GSAP `fromTo` 타임라인.
- **프로젝트 루트 승격**: `hyperframes/demo/` → `hyperframes/` (번들러가 루트 밖 import 불가
  실측 → 요청 경로 `lib/charts/` 쓰려면 필수, 사용자 결정). `git mv` 히스토리 보존.
- `index.html` 이 `lib/charts/candle.html` 을 `data-composition-src` 로 import (브렌트 씬
  narration/자막 sync·Ken Burns 보존). `examples/gallery.html` 시퀀싱 템플릿 신설.
- **실측 확립한 sub-comp 패턴 (v0.6.76)**: ① 타임라인은 authored id + runtime id 둘 다 등록
  ② 데이터 주입은 host `data-variable-values` 를 DOM 직독(getVariables host override 미전파)
  ③ `data-composition-src` 는 루트 밖 못 나감. (상세: DEVLOG v0.34.13 / hyperframes/CLAUDE.md)
- 빌드 한 줄: `python hyperframes/scripts/render_demo.py --with-narration` (경로 루트 기준 갱신됨).

---

## 컨텍스트 한 줄

OSINT 한국어 영상 자동 생성 시스템. 사용자 평가 "전반적으로 너무 구려" 이후
**v0.30~0.34.12 영상미 재빌드 + Remotion 폐기 + HyperFrames 전환** 진행 중. 음성
파이프라인(ElevenLabs + 발음 사전 + sync) 완성. 본격 차트·씬 라이브러리·자동화는 다음.

## 지금까지 (v0.30 → v0.34.12, 머지 완료)

### Phase A — 영상미 디자인 시스템 갈아엎기
- **v0.30.0**: `remotion/src/design.ts` 토큰 + ChartFrame/Axis/Callout/ReferenceRegion 공용 컴포넌트.
- **v0.31.0**: XY family 정통 재구현 (line/area/dual_line/forecast).
- **v0.32.0~0.32.2**: Bar/Point family 9 종 + demo_props + `.env` 로딩 + `build-audio-demo`.
- **v0.33.0~0.33.1**: 사용자 평가 "촌스러움" → Aurora glass / glow / Okabe-Ito 8색 폐기,
  light dashboard + 오렌지 단일 accent + Pretendard + Ken Burns + 다크 broadcast 자막
  으로 전면 재구성. 사용자 mp4 검수.

### Phase B — Remotion 폐기 + HyperFrames 전환
- **v0.34.0~0.34.4**: HyperFrames (HeyGen 오픈소스, HTML+GSAP→mp4) 프로토타입.
  브렌트 유가 line→캔들 12 주봉. 자막 sync, draw-on, 콜아웃, Ken Burns 다 작동.
- **v0.34.5~0.34.7**: 음성 파이프라인 — `build_narration.py` (ElevenLabs API) +
  `render_demo.py` (portable ffmpeg via imageio-ffmpeg) + `mutagen` mp3 duration.
- **v0.34.8**: 음성·자막 sync drift 픽스 — `cuesync.json` + `index.synced.html` 자동 patch.
- **v0.34.9**: ElevenLabs `voice_settings` hardcode 제거, voice library default 사용.
- **v0.34.10**: TTS-AP-054~057 발음 사전 신규 (`orchestrator/tts_pronounce.py` +
  `pronounce.json`) — 16 unit tests.
- **v0.34.11**: cue 의 `(text, narration)` 명시 분리 (자막 = 한국어, narration = 발음 표기).
- **v0.34.12**: 자동 발음 변환 **default OFF** (날짜 "오 월 사 일" 끊어 읽기 사고 해소).
  `--auto-pronounce` opt-in.

### 핵심 산출물 (사용자 머신 실행)

```cmd
cd C:\01_Antigravity\osint_generator
git pull origin main
python hyperframes\scripts\render_demo.py --with-narration
```

→ 브렌트 유가 캔들 30초 mp4 (음성 + 자막 + 콜아웃 + Ken Burns), `.env` 의
`ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` 자동 사용.

## 앞으로 (v0.34.13~) — 우선순위 결정

사용자 합의된 순서 (HANDOFF + PROFESSIONAL_REBUILD_PLAN 통합):

| # | 항목 | 비고 |
|---|---|---|
| ~~**B**~~ | ~~**차트 family HyperFrames 컴포넌트화**~~ | **v0.34.13 1차 완료** — candle/line/bar/donut 4 종. SSOT 패턴 확립: `hyperframes/lib/charts/<type>.html` (template) + host `data-variable-values` 주입 + GSAP timeline. **확장 잔여**: stacked/waterfall/scatter/heatmap/gantt/network (= 아래 B-ext). |
| **B-ext** | **차트 family 확장** | 남은 차트 종류 추가 (stacked_bar/waterfall/scatter/bubble/heatmap/gantt/network/sankey). candle/line/bar/donut 의 컨트랙트(template + host 변수 DOM 직독 + 타임라인 이중 키)를 그대로 따른다. network/sankey 는 헤드리스 레이아웃 사전계산 필요. |
| **C** | **agents_reviewer 번들 → HyperFrames 자동 변환** | `orchestrator/render_io.py` 의 후속. ReportBundle → 다중 scene HyperFrames 컴포지션 자동 생성. `index.html` 이 sub-composition 들을 `data-composition-src` 로 import. Scene 별 cue 데이터 + narration 명시 자동 추출(LLM)·수동 override 패턴. |
| **D** | **인물 카드 + 엔티티 연결선 draw** | 날리지식 패턴 ③ ④. 인물 사진/플래그 + 부드러운 fade + 두 엔티티 간 Bezier path stroke-dash draw-on. SVG 컴포넌트 + GSAP 통합. |
| **E** | **다크 지도 GeoScene** | 날리지식 패턴 ⑤. d3-geo + world-atlas + ISO 매핑. 국가 하이라이트 + 마커 + 아크. dark theme 별도 디자인 토큰. |
| **A** | **forced-alignment (자막 정밀 sync)** | HANDOFF 보류 1. whisper 단어 타임스탬프 → cue 의 자막 시점 정밀화. 사용자 머신 전용 (huggingface 차단). 현재 v0.34.12 의 timing (cuesync.json 기반) 도 충분히 정확하므로 우선순위 낮음. |
| **F** | **자동 캐치 트리거** | HANDOFF 보류 2. agents_reviewer push → watcher → 자동 import + 빌드. 인프라. |
| **G** | **Codex 영상미 검수 체계** | v0.33.x 사용자 5번 피드백 부채. 매 PATCH 키프레임 추출 → 영상 LLM 검사. CLAUDE.md 의 C10 (코드 리뷰) 와 분리된 새 카테고리. |
| **H** | **pronounce.json 운영** | 새 misread 발견 시 사전 갱신 + 회귀 테스트 추가. 누적 운영. |

**제 추천 시작점**: **C** (agents_reviewer 번들 → 다중 씬 자동 변환) — B 의 컴포넌트 토대가
생겼으니, 이제 `examples/gallery.html` 시퀀싱 패턴을 ReportBundle → N 씬 자동 생성으로 잇는다.
차트 종류가 더 필요해지면 그때 **B-ext** 로 해당 차트만 추가(컨트랙트 동일).

## 진행 규칙 (CLAUDE.md 참조)

- C0 영상미 최우선 (정확성·검증 위에서).
- C5 버전 표기 의무 (VERSION 파일 + `vX.Y.Z:` commit prefix).
- C10 외부 코드 리뷰 의무 (MINOR/MAJOR 후 codex review).
- append-only (CHANGELOG/DEVLOG/ANTIPATTERNS 과거 수정 금지).
- 사용자 명시 요청 없이는 PR 생성 / main push 금지.
- 작업 브랜치: 새 세션은 새 `claude/<slug>` 브랜치 생성해 작업 (필요시).

## 즉시 사용할 첫 프롬프트 (사용자 paste 용)

```
이전 세션 v0.34.13 머지 완료 (옵션 B 1차 — candle/line/bar/donut 컴포넌트 + 루트 승격).
다음 작업은 hyperframes/scripts/NEXT_SESSION_PROMPT.md 의 우선순위 표 참조.
옵션 C (agents_reviewer 번들 → HyperFrames 다중 씬 자동 변환) 부터 시작해.
examples/gallery.html 의 시퀀싱 패턴을 ReportBundle → N 씬 자동 생성으로 잇고,
각 씬은 lib/charts/<type>.html 을 data-composition-src + data-variable-values 로 주입.
scene 별 cue/narration 자동 추출(LLM)·수동 override 패턴 설계.

먼저 hyperframes/scripts/NEXT_SESSION_PROMPT.md 와 HANDOFF.md,
hyperframes/CLAUDE.md(sub-comp 작성 규칙), DEVLOG v0.34.13 정독 후 시작.
```

(원하면 다른 옵션 [B-ext/D/E/A 등] 으로 교체)
