---
id: R-0146
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G12"
version: v5.1.0
commit: 485b1bf
status: in_progress
---

# G12 결정 요청 7건 — 차트 아일랜드 카메라·레인 높이·겹침·패널 범위·사진 출처·원문 없는 기사·보조 무대

§0(485b1bf) 끝, §G·§A·§D 진행 중입니다. 아래 7건은 D-0121·D-0123 이 decision_request 로 지목했거나 실측에서 새로 나온 쟁점입니다.
결정 전에는 해당 부분을 만들지 않습니다(README §6.4-3).

## Q1. 차트 아일랜드의 카메라(w·date)를 어디에 적는가
**쟁점**: backdrop 무대 카메라는 `{}`(이동 없음, D-0123 §1)입니다. 그러면 차트 아일랜드 안 시간축 뷰포트의 w·date 는 어디서 오는지 정해야 합니다.
현재 `engine/direction.build` 는 숏 무대 ≠ 주 무대면 "보조 무대 렌더는 아직 없다" 오류입니다.
- **A. `stage: timeline` 숏 = 차트 아일랜드 카메라.** 주 무대 backdrop, 시간축 숏은 아일랜드 뷰포트만 움직입니다. 기존 숏·카메라 빌더·camera_suggest·§A 검사를 그대로 씁니다. 위험: "숏 무대 ≠ 주 무대" 의미가 아일랜드 한정으로 바뀝니다(문서 1줄 필요). 되돌리기: 숏 해석 한 곳.
- **B. 아일랜드 이벤트 안 `view: [{at, date, lane?, w, dur}]`.** 이벤트가 자기 카메라를 가집니다. 위험: 카메라 빌더·검사·프롬프트 예시를 새로 만들고, 두 카메라 문법이 생깁니다.
- **Opus 권고: A**(②·③ — D-0121 §B "카메라·축 로직은 그대로(상자 = 뷰포트)", 새 문법 0).

## Q2. 아일랜드 안 레인 높이
**쟁점**: fed 레인 3 × `lane_h 96` = 288px. 아일랜드(480p 높이의 62 % ≈ 298px)에서 제목·눈금 자리를 빼면 약 230px 입니다. 안 들어갑니다.
- **A. 자동 맞춤**: `y_px_per_unit = min(lane_h, 아일랜드 레인 영역 ÷ 레인 수)`. 레인 수가 바뀌어도 넘치지 않습니다.
- **B. 규칙 값 `island.lane_h`**(예 72) + 넘치면 오류.
- **C. 96 유지 + 카메라 y 세로 스크롤**(현재 `frame_y1` 클램프).
- **Opus 권고: A**(① 규칙 값 하나 없이 넘침 0, P6 — 조용한 잘림 없음. 글자 크기는 그대로라 glyph_size 영향 0).

## Q3. 아일랜드 겹침 규칙(checks `island_overlap` hard)
- **A.** 같은 순간 보이는 아일랜드 상자(슬라이드 끝 제자리, 그림자 제외)끼리 교차 면적 > 0 = hard. 자막 구역(`reserved_zones.subtitle`)과 교차도 hard. 카드·배지는 아일랜드가 아니라 기존 예약 영역 규칙.
- **B.** A + 그림자·슬라이드 경로까지 포함(더 엄격, 등장 중 스침도 오류).
- **Opus 권고: A**(①, 페이드 중 스침은 시각 결함이 아님).

## Q4. 패널 통일 범위(D-0123 §1 "패널은 island 규칙 값으로 통일")
**쟁점**: hormuz 골든에 패널 5종이 있습니다. 전 무대에서 패널 radius·fill·edge 를 island 값으로 바꾸면 골든 패널 컷이 바뀝니다(D-0123 §4 "골든 무변경"과 충돌).
- **A.** G12 는 backdrop 무대 위 패널만 island 상자 규칙. mercator·timeline 패널 수치 무변경.
- **B.** 전 무대 통일 + 골든 expected_deltas.
- **Opus 권고: A**(① + D-0123 §4 골든 무변경).

## Q5. 배경·프레스 사진 출처
**실측**: 미디어 레지스트리의 권리 기록 있는 fed 사진은 연준 Flickr(PDM, license 10) 3장입니다 — 전부 9.16·7.29 기자회견 연단 사진(`fed_presser_0916`, `_0916_b`, `_0729`). hormuz 기사 2건(Reuters 9.4, Korea Herald 9.7)에 맞는 권리 기록 공식 사진은 없습니다.
- **A.** fed: 연준 이사회 Flickr(license 8/9/10 만, `tools/media_fetch` flickr 경로)에서 에클스 빌딩 외관·FOMC 회의실 등 2~3장 추가 등재 → 5~6장. hormuz: 블러 무대 폴백(`article.press: none`).
- **B.** fed: 등재된 3장만(최소 3 충족, 같은 연단 사진 반복). hormuz: 폴백.
- **C.** A + 백악관 퍼블릭 도메인 사진(트럼프 대통령의 금리 압박 장면용).
- **Opus 권고: A**(C9 경로 재사용, 3장만으로는 장면 전환이 같은 연단 사진 교대라 D106 "주제가 바뀔 때 전환"의 의미가 약합니다). C 는 발언 장면 적합성을 사람이 봐야 해서 이번엔 제외 권고.

## Q6. 원문 헤드라인이 없는 기사
**실측**: D-0121 §C 는 헤드라인 = 원문 언어 verbatim 입니다. fed 2건은 레지스트리 `title` 에 영어 원문이 있습니다(CNN 12단어, Fox Business 13단어, 15단어 미만 조건 충족). hormuz 2건(Reuters·Korea Herald)은 `pending_source: 원문 URL 미확보`라 원문 헤드라인이 저장소에 없습니다. 지어낼 수 없습니다.
- **A.** 레지스트리에 `headline_original`(선택) 필드 추가. 없으면 한국어 번역 헤드라인(현 `headline`)을 세리프로 쓰고 source 줄에 "헤드라인 번역" 표기, sub 는 현 `sub`. provenance `article.headline: translated`.
- **B.** 원문 없는 기사 = 오류(렌더 중단). hormuz 기사 2건은 원문 확보 전까지 G12 클립 불가.
- **Opus 권고: A**(③ 저장소 실측 + P6 기록, 사실 정확성 유지 — 번역임을 화면에 밝힘). 원문 확보는 사용자 몫으로 남깁니다.

## Q7. backdrop 보조 무대(지도 주 무대 안 삽입) 렌더 범위
**쟁점**: D-0123 §2 는 "mercator 주 무대에 backdrop 보조 무대 삽입 가능"이라 적었습니다. 보조 무대 렌더 자체는 아직 없습니다(`direction.build` 오류). G12 산출물(fed = backdrop 주 무대, hormuz = 기사 이벤트만)에는 필요 없습니다.
- **A.** G12 는 backdrop 을 주 무대로만. 보조 무대 삽입은 문법·검사(stage.max_secondary·continuity)만 두고 렌더는 다음 Phase. 오류 문구 유지.
- **B.** G12 에서 보조 무대 렌더까지.
- **Opus 권고: A**(④ 범위 — D-0121 산출물에 불필요, 보조 무대 렌더는 카메라·전환 설계가 따로 필요).

## 막히는 범위
- **막힘**: 차트 아일랜드 뷰포트(Q1·Q2), `island_overlap` 검사(Q3), backdrop 위 패널(Q4), fed 사진 추가 수집(Q5), 기사 v2 헤드라인 줄(Q6).
- **계속함**: §G 버전 도장, §A 축 스케일 검사, §D 발음 사전, backdrop 무대 뼈대(레지스트리 세 곳·블러 사진 시퀀스·`backdrop` 이벤트·`backdrop_rights`·`backdrop_repeat`·`stage_choice`·default_stage), 기사 v2 레이아웃(theme·덮개·세로 선·페이드), 옛 오른쪽 카드 경로 삭제.

§7 사용자 고유 결정 해당 없음(Fable 전결). Q6 의 원문 확보는 사용자 작업이 필요할 수 있습니다.
