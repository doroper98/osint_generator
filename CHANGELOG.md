<!--
tier: 3
last_synced_with: v0.38.1
ssot_for: [release-notes]
depends_on: [README.md, GOAL.md]
last_review: 2026-06-11
-->

# CHANGELOG

본 문서는 사용자(또는 후속 개발자) 관점의 릴리즈 노트입니다.
released 항목은 **append-only**입니다.

본 저장소는 [Semantic Versioning](https://semver.org/)을 따릅니다.

---

## [Unreleased]

### Added
-

### Changed
-

### Fixed
-

---

## [v0.38.1] — 2026-06-12

### Added
- **내레이션 파이프라인 (auto 컴포지션)** — 음성이 영상의 시계가 됨:
  - `hyperframes/scripts/build_auto_narration.py` — cue(text/tts)별 ElevenLabs
    합성 → **실측 커서 조립** (조각별 실측 길이 누적 = cue 시각, mp3 프레임
    패딩 드리프트 원천 차단 — 최초 구현은 목표시각+무음 방식으로 2.9초
    드리프트 발생, v0.34.8 교훈 재적용) → cuesync_auto.json + 단일 mp3.
  - `bundle_to_video.py --narration=synth|estimate` — 1차 변환 → 합성 →
    cuesync 재시계 2차 변환 + `<audio>` 트랙 주입(demo 계약)을 한 줄로.
    `--cuesync=path` 단독 적용도 지원.
  - `--estimate` 모드: API 없이 글자수 기반 길이 추정 + 무음 mp3 — sync
    메커니즘 검증용 (본 환경 e2e: 12씬 118초 → 음성 페이스 207초 재시계).

---

## [v0.38.0] — 2026-06-12

### Added
- **영상 필드 계약 소비 구현 (옵션 C 2차 완성, MINOR)** — agents_reviewer 가
  계약(docs/VIDEO_BUNDLE_CONTRACT.md)대로 번들에 실어 보낸 video 필드를 영상이
  실제로 사용:
  - **내레이션 cue 교체**: sections[].video.narration + report.video
    intro/outro_narration 을 해당 씬 시간창에 균등 배치 — 템플릿 문장 대체
    (SpaceX 번들 기준 32문장 채택, 템플릿 17건 대체). narration_tts 는 cue.tts
    로 보존 (음성 합성용).
  - **검증기 (G4)**: narration/highlights 의 모든 수치 토큰을 번들 직렬화
    말뭉치와 대조 — 불일치 문장 폐기 + 템플릿 폴백.
  - **스테이트먼트 씬**: 차트 없는 서술 섹션의 highlights 를 대형 세리프
    타이포(순차 등장 + emphasis 액센트)로 — 서술 전용 섹션 누락 해소.
  - versus 진영명 자동 추출 ("A인가, B인가" 제목 패턴), 쟁점/신호 섹션 매칭
    확장, 마켓/시그널 씬에 섹션 연결.
- 테마 별칭 (forest_sage→forest_archive, midnight_indigo→midnight_navy).
- `samples/spacex2026/` — 계약 구현 첫 번들 보존.

### Fixed
- 간트: 월 단위 날짜(YYYY-MM) 허용, 장기 범위에서 분기/연 눈금 자동 전환 +
  기간 라벨 연도 표기 (3년 임대에서 월 라벨 도배되던 문제).
- 스캐터: 좁은 범위(0~1) 눈금 소수 표기, accent→hi 매핑, 라벨 괄호 제거 +
  플레이트 줄바꿈 활용.

---

## [v0.37.2] — 2026-06-12

### Added
- `docs/VIDEO_BUNDLE_CONTRACT.md` — agents_reviewer 와의 영상 필드 계약 초안.
  sections[].video (narration/narration_tts/highlights/emphasis) +
  report.video (intro/outro_narration). 목적: ① cue 템플릿 문장 탈피 (대본
  생성을 보고서 작성 주체로 이동, 영상 쪽 LLM 무호출 유지), ② 차트 없는
  서술 전용 섹션의 영상 누락 해소 (스테이트먼트 씬). 사용자 결정 (옵션 ③).

---

## [v0.37.1] — 2026-06-12

### Added
- **잔여 차트 유형 5종** (NEXT_SESSION_PROMPT 옵션 B 잔여분, 사용자 요청):
  - SceneKit `buildStackedBars` — 가로 누적 막대 (세그먼트 좌→우 성장 + 범례
    pill + 행 합계), `buildWaterfall` — 증감 브리지 (부유 컬럼 + 점선 커넥터 +
    상승/하락/절대값 3색), `buildScatter` — 이변량 분포 (축·눈금 + 대각 기준선
    draw-on + LabelField 충돌 회피 포인트 라벨), `buildHeatmap` — 행×열 강도
    (단색/다이버징 자동 + 대각 웨이브 리빌 + 강한 셀 값 표기), `buildGantt` —
    일정 레인 (월 눈금 + phase 색 + "오늘" 라인 + 막대 성장).
  - auto_builder 씬 타입 5종 + 변환기 정규화기(`norm_*`, 복수 스키마 허용:
    parts/segments/series, kind/type, dict/list 히트맵) + 씬 플랜 자동 통합.
  - `--preview-charts` — 합성 데이터 갤러리 컴포지션 생성 (시각 회귀 픽스처,
    `hyperframes/briefing/preview_charts.html`).

---

## [v0.37.0] — 2026-06-11

### Added
- **타임라인 시각화 5유형** (사용자 요청): 계단(ladder)·수평 축(axis)에 더해
  **서펜타인**(2단 S자 — 분기점 11개↑), **수직 레일**(긴 설명형 라벨),
  **메트로**(국면 구간 색 노선도 — 미래 비중 40%↑) 신설. 변환기가 데이터
  성격(국면 조합/개수/라벨 길이/미래 비중)으로 자동 선택, `--timeline=` 강제.
- **컬러 테마 5종** (`assets/themes.js` + CSS 토큰화): ink_brass(디폴트),
  graphite_slate(앰버 — agents_reviewer 동명 테마 자동 매칭), midnight_navy
  (아이스 블루), forest_archive(민트 그린), **paper_oxblood(라이트 — 신문
  인포그래픽)**. 번들 theme.id 일치 시 자동 적용, `--video-theme=` 강제.
  의미색(국면/마켓)은 적용된 테마 변수에서 런타임 파생.
- **미개발 유형 선반영**: 슬로프 차트 씬(ch-10 사용 — 좌→우 변화선 + 최대
  변화 하이라이트), **도넛 차트 빌더**(구성비 — 세그먼트 draw + 리더 라벨,
  데이터 도착 시 즉시 사용 가능), **인용 인터스티셜 씬**(pull_quote → 대형
  세리프 한 장, 숫자 자동 강조).
- 반도체 번들 자동 영상: 9씬 89초 → **11씬 106초** (인용·슬로프 추가,
  graphite_slate + 서펜타인 자동 선택).

---

## [v0.36.1] — 2026-06-11

### Added
- **씬 라이브러리 확장** (사용자 피드백 "단조롭다 + 화면 수 적다 + 계단 타임라인
  매번은 별로"):
  - SceneKit `buildAxisTimeline` — 수평 축 타임라인 (중립 시계열용). 변환기가
    **crack+present 공존(에스컬레이션 서사)일 때만 계단**, 아니면 수평 축 자동 선택.
  - SceneKit `buildCandleChart` — 일봉 캔들 (가이드라인 + 우측 가격축 + 종가 라인).
  - SceneKit `buildBarPanels` — 가로 바 패널 1~2개 (최댓값 하이라이트 + 카운터 +
    note). 같은 단위의 마지막 바 차트 2개는 듀얼 패널로 자동 묶음 (두 회사 목표가).
  - auto 씬 "signals" — 관측 신호 카드 (deadline 칩 + `<미검증>` 태그, G4).
- 반도체 번들 기준 자동 영상이 **5씬 53초 → 9씬 89초** (candle/bars×2/signals 추가).

### Fixed
- **렌더러 빈 화면 사고**: hyperframes 렌더 세션이 body 끝의 외부
  `<script src>` 를 실행하지 않아 v0.36.0 의 auto.html 이 53초 내내 빈
  프레임으로 인코딩됨 (로컬 Chromium 검증과 렌더 결과 불일치). 변환기가
  auto_builder.js 를 **인라인**으로 박도록 수정 (SSOT 는 assets 파일 유지).
- 듀얼 바 패널 cue 가 단위 스케일이 다른 두 패널을 섞어 비율(19.0배)을 내던
  버그 → 패널별 상단/하단 비율로 교정.

---

## [v0.36.0] — 2026-06-11

### Added
- **번들 → 영상 자동 변환 1차** (NEXT_SESSION_PROMPT 옵션 C, MINOR):
  - `hyperframes/scripts/bundle_to_video.py` — agents_reviewer report_bundle 을
    읽어 씬 플랜(타이틀/타임라인/쟁점/가격/클로징)·cue·테마를 결정론 추출,
    `hyperframes/briefing/auto.html` 생성. **데이터에 있는 씬만 조립** —
    이번 번들(반도체 분석)은 지도·행위자가 없으므로 해당 씬 없음.
  - `hyperframes/briefing/assets/auto_builder.js` — DATA 주도 제네릭 컴포지션
    팩토리 (씬 조건부 생성 + 마스터 타임라인 + cue). CSS 는 briefing/index.html
    <style> 재사용 (테마 SSOT).
  - 번들 테마 토큰(accent/up/down) → CSS 변수 오버라이드 (graphite_slate 검증).
  - 헤드라인 자동 줄바꿈+마지막 줄 강조, 타임라인 13→7 분기점 샘플링(비과거
    우선), contradictions → 강세/보수 카드(다수설/소수설 + 게이지), line 차트
    → 마켓 카드(%·kind 자동 분류), pull_quote 숫자+단위 자동 강조(em),
    confidence → 신뢰도 박스, 출처 라인 자동 구성.
- SceneKit `buildProfileCards` 게이지 축 라벨 파라미터화 (자제/확전 →
  임의 축, 예: 신중/강세).
- `samples/semicon2026/` — 검증에 사용한 실제 번들
  (analysis_20260611_130642_9f7fbb749d) 보존.

---

## [v0.35.6] — 2026-06-11

### Fixed
- **링크의 국기/플레이트 간섭 제거** (사용자 보고 "선들이 국기에 가려지거나
  간섭되면 안 될 것"): buildNetwork 라우팅에 회피 탐색 추가 — 곡선은 bend×방향
  8후보, 직각은 엘보 위치 5후보(+곡선 폴백 6후보)를 22px 샘플링으로 검사해
  ① 노드·플레이트 모두 회피 → ② 노드만 회피 순으로 선택. 스테이지 밴드 이탈
  후보는 기각. 이름 플레이트 배치를 링크보다 먼저로 재배열(회피 대상 확정).

---

## [v0.35.5] — 2026-06-11

### Changed
- **하이브리드 링크 라우팅** (사용자 결정 "원거리 지원/영향은 곡선"):
  근거리(인접 관계) = 라운드 직각, 장거리 = 완만한 위쪽 아치(거리 비례 bend).
  엔진 기본은 거리 임계값(430px) 자동 판별 + 링크별 `curve` 강제 오버라이드.
  브리핑 데이터: 미국발 관계 3건은 대양 건너 투사 의미로 곡선 강제,
  현지 관계(헤즈볼라↔이스라엘/레바논)는 직각 유지. 흐름 펄스는 두 라우팅
  모두에서 동일 작동.

---

## [v0.35.4] — 2026-06-11

### Changed
- **연결선 직각 라우팅** (사용자 요청 "각진 부분에 라운드가 있는 직각 선, 단정하게"):
  SceneKit `orthoPath` 신설 — H-V-H / V-H-V 엘보 + 라운드 코너(Q 베지어),
  노드 가장자리 stub. 네트워크 링크가 직선 사선 → 라운드 직각으로.
- **흐름 펄스 애니메이션**: 링크 draw 완료 후 밝은 세그먼트가 s→t 방향으로
  경로를 순환(2.4s × 3바퀴) — 영향을 주고받는 방향성 시각화. 타임라인 내
  tween 이라 시킹 안전.
- **국기 풀블리드**: 노드 원 클립 r-3 → r-1 + 잉크 오버레이 제거, 프로필 카드
  국기 82px — 도형 안에 꽉 채움 (사용자 요청).

---

## [v0.35.3] — 2026-06-11

### Added
- **실측 베이스맵** (날리지식 패턴 ⑤, NEXT_SESSION_PROMPT 옵션 E 첫 단):
  `hyperframes/scripts/build_mideast_map.mjs` — world-atlas(Natural Earth 50m,
  PD) → 메르카토르 사전 계산 → `assets/mideast_map.js` (19개국 path + 지명 px,
  52KB). 런타임 d3 의존 없음 (결정론 유지).
- SceneKit `buildBasemap` — 잉크 톤 실측 지형 + 당사국 하이라이트 + 헤더 밴드
  보호 상단 페이드 마스크.
- **국기/인물 노드** (날리지식 패턴 ③, 사용자 레퍼런스): `buildNetwork` 재작성 —
  지오 앵커(앵커 점 + 점선 리더 + 노드 충돌 회피 배치) + 원형 클립 국기/이미지
  노드 + 이름 플레이트. 프로필 카드 모노그램에도 국기 적용.
- `assets/flags/` — flag-icons(MIT) 국기 4종 + RIGHTS.md (C9 권리 기록).
  헤즈볼라는 조직기 권리·민감성 문제로 모노그램 유지. 인물 사진은 위키미디어
  차단(네트워크 정책)으로 보류 — `assets/portraits/` 추가만으로 교체 가능 구조.

### Changed
- S3 행위자 네트워크 / S5 지오 씬 모두 **실제 중동 지도 중심**으로 재구성
  (사용자 요청). 마커·앵커 좌표 전부 실측 투영값.
- scene-head/scene-no z-index 상향 — 지도 육지가 타이틀을 덮던 레이어 사고 픽스.

---

## [v0.35.2] — 2026-06-11

### Changed
- **테마 전면 교체: midnight_indigo → ink & brass 에디토리얼** (사용자 피드백
  "AI vibe가 너무 많이 느껴져 정성이 안 느껴진다").
  - 네이비/파란 글로우/블롭/그리드/글래스 카드 등 AI-dashboard 문법 전부 제거.
  - 잉크 차콜 배경 + 브라스(#c4a265) 단일 액센트 + 옥사이드/세이지/슬레이트
    뮤트 데이터 컬러 + 헤어라인 룰.
  - **Noto Serif KR**(가변, 124 서브셋 6.3MB 로컬 내장) — 헤드라인·씬
    타이틀·인용·씬번호·모노그램에 세리프 디스플레이.
  - SceneKit SVG 하드코딩 색 → CSS 토큰(`--sk-*`, 폴백 포함)으로 분리 —
    엔진이 테마 독립적이 됨.

---

## [v0.35.1] — 2026-06-11

### Added
- SceneKit 씬 빌더 ⑤ `buildProfileCards` — 키 플레이어 프로필 카드
  (모노그램 + 컬러 링 draw-on + 입장 게이지 "자제↔확전" + 분석 추정 태그).
  C9 권리 안전 기본값: 인물 사진/AI 이미지 대신 모노그램.
- `hyperframes/briefing/` 신규 S4 "키 플레이어" 씬 (트럼프/이란 지도부/
  이스라엘/헤즈볼라 4카드, 날리지식 패턴 ③ — NEXT_SESSION_PROMPT 옵션 D 첫 단).

### Changed
- 브리핑 컴포지션 60초 6씬 → **72초 7씬** (지도/마켓/클로징 +12s 시프트,
  cue 3개 신규 + 7개 시프트). 브리핑은 narration mp3 미생성 상태라 시프트 안전.

---

## [v0.35.0] — 2026-06-11

### Added
- `hyperframes/briefing/assets/scene_kit.js` — **SceneKit 영상 컴포지션 엔진**
  신설. 안전영역 밴드(헤더/스테이지/자막), 결정론적 텍스트 폭 추정,
  **LabelField 충돌 회피 라벨 배치기**(선분·베지어·원 장애물 + 후보 슬롯 +
  밀어내기 탐색), 플레이트 라벨(자동 줄바꿈), 마커↔라벨 리더선,
  `getTotalLength` 실측 draw-on, 단어 단위 글자 분할, 씬 빌더 4종
  (스텝 타임라인 / 행위자 네트워크 / 지오 씬 / 마켓 카드).

### Changed
- `hyperframes/briefing/index.html` — v0.34.13의 일회성 하드코딩 레이아웃을
  SceneKit 기반 데이터 주도 빌드로 전면 리팩토링. 사용자 보고 결함
  ("라벨 겹침, 줄 위에 글자, 어디에 내놓을 수 없는 수준") 구조적 해소:
  - S2 사다리: 7개 스텝 라벨이 서로/연결선/씬번호와 겹치던 사고 → 플레이트
    + 리더선 + 충돌장 배치로 겹침 0.
  - S3 네트워크: 노드 원 밖으로 글자 넘침 → 라벨 폭 기반 반지름 자동 산정.
    링크가 원 중심까지 파고들던 것 → 원 가장자리에서 트리밍. 범례가 씬번호와
    겹침 → 수평 pill 범례로 재배치.
  - S4 지도: 인접 마커(베이루트/북부 이스라엘) 라벨 상호 겹침 + 점선 아크가
    글자 관통 → 충돌장 배치 + 플레이트. 데이터에만 있고 미렌더되던 보조 아크
    라벨(헤즈볼라 사격/이스라엘 공습) 렌더 + 미사일 도착 임팩트 링 추가.
  - S6 인용문: 글자 단위 분할이 keep-all 을 무력화해 단어 중간 줄바꿈
    ("명/분") → 단어 span 래핑으로 차단.
  - 하드코딩 stroke-dasharray(4000/3000/2000) 전부 실측 길이로 대체.
  - 자막 가독용 하단 스크림 추가.
- 검증: Playwright(chromium 1194) 시킹 렌더 11프레임 + 플레이트 겹침/밴드
  위반 자동 감사(pageerror 0, 겹침 0, 위반 0).

### Note
- agents_reviewer 의 차트 생성 보강은 **참고만** — 본 엔진은 영상 생성
  맥락(GSAP 타임라인 시킹, 결정론, 1920×1080 브로드캐스트 레이아웃)에 맞춰
  독자 설계 (C0).

---

## [v0.34.13] — 2026-06-08

### Added
- `hyperframes/briefing/` — OSINT 시네마틱 브리핑 컴포지션 신규. report_bundle
  (`midnight_indigo` 테마) 데이터를 100% 적용한 60초 6씬 GSAP 영상 HTML(타이틀·
  에스컬레이션 사다리·5행위자 네트워크·3좌표 지도/미사일 아크·시장 스파크라인·
  클로징). 과거 demo 미감 비상속, 전면 재설계(영상미 C0).

---

## [v0.34.2] — 2026-06-06

**v0.34.1 사용자 검수 후 버그 픽스 — 라인/자막 안 보이던 문제 해결 + 30초 확장**.
사용자 스크린샷으로 진단: 차트 라인 0:10 시점에서도 보이지 않고, 자막 박스만 보이고
텍스트는 빈 상태. 두 근본 원인 식별 후 픽스.

### Fixed

- **라인 draw-on 작동 안 함** — SVG `pathLength="1"` + `stroke-dasharray="1"` +
  `stroke-dashoffset="1"` attribute 의존이 GSAP 트윈 시작점 인식 실패 야기. `path
  .getTotalLength()` 로 실제 path 길이 측정 후 `gsap.set(p, {strokeDasharray: len,
  strokeDashoffset: len})` 명시 시작. 콜아웃 connector 3개 (`#conn1-3`) 동일 패턴.
- **자막 텍스트 비어 보임** — cue 들이 `position: absolute` 인데 부모 `.subtitle` 에
  `position: relative` 누락으로 cue 가 viewport 어딘가 튀어감. 자막 박스 하나
  (`<span id="subtitleText">`) 만 두고 GSAP `.call()` 로 시간 시점에 `textContent`
  swap + 박스 자체 opacity 짧은 페이드 (0.2-0.25s).

### Changed

- **composition duration 14s → 30s** (사용자 요청).
- **narration cue 4 → 8** (호르무즈 시나리오 확장: 봉쇄 발생 → 원유 20% 차단 → 유가
  50% 급등 → 1차 휴전 안정 → UAE 표적 공격 재반등 → 협상 진행 → 지정학 리스크 요약).
- **콜아웃 2 → 3** (호르무즈 봉쇄 + 1차 휴전 + UAE 표적 공격). 명시 `style="opacity:0"`
  inline 으로 GSAP 트윈 시작점 안전 확보.
- **데이터 점 마커 스타일** = 흰 fill + 두꺼운 오렌지 stroke 3px → line 위에서 가독성
  향상. r=5 → r=6.
- **라인 draw-on 시간** 2.0s → 3.0s (좀 더 느긋하게).
- **Ken Burns** 1.03 → 1.04 (30초 동안 좀 더 확대).

### Known Limitations

- 음성 여전히 placeholder (`assets/audio/brent.mp3`). 사용자 머신에서 ElevenLabs 로
  생성 시 자동 재생.

---

## [v0.34.1] — 2026-06-06

**HyperFrames 프로토 — 사용자 1차 피드백 4 픽스 (영상미 C0)**.

### Added

- **데이터 점 마커 9개** — line path 의 각 데이터 점에 오렌지 fill + 흰 테두리 r=5px
  원. 라인 draw-on 진행에 맞춰 stagger pop-in (0.18s 간격, 라인이 닿을 때 차례로 등장).
  사용자 피드백 "차트에 데이터가 없었던 것 같다" 대응.
- **자막 다중 큐 4개** — 14초 동안 시간 비례로 swap (3.2s / 3.5s / 3.0s / 3.5s):
  - "3월 4일, 호르무즈 해협 봉쇄로 브렌트유가 한 달 만에 50% 급등했습니다"
  - "유가는 한때 배럴당 120달러를 돌파하며 시장에 충격을 줬습니다"
  - "4월 7일 1차 휴전 합의 직후 잠시 안정세를 보였지만"
  - "5월 들어 다시 약 114달러까지 반등하며 변동성을 이어가고 있습니다"
- **`<audio data-start data-duration src="assets/audio/brent.mp3">`** placeholder —
  사용자 머신에서 ElevenLabs key 로 생성한 mp3 를 본 경로에 두면 자동 재생.

### Changed

- **자막 폰트 weight 700 → 800 (Pretendard ExtraBold)** — Korean broadcast 가독성 +
  편집 톤. letter-spacing -0.4px 조여서.
- **자막 배경 `rgba(26,26,26,0.82)` → `#4a1e10` (dark burnt orange)** — 차트 accent
  `#e84a2d` 의 dark variant. 사용자 요청 "차트/지도/정보에 맞는 짙은 색" 대응. 톤 매칭
  그림자 `rgba(74,30,16,0.35)` 추가.
- 향후 씬별 토큰화 예정 (회색 dashboard → `#1a1a1a`, 지도 빨강 강조 → `#2a0a0a`).

### Known Limitations

- **음성 클라우드 미렌더**: SSL 인터셉트 (`certificate verify failed`) 로 edge-tts /
  ElevenLabs API 호출 불가. 음성 합성은 사용자 머신에서 본인 `.env` 의 ElevenLabs key
  로 실행. 본 PATCH 는 `<audio>` placeholder 만 사전 배선.
- composition duration 10s → 14s 로 확장 (자막 4 큐 시간 확보).

---

## [v0.34.0] — 2026-06-06

**HyperFrames 마이그레이션 시작 — Remotion 폐기, HTML+GSAP+headless Chrome 으로 전환 (영상미 C0)**.
사용자가 v0.33.1 영상 검수 후 HyperFrames (HeyGen 오픈소스, Apache 2.0) 검토 요청 →
deep research 결과 GSAP/Lottie 1급 지원, HTML 단순성, deterministic seek 가 NYT/Vox-grade
편집 영상미와 정합. 사용자 결정: "1로 가자" (완전 전환). 첫 프로토타입 1 씬 (브렌트 유가
line chart) 렌더 + SendUserFile 전달 완료. 사용자 평가 "훨씬 나아졌다, 방향 OK".

### Added

- **`hyperframes/` 디렉토리** — 새 모션그래픽 엔진 (Remotion 대체 후보, 병렬 검증 중).
  - `hyperframes/package.json` + `node_modules/hyperframes@0.6.76` CLI.
  - **`hyperframes/demo/index.html`** (프로토타입 1 씬, 10초):
    - Pretendard Variable `@font-face` 로컬 로드 (`assets/fonts/PretendardVariable.woff2`)
    - 광범위 light dashboard 톤 (`#f5f1ea` 크림 + `#ffffff` 카드 + `#e84a2d` 오렌지 accent)
    - SVG line + 콜아웃 2개 (Subject + Connector + Note) + 끝점 라벨
    - GSAP timeline (paused, `window.__timelines["brent"]` 등록) 으로:
      * 브랜드 / 출처 / takeaway 페이드인
      * 라인 `strokeDashoffset` draw-on (2초, power1.inOut)
      * 콜아웃 1·2 subject pop + connector draw + note 페이드 stagger
      * 끝점 마커 pop + 시리즈명·값 슬라이드인
      * Ken Burns 전체 scale 1.0 → 1.03 (10초)
    - 자막 바 다크 translucent `rgba(26,26,26,0.82)` + 흰 굵은 글씨 (한국 broadcast 톤)
  - `hyperframes/demo/{CLAUDE.md, AGENTS.md, hyperframes.json, meta.json, package.json}`
    — `npx hyperframes init` scaffold 산출.
- **`.gitignore`** — hyperframes `node_modules` / `renders` / `.hyperframes-cache` 추가.
- **시스템 설치**: `ffmpeg 6.1.1` (apt), `chromium-browser` 제거 (snap 의존이라 puppeteer
  실패), `PUPPETEER_EXECUTABLE_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome` 로
  playwright 번들 chromium 우회.

### 결정 근거 (Deep Research 5 트랙 통합)

| 축 | Remotion | HyperFrames |
|---|---|---|
| 모델 | React + `useCurrentFrame` | HTML + `data-*` + GSAP timeline.seek |
| GSAP | wall-clock 충돌 위험 | **1급 어댑터, deterministic** |
| Lottie | `@remotion/lottie` expression 이슈 | **1급 어댑터** (AE → JSON 워크플로우 표준) |
| 폰트 | `@remotion/fonts` cancelRender 사고 (v0.33.0) | HTML `@font-face` 단순 |
| 라이센스 | Apache 2.0 + 회사 seat | Apache 2.0 **완전 무료** |
| 산업 사례 | NYT/Vox 0건 | HeyGen 자체 + tldraw/TanStack |

### 사용자 1차 평가 (HyperFrames 프로토)

- ✅ "훨씬 나아졌다" — 방향 옳음
- ⚠️ "차트에 데이터가 없었던 것 같다" — line path 만 그리고 각 데이터 점 마커 누락
- ➕ "자막을 진짜 나레이션 스러운 자막 + 음성을 입혀보자" — ElevenLabs TTS 통합
- ➕ "자막 폰트는 어떤걸로?" — 권장: Pretendard ExtraBold 단일계 유지
- ➕ "자막 배경을 차트/지도/정보에 맞는 짙은 색으로" — 씬별 `subtitleBgColor` 동적

### 다음 (v0.34.1 — 사용자 4 피드백 반영)

1. 데이터 점 마커 추가 (line 의 각 7 점에 작은 원)
2. ElevenLabs TTS + 단어 단위 자막 sync
3. 자막 폰트 = Pretendard ExtraBold 단일계
4. 자막 배경 동적 (씬별 `subtitleBgColor`, dark variant 자동 derive)

### 다음 (사이클)

- v0.34.x: HyperFrames 프로토 검증·확장 + 음성·자막 통합 + 차트 데이터 표현 보강
- v0.35.0: 차트 family 15종 HTML+SVG+GSAP 으로 포팅 (Remotion 의 React 자산 변환)
- v0.36.0: `orchestrator/render_io.py` → HyperFrames 매니페스트 출력. `build-audio-demo`
  → HyperFrames 음성 동기. Remotion 디렉토리 archive 또는 삭제.
- v0.37.0+: 호르무즈 풀 파이프라인 + 사용자 최종 검수

### Deep Research 출처 (v0.34.0 결정 근거)

- [HyperFrames GitHub (heygen-com/hyperframes)](https://github.com/heygen-com/hyperframes)
- [Hyperframes Student Kit — GSAP/HTML 예제 12개](https://github.com/nateherkai/hyperframes-student-kit)
- [HyperFrames Open-Source Framework — Medium 해설](https://medium.com/data-science-in-your-pocket/heygen-hyperframes-open-source-video-generation-framework-bcb9c447b444)

---

## [v0.33.1] — 2026-06-06

**사용자 1차 검수 후 4 픽스 (영상미 C0)**.

### Fixed

- `ChartView.tsx`: 모든 차트에 `title={chart.title}` → `title={null}` (Briefing takeaway
  와 중복 정보 → line 차트 왼쪽 첫 점 라벨이 차트 제목에 가려 안 보이던 문제 해소).
- `Briefing.tsx`: 우상단 `<확인>` `<추정>` 라벨 배지 화면 표시 제거 (`scene.label` 데이터
  는 보존).
- `design.ts`: `chart.padRight` 100 → 180 (stacked area 우측 끝점 직접 라벨 잘림 픽스).
- `charts/xy/ForecastChart.tsx`: actual 마지막 점을 forecast mid + band 시작에 prepend
  (두 시리즈 간 공백 제거, agents_reviewer 동일 지적 사용자 재확인).

---

## [v0.33.0] — 2026-06-06

**Editorial Restraint Reset — 디자인 시스템 전면 갈아엎기 + 사용자 1차 픽스 (영상미 C0)**.
사용자 평가 "전반적으로 차트라던지 폰트, 네온 글로우 같은 이펙트가 너무 구려. 촌스러워"
→ v0.29.0 Aurora Glass + 8색 Okabe-Ito + 다크 베이스 + 글로우 노선 폐기. Deep research 5
트랙(NYT/Vox/FT/Bloomberg 편집 룰, Remotion 베스트 프랙티스, 편집 안티패턴, 한국 broadcast
타이포, 한국 채널 실 사용) + 사용자 9장 dashboard 레퍼런스 + 3장 날리지식 화면 + 5개
모션 패턴 텍스트 지시 통합해 **light dashboard + 오렌지 단일 accent + Pretendard 굵은
산세리프 + Ken Burns + 다크 broadcast 자막** 으로 전면 재구성. 클라우드 환경에서 직접 mp4
2회 렌더 (v0.33.0 첫 컷 + v0.33.1 사용자 피드백 4 픽스) 사용자 SendUserFile 전달 완료.

### Removed

- **`remotion/src/AuroraGlassCard.tsx`** 삭제. conic gradient + 회전 글로우 폐기
  (NN/g glassmorphism 가이드 위반, Reuters/FT/NYT 시스템 0건).

### Added

- **`remotion/src/design.ts` 전면 재작성** — 편집 dashboard 토큰 SSOT.
  - Color: `surface.page #f5f1ea` (크림) + `surface.card #ffffff` + `accent.primary
    #e84a2d` (오렌지) + 시리즈 5색 (오렌지/네이비/라벤더/핑크/앰버). 의미 라벨 4색
    톤다운. 8색 Okabe-Ito + Aurora + neon 폐기.
  - Typography: Pretendard Variable 폰트 스택, weight 400-900, size 14→180 hero,
    `letterSpacing.tightest -2` (거대 숫자), `letterSpacing.caps 3` (kicker).
  - Motion: Material decelerate/standard/accelerate, duration 150-1200ms, stagger
    50-150ms (Vox/NYT 편집 기준). spring/bounce/glow 폐기.
  - Spacing: 8 grid, `radius.lg 22` 라운드 카드, shadow 1단계 절제.
  - **v0.33.1 픽스**: `chart.padRight 100 → 180` (끝점 직접 라벨 잘림 해소).
- **`remotion/src/components/SurfaceCard.tsx`**(신규) — 흰 라운드 카드 + soft shadow,
  Aurora glass 대체 표준 컨테이너.
- **`remotion/src/components/NumericHero.tsx`**(신규) — 거대 숫자 카운트업 hero.
- **`remotion/src/fonts.ts`**(신규, no-op 스텁) — Phase 5 에서 staticFile+FontFace+
  delayRender 안전 패턴 재구현 예정. `@remotion/fonts` 의 `loadFont` 가 fetch 실패 시
  cancelRender 까지 가서 렌더 자체 실패 → silent skip.
- **`remotion/public/fonts/PretendardVariable.woff2`** (2MB, npm `pretendard` 추출).
- **npm**: `@remotion/fonts`, `@remotion/paths`, `@remotion/layout-utils`,
  `pretendard`, `@fontsource/pretendard`.

### Changed

- **`remotion/src/Briefing.tsx`** 전면 재작성. AuroraGlassCard 제거. 사각형+캡스 브랜드,
  SurfaceCard 중앙 컨텐츠, Ken Burns 1.0→1.03 전 씬, 다크 translucent 자막.
  **v0.33.1 픽스**: 우상단 `<확인>` `<추정>` 라벨 배지 화면 표시 제거 (scene.label 데이터
  보존, 사용자 명시 요청).
- **`remotion/src/ChartView.tsx`** **v0.33.1 픽스**: 모든 차트에 `chart.title` 대신 `null`
  전달 (Briefing 의 takeaway 와 중복 정보 → 왼쪽 첫 점 라벨 가림 해소).
- **`remotion/src/charts/xy/ForecastChart.tsx`** **v0.33.1 픽스**: `actual` 마지막 점을
  `forecast.mid` 와 `band` 시작에 prepend → 두 시리즈 간 공백 제거 (agents_reviewer 가
  지적했던 동일 이슈 사용자 재확인).
- **`remotion/src/components/{ChartFrame,Axis,Callout,ReferenceRegion}.tsx`** — 새 토큰
  재배선, glow/halo/blur 제거.
- 모든 차트 컴포넌트 — `surface.s1/base` → `surface.cardAlt/page`, `accent.quote` →
  `accent.primary`, `accent.positive/negative` → `label.verified/unverified` 일괄 rename.

### 사용자 측 사용법

```cmd
cd C:\01_Antigravity\osint_generator
git pull origin claude/stoic-galileo-Xmxyj
cd remotion
npm install
npx remotion render src/index.ts Briefing demo_out.mp4 ^
  --props=demo_props.json --public-dir=public
```

### 날리지식 5 모션 패턴 진행

| 패턴 | 상태 |
|---|---|
| ① 화면전환 부드러움 | 부분 (씬 진입 18f opacity fade) |
| ② Ken Burns 스케일 | ✅ 적용 — 전 씬 1.0→1.03 |
| ③ 인물 부드러운 등장 | 미구현 (Phase 4) |
| ④ 엔티티 연결선 draw | 미구현 (Phase 4, Callout 부분 패턴) |
| ⑤ 다크 지도 + 토큰 | 미구현 (별도 GeoScene, Phase 3) |

### 다음 (사용자 요청 별도 PATCH)

사용자 5번 피드백 = **Codex 영상미 검수 체계** 신설 (v0.33.2 메타 PATCH 예정). 매 PATCH 마다
자동 키프레임 추출 → 영상 LLM 에 편집 영상미 룰 위반 검사 → review 결과를 다음 PATCH 입력
으로. C10 (코드 리뷰) 와 분리된 새 카테고리 (디자인 리뷰) 로 CLAUDE.md 박음.

### Deep Research 출처 (의사결정 근거)

- NYT/Vox/FT/Bloomberg 편집 룰 (FlowingData NYT, FT Visual Vocabulary, Reuters Graphics
  style, Wilke Fundamentals Ch.26, Amanda Cox annotation layer, NN/g glassmorphism)
- Remotion 베스트 프랙티스 (remotion-dev/d3-example, charts.md, @remotion/fonts,
  @remotion/paths evolvePath, GSAP/Lottie deterministic pitfalls)
- 한국 broadcast 타이포 (Fontrix Rix헤드/Rix정고딕 SBS, MBC 새로움체, KBS Yoon Design,
  Pretendard GOV 2024-04 적용)
- 사용자 9장 dashboard 인포그래픽 레퍼런스 + 3장 날리지식 (`UCQKZQFd7AfgHOYoui6OE9Ew`)

---

## [v0.32.2] — 2026-06-05

**`build-audio-demo` CLI — 데모 props 에 음성 입히기 (사용자 편의)**. project state /
full_script 흐름을 거치지 않고 props 한 파일만으로 ElevenLabs (또는 다른 백엔드) 음성을
입혀, 새 차트 데모 + 음성을 빠르게 검수.

### Added

- **`orchestrator/audio_demo.py`**(신규) — `build_audio_demo(props_path, backend,
  voice, audio_subdir)`. props 의 각 scene narration → TTS 합성 → `demo_audio/`
  서브폴더에 wav/mp3 저장 → scene `audioPath` + `durationSec` + `startSec`
  실 음성 길이에 맞춰 갱신 → `<원본stem>_with_audio.json` 출력. project state /
  full_script / project_dir 컨텍스트 없이 동작.
- **`orchestrator/main.py`** — `build-audio-demo <props_path> [--backend
  elevenlabs|local|stub|voicebox] [--voice ID] [--audio-subdir NAME]` 서브커맨드.
  `_cmd_build_audio_demo` 핸들러.
- **`tests/test_audio_demo.py`**(신규, 4 케이스) — stub backend e2e (props 갱신,
  startSec 재누적, 누락 파일 / 빈 scenes 에러).

### Changed

- 본 PATCH 는 기존 `build-audio` (project state 기반) 동작을 변경하지 않음. demo 전용
  병렬 경로 추가.

### 사용자 측 사용법

```cmd
cd C:\01_Antigravity\osint_generator
python -m orchestrator.main build-audio-demo remotion\demo_props.json --backend elevenlabs

cd remotion
npx remotion render src/index.ts Briefing demo_out.mp4 ^
  --props=demo_props_with_audio.json --public-dir=.
```

`.env` 의 `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` 자동 사용(v0.32.1).

---

## [v0.32.1] — 2026-06-05

**`.env` 자동 로딩 — 매 cmd 세션 키 입력 불필요 (사용자 편의)**. ElevenLabs 등 secret 을
저장소 root `.env` 한 곳에 모으고, 모든 `python -m orchestrator.main ...` CLI 가 자동
로드. `.env` 는 `.gitignore` 가 이미 차단(C9).

### Added

- **`orchestrator/main._load_env_file()`**(신규) — `main()` 진입점에서 호출. 저장소 root
  `.env` 가 있으면 `python-dotenv` 로 로드. **`override=False`** — 운영 환경의 명시적
  export 가 `.env` 보다 우선(prod 안전). `.env` 미존재 / `python-dotenv` 미설치는 silent
  no-op.
- **`requirements.txt`** — `python-dotenv>=1.0` 추가(ASCII-only 주석 규칙 준수).
- **`.env.example`** — 갱신. 옛 placeholder (ANTHROPIC/OPENAI/Telegram/YouTube/Drive) 정리,
  실제 사용 중인 `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` / `ELEVENLABS_MODEL_ID` /
  `OSINT_ALIGN_BACKEND` / `OSINT_LLM_STUB` 등 도큐먼트.
- **`tests/test_env_loader.py`**(신규, 4 케이스) — ① 키 로드, ② 기존 환경변수 override 안
  함, ③ .env 없을 때 silent, ④ dotenv 미설치 시 silent.

### MVP Professional Bar 진행

- 없음 (사용자 편의 PATCH — 영상미 사이클과 직접 무관).

---

## [v0.32.0] — 2026-06-05

**Phase 2 — Bar / Point family 정통 재구현 (영상미 C0)**. bar / lollipop / range_bar /
stacked_bar / waterfall / scatter / bubble / slope / candle 를 디자인 시스템 + d3-scale
`scaleBand` + 카테고리 stagger + Material easing + 직접 라벨 + 라벨 충돌 회피로 재구현.

### Added

- **`remotion/src/charts/cat/BarChart.tsx`**(신규) — `mode: "bar" | "lollipop" | "range"`
  단일 컴포넌트. `scaleBand` 로 카테고리 배치, 카테고리 stagger 진입(`staggerToken(n)`),
  Material decelerate easing, 막대 위/아래 값 라벨(grow 끝나기 직전 페이드인), 음수 막대는
  `seriesColor(5)` 다크오렌지. Range 막대는 중앙에서 양쪽으로 확장.
- **`remotion/src/charts/cat/StackedBarChart.tsx`**(신규) — 카테고리 + 시리즈 이중 stagger
  (카테고리 sweep + 그 안에서 시리즈 60ms 간격), 마지막 시리즈 상단 둥근 모서리, 우상단
  시리즈 범례.
- **`remotion/src/charts/cat/Waterfall.tsx`**(신규) — 누적 막대 + connector 점선
  (이전 막대 끝 → 본 막대 시작), `accent.positive`/`accent.negative`/`seriesColor(0)`
  분기, `+`/`-` 부호 자동 표기, total 막대는 기준선부터 grow.
- **`remotion/src/charts/cat/PointChart.tsx`**(신규) — scatter / bubble. bubble 반지름 =
  `sqrt(size/smax) * 50`(면적 비례), 점 stagger pop-in(60ms × 항목), 라벨 1D 충돌 회피 +
  leader line + 데이터 점 우측/좌측 자동 결정, 축 라벨(xLabel/yLabel) 슬롯.
- **`remotion/src/charts/cat/SlopeChart.tsx`**(신규) — 좌·우 라벨 각각 충돌 회피, 좌/우
  세로 가이드, 라벨 = 시리즈명(컬러) + 값(보조 컬러), 도착 마커는 도달 시(`prog > 0.97`)
  나타남.
- **`remotion/src/charts/cat/CandleChart.tsx`**(신규) — 양봉/음봉 `accent.positive`/
  `accent.negative`, high-low wick + open-close 박스 grow, x tick 자동 thinning (라벨
  너무 많을 때 균등 분포).

### Changed

- **`remotion/src/ChartView.tsx`** — Bar/Point family(9 종) 디스패치 새 컴포넌트로 라우팅:
  `bar` / `lollipop` / `range_bar` → `BarChartV2(mode=...)`,
  `stacked` / `stacked_bar` → `StackedBarChartV2`,
  `waterfall` → `WaterfallV2`,
  `scatter` → `PointChartV2`, `bubble` → `PointChartV2(bubble)`,
  `slope` → `SlopeChartV2`, `candle` → `CandleChartV2`,
  `choropleth` → `BarChartV2`(country_code/value 매핑).
  legacy `BarChart` / `StackedBar` / `Waterfall` / `PointChart` / `Candle` / `Slope` /
  `ChoroplethBars` 제거(~200 LOC).
- 남은 legacy: `Donut` / `Gantt` / `Heatmap` / `Network` / `Sankey` (Phase 3 에서
  `d3-force` / `d3-sankey` / `world-atlas` 로 정통 재구현 예정).

### MVP Professional Bar 진행 (누적)

- ✅ 1. 차트 토큰 일관성 — XY 6 종 + Bar/Point family 9 종 = 15/21 (71%) 가 design.ts 토큰
  100% 사용. 남은 6 종(donut/gantt/heatmap/network/sankey/choropleth 의 실 지도 버전)은
  Phase 3.
- ✅ 7. Material easing 만 사용 — XY + cat family 15 종 모두 적용.
- ✅ 8. Stagger — 카테고리 stagger(staggerToken), 시리즈 stagger(stacked) 모두 적용.
- ✅ 9. Draw progression — 막대 grow / 점 pop / 슬로프 sweep / 캔들 박스 grow.
- ✅ 11. Direct labeling — 모든 cat family 의 값 라벨 직접 표시.

---

## [v0.31.0] — 2026-06-05

**Phase 1 — XY family 정통 재구현 (영상미 C0)**. line / area / stacked_area /
small_multiples / dual_line / forecast 를 d3-scale + d3-shape + ChartFrame + Axis +
Callout + ReferenceRegion + 자체 1D 라벨 충돌 회피로 다시. 차트 family 첫 본체 진입.

### Added

- **`remotion/src/charts/util.ts`**(신규) — XY 공용 헬퍼.
  - `buildXScale(xs, range)` — **time-aware**: ISO(`%Y-%m-%d` / `%Y-%m` / `%Y/%m/%d` / `%Y`)
    면 d3 `scaleTime` + 시간 위계 자동 포맷(연/월/일), 아니면 `scalePoint` 폴백.
  - `buildYScale(values, range, opts)` — **nice ticks** (Robert Wickham nice-numbers
    알고리즘), `includeZero`, unit 자동 접미사(`k` for 10k+).
  - `easeDecelerate` / `easeStandard` — Material easing 의 결정론적 t→y 함수(Newton 2-step).
  - `useDrawProgress(delaySec, durMs)` — Remotion frame → 0–1 progress + Material easing.
  - `useSeriesProgress(i, total, ...)` — stagger 적용 시리즈별 진입.
  - `layoutEndpointLabels` — 자체 1D 충돌 회피(labella 의존 회피, 결정론). 양방향 패스 +
    경계 클램프.
  - `groupBySeries` / `unionXs` — flat rows → 시리즈 그룹화 + x 합집합(순서 보존).
- **`remotion/src/charts/xy/XYChart.tsx`**(신규) — line / area / stacked_area /
  small_multiples 통합 컴포넌트.
  - d3-shape `line()` + `area()` + `curveMonotoneX`.
  - **Draw progression**: x-방향 `clipPath` wipe + Material decelerate easing.
  - **Direct labeling**: 끝점 마커 + leader line + 시리즈명 + 값(75% progress 후 등장).
  - 끝점 라벨 1D 충돌 회피(`layoutEndpointLabels`).
  - **Subject + Note + Connector 콜아웃**(`Callout`): `event` 필드 있으면 자동 노출.
  - **ReferenceRegion**: 위기 구간(`referenceRegions` 옵션) 음영 + 라벨.
  - Surface plate (배경 카드) + Pretendard + design.ts 토큰만.
- **`remotion/src/charts/xy/DualLineChart.tsx`**(신규) — 좌/우 독립 y 스케일, 우 시리즈
  점선(`dasharray`), 시리즈명 색-매칭 헤더, 끝점 마커.
- **`remotion/src/charts/xy/ForecastChart.tsx`**(신규) — 실측(실선) + 전망(점선 mid +
  band area) + ReferenceRegion 으로 전망 구간 시각 분리 + "실측"/"전망" 끝점 라벨.

### Changed

- **`remotion/src/ChartView.tsx`** — XY family(6 종) 디스패치를 새 컴포넌트로 라우팅:
  `line` / `area` / `stacked_area` / `small_multiples` → `XYChart`,
  `dual_line` → `DualLineChart`, `forecast` → `ForecastChart`.
  legacy `LineLike` / `ForecastChart` / `DualLine` 코드 제거(~110 LOC).
  bar / stacked / waterfall / scatter 등 나머지 14 종은 legacy 렌더러 유지(Phase 2+ 교체).

### MVP Professional Bar 진행

- ✅ 8. Stagger 헬퍼 도입(`stagger(n)`, XY 시리즈별 진입).
- ✅ 9. Draw progression(x-wipe + Material decelerate).
- ✅ 10. Subject+Note+Connector 콜아웃(XY 의 event 필드).
- ✅ 11. Direct labeling(끝점 시리즈명+값, 1D 충돌 회피).
- ✅ 12. ReferenceRegion 동작(forecast 전망 구간 + XY 옵션).
- 부분 ✅ 1. 토큰 일관성(XY 만 design.ts 100%, 나머지 family 는 Phase 2+ 에 이관).

---

## [v0.30.0] — 2026-06-05

**Phase 0 — 프로페셔널 재빌드 디자인 시스템 토대 (영상미 C0)**. 차트·자막·타이포의 전면
재빌드 사이클 (v0.30.0 → v0.36.0) 출발. 본 PATCH 는 **차트 본체는 한 줄도 안 건드린다** —
토큰·공용 컴포넌트·외부 리서치 통합·합격 기준만 박는다. 사용자 평가 "전반적으로 너무 구려"
에 대한 구조적 대응.

### Added

- **`docs/PROFESSIONAL_REBUILD_PLAN.md`**(신규) — 5 트랙 외부 리서치 통합(차트 애니메이션 /
  한글 타이포 / 시각화 이론 / 다크 컬러 / 날리지식·Vox 미학) + 현 코드 자기 평가(평균 갭
  -5.9) + Phase 0 → 5+E 실행 계획 + **MVP Professional Bar 20 합격 기준**. 본 사이클의 SSOT.
- **`remotion/src/design.ts`**(신규) — 디자인 시스템 토큰 SSOT. **Color**(Material Dark
  베이스 `#121214` + Okabe-Ito 색맹 안전 시리즈 7 색 + 의미 라벨 4 색 + Aurora 4 색),
  **Typography**(Pretendard Variable 폰트 스택, 1.618 황금비 size scale 14→18→28→46→76→124,
  weight 400–900, lineHeight tight/normal/relaxed/loose, **한글 `word-break: keep-all` +
  `overflow-wrap: anywhere`**, Netflix Korean 자막 표준 16자/2줄/17CPS), **Motion**(Material
  easing decelerate `[0,0,0.2,1]` / standard / accelerate, duration 150/300/400/600/900ms,
  `stagger(n)` 헬퍼), **Spacing**(8 grid + safe area + chart 영역 + radius + stroke).
  헬퍼 `msToFrames(ms, fps)`, `seriesColor(i)`, `labelColor(key)`.
- **`remotion/src/components/ChartFrame.tsx`**(신규) — 모든 차트 family 공용 외곽: kicker /
  title / subtitle / source 슬롯. 빈 슬롯은 공간 차지 안 함. design.ts 토큰만 사용.
- **`remotion/src/components/Axis.tsx`**(신규) — SVG group x/y 축 + grid + tick + 라벨.
  d3-axis 의존 회피(결정론·경량). 호출자가 미리 계산한 tick 배열을 전달.
- **`remotion/src/components/Callout.tsx`**(신규) — D3-annotation Subject + Note + Connector
  패턴. 진입 모션 트랙(subject grow 300ms → connector draw 300ms → note fade 200ms),
  Bezier 곡선 connector, foreignObject 로 한글 줄바꿈 안전, design.ts 토큰만.
- **`remotion/src/components/ReferenceRegion.tsx`**(신규) — 위기 구간 / 이벤트 영역 표시.
  회색 알파 fill + 점선 경계 + 라벨(top/inside/bottom). 시계열 차트 맥락 강조.
- **npm 의존성 추가** — `d3-scale` `d3-shape` `d3-time-format` `d3-array`
  `d3-scale-chromatic` `labella` + 각 `@types/*`. Phase 1 XY family 정통 재구현용.

### Changed

- 본 PATCH 는 **차트/자막/지도 본체 동작 변경 없음**(기존 211/328 회귀 모두 그대로).

---

## [v0.29.0] — 2026-05-25

**Visual Skin 1차 — Aurora Glass Card (영상미 C0, ChatGPT 피드백 반영)**. 카드 표면 처리로
"다크 럭셔리 OSINT 브리핑" 미감. 절제 원칙(본체 차분, 강조 레이어만 럭셔리).

### Added

- **`remotion/src/AuroraGlassCard.tsx`**(신규) — 다크 glassmorphism fill + 얇은 오로라
  그라데이션 보더(블루·바이올렛·마젠타·샴페인) + 느린 엣지 하이라이트(frame 구동 회전 →
  프레임 정확) + soft bloom. CSS 키프레임 미사용(결정론).
- **`remotion/src/Briefing.tsx`** — 브랜드 태그 / `<추론>` 배지(색 점+텍스트) / 하단 자막
  바를 AuroraGlassCard 로 교체. **차트·지도 본체는 그대로**(축·선·격자 glow 금지 — 절제).

### Notes

- 후속(스테이징): 이벤트 콜아웃 카드(차트 내), title glow panel, 스타일 프리셋(surface 토큰),
  scene 별 surfaceEffect, 프롬프트 규칙, 스타일 가이드 문서.
- 절제 가드: 화면당 글로우 카드 3~4개, 느린 sweep, pulsing 금지(과하면 사이버펑크화).

## [v0.28.0] — 2026-05-25

**forced-alignment 스캐폴드 — 자막 음성 정밀 싱크(교체형 백엔드 + 비례 폴백)**.

### Added

- **`orchestrator/subtitle_align.py`** — `align_cues`: 음성에 맞춰 자막 큐 [start,dur] 정밀화.
  백엔드 env `OSINT_ALIGN_BACKEND`(none/whisper). whisper 는 단어 타임스탬프→큐 매핑(모델+실제
  음성 필요 = 사용자 머신). 실패/미설정/무음은 모두 None(비례 폴백) — graceful.
- **`orchestrator/render_io.py`** — `build_and_persist_render_props` 가 백엔드 설정 시 scene
  자막 큐를 정렬로 교체(opt-in). 본 클라우드는 stub 무음이라 기본 no-op(기존 비례 큐 유지).
- **`tests/test_subtitle_align.py`** — 백엔드 선택 + 폴백(None) 경로 5종(328 통과).

### Notes

- 정밀 정렬은 사용자 Windows(실제 음성 + whisper)에서만 동작. 클라우드는 항상 폴백.

## [v0.27.0] — 2026-05-25

**전 차트 family 영상용 렌더러 + 라벨 다듬기 (영상미 C0)**. line 에 이어 21종 전 타입을
Remotion 에서 데이터로 cinematic 재렌더.

### Added

- **`remotion/src/ChartView.tsx`** — family 렌더러 전면 확장: XY(line/area/stacked_area/
  small_multiples), dual_line, forecast(전망 band), bar/lollipop/range_bar, stacked(_bar),
  waterfall, scatter/bubble, candle, donut, gantt, slope, heatmap, network(원형), sankey(간이),
  choropleth(간이 막대). 공용 draw-on 애니 + 팔레트 + 라벨 clamp/anchor(경계 클립 방지).
- **`orchestrator/render_io.py`** — `SUPPORTED_CHART_TYPES` 전 타입으로 확장.
- 실물 호르무즈 보고서로 network/gantt/bubble/line 프레임 검증(안 깨짐).

### Notes

- 거친 부분(버블/라벨 미세 겹침·일부 클립)은 의도적으로 남김 — 사용자가 계속 다듬는 전제.
- network/sankey/choropleth 는 간이 버전(원형/2열/막대) — 추후 고도화 여지.

## [v0.26.0] — 2026-05-25

**영상용 차트 family 렌더러 — line (영상미 C0 첫 구현)**. 정적 SVG 이식이 아니라, 차트
데이터로 우리가 cinematic 재렌더(좌→우 draw-on + event 강조). 실물 호르무즈 보고서의 브렌트
유가 라인차트로 검증.

### Added

- **`schemas/models.py`** — `RenderChart`(type/title/data/unit) + `RenderSceneProps.chartData`.
- **`orchestrator/render_io.py`** — claim_refs 에 지원 차트 id 가 있으면 scene 에 chartData
  attach. `SUPPORTED_CHART_TYPES={line}`(확장 중). unit 은 provenance.sources 에서.
- **`remotion/src/ChartView.tsx`**(신규) — line family: 데이터 스케일 + 좌→우 draw-on
  애니(stroke-dashoffset) + event 마커/라벨 + 축. type 별 디스패치(미지원→null=텍스트 폴백).
- **`remotion/src/Briefing.tsx`** — 중앙 비주얼 우선순위 map>chart>text, caption 은 제목 축소.
- **`tests/test_render_flow.py`** — 차트 attach/미지원 제외 테스트(323 통과).

### Notes

- 알려진 다듬기: 끝점 event 라벨이 SVG 경계서 잘림 / 라벨 겹침 — 후속 미세조정.
- 다음 family: bar/bubble/waterfall/gantt → 그다음 복잡 타입(network 등).

## [v0.25.0] — 2026-05-25

**최우선 가치 "영상미(Cinematic Quality First)" 를 최상위 규칙으로 박음 (사용자 결정)**.
정적 보고서 이식이 아니라, 데이터·맥락을 이해해 영상용으로 재렌더하는 것을 osint_generator
의 제1 미덕으로 확정.

### Changed

- **`CLAUDE.md`** — **C0. 최우선 가치 — 영상미** 신설(C1 위, 최상위). 선택지가 갈리면 정적·쉬운
  길보다 영상미 높은 길을 택한다(쫓는 비용 감수). 차트는 정적 SVG 이식이 아니라 데이터로
  cinematic 재렌더, 외부 SVG 는 렌더러 없는 복잡 타입 폴백. 경계: 사실 정확성·검증(G4)·권리(C9)
  위에서만.
- **`GOAL.md`** — **G0. 최우선 미덕 — 영상미** 신설(G1 위). 비주얼은 영상에 적합하게 생성/재렌더.
- **방침 전환**: 이전의 "전 타입 SVG passthrough 로 안 쫓기"(v0.18~0.20 논의)는 폐기. 전반
  구도를 모른 채 내린 결정이었음(사용자). agents_reviewer 계약의 A안(consumer 가 데이터로
  재렌더)과도 정합 — 분쟁이 아니라 수렴.
- **`HANDOFF.md` / `docs/05`** — 차트 보류 항목을 "우리가 데이터로 cinematic 재렌더(family
  렌더러) + 복잡 타입만 SVG 폴백" 으로 재정의.

---

## [v0.24.0] — 2026-05-25

**관대한 수신자(tolerant reader) — 진화하는 보고서 수용 + v5.5.2 timeline**. bundle 수신
모델을 `extra="forbid"` → `extra="ignore"` 로 전환. agents_reviewer 보고서 양식이
진화(새 top-level 블록·섹션 필드)해도 깨지지 않는다.

### Fixed / Changed

- **`schemas/models.py`** — bundle 모델 공용 베이스 `_BundleModel(extra="ignore")` 도입,
  모든 Bundle* + `ReportBundle` 이 상속/적용. 모르는 필드는 무시(거부 X), 선언 필드는
  계속 검증(타입·enum·필수·참조무결성). **v5.5.2 가 추가한 `timeline` 블록 수용**
  (`BundleTimeline`/`BundleTimelinePoint`, 현재 보관만 — 영상 소비는 추후 타임라인 비주얼).
- **`orchestrator/bundle_io.py`** — `load_report_bundle` 이 모델 미정의 top-level 필드를
  로그(warning)로 surface(무시하되 인지 — 새 블록 추가를 알아채도록).
- **근거**: 직전 `extra="forbid"` 가 v5.5.2 의 `timeline` 하나에 번들 전체를 거부 → 계약 §1
  "additive=schema_version 무증분" 과 모순. tolerant reader 가 §1 과 정합.
- **`tests/`** — extra-rejected 테스트를 tolerant(무시) 테스트로 교체 + timeline/섹션
  미지필드 수용 테스트. 321 통과.

### Notes

- 계약 §1 문구(consumer `extra="forbid"`)는 "consumer=tolerant reader"로 갱신 권고
  (agents_reviewer 정본 doc). 우리 consumer 가 관대해도 producer 검증은 그쪽 schemas.py 가 유지.

---

## [v0.23.1] — 2026-05-25

**보류 작업 추적 (docs-only)**. 사용자가 순서를 미룬 작업(forced-alignment, ③ 자동 캐치,
차트 SVG 대기)을 HANDOFF 상단에 박아 세션 재개 시 상기되도록.

### Changed

- **`HANDOFF.md`** — 상단에 "⏳ 다음 할 일 (사용자 보류)" 블록 추가 + last_synced_with
  v0.3.3→v0.23.1. 세션이 바뀌어도(컨테이너 재생성) 보류 작업이 유실되지 않게 영속화.

---

## [v0.23.0] — 2026-05-25

**② 지도 비주얼 (Phase B) — bundle map 을 d3-geo 로 재렌더**. geo 번들의 지도(마커·arc)를
영상 중앙에 그린다. 비주얼↔scene 배치는 claim_refs 로 보존(차트/지도를 claim 으로 합성한
결과)되어, map id 를 참조하는 scene 에만 지도가 붙는다.

### Added

- **`schemas/models.py`** — `RenderMap`/`RenderMapMarker`/`RenderMapArc` +
  `RenderSceneProps.mapData`. (additive)
- **`orchestrator/bundle_io.py`** — `persist_report_bundle`/`load_persisted_bundle`
  (받은 bundle 사본을 `04_research/report_bundle.json` 으로). import-bundle 이 영속화.
- **`orchestrator/render_io.py`** — bundle.map → RenderMap 변환 + scene 의 claim_refs 에
  map id 가 있으면 `mapData` attach.
- **`remotion/src/MapView.tsx`** (신규) — d3-geo(geoMercator) + world-atlas(npm, 런타임
  fetch 없음) 베이스맵 + 마커(라벨/highlight) + arc(곡선·강조). markers fitExtent 투영.
- **`remotion/src/Briefing.tsx`** — mapData 있으면 중앙에 지도, caption 은 제목으로 축소.
- **`remotion/`** — d3-geo / topojson-client / world-atlas 의존성 추가.

### Notes

- 차트(line/bubble/gantt 등)는 agents_reviewer 의 `prerendered_svg`(v5.5.0 엔 null) 도착 후
  SVG passthrough 로. 지도는 타입이 하나라 재렌더가 합리적이라 먼저 구현.

---

## [v0.22.1] — 2026-05-25

**ScriptWorker LLM 타임아웃 상향(600→1200초)**. 5분 대본 1-shot 생성에서 claude think
시간이 600초를 넘겨 timeout 실패하는 사례 관측(실측 526초 성공 / 600초 timeout). 긴 생성
전용으로 한도를 올림(다른 worker 는 600초 유지).

### Fixed

- **`workers/script_worker.py`** — `invoke_timeout_sec` ClassVar=1200 override.

---

## [v0.22.0] — 2026-05-25

**① 화면 상단 출처 텍스트 배선**. bundle 출처를 source_registry 로 영속화하고 scene 의
claim→evidence→출처로 해소해 화면 상단에 표기.

### Added

- **`orchestrator/bundle_io.py`** — `bundle_to_source_registry`: bundle top-level
  sources + 차트/지도 `provenance.sources`(예: mkt-1=YAHOO)를 `SourceRegistry` 로 수집
  (source_id dedup, top-level 우선).
- **`orchestrator/bundle_service.py`** — import-bundle 이 `02_sources/source_registry.json`
  도 영속화(선택적, 실패해도 전이 무방).
- **`orchestrator/render_io.py`** — scene 의 segment claim_refs → dossier claim →
  evidence.source_id → registry 표기명(publisher/provider/도메인)으로 `source` 해소
  (해소 불가 시 ""; v5.5.0 의 sparse 한 claim-출처 연결에서 과잉 귀속 방지). 최대 3개.
- **`orchestrator/source_registry_io.py`** — `load_source_registry` 추가.
- **`tests/`** — bundle→registry 수집 + scene 출처 해소 테스트(317 통과).

### Notes

- v5.5.0 은 claim-출처 연결이 sparse(차트 데이터 출처 위주) → fin(시장데이터)은 출처 표기,
  geo(서술 위주)는 대부분 빈 출처(과잉 귀속 방지). 정밀화는 claim-출처 연결 강화(v5.6+)와 함께.

---

## [v0.21.0] — 2026-05-25

**순차 자막 — 통문단 대신 줄 단위로**. 자막 바가 나레이션 전체를 한 번에 띄우던 것을
문장/줄 단위 큐로 쪼개 순차 표시(자막다운 표시).

### Added

- **`schemas/models.py`** — `SubtitleCue`(text/startSec/durationSec) 모델 +
  `RenderSceneProps.subtitleCues`. additive(schema_version 1).
- **`orchestrator/render_io.py`** — `split_subtitle_cues`: narration 을 문장 단위로 나누고
  긴 문장은 줄 길이(42자)로 재분할, scene 길이를 글자수 비례로 배분(TTS 타임스탬프 부재 시
  표준 근사). 각 scene 의 `subtitleCues` 채움.
- **`remotion/src/Briefing.tsx`** — 현재 프레임 시각에 해당하는 큐만 자막 바에 표시(짧은
  페이드인). 큐 없으면 narration 전체 폴백.
- **`tests/test_render_flow.py`** — 큐 분할/타이밍/긴문장 줄바꿈 테스트(314 통과). 실물 geo
  번들로 같은 scene 두 시각 렌더 → 자막 줄 단위 전환 확인.

---

## [v0.20.1] — 2026-05-25

**LLM-AP-005 — bundle 경로 대본 생성 실패 수정**. geo 실물 번들 풀 seam 에서 발견:
거대 입력이 ScriptWorker(LLM) 출력을 쪼개고 형식을 깨 parse_failed.

### Fixed

- **`orchestrator/bundle_io.py`** — `_narrative_summary` 가 섹션당 prose 를 문장 경계에서
  발췌(`_SECTION_PROSE_CAP=320`)해 '구조적 개요'만 summary 로 전달(입력 비대화 방지).
  geo summary 4,833 → 2,462자. 살은 ScriptWorker 가 붙인다(5분 대본은 응축).
- **`workers/base_llm_worker.py`** — `_extract_json_block` 견고화: 서두 prose + 본문 중간
  ```json 블록 / 첫 균형 {...} 객체(문자열 내 중괄호·이스케이프 고려) 추출. 모델이 형식
  지시를 어기고 펜스·서두를 붙여도 도메인 JSON 회수.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md`** — LLM-AP-005 기록(C6).
- **`tests/test_base_llm_worker.py`** — 서두+펜스/균형객체 추출 테스트.

---

## [v0.20.0] — 2026-05-25

**실물 v5.5.0 emit 연동 — §11 갭 수정 + 라벨 척추 provenance 합성**. agents_reviewer
실제 번들 2건(fin/geo)으로 수신 모델 대조 + 어댑터 강화.

### Fixed

- **`schemas/models.py`** — `BundleMapArc.highlight` 필드 추가. 실물 geo 번들의 map arc 가
  `highlight` 를 emit 하는데 모델에 없어 거부되던 §11 갭 수정(extra=forbid). additive.

### Added

- **`orchestrator/bundle_io.py`** — `claims=[]`(v5.5.0 현실)일 때 라벨 척추를
  charts/map `provenance.verification` + contradictions 에서 합성: 차트→claim
  (measured→`<확인>`, inference→`<추론>`), map→claim, contradictions→`disputed`(`<반박됨>`).
  섹션 prose 는 `summary` 로 실어 ScriptWorker 가 발화형 변환(계약 §6). bundle.claims 가
  차 있으면(v5.6+) 직매핑.
- **`tests/test_bundle_flow.py`** — v5.5.0 빈 claims 합성 + arc.highlight 수용 4종(309 통과).
- 실물 검증: fin/geo 번들이 우리 v0.20.0 수신 모델로 검증 통과(arc 수정 후), 어댑터가
  라벨 보유 claim(fin 5 / geo 6) + 서사 summary(4천여 자) 생성 확인.

---

## [v0.19.0] — 2026-05-25

**영상 문법 재설계 — key takeaway 중앙 + 전체 나레이션 자막 바 + 인용 강조**. 글자 도배
슬라이드에서 "화면엔 핵심만, 음성+자막" 형태로(레퍼런스 브리핑 스타일).

### Added

- **`remotion/src/Briefing.tsx`** — 레이아웃 재설계: 중앙 key takeaway(caption) 크게,
  하단 **자막 바**에 전체 narration, 좌상단 브랜드, 상단 출처, 우상단 검증 라벨 배지.
  인용(`isQuote`)은 테마 강조색 + 인용부호(`" "`/`「 」`) + 좌측 강조 보더로 명확히 구분.
- **`schemas/models.py`** — `RenderSceneProps`에 `source`(상단 출처 텍스트) + `isQuote`
  (인용 표기 신호) 필드 추가(additive, schema_version 1 유지).
- **`orchestrator/render_io.py`** — caption 의 인용부호 휴리스틱으로 `isQuote` 자동 set
  (정식 인용 마킹은 ScriptWorker/bundle pull_quote 도입 시 교체).
- **`tests/test_render_flow.py`** — isQuote 휴리스틱 테스트(305 통과). still 프레임 2종
  (정상/인용)으로 레이아웃 실물 검증.

### Notes

- `source` 텍스트 배선(소스체인/bundle sources)은 다음 단계(bundle 어댑터 강화)와 함께.

---

## [v0.18.1] — 2026-05-25

**외부 계약 v1 draft 보정 동기화 — map.id + section.map_ref resolve**. seam 에서 보고한
`map_ref` 미해소 갭을 agents_reviewer 가 "단일 map + id" 로 확정(정본 계약 보정) → 우리
수신 mirror 반영.

### Changed

- **`schemas/models.py`** — `BundleMap.id` 필드 추가. `ReportBundle` model_validator 에
  `section.map_ref → map.id` resolve 검증 추가(보고서당 단일 map, 다중 지도 회피).
- **`tests/test_bundle_flow.py`** — map_ref resolve / dangling map_ref 거부 테스트(304 통과).
- 계약 schema_version 무증분(draft 보정, 양측 합의).

---

## [v0.18.0] — 2026-05-25

**외부 연동: agents_reviewer `report_bundle` 수신 (인터페이스 계약 v1, 텍스트 슬라이드 seam)**.
agents_reviewer 의 보고서 분석 데이터를 우리 `research_dossier` 로 흡수하는 새 intake 경로
(`build-research-dossier` LLM 단계의 드롭인 대체). 이번 단계는 차트 없이 컨테이너·매핑을
검증하는 ② seam.

### Added

- **`schemas/models.py`** — `ReportBundle` 수신 모델 + 하위 모델(Producer/Report/Theme/
  Provenance/Chart/Map·Marker·Arc·Legend/Section/Evidence/Claim/Signal/Contradiction/
  Source/Confidence). 계약 v1 의 소비자측 미러. `extra="forbid"` fail-closed +
  `model_validator` 로 bundle 내 id unique + chart_refs/claim_refs resolve 강제(§8).
  차트 `data` 모양 SSOT 는 agents_reviewer `schemas.py` 라 `Any` 로 통과(§9, 이중 SSOT 회피).
- **`orchestrator/bundle_io.py`** — `load_report_bundle`(검증 로드) +
  `bundle_to_research_dossier`(순수 변환: claims→ResearchClaim 라벨 무손실,
  quote_or_data→quote, signals→open_questions).
- **`orchestrator/bundle_service.py`** — `import_report_bundle` 오케스트레이션
  (source_completeness_review → research_in_progress, research_service 동형).
- **`import-bundle {pid} --file <path>`** CLI 서브커맨드.
- **`tests/test_bundle_flow.py`** — 모델 검증 + 어댑터 14종 (302 통과).

### Changed

- 라벨 척추: bundle `provenance.verification`(=`ResearchClaimStatus`) 단일 축에서 화면 라벨
  파생, 그대로 신뢰(재검증 floor 없음 — 사용자 결정). `model_forecast→inferred` 매핑(producer).

---

## [v0.17.0] — 2026-05-24

**대본 규칙: 4~6분 길이 + 후속 안내 마무리**. 브리핑 포맷 규칙을 script_worker 에 적용.

### Changed

- **`workers/script_worker.py`** — system prompt 규칙 추가:
  - 영상 길이를 **4~6분(240~360초)** 으로 제한(total_est_duration_sec 가 그 범위). manifest
    target_duration_min(3~20)과 별개의 스크립트 포맷 운영 목표.
  - **마지막 세그먼트는 항상 '후속 안내' 마무리**("앞으로도 지속 확인하고 새 사실은 이어서
    전하겠다" 뉘앙스)로 끝내되 매번 표현을 다르게. label=null, claim_refs 비움 허용.
- 본 규칙은 이후 `build-script` 생성분부터 적용(기존 samples 대본은 규칙 전 스냅샷).

---

## [v0.16.0] — 2026-05-24

**TTS 발음 안전 — 생성 차단 + 자동 린터 (재발 방지)**. ElevenLabs 합성을 들어보니
나레이션의 약어(USGS/CWA/OSINT 등)를 영어식으로 읽어 "AI 티"가 났다. 사용자가 제공한
실무 표기-해석 오류 리스트(50+)를 두 갈래로 흡수.

### Added

- **`orchestrator/tts_lint.py`** — `lint_narration` 순수 린터. narration 의 TTS-위험
  표기(로마자 약어 / 시각 콜론 / 날짜 점·하이픈 / 화살표 / 범위 / 슬래시 / 천단위 콤마 /
  숫자+영문단위 / 버전 / URL·이메일 / 파일경로 / 기호)를 카테고리별 탐지. 한국어 숫자·
  단위는 정상. (한글이 유니코드 \w 라 \b 대신 숫자 룩어라운드.)
- **`orchestrator/main.py`** — `lint-script {pid} [--strict]` CLI + `build-script` 가
  생성 직후 TTS-lint 요약 자동 출력.
- **`tests/test_tts_lint.py`** — 카테고리별 탐지 + 깨끗한 한국어 통과 (288 통과).

### Changed

- **`workers/script_worker.py`** — system prompt "TTS 발음 안전 규칙" 확장(약어→한국어,
  날짜·시각·범위·슬래시·단위·버전·URL·기호 발화형, 영문/기호는 caption 에만).
- **`docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md`** — 부록 A: 사용자 실무 리스트 정리.
- **`samples/hualien2024/`** — TTS-안전 규칙으로 대본·scene 재생성(약어 제거).

---

## [v0.15.7] — 2026-05-24

**build-audio 세그먼트 진행 로그**. 백엔드 합성은 건당 수 초(외부 API)라 16개를 도는
동안 출력이 없어 "멈춘 것처럼" 보이는 혼동(실제 사용자). 건별 `[i/n] ... 합성/완료` 로그.

### Changed

- **`orchestrator/audio_service.py`** — build_audio 가 세그먼트별 진행을 stdout 으로 출력.

---

## [v0.15.6] — 2026-05-24

**ElevenLabs 무료 플랜용 mp3 기본 출력**. 권한·목소리 다 통과한 뒤에도 `500
service_unavailable` — 원인은 요청한 `pcm_16000` 출력이 무료 플랜에서 막힘(무료는 mp3만).
사용자 실제 무료 키에서 발견(재현 일관).

### Fixed

- **`workers/tts_backends.py`** — ElevenLabs 기본 출력 `mp3_44100_128`(무료 OK).
  `ELEVENLABS_OUTPUT_FORMAT` 로 변경 가능(유료/정밀 길이는 `pcm_16000`→wav). 백엔드별
  `file_ext` 추가, mp3 는 CBR 비트레이트로 길이 추정(`_mp3_duration_sec`).
- **`orchestrator/audio_service.py`** — 출력 파일 확장자를 백엔드 `file_ext` 로 결정
  (mp3/wav). Remotion `<Audio>` 는 둘 다 재생.
- **`tests/test_audio_flow.py`** — mp3 기본 출력 단언 (276 통과).

---

## [v0.15.5] — 2026-05-24

**ElevenLabs 기본 voice 폴백 (voices_read 권한 불요)**. TTS 권한만 있는 키로
`build-audio --backend elevenlabs` 시 `401 missing_permissions voices_read` 로 실패.
목소리 자동선택을 위해 `GET /v1/voices` 를 호출했는데 그게 voices_read 권한을 요구.
사용자 실제 키에서 발견.

### Fixed

- **`workers/tts_backends.py`** — voice 미지정 시 `/v1/voices` 조회 대신 기본 premade
  voice(`21m00Tcm4TlvDq8ikWAM`, Rachel)로 폴백 → **text_to_speech 권한만으로 동작**.
  voice 인자 > ELEVENLABS_VOICE_ID > 기본. 본인 목소리/클론은 ELEVENLABS_VOICE_ID 지정.
- **`tests/test_audio_flow.py`** — 기본 voice 사용 시 GET 미호출 + POST 가 기본 voice id,
  ELEVENLABS_VOICE_ID override 검증 (276 통과).

---

## [v0.15.4] — 2026-05-24

**Windows npx 실행 버그 수정 (RENDER-AP-002)**. Windows 에서 `render-debug` 가
`npx/node 를 찾을 수 없습니다` 로 실패 — Node 는 설치돼 있고 셸에선 `npx` 동작하나,
Python subprocess 가 `npx.cmd`(배치)를 PATHEXT 없이 못 찾음. 사용자 실제 Windows 발견.

### Fixed

- **`orchestrator/main.py`** — `shutil.which("npx")` 로 실제 경로(Windows 면 npx.cmd)
  해석 후, 배치면 `cmd /c` 경유 실행. POSIX 영향 없음.
- **`docs/ANTIPATTERNS/RENDER_ANTIPATTERNS.md`** — RENDER-AP-002.

---

## [v0.15.3] — 2026-05-24

**TTS env 값 공백 strip (Windows `set` 트레일링 스페이스)**. ElevenLabs 키에 뒤 공백이
붙어 `httpx ... Illegal header value` 로 실패. Windows `set VAR=값 ` 이 뒤 공백을 값에
포함시킨 게 원인 (실제 사용자 환경).

### Fixed

- **`workers/tts_backends.py`** — ElevenLabs(api_key/voice/base_url/model_id) 및
  Voicebox(url/profile/lang) 환경변수 값을 `.strip()`. 트레일링 공백/탭에 안 깨짐.
- **`tests/test_audio_flow.py`** — 뒤 공백 키 strip 회귀 테스트 (275 통과).

---

## [v0.15.2] — 2026-05-24

**requirements.txt cp949 디코드 버그 수정 (Windows)**. 한국어 Windows 에서
`pip install -r requirements.txt` 가 `UnicodeDecodeError: 'cp949' ... 0xe2` 로 실패.
pip 가 requirements 파일을 로케일 코덱(cp949)으로 읽는데 파일에 한글 주석 + en-dash
같은 UTF-8 문자가 있어서였다. 사용자의 실제 Windows 실행에서 발견.

### Fixed

- **`requirements.txt`** — 주석을 ASCII(영문)로, en-dash→hyphen. 상단에 "ASCII-only
  유지" 주석 추가(재발 방지). 패키지 목록은 동일.
- 워크어라운드(구버전 받은 경우): `set PYTHONUTF8=1` 후 pip install.

---

## [v0.15.1] — 2026-05-24

**로컬 테스트 샘플 + 가이드**. 클라우드 세션에서 만든 hualien2024 산출물은 그 세션
안에만 있어, 사용자가 본인 PC 에서 대본+음성 영상을 바로 테스트할 수 있도록 동일
산출물을 커밋.

### Added

- **`samples/hualien2024/`** — 화롄 지진 브리핑의 project_manifest / research_dossier /
  full_script / scene_manifest JSON (실제 claude run 산출물). `projects/` 로 복사하면
  research/script 재생성 없이 build-audio + render-debug 만으로 음성+영상 테스트 가능.
- **`docs/RUN_LOCAL.md`** — ElevenLabs 키만으로 음성 입히고 렌더하는 최소 절차
  (복사 → build-audio --backend elevenlabs → render-debug). 백엔드 교체 안내 포함.

---

## [v0.15.0] — 2026-05-24

**ElevenLabs 백엔드 "키만 있으면 동작" 보강 + 통합 검증**. 사용자가 default-voice 경로로
ElevenLabs 선택. voice ID 안 찾아도 되게 자동 선택 추가.

### Changed

- **`workers/tts_backends.py`** — `ElevenLabsTTSBackend`: 목소리 미지정 시
  `GET /v1/voices` 로 계정 첫 목소리 자동 선택(voice > ELEVENLABS_VOICE_ID > auto).
  `ELEVENLABS_BASE_URL`(기본 api.elevenlabs.io)·`ELEVENLABS_MODEL_ID`(기본
  eleven_multilingual_v2, 한국어) 환경변수화. pcm_16000 → wav(길이 측정) 유지.

### Tests

- **`tests/test_audio_flow.py`** — `_MockElevenLabsServer`(GET /v1/voices + POST
  /v1/text-to-speech/{id}). 키만으로 자동 목소리 선택→합성→audio_manifest, 요청이
  xi-api-key 헤더 + output_format=pcm_16000 계약을 따름을 실 소켓 검증. 키 누락 시
  CLI exit 1 (274 통과).

---

## [v0.14.1] — 2026-05-24

**Voicebox 백엔드 파이프라인 통합 검증**. 실제 음성 합성(Voicebox+GPU+가중치)은 이
환경에서 불가하지만, **우리 통합 쪽**(HTTP 어댑터 → audio_manifest)이 도는지 Voicebox-모양
mock 서버로 실 소켓 검증.

### Tests

- **`tests/test_audio_flow.py`** — `_MockVoiceboxServer`(스레드 HTTP, `POST /generate` →
  무음 wav). voicebox 백엔드가 (1) audio/wav 응답, (2) JSON+base64 응답 모두 처리해
  audio_manifest+wav 생성, (3) 요청이 문서화된 `{text, profile_id, language}` 계약을
  따름을 검증 (272 통과). 신경망 합성만 Voicebox 몫, 우리 통합은 실제 작동 확인.

---

## [v0.14.0] — 2026-05-24

**Voicebox TTS 백엔드 흡수** (github.com/jamiepine/voicebox, MIT). 로컬 음성복제 앱의
FastAPI 서버를 HTTP 로 호출하는 `voicebox` 백엔드 추가. 무거운 모델/가중치/GPU 는
Voicebox 쪽이고 우리 repo 는 가벼운 어댑터만 유지(벤더링 아님).

### Added

- **`workers/tts_backends.py`** — `VoiceboxTTSBackend` (name="voicebox"). `POST {OSINT_
  VOICEBOX_URL=http://127.0.0.1:17493}/generate {text, profile_id, language}`. profile_id
  는 `OSINT_VOICEBOX_PROFILE`/voice 인자, 언어 `OSINT_VOICEBOX_LANG`(기본 ko). 응답이
  audio bytes/JSON(path·base64) 양쪽을 방어적으로 처리, wav 면 길이 측정·아니면 추정 폴백.
- **`tests/test_audio_flow.py`** — voicebox 등록 + profile 미지정 가드 (269 통과).

### Notes

- **검증은 사용자 로컬에서**: 이 클라우드 환경은 HF(가중치)를 allowlist 차단(`Host not in
  allowlist`)하고 Voicebox 서버도 없어 합성 실검증 불가. 어댑터 + stub 테스트만 검증.
  사용자 머신에서 Voicebox 앱 실행 → `build-audio <pid> --backend voicebox --voice <profile_id>`.
- 사양: Voicebox 는 엔진 선택형 — LuxTTS(~1GB VRAM, CPU 150x)/Kokoro(82M) 는 저사양, Qwen3/
  TADA 는 GPU 권장. 배치 합성이라 저사양도 실용적. GPU/부담은 Voicebox 측, 우리 repo 무관.

---

## [v0.13.0] — 2026-05-24

**수직 슬라이스 V4b: 영상-음성 싱크**. render_props 가 scene + script + audio 의 최종
결합점이 되어, audio_manifest 가 있으면 **실측 음성 길이로 scene 타이밍을 재계산**하고
각 scene 에 나레이션 wav 를 단다. Remotion `Briefing` 이 `<Audio>` + `staticFile` 로
오디오 트랙을 삽입(렌더 시 `--public-dir`=project_dir). 영상이 음성과 동기화됨.

### Added / Changed

- **`schemas/models.py`** — `RenderSceneProps.audioPath` 추가 (Optional).
- **`orchestrator/render_io.py`** — `build_render_props(audio_manifest=...)`: 음성 길이로
  duration/start 재계산 + audioPath. `build_and_persist_render_props` 가 audio_manifest 를
  자동 로드(있으면). 무음 폴백 유지(하위호환).
- **`remotion/src/Briefing.tsx`** — scene 에 `<Audio src={staticFile(audioPath)}>`.
- **`orchestrator/main.py`** — `render-debug` 가 `--public-dir`=project_dir 전달.
- **`tests/test_render_flow.py`** — 오디오 반영/무음 폴백 (267 통과).

### Verified

- hualien2024 재렌더: 14136 프레임(471초, **오디오 길이 기반** 재계산) + 오디오 트랙
  muxing(28.9MB). staticFile/public-dir 정상. 소리는 stub(무음) — 실제 음성은 로컬
  TTS/ElevenLabs 백엔드 필요.

---

## [v0.12.0] — 2026-05-23

**수직 슬라이스 V4: TTS 흡수 (교체 가능 백엔드)**. full_script → 나레이션 wav +
audio_manifest.json. 영상의 무음 한계를 메우기 위한 음성 단계. 백엔드를 갈아끼울 수
있게 설계: `local`(기본·프라이버시·무료) / `elevenlabs`(외부 API·고품질·opt-in) /
`stub`(테스트). 실제 음성 길이를 담아 후속 타이밍 정확도 기반 마련.

### Added

- **`workers/tts_backends.py`** — `TTSBackend` 추상화 + Stub/Local/ElevenLabs 구현 +
  `get_backend`. local 은 `OSINT_TTS_CMD`, elevenlabs 는 `ELEVENLABS_API_KEY`(커밋 금지).
- **`schemas/models.py`** — `AudioManifest` (+ `AudioSegment`).
- **`orchestrator/audio_io.py`** — `08_audio/audio_manifest.json` 영속화/로딩/경로.
- **`orchestrator/audio_service.py`** — `build_audio`: full_script → 세그먼트별 합성 →
  manifest (실측 길이).
- **`orchestrator/main.py`** — `build-audio {pid} [--backend] [--voice]` CLI.
- **`tests/test_audio_flow.py`** — 백엔드 추상화 + stub CLI + 미설정 실패 (265 통과).

### Docs

- **`docs/06` §8.5** — TTS 음성 권리(본인 목소리만, elevenlabs opt-in 트레이드오프).
- docs/03/05/13 동기화.

---

## [v0.11.1] — 2026-05-23

**렌더 환경 대응 (RENDER-AP-001) + 첫 실물 영상**. V3 첫 실 렌더에서 Remotion 의
chromium headless-shell 자동 다운로드가 네트워크 allowlist(403)에 막힘. 머신의
chrome-headless-shell 을 자동탐지해 `--browser-executable` 로 넘기도록 수정 →
hualien2024 영상(13170 프레임, 7분19초, 27MB) 렌더 성공. **topic→영상 파이프라인 첫 완주.**

### Fixed

- **`orchestrator/main.py`** — `render-debug` 에 `_detect_headless_shell()` 자동탐지 +
  `--browser-executable` 플래그 + `OSINT_HEADLESS_SHELL` 환경변수 override. full chrome
  가 아닌 chrome-headless-shell 만 채택(full chrome 는 old-headless 미지원 launch 실패).

### Docs

- **`docs/ANTIPATTERNS/RENDER_ANTIPATTERNS.md`** — 신규. RENDER-AP-001 기록.

---

## [v0.11.0] — 2026-05-23

**수직 슬라이스 V3: Remotion 최소 렌더**. scene_manifest + full_script → render_props.json
→ Remotion `Briefing` 컴포지션(텍스트 슬라이드)으로 draft_debug.mp4. 미검증/추론/주장
라벨이 슬라이드 배지로 표시된다. 이로써 topic → 영상까지 파이프라인이 처음으로 관통.

### Added

- **`remotion/`** — Remotion 프로젝트 (package.json/tsconfig/src). `Briefing` 컴포지션:
  scene 당 풀스크린 슬라이드(캡션+나레이션+라벨 배지+출처 표기), calculateMetadata 로
  총 길이를 props 에서 산출.
- **`schemas/models.py`** — `RenderProps` (+ `RenderSceneProps`). camelCase (TS 친화).
- **`orchestrator/render_io.py`** — `build_render_props`(순수: scene_manifest+full_script
  join) + `09_render/render_props.json` atomic 영속화.
- **`orchestrator/main.py`** — `render-debug {pid} [--props-only]` CLI (props 생성 →
  `npx remotion render` → draft_debug.mp4, state 전이 없는 미리보기).
- **`tests/test_render_flow.py`** — render_props 빌더(순수) + render-debug --props-only
  CLI (256 통과). 실제 Remotion 렌더는 실행 검증.

---

## [v0.10.0] — 2026-05-23

**수직 슬라이스 V2: 최소 Scene**. `full_script → scene_manifest.json` 을 만드는
결정론적 빌더 + `build-scene` CLI. 텍스트 슬라이드 영상이 목표라 LLM 없이 세그먼트
1개를 SceneEntry 1개로 매핑(누적 타이밍, 캡션, 라벨 신호). hualien2024 실행으로 16
scene / 7.32분 생성 확인 — 미검증/추론/주장 세그먼트에 inference_label_required 정확 표기.

### Added

- **`orchestrator/scene_builder.py`** — `build_scene_manifest(full_script)` 순수 함수.
  segment→SceneEntry 1:1, start_sec 누적, inference_label_required=segment.label 유무,
  source_link_required=claim_refs 유무.
- **`orchestrator/scene_io.py`** — `06_scene/scene_manifest.json` atomic 영속화·로딩 +
  `build_and_persist_scene_manifest`.
- **`orchestrator/main.py`** — `build-scene {pid}` CLI (precondition script_writing →
  `script_review` 흡수 → `scene_planning` 전이).
- **`tests/test_scene_flow.py`** — 순수 빌더 결정론·매핑 + CLI happy/precondition (252 통과).

---

## [v0.9.0] — 2026-05-23

**Phase 6 Script (수직 슬라이스 V1)**. `research_dossier → full_script.json` 을 만드는
ScriptWorker + `build-script` CLI 추가. 별도 Blueprint 단계를 흡수해 dossier 에서 곧장
대본을 뽑는다. 실제 claude run 으로 검증 — claim status 라벨(`<미검증>`/`<추론>`/`<주장>`
/`<반박됨>`)이 research→script 로 무손실 전파되고, 미검증 내용은 헤지 서술, 목표 길이
(8분) 분량 맞춤 확인.

### Added

- **`schemas/models.py`** — `FullScript` (+ `ScriptChapter` / `ScriptSegment`).
  schema_version 1 유지. segment.label 로 미검증/추론/주장/반박 항목 영상 라벨 추적.
- **`workers/script_worker.py`** — `ScriptWorker` (BaseLLMWorker, response).
- **`orchestrator/script_io.py`** — `05_script/full_script.json` atomic 영속화·로딩.
- **`orchestrator/script_service.py`** — `run_script_worker` (precondition → worker →
  영속화 게이트 → `research_in_progress→blueprint_review→script_writing` 전이).
- **`orchestrator/main.py`** — `build-script {pid} [--backend] [--force]` CLI.
- **`tests/test_script_flow.py`** — happy/검증실패/precondition/프롬프트 회귀 (247 통과).

### Changed

- **개발 방향**: 수직 슬라이스로 전환 (실물 영상 최단경로 + 실제 LLM run 검증).
  codex 외부 리뷰(C10.1) 한시 중단. docs/13 에 기록.

---

## [v0.8.1] — 2026-05-23

**LLM 브리지 response 모드 격리 (LLM-AP-004)**. 6A 를 실제 `claude` 로 처음 돌렸더니
`claude -p ... --output-format json` 이 한 방 JSON 이 아니라 **에이전트로 22턴**(repo
CLAUDE.md/훅을 물고 commit·push 시도, 6분/$0.74, JSON 아님)을 도는 사고 발견. stub
테스트가 subprocess 를 안 타서 못 잡던 실 환경 이슈.

### Fixed

- **`workers/base_llm_worker.py`** — `CLI_INVOCATION` 의 claude response 모드에
  `--tools ""` + `--no-session-persistence` 추가, `_invoke_llm` 이 subprocess 를 repo
  밖 중립 cwd 에서 실행 (CLAUDE.md 자동 탐색 차단). 실측 22턴/6분/$0.74 → 1턴/1.3초/$0.005.

### Docs

- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md`** — LLM-AP-004 신규 기록.
- **`docs/ADDENDUM_04`** §4.1/§5.1 — response 모드 호출 형태/격리 규칙 동기화.

---

## [v0.8.0] — 2026-05-23

**Phase 6A Research 구현**. source_registry + manifest.initial_links 를 입력으로
영상 서사의 주장-근거 페어(`ResearchDossier`)를 생성하는 ResearchWorker 와
`build-research-dossier` CLI 를 추가. Phase 5 패턴(모델→worker→io→thin CLI→전이)을
답습. 사용자 사전 제공 리포트(initial_links)는 2차/파생 시드로 다루고 1차 출처 별도
검증을 프롬프트·스키마에 강제. state `source_completeness_review → research_in_progress`.

### Added

- **`schemas/models.py`** — `ResearchDossier` (+ `ResearchSeed` / `ResearchClaim` /
  `Evidence` / `ResearchClaimStatus` enum / `CLAIM_STATUS_LABELS` 매핑). schema_version 1
  유지 (additive). claim 의 검증 상태가 SSOT 이고 영상 라벨(`<미검증>` 등)은 파생.
- **`workers/research_worker.py`** — `ResearchWorker` (BaseLLMWorker, response 모드).
  build_user_prompt 는 `.replace()` 로 source_registry + 시드 합성, 사용자 질문 없이
  open_questions/notes 로만 신호 (C4).
- **`orchestrator/research_io.py`** — `04_research/research_dossier.json` atomic 영속화·
  로딩·경로 SSOT (source_registry_io 패턴).
- **`orchestrator/research_service.py`** — `run_research_worker` thin orchestration
  (precondition → worker → 영속화 검증 게이트 → 전이). idempotent (유효 dossier 시 skip).
- **`orchestrator/main.py`** — `build-research-dossier {pid} [--backend] [--force]` CLI.
- **`tests/test_research_flow.py`** — happy path / stub 검증 실패 / state precondition /
  영속화·idempotency / 워커 프롬프트 회귀.

### Docs

- **`docs/05`** §3.4c (ResearchDossier), **`docs/03`** (Research Agent 행 → workers/),
  **`docs/12`** §3 (claim 라벨 매핑), **`docs/13`** (6A ✅ 표기) 동기화.

---

## [v0.7.3] — 2026-05-23

**Phase 6 세부 분해 (서브스텝) 문서화**. Phase 6(Research/Script/Scene)를 6A~6E
서브스텝으로 분해하여 docs/13 로드맵에 추가. 각 서브스텝의 산출물·워커·입력·state/Gate·
증분 단위를 표로 정리하고 Phase 5 패턴(모델→worker→io→CLI→Gate) 답습 원칙을 명시.

### Docs

- **`docs/13_IMPLEMENTATION_ROADMAP.md`** — "Phase 6 세부 분해" 서브섹션 추가
  (6A Research / 6B Evidence Guard / 6C Blueprint / 6D Script / 6E Scene).

---

## [v0.7.2] — 2026-05-23

**목표 영상 길이 범위 3~20분으로 통일**. 기존 "15–20분" 가정을 풀어 짧은 브리핑부터
가능하게 하고, 웹 폼이 1~180으로 과하게 열려 있던 것을 지원 범위로 좁혔다.

### Changed

- **`schemas/models.py`** — `ProjectManifest.target_duration_min` 과
  `IntakePlan.target_duration_min` 에 `ge=3, le=20` 제약 추가 (schema_version 1 유지).
- **`web/intake_page_app.py`** — 새 프로젝트 폼의 길이 입력을 `min=3 max=20` 으로,
  `_parse_duration` clamp 를 1~180 → 3~20 으로.
- **docs** — roadmap Phase 6 완료 기준 "15–20분" → "3–20분", 05 스키마 스펙 범위 표기.

### Tests

- 신규 2 케이스 (범위 밖 CLI 거부, 웹 폼 clamp). 전체 234 → 236 통과.

---

## [v0.7.1] — 2026-05-23

**외부 코드 리뷰 1차 반영** (codex review, v0.7.0 대상). High 2 / Medium 3 / Low 2 를
모두 흡수 (false positive 없음).

### Fixed

- **`web/intake_page_app.py:create_project`** — `run_intake_planner` 의 `ValueError`
  (상태 전이 실패 — 동시 상태 변경 등) 와 예기치 못한 예외를 구조화 JSON 으로 처리
  (각각 409 "retry" / 500 + traceback 로깅). 이전엔 `IntakePlanningError` 만 잡아
  나머지가 비구조화 500 으로 샜다. (codex High2)
- **`orchestrator/intake_service.py`** — 최종 `intake_pending_user` 전이가
  `resume_project` 재호출 대신 in-memory manifest 를 사용 — worker 완료 후 재로딩
  사이의 race window 제거 (planner 는 manifest 를 건드리지 않음). (codex High1)

### Changed

- **`web/intake_page_app.py`** — 잘못된 `Content-Length` 헤더는 무시하지 않고 400,
  잘못된 `backend` 는 조용한 claude fallback 대신 400. (codex Med1/Med3)
- **`orchestrator/project_manager.py`** — `initial_links` 를 입력 경계에서 정규화
  (`_normalize_initial_links`): 제어문자/공백 제거, `http(s)://` 만 유지, 링크당
  2048자·최대 50개 cap. 사용자 링크가 IntakePlanner 프롬프트에 삽입되는 trust
  boundary 를 강화 (prompt-injection/구조 훼손 방지). (codex Med2)
- **`workers/base_llm_worker.py` 외 3개 worker** — `llm_backend` 를 `ClassVar` 에서
  일반 속성으로 변경하여 인스턴스 단위 override (`worker.llm_backend = backend`) 가
  타입상 합법이 되도록 → `# type: ignore[misc]` 제거. (codex Low1)
- **`orchestrator/intake_service.py`** — 미사용 `projects_root` 파라미터 제거
  (`worker_args.projects_root="projects"` 고정, cfg 와 단일 출처). (codex Low2)

### Tests

- 신규 2 케이스 (링크 정규화 drop, 잘못된 backend 400). 전체 232 → 234 통과.

---

## [v0.7.0] — 2026-05-23

**웹 주제 입력 진입 화면 + 초기 링크 주입**. 그동안 CLI 전용이던 "주제 입력 → 인테이크
계획 생성" 흐름을 웹으로 끌어올렸다. 사용자가 사전 확보한 자료 링크(분석 리포트 등)를
프로젝트 생성 시 함께 넣으면 IntakePlanner 가 계획에 반영한다.

### Added

- **`web/intake_page_app.py`** — `GET /new` (주제/카테고리/길이/초기 링크 입력 폼) +
  `POST /new` (검증 → `new_project` → `IntakePlanner` → `/intake/{pid}` 303 리다이렉트).
  루트 `/` 는 `/new` 로 리다이렉트. content-length 상한·project_id 검증·중복 409·
  planner 실패 500 처리.
- **`orchestrator/intake_service.py`** (신규) — `run_intake_planner` : `created`/
  `intake_planning` → `intake_pending_user` 전이 + worker 실행 + idempotency 를 한
  함수로. CLI(`plan-intake`)와 Web(`POST /new`)이 공유하는 단일 출처.
- **`ProjectManifest.initial_links: list[str]`** — 생성 시 사용자 사전 제공 링크.
  additive (schema_version 1 유지).
- **`new-project --link URL`** (반복 가능) + `new_project(initial_links=...)`.
- IntakePlanner 프롬프트에 "사용자 사전 제공 자료(manual_user_provided 후보)" 섹션
  추가 — 링크가 있으면 관련 required_item 의 default_mode 를 link_provide 로 유도.

### Changed

- **`orchestrator/main.py:_cmd_plan_intake`** — 오케스트레이션을 `intake_service` 로
  위임하는 thin wrapper 로 리팩토링 (동작·exit code 보존).

### Tests

- 신규 10 케이스 (초기 링크 영속화·프롬프트 반영, 웹 `/new` 폼 렌더·생성·리다이렉트·
  중복/검증 오류). 전체 222 → 232 통과.

---

## [v0.6.1] — 2026-05-23

**외부 코드 리뷰 1차 반영** (codex review, v0.5.5/v0.6.0 대상). Critical/Medium/Nit
중 합의된 항목 흡수. High(빈 partials strict 모드) 와 일부 Low 는 false positive /
scope 밖으로 보류 (DEVLOG 근거 명시).

### Fixed

- **`orchestrator/main.py`** — `build-source-registry` 의 `source_registry.json`
  영속화 단계에서 발생하는 디스크 `OSError` 가 잡히지 않아 controlled exit code
  대신 uncaught exception 으로 종료되던 갭 수정. report persist 의 `OSError`
  처리와 대칭으로, 두 영속화 단계 중 어디서 깨지든 상태 전이를 막는다.

### Changed

- **`orchestrator/source_completeness_checker.py`** — severity 카운터를
  `str(i.severity)` 로 정규화하여 `CompletenessIssue.model_config` (`use_enum_values`)
  변경에 결합되지 않도록 robustness 보강.

### Added

- **`schemas/models.py`** — `CompletenessIssueType.RIGHTS_STATUS_UNKNOWN_VALUE`
  신규 값. 정책 §2 미정의 권리 상태(스키마 drift) 를 known `review_required` 와
  구분되는 전용 진단으로 표면화. `SourceEntry.reliability_score` 와
  `SourceCompletenessReport.reliability_threshold` 에 `ge=0.0, le=1.0` 범위 제약
  추가. 모두 additive — `schema_version` 1 유지.

---

## [v0.6.0] — 2026-05-23

**Phase 5 완료** — Source Registry & Source Completeness Check. roadmap §42 의
두 산출물 (`source_registry.json` + `source_completeness_report.json`) 이 모두
생성되고, Review Gate 2 (`source_completeness_review`) 로 전이한다.

### Added

- **`schemas/models.py`** — `SourceCompletenessReport` (+ `CompletenessIssue`,
  `CompletenessSeverity`, `CompletenessIssueType`). optional 모델 추가이므로
  schema_version 1 유지 (C3). Review Gate 2 입력 산출물.
- **`orchestrator/source_completeness_checker.py`** — 순수 함수
  `check_source_completeness(registry, *, reliability_threshold=0.5)`. 부족 자료
  식별:
  - 사용 가능 (✅): `rights_clear` / `manual_user_provided` → usable_sources 집계.
  - `do_not_use` / `review_required` / `download_failed` / `login_required` /
    `private_or_deleted` → WARNING.
  - `rights_unknown` → INFO (Review Gate 통과 시 사용 가능).
  - `reliability_score < threshold` (strict `<`, 기본 0.5) → WARNING.
  - `risk_flags` 존재 → WARNING (정책 §5).
  - **사용 가능 자료 0개일 때만 BLOCKER** (`no_usable_sources`). overall_status
    ∈ {ready, needs_attention, insufficient}.
- **`orchestrator/source_registry_io.py`** — `persist_source_completeness_report`
  + `source_completeness_report_path`.
- **테스트** — `test_source_completeness_checker.py` (18) + io report round-trip
  (1) + CLI 검증 강화. baseline 204 → 222.

### Changed

- **`orchestrator/main.py`** — `build-source-registry` 가 registry 영속화 후
  completeness report 를 생성하고 `source_collecting → source_completeness_review`
  로 전이. 두 산출물이 갖춰진 뒤에만 전진 (영속화 실패 시 전이 안 함).
- **docs** — `05_DATA_SCHEMA_SPEC.md` 에 `SourceCompletenessReport` 요약 추가,
  `13_IMPLEMENTATION_ROADMAP.md` Phase 5 ✅ 마킹.

---

## [v0.5.5] — 2026-05-23

Phase 5 셋째 PATCH — `source_registry_builder` (순수 함수) 의 **I/O 경계** 를
신설하고 CLI 에 연결한다. partials 가 디스크에 흩어진 채로는 효용이 없으므로,
`02_sources/partials/*.json` 을 로드 → builder → `02_sources/source_registry.json`
영속화하는 wiring 을 추가. builder 의 순수성 (디스크 I/O 없음) 은 유지.

### Added

- **`orchestrator/source_registry_io.py`** — builder 의 I/O 경계.
  - `load_partials(project_id, cfg)` — `02_sources/partials/*.json` 로드 →
    `SourceCollectionPartial[]`. **결정론적 순서** (parsed `task_id` asc, tie-break
    파일명) 로 반환하여 builder 의 caller-ordering 계약 충족. `Path.glob` 의
    OS 의존적 순서를 builder 에 그대로 넘기지 않는다. 손상 partial 은 건너뛰지
    않고 예외 전파 (fail-fast).
  - `persist_source_registry(project_id, registry, cfg)` — atomic write
    (tmp → fsync → rename, 부모 디렉토리 best-effort fsync). `project_manager`
    의 manifest 영속화와 동일 정책.
  - `build_and_persist_source_registry(project_id, *, strict_input_item_id, cfg)`
    — 로딩 → builder → 영속화 thin orchestration. registry + `partial_counter`
    통계 반환.
- **`orchestrator/main.py`** — `build-source-registry {pid}` 서브커맨드.
  state precondition (`source_collecting` 에서만 허용), `--lenient-input-item-id`
  플래그 (builder 의 `strict_input_item_id=False`). 상태 전이는 source
  completeness report 와 함께 처리하는 Phase 5 완료 단계로 미룸 (본 단계는
  registry 영속화까지).
- **테스트** — `tests/test_source_registry_io.py` (15), `test_intake_flow.py` 에
  `TestBuildSourceRegistryCLI` (5). baseline 184 → 204.

---

## [v0.5.4] — 2026-05-23

v0.5.3 (SourceRegistryBuilder) 의 codex 1차 외부 리뷰 흡수 — Critical 0 /
High 2 / Medium 3 / Low 2 / Nit 1. fail-fast invariant 의 두 가지 식별자
무결성 갭 (input_item_id=None 우회, 식별자 정규화 미검증) 을 메우고, 에러
메시지에 operator action hint 를 박는다.

본 PATCH 는 CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (외부 리뷰 결과 흡수
PATCH).

### Changed

**High 흡수:**

- **`orchestrator/source_registry_builder.py:build_source_registry`** —
  `strict_input_item_id: bool = True` 키워드 인자 추가. pipeline production
  path 의 default 는 strict (None 자체 raise — planner / worker drift 신호).
  도메인 재사용 (다른 collector 가 input_item_id 안 쓰는 경우) 을 위해
  strict=False lenient 모드 보존 — 이 경우 v0.5.3 동작과 동일 (None 끼리는
  충돌 검사 skip). codex High#1 ("None 충돌 검사 우회로 idempotency 약화").

- **`orchestrator/source_registry_builder.py:_validate_identifier`** — 신규
  헬퍼. 모든 식별자 (project_id / task_id / input_item_id / source_id) 에
  대해 **case-sensitive + NFC + 전후 공백 금지** contract 강제. 정규화 후
  매칭이 아니라 의심 변이 자체를 reject — 정규화 매칭은 정상 case 차이를
  충돌로 오인할 수 있고 (`ABC` ↔ `abc`), 침묵 정규화는 식별자 무결성을
  약화시킨다. cross-partial 정규화 충돌이 들어오면 fail-fast 로 raise 하여
  upstream 의 string formatting / OS 정규화 차이 (macOS HFS+ NFD 등) 를
  즉시 노출. codex High#2 ("byte-exact 비교만 수행, 변이 무결성 갭").

**Medium 흡수:**

- **builder 의 모든 raise 메시지** — `action: ...` 형식의 operator next-step
  hint 추가. LLM-AP-003 production breach 신호 시 (1) 어느 task 의 raw
  response 를 비교할지, (2) 머지를 재실행하지 말고 어느 단계를 수정할지,
  (3) idempotency 가드의 어느 로그를 inspect 할지 명시. codex Medium#1
  ("진단 정보는 풍부하지만 cold reader 가 첫 단계를 모름, alert fatigue
  위험"). LLM-AP-003 참조는 유지 — 진단의 정합 근거.

- **`tests/test_source_registry_builder.py`** — codex Medium#2 흡수.
  v0.5.3 의 `test_input_item_id_none_is_allowed_and_skips_collision_check`
  를 두 갈래로 양분: (a) strict default 에서는 raise (negative test),
  (b) strict=False 에서는 v0.5.3 동작 (lenient positive test). 약한
  invariant 의 영속화 방지.

- **`tests/test_source_registry_builder.py`** — codex Medium#3 흡수.
  `IdentifierNormalizationContractTests` 클래스 신설 (10 케이스):
  case-sensitive 충돌 아님 (2), 전후 공백 raise (6 — source_id /
  input_item_id / project_id arg / project_id arg with empty partials /
  task_id, leading / trailing), NFC raise (2 — source_id NFD / input_item_id
  NFD, plus 정상 NFC 통과).

**Low 흡수:**

- **`build_source_registry` docstring** — caller ordering 계약을 "MUST
  provide deterministic order (recommended: sort by task_id asc)" 로 강화.
  다른 loader (e.g. `os.listdir` 의 OS-dependent 순서) 와 mix 시 발생할 수
  있는 비결정성을 docstring 에서 명시. codex Low#1.

- **`tests/test_source_registry_builder.py:CollisionAlwaysRaisesSentinelTests`**
  — sentinel test class 신설 (3 케이스). 미래 dedupe 모드 도입 시 본
  sentinel 이 깨지고, docstring 의 "머지 정책" 섹션도 같이 갱신해야 함을
  코드 레벨에서 마킹. builder docstring 의 dead-path 정책과 코드의 연결
  포인트. codex Low#2.

**Nit 흡수:**

- **`tests/test_source_registry_builder.py:_partial / _entry`** — helper 의
  `kwargs: dict` → `dict[str, object]` 로 타입 정밀화. codex Nit.

### False positives / 흡수 안 함

없음. codex 1차 리뷰의 모든 항목을 흡수.

### Test baseline

- `python -m unittest discover -s tests` : **184/184** (운영 148 + builder
  36; v0.5.3 의 19 → 36 으로 +17 케이스 신설).
- `python -m py_compile orchestrator/source_registry_builder.py` 통과.

### Changed

- **`VERSION`** 0.5.3 → 0.5.4.
- **`CHANGELOG.md`** `last_synced_with: v0.5.4`.
- **`DEVLOG.md`** `last_synced_with: v0.5.4`.

---

## [v0.5.3] — 2026-05-23

Phase 5 의 두 번째 PATCH. SourceCollectionPartial[] 을 정식 SourceRegistry 로
합치는 순수 함수 빌더 도입. 직전 PATCH (v0.5.0 / v0.5.2) 에서 deferred 된 항목
중 §3 표의 1 번 (가장 작고 위험 적은 항목) 부터 진입.

본 PATCH 는 **순수 함수 + Pydantic 합성**. 디스크 I/O / 네트워크 / LLM 호출 모두
없음. 단위 테스트만으로 충분.

본 PATCH 는 새 도메인 컴포넌트 도입 (CLAUDE.md C10.1 의 "권장" 카테고리) — codex
재리뷰 의무 면제. 단, 후속 v0.5.4 (MINOR) 진행 전에 본 PATCH 의 빌더 정책이
실제로 source_intake → partials → registry 의 e2e 흐름에서 정합한지 한 번
재검토 권장.

### Added

- **`orchestrator/source_registry_builder.py`** — 순수 함수 빌더 두 개:
  - `build_source_registry(project_id, partials) -> SourceRegistry` —
    partials 를 합쳐 정식 레지스트리 생성.
  - `partial_counter(partials) -> dict[str, int]` — 빌드 통계 (호출자 로그용).

  **설계 결정 (사용자 확정)**: 본 빌더는 fail-fast 정책 — 충돌 자체가 worker /
  planner 단의 버그 신호이거나 buggy upstream 의 사고이므로 조용히 merge / dedup
  하지 않고 raise. 무결성 사고 은폐 방지. 다섯 가지 invariant:

  1. **cross-partial source_id 충돌**     → raise (LLM-AP-003 echo identifier
                                            production breach 신호)
  2. **cross-partial input_item_id 충돌** → raise (한 input_item_id 는 한
                                            partial, planner / task_queue
                                            idempotency 검증)
  3. **intra-partial source_id 중복**     → raise (Pydantic 가 list uniqueness
                                            강제 안 함, builder 진입 전 검증)
  4. **schema_version 불일치**            → raise (C3 additive-first 위반)
  5. **project_id 불일치**                → raise (다른 프로젝트와 섞임 방지)

  **빈 partial 처리**: `collected_sources` 가 빈 partial 은 통계
  (`empty_partial_count`) 에만 +1, `sources` 에는 기여 없음. "collector 가
  실행됐으나 후보 없음" 을 구분 가능하게.

  **머지 정책 (raise 정책상 도달 불가, 향후 dedupe 모드 재사용 대비
  docstring 으로만 명문화)**:
  - `rights_status`: `do_not_use > review_required > rights_unknown > rights_clear`
    (legal-safe, false negative 회피)
  - `verification_status`: `disputed > unverified > cross_checked > official`
    (의심 우선 — 자동 머지가 임의로 official 로 승격하지 않음)
  - `reliability_score`: `min(a, b)` (정보 손실 최소화)
  - `risk_flags` / `usage_plan`: 순서 보존 합집합 (정보 보존)

- **`tests/test_source_registry_builder.py`** — 신규 19 케이스. happy path 8
  (빈 입력, 단일 partial, 다수 partial 순서 보존, 빈 partial 통계 반영,
  input_item_id=None 허용, schema_version 일치, 필드 통과) + 충돌 / 무결성
  5 (cross source_id / cross input_item_id / intra source_id / project_id /
  schema_version) + counter 3 + 충돌 검출 순서 1 + 추가 보조 케이스.

### Changed

- **`VERSION`** 0.5.2 → 0.5.3.
- **`CHANGELOG.md`** `last_synced_with: v0.5.3`, `last_review: 2026-05-23`.

### Test baseline

- `python -m unittest discover -s tests` : **167/167** (운영 148 + 신규 19).
  실 codex e2e 는 본 PATCH 의 범위 밖 (디스크 I/O / 네트워크 / LLM 호출 없음).

---

## [v0.5.2] — 2026-05-22

v0.5.0 의 codex 1차 외부 리뷰 흡수 (Critical 2 / High 3 / Medium 3 / Low 2 / Nit 5).
worker / planner / tests 의 4 가지 robustness 갭을 메우고, 본 절차 자체의 사용자
워크플로우 적합성을 v0.5.1 에 이어 한 번 더 박는다 (전달 형태 강제 규칙 C10.5).

본 PATCH 는 CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (외부 리뷰 결과 흡수 PATCH +
본 절차 자체의 수정).

### Changed

**Critical 흡수:**

- **`orchestrator/source_collection_planner.py:task_id_for`** — single-line
  concatenation 만 하던 v0.5.0 구현이 buggy/malicious upstream 의 `/`, `\\`,
  `..`, 매우 긴 item_id 를 그대로 통과시켜 worker 실행 시점의 sandbox guard 까지
  contract drift 됐던 것을 fail-fast 로 승격. (1) item_id 자체에 path
  separator / `..` 토큰 검사, (2) `_TASK_ID_PREFIX{item_id}` candidate 의
  `_is_safe_path_segment` 검증. 양쪽 모두 ValueError. planner 단에서 fail.
- **`workers/source_collector_worker.py:run`** — `BaseLLMWorker.run` 위에 post-
  parse identity invariant 검증을 추가. LLM 응답의 `project_id` / `task_id` /
  `input_item_id` 가 task 와 일치하지 않으면 (Pydantic 은 통과해도) `FAILED` 로
  마킹 + `identity_mismatch:<field>` 에러. cross-task contamination 차단.

**High 흡수:**

- **`SourceCollectorWorker._find_decision`** — 0/1/many 분기 명시. duplicate
  item_id 가 source_intake.json 에 있으면 ValueError (이전엔 first-match-wins
  silent 동작).
- **`SourceCollectorWorker.run` preflight** — `build_user_prompt` 가 raise 하는
  모든 분기 (input_item_id 누락 / intake 부재 / 매칭 결정 없음 / 잘못된 mode /
  중복 / mixed-with-remaining=False) 가 run() 안에서 catch 되어
  `TaskResult(FAILED)` 로 변환. LLM 호출 비용 절감 + task_result.json 추적성 보장.
- **`tests/test_source_collector_worker.py` argv 검증** — index-based adjacency
  (`cmd[idx+1]`) → `_argv_get_option` 헬퍼로 `--name value` 와 `--name=value` 두
  형태 모두 robust 인식. codex CLI 의 옵션 표기 변화에 brittle 하지 않음.

**Medium 흡수:**

- **`workers/source_collector_worker.py`** unused `import json` 제거 (C2 hygiene).
- **`SourceCollectorWorker._preflight_validate`** — `mode == mixed` 이고
  `ai_delegate_remaining == False` 인 경우 ValueError. planner 가 이미
  필터링하지만 worker 단에서도 enforce — 수동/잘못된 task_queue 진입 차단.
- **`tests/test_source_collector_worker.py::test_mentions_source_entry_keys`** —
  9 → 16 필드 (전체) 검증. prompt 에서 일부 필드가 빠지는 회귀 차단.
- **`test_long_user_note_does_not_raise`** — 약 80 KB user_note 도 raise 없이
  envelope 안에 wrap. 명시적 truncation 정책은 후속 PATCH (현재 동작 잠금).

**Low 흡수:**

- **`source_collection_planner.py`** `Optional[set[str]]` → `set[str] | None`
  modern union 스타일 통일.
- **`source_collector_worker.py` system_prompt** — `%TEMP% (Unix /tmp)` →
  "OS 임시 디렉토리 (Windows `%TEMP%`, Unix `/tmp`)" 로 platform 표현 명확화.

**규칙 강화 (사용자 요청, v0.5.0/v0.5.1 운용 사고 반영):**

- **`CLAUDE.md` C10.0** — AI 책임에 (d) 신설: "**codex 환경이 GitHub fetch 못 할
  가능성을 디폴트로 가정**하고 신규/변경 파일 본문을 review-prompt 안에 inline
  으로 (`### FILE: <path>` 헤더 구분) 함께 박는다". v0.5.0 세션에서 codex 클라우드
  fetch 가 HTTP 403 / outbound 차단으로 실패해 리뷰가 blocked 됐던 사고 반영.
  v0.5.1 에서 잠시 박았던 "inline + SendUserFile 동시 노출" 규칙은 사용자가 중복
  거추장스럽다 거부 → C10.5 의 크기 분기 표로 교체.
- **`CLAUDE.md` C10.5** 신설 — review-prompt 본문 전달 형태 강제 규칙. ≤ 30 KB
  는 inline 코드블록 단독, > 30 KB 는 SendUserFile 단독. 4 가지 금지 형태
  (동시 노출 / SendUserFile 단독 with 작은 본문 / 코드블록 분할 / 머신 경로
  placeholder 노출) 를 v0.5.0/v0.5.1 운용 사고 사례와 함께 명시.
- **`CLAUDE.md` C10.2 step 2** — inline 본문 박는 의무를 절차 본문에도 반복
  명시. 전달 형태는 C10.5 위임.
- **`CLAUDE.md` last_synced_with** v0.5.1 → v0.5.2.

### Verification

- `python -m py_compile` 통과 (수정된 worker / planner / tests).
- `python -m unittest discover -s tests` = **148/148 통과** (직전 129 + 신규 19).
  신규 19 분포: source entry full-fields 1 + duplicate 1 + mixed-False 1 +
  long-payload 1 + preflight run-level 6 + identity invariant 5 + argv
  helper 3 + planner unsafe item_id 5 = 22 추가 중 일부는 기존 ID 변경
  (실제 +19).
- 본 PATCH 의 코드 변경은 backward-compat — v0.5.0 의 contract 를 부수지 않음
  (test_run_ok_persists_partial_and_record 등 기존 정상 경로 회귀 통과).

### Migration / Compatibility

- 코드: worker / planner 의 raise 조건이 더 엄격해졌으나 정상 입력은 영향 없음.
  malicious / buggy upstream 만 빨리 fail.
- 절차: 다음 MINOR/MAJOR commit 부터 C10.5 의 전달 형태 분기표 적용. 본 세션
  컨텍스트 안의 AI 어시스턴트도 즉시 따른다 ("기억해" 사용자 명령 반영).

---

## [v0.5.1] — 2026-05-22

CLAUDE.md C10 외부 코드 리뷰 절차의 운영 패턴을 갱신. v0.5.0 세션에서 실 사용 중
드러난 두 사고를 규칙으로 박는다 — (1) review-prompt 본문이 SendUserFile 만으로
전달되어 사용자가 다운로드 파일을 못 찾는 사고, (2) "MINOR 증분 직전" 표현이 codex
클라우드 (commit 된 브랜치를 fetch 하는 방식) 와 충돌하던 모호성.

CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (본 절차 자체의 수정).

### Changed

- **`CLAUDE.md` C10.0** — AI 어시스턴트 책임에 다음 항목을 신설/강화:
  - (b) 트리거 commit (MINOR/MAJOR) 을 만들고 작업 브랜치에 **push 까지 완료** 한다
    (codex 클라우드는 push 된 브랜치만 fetch 하므로).
  - (c) review-prompt 본문을 **SendUserFile 과 inline 코드블록 두 가지 형태로
    동시에** 전달한다 (사용자가 다운로드 파일을 못 찾는 사고 방지).
  - (d) 결과 흡수는 다음 PATCH (`vX.Y.(Z+1)` "외부 코드 리뷰 N차 반영").
  - 사용자 책임에 codex 클라우드 (권장) / 로컬 codex CLI (폴백) 선택 명시.
  - 위반 사례로 "SendUserFile 단독 전달" 도 명문화.
- **`CLAUDE.md` C10.1** — 트리거 표 갱신:
  - "MINOR / MAJOR 증분 직전" → "**MINOR / MAJOR commit + push 직후**"
    (v0.4.0 → v0.4.1, v0.5.0 → v0.5.1 패턴 명시).
  - "본 C10 절차 자체를 도입/수정하는 PATCH" 행 신설 (면제 명시).
- **`CLAUDE.md` C10.2** — 절차를 6 단계로 재구성. push 가 1 번 단계로 선행.
  codex 클라우드 vs 로컬 codex CLI 두 패턴 분기 명시.
- **`docs/REVIEW_PROMPT.md` §3** — 실행 패턴 절을 재구성:
  - **§3.0 codex 클라우드 (권장)** 신설. repo + 브랜치 + review-prompt 본문 paste
    패턴. 장단점 표. commit-안된-변경 못 보는 제약 명시.
  - 기존 §3.1 Windows cmd, §3.2 macOS/Linux 는 "로컬 codex CLI (폴백)" 으로 재라벨.
- **`CLAUDE.md` / `docs/REVIEW_PROMPT.md` 의 `last_synced_with`** v0.3.4 → v0.5.1.

### Verification

- 본 PATCH 는 문서 변경만. 코드 / 스키마 / 테스트 영향 없음.
- C10.3 에 따라 codex 재리뷰 면제 — 본 절차 자체의 수정.

### Migration / Compatibility

- 다음 MINOR/MAJOR commit 부터 본 절차 적용. 절차상 차이는 push 시점 (commit 전 →
  commit 직후) 뿐, 결과 흡수 형식은 동일.

---

## [v0.5.0] — 2026-05-22

Phase 5 첫 PATCH — `SourceCollectorWorker` 도입 (codex agent 모드 첫 도메인 worker).
본 시점에 v0.4.0–v0.4.2 의 LLM-AP-003 mitigation (sandbox + scratch dir + path
가드 + side-channel known-limits) 위에서 실 호출하는 worker 가 처음 들어온다.

### Added

- **`workers/source_collector_worker.py`** — `BaseLLMWorker` 상속, `llm_backend=
  "codex"`, `llm_mode="agent"`, `allow_agent_mode=True` (LLM-AP-003 opt-in).
  `response_model=SourceCollectionPartial`. system prompt 가 SourceCollectionPartial
  / SourceEntry / RightsStatus 스키마와 codex agent sandbox 의 verified side
  channels (`%TEMP%`, `~/.codex/memories`) 접근 금지를 명시. `build_user_prompt`
  는 `01_intake/source_intake.json` 의 매칭 `UserDecision` 을 읽어 `user_note`,
  `provided_links`, `google_drive_links`, `uploaded_files` 를 `wrap_untrusted`
  로 단일 `<untrusted_source>` envelope 으로 격리. mode ∈ {ai_delegate, mixed}
  외에는 ValueError. output_path = `02_sources/partials/{task_id}.json`.
- **`orchestrator/source_collection_planner.py`** — 순수 함수 빌더. `task_id_for`,
  `needs_collection`, `build_source_collection_tasks(intake, existing_task_ids=...)`.
  `ai_delegate` / `mixed(ai_delegate_remaining=True)` 만 task 로 변환. `task_id`
  prefix `src_collect__{item_id}` 로 `_is_safe_path_segment` 통과 보장.
  `existing_task_ids` 로 idempotency.
- **`tests/test_source_collector_worker.py`** — 29 케이스 / 7 클러스터:
  system_prompt 정합 (스키마 / enum / sandbox 경계 / envelope guidance /
  `.format()` 금지), build_user_prompt (정상 매핑 / envelope injection 격리 /
  누락 / 잘못된 mode), output_path, run() 4 분기 (ok / parse_failed /
  validation_failed / subprocess_error), agent opt-in 가드 통과,
  `_build_invocation_cmd` 의 sandbox argv shape + scratch dir 부수 효과,
  task builder mode 필터 + idempotency.

### Changed

- **`VERSION`** 0.4.2 → 0.5.0 (MINOR — 새 worker 추가, C5.4).

### Verification

- `python -m py_compile` 통과 (신규 3 파일).
- `python -m unittest discover -s tests` = **129/129 통과** (기존 100 + 신규 29).
- 본 PATCH 는 commit + push 후 codex 클라우드 외부 리뷰 예정 (CLAUDE.md C10.1
  MINOR 직전 의무). 결과 흡수는 후속 v0.5.1 PATCH (v0.4.0 → v0.4.1 패턴과 동일).

### Migration / Compatibility

- 스키마 변경 없음 (`SourceCollectionPartial` 은 v0.4.0 도입). `schema_version`
  변경 없음.
- 호출하는 task / CLI / state 전이는 후속 PATCH. 본 PATCH 만으로는 worker 가
  pipeline 에 자동 합류하지 않음 — orchestrator 가 source_collection task 를
  생성하기 시작해야 활성화.

### Out of Scope (deferred)

- `task_queue.json` 영속화 + CLI 명령 (`build-source-tasks` 등) + state 전이.
- `SourceRegistryBuilder` (partial → `SourceRegistry` 합치기).
- 실 codex 프로세스를 띄우는 e2e smoke (사용자 머신에서 후속 PATCH).
- Phase 5 완료 marker.

---

## [v0.4.2] — 2026-05-22

LLM-AP-003 mitigation 의 실 효과 검증 (codex 0.130.0 Windows) 후 known-limits
및 ADDENDUM_04 §5.2.1 갱신. 코드 변경 없음, 문서만. CLAUDE.md C10.3 에 따라
codex 재리뷰 면제 (외부 검증 결과 반영 PATCH).

### Changed

- **`docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` §5.2.1 신설** — codex agent
  mode sandbox 가정의 실 검증 표. workdir 외 자동 허용 영역 (`%TEMP%`,
  `~/.codex/memories`) + junction 차단 확인 + codex 0.130.0 CLI 의 narrowing
  옵션 부재 + 버전 종속성 명시.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003 known-limits** —
  v0.4.2 갱신. "검증된 보호" / "검증된 side channels" 두 절로 재구성. v0.4.1
  의 `_assert_no_symlinks_in_path` preflight 가 codex 0.130.0 의 OS-level
  junction 차단과 중복하지만 defense-in-depth 로 유지함을 명시.

### Verification

실 검증 시나리오 (사용자 머신, ChatGPT Plus 구독, codex-cli 0.130.0):

**Stage 1 — codex CLI 직접 호출**:
- 1a: workdir 안 write → ✅ 정상 (codex 가 `inside.txt` 생성)
- 1b-Desktop: workdir 밖 명확한 write → ✅ codex 가 sandbox 거부 명시
- 1b-multi: `C:\tmp\sibling`, `%TEMP%`, `~/.codex/memories` 각각 시도 →
  sibling 차단 ✅ / `%TEMP%` 허용 ⚠️ / memories 허용 ⚠️
- 1c-junction: `mklink /J` 로 scratch 안에 outside 가리키는 junction 깐 뒤
  via_junction.txt 작성 시도 → codex 가 OS-level 차단 ✅

**Stage 2 — Python 가드 단독** (컨테이너):
- `_is_safe_path_segment` 11 케이스 모두 기대값
- `_scratch_dir_for_task` 멱등성 / clean_scratch ephemeral / opt-out 정상
- `_build_invocation_cmd` argv 모양: codex agent 에 sandbox + scratch_cd 포함,
  claude response 에 sandbox 부재 + mkdir 부재
- `_assert_no_symlinks_in_path` POSIX symlink 검출 동작
- placeholder fail-fast + response + `{scratch_dir}` raise 모두 동작
- 사용자 prompt 본문의 JSON `{}` 는 검사 제외

**결론**: v0.4.0-v0.4.1 mitigation 은 핵심 자산 보호 (다른 worker 산출물 /
git 추적 코드 / 사용자 자료) 에 효과적. `%TEMP%` 와 `.codex/memories` 두
side channel 은 codex CLI 의 디폴트로 닫을 수 없어 known-limit 로 명시 +
prompt 측 / 운영 절차로 보강.

### Migration / Compatibility

문서 변경만. 코드/스키마 변경 없음.

---

## [v0.4.1] — 2026-05-22

v0.4.0 의 codex 1차 외부 리뷰 흡수 (Critical 2 / High 3 / Medium 3 / Low 1 / Nit 1).
sandbox + scratch dir 격리의 "의도된 가정" 들을 명시적 가드로 승격하고 회귀 테스트로
잠근다. 본 PATCH 는 CLAUDE.md C10.3 에 따라 codex 재리뷰 면제.

### Added

- **`workers/base_llm_worker.py:_is_safe_path_segment`** (module-level helper)
  — task_id 가 단일 path 세그먼트로 안전한지 검사. `/`, `\\`, `..`, `.`,
  leading `.`, 길이 > 128 거부. `Path(s).name == s` 추가 확인.
- **`workers/base_llm_worker.py:_assert_no_symlinks_in_path`** (module-level
  helper) — `path` 부터 `stop_at` 까지 위로 올라가며 symlink 검사. scratch
  경계가 symlink 인 escape 시나리오 차단.
- **`BaseLLMWorker.clean_scratch_on_start: ClassVar[bool] = True`** — scratch
  dir ephemeral 보장. 같은 task_id 재실행 시 이전 잔존물 노출 차단. 멱등
  worker (parse-on-resume) 가 잔존물 활용해야 하면 False 로 opt-out.
- **`BaseLLMWorker._build_invocation_cmd(args, full_prompt) -> list[str]`** —
  `_invoke_llm` 에서 argv 빌드 로직을 분리. subprocess 호출 없는 순수 함수라
  argv shape 회귀 테스트 가능.
- **`tests/test_base_llm_worker_sandbox.py`** — 17 메소드. path segment
  safety / scratch dir lifecycle / symlink preflight / codex-agent argv 의
  sandbox+scratch_cd 존재 / response argv 의 sandbox 부재 / placeholder
  fail-fast / response 모드 + `{scratch_dir}` raise / 사용자 prompt 본문 내
  `{...}` 허용 카테고리.

### Changed

- **`BaseLLMWorker._scratch_dir_for_task`** — (a) `_is_safe_path_segment` 로
  task_id 검증, 실패 시 `LLMSubprocessError` (LLM-AP-003 path traversal 가드).
  (b) `clean_scratch_on_start=True` 면 mkdir 전에 `shutil.rmtree`. (c) mkdir
  직후 `_assert_no_symlinks_in_path` preflight 로 scratch_root → scratch_dir
  경로상 symlink 검사.
- **`BaseLLMWorker._build_invocation_cmd`** (분리된 신규 메서드 안) —
  (a) template-driven scratch: `{scratch_dir}` 가 template 에 있을 때만
  `_scratch_dir_for_task` 호출 (mode-driven → template-driven). (b) response
  모드 template 에 `{scratch_dir}` 발견 시 `LLMSubprocessError` raise (silent
  empty-string substitution footgun 제거). (c) 치환 후 `{name}` 패턴이 cmd
  argv 에 잔존하면 fail-fast (사용자 prompt 자리는 예외 — JSON `{}` 충돌 회피).
- **`schemas/models.py:SourceCollectionPartial`** — (a) docstring "Phase 4"
  → "Phase 5" 정정 (DEVLOG/CHANGELOG/LLM-AP-003 의 표기와 일치). (b)
  `notes` → `collector_notes` rename (consumer 입장에서 출처 명확화). 본
  모델은 v0.4.0 신규로 영속 인스턴스 없어 호환성 부담 없음.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003** — mitigation /
  regression_test / resolved / status / known-limits 절 v0.4.1 항목 추가.
  v0.4.0 의 "scratch 밖으로도 write 못 함" 단정 → "의도된 가정 하에서 …"
  로 톤다운 (known-limits 의 symlink/mount 불확실성과 균형).

### Rationale

codex 1차 리뷰가 정확히 짚은 것: v0.4.0 는 "올바른 방향" 이지만 "실 효과를
보장하는 가드" 가 빠져 있었다. v0.4.0 의 LLM-AP-003 본문이 "intent" 만 적고
"verified guarantees" 까지 적지 못한 것을 v0.4.1 에서 보강.

Critical 2 항목 (task_id traversal / symlink escape) 은 단일 가드 함수
도입으로 처리. High 3 (placeholder footgun / mode-template drift / 테스트
부재) 는 `_build_invocation_cmd` 추출 + fail-fast + 17 회귀 테스트로 처리.
Medium 3 / Low 1 / Nit 1 도 같은 PATCH 에 묶음 — 모두 같은 의도 "v0.4.0
mitigation 의 가드 승격" 하에 있음.

### Testing

- `python -m py_compile workers/base_llm_worker.py schemas/models.py
  tests/test_base_llm_worker_sandbox.py` 통과.
- `python -m unittest discover tests` — 100 케이스 통과 (기존 83 + 신규 17,
  회귀 없음).

### False positive

리뷰의 첫 번째 round (commit 9b200a8 이전 working tree 기준) 는 컨테이너의
uncommitted 변경을 사용자 머신에서 못 봐서 "구현 안 됨" 으로 정확히 짚었지만,
두 번째 round (commit 9b200a8 기준) 로 superseded. 본 PATCH 는 두 번째 round
만 흡수.

### Migration / Compatibility

- `SourceCollectionPartial.notes` → `.collector_notes` rename: 본 모델은
  v0.4.0 신규라 영속 데이터 없음. 호환성 영향 없음.
- 기존 BaseLLMWorker 하위 클래스에서 `clean_scratch_on_start` 를 명시하지
  않으면 기본 True 가 적용 — 이전엔 잔존물 보존이었지만 v0.4.1 부터는
  ephemeral. 의도적 잔존물 활용 worker 가 있으면 클래스 변수로 `False` 명시.
  현재 agent 모드 worker 가 0 개이므로 실 영향 없음.

---

## [v0.4.0] — 2026-05-22

LLM-AP-003 의 본격 sandbox/scratch dir 격리 도입 — codex agent 모드의 CLI
매핑을 안전한 형태로 변경하고, Phase 5 `source_collector_worker` 의 출력 모델
(`SourceCollectionPartial`) 을 선행 정의. 본 PATCH 는 CLI 매핑 변경 + 헬퍼
신설 + 도메인 모델 추가에 해당해 **MINOR** 증분.

### Added

- **`workers/base_llm_worker.py:BaseLLMWorker._scratch_dir_for_task`** — agent
  모드 codex CLI 의 `--cd` 대상 디렉토리. `projects/{pid}/scratch/{task_id}/`
  를 mkdir(parents=True, exist_ok=True) 로 생성하고 반환. agent 가 본 디렉토리
  밖으로 write 하지 못하도록 `--sandbox workspace-write` 와 함께 사용.
- **`schemas/models.py:SourceCollectionPartial`** — Phase 5 의
  `source_collector_worker` 단일 task 출력 모델. project_id / task_id /
  input_item_id (Optional) / collected_sources (list[SourceEntry]) / notes
  필드. 추가는 optional 모델 신설이므로 `schema_version` 1 유지 (C3 준수).

### Changed

- **`workers/base_llm_worker.py:CLI_INVOCATION`** — codex agent 엔트리에
  `--sandbox workspace-write` 추가. `--cd` 인자를 `{project_dir}` → 새
  placeholder `{scratch_dir}` 로 변경. response 모드는 영향 없음 (entry
  자체가 `--cd` / `--sandbox` 를 갖지 않음).
- **`workers/base_llm_worker.py:_invoke_llm`** — placeholder 치환 시
  `llm_mode == "agent"` 인 경우에만 `{scratch_dir}` 를
  `_scratch_dir_for_task(args)` 결과로, response 모드는 빈 문자열로 치환.
  agent 모드 templates 가 본 placeholder 를 갖지 않으면 빈 문자열로도 안전.
- **`docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-003** — mitigation /
  regression_test / resolved / 상태 / 알려진 한계 절 갱신. status 는
  `resolved-partial` 유지하되 partial 의 의미가 "sandbox 매핑까지 마련,
  실 호출하는 worker 도입은 Phase 5" 로 이동.

### Rationale

LLM-AP-003 의 v0.2.5 (opt-in 가드) / v0.3.3 (envelope 헬퍼) 다음 단계.
agent 모드의 prompt injection 면적을 줄이는 세 번째 layer: OS 레벨 sandbox
+ 파일시스템 격리. Phase 5 의 `source_collector_worker` 가 들어와야 실
효과를 실증할 수 있지만, CLI 매핑과 헬퍼는 worker 보다 먼저 박혀 있어야
worker 가 일관된 sandbox 가정 위에서 동작할 수 있다.

`SourceCollectionPartial` 도 같은 맥락 — Phase 5 worker 를 짤 때 출력 모델이
schema 에 미리 있어야 한 PATCH 안에서 worker + 모델을 동시에 도입하지 않아도
된다 (작은 단위 커밋 원칙 C8.2).

### Testing

- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
- 기존 단위 테스트 83 케이스 모두 통과 (회귀 없음).
- 새 코드 경로의 회귀 테스트는 Phase 5 의 `source_collector_worker` 도입과
  함께 추가 예정 — 본 v0.4.0 은 CLI 인자 정적 정합성과 헬퍼 mkdir 의 부수
  효과만 다루므로 단위 테스트만으로는 실 효과 검증이 제한적.

### Migration / Compatibility

- 사용자 머신의 codex CLI 가 `--sandbox` 플래그를 지원해야 한다 (rust 구현 기준
  현재 버전 대다수 지원). 미지원 codex 는 agent 모드 호출 시 unknown flag
  로 비0 종료 → `_invoke_llm` 의 H1 로깅 후 `LLMSubprocessError`. 호출자가
  분기 가능.
- 기존 agent 모드 worker 가 `{project_dir}` 안의 자료를 prompt-time 에 직접
  파일로 읽던 경우, v0.4.0 부터는 codex 가 sandbox 외부를 못 보므로 그 자료를
  `build_user_prompt` 안에서 텍스트로 inline (가급적 `wrap_untrusted` 로
  격리) 해야 한다. 현재 agent 모드를 opt-in 한 worker 는 0 개이므로 실
  마이그레이션 영향 없음.

---

## [v0.3.4] — 2026-05-22

codex 외부 리뷰 절차의 **역할 분담을 규칙으로 박음**. 트리거 시점에 AI 어시스턴트가
`review-prompt.txt` 본문을 직접 생성하고, 사용자가 codex 실행 + 결과 paste 만 수행하도록
명문화. AI 가 절차를 *안내만* 하고 사용자 요청을 기다리는 형태도 위반으로 정의.
본 PATCH 는 C10.3 (절차 자체 수정) 에 의해 codex review 면제.

### Changed

- **`CLAUDE.md` C10** — 새 §C10.0 "역할 분담 (변경 불가)" 추가. AI 어시스턴트 / 사용자
  각자의 책임을 표로 명시. "AI 어시스턴트는 본 절차를 임의로 생략하지 못한다" 를
  굵은 강조로 명문화. trigger 시점에 *안내만* 하는 행동도 위반으로 정의.
- **`CLAUDE.md` C10.2** — 절차 5 단계의 각 step 에 `(AI 어시스턴트 책임)` /
  `(사용자 책임)` / `(공동)` 태그를 부여. step 1 은 "AI 가 세 절을 모두 직접 채워서
  완성된 `review-prompt.txt` 를 전달" 로 재정의 (이전: 누가 채우는지 불명시).
- **`docs/REVIEW_PROMPT.md` §2** — 표준 프롬프트 템플릿 안내 직후에 "세 절의 변수
  채움은 AI 어시스턴트의 책임" / "AI 가 빈 칸을 사용자에게 떠넘기는 형태는 금지"
  를 인용 블록으로 추가.

### Rationale

v0.3.3 까지의 절차 문서는 codex review 가 "필수" 임을 명시하긴 했지만, 누가
프롬프트를 채우는지 / AI 가 능동적으로 절차를 시작해야 하는지가 불명확했음.
실제 사례에서 AI 어시스턴트가 MINOR 증분 직전임에도 절차를 "사용자가 직접
codex 에 paste 할 단계" 정도로만 안내하고 능동적 시작을 누락하는 일이 발생.
본 PATCH 는 이 ambiguity 를 닫음 — AI 어시스턴트의 비결정적 안내가 아니라
**의무로 박힌 행동** 으로 전환.

---

## [v0.3.3] — 2026-05-22

LLM-AP-003 후속 사전 작업. `<untrusted_source>...</untrusted_source>` envelope 헬퍼
도입 — 순수 함수 + 회귀 테스트만. Phase 4 의 `source_collector_worker` (agent 모드)
가 외부 자료를 prompt 에 넣을 때 사용 예정. 본 PATCH 는 코드 동작 변경 없음 (헬퍼
신설만, 호출하는 worker 는 아직 없음).

### Added

- **`workers/prompt_safety.py:wrap_untrusted`** — 외부 자료를 `<untrusted_source>`
  envelope 으로 안전하게 wrap 하는 순수 함수. content / source_label 안의 동일 envelope
  태그 토큰 (`<untrusted_source>` / `</untrusted_source>` + case-insensitive /
  whitespace-tolerant 변형) 을 명시적 escape 마킹으로 치환해 LLM 이 envelope 경계를
  오인하지 않게 한다. opener 의 label 속성은 `"` / newline 도 안전화. 디스크 / 네트워크
  / subprocess I/O 없음.
- **`tests/test_prompt_safety.py`** — 5 카테고리 × 13 메소드. ① 정상 wrap 형식 / 빈
  content / label 속성 / 빈 label 생략 ② close-tag injection escape ③ open-tag injection
  + 속성 달린 open-tag escape ④ case (대문자) / whitespace 변형 escape ⑤ label 안전화
  (`"` → `&quot;`, envelope 태그 escape, newline 평탄화).

### Changed

- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` — LLM-AP-003 의 mitigation / regression_test /
  resolved 항목에 envelope 헬퍼 진전 반영. status 는 여전히 `resolved-partial` —
  sandbox 매핑 / scratch dir 격리는 Phase 4 에서 완료 예정. 알려진 한계도 sentinel
  vs sandbox 의 역할 분리 명시.

### Testing

- 단위 테스트 70 → **83 케이스** (state machine 10 + prompt safety 13 추가). 모두 통과.
- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.

---

## [v0.3.2] — 2026-05-22

SCHEMA-AP-001 (`ProjectState` 임의 점프 / self-loop) 회귀 테스트 명시. v0.2.7 카탈로그
등록 시점부터 `pending` 으로 남아있던 부채를 청산. 코드 동작 변경 없음, 테스트만 추가.

### Added

- **`tests/test_state_machine.py`** — SCHEMA-AP-001 회귀 5 카테고리 × 10 테스트 메소드.
  ① 정상 선형 (`LinearSequenceTransitions`: `LINEAR_SEQUENCE` 의 모든 인접 페어 + str
  coerce) ② 임의 점프 거부 (`ArbitraryJumpRejected`: 정·역 양방향) ③ self-loop 거부
  (`SelfLoopRejected`: 비-archived + archived) ④ ARCHIVED 어디서든 도달
  (`ArchivedReachableFromAnywhere`: `allowed_next_states` + 실 전이) ⑤ ARCHIVED 종착성
  (`ArchivedIsTerminal`: allowed 빈 집합 + 모든 외부 전이 거부).

### Changed

- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` — SCHEMA-AP-001 의 `regression_test` 가
  `pending` → 실제 파일 경로로 갱신. 5 카테고리·10 메소드 매핑 명시. `status: active`
  의 의미를 "감지·차단·회귀 모두 마련됨" 로 보강.

### Testing

- 단위 테스트 60 → **70 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 +
  인테이크 flow 15 + state machine 10). 모두 통과.
- `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.

---

## [v0.3.1] — 2026-05-21

Codex 4차 리뷰 (v0.3.0, 89f56f9 검증, Phase 3 직후) 결과 일괄 흡수 —
Critical 1 / High 3 / Medium 4 / Low 1 / Nit 1. 모두 진짜로 판정, false positive 없음.
본 PATCH 는 C10.3 self-exemption (외부 리뷰 결과 흡수 PATCH) 에 해당해 추가 review 면제.

### Fixed (외부 코드 리뷰 4차 반영)

- **(C1) `{project_id}` path traversal 차단** — `web/intake_page_app.py` 의 GET/POST 가
  raw path segment 를 그대로 `project_dir(pid)` 에 전달해 `../../etc` 같은 입력으로 `projects/`
  바깥에 접근 가능했음. `orchestrator/project_manager.py` 에 공개 가드 `validate_project_id`
  를 분리 (기존 `new_project` 의 내부 검증을 추출). web 의 `_validated_pid` 가 두 endpoint
  진입점에서 강제, CLI `plan-intake` / `submit-intake` 도 동일 가드 호출. 위반 시 400 +
  `"invalid project_id"` generic 메시지 (사용자 입력 echo 안 함, 정찰 가치 축소).
- **(H1) 404 detail 의 절대경로 누출 차단** — `FileNotFoundError` 의 원본 메시지에 절대 경로
  + 후속 명령어 예시가 포함돼 그대로 HTTP detail 로 노출됐음. 이제 generic 메시지만 클라이언트에
  반환하고 절대경로는 `logger.warning(...)` 으로 서버 측에만 기록.
- **(H2) form body 크기 상한 (`MAX_FORM_BYTES=256KiB`)** — `await request.form()` 이 무제한
  입력을 받아 DoS 가능했음. submit 핸들러가 `content-length` 헤더를 미리 검사해 초과 시 413
  + `"request body too large"` 즉시 거부. 변조된 헤더는 무시하고 starlette 내부 한도가 fallback.
  운영 튜닝/테스트용으로 모듈 변수 형태 노출.
- **(H3) `plan-intake` idempotency 보강** — 이전 흐름은 매 호출마다 worker 를 재실행해
  LLM 호출 비용 + record 누적. `intake_planning` 상태에서 유효한 `01_intake/intake_plan.json`
  이 이미 있으면 worker skip 하고 `intake_pending_user` 로 전이만 진행. 손상된 plan 은 재실행.
  `--force` 옵션으로 강제 재실행. 출력에 `skipped=True/False` 명시.
- **(M1) `submit-intake` write 와 transition 순서 역전 (CLI + Web)** — 이전 흐름은
  `source_intake.json` 을 먼저 디스크에 쓰고 `transition_state` 가 실패해도 파일이 남아 잘못된
  상태에서 덮어쓰기 가능. CLI 는 tmp write → transition → atomic rename (transition 실패 시
  tmp cleanup). Web 은 state precondition 검증 → transition → write 순으로 재배열 + 사전
  current_state 검증 (intake_pending_user 아니면 409 즉시 거부, 파일 미수정).
- **(M2) `plan-intake` 가 `task_result.json` 영속화** — `worker.run()` 직접 호출 경로가
  `BaseWorker.main` 의 표준 흐름을 우회해 task_result.json 이 안 만들어졌음. C4 의 추적성 정합을
  위해 `worker.write_result(args, result)` 명시 호출. Phase 4 의 정식 task_queue 흐름 도입
  전까지의 stopgap 이지만 PR review 와 사후 분석에서 일관된 인공물 생성 보장.

### Added (회귀 테스트)

- **(M3) IntakePlannerWorker `parse_failed` / `subprocess_error` 회귀** — 기존엔 ok /
  validation_failed 두 케이스만 cover. 본 PATCH 가 4 parsed_status 분기 전부 명시 도달.
  `tests/test_intake_planner_worker.py::TestRunParseFailed` (자연어 stub → JSONDecodeError) +
  `TestRunSubprocessError` (`_invoke_llm` monkeypatch → exit_code 7 record 영속화 검증).
- **(M4) Web negative path 회귀** — `tests/test_intake_flow.py::TestWebSecurityAndNegativePaths`
  6 케이스. (a) `..` 인코딩 PID GET/POST 거부, (b) 대문자 PID 거부 (정책 정규식), (c) 없는 PID 의
  404 generic detail (절대경로 미노출), (d) MAX_FORM_BYTES 임계치 잠시 낮춰 413 확인, (e) state
  precondition 미충족 시 POST 409 + 기존 source_intake.json bytes 보존 (M1 검증), (f) plan-intake
  의 task_result.json 영속화 (M2 검증), (g) idempotent skip 회귀 (LLM stub unset 상태에서도 worker
  미호출, llm_calls/ 미생성).

### Fixed (Nit)

- **(N1) `tests/test_intake_planner_worker.py` 코멘트 정정** — "required_items 누락 →
  IntakePlan validation 통과" 는 사실과 다름 (required_items 가 `default_factory=list` 라
  누락만으로는 위반 안 됨; 실제 실패 유발은 `unknown_extra_field` 의 `extra="forbid"` 위반).
  코멘트를 정확히 다시 작성.

### Notes

- 단위 테스트 49 → **60 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 + 인테이크
  flow 15). 모든 추가가 회귀 테스트로 검증.
- 본 PATCH 는 `last_synced_with` 일괄 갱신을 하지 않음 — v0.2.9 의 n9ird 컨벤션 (수정한 파일의
  헤더만 갱신) 을 따름. PATCH 범위가 코드 4 파일 + 테스트 2 파일 + 본 CHANGELOG + DEVLOG +
  HANDOFF 만 수정. 다음 MINOR (v0.4.0) 에서 다시 일괄.
- **C10.3 self-exemption**: 본 PATCH 는 외부 코드 리뷰 결과 흡수 PATCH 이므로 codex review
  의무 면제 (무한 루프 방지). 다음 외부 리뷰는 v0.4.0 MINOR 직전.
- HANDOFF.md 의 "1. 지금 어디까지 와 있나" 표에 v0.3.1 행 추가.

### Codex 4차 리뷰 미반영 항목

없음. C/H/M/L/Nit 11 항목 전부 흡수.

---

## [v0.3.0] — 2026-05-21

**Phase 3 완료 — Dynamic Intake Page + IntakePlannerWorker (첫 도메인 LLM Worker).**

C5.4 의 MINOR 트리거 두 가지 (Phase 완료 + 새 Worker 추가) 가 동시에 충족됨. Phase 2 (v0.2.0) 와
동일하게 단일 MINOR 커밋으로 Phase 의 모든 변경을 묶음.

### Added
- **`workers/intake_planner_worker.py:IntakePlannerWorker`** — 본 저장소 첫 도메인 LLM
  Worker. `BaseLLMWorker` 상속, `response_model=IntakePlan`, `llm_backend="claude"` 기본
  (인스턴스 attribute 로 `"codex"` 전환 가능), `llm_mode="response"` (외부 자료 미사용,
  `allow_agent_mode` 는 False 유지 → LLM-AP-003 우회). `system_prompt` 는 IntakePlan /
  IntakePlanItem 스키마 + IntakeMode enum 전체 값 + 출력 규칙 (JSON 한 객체, 한국어 문자열,
  `extra="forbid"`) 을 LLM 에 강제. `CATEGORY_GUIDANCE` 가 GOAL.md G2 의 5 카테고리
  (지정학·전쟁/군사·경제·정보전·자연재해/지진) 별 표준 인테이크 항목 baseline 을 보유.
  `build_user_prompt` 가 ProjectManifest 의 title/category/duration/topic_summary 를
  `.replace()` 로 치환 (CLAUDE.md C2 — `.format()` 금지 준수). `output_path` 는
  `projects/{pid}/01_intake/intake_plan.json` 로 고정.
- **`web/intake_page_app.py`** — FastAPI 기반 Dynamic Intake Page. `GET /intake/{pid}`
  가 `intake_plan.json` 을 카드 형태 HTML 폼으로 렌더 (외부 템플릿 엔진 없이 인라인 문자열 +
  `html.escape` 로 XSS 방지). `POST /intake/{pid}/submit` 가 form 데이터를 `UserDecision[]` 로
  변환 → `SourceIntake` 로 영속화 + `intake_pending_user → source_collecting` 전이.
  `GET /healthz` 배포 검증용. 추가 의존성: `fastapi>=0.110`, `uvicorn>=0.27`,
  `python-multipart>=0.0.9`.
- **CLI: `plan-intake <pid> [--backend claude|codex]`** — IntakePlannerWorker 1 회 실행 +
  `created → intake_planning → intake_pending_user` 자동 전이. Phase 4 의 자동 task_queue
  도입 전 단계라 합성 `TaskQueueItem` 을 직접 만들어 `worker.run()` 호출.
- **CLI: `submit-intake <pid> --file <path>`** — 검증된 `source_intake.json` 후보를 받아
  영속화 + `intake_pending_user → source_collecting` 전이. 웹 흐름 외에 CLI 로도 결제 가능.
  project_id 불일치 / 스키마 위반 즉시 거부.
- **`tests/test_intake_planner_worker.py`** (13 케이스) — system_prompt 스키마 안내 / IntakeMode
  enum 전체 노출 / `.format()` 비사용 검증 / 5 카테고리 CATEGORY_GUIDANCE 커버리지 / build_user_prompt
  의 manifest 필드 반영 + 미등록 카테고리 폴백 / output_path 고정 / stub mode 통합 (claude + codex
  backend 양쪽 ok / IntakePlan validation_failed 도달성).
- **`tests/test_intake_flow.py`** (6 케이스) — `plan-intake` CLI end-to-end (state 진행 + plan
  파일 생성 + state_history 두 전이 모두 기록), 실패 시 `intake_planning` 에서 멈추는지,
  `submit-intake` CLI end-to-end + project_id 불일치 거부, FastAPI `TestClient` 로
  `POST /submit` end-to-end + `GET /intake/{pid}` HTML 렌더 검증. `REPO_ROOT` 를
  `orchestrator.config` / `workers.base_worker` 양쪽 모두 임시 디렉토리로 monkeypatch
  해 실제 `projects/` 를 건드리지 않음.

### Changed
- **`orchestrator/main.py`** 에 `plan-intake` / `submit-intake` 서브커맨드 추가. `_cmd_plan_intake`
  / `_cmd_submit_intake` 헬퍼 분리. `SourceIntake` import 추가, `manifest_intake_path` 헬퍼 도입.
- **`requirements.txt` / `pyproject.toml`** 에 FastAPI 의존성 3 종 추가. 기존 pydantic v2 +
  textual 등은 변경 없음.
- **`docs/03_AGENT_ARCHITECTURE.md`** Agent 카탈로그 §2 의 Dynamic Intake Planner 행을
  `agents/dynamic_intake_planner.py` → `workers/intake_planner_worker.py (BaseLLMWorker)` 로 갱신.
  Worker 카탈로그 §3 에 Intake Planner 행 추가 (Phase 3, slot 1개, LLM 호출이므로 parallelizable
  ❌ 표기 — Worker Slot Manager 가 별도 slot 으로 격리할지는 Phase 4 결정 사항).
- 모든 Tier 1·2·3 마크다운/HTML `last_synced_with: v0.2.* → v0.3.0` 일괄 갱신 (36 파일).

### Notes
- `schemas/models.py` 의 IntakePlan / IntakePlanItem / UserDecision / SourceIntake 는 Phase 0 부터
  이미 정의되어 있어 본 PATCH 에서 신규 추가 없음. schema_version 1 유지.
- LLM 호출은 `BaseLLMWorker` 의 v0.2.5 견고성 보장을 그대로 상속: parsed_status 4 상태 분리,
  output_path 컨테인먼트, agent 모드 opt-in 가드, prompt/raw/record 3-파일 영속화. IntakePlanner
  는 그 위에서 도메인 system_prompt + CATEGORY_GUIDANCE 만 책임.
- 단위 테스트 총 30 → 49 케이스 (BaseLLMWorker 22 + run 통합 8 + IntakePlannerWorker 13 + 인테이크
  flow 6). DoD 의 "30+ → 35+" 초과 충족.
- v0.2.9 의 미반영 항목 중 "SCHEMA-AP-001 회귀 테스트" 는 본 PATCH 범위 외로 분리 — Phase 3 의
  intake flow 가 정상 전이 케이스를 6 케이스 추가로 cover 하지만, 임의 점프/self-loop 차단에 대한
  명시 회귀는 별도 v0.3.x PATCH 후보.
- C10.1 (MINOR 직전 codex review 1 회 필수) 은 사용자 머신에서 실행. 본 컨테이너에는 codex CLI
  미설치. 머지/태깅 직전 사용자가 `docs/REVIEW_PROMPT.md` 절차로 1 회 실행 후 결과를 본 v0.3.0
  의 후속 PATCH (v0.3.1) 로 흡수하거나 false-positive 합의.

### 알려진 한계 (Phase 4 처리 예정)
- IntakePlannerWorker 가 직접 `task_queue.json` 을 쓰지 않고 합성 task 로 한 번 호출. Phase 4 의
  `task_queue.json` 자동 생성 흐름이 도입되면 일반 worker 처럼 task slot 배정.
- LLM-AP-003 후속 (codex `--sandbox`, scratch dir, `<untrusted_source>` envelope) 은 IntakePlanner
  가 agent 모드 미사용이라 본 Phase 미해당. Phase 4 의 `source_collector_worker` 도입 전 처리.

---

## [v0.2.9] — 2026-05-20

Codex 3차 리뷰 (단일 브랜치, HEAD 78f11bb 검증) 결과 흡수 — High 1 + Medium 1 + Low 1. 새 코드 결함 (`new` defects) 만 처리, 이전 리뷰에서 v0.2.9 후보로 분리해둔 나머지 4건 (TUI reload 분기 보강, current_state 단순화, SCHEMA-AP-001 회귀 테스트, ARCHIVED 중복) 은 Codex 가 본 차에서 모두 "OK 확인" 또는 미언급으로 분류해 별도 후속.

### Fixed (외부 코드 리뷰 3차 반영)
- **(H) `_write_manifest` 의 디렉토리 fsync 실패 신호화** — v0.2.8 의 dir fsync 가 `OSError` 를 통째로 swallow 해서 durability 보장 문구와 runtime 현실이 어긋날 수 있던 문제. `logging.getLogger(__name__).warning(...)` 로 platform·errno·메시지를 포함한 경고 emit. 실패 자체는 여전히 흡수 (rename 은 이미 visible, durability 만 약화) 하되 운영자가 사후 인지 가능. 호출 측이 logging 설정 없으면 root logger 가 stderr 로 보낸다.
- **(M) `orchestrator/main.py:_print_manifest_summary` 타입 힌트** — `# type: ignore[no-untyped-def]` 우회를 제거하고 `manifest: ProjectManifest` 명시. CLAUDE.md C2 "모든 함수 시그니처 타입 힌트 필수" 정합. `from schemas.models import ... ProjectManifest` 추가.
- **(L) `_SLUG_RE` 주석 정합화** — "영문 소문자/숫자/하이픈만 허용" → "영문 소문자·숫자·하이픈·언더스코어를 허용하며, 첫 글자는 영문 소문자 또는 숫자 (선두 `-`/`_` 차단)" 로 실제 정규식 의도와 일치. 코드 독해 혼란 제거.

### Added
- `orchestrator/project_manager.py` 모듈 레벨 `logger = logging.getLogger(__name__)`. 본 저장소 첫 표준 logging 도입.

### Notes
- smoke test 신규: `os.fsync` mock 으로 dir fsync 실패 시뮬레이션 → warning 로그에 `errno=13` / `platform=posix` 포함 검증. 기존 `Path.replace` mock cleanup 회귀 동시 통과.
- 30/30 단위 테스트 회귀 통과.
- 본 PATCH 자체는 외부 리뷰 결과 흡수 PATCH 이지만 코드 변경이 작아 (3 파일, ~30 줄) C10.3 self-exemption 미적용. 머지 전 final 검증으로 다음 codex 리뷰 1 회 추가 권장.

### Codex 3차 리뷰 미반영 항목 (의도적)
- 이전 리뷰 M ("TUI reload PermissionError 분기"): 3차 Codex 가 "분리 명확, 외곽 tick except 로 집계됨" 으로 OK 분류.
- 이전 리뷰 M ("current_state 대입 단순화"): 3차 Codex 가 "ProjectState → str 처리 적절" 로 OK.
- 이전 리뷰 M ("SCHEMA-AP-001 회귀 테스트"): 3차 Codex 도 동일 지적, 다만 본 PATCH 범위에서 분리해 Phase 3 진입 전 별도 PATCH 후보.
- 이전 리뷰 L ("ARCHIVED 중복 표현"): 3차 Codex 미언급. 코스메틱.
- 이전 리뷰 L ("CLAUDE.md C5.2 해석 충돌"): 거버넌스 논의 후보. 본 PATCH 범위 외.

---

## [v0.2.8] — 2026-05-20

Codex 2차 리뷰 (3-way 통합 검수) 의 High 2건 중 코드 측 H2 반영. H1 은 절차 이슈로 별도 처리.

### Fixed (외부 코드 리뷰 2차 반영 — codex `exec review` H2)
- **`_write_manifest` durability + 예외 안전 보강** — v0.2.7 의 atomic write 는 visibility (rename atomicity) 만 보장했고, 전원장애·강제종료 시 마지막 write 유실 가능성이 있었음. tmp write 직후 `flush()` + `os.fsync(fd)` 로 데이터의 디스크 도달을 보장하고, rename 직후 부모 디렉토리 `os.fsync(dir_fd)` (POSIX 한정, Windows 는 `O_DIRECTORY` 미지원이라 best-effort skip) 로 rename 사실까지 durable. 또한 write/replace 도중 예외 발생 시 leftover tmp 파일을 best-effort `unlink` 로 cleanup (실패해도 원본 예외만 전파).
- docstring 을 "atomic visibility" vs "durability" 로 명시적으로 분리하여 향후 reader 가 어떤 보장이 어디까지 적용되는지 명확화.

### Notes
- 본 PATCH 는 외부 리뷰 결과 흡수 PATCH 이지만 C10.3 의 자기 검증 면제는 적용 안 함 (코드 변경 있음, M/L 항목은 다음 PATCH 로 분리하기 위해 본 PATCH 만 다시 검증 가능 상태로 둠).
- 5 케이스 smoke test: 정상 happy path / `Path.replace` 실패 시 tmp cleanup 검증 / corrupt manifest → `ValidationError` / non-JSON → `JSONDecodeError`. 30/30 기존 단위 테스트 회귀 통과.
- Codex H1 (Ij1TX 원본 커밋 `ef49e49` 부재) 은 코드가 아닌 절차 이슈. Codex Cloud 에 비교 브랜치를 fetch 하도록 안내 (다음 리뷰 요청 시 `claude/start-after-handoff-Ij1TX` 명시).
- Codex M/L 항목 (TUI reload `PermissionError`/`OSError` 분기, current_state 대입 조건 단순화, SCHEMA-AP-001 회귀 테스트 추가, _SLUG_RE 주석 정합화, state_machine ARCHIVED 중복 표현, CLAUDE.md C5.2 해석 충돌) 은 다음 PATCH (v0.2.9) 또는 Phase 3 진입 전 일괄 처리 후보.

---

## [v0.2.7] — 2026-05-20

평행 브랜치 (`claude/start-after-handoff-Ij1TX`) 흡수 — SCHEMA-AP 카탈로그 + TUI 라이브 manifest 반영 + atomic write.

배경: 동일 출발점 (`v0.1.5` main) 에서 두 Claude Code 세션이 평행으로 Phase 2 를 구현. 본 브랜치 (`claude/phase-2-finalize` ← `n9ird` 베이스) 가 정본이고, Ij1TX 의 차별점 3 가지만 본 PATCH 로 가져옴.

### Added
- **`docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md`** 신설 + **SCHEMA-AP-001** 등록: `ProjectState` 임의 점프 / self-loop 전이. mitigation 칸에 `LINEAR_SEQUENCE` + `allowed_next_states` + `transition_state` 단일 진입점 + atomic write 의 4중 방어 명시.
- **TUI Job Dashboard 라이브 manifest 반영** — `orchestrator/tui_app.py:_tick_loop` 가 매 tick 마다 `load_manifest` 로 디스크 재로딩. 외부 프로세스 (`python -m orchestrator.main transition ...`) 의 상태 변경을 TUI 가 즉시 따라잡음. 변경 감지 시 Orch CLI Log 에 `state changed: A → B` 한 줄 emit.

### Changed
- **`orchestrator/project_manager.py:_write_manifest`** atomic write 화. `path.write_text` 직접 호출 → tmp 파일에 쓴 뒤 `Path.replace` 로 교체. 외부 reader (TUI 라이브 reload) 가 half-written 상태를 보는 race 차단. POSIX rename / Windows `os.replace` 모두 atomic.
- `docs/ANTIPATTERNS/README.md` SCHEMA-AP 줄을 "Phase 2부터" → "Phase 2 v0.2.7 신설, SCHEMA-AP-001~" 로 갱신.
- 모든 Tier 1·2·3 마크다운 `last_synced_with: v0.3.0 → v0.2.7` 일괄 갱신.

### Fixed
- TUI 가 외부 `transition` CLI 호출 후에도 stale state 를 표시하던 문제.
- `_write_manifest` 의 partial-write race (드물지만 atomic 미적용 시 reader 가 깨진 JSON 을 볼 수 있었음).

### Failure modes added to `_reload_manifest_state`
- `FileNotFoundError` → state=`unknown` 표시, 다음 tick 재시도.
- `JSONDecodeError` / `pydantic.ValidationError` → state=`invalid` 표시, 다음 tick 재시도. 동일 상태 진입 시에만 1 회 stderr 로그 (noise 억제).
- 모든 예외 swallow → tick loop 유지.

### Notes
- 본 PATCH 는 코드 변경이 작아 (3 파일, ~70 줄 추가) C10 self-exemption 가 아닌 정식 codex review 대상. 통합 검수 시 본 브랜치 + n9ird + Ij1TX 3-way 비교를 권장.
- 평행 브랜치 `claude/start-after-handoff-Ij1TX` 는 본 흡수 완료 후 폐기 예정.
- 단위 테스트 5 케이스 smoke (생성·atomic·전이·corrupt manifest ValidationError·non-JSON JSONDecodeError) 모두 통과.

---

## [v0.2.6] — 2026-05-20

### Added
- **CLAUDE.md C10 — 외부 코드 리뷰 (codex review) 의무화**. MINOR/MAJOR/Phase 완료 직전 codex review 1 회 실행 필수. Critical/High 흡수 후에만 버전 증분 허용. 본 절차 자체와 외부 리뷰 결과 흡수 PATCH 는 자기 검증 면제.
- **`docs/REVIEW_PROMPT.md`** 신설 (tier 2 ssot_for=codex-review-procedure). 표준 영문 프롬프트 템플릿, Windows cmd / macOS-Linux 호출 명령어, 결과 해석 가이드 (Critical/High/Medium/Low/Nit), 거짓 양성 처리 절차, 절차의 알려진 한계.
- **`HANDOFF.md`** 의 신규 세션 체크리스트에 codex review 단계 + 30 단위 테스트 통과 확인 명령 추가.

### Changed
- `HANDOFF.md` 의 "1. 지금 어디까지 와 있나" 표에 v0.2.3 / v0.2.4 / v0.2.5 / v0.2.6 행 추가, "2. 다음 작업" 절을 Phase 3 (v0.3.0 — Dynamic Intake Page + IntakePlannerWorker) 로 갱신. 알려진 antipattern 카탈로그 갱신 (LLM-AP-001/002 resolved, LLM-AP-003 resolved-partial).
- "자주 까먹는 규칙" 에 agent 모드 opt-in, codex review 의무, parsed_status 4 상태, exit_code Optional, output_path 컨테인먼트 항목 추가.

### Notes
- 본 PATCH 는 거버넌스 강화 + 다음 세션 인계 정리. 코드/스키마/테스트 변경 없음.
- C10.3 의 self-exemption 에 의해 본 PATCH 자체에는 codex review 를 돌리지 않음.

---

## [v0.2.5] — 2026-05-20

### Fixed (외부 코드 리뷰 1차 반영 — codex `exec review`)
- **(H1) 비0 종료 stdout 보존** — `LLMSubprocessError` 에 `stdout`/`stderr`/`exit_code` 첨부. CLI 가 비0 으로 종료해도 stdout 부분이 `raw.txt` 에 영속화되어 postmortem 가능.
- **(H2) Timeout stdout/exit_code 보존** — `subprocess.TimeoutExpired.stdout/stderr` 를 동일 경로로 보존. `exit_code=None` 으로 "미완료" sentinel 기록.
- **(H3) `parse_failed` 도달 가능** — `model_validate_json` 대신 `json.loads` → `model_validate(dict)` 2 단계로 분리. JSON 파싱 실패와 schema 위반이 별도 `parsed_status` 로 기록.
- **(H4) `LLMCallRecord` 항상 영속화** — `run()` 전체를 `try/finally` 로 감싸 어떤 예외 경로에서도 record/prompt/raw 3 파일이 디스크에 남음. output write 실패 시에도 record 의 `error_message` 에 기록.
- **(H5) `output_path` 컨테인먼트 검증** — `_validate_output_path` 헬퍼 추가. project_dir 밖이면 거부, `task.output_refs` 가 비어있지 않으면 그중 하나와 일치해야 함. CLAUDE.md C4 "writes only own output_refs" 의 코드 단 가드.
- **(M1) claude wrapper subtype 엄격화** — `type=="result"` 인데 `subtype != "success"` 면 `LLMSubprocessError` raise (이전 pass-through 였음 → `validation_failed` 로 흡수돼 원인 추적 어려웠음).

### Added
- **(H6 / LLM-AP-003) agent 모드 opt-in 가드** — `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False`. `llm_mode="agent"` worker 가 `allow_agent_mode=True` 를 명시 선언하지 않으면 LLM 호출 전 즉시 `TaskResult(FAILED)`. prompt injection 면적 축소의 1 단계 가드. 본격 sandbox (CLI `--sandbox`, scratch dir) 는 Phase 3+ 후속.
- **(M3) `tests/test_base_llm_worker_run.py`** 신설 — 4 `parsed_status` 케이스 (ok / parse_failed / validation_failed / subprocess_error 2 종) + agent gate + output_path 컨테인먼트 (project_dir 밖 / output_refs 불일치) 총 8 케이스. 모든 케이스에서 prompt.txt / raw.txt / record.json 3 파일 영속화 검증.
- **(M1) `tests/test_base_llm_worker.py`** 에 wrapper subtype 검증 2 케이스 추가 (`subtype=partial`, subtype 누락).

### Changed
- **(M2) `schemas/models.py:LLMCallRecord.exit_code`** `int = 0` → `Optional[int] = None`. None = "CLI 호출 이전 실패" 또는 "timeout" sentinel. schema_version 1 유지 (호환 변경).
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-003** 신규 등록 (status=`resolved-partial`).

### Notes
- 단위 테스트 총 20 → 30 케이스 (unwrap 22 + run 통합 8). 전부 통과.
- 외부 리뷰 verdict ("방향성 OK, 추적성/상태 분류 정밀화 필요") 의 모든 High/Medium 항목 반영. Low/Nit 은 모두 OK 확인 항목이라 변경 없음.
- Phase 3 의 IntakePlannerWorker 가 BaseLLMWorker 를 상속할 때 보장되는 것: (a) record 가 어떤 실패 경로에서도 남음, (b) output_path 가 project_dir 안에 강제, (c) agent 모드는 의도적 opt-in 필요, (d) 모든 4 parsed_status 가 의미적으로 구분.

---

## [v0.2.4] — 2026-05-20

### Fixed
- **LLM-AP-002 발견 즉시 해결** — `codex exec --json` 의 stdout 은 단일 JSON wrapper 가 아니라 JSONL 이벤트 스트림 (`thread.started` / `turn.started` / `item.completed` / `turn.completed`). 도메인 응답은 마지막 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드. `_unwrap_codex_response` 가 JSONL 을 순회하며 마지막 agent_message 의 text 를 추출하고, markdown fence 가 끼면 `_extract_json_block` 으로 한 번 더 벗긴다.

### Changed
- `workers/base_llm_worker.py:CLI_INVOCATION` 의 codex 매핑 보강:
  - `--skip-git-repo-check` 추가 (project_dir 이 .git 아닐 수 있음)
  - `--color never` 추가 (ANSI 코드 안전장치)
  - agent 모드는 `--cd {project_dir}` 유지
- 검증 환경: codex-cli 0.130.0 (Windows cmd). 실제 한 줄 호출 캡쳐를 fixture 로 보존.

### Added
- `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` 8 케이스 — 실 캡쳐 / markdown fence / 다중 agent_message / tool_call 등 미지 item type 무시 / agent_message 없음 → `LLMSubprocessError` / 단일 JSON pass-through / non-JSONL pass-through / 빈 입력. 총 단위 테스트 13 → 20 케이스.
- `LLM_ANTIPATTERNS.md` 에 **LLM-AP-002** 신규 등록 (status=resolved, 발견 즉시 해결).

### Notes
- 알려진 한계: 다중 turn / `--output-schema` / `--output-last-message` 같은 더 견고한 codex 옵션은 도입하지 않음 (단순성 우선). Phase 3 에서 schema 강제 도입 재검토.
- 본 fix 로 v0.2.2 시점의 "codex 는 별도 후속" 항목이 해소됨. Phase 3 의 IntakePlannerWorker 가 backend 를 claude/codex 어느 쪽으로 설정해도 BaseLLMWorker 가 정상 동작.

---

## [v0.2.3] — 2026-05-20

### Fixed
- **LLM-AP-001 구조적 조치** — `BaseLLMWorker` 가 `claude -p ... --output-format json` 의 wrapper (`{type:result, subtype:success, result:"...", ...}`) 를 벗긴 뒤 `response_model.model_validate_json` 을 호출하도록 변경. wrapper `is_error=True` 면 `LLMSubprocessError` 로 변환. `result` 문자열 안의 markdown code fence (```` ```json ... ``` ````) 도 자동 제거.
- `raw.txt` 영속화는 unwrap 전 stdout 그대로 유지 → 디버깅 추적성 보존.

### Added
- `tests/__init__.py`, `tests/test_base_llm_worker.py` — 13 케이스 단위 테스트 (extract_json_block 5 / claude wrapper 7 / codex pass-through 1). `python -m unittest tests.test_base_llm_worker` 통과.
- `workers/base_llm_worker.py` 에 모듈 레벨 헬퍼: `_unwrap_claude_response`, `_unwrap_codex_response`, `_extract_json_block`. `BaseLLMWorker._unwrap_response(raw)` 가 `self.llm_backend` 로 dispatch.

### Notes
- codex CLI wrapper 는 v0.2.3 시점 미검증 → pass-through. 실제 호출 가능 환경 확보 후 별도 작업 (LLM-AP-002 후보) 으로 분리.
- LLM-AP-001 status `active` → `resolved`.

---

## [v0.2.2] — 2026-05-20

### Added
- **`workers/base_llm_worker.py:BaseLLMWorker` 코드 도입** (ADDENDUM_04 §4 의 정식 구현).
  - 클래스 변수: `llm_backend ∈ {"claude", "codex"}`, `llm_mode ∈ {"response", "agent"}`, `system_prompt`, `response_model`.
  - 추상 메서드: `build_user_prompt(args, task)`, `output_path(args, task)`.
  - `_invoke_llm` 가 backend/mode 별 `CLI_INVOCATION` 매핑으로 subprocess 호출. `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 흡수.
  - `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회 (smoke test 전용).
  - 전 호출이 `projects/{pid}/llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 3 파일로 영속화.
- `schemas/models.py` 에 `LLMCallRecord` Pydantic 모델 추가. `parsed_status ∈ {"ok", "parse_failed", "validation_failed", "subprocess_error"}`.
- `workers/dummy_llm_worker.py` 신설 (`DummyLLMResponse` 응답 모델 포함). smoke test 전용.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 의 첫 항목 **LLM-AP-001** 등록 — `claude -p ... --output-format json` 응답이 wrapper JSON (`type/subtype/result/usage/uuid` 등) 으로 감싸여 있어 그대로는 도메인 Pydantic 모델 검증 통과 안 함. 구조적 조치 v0.2.3 patch.

### Changed
- `docs/ADDENDUM_04 §4` 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 으로 구체화.

### Notes
- smoke test 4 케이스 (정상 stub / 잘못된 JSON / 스키마 위반 / 실 claude CLI) 모두 의도대로 동작. LLMCallRecord 4건 영속화 확인.
- `BaseLLMWorker` 는 새 Worker 베이스이므로 C5.4 의 MINOR 사유 ("새 Worker 추가") 에 해당. MINOR 0.2.1 → 0.2.2.

---

## [v0.2.1] — 2026-05-19

### Added
- **Subscription LLM Bridge 패턴 정식 문서화** — 본 시스템은 LLM API 키를 사용하지 않고, 사용자가 이미 구독 중인 `claude` (Claude.ai) 와 `codex` (ChatGPT Plus/Pro) CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정 정립.
- `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설. GOAL.md G4 와 동등한 강제력으로 운용. `BaseLLMWorker` 인터페이스 명세, 호출 모드 (`response` / `agent`), 백엔드 선택 가이드, 추적성 (`projects/{pid}/llm_calls/{call_id}.json`), 에러 모드 정의.
- `docs/03_AGENT_ARCHITECTURE.md` §4.5 에 `BaseLLMWorker` 계약 요약 추가. §4 베이스워커 안내문에 "LLM 호출은 `BaseLLMWorker` 상속 필수" 명시.
- `CLAUDE.md` C6 안티패턴 카테고리에 `LLM-AP-N` 추가.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설 (항목은 Phase 3 첫 실 호출부터 누적).
- `docs/ANTIPATTERNS/README.md` 인덱스에 `LLM-AP` 행 추가.

### Notes
- 본 변경은 **G4 본문은 건드리지 않는** PATCH. ADDENDUM_04 가 G4 와 동등한 강제력을 갖도록 본문에 명시. v1.0.0 시점에 G4 #13 으로 정식 흡수 (MAJOR 증분).
- 코드 변경 없음. `BaseLLMWorker` 코드는 v0.2.2 patch 또는 Phase 3 시작 시점에 도입.

---

## [v0.2.0] — 2026-05-19

### Added
- **Phase 2 완료: Project Manager / State Machine**.
- `orchestrator/state_machine.py` 신설. `LINEAR_SEQUENCE` 가 docs/02 §4 의 24개 상태 선형 흐름을 SSOT 로 보유. `allowed_next_states` / `validate_transition` 순수 함수 제공.
- `orchestrator/project_manager.py` 신설. `project_manifest.json` 의 유일한 쓰기자. `new_project` / `resume_project` / `transition_state` 공개 API.
- `schemas/models.py` 에 `StateTransition` 모델 추가, `ProjectManifest.state_history` (append-only) 필드 추가. schema_version 은 1 유지 (optional 필드 추가).
- CLI 명령 `new-project <pid> --title ... --category ... [--duration-min] [--topic-summary]`, `resume <pid>`, `transition <pid> --to <state> [--reason]` 정식 구현.
- 전이 규칙: 선형 다음 상태 또는 `archived` 만 허용. 동일 상태 전이 / 임의 점프는 명확한 한글 메시지와 함께 `ValueError` (CLI exit=2).

### Changed
- `orchestrator/command_center.py` 가 `project_manager.load_manifest` 를 통해 manifest 를 read-only 로 로드하도록 정리. raw json 파싱 코드 제거.
- `orchestrator/main.py` 의 `new-project` / `approve` placeholder 문구 제거, 실 구현으로 교체.

---

## [v0.1.5] — 2026-05-19

### Removed
- `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에서 `test/graph-demo` 항목 삭제 (브랜치 자체가 삭제됨).
- `COMMIT_DESCRIPTIONS` 에서 `0159299` 엔트리 삭제 (해당 commit 이 도달 가능한 브랜치가 없어 dead code).

### Changed
- `test/graph-demo` 원격 브랜치 사용자 측에서 삭제 완료 (v0.1.3 그래프 분기 시각화 검증 종료).

---

## [v0.1.4] — 2026-05-19

### Added
- `docs/branches.html` 에 `COMMIT_DESCRIPTIONS` 맵 추가. 영어로 작성된 과거 커밋의 한글 설명을 SHA(앞 7자) 기준으로 override. 신규 커밋은 처음부터 한글로 작성하면 맵 갱신 불필요.
- `BRANCH_PRIORITY` + `sortBranchRefs` 헬퍼 추가. 같은 SHA 에 여러 브랜치가 가리킬 때 라벨 표시 우선순위 결정 (main → develop → release/ → feature/ → test/ → claude/ → 그 외 알파벳).
- `BRANCH_DESCRIPTIONS` 에 `test/graph-demo` 항목 추가 (임시 검증 브랜치).

### Fixed
- 같은 SHA 를 두 브랜치가 가리킬 때 `main` 라벨이 안 보이고 부차 브랜치 라벨만 보이던 문제 수정. (`sortBranchRefs` 가 main 을 항상 앞에 배치)

---

## [v0.1.3] — 2026-05-19

### Added
- `HANDOFF.md` (Tier 1) 신설. 다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 인계 문서. 현재 상태, Phase 2 후보, 체크리스트, 자주 까먹는 규칙 정리.
- `docs/branches.html` 에 `@gitgraph/js` (jsDelivr CDN) 통합. 모든 브랜치를 단일 SVG git graph 로 렌더. 브랜치가 갈라지면 자동으로 가지 그림이 나옴.
- 사이드 패널이 등록되지 않은 브랜치를 자동 감지해서 "설명 미등록" 경고 카드로 노출 (한글).

### Changed
- `docs/branches.html` 의 데이터 모델을 commit-graph 중심으로 재작성. 브랜치별 commit 을 전역 SHA 맵으로 통합, parents 필드 활용해 토폴로지 보존. 모든 브랜치 commit fetch 병렬화 (`Promise.all`).

---

## [v0.1.2] — 2026-05-19

### Added
- `docs/index.html` 추가. 루트 URL (`/`) 접근 시 `/branches.html` 로 즉시 리다이렉트 (meta-refresh + JS 양쪽).

### Fixed
- Vercel 배포에서 루트 URL 이 `404: NOT_FOUND` 를 반환하던 문제 수정. `vercel.json` 의 `rewrites` 룰이 `outputDirectory: "docs"` 와 함께 쓰일 때 안정적이지 않아 실제 `index.html` 파일로 대체.

### Changed
- `vercel.json` 에서 `rewrites` 블록 제거 (정적 `index.html` 로 충분).

---

## [v0.1.1] — 2026-05-19

### Added
- `vercel.json` 루트 추가. Vercel 로 `docs/` 정적 호스팅 (Private 저장소 호환). 푸시마다 자동 재배포.
- `docs/branches.html` 에 Personal Access Token 입력 다이얼로그 추가. 토큰은 브라우저 localStorage 에만 저장. Private 저장소 GitHub API 호출에 사용.
- README 에 Vercel 설정 절차 + PAT 발급 절차 안내.

### Changed
- GitHub default branch 가 `main` 으로 통합됨에 따라 로컬 브랜치도 `main` 으로 rename, `branches.html:BRANCH_DESCRIPTIONS` 도 갱신.
- `branches.html:loadVersion` 이 raw.githubusercontent.com 대신 `/contents/VERSION` API 를 사용하도록 변경 (Private 저장소에서도 Bearer 인증으로 동작).
- 모든 Tier 1·2·3 마크다운/HTML 의 `last_synced_with: v0.1.0 → v0.1.1` 동기화.

### Fixed
- 없음 (Phase 1 PIPELINE-AP-006 은 v0.1.0 안에서 fix 됨).

---

## [v0.1.0] — 2026-05-19

### Added
- 저장소 초기화 (Phase 0)
- Tier 1 거버넌스 문서: `README.md`, `GOAL.md`, `CLAUDE.md`, `DOCS_GOVERNANCE.md`
- Tier 3 운영 문서: `CHANGELOG.md`, `DEVLOG.md`, `WORKFLOWS.md`
- Tier 2 스펙 문서 19종 (`docs/00_~16_`, `docs/ADDENDUM_01~03`)
- Antipattern 카탈로그 골격 (`docs/ANTIPATTERNS/README.md`, `TTS_ANTIPATTERNS.md`, `PIPELINE_ANTIPATTERNS.md`)
- 프로젝트 스캐폴딩: `pyproject.toml`, `requirements.txt`, `config.yaml`, `run_pipeline.bat`, `.gitignore`, `.githooks/commit-msg`
- Pydantic 스키마 모듈 `schemas/models.py` (project_manifest, task_queue, worker_slot, task_result 등)
- **Phase 1 MVP**: Orchestrator Command Center (Textual TUI)
  - `orchestrator/command_center.py` — TUI 진입점
  - `orchestrator/tui_app.py` — Orch CLI Log + Job Dashboard + Worker Slot 4개 패널
  - `orchestrator/worker_slot_manager.py` — Worker subprocess 배정
  - `orchestrator/log_router.py` — Worker stdout/stderr 라우팅
  - `orchestrator/dashboard.py` — 작업 현황 집계
  - `orchestrator/config.py` — config.yaml 로더
  - `workers/base_worker.py` — Worker CLI 공통 베이스
  - `workers/dummy_worker.py` — Phase 1 검증용 더미 워커
- 데모 프로젝트 `projects/demo/`와 4개 dummy task가 포함된 `task_queue.json`
