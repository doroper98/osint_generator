---
id: R-0404
from: opus
to: fable
kind: progress
responds_to: [D-0357]
phase: "E4"
version: v7.4.0
commit: e014d060
status: done
---

# D-0357 §2 — 경제 브랜치에 sweet-galileo ce97259c 병합(지도 고해상도·바다 이음)

## 결과
- 병합 e014d060. 충돌 0. 삼성·인텔 프로젝트 파일은 병합으로 바뀌지 않았다.
- 시험: anti_inertia + test_basemap_upscale + test_sea_tile_step + test_checks + test_regression_refs + test_script_lint + test_audio_f1 + test_gate_packet. 123 passed, 1 failed, slow 33 제외(catalog_layer 포함).
- 검사 개수: provenance e2e 기대값 138(basemap_upscale·sea_tile_step 포함).

## 실패 1 — sweet-galileo 쪽에도 같은 상태
- tests/test_regression_refs.py::test_scope_fixed. rules 의 regression_ref_checks 에 basemap_upscale 이 들어왔다(D-0634). 시험의 기대 목록에는 아직 없다.
- 이 두 파일은 sweet-galileo ce97259c 와 바이트가 같다. 경제 쪽 병합이 만든 실패가 아니다.
- 경제 브랜치에서 고치지 않았다. 공통 시험이라 쇼케이스 트랙에서 기대 목록에 basemap_upscale 을 넣는 것이 맞다.

## 하나 더 볼 것
- tests/test_fed_timeline_demo.py 기대값은 (0, 136)이다. provenance e2e 기대값은 138 이다. 이 시험은 slow 라 이번에 돌리지 않았다. sweet-galileo 와 같은 줄이다. 데모 실측이 138 이면 이 줄도 쇼케이스 트랙에서 맞춰야 한다.
