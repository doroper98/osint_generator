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

## RENDER-AP-005 — 차트 아일랜드가 상자 밖 마커 라벨을 조용히 자름
- **증상**: fed_policy 차트 아일랜드 오른쪽 끝 마커 "다음 FOMC" 라벨이 상자 테두리에서 잘려 "다" 만 보였다. G12 v9·G13 v15 시각 검수가 두 번 hard 로 지적했고 검사는 0이었다.
- **원인**: 아일랜드 렌더러는 상자 모양으로 clip 한다. 마커 라벨은 지도 무대 규칙(점 오른쪽 고정)을 그대로 따라 상자 밖으로 나가도 알리지 않았다(조용한 드롭, 15 P6). 연출로 고쳐도 차트 오른쪽 끝 날짜면 다시 생긴다.
- **좋은 예**: 라벨 자리는 렌더 수치라 코드가 정한다 — 아일랜드 마커만 상자 가장자리 − `island.chart.label_flip_pad` 를 넘으면 반대쪽, 그래도 넘치면 클램프. 그 뒤에도 밖이면 hard 검사. 지도 무대 마커 경로는 그대로(골든).
- **자동 조치**: `engine/layers/markers.island_label`, checks `island_label_clip`(hard)·`island_label_overlap`(warning), `tests/test_g13_label_clip.py`(반전·클램프·지도 경로 무변경·hormuz 25/25 기록).
- **발견 버전**: v5.1.0 (G12 검수) · **해결 버전**: v5.2.0 (D-0133) · **상태**: active

## RENDER-AP-006 — 인물 뱃지의 정수리가 원 테두리 밖(위)으로 나와 어색함
- **증상(실제 현상)**: valdai-2026 배포본(v5.4.0, 사용자 시청 2026-10-02) — "푸틴의 정수리가 푸틴을 둘러싼 원의 테두리 밖(위쪽)으로 나와 있다." hormuz 골든의 노무현 대통령 뱃지도 머리 윗부분이 원 위로 몇 px 나왔다.
- **원리(원인)**: v3 의 '머리 내밀기' 표현 — 초상을 원과 그 위 2.4R 직사각형의 합집합으로 잘라 머리가 원 밖으로 솟게 그렸다(`badge_at` clip = arc ∪ rectangle). 초상은 아래 끝(어깨)에 맞춰 놓이므로 머리 높이는 초상마다 다르다. 라이브러리 가공본(머리-어깨 정규화 폭 420, 높이 ≤ 1.22×폭)은 머리가 원 반지름보다 높게 오는 경우가 많다. 그래서 테두리 선이 이마·정수리를 가로질러 '테두리 밖으로 삐져나온' 모양이 된다.
- **좋은 예**: 초상은 원 안에만 그린다. 실측 정수리(`portrait_head_top`, 중심에서 R 단위)가 `badge.head_inside_max`(0.9)를 넘으면 그만큼 초상을 아래로 내려 머리 전체가 원 안에 든다(어깨 쪽이 원에 잘린다). 머리 예약 상자도 원(+그림자)까지.
- **자동 조치**: `rules badge.head_popout: false`·`head_inside_max: 0.9`, `engine/layers/badges.badge_at`·`portrait_top`·`head_factor`. 인용(quote) 초상도 같은 렌더러. hormuz 골든 재기준선 `reports/phaseG16`(expected_deltas `g16_head_path`).
- **발견 버전**: v5.4.0 (사용자 시청) · **해결 버전**: v5.5.0 · **상태**: active

## RENDER-AP-007 — 지도 이동 중간에 흐름 방향이 살짝 틀어짐(이동 + 줌 동시)
- **증상(실제 현상)**: valdai-2026 배포본(v5.4.0, 사용자 시청 2026-10-02) — "지도의 이동 중간에 방향이 살짝 틀어지는 경우가 있다." 측정: 카메라 중심 경로는 키마다 곧은 직선이고 이동 겹침(앞 이동이 끝나기 전 다음 이동)도 0건이었다 — 중심이 아니라 **지도 위 점들의 화면 경로**가 휘었다.
- **원리(원인)**: 옛 보간은 중심을 진행률 e 에 정비례(c = c0 + Δ·e)로, 화면 폭은 로그로(w = w0·(w1/w0)^e) 움직였다. 지도 위 점 P 의 화면 좌표 = (P − c(e)) / w(e). 분자는 e 의 1차식, 분모는 지수식이라 그 궤적은 직선이 아니라 곡선이다. 확대·축소와 이동이 함께인 숏(예: 모스크바 w 7 → 동유럽 w 58)에서 화면이 미끄러지는 방향이 이동 중에 돈다. 순수 이동(폭 같음)이나 순수 줌에서는 생기지 않는다.
- **좋은 예**: 중심을 폭에 비례해 움직인다(c = c0 + Δ·(w − w0)/(w1 − w0)). 그러면 (P − c)/w = U/w − V 꼴(고정 벡터 U·V)이 되어 모든 점이 직선으로 흐른다 — 한 고정점을 중심으로 한 확대·축소 + 평행이동(닮음 변환). 폭이 같으면 진행률 비례로 되돌아간다. 이징(ease_io)은 폭(로그)에 그대로 걸린다.
- **자동 조치**: `rules shot_grammar.move_path: fixed_point`, `engine/camera.build_camera`. 검증: 합성 이동(w 7 → 58, 대각 이동)에서 점 궤적 직선 이탈 ≈ 0(2e-16).
- **발견 버전**: v5.4.0 (사용자 시청) · **해결 버전**: v5.5.0 · **상태**: active

## RENDER-AP-008 — 인물 뱃지가 아일랜드(카드) 때문에 떴다가 위아래로 움직임

- **증상(실제 현상)**: kaliningrad-suwalki 콘티 판(사용자 시청 2026-10-04) — 오른쪽 위 아일랜드 카드와 인물 뱃지가 함께 뜨는 장면마다, 뱃지가 나타난 뒤 카드가 들어오고 나가면서 위아래로 미끄러졌다. 사용자: "뱃지 위치를 아일랜드 아래에 고정되게".
- **원리**: 카드 회피(D-0033)가 이동량 = 밀어낼 거리 × 카드 존재도(0→1→0) 였다. 카드가 뱃지보다 늦게 들어오거나 먼저 나가면 존재도가 변하는 동안 뱃지가 움직인다 — 의도는 "카드가 사라지면 제자리로"였지만 화면에서는 흔들림으로 보인다.
- **원칙**: 뱃지는 사는 동안 한 자리에 있다. 수명과 겹치는 카드 전부를 동시에 피하는 자리를 처음부터 쓴다(카드 아래가 우선).
- **자동 조치**: rules `layout_480p.reserved.badge_hold: true`·`hold_directions: [down, left]`·`hold_sample_sec` — `engine.reserved.hold_pushes` 가 load_project 에서 뱃지마다 고정 이동 `push_hold` 를 정하고, `place_badge` 는 그 값만 쓴다. 못 피하면(max_push_px 초과) 기존 회피. provenance `reserved.avoidance` strategy `hold`.
- **회귀 테스트**: `tests/test_v560_script_review.py::BadgeHoldTest`
- **발견 버전**: v5.5.1 · **상태**: active

## RENDER-AP-009 — 지도 지명 글자끼리·뱃지와 지명 글자가 겹쳐도 검사가 잡지 못함

- **증상(실제 현상)**: kaliningrad-suwalki 콘티 판(사용자 시청 2026-10-04) — ① 수바우키 장면에서 '수바우키'·'수바우키 회랑' 마커와 부제, 빌뉴스 부제, 경로 라벨이 서로 겹쳤다. ② 왼쪽 위 슬롯의 나토 휘장 뱃지가 '발트해' 마커 부제의 날짜("2025년 1월~")를 가렸다. checks hard 0 이었다.
- **원리**: 검사는 화면 밖·자막 겹침·카드 겹침만 봤고, 마커와 마커·뱃지와 마커 사이는 보지 않았다. 또 `marker_box(with_sub)` 가 위·아래(side top/bottom) 라벨을 점 오른쪽으로 펼친 상자로 계산해, 실제로 점 가운데 정렬로 그린 글자 자리와 달랐다(검사 상자 ≠ 그린 자리).
- **원칙**: 같은 순간 보이는 지도 글자·뱃지는 서로 겹치지 않는다. 검사 상자는 그린 자리와 같다.
- **자동 조치**: `engine.checks.check_label_collision` — hard `label_collision`(표본 0.5초, 쌍마다 한 줄, 허용 2px). `marker_box(with_sub=True)` 가 top/bottom 을 가운데 정렬 상자로. `place_over` 가 뱃지 고정 이동(push_hold)을 반영. hormuz 골든 0건(기준선 영향 없음).
- **회귀 테스트**: `tests/test_v560_script_review.py::LabelCollisionTest`
- **발견 버전**: v5.5.1 · **상태**: active

## RENDER-AP-010 — 720p 자막에서 강조어 앞뒤에 틈이 생김(측정 배율 ≠ 그리는 배율)

- **증상(실제 현상)**: kaliningrad-suwalki 720p 전편(v5.6.0, 2026-10-04 내 검수) — "발트해의 [해저 기반시설]을"이 [발트해의 ␣␣해저 기반시설␣을]처럼 강조 구간 앞뒤가 벌어졌다. 480p 프리뷰·콘티 판(480p)에서는 정상이라 사용자 검토 단계에서 보이지 않았다.
- **원리**: 자막은 줄을 구간(일반·강조)으로 나눠 왼쪽부터 이어 그린다. 구간 전진 폭을 1배 측정 컨텍스트(`typography._M`)에서 쟀는데, 그리기는 장치 배율 k=1.5 컨텍스트에서 한다. 글꼴 힌팅이 글자 전진 폭을 장치 픽셀로 반올림하므로 배율마다 합이 달라지고, 구간 경계마다 오차가 쌓여 틈이 된다. 480p(k=1)는 두 컨텍스트가 같아 드러나지 않는다.
- **원칙**: 이어 그리는 글자의 전진 폭은 그 글자를 그리는 컨텍스트에서 잰다. 배포 해상도(720p)는 480p 와 다른 경로라, 배포 해상도 컷으로 한 번 더 본다.
- **자동 조치**: `engine.subtitles._ctx_w` — 줄 가운데 맞춤·구간 전진 폭을 그리는 컨텍스트로. 480p 는 값이 같다(골든 불변). 줄 나눔(wrap)은 린트와 같은 1배 측정 그대로.
- **발견 버전**: v5.6.0 · **상태**: active


## RENDER-AP-011 — 월 단위 타임라인 패널에 수백 년을 넣어 날짜·막대가 깨짐

- **증상(실제 현상)**: kaliningrad-suwalki 720p 전편(v5.6.0, 2026-10-04 사용자 지적 "숫자나 도식화 모두 0점") — 쾨니히스베르크 연표 패널에 "1.1"·"4.9"·"8.1" 같은 월.일 표기와 화면을 가로지르는 거대한 흰·회색 막대가 나왔다.
- **원리**: `timeline` 패널은 월 축(눈금 = 월, 날짜 = M.D) 전용이다. 연출 판이 1255–1990 사건을 이 패널에 넣어 축이 약 9,000개월로 늘었고, 눈금·막대 폭이 무너졌다. 검사는 패널 종류·좌표만 보고 축 범위는 보지 않았다.
- **원칙**: 연도 단위 경과(수십~수백 년)는 연도 카드(`precedent`)로 보여 준다. 월 축 패널은 짧은 기간(규칙 `panels.timeline.max_span_months`)만.
- **자동 조치**: `engine.checks.check_timeline_span`(hard) — 시작~끝 개월 수가 `max_span_months`(36)를 넘으면 오류. kaliningrad 연출 판은 연도 카드 4장(1255·1945·1946·1990)으로 교체.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-012 — 경로 이름표가 마커 글자와 겹치고, 장면 주제(철도 구간)가 프레임 밖

- **증상(실제 현상)**: kaliningrad-suwalki 720p(v5.6.0, 2026-10-04 사용자 지적 "철도 훈련 장면에서 철도 구간이 화면 프레임 밖") — 2026년 2월 리투아니아 철도 훈련 문장의 카메라가 위도 53°(프레임 위끝 54.66°)에 있어 철도(54.64~54.95°)와 훈련 마커가 화면 위 가장자리 밖으로 나갔다. 고치는 과정에서 경로 이름표 "칼리닌그라드행 러시아 통과 열차"가 훈련 마커 라벨과 겹쳤고, 같은 영상 2004년 장면의 "육상 연결" 이름표도 칼리닌그라드 마커와 겹쳐 있었다 — 둘 다 검사가 통과시켰다.
- **원리**: ① `offscreen` 검사는 마커·뱃지 상자만 본다 — 경로(route) 선 자체가 프레임 밖이어도 잡지 않는다. 철도 훈련 마커는 "지점 비공개"라 등장 0.2초 전후 가장자리에 걸쳐 통과했다. ② `label_collision`(RENDER-AP-009)은 뱃지·마커끼리만 대조했다 — 경로·봉쇄선 이름표는 대상 밖.
- **원칙**: 문장의 주제가 되는 선(경로)은 그 문장의 카메라 프레임 안에 있어야 한다. 한 장면 안에서 주제 지역이 크게 바뀌면(북쪽 철도 → 남쪽 벨라루스 훈련장) 문장 경계에 카메라 이동 1회를 둔다(문장마다 이동은 여전히 금지). 자막이 이미 말하는 경로 이름표는 지운다.
- **자동 조치**: `label_collision` 이 경로·봉쇄선 이름표(`_place_label_boxes`, 렌더러와 같은 자리)도 대조 — 마커와는 글자 영역만(`_text_part`, 점·맥동 고리 제외: 호르무즈 골든 '봉쇄' 합격 배치 불변). kaliningrad 연출 판: year_2026 2컷(철도 북쪽 · 벨라루스 남쪽), 철도 이름표는 마커 부제로 합침, 2004년 "육상 연결" 이름표 삭제(자막과 중복).
- **자동 조치 2**: `engine.checks.check_route_frame`(hard) — 다 그려진 경로 곡선의 화면 밖 비율이 `rules route_frame.max_out`(0.25)을 넘으면 오류. 카메라가 떠난 뒤에도 살아 있던 철도 경로(화면 밖 100%)를 이 검사가 잡아, 경로·훈련 마커를 카메라 이동 시각에 끝냈다. 호르무즈 골든 0.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-013 — 연도 카드(precedent) 글자가 카드 밖으로 나가도 검사 통과

- **증상(실제 현상)**: kaliningrad-suwalki 연표에 1701 카드를 더하자 "전간기 동프로이센 · 독일 본토와 단절"의 "단절"이 카드 오른쪽 밖으로 나갔다(720p 프리뷰, 2026-10-04 내 검수). 검사 hard 0 이었다.
- **원리**: versus 패널은 v5.3.1 부터 항목 폭을 재지만(`VersusOverflowError`), precedent 는 카드 폭(172px)을 재지 않고 글자를 그대로 그렸다. 또 versus 오류도 그리는 순간에만 나서 프리뷰 컷 밖이면 렌더 전 검사에 안 걸린다.
- **원칙**: 패널 글자는 상자 안에서 끝난다. 넘치면 조용히 자르지 않고 연출이 문구를 줄인다(15 P6).
- **자동 조치**: `engine.panels.precedent.overflow` + 검사 `panel_overflow` hard — 연도·제목·줄·인물 캡션이 카드 폭 − 여백(146px)을 넘으면 렌더 전 오류. 1701 카드는 3줄로 줄임. 패널 4장 상한(PanelPrecedent)으로 1945·1946 카드를 합침.
- **발견 버전**: v5.6.0 · **상태**: active
