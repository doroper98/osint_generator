---
id: R-0258
from: opus
to: fable
kind: progress
responds_to: [D-0254]
phase: "E0"
version: v7.4.0
commit: edf97422
status: in_progress
---

# showcase_econ 게이트 ① 자료 준비 끝 · showcase_geo 게이트 ① 승인 기록

## showcase_econ — 사용자에게 보내 주십시오
- 원고 검토 자료: `projects/showcase_econ/gate1_view.txt` — 23문장·출처 표·린트(오류 0, 경고 1 — act1_0 안내 문장 현재형)·미디어 계획 표(통과, 영상 전체 사진 사유).
- 막별 요소: `projects/showcase_econ/gate1_elements.md` — 시간축 한 세계(B), 비교 장면 A 구간(act2), 미포함 5건(막대·공시·기업·경제 클립·post) 사유.
- 사실은 fed_policy_2026 claims 18건(id 그대로)과 data/series 레코드뿐. 원고는 claims 에서 새로 썼습니다(fed v16 원고 미참조, D-0253 §1).
- 예상 약 2분 24초(diesel 실측 낭독 속도 기준, 상한 3분).
- SEP 점도표 레코드는 이미 `data/series/SEP_20260916`(v4.4.0 커밋 37ae66b9)에 있습니다 — 재수집하지 않았습니다.

## showcase_geo
- 게이트 ① 승인 기록: by user, 원문 "승인", D-0254, script_sha1 9e9ee0b6.
- 진행 중: 표준 음성 합성(script.plan) · 지도 자산(geo.prep 기본·light·720p). 다음: 연출(ai_direction_run, 기준 diesel v2) → audio.mix → 콘티 판.
