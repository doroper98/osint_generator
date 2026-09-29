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

## RENDER-AP-003 — 검사용 상자를 렌더 예약 영역과 공유하다 골든을 바꿈
- **증상**: v3.1.0 마커 잘림 검사(D-0049)를 넣으며 `marker_box` 를 부제 폭까지 넓혔더니, 같은 함수를 쓰는 `draw_marker` 의 예약 영역(R.reserved)도 넓어져 도시 라벨 회피가 바뀌었다. 골든 route_2·route_3 컷 MAD 0 → 0.09.
- **원인**: "검사가 보는 상자"와 "렌더가 비키는 상자"는 다른 계약인데 한 함수의 기본값을 바꿨다. pytest 에 골든 25컷 렌더 대조가 없어 전체 통과였다.
- **좋은 예**: 기본값은 렌더 계약(v3 그대로), 검사는 명시 인자(`with_sub=True`). 렌더 공용 함수를 바꾸면 golden_compare 를 돌린다.
- **자동 조치**: `tests/test_checks.py::test_marker_reserved_box_label_only`.
- **발견 버전**: v3.1.0 (Phase 6.9 작업 10 골든 대조) · **상태**: active

## RENDER-AP-004 — loudnorm 이 TP 를 맞춰도 AAC 인코딩이 트루 피크를 올림
- **증상**: dmz_mine_2026 을 ElevenLabs 내레이션으로 바꾸자 mux 오디오 QA 가 hard 실패. 2패스 loudnorm(dynamic) 출력 TP −1.50 dBTP → final.mp4(AAC 192k) −1.09 dBTP, 허용(−1.5 + 여유 0.15) 초과.
- **원인**: loudnorm 은 필터 출력의 트루 피크만 맞춘다. 날카로운 순간 피크가 많은 음성은 AAC 인코딩에서 0.4dB 가까이 더 오른다(edge-tts 는 0.03~0.15 로 여유 안이었다).
- **좋은 예**: loudnorm 뒤 샘플 피크 리미터(`rules audio.post_limiter_dbfs`, −2.0 dBFS)를 둔다. 실측: 같은 믹스 AAC −1.62 dBTP, I −14.26 LUFS(목표 −14 ± 1).
- **자동 조치**: `audio/qa.py loudnorm_two_pass` 필터 끝 alimiter + 기록 `post_limiter_dbfs`, `tests/test_audio_qa.py::test_two_pass_record`. QA 여유(tp_codec_margin_db)는 넓히지 않았다.
- **발견 버전**: v4.4.0 (dmz_mine_2026 v2) · **상태**: active
