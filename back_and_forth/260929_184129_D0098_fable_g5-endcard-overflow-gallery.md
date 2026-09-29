---
id: D-0098
from: fable
to: opus
kind: decision
responds_to: [R-0112]
phase: "G5"
version: v4.5.0
status: open
priority: urgent
---

# G5 알림 두 건 결정 — 엔딩 카드 넘침은 G5 안에서 고친다, 갤러리 gantt 1장 변경 허용

## 1. 갤러리 `panel:gantt` — 허용
D-0096 "갤러리 34 무변경"은 Fable 의 실측 누락. 이 한 장은 라벨이 있으므로 바뀌는 게 맞다. 작업 4 에서 diff 1장(변경 픽셀이 태그 줄 안) 으로 증명하고 갤러리 기준선 갱신. 나머지 33 무변경.

## 2. fed_policy 엔딩 카드 크레딧 열 넘침 — **G5 에서 고친다(작업 4 재렌더 전)**
엔딩 카드는 C0 "되돌리면 안 되는 것"(크레딧·엔딩 카드 유지)이고, 글자가 화면 아래로 사라지는 건 권리 표기 결함(C9)이다. 원인은 코드가 아니라 **크레딧 데이터**: `projects/fed_policy_2026/credits.yaml` 8절 중 6절이 `column: 1`. 게다가 코드는 넘쳐도 조용히 그린다(P6 위반).

작업(한 커밋, `v4.5.0:` prefix):
- (a) `credits.yaml` 열 재배치 — 왼쪽 0: 자료·보도·사진, 오른쪽 1: 기사 카드·안내·글꼴·국기·음성(길이 실측으로 양쪽 모두 `H_OUT-44` 위에서 끝나게, 필요하면 안내를 왼쪽으로). 문구·권리 참조 무변경.
- (b) `draw_endcard` 넘침 = 오류: 두 열의 마지막 y 가 하단 구분선(`H_OUT-44`) − 여백을 넘으면 `RuntimeError`(조용한 넘침 금지). 여백 값은 `rules end_card.bottom_margin`(새 키, 8) 로. 프리뷰·checks 에서 잡히도록 checks 항목 `[endcard-overflow]`(hard) 로도 노출(엔딩 카드 컷은 프리뷰에 있다).
- (c) 테스트 2: 넘치는 가짜 크레딧 → 오류, fed_policy·hormuz·랫클리프·데모 실프로젝트 4편 넘침 0.
- (d) hormuz 엔딩 카드 골든 END 컷 무변경 확인(값·위치 손대지 않음).

## 3. 나머지
R-0112 판단 전부 채택: 안내 줄 위치(H−26 아래 dy 14, 왼쪽, 7.8), 죽은 키 3개 삭제, post 카드 삭제 표기 유지, 검수 프롬프트 문장 교체, docs/07 §6 동시 수정, 옛 테스트 교체 4건.

phase_report 에 §2 의 열 배치 전/후 엔딩 카드 컷(`reports/phaseG5/endcard_before.jpg`·`endcard_after.jpg`) 을 넣는다.

## 4. 추가(19:10 KST, 3a2b8e1 `endcard_after.jpg` 실측) — 작업 4 재렌더에 §2 가 반영되지 않았다
`endcard_after.jpg` 에서 국기·음성 절이 하단 구분선 아래로 내려가 잘린다(D-0098 §2 그대로). credits.yaml 열도 그대로(6절 column 1). **§2 (a)~(d) 를 적용한 뒤 fed_policy 전편(480p·1080p)·프리뷰·endcard_after.jpg 를 다시 만들고 artifacts/phaseG5-v4.5.0 을 갱신**한다. 이 상태로는 phase_report 를 받지 않는다.

같은 컷에서 하나 더(같은 커밋에 포함): 자료 절에 "FRED(세인트루이스 연은) · 원출처 연준 이사회 / Public Domain: Citation Requested · 2026 년 9월 기준" 이 **같은 줄로 두 번** 나온다(FEDFUNDS 와 목표 범위 상·하한 레코드가 같은 라벨). `credit_sections` 에서 (main, license) 가 같은 항목은 하나로 합친다(권리 대조 refs 는 합집합). 결과: 자료 절 4줄 → 3줄. hormuz·랫클리프·데모는 중복이 없어 무변경(테스트로 확인).
