# HyperFrames Composition Project

## Skills — USE THESE FIRST

**Always invoke the relevant skill before writing or modifying compositions.** Skills encode framework-specific patterns (e.g., `window.__timelines` registration, `data-*` attribute semantics, shader-compatible CSS rules) that are NOT in generic web docs. Skipping them produces broken compositions.

| Skill                      | Command                   | When to use                                                                                       |
| -------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------- |
| **hyperframes**            | `/hyperframes`            | Creating or editing HTML compositions, captions, TTS, audio-reactive animation, marker highlights |
| **hyperframes-cli**        | `/hyperframes-cli`        | Dev-loop CLI: init, lint, inspect, preview, render, doctor                                        |
| **hyperframes-media**      | `/hyperframes-media`      | Asset preprocessing: tts (Kokoro), transcribe (Whisper), remove-background (u2net)                |
| **hyperframes-registry**   | `/hyperframes-registry`   | Installing blocks and components via `hyperframes add`                                            |
| **website-to-hyperframes** | `/website-to-hyperframes` | Capturing a URL and turning it into a video — full website-to-video pipeline                      |
| **tailwind**               | `/tailwind`               | Tailwind v4 browser-runtime styles for projects created with `hyperframes init --tailwind`        |
| **gsap**                   | `/gsap`                   | GSAP animations for HyperFrames — tweens, timelines, easing, performance                          |
| **animejs**                | `/animejs`                | Anime.js animations registered on `window.__hfAnime`                                              |
| **css-animations**         | `/css-animations`         | CSS keyframes that HyperFrames can pause and seek                                                 |
| **lottie**                 | `/lottie`                 | `lottie-web` and dotLottie players registered on `window.__hfLottie`                              |
| **three**                  | `/three`                  | Three.js scenes rendered from HyperFrames `hf-seek` events                                        |
| **waapi**                  | `/waapi`                  | Web Animations API motion driven through `document.getAnimations()`                               |

> **Skills not available?** Ask the user to run `npx hyperframes skills` and restart their
> agent session, or install manually: `npx skills add heygen-com/hyperframes`.

## Commands

```bash
npm run dev          # start the preview server (long-running — keep it alive in background)
npm run check        # lint + validate + inspect
npm run render       # render to MP4
npm run publish      # publish and get a shareable link
npx hyperframes lint --verbose  # include info-level findings
npx hyperframes lint --json     # machine-readable output for CI
npx hyperframes docs <topic> # reference docs in terminal
```

> **`npm run dev` is a long-running server, not a one-shot command.** It blocks until stopped.
> In Claude Code, always run it with `run_in_background: true`. Never run it as a foreground
> command — it will time out and the server will die, breaking the browser preview.

## Documentation

**For quick reference**, use the local CLI docs command (no network required):

```bash
npx hyperframes docs <topic>
```

Topics: `data-attributes`, `gsap`, `compositions`, `rendering`, `examples`, `troubleshooting`

**For full documentation**, discover pages via the machine-readable index — do NOT guess URLs:

```
https://hyperframes.heygen.com/llms.txt
```

## Project Structure (v0.34.13 — 루트 승격)

- `index.html` — 메인 컴포지션 (브렌트 캔들 씬, root timeline). `lib/charts/candle.html` 을
  `data-composition-src` 로 import.
- `lib/charts/{candle,line,bar,donut}.html` — 재사용 차트 컴포넌트 라이브러리.
  각각 `<template>` wrapper sub-composition. `data-composition-variables` 로 변수 선언 +
  host 의 `data-variable-values`(JSON)로 데이터 주입.
- `examples/gallery.html` — 4 종 쇼케이스 / 12 씬 시퀀싱 템플릿 (`render -c examples/gallery.html`).
- `generated/<pid>.html` — **자동 생성**(gitignore). `python -m orchestrator.main compose-hyperframes <pid>`
  가 ReportBundle → 다중 씬 컴포지션으로 만든 산출. `render -c generated/<pid>.html` 로 렌더.
- `assets/` — gsap.min.js, fonts/, audio/, pronounce.json (sub-comp 은 루트 기준 `assets/...`
  로 참조; examples 처럼 하위 디렉토리는 `../assets/...`).
- `scripts/` — `render_demo.py`(통합 빌드), `build_narration.py`(ElevenLabs narration).
- `meta.json` — project metadata (id, name)

> **차트 컴포넌트 작성 규칙 (v0.6.76 실측 quirk 대응)**:
> 1. 타임라인은 **authored id 와 runtime 인스턴스 id 둘 다**로 `window.__timelines` 에 등록
>    (`__timelines["candle"]` + `__timelines[__hfTimelineCompId]`). 한쪽만 등록하면 45s 대기 후 실패.
> 2. 데이터 주입은 host 의 `data-variable-values` 를 **DOM 에서 직접 읽음**
>    (`root.closest('[data-variable-values]')`). v0.6.76 에서 `getVariables()` 의 sub-comp
>    host override 가 전파 안 되므로. `getVariables()` + JS 폴백을 보조 경로로 둠.
> 3. `data-composition-src` 는 **프로젝트 루트 밖으로 못 나감** — 차트는 반드시 루트 하위에.

## Linting — ALWAYS RUN AFTER CHANGES

After creating or editing any `.html` composition, **always** run the full check before considering the task complete:

```bash
npm run check
```

Fix all errors before presenting the result. Inspect warnings should be reviewed before rendering.

## Key Rules

1. Every timed element needs `data-start`, `data-duration`, and `data-track-index`
2. Elements with timing **MUST** have `class="clip"` — the framework uses this for visibility control
3. Timelines must be paused and registered on `window.__timelines`:
   ```js
   window.__timelines = window.__timelines || {};
   window.__timelines["composition-id"] = gsap.timeline({ paused: true });
   ```
4. Videos use `muted` with a separate `<audio>` element for the audio track
5. Sub-compositions use `data-composition-src="compositions/file.html"` to reference other HTML files
6. Only deterministic logic — no `Date.now()`, no `Math.random()`, no network fetches
