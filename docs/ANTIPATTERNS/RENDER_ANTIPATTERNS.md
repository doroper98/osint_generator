<!--
tier: 3
last_synced_with: v0.15.4
ssot_for: [render-antipatterns]
depends_on: [../13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-05-23
-->

# Render Antipatterns

본 문서는 Remotion / FFmpeg 렌더 관련 안티패턴 카탈로그입니다. **append-only**.
각 항목은 [README.md](README.md) 의 표준 포맷을 따릅니다.

---

## RENDER-AP-001 — Remotion 의 chromium headless-shell 자동 다운로드가 네트워크 allowlist 에 막힘

- **증상 (symptom)**: `npx remotion render` 첫 실행 시 `remotion.media` 에서
  chrome-headless-shell zip 을 받으려다 `403 ... Host not in allowlist` 로 실패.
  번들링(100%)까지는 되지만 브라우저 확보 단계에서 중단되어 mp4 가 생성되지 않음.
  (v0.11.0 수직 슬라이스 V3 첫 실 렌더에서 발견. 원격 실행 환경의 outbound 정책.)

- **원인 (root cause)**: Remotion 은 렌더에 headless chromium 을 쓰며, 없으면 자체 CDN
  에서 자동 다운로드한다. 격리된 실행 환경은 npm 레지스트리는 허용해도 remotion.media
  같은 부가 CDN 은 allowlist 에 없을 수 있다. 또한 머신에 있는 **full chrome** 를
  `--browser-executable` 로 줘도 "Old Headless mode has been removed" 로 launch 실패 —
  Remotion 은 **chrome-headless-shell**(old headless 구현)이 필요하다.

- **구조적 조치 (structural fix, v0.11.1)**:
  - `orchestrator/main.py:render-debug` 에 `_detect_headless_shell()` 추가 — 머신에 이미
    설치된 chrome-headless-shell 바이너리를 자동탐지(Playwright `/opt/pw-browsers/
    chromium_headless_shell-*/.../headless_shell`, ms-playwright 캐시, puppeteer 캐시)해
    `--browser-executable` 로 넘긴다.
  - 우선순위: `--browser-executable` 플래그 > `OSINT_HEADLESS_SHELL` 환경변수 > 자동탐지.
  - 못 찾으면 플래그 미부착 → 정상 환경에서는 Remotion 자동 다운로드로 폴백.
  - full chrome 가 아니라 **headless_shell** 만 채택 (full chrome 는 launch 실패 확인).

- **발견 버전 (discovered)**: v0.11.0.
- **해결 버전 (resolved)**: v0.11.1 — 자동탐지 + 플래그/환경변수 override. 실측: headless_shell
  지정 시 13170 프레임(7분19초) 렌더 성공, 27MB mp4 생성.

- **상태 (status)**: `resolved` (본 실행 환경). 다른 환경에서는 (a) 자동 다운로드 허용,
  (b) `OSINT_HEADLESS_SHELL` 지정, (c) `npx remotion browser ensure` 로 사전 확보 중 택1.

- **알려진 한계**:
  - 자동탐지 경로는 알려진 위치(Playwright/puppeteer 캐시)만 본다. 다른 위치의 shell 은
    `--browser-executable` / `OSINT_HEADLESS_SHELL` 로 명시해야 한다.
  - chrome-headless-shell 버전과 Remotion 요구 버전이 크게 어긋나면 호환 문제 가능 —
    그 경우 Remotion 권장 버전을 별도 확보.

---

## RENDER-AP-002 — Windows 에서 subprocess 가 `npx`(=npx.cmd) 를 못 찾음

- **증상 (symptom)**: Windows 에서 `render-debug` 가 `error: npx/node 를 찾을 수 없습니다`
  로 실패. 그런데 같은 cmd 창에서 `npx --version` 은 정상 동작(11.x). Node 도 설치돼
  있음(`node --version` v24). (실제 사용자 한국어 Windows 에서 발견.)

- **원인 (root cause)**: Windows 에서 npx 실행파일은 `npx.cmd`(배치)다. Python
  `subprocess.run(["npx", ...], shell=False)` 는 CreateProcess 를 쓰는데, CreateProcess
  는 PATHEXT 를 적용하지 않아 확장자 없는 `npx` 를 찾지 못하고 FileNotFoundError 를
  던진다. (cmd 셸은 PATHEXT 로 `.cmd` 를 찾아주므로 셸에선 됨.)

- **구조적 조치 (structural fix, v0.15.4)**:
  - `orchestrator/main.py:render-debug` 가 `shutil.which("npx")` 로 실제 경로(Windows 면
    `...\npx.cmd`)를 해석한다. None 이면 친절한 설치 안내.
  - 해석된 경로가 `.cmd`/`.bat` 이고 `os.name == "nt"` 면 `["cmd", "/c", npx, *args]` 로
    실행 (배치파일은 CreateProcess 직접 실행 불가 → cmd.exe 경유). 그 외엔 `[npx, *args]`.

- **발견 버전 (discovered)**: v0.15.3 (사용자 Windows 첫 렌더 시도).
- **해결 버전 (resolved)**: v0.15.4.

- **상태 (status)**: `resolved`. POSIX(Linux/macOS)는 `shutil.which` 가 npx 스크립트를
  그대로 반환·실행되어 영향 없음.

- **알려진 한계**:
  - cmd.exe /c 경유 시 인자는 `subprocess.list2cmdline` 규칙으로 인용된다. 산출물 경로에
    특수문자가 많으면 별도 검증 필요(현재 경로엔 공백 정도만 가정).

- **같은 클래스 재발**: LLM subprocess(codex/claude)도 동일한 Windows `.cmd` 셈 문제를
  겪었다 → `LLM-AP-006`(v0.35.1, `workers/base_llm_worker.py:_resolve_launcher`).
  현재 두 call site(render-debug 인라인 / `_resolve_launcher`)가 같은 패턴을 각자
  구현한다. 세 번째 재발 시 공용 유틸로 추출 권장(워커→orchestrator.main 역의존은 피하고
  중립 모듈에 둘 것).

---

## RENDER-AP-003 — 차트 없는 섹션이 prose 전문을 화면 body 로 박아 "정적 보고서를 화면에 박은" 글자 벽이 됨

- **증상 (symptom)**: 실 번들(「AI 메모리의 역설」)을 compose → 렌더한 영상에서, 차트가
  없는 섹션("메모리 벽" 563자 / "두 갈래 길" 711자)이 **섹션 통문단 전체를 화면 본문에
  그대로 표시**. 화면이 빽빽한 글자 벽이 됨 — C0("화면은 글자 도배가 아니라 key-takeaway
  + 비주얼") 정면 위반. (사용자 스크린샷으로 발견.)

- **원인 (root cause)**: `orchestrator/hyperframes_compose.py` 의 text 씬 생성이
  `body = sec.pull_quote or prose` 였다. pull_quote 가 없는 섹션은 prose **전문**으로
  폴백 → body 에 수백 자가 박힘. (prose 는 이미 자막 큐로도 흐르므로 이중 노출이기도 함.)

- **구조적 조치 (structural fix, v0.35.2)**:
  - `_text_scene_body(pull_quote, prose, cap=140)` 신설: pull_quote 우선, 없으면
    prose **첫 문장만** cap 자로 발췌한 key-takeaway 한 줄을 body 로. prose 전문은
    body 가 아니라 자막 큐로만 흐른다. text 씬 생성이 이 헬퍼를 쓴다.
  - 회귀 테스트 `tests/test_hyperframes_compose.py`: pull_quote 없는 섹션의 body 가
    첫 문장만(통문단 아님)인지 / 마침표 없는 초장문도 cap 으로 잘리는지 / pull_quote
    우선인지 잠금.

- **발견 버전 (discovered)**: v0.35.1 (사용자 첫 실 번들 렌더).
- **해결 버전 (resolved)**: v0.35.2.

- **상태 (status)**: `resolved` (결정론 경로). codex 연출(`--planner codex`)은 그 위에서
  자막을 key-takeaway 로 재작성 + 헤드라인/강조/순서를 더한다(연출 레이어, 본 수정과 직교).

- **알려진 한계**: codex 가 text 씬의 핵심 한 줄(body/pull-quote)을 직접 고르게 하려면
  `PlannedScene` 에 필드 추가가 필요(현재 codex 는 heading override 만). 후속 증분 과제.

---

## RENDER-AP-004 — 자막 swap 을 `tl.call`(순수 콜백)로 하면 seek 기반 캡처 렌더러에서 크래시

- **증상 (symptom)**: `npx hyperframes render` 가 capture 단계에서 실패.
  `[Browser:PAGEERROR] tl.call is not a function (index.html:...)` →
  `✗ Render failed: Composition has zero duration. Runtime ready: false`. 음성 나레이션
  영상(v0.36.0) 첫 실 렌더에서 사용자 보고. (data-duration 은 155s 로 정상인데도 실패.)

- **원인 (root cause)**: compose 템플릿의 자막 큐 루프가 `tl.call(() => { $sub.textContent
  = c.text; }, [], t)` 로 텍스트를 swap 했다. HyperFrames 렌더러는 **paused 타임라인을
  frame 별로 seek** 해 캡처하는데(`hyperframes/lib/motion/hf-motion.js` §"모든 효과는 paused
  타임라인에 add 되어 seek 로 재생"), 이 환경의 timeline 에는 순수 콜백 `.call` 이 노출되지
  않는다(결정론 캡처라 콜백 비결정성 배제로 추정). `.call` 이 throw → 타임라인 IIFE 중단 →
  `window.__timelines["root"]` 미설정 → 런타임이 zero duration 으로 판단 → 렌더 실패.
  (데모 index.html 도 동일 `tl.call` 패턴을 갖고 있어 같은 클래스 잠재.)

- **구조적 조치 (structural fix, v0.36.1)**:
  - `render_composition_html` 의 자막 swap 을 `tl.call` 대신 **`tl.to(proxy, {onUpdate})`**
    (hf-motion 의 `countUp` 과 동일한 seek-safe 패턴)로 교체. 전체 길이에 걸친 단일 트윈의
    onUpdate 에서 현재 시점(now)의 활성 큐(가장 최근 `c.t <= now`)를 골라 `$sub.textContent`
    를 갱신. 콜백 0, 레이아웃 변경 0.
  - 회귀 테스트 `tests/test_hyperframes_compose.py:test_subtitle_swap_is_seek_safe_no_tl_call`:
    생성 HTML 에 `tl.call(` 호출이 없고 `onUpdate` 가 있는지 잠금.

- **상태 (status)**: `resolved` (compose 경로). 실 렌더 재검증은 사용자 PC(이 환경엔
  hyperframes 렌더러/GSAP 런타임이 없어 HTML 구조까지만 검증).

- **알려진 한계**: 데모(`hyperframes/index.html`)·`build_narration`/`render_demo` 경로의 동일
  `tl.call` 은 본 수정 범위 밖(현재 사용자 경로는 compose). 데모를 다시 쓰면 같은 패턴으로
  교체 필요.

- **연관**: RENDER-AP-001/002(렌더 환경), hf-motion.js(seek-safe 모션 규약).

---

## RENDER-AP-005 — generated/ 의 컴포지션이 `../assets` 로 음성을 가리켜 렌더러 서버 루트 밖이라 로드 실패

- **증상 (symptom)**: 나레이션 영상 렌더가 `tl.call` 수정(RENDER-AP-004) 후에도 실패.
  `[Browser:REQUESTFAILED] GET .../assets/audio/aimem01.mp3 net::ERR_ABORTED` →
  `Composition has zero duration. Runtime ready: false`. JS PAGEERROR 는 없음(콜백 수정됨).

- **원인 (root cause)**: HyperFrames 렌더러는 `-c` 로 받은 파일의 **디렉토리를 정적 서버
  루트**로 서빙한다(`generated/aimem01.html` → 루트=`generated/`, 파일은 `/index.html`).
  compose HTML 은 `<audio src="../assets/audio/<pid>.mp3">` 로 음성을 가리켰는데, 브라우저가
  `/index.html` 기준 `../assets` 를 정규화하면 루트 밖으로 못 나가 `/assets/...`(=generated/
  assets, 부재)로 떨어진다 → 미디어 로드 실패 → 런타임이 음성 대기에서 ready 못 됨 → zero
  duration. (차트 `../lib/charts` 는 **번들러가 파일 실위치 기준으로 resolve**해 영향 없음 —
  raw `<audio>` 만 브라우저 fetch 라 깨졌다. 데모는 루트의 index.html + `assets/audio/...`
  라 원래 맞았다.)

- **구조적 조치 (structural fix, v0.36.2)**:
  - `_compose_with_narration`: 음성 mp3 를 `generated/assets/audio/<pid>.mp3` 로 쓰고
    `audio_src="assets/audio/<pid>.mp3"`(상대, ../ 없음). 데모와 동일한 서버-루트 상대 구조.

- **상태 (status)**: fix 적용. 실 렌더 재검증은 사용자 PC(이 환경엔 hyperframes 렌더러 없음 —
  파일 위치/HTML src 까지만 검증).

- **연관**: RENDER-AP-004(선행 tl.call 수정), 데모 render_demo 의 루트-기준 자산 배치.
