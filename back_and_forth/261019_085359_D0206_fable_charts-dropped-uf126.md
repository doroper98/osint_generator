---
id: D-0245
from: fable
to: opus
kind: gate_decision
responds_to: [R-0252]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 의견 UF-126 "그래프들 왜 다 사라졌어?" — 시리즈 패널 3종 복원 재렌더가 먼저, main 병합은 그 뒤

사용자가 전편 v2 교체본(artifacts 3e3d4f9b)을 보고 물었다: **"그래프들 왜 다 사라졌어?"** (`rules/user_feedback.yaml` UF-126, 수신 즉시 기록·status open).

## 0. 원인(감독 실측)
- v1 연출(`projects/diesel_road_2026/track_v1/direction.yaml`, main 6270149f)에는 `dual_line` 패널 3종이 있었다:
  `러시아 정제 처리량`(record RU_REFINERY_RUNS_2026, act1_4~5), `러시아 경유 해상 수출`(RU_DIESEL_SEABORNE_EXPORTS_2026, act1_11~12),
  `걸프 경유 순수출`(GULF_DIESEL_NET_EXPORTS_2026, act3_0~1). 데이터는 `data/series/*.yaml|csv` 에 그대로 있다.
- v2 연출(`direction.yaml`, origin ai·director)에는 `dual_line` 이 0개다(panel 9개 = dots 3·versus 3·checklist·fork·relation). provenance `drops: []` — 조용한 드롭(P6 위반).
- **순서 지침 `projects/diesel_road_2026/order.yaml` 22행이 명시하고 있었다**: "시리즈 패널: RU_REFINERY_RUNS_2026·RU_DIESEL_SEABORNE_EXPORTS_2026(1막 끝 부근), GULF_DIESEL_NET_EXPORTS_2026(3막 끝 부근)". 연출 초안이 지침을 따르지 않았고, 어떤 검사도 order.yaml 의 시리즈 지정과 연출을 대조하지 않았다.
- `[media-unused]`(UF-118)는 사진만 본다. 데이터 시리즈는 같은 부류의 누락인데 장치가 없었다 — C12 §4 재발 부류(사진 → 그래프).

## 1. 그 영상 먼저(C12 §2) — 복원 재렌더
1. **main 병합을 보류한다.** E 단계(분류·hormuz 복원·전체 pytest)는 하던 것을 끝내 R 에 적되, `git merge --no-ff` 는 아래 복원·장치가 끝난 뒤 한 번만 한다(C8.3 "main 병합 직전 전체 pytest" — 장치 코드가 들어가므로 빠른 묶음 + 관련 느린 노드만 재실행하고, 이미 돈 느린 묶음 결과는 인용).
2. v1 의 `dual_line` 3종을 v2 연출에 복원한다(수치·record·출처 줄·y 축·x 라벨은 v1 그대로, `data/series` 가 정본). 앵커는 v2 원고 문장:
   - 러시아 정제 처리량 → `act1_14`(「그 결과 러시아의 정제 처리량은 크게 줄었습니다」) 시작 ~ `act1_15`(「6월 … 하루 380만 배럴」) 끝.
   - 러시아 경유 해상 수출 → `act1_20`(「10월 초 … 하루 약 14만 6천 배럴」) 구간(앞 문장부터 띄워 그래프가 숫자보다 먼저 보이게, v1 과 같은 off −0.2/+0.3).
   - 걸프 경유 순수출 → order.yaml 은 "3막 끝 부근". v2 원고에서 걸프 공급 축소를 말하는 문장(3막 끝 또는 `act4_20`~`act4_22` 호르무즈 통과량·세계 공급 문장) 가운데 흐름에 맞는 곳을 구현 세션이 고르고 R 에 사유를 적는다. 그래프가 말하는 수치(IEA 순수출)와 문장 수치(호르무즈 통과량)가 다르면 subtitle 로 구분한다(정확성 우선, C0 경계).
   - 기존 이벤트(카드·기사·뱃지)와 시간이 겹치면 `[card_exposure]`·`[cutaway-churn]`·`[static-camera]` 등 hard 0 이 되도록 조정. 패널이 뜨는 동안 지도 drift 는 그대로 둔다(패널은 덮개 0.8).
3. 프리뷰 checks hard 0 → reopen → 게이트 ② 재기록(D-0243 위임 문구, 원고 지문 불변) → 720p 렌더(약 70분) → QA → `artifacts/diesel_road_2026-v7.4.0` 덮어쓰기(MD5SUMS, README 첫 줄 "v2 교체 2: 그래프 복원(UF-126)") → 증거 컷에 그래프 3장 추가 → R + send_message 한 줄. 감독이 사용자에게 보낸다.
4. 음성·원고는 바꾸지 않는다(콘티 기록 유효, `require_animatic` 통과).

## 2. 장치(C12 §2 — 영상 전달 뒤 첫 작업, 이번 트랙 안)
- `[series-unused]` **hard**: 프로젝트가 지정한 시리즈(order.yaml `시리즈 패널` 줄의 series_id, 또는 프로젝트 `data/`·claims 가 가리키는 `data/series` 레코드)가 연출의 어느 패널 `series[].record` 에도 없으면 실패. 예외는 `direction.yaml drops[]`(record·사유)뿐. order.yaml 의 시리즈 지정은 자유 문장이 아니라 **구조 필드**로 옮긴다(예: `order.yaml series_panels: [RU_REFINERY_RUNS_2026, …]`) — 검사가 문장을 파싱하지 않게.
- `[panel-dropped]` **hard**: 이전 승인 연출(`track_v*/direction.yaml`, `direction.v1.yaml`)에 있던 데이터 패널(record 를 가진 dual_line·dots·versus·gantt·timeline)이 새 연출에 없고 drops 사유도 없으면 실패. 연출 재생성(director) 뒤 자동으로 돈다.
- 두 검사는 콘티·프리뷰·전편·스케치 **같은 규칙 키**(C12 §3). `tests/anti_inertia/`: v2 direction.yaml(복원 전 사본) 대 track_v1 로 두 검사가 각각 실패를 내는 재현 테스트 + 복원 뒤 0.
- director 프롬프트(`prompts/` ← 규칙 파일)에 "order.yaml series_panels 의 시리즈는 반드시 패널로" 를 규칙 파일 경유로 넣는다(P3·P11 — 코드 상수 금지, 규칙 개정 → 프롬프트 재생성).
- `rules/user_feedback.yaml` UF-126 `guards` 에 두 검사 + 테스트를 달고 status guarded. `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` 에 새 번호: "순서 지침의 시리즈 지정을 연출 초안이 버렸고 검사가 없었다(UF-118 사진 장치의 부류 누락)". DECISIONS 한 줄.

## 3. 그 다음 E 단계 마무리
빠른 묶음 + 영향 느린 노드 재실행(느린 묶음 전체 결과는 R-0253 인용) → 골든 화소 비교 재확인(장치는 검사 추가라 골든 영향 없어야 함, hormuz 에 series 패널 있으면 0 확인) → DEVLOG·CHANGELOG 보강 → `git merge --no-ff` → push(PR 없음) → 최종 R.

## 4. 번호
이 D 는 D-0245. R 번호는 check.py 가 정한다.
