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

## RENDER-AP-014 — 국기 뱃지가 다른 나라 땅 위에 놓임(리투아니아 위 러시아 국기)

- **증상(실제 현상)**: kaliningrad-suwalki 본편(v5.6.0) 사용자 지적(2026-10-05) — "첫 화면에 리투아니아 지역에 러시아 국기 뱃지가 있어서 처음 보는 사람들은 헷갈릴 수 있다". 슬롯 map_upper_right 가 그 카메라에서 리투아니아 땅 위였다.
- **원리**: 지도 슬롯은 화면 고정 자리라, 카메라가 바뀌면 그 아래 땅도 바뀐다. 국기는 "이 땅 = 이 나라"로 읽힌다. 검사는 화면 밖·겹침만 봤고 국기와 그 아래 땅의 관계는 보지 않았다.
- **원칙**: 국기 뱃지는 그 나라 땅·바다·화면 가장자리에. 남의 땅 위면 슬롯을 바꾼다.
- **자동 조치**: 검사 `flag_territory` hard — 국기 뱃지 가운데 지점의 나라(저장소 막지도 110m 폴리곤)가 국기 나라와 다르면 오류. direction_grammar 한 줄. 전수 측정: kaliningrad 5·hormuz-talks 3·valdai 1, 골든 0.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-015 — 양측 비교 패널 위에 인물 뱃지가 한 자리에 번갈아 떠 발언자 혼동·글자 가림

- **증상(실제 현상)**: 같은 영상 "자파드 2025를 둘러싼 두 주장" 화면(사용자 지적 2026-10-05 — 사용자 표현 "투스크와 포로셴코", 실제는 투스크·루카셴코) — 두 뱃지가 같은 자리에 차례로 떠 누구의 의견인지 헷갈리고, 뱃지가 기둥 글자 일부를 가렸다.
- **원리**: 패널이 뜬 순간 시작하는 뱃지는 panel_badge 고정 자리(96,300 / 758,300)로 가는데, versus 기둥(x 60~404 / 450~794, y 120~382) 안이다. 또 검사(place_over)는 패널이 지도를 덮으면 뱃지를 건너뛰어 겹침을 보지 못했다.
- **원칙**: versus 패널 동안 인물 뱃지를 띄우지 않는다 — 기둥 제목이 발언자를 밝힌다(같은 무게, G4). 인물 소개는 패널 앞 문장에서.
- **자동 조치**: 검사 `badge_over_panel` hard(뱃지·versus 패널 시간 겹침 0.3초 초과). direction_grammar 한 줄.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-016 — 지도 영상이 좁은 화면으로 시작해 지리를 모르는 시청자가 위치를 못 잡음

- **증상(실제 현상)**: 같은 영상 사용자 지적(2026-10-05) — "수바우키 회랑 같은 주제는 지리를 잘 모르는 사람은 대략적으로도 어느 위치인지 인지하기 어렵다. 전체 지도에서 해당 지역으로 천천히 들어가는 오프닝". 첫 카메라 폭 9°(발트해 남동부만).
- **원리**: 연출 문법에 오프닝 규칙이 없었다. 전수 측정에서 모든 지도 영상이 7~9°(hormuz-talks 만 32°)로 시작했다.
- **원칙**: 넓은 지도(나라·주변국이 함께 보이는 폭)에서 시작해 대상 지역으로 천천히 들어간다(establishing shot).
- **자동 조치**: 규칙 `opening`(min_w 30°, 25초 안에 2.5배 이상, 이동 4초 이상), 검사 `opening_establish` hard, 면제 = 연출 `opening_exempt`(사유) — hormuz_korea 골든만(사용자 합격 오프닝). direction_grammar 한 줄.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-017 — 무기체계가 나오는데 실사 이미지 없이 숫자 카드만

- **증상(실제 현상)**: 같은 영상 사용자 요청(2026-10-05) — "무기체계가 나올 때는 웬만하면 무기체계의 실사 이미지가 나오면 좋겠다". 이스칸데르 문장에 "500km 사거리" 카드만 있었다.
- **원리**: 미디어 레지스트리에 무기 자료사진이 없었고, 연출 문법도 무기 사진을 요구하지 않았다(미디어 0건 경고는 R-0167 이후 결정 요청 상태).
- **원칙**: 무기체계 이름이 나오는 문장엔 그 무기의 실사 사진(권리 기록된 자료사진)을 우선.
- **자동 조치**: 규칙 `weapon_photo.terms`, 검사 `weapon_photo` warning(권리 있는 실사가 없을 수 있다 — 사람이 판단). direction_grammar 한 줄.
- **발견 버전**: v5.6.0 · **상태**: active

## RENDER-AP-018 — 지도 이동 한가운데서 "딱 꺾이는" 카메라(교훈이 스케치 트랙에만 배선된 재발)

- **증상(실제 현상)**: gulf_pact_2026 본영상 사용자 의견(2026-10-11, UF-02) — "지도의 전환이 이전에 내가 코멘트 했었는데 왜 부드럽게 이동하지 않고 중간에 딱 꺾이는 지점이 있지?". v5.5.0(2026-10-02, 이동 경로 휨)에 이은 같은 영역 재지적.
- **원리**: 이동 이징이 조각 3차(easeInOutCubic)라 이동 한가운데서 가속도가 +12 → −12 로 불연속 — 3차 차분(저크)이 튄다(gulf 0.0068, 288.4초). 멈칫(2차 차분) 교훈은 D-0141 에서 스케치 SK-C1 으로만 검사했고 본 엔진 checks 에는 없었다. 1·2차 임계로는 이 꺾임이 보이지 않는다.
- **원칙**: 카메라 이동은 속도·가속도가 모두 연속(5차 이상)이다. 같은 교훈은 모든 렌더 트랙(본 엔진·스케치)에 같은 키·같은 측정 함수로 배선한다.
- **자동 조치**: 규칙 `shot_grammar.move_ease: quintic`(engine/camera·sketch/common/camera 둘 다), `engine.camera.continuity` 한 함수(1·2·3차), 본 엔진 검사 `camera_continuity` hard·스케치 SK-C1 3차 — 임계 `sketch.checks.max_dlogw/max_d2logw/max_d3_per_frame`. 테스트 `test_camera_continuity`(두 트랙 배선 포함). 남은 것: 스케치 3D 지구본 카메라(ease_io, 3D 검사는 화면 px 2차만).
- **발견 버전**: v5.21.9 · **상태**: active

## RENDER-AP-019 — 기사 카드가 읽기도 전에 사라짐(완전 노출 0.4초)

- **증상(실제 현상)**: gulf_pact_2026 본영상 사용자 의견(2026-10-11) — "첫 오프닝에서 화면 전환에 너무 급해. 기사 화면이 나왔는데 0.5초도 안 돼서 사라지는 것 같아". 첫 기사 카드(art_0001) t0 10.52 ~ t1 12.92 — 프레스 단독 1초·페이드 0.5초씩을 빼면 글자가 다 보이는 시간 0.40초.
- **원리**: 기사 카드 길이에 하한이 없었다. 연출가가 문장 끝(+0.2초)까지만 걸었고, 바로 뒤에 제목 카드가 있어 늘릴 자리가 없었다. 검사·연출 문법 어디에도 "읽을 시간"이 없었다.
- **원칙**: 기사·인용 카드는 글자가 다 보이는 시간이 2.5초 이상. 문장이 짧으면 다음 문장까지 늘리거나 시작을 앞당긴다.
- **자동 조치**: 규칙 `qa_checks.card_full_exposure_min_sec`(2.5), 검사 `card_exposure` hard(구간 = 그리기 알파와 같은 함수 `article_full_span`·`quote_full_span`), 연출 문법 한 줄. 테스트 `test_card_exposure`. gulf: art_0001 시작을 open_1 +1.2초·끝을 제목 카드 시작(문장 끝 +0.7)으로 → 2.70초, 사우디 강조·뱃지를 open_1 시작으로 당김.
- **발견 버전**: v5.21.10 · **상태**: active

## RENDER-AP-020 — 경로 선이 자기 이름표·마커 부제를 지나가 글자가 안 읽힘

- **증상(실제 현상)**: gulf_pact_2026 본영상 사용자 의견(2026-10-11) 3건 — 38초 '상호방위협정 · 2025'(금색 글자가 밝은 지도·자기 선과 겹침), 101초 '합의된 군사력 즉시 배치'(선 바로 위·해역 이름과 겹침, 마커 부제 끝을 선이 지나감), 275초. hormuz 골든 59초 '허가받은 배만 통과'도 같은 결함이었다.
- **원리**: 경로 이름표가 곡선 가운데 점 위 11px 고정이었다 — 선의 기울기·다른 선·지명·뱃지를 보지 않았다. 마커·뱃지보다 먼저 그려 장애물을 알 수 없었다. 이름표 대비·선 교차 검사가 없었다(대비 검사는 지명만 required).
- **원칙**: 지도 위 글자는 어떤 선도 지나가지 않는다. 밝은 지도에서 색 글자 대신 짙은 글자 + 밝은 halo, 색은 보조 표시로.
- **자동 조치**: `engine.layers.routes.place_route_label`(렌더·검사 공용, 마커·뱃지 뒤 `flush_route_labels`), 규칙 `layout_480p.route_label` 자리 키·`geo.themes.light.map.route_label`, 검사 `route_label_cross`·`route_label_overlap` hard, 이름표 `contrast="required"`, 연출 문법 한 줄. 테스트 `test_route_label_place`.
- **발견 버전**: v5.21.11 · **상태**: active

## RENDER-AP-021 — 같은 영상 안 기사 카드 배경이 흰색·검은색으로 갈림

- **증상(실제 현상)**: gulf_pact_2026 본영상 사용자 의견(2026-10-11) — "기사 조판의 배경이 흰색인 문제. 통일감 문제"(113초). 67·113초 카드 뒤가 밝게, 160·260초는 어둡게 보였다.
- **원리**: 사진 없는 카드는 지금 무대를 블러·dim 하는데, 밝은 지도에선 평균 밝기 0.37(어두운 지도 0.07)이 남는다. 카드 theme 도 연출가가 카드마다 dark·light 를 골랐다(113초 light = 흰 덮개).
- **원칙**: 기사 카드 무대는 지도 테마와 무관하게 하나의 모습, 한 영상 안 카드 theme 하나.
- **자동 조치**: `press_fallback.max_luma`(0.075, `fallback_gain`), 검사 `article_backdrop` hard, 연출 문법 한 줄. 테스트 `test_article_backdrop`.
- **발견 버전**: v5.21.12 · **상태**: active

## RENDER-AP-022 — 이동·공격 문장인데 그 목적지로 가는 선이 없거나 대상이 화면 밖

- **증상(실제 현상)**: gulf_pact_2026 본영상 사용자 의견(2026-10-11) 3건 — "아덴에 보냈다는데 사우디 방면 선만 있어 오해"(troop_numbers_7), "미사일 발사 궤적 선이라도"(riyadh_airport_0), "지도에 예멘 쪽이 안 보인다"(briefing_2).
- **원리**: 연출 문법·검사가 문장의 동사(보냈·공격)와 화면 요소(경로·카메라 구도)의 관계를 보지 않았다. 마커만 있고 경로가 없거나, 다른 문장의 경로가 남아 사실 방향과 반대로 읽혔다.
- **원칙**: 이동·공격 문장의 목적지·표적에는 그곳에 닿는 선이 그 문장에 있다. 문장이 부르는 대상은 그 문장 동안 화면 안.
- **자동 조치**: 규칙 `qa_checks.route_missing`·`frame_missing`, 검사 route_missing·route_missing_other(hard)·frame_missing·frame_missing_target(hard), 필드 description·연출 문법. 테스트 `test_story_geo`.
- **발견 버전**: v5.21.14 · **상태**: active

## RENDER-AP-023 — 인용 카드 국기 뱃지가 경로 이름표를 덮음

- **증상(실제 현상)**: gulf_pact_2026 v5.22.4 본영상 240~245초(감독 관찰, 사용자 지적 아님) — 인용 "전면적 전쟁범죄"의 사우디 국기 뱃지가 궤적 이름표 "탄도미사일 궤적 · 개략" 끝을 덮었다. route_label_overlap·label_collision 모두 0.
- **원리**: 이름표 장애물은 지도 층(마커·뱃지·해역 이름·자막)만 보았다. 인용·카드 같은 전경 층은 지도 위에 그려지지만 장애물 목록에 없었다.
- **원칙**: 지도 이름표는 그 순간 보이는 전경 상자(인용·카드·게시물·도형·겹침 카드)도 피한다. 기사 카드는 화면 전체 덮개라 제외.
- **자동 조치**: `engine.layers.routes.foreground_boxes` 를 `label_obstacles`(렌더·route_label_overlap 공용)에 추가, label_collision 은 전경 상자 ↔ 경로·봉쇄선 이름표 대조. 테스트 `test_route_label_foreground`. 골든 dark·light 무변화.
- **남은 점**: 인용이 나타날 때 이름표가 다른 자리로 옮겨 간다(인용 덮개가 어두워지는 동안). 감독 판단 대기.
- **발견 버전**: v5.22.6 · **상태**: active

## RENDER-AP-024 — 경로 이름표가 보이는 중에 자리를 옮김(그리고 렌더·검사가 다른 장애물로 자리를 골랐음)

- **증상(실제 현상)**: v5.22.6 패치 뒤 gulf 240~246초 — 인용이 나타나자 "탄도미사일 궤적 · 개략" 이 궤적 위쪽으로 0.3초 사이 옮겨 갔다가 돌아옴(감독 판정: C0 "튀어 오르는 연출"과 같은 종류, D209). 조사 중 골든 59.02초에서 렌더는 후보 7, 검사는 후보 3 을 고르고 있었음을 확인 — 렌더 R.reserved 의 뱃지 상자(이름표 포함)와 검사 place_over 상자가 달랐다.
- **원리**: 이름표 자리를 프레임마다 그 순간 장애물로 다시 골랐다. 나중에 나타나는 요소가 있으면 수명 중에 자리가 바뀐다. 렌더와 검사가 "같은 함수"를 쓰지만 장애물 목록을 따로 만들었다.
- **원칙**: 이름표 자리는 나타나는 순간 이미 있는 장애물만 피해서 정하고 수명 내내 그 후보. 나중 전경 층에 가리면 그 자리에서 흐린다. 자리 고르기의 장애물은 렌더가 그 프레임에 실제로 예약한 상자다.
- **자동 조치**: `engine.checks.route_label_slots`(나타나는 프레임의 렌더 지도 층을 붙잡아 R.reserved 그대로 사용, 렌더·검사 공용), `label_fade`, 검사 `label_jump` hard(`qa_checks.label_jump_px`). 테스트 `test_route_label_foreground`. 골든 dark·light 25/25 바이트 동일.
- **발견 버전**: v5.22.7 · **상태**: active

## RENDER-AP-025 — 카메라 장치가 "매끄러움"만 재고 "빠르기"는 재지 않아 같은 지적이 다시 나옴(UF-02 재발 → UF-97)

- **증상(실제 현상)**: v5.22.4 gulf_pact_2026 오프닝 0~10초 — 사용자 "첫 10초동안의 오프닝에서 여전히 너무 지도의 이동이 급격한 이동이 있는 부분이 있고"(UF-97, recurs_of UF-02). 실측: 6.0초에 시작한 w 88→34 이동이 4.4초 — 줌 |d ln w/dt| 최대 0.40/초, 제목 카드(13.4초) 전 오프닝인데 본문 이동과 같은 빠르기. 이 판은 `camera_continuity`(UF-02 장치)·스케치 SK-C1 을 모두 통과했다.
- **원리**: UF-02("중간에 딱 꺾이는 지점")에 단 장치는 프레임 사이 차분의 1~3계 미분(Δ ln w, Δ²·Δ³ — 꺾임·멈칫)만 쟀다. 이징이 매끄러우면 아무리 빨라도 통과한다. 사용자의 불만은 "꺾임" 한 가지가 아니라 "부드럽지 않다"는 감각 전체였고, 장치는 그중 한 성분만 막았다. 장치가 의견 문장의 표면(꺾임)에 맞춰졌고 같은 의견의 다른 성분(속도)이 열려 있었다.
- **원칙**: 카메라 의견의 장치는 **모양(연속성)과 크기(속도)를 둘 다** 잰다. 속도는 무대 좌표가 아니라 화면 기준(중심 이동 ÷ 화면 폭, |d ln w/dt|)으로 재고, 오프닝(제목 카드 전)은 본문보다 낮은 상한을 둔다. 재발 의견을 받으면 "원래 장치가 왜 통과시켰는가"를 실측으로 확인하고 그 빈 성분을 장치로 막는다(C12-4).
- **자동 조치**: `engine.camera.speed`(본 엔진·스케치 공용 함수), 검사 `camera_speed` hard(일반 상한·오프닝 상한, `rules shot_grammar.camera_speed`), 스케치 SK-C1 같은 함수·같은 일반 상한. 테스트 `tests/test_camera_speed_title_backdrop.py::CameraSpeedTest`. UF-02 장치 칸에 `camera_speed` 보강. 함께 찾은 결함: `opening_establish` 가 이동 길이 대신 키 사이 간격을 재던 것 → 이동 키 `dur` 로 판정(v6.0.2).
- **남은 것**: 시간축 무대(fed_timeline_demo)는 아직 지도 무대만 적용 — 감독 판단 대기(R 보고).
- **발견 버전**: v6.0.2 · **상태**: active

## RENDER-AP-026 — 검사가 렌더 직전 중간값을 재서 화면의 결함을 못 봄(재는 것 ≠ 보이는 것) — 카메라 꺾임 세 번째 재발(UF-99)

- **증상(실제 현상)**: v6.0.2 gulf_pact_2026 전달본 — 사용자 "여전히 지도에서의 카메라 무빙에 있어서 한번 꺾이는 지점이 있어. 이거 이전에도 코멘트 했고 계속 코멘트 하는데 개선이 안되네?"(UF-99, recurs_of UF-02·UF-97). 감독 광류 실측(D-0220): 29.71·61.67·132.50·288.62·300.38초에 고정점이 화면 왼쪽 끝으로 튀고, 줌이 한 프레임 만에 멈추거나 시작, 가로 흐름 방향 반전. 이 판은 `camera_continuity`·`camera_speed`·`opening_establish`·SK-C1 을 모두 통과했다.
- **원리**: 연출 키가 무대(티어 W, gulf 경도 폭 54도)보다 넓은 w(88·72·84)를 요청했다. 렌더 `engine/projection.py View` 가 경계로 잘라(클램프) 화면은 경계에 멈춰 있다가, 요청 궤적이 경계 안으로 들어오는 순간 이동 중간 속도로 출발한다 — 클램프는 연속이지만 미분이 끊기는 함수다. 카메라 검사는 모두 클램프 전 요청 궤적(`P.cams`)을 쟀다. 요청 궤적은 매끄러웠으므로 통과했다.
- **경과(같은 의견 세 번)**: UF-02(꺾임) → D-0202 5차 이징(요청 궤적의 가속도 뒤집힘 제거) → UF-97(빠름) → D-0216 속도 상한(요청 궤적) → UF-99. 고친 것은 매번 요청 궤적이었고 결함은 렌더 단계에 있었다. 연출 입력(`workers/direction_io.geo_text`)이 고정 문구 "카메라 w 2.5~96" 으로 경계보다 넓은 w 를 허용한 것이 원인 제공.
- **원칙**: 검사는 **화면에 그려진 것**을 잰다. 렌더 단계의 보정(클램프·스냅)이 걸리면 실패한다 — 렌더가 조용히 고치는 것은 P6 의 조용한 폴백이다. 재발 의견을 받으면 "장치가 잰 값"과 "사용자가 본 값"이 같은지부터 실측한다.
- **자동 조치**: `engine.camera.screen_track`·`bounds_excess`·`max_view_w`(렌더와 같은 View), hard `camera_bounds`(`rules qa_checks.camera_bounds_rel_tol`, 지도·시간축·차트 아일랜드), `camera_continuity`·`camera_speed`·스케치 SK-C1 을 화면 궤적으로 교체, 제안 `frame_points`·연출 입력 `geo_text`(w 상한 = 무대 경계)·`rules direction_grammar` 는 경계 안 키만. 시험 `tests/test_camera_bounds.py`(gulf v6.0.2 키 고정 자료 — 실측 시각 실패, 요청 궤적 통과·화면 궤적 실패, 볼록성, 제안, 스케치). 골든 hormuz dark·light 무변화(클램프 0).
- **발견 버전**: v7.0.1 · **상태**: active

## RENDER-AP-027 — 콘티 판 막지도가 사용자의 지도 판단을 왜곡함(UF-106 → UF-121 재발)

- **증상(실제 현상)**: v7.4.0 diesel_road_2026 콘티 판 v2 — 사용자 "지도를 밝은 테마에서는 행정구역과 도시들과 주요 도로가 표현 되게 해놨자나. 그거 왜적용 안하지?"(UF-121, recurs_of UF-106). 전편 엔진에는 도로·강·행정선·도시 라벨이 들어갔으나, 콘티 판은 v4.9.0 D-0108 막지도(FlatMercatorStage — 육지·바다 단색 + 국경선, 라벨 없음)로 렌더됐다.
- **원리**: 콘티 판은 "흐름만 싸게 보는 판"으로 설계됐지만, 사용자는 콘티 판으로 지도 표현까지 판단한다. 두 판의 지도가 달라 "적용된 기능이 결과물에 나타나지 않는다"(15 관성)는 인상이 생겼다. 장치(도로·강 레이어)는 전편 경로에만 걸려 있었다 — 한 트랙에만 걸린 장치는 미보호다(C12-3, UF-02 교훈).
- **원칙**: 사용자가 판단하는 판은 전편과 같은 무대로 그린다. 콘티 판의 차이는 해상도·자리표시(사진·영상)·표식 띠뿐이다.
- **자동 조치**: 막지도 코드 삭제(FlatMercatorStage·draw_flat_map·flat_stage_factory·rules animatic.flat_map — 15 P2). `load_project(animatic=True)` 는 본 MercatorStage + geo 자산. 국가 폴리곤 자료(NE 110m)는 검사용으로 `geo/country_polygons.py`·`rules geo.country_polygons` 에 남김. 시험 `tests/test_g8_animatic.py::AnimaticMapRenderTest`(콘티 판 무대 = MercatorStage, geo.pkl 지오메트리 읽음).
- **발견 버전**: v7.4.0 · **상태**: active

## RENDER-AP-028 — 글꼴 교체로 사용자 지적(십자형 t)을 풀려 했으나 기준은 표기였음(UF-111 → UF-122 재발)

- **증상(실제 현상)**: v7.4.0 diesel_road_2026 콘티 판 v2 — 사용자 "오른쪽 상단 아일랜드에 십자가 처럼 보이는 t를 쓰지 말고 ton으로 표기 하라고 했자나."(UF-122, recurs_of UF-111). UF-111 장치는 단위 글자만 다른 글꼴(rules fonts.unit_font)로 그려 t 모양을 바꿨다 — 표기는 여전히 t.
- **원리**: 의견 문장의 표면("십자가처럼 보인다")을 글꼴 문제로 읽었고, 사용자의 기준(화면 표기 = ton)을 놓쳤다. 장치가 "어떻게 보이나"를 고쳤고 "무엇을 쓰나"는 열어 두었다.
- **원칙**: 사용자 의견의 장치는 문장의 요구를 그대로(표기·단어·값) 검사한다. 모양 보정은 보조일 뿐이다.
- **자동 조치**: `rules data.units` 에 ton, `rules data.unit_ton_pattern`, 검사 `unit_ton_glyph` hard(연출 화면 문자열 — 카드·패널·마커·경로 이름표). 시험 `tests/test_v740_static_camera.py::UnitTonTest`. 자막(원고)의 t 는 UF-122 범위 밖(오른쪽 위 아일랜드 지적) — 감독 결정 D-0241 §3.
- **발견 버전**: v7.4.0 · **상태**: active

## RENDER-AP-029 — 가장자리 보정이 화면 위끝 국기를 "통과"시킴(offscreen 검사의 사각)

- **증상(실제 현상)**: v7.4.0 diesel_road_2026 전편 v2 — 블라디보스토크 러시아 국기(act2_14~17)가 화면 위 가장자리에 걸려 보임(감독 D-0244). 앵커가 화면 y≈3 에 있어 edge_nudge 가 원을 34px 끌어내려 붙였다. offscreen 검사는 보정 뒤 상자만 보아 통과.
- **원리**: edge_nudge 는 앵커가 화면 안일 때만 켜진다. 앵커가 위끝에 걸치면 카메라·해상도 반올림에 따라 보정이 꺼져 원이 반쯤 잘린다. 보정 뒤 위치만 보는 검사는 이 경계를 못 본다.
- **원칙**: 뱃지 앵커는 화면 안쪽에 둔다. 위 가장자리 보정에 기댄 배치는 실패로 본다(좌우 보정은 골든 v3 인물 뱃지가 쓰므로 허용).
- **자동 조치**: 검사 `badge_clipped` hard(뱃지 원 안전 영역 + 위 가장자리 보정 의존). 시험 `tests/test_v740_static_camera.py::BadgeClippedTest`. 골든 0.
- **발견 버전**: v7.4.0 · **상태**: active

## RENDER-AP-030 — 지도 무대 패널 위 카드 겹침을 잡는 검사가 없었다(island 검사는 backdrop 전용)

- **증상(실제 현상)**: v7.4.0 diesel_road_2026 그래프 복원 프리뷰 — 오른쪽 상단 카드(act1_15·act4_21·act4_22)가 dual_line 패널 제목·출처 줄(걸프 "호르무즈 통과량과 다른 집계")을 가렸다. 사용자 "그래프 넣는 씬에서 오른쪽 상단 아일랜드가 그래프를 가리지 않도록 해"(UF-129). checks hard 0 으로 통과했다.
- **원리**: island_overlap·card_island 는 backdrop 무대 아일랜드 전용, badge_over_panel 은 versus 패널 + 뱃지만 본다. 지도 무대 패널 위 카드는 어떤 검사의 대상도 아니었다.
- **원칙**: 패널(모든 kind)이 떠 있는 동안 카드·계단식 카드·기사·인용은 패널 상자를 덮지 않는다(사진·영상·컷아웃은 골든 v3 의도 배치라 검사 밖 — 감독 결정 요청). 연출이 패널 앞에 끝내거나 뒤에 시작한다(자동 이동·숨김 없음, P8).
- **자동 조치**: 검사 `card_over_panel` hard(rules qa_checks.card_over_panel {min_overlap_sec 0.3, panel_pad_px 4}), director 프롬프트 규칙(rules direction_grammar). 시험 `tests/test_v740_card_over_panel.py`.
- **발견 버전**: v7.4.0 · **상태**: active

## RENDER-AP-031 — 큰 숫자 글꼴에 없는 '−'(U+2212)가 네모로, 글리프 검사는 표본 시각에서만 실제 글꼴 대조 (recurs_of fed_policy_2026 v1 '−' 사고)

- **증상(실제 현상)**: v7.4.0 diesel_road_2026 교체 3 — act3_11 카드 '−3.4%' 가 네모로 나왔다. 사용자 "특수문자 에러"(UF-131).
- **원리**: `glyphs` 검사의 문자열 대조는 프로젝트 글꼴 **합집합**(IBM Plex 에 U+2212 가 있어 통과)이고, 실제 그린 글꼴 대조(glyph_miss)는 프리뷰 컷 시각에서만 돌아 이 카드 시각이 표본에 없었다. v4.4.0 의 실제 글꼴 대조 장치가 표본 의존이라 같은 부류가 재발했다.
- **원칙**: 글꼴에 없는 글자는 같은 굵기 대체 글꼴로 그린다(원고·데이터 불변). 글리프 대조는 표본 시각과 상관없이 위험 문자열을 가진 모든 이벤트를 실제로 그려 본다.
- **자동 조치**: rules `fonts.glyph_fallback {disp: sansbb, dispm: sansb}`(typography.fallback_runs), 프리뷰·콘티 판 `glyph_sweep`(공통 cmap 밖 글자를 가진 이벤트마다 한 프레임, 파일 저장 없음) → checks glyphs hard. 시험 `tests/test_v740_outlet_glyph.py::GlyphFallbackTest`.
- **발견 버전**: v7.4.0 · **상태**: active
