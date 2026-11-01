---
id: R-0316
from: opus
to: fable
kind: gate_request
responds_to: [D-0463]
phase: "IR3"
version: v7.4.0
commit: a06d7c19
status: awaiting_decision
---

# 게이트 ② 재승인 자료 — 프리뷰 v2(연출 v9) hard 0

## 1. 자료(artifacts/iran-ceasefire-v7.4.0 414ed10)
- `iran_ceasefire_2026/preview_v2/`: `preview_sheet.jpg`(18컷), `preview_checks.json`, `preview_provenance.json`, MD5SUMS.
- 콘티 판 v5: `animatic_v5/`(md5 f2796da0, D-0463 통과).
- script_sha1 `4a47c0a2…`. 원고·음성은 바뀌지 않았습니다.

## 2. checks(프리뷰, --preview auto)
- hard 0, warning 49. `element_hold` 0, `media_overlap` 0, `forbidden`(label-in-body) 0.
- provenance `user_feedback_guards`: UF-170 forbidden 0 · UF-171 element_hold 0 · UF-172 media_overlap 0.
- warning 은 콘티 판 v5 와 같은 항목에 `map_contrast_shape` 2건(394·421초 항로선 대비)이 더해졌습니다. 첫 전달본과 같습니다.

## 3. 정정
- R-0315 에 "뺀 것 6" 이라 적었는데 실제로는 5건입니다. 루비오 뱃지, 샤리프 뱃지, 트럼프 quote(act1_9), 기사 0043, 기사 0047 입니다.

## 4. 다음
- 감독이 transition → approve 를 실행해 manifest 를 푸시하면 720p → `final_deliver.mp4`(≤30 MB) → `final_v2/` → 최종 R 로 갑니다.
