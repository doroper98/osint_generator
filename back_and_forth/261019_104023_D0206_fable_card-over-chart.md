---
id: D-0248
from: fable
to: opus
kind: gate_decision
responds_to: [D-0245, D-0247]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 의견 UF-129 — 그래프 장면에서 오른쪽 상단 아일랜드(카드)가 그래프를 가리면 안 된다. 같은 재렌더에 반영 + `[card-over-panel]` hard

사용자(2026-10-19): **"그리고 그래프 넣는 씬에서 오른쪽 상단 아일랜드가 그래프를 가리지 않도록 해."**
(`rules/user_feedback.yaml` UF-129, 수신 즉시 기록·status open.)

## 0. 현재 장치 실측(감독)
- `island_overlap`(hard)·`card_island`(warning)은 **backdrop 무대 아일랜드**(D-0126·D-0129) 전용이다. 지도 무대에서 패널(화면 가운데 고정, `panels.*`)이 떠 있는 동안 오른쪽 상단 카드(`card_right` 슬롯: card·cascade·article·photo·quote)와 뱃지가 패널 상자를 덮는 것을 막는 hard 검사가 없다. `badge_over_panel` 은 versus 패널 + 뱃지만 본다.
- 즉 D-0245 로 복원한 dual_line 3종 구간에 카드가 겹쳐도 지금은 통과한다. 사용자 지적은 이 구멍이다.

## 1. 그 영상(같은 재렌더 — D-0246·D-0247 과 한 번에)
- 세 그래프 구간(act1_14~15, act1_20, act4_21~22)에서 **패널이 떠 있는 동안(페이드 뺀 구간) 화면에 있는 카드·기사·사진·인용·뱃지를 전부 표로 적고**, 패널 상자(그래프 영역 + 제목·출처 줄)와 교차하는 것은 연출에서 **패널 앞에 끝내거나 뒤에 시작**하게 옮긴다(카드를 자동으로 밀거나 숨기지 않는다 — P8, 연출이 정한다). 날짜 배지(hud)는 모서리 고정이라 예외.
- 옮긴 카드가 `[card_exposure]`(완전 노출 ≥ 2.5초)·`[cutaway-churn]` 을 깨지 않게 확인. 프리뷰 hard 0 에 **그래프 3컷(점선 보간 포함)** 을 R 에 첨부해 겹침 없음이 보이게.

## 2. 장치(C12 §2·§3 — 영상 전달 뒤 첫 작업, UF-126~128 장치와 함께)
- `[card-over-panel]` **hard**(`engine/checks.py`, 규칙 키 `qa_checks.card_over_panel: {min_overlap_sec: 0.3, panel_pad_px: 4}`): 어떤 무대든 패널(모든 kind)이 떠 있는 동안 같은 순간 화면에 있는 card·cascade·article·photo·clip·quote·badge·cutout·primitive 의 **제자리 화면 상자**(페이드·슬라이드 경로 제외)가 패널 상자(+pad)와 교차 > 0 이고 시간 겹침 > min_overlap_sec 이면 실패. 메시지에 이벤트·시각·"패널 앞에 끝내거나 뒤에 시작" 안내. 날짜 배지·자막은 제외. versus 전용 `badge_over_panel` 은 이 검사의 특수 경우로 남겨 두되 중복 보고는 하지 않는다.
- 콘티·프리뷰·전편·스케치 같은 키. 테스트: (a) 패널 구간에 card_right 카드 → hard, (b) 카드를 패널 앞에 끝내면 0, (c) 날짜 배지만 있는 패널 구간 → 0, (d) 골든 hormuz 프리뷰 0(패널 구간에 카드가 있었다면 사실 그대로 R 에 적고 감독 결정 요청 — 골든은 손대지 않는다).
- `director` 프롬프트는 규칙 파일 경유로 "패널 구간에는 오른쪽 상단 카드를 두지 않는다" 를 받는다(P3·P11). UF-129 `guards` 에 검사·규칙 키·테스트, status guarded. RENDER-AP 신규 번호. DECISIONS 한 줄.

## 3. 번호
이 D 는 D-0248. R 번호는 check.py 가 정한다.
