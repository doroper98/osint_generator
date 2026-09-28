<!--
tier: 3
last_synced_with: v3.1.0
ssot_for: [report-phase6_9-hormuz_ai-qa_loop]
depends_on: [docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, orchestrator/ai_direction.py]
last_review: 2026-09-28
-->
# hormuz_ai — AI 연출 · 시각 검수 루프 기록 (Phase 6.9 작업 10 (b))

입력은 v3『호르무즈와 한국』의 **원고(script.yaml)·plan.json·자산뿐**이다. direction.yaml 은 없다.
DirectorWorker 가 연출을 쓰고, 코드가 checks → 시트 → VisualQA → ReviseDirection 루프를 돌렸다(상한 rules `qa_checks.visual_qa_loop_max` = 2).
실행: `python tools/ai_direction_run.py projects/hormuz_ai --preview golden` (파이프라인 advance 와 같은 run_worker·qa_loop·run_stage).
시트는 모두 골든 25 앵커 컷이다 — v3 골든과 같은 순간을 비교하기 위해서.

## 결과 한눈에

| 판 | 만든 것 | checks hard / warn | 시각 검수 | 시트 |
|---|---|---|---|---|
| direction.v1 | 연출가(재요청 0, 224초) | 0 / 0 | revise · hard 1 · soft 8 | `sheet_v1.jpg` |
| direction.v2 | 수정 1회차(changelog 9, 재요청 1 — JSON 괄호) | 0 / 0 | revise · **hard 0** · soft 5 | `sheet_v2.jpg` |
| direction.v3 | 수정 2회차(changelog 5) | 0 / 0 | revise · hard 2 · soft 6 | `sheet_v3_final.jpg` |

- 루프는 상한(수정 2회)에서 끝났고 결정적 검사 hard 0 이라 게이트 ②로 갈 수 있는 상태다(`ai_run_summary.json`).
- **2회차 수정이 오히려 나빠졌다.** 공습 클립을 1회차에 지적받은 슬롯(panel_gap)으로 되돌렸고, 호르무즈 마커 라벨을 left 로 뒤집어 화면 왼쪽 끝에서 25px 잘렸다.
  → 진동·판 선택·마커 잘림 검사는 R-0057 로 결정 요청.
- 3회 연속 지적(이재명 뱃지가 타이틀 카드 밑에 남음)은 수정 LLM 이 고칠 수 없었다. 타이틀 카드가 open 장면 **안**에 있어
  `scene_end open` 기준으로는 아무리 당겨도 남는다. 수정 입력에 시각표가 없어서다(R-0057 쟁점 1).
- 수정 LLM 은 연출 필드로 못 고치는 지적(클립 원본 검은 영역, 패널 글자 크기·높이)을 "변경 없음 — 렌더러 몫"으로 정직하게 남겼다.
  이 셋(niovi 클립 레터박스, versus 패널 여백, timeline 라벨 크기)은 렌더러·미디어 과제로 넘긴다.
- 원고에 없는 사실을 새로 쓴 경우는 없었다(수정 v3 의 카드 문구는 원고 문장 그대로, changelog 에 명시).

## 검수 LLM 의 판정 흔들림 (참고)
같은 direction.v1 을 네 번의 실행에서 검수했다(attempts/ + 이번). 지적 수 11·10·8·9, hard 는 네 번 모두 1건(clip:strikes)으로 **hard 는 안정**,
soft 는 절반쯤 겹친다. 이번 실행의 검수 v1 은 근거 문장을 영어로 썼다(프롬프트는 한국어, v2·v3 는 한국어) — 언어 고정 규칙 한 줄 후보.

## 앞선 실행이 멈춘 이유 (코드 버그 — 모두 수정)
| 실행 | 멈춘 곳 | 원인 | 수정 |
|---|---|---|---|
| 0 | 연출가 check_parsed | 저장 전 점검이 place 슬롯을 버려 뱃지 lon/lat 누락으로 거부 | PIPELINE-AP-007, `load_project(direction=)` |
| 1 | 시각 검수 기록 | LLMCallRecord.mode 에 vision 없음 | LLM-AP-007 |
| 2 | 수정 불변 검사 | "badge:이재명" ↔ "badge\|person\|이재명\|앵커" 형식 불일치, 컷 표지 미해석 | PIPELINE-AP-008, `engine.qa.resolve_refs` |
| 3 | 수정 JSON | 점 슬롯에 영상·사진(재요청 소모) 후 JSON 괄호 초과 | 수정 프롬프트에 슬롯 표 추가(재실행 4에서 슬롯 오류 0) |

## 회차별 판정·changelog

### 검수 v1 — direction.v1 · 판정 `revise` · hard 1 · soft 8

| 컷 | 등급 | 분류 | 대상 | 근거(요약) |
|---|---|---|---|---|
| p_0136.97 | hard | occlusion | clip:strikes | The strike clip card sits in the middle of the timeline and hides the 4월–7월 section. The label for the 4.13 … |
| p_0061.25 | soft | media | clip:niovi | The niovi clip thumbnail has solid black rectangles at its left edge and bottom-right corner. They look like… |
| p_0022.27 | soft | occlusion | badge:이재명 | Behind the title card, the Lee Jae-myung badge and the '이재명' label are still faintly visible at the lower le… |
| p_0258.61 | soft | density | photo:hormuz_transit | The CENTCOM badge, the '10억 배럴' card, the photo and the route all appear at once. The photo covers the Bay o… |
| p_0164.59 | soft | media | card:9월 초 · 국내 방송 보도 | The sentence is about domestic broadcast reports, but the background is a wide map covering India through So… |
| p_0220.96 | soft | empty | marker:주한 미국대사관 근처 | The protest scene is only one small marker, '주한 미국대사관 근처', on a zoomed-out view of the central Korean penins… |
| p_0238.00 | soft | empty | panel:파병을 둘러싼 두 입장 | The support column has one bullet and the opposition column has two. The bottom half or more of both columns… |
| p_0124.25 | soft | legibility | panel:전쟁과 협상의 여섯 달 | The timeline's date and event labels (2.28, 3.15, 4.13, 7.8) are very small compared with the panel size. Th… |
| p_0080.70 | soft | order | panel:3월 15일, 해협을 직접 지키라는 요구 | The sentence is about all five countries refusing, but 호주's '거절' is faint and 한국 has no '거절' label yet at th… |

### 수정 → direction.v2 · changelog 9건

| 지적 | 바꾼 것 |
|---|---|
| clip:strikes | 타임라인 축 한가운데를 가리던 panel_gap 슬롯에서 map_right_low 슬롯으로 옮기고, 시작을 timeline_4 +0.3초에서 +1.2초로 늦춰 7.8 휴전 붕괴 점과 라벨이 먼저 드러난 뒤 들어오게 함(길이 5.0초 유지) |
| badge:이재명 | open 장면의 이재명 뱃지와 서울 마커 종료를 scene_end open 에서 0.6초 앞당겨(off -0.6) 타이틀 카드가 뜨기 전에 완전히 사라지게 함 |
| photo:hormuz_transit | 사진 등장을 now_0 +1.0초에서 now_1 +0.6초로 옮겨 '10억 배럴' 카드(now_0 끝 +0.4초 퇴장)와 겹치지 않게 엇갈림. 슬롯 체계상 경로를 완전히 피하는 하단 우측 슬롯이 따로 없어 배치는 map_right_low 유지 |
| card:9월 초 · 국내 방송 보도 | review 장면 진입 dip 카메라를 넓은 인도양 지도(92,21,w92)에서 한국 중심(127.6,35.8,w16)으로 바꾸고, review_3 -1.2초에 3.2초 move 로 기존 넓은 화면(92,21,w92)으로 빠지게 함. 장면당 이동 1회, 폭 비율 5… |
| marker:주한 미국대사관 근처 | debate 장면 카메라를 w3.6에서 도시 단위 w2.5로 좁히고 중심을 대사관 쪽(126.98,37.54)으로 당김. 집회 사진·기사 소재가 제공되지 않아 미디어 추가는 하지 않음 |
| panel:3월 15일, 해협을 직접 지키라는 요구 | 다섯 나라 '거절' state_changes 시각을 각 나라 이름 단어 앵커에서 0.3초씩 앞당겨(off -0.3) 이름을 말할 때 이미 라벨이 드러나 있게 함 |
| clip:niovi | 변경 없음 — 연출 필드(mid·x·y·w·place)로는 영상 내부 검은 영역을 잘라낼 수 없음. 미디어 원본 재크롭이 필요함 |
| panel:파병을 둘러싼 두 입장 | 변경 없음 — 원고에 없는 근거를 새로 넣을 수 없고 칼럼 높이는 렌더러 레이아웃 몫이라 연출에서 고칠 수 없음 |
| panel:전쟁과 협상의 여섯 달 | 변경 없음 — 라벨 글자 크기와 패널 세로 사용은 연출 필드에 없어 렌더러에서 조정해야 함 |

### 검수 v2 — direction.v2 · 판정 `revise` · hard 0 · soft 5

| 컷 | 등급 | 분류 | 대상 | 근거(요약) |
|---|---|---|---|---|
| p_0022.27 | soft | style | badge:이재명 | 타이틀 카드 뒤로 직전 장면의 서울 마커와 이재명 인물 뱃지가 반투명하게 남아 있다. 뱃지 원형이 부제 '한국은 왜 파병하지 않았나' 왼쪽 아래에 겹쳐 보여서 타이틀 화면이 정리되지 않은 인상을… |
| p_0045.03 | soft | occlusion | marker:호르무즈 해협 | 경로선 시작점 원형 표지가 '호르무즈 해협' 마커 라벨과 그 아래 주황색 보조 문구 위에 겹쳐 글자 일부가 가려진다 |
| p_0136.97 | soft | legibility | clip:strikes | 타임라인 날짜·사건 라벨(2.28, 3.15, 4.13, 6.17~7.8 등)이 매우 작고 서로 촘촘하다. 오른쪽 공습 클립이 '7.8 휴전 붕괴' 라벨 바로 옆까지 붙어 있어 마지막 구간이 읽… |
| p_0238.00 | soft | empty | panel:파병을 둘러싼 두 입장 | versus 패널 두 칸에 항목이 각 1~2줄뿐이다. 카드 높이의 절반 이상이 비어 있고 하단에는 작은 날짜만 떠 있어 휑하다 |
| p_0028.77 | soft | legibility | marker:호르무즈 해협 | '호르무즈 해협' 마커 아래 주황색 보조 문구가 매우 작은 글씨로 해안선 위에 얹혀 있어 축소 화면에서 판독이 어렵다(p_0038.45도 같음) |

### 수정 → direction.v3 · changelog 5건

| 지적 | 바꾼 것 |
|---|---|
| badge:이재명 | p_0022.27: open 장면의 서울 마커와 이재명 인물 뱃지 퇴장 시점을 scene_end open 기준 -0.6초에서 -1.6초로 앞당겨 타이틀 카드가 뜨기 전에 완전히 사라지게 함 |
| marker:호르무즈 해협 | p_0045.03: route 장면 호르무즈 마커의 라벨 방향을 right에서 left로 바꿈. 동쪽으로 뻗는 oil 경로 시작점 표지와 라벨이 겹치지 않게 함 |
| marker:호르무즈 해협 | p_0028.77, p_0038.45: route 장면 호르무즈 마커에서 작은 보조 문구 sub를 뺌. 같은 문구 '페르시아만에서 먼바다로 나가는 유일한 바닷길'은 route_0 구간 카드(card_right 기본 위치)로 옮겨 크게 보여 줌. 원고 문구만 사용함 |
| clip:strikes | p_0136.97: 공습 클립 배치 슬롯을 map_right_low에서 panel_gap으로 옮겨 '7.8 휴전 붕괴' 라벨 옆을 비움. 타임라인 라벨 글자 크기는 이벤트 필드로 조정할 수 없어 바꾸지 않음 |
| panel:파병을 둘러싼 두 입장 | 변경 없음(p_0238.00): versus 패널에는 높이 필드가 없음. 원고에 없는 근거·출처를 새로 넣을 수 없어 그대로 둠. 렌더러에서 카드 높이를 내용에 맞추는 조정이 필요함 |

### 검수 v3 — direction.v3 · 판정 `revise` · hard 2 · soft 6

| 컷 | 등급 | 분류 | 대상 | 근거(요약) |
|---|---|---|---|---|
| p_0045.03 | hard | occlusion | marker:호르무즈 해협 | 경로 시작점인 호르무즈 해협 마커가 화면 왼쪽 끝에 붙어 있어 이름표가 '르무즈 해협'처럼 앞이 잘려 보이고, 경로선 시작 부분도 화면 밖에서 들어온다 |
| p_0136.97 | hard | occlusion | clip:strikes | 공습 클립 창이 타임라인 위에 떠서 4.13 눈금 라벨('미국 해…')과 그 주변 눈금 글자를 가리고 있다. 7월 8일 지점도 클립 아래에 묻혀 문장이 말하는 날짜가 보이지 않는다 |
| p_0061.25 | soft | media | clip:niovi | 선박 클립 안 왼쪽 아래와 오른쪽에 검은 사각형 덩어리가 보여 원본 레터박스나 크롭이 덜 된 것처럼 보인다 |
| p_0022.27 | soft | style | badge:이재명 | 제목 화면 왼쪽 아래에 앞 장면의 이재명 인물 뱃지가 흐리게 남아 있어 타이틀 구성이 산만해 보인다 |
| p_0238.00 | soft | empty | panel:파병을 둘러싼 두 입장 | 찬반 패널에 항목이 한두 줄씩만 있어 두 칸 아래쪽 절반 이상이 비어 있다. 이벤트 목록에는 '주한 미국대사관 근처' 마커가 있지만 화면에는 보이지 않는다 |
| p_0105.28 | soft | empty | panel:3월 21일 공동성명 | 공동성명 패널에서 국기 세 개와 한국 국기 사이가 넓게 비어 있고, 연결선이 흐려 관계가 잘 읽히지 않는다 |
| p_0124.25 | soft | legibility | panel:전쟁과 협상의 여섯 달 | 타임라인의 날짜와 사건 라벨이 축 위아래에 아주 작게 흩어져 있어, 축소한 화면 기준으로 4.13 라벨을 읽기 어렵다 |
| p_0288.44 | soft | legibility | credits:자료 및 출처 | 자료 및 출처 화면의 본문 글자가 매우 작고 대비가 낮으며, 화면 왼쪽 위 절반에만 몰려 있고 아래쪽은 비어 있다 |
