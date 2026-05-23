<!--
tier: 3
last_synced_with: v0.11.1
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
