---
id: D-0317
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — R-0292(승인 뒤 렌더 준비): 상태를 `transition` 으로 preview_approval 에 고정(사유 기록), require_animatic·require_feedback_guards 는 그대로 통과. 렌더 계획 승인

1. **상태 고정 승인**: econ(assets)·geo(direction) 를 `advance` 로 다시 돌리면 revise 루프가 승인할 연출을 고칠 수 있다 — 네 제안대로 `transition --to preview_approval --reason "게이트 ② 자료 R-0290·R-0291 연출 지문 고정(econ 43b29be8·geo c10ce72e → 최신)"` 로 두고, **우회 플래그 없이** `approve --gate preview_approval` 이 require_animatic(현재 음성 타임라인의 콘티 판 기록 — 원고·음성은 콘티 판 뒤 불변이라 통과해야 한다)·require_feedback_guards(앞선 영상 open 의견 0 — UF-146·148 guarded, UF-149~155 는 samsung 몫)를 그대로 검사하게 한다. 둘 중 하나라도 거부되면 **우회하지 말고 R** — 그게 장치다.
2. **렌더 계획 승인**: 한 편씩 `advance --jobs 4`(render → audio_mix → deliver), geo 먼저(카탈로그 재렌더 포함) → econ(A/B 결과가 A 면 카탈로그 그대로, B 면 프리뷰·카탈로그 재렌더) → `tools/showcase_concat.py` 결합본(재인코딩 없음, md5 README). 메모리 계산(geo 4.8 GB·econ 7.2 GB / 15.4 GB) 승인. 렌더 중 규칙·엔진 변경 금지.
3. 시작 신호 = 감독의 D(from: user, 게이트 ② 승인·A/B). 그 전엔 렌더 금지.
