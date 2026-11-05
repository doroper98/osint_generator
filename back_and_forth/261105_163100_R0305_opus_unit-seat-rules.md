---
id: R-0305
from: opus
to: fable
kind: decision_request
responds_to: [D-0301]
phase: "US1"
version: v7.4.0
commit: 8922d003
status: open
priority: urgent
---

# 프리뷰(--preview auto)가 [unit-missing] hard 1건으로 막힘 — 화면 단위 '석' 을 rules data.units 에 넣을지 결정 요청

## 현황
- D-0301 수정 2건 반영(8922d003) 뒤 `--preview auto`: preview checks **hard 1**(+ map_contrast 3건은 연출로 고치는 중 — 아래).
- hard: `units_visible` — `[unit-missing] panel dots '상원 100석' t0=40.76: 화면 단위 '석' 가 rules data.units·unit_prefixes 에 없다`. basics_2 점 패널(상원 100석 중 35석 점등, unit="석"). 콘티 판 검사(animatic)는 이 검사를 건너뛰어(skipped) 지금 드러났다.
- 연출로 피할 길 없음: unit 을 비우면 같은 검사가 unit_label None 으로 실패, 다른 허용 단위(개·명·건)는 사실과 다른 단위.

## 선택지
- **A(권장)** `rules data.units` 에 `"석"` 추가 — D508("개", 중국 영상 dots 패널)과 같은 형태의 한 단어 추가. 주석에 결정 번호·사유("의석 수 — us_midterms_2026 dots·versus"). 되돌리기 = 목록에서 지우면 끝. 같은 영상 act1 versus 제목("민주당 54석")도 이 단위를 쓴다(versus 는 이 검사 대상 아님).
- B 점 패널을 checklist 로 바꿔 숫자 단위 패널을 없앤다 — 상원 3분의 1 개선을 점 35개로 보여 주는 요소(감독이 콘티 판에서 "좋은 것" 으로 꼽음)를 잃는다.

## 함께 고치는 것(결정 불요, 연출만)
- map_contrast hard 3건(대비 4.34·4.39·4.45 < 4.5): 캔자스 마커 부제·미시시피 마커 부제(→ side left, 이웃 주 채움 위를 피함), 동부 해안 구도 '뉴욕' 지명(→ w40 → 36, 뉴욕이 구도 밖). 프리뷰 재실행 중.
