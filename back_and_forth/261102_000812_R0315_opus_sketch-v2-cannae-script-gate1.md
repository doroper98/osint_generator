---
id: R-0315
from: opus
to: fable
kind: phase_report
responds_to: [D-0607, D-0608]
phase: "E9"
version: v7.4.0
commit: HEAD
status: needs_decision
---

# D-0608 단계 1(스케치 v2 보정) · 단계 2(W6-1 칸나이 원고, 게이트 ① 자료) · 결정 요청 셋

## 1. 스케치 v2 — artifacts `b49c90d3`, `war_history/sketch_v2/`

칸나이·인천 mp4·시트·provenance·spec·media·RIGHTS·MD5SUMS 를 올렸습니다. 수치는 렌더 뒤 provenance 입니다.

| 검사 | 칸나이 v1(R-0302) | 칸나이 v2 | 인천 v1 | 인천 v2 |
|---|---|---|---|---|
| SK-W6 카드 덮임(hard) | 9.3초 | **0** | 4.6초 | **0** |
| SK-W5 화면 밖 글자(hard) | 159프레임 | **0** | 4프레임 | **0** |
| SK-C2 겹침(warning) | 395프레임 | 376프레임 | 546프레임 | **31프레임** |

- 칸나이 SK-C2 376프레임의 대부분은 전술 숏(t≈26~35)의 초승달 블록끼리 맞닿은 것입니다(이름 없는 블록 예약 상자). 진형이 실제로 붙어 있어서입니다. 9~15초는 작전 지도 지명 줄입니다. 더 줄이려면 이름 없는 블록을 겹침 입력에서 빼야 하는데, SK-W6 입력과 같은 상자라 판단을 받겠습니다(§4-③).
- 고친 것(커밋 e029c8f7 이후):
  - 전쟁사 스케치 기본 테마 relief(`sketch.war.default_theme`, D-0607 ③). provenance features_drawn 에 `theme:relief`.
  - 라벨 LOD(`sketch.war.lod`) — 물러난 숏에서 부대 이름이 흐려져 접히고 지명 유래 줄은 한 줄. 접힌 수는 `lod:*` 로 남습니다(인천 6).
  - 큰 회전(> `unit.turn_first_deg` 30°)은 방위 먼저, 크기는 뒤 절반(쐐기 늘어짐).
  - 오른쪽 끝을 넘는 지명 라벨은 핀 왼쪽 오른쪽 맞춤(글자를 빼지 않음, `label_flip_left`).
  - 없는 '현재 이름' 줄을 예약하던 버그 제거(SK-C2 의 큰 몫).
  - 인천 부대·지명 간격과 카메라 조정(개략 범위 안).
- 인천 clip 층: 미 국방부 기록 영화 Operation Inchon(1952, DIMOC PIN 22337, archive.org CC0) 494~502초 상륙 장갑차.
  - 원본(512kb 파생본 320×240)은 media_src 에 보존(md5 99d10364). 카드는 원폭 그대로(`card.clip_px_w` 320).
  - "자료 영상" 표기. 정확한 해안·날짜가 영상에 없어서입니다.
  - DIMOC 20265(Combat Bulletin 102, CC0)는 받아 두었고 쓰지 않았습니다.
  - NARA 111-ADC-8251 은 archive.org 라이선스 칸이 비어 있습니다. NARA 카탈로그는 이 세션에서 막혀 있어(프록시 403) 권리 미확인으로 쓰지 않았습니다.
- 칸나이 주화: Sailko 사진 원본 수신(Commons 429 가 약 45분 이어졌습니다). source_hash 42caacf6, 도안 대조 = 월계관 두상·코끼리 기수.
- D710 보강: 입체 유물 사진에 유물 나이 PD 분류만 있으면 `photo_pd_basis` 가 필수입니다. 칸나이 흉상(Alinari 1900년경)에 사진 자체 PD 근거를 적었습니다. 해당 레코드는 그 한 건입니다.

## 2. 이란 장치 체리픽(25bc3915) — fbe77f1d

- element_hold·media_overlap hard 를 가져왔습니다. 검사 항목 125(우리 123 + 2), regression_ref_checks 는 합집합입니다.
- 전쟁사 증거 카드는 엔진 이벤트 photo(작품·기록)·quote(사료)라 types 에 이미 듭니다. 바꾼 것은 없습니다.
- UF-170 행은 넣지 않았습니다. 그 장치 시험(`tests/test_gates_pipeline.py::...no_status_labels`)이 이 브랜치에 없어서입니다. 이란 병합 때 들어옵니다.

## 3. W6-1 칸나이 원고 — `projects/cannae_216bc`, 게이트 ① 자료 `gate1_view.txt`

- 사료: archive.org 미국 PD 영역본을 장 단위 소스 10개로 넣었습니다. 폴리비오스 III.107~118(Paton 1922), 리비우스 XXII.43~51(Foster 1929 — 1929 미국 발행, 2025년부터 PD). 작품 정보 1개는 Commons 파일 정보 그대로입니다.
  - 첫 시도는 소스 두 개(각 4~5만 자)였습니다. 검증 입력 상한(`verification.body_max_chars` 12000)에 잘려 주장이 전투 초반까지만 나왔습니다(초안 1, 기록 커밋). 장 단위로 다시 접수했습니다.
- 검증: claims 40(verified 35·disputed 4·unverified 1). 폴리비오스·리비우스가 다른 곳(우익 지휘관 한노/마하르발, 전사자·포로 수, 바로와 달아난 기병 70/50)은 disputed 로 잡혔습니다. 원고는 둘 다 귀속해 나란히 씁니다.
- 원고 v2: 61문장, 예상 414초(약 6분 54초)입니다. 목표 4~6분을 넘습니다(§4-②).
- 구성: cold_open 4 · prelude 9 · deployment 16 · encirclement 16 · aftermath 12 · ending 4.
- ScriptWorker 출력에 손댄 것(사실·수치 추가 없음, 파일 머리 주석에 기록):
  - 린트 오류 6·경고 4 를 해소했습니다(논쟁 주장 귀속, force: 인용, 군더더기 1문장 삭제, 과거 시제).
  - aftermath 막 도입 두 문장(bridge·intro)을 넣었습니다.
- 린트 0·0, slop 0 입니다.
- 병력·사상자: `forces.yaml` 레코드 5(영역본 문장 그대로).
  - rome_killed(폴리비오스 III.117.4, 약 7만)·rome_killed_livy(XXII.49, 48,200)
  - carthage_strength(III.114.5, 5만 — 리비우스 XXII.46 과 같음)·carthage_killed(III.117.6, 5,700 = 합)·rome_captured(III.117.3)
  - 숫자가 든 사상자 문장은 전부 force: 를 인용합니다.
  - 절 번호는 Paton 영역에 절이 없어 그리스어 쪽 여백 번호로 맞췄습니다(OCR 근거, 레코드 주석).
- 작품: 카푸아 흉상(1667 발견)·트럼불(1773) 두 점이 문장에 있습니다. 주화·클로스 판화는 문장에 없습니다. 연출에서 캡션 + 미술사 한 줄로 보입니다.
- 지명 유래 레코드(칸나이, 확신도 미상)는 원고 문장에 들어가지 않았습니다. 연출 marker 의 지명 유래 줄로 보입니다.
- 이 단계에서 고친 공용 코드: `script/labels.py` 가 `force:` 를 claim 밖 참조로 봅니다. 전쟁사 W2 누락이고 `series:` 와 같은 처리입니다.
- 감독 검토 뒤 사용자 게이트 ① 로 보내 주십시오. 승인 전에는 음성·연출·콘티 판에 착수하지 않습니다.

## 4. 결정 요청

① **force 레코드의 범위 띠(band)** — 현대 학술 추정을 이 세션에서 열람하지 못했습니다(위키백과·학술 사이트 프록시 차단). Dodge 『Hannibal』(1891) archive.org 본은 1권뿐이라 칸나이가 없습니다.
- 지금 band 는 "고대 사료 간 범위"입니다. 전사자 43,500~70,000 은 Foster 1929 각주의 사료 비교에서 왔습니다. 출처 칸에 "현대 학술 추정 아님"을 적었습니다.
- 선택지:
  - (가) 이대로 두고 화면·내레이션에 "사료마다 다르다"만 말한다.
  - (나) 감독이 열람 가능한 현대 추정(학술서·논문)을 지정해 준다.
  - (다) 규칙 `war_history.casualty.band_required` 를 "사료 간 범위도 허용"으로 개정(사람 승인)한다.
- 로마군 병력 레코드는 사료 하나(폴리비오스)라 만들지 않았습니다. 원고 cold_open_1 의 "보병 약 8만 명, 기병 6천여 명"은 병력·사상자 낱말이 없어 린트가 걸지 않습니다. 그래도 force 인용을 붙이려면 ①의 결정이 필요합니다.

② **길이 414초** — 목표 4~6분을 넘습니다. 줄이면 deployment(16문장) 지휘관 배치 문장부터 줄이겠습니다. 이대로 사용자 게이트 ① 에 보낼지 결정을 부탁드립니다.

③ **칸나이 SK-C2** — 이름 없는 부대 블록끼리 맞닿은 것도 겹침으로 셉니다. 겹침 입력에서 빼면(SK-W6 입력은 그대로) 수치가 진형 실태를 덜 왜곡합니다. 바꿀지 결정 부탁드립니다. 경고라 영상은 막지 않습니다.

④ **제목의 날짜** — 프로젝트 제목 "칸나이 — 기원전 216년 8월 2일"의 8월 2일은 이번 사료(폴리비오스·리비우스 발췌)에 없습니다. 다른 고대 기록에서 온 날짜로 보이나, 이 세션에서 출처를 확인하지 못했습니다. 원고 제목은 "칸나이, 기원전 216년"이고 문장 날짜도 -216 입니다. 스케치 날짜 뱃지는 -216.08.02 입니다. 원고·연출에서 8월 2일을 쓰려면 출처 소스를 하나 더 넣어야 합니다. 넣을지 결정을 부탁드립니다.

## 5. 검증

- 관련 시험: test_sketch_war·test_war_rights(15)·test_war_arms·test_sketch_common·anti_inertia/test_sketch_no_literals → 통과.
- 체리픽 뒤 test_element_hold·test_regression_refs·test_checks·test_user_feedback_guards·test_provenance_e2e → 통과(UF-170 제외 뒤).
- **전체 pytest 는 아직입니다.** 오늘 -n 3 실행은 렌더와 CPU 를 다퉈 7%에서 멈췄고 제가 중단했습니다. 이 R 직후 다른 작업 없이 1회 돌려 이름까지 다음 R 에 올립니다. 그동안 rules·schemas 는 고치지 않습니다.

## 6. 남은 일

1. 전체 pytest 1회(지금) → 결과 R.
2. §4 결정 반영.
3. (사용자 게이트 ① 검토 중) W5 디자인 시트·등록(relief 정식·terrain3d stages·픽토그램·휘장 — 3D 휘장 포함)·BGM decision_request.
4. 게이트 ① 승인 뒤 음성·연출·콘티 판.
- 미등록 패치 없음.
