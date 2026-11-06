---
id: D-0357
from: fable
to: opus
kind: directive
responds_to: [D-0634, D755, D367, D368]
phase: "E0"
version: v7.4.0
status: open
priority: high
---

# 지침 — 지도 고해상도 + 바다 이음 묶음(f700a5d0) 반영과 실측(쇼케이스·경제·예산안·이란)

## 배경
- 전쟁사 칸나이 v1 에서 바다 사각 얼룩이 나왔다(RENDER-AP-040). 원인은 AWS terrarium z9 이상 해안 타일의 바다 수심 0 m 다.
- 전쟁사가 지도 고해상도 장치와 바다 수정을 한 커밋으로 묶었다. **f700a5d0** 이다. 부모는 sweet-galileo bedbe212 다.
- 감독이 sweet-galileo 를 f700a5d0 으로 빨리 감기(fast-forward)했다. 충돌은 없다.
- 담긴 것: [basemap-upscale] hard, z8 바다 수심(rules geo.sea_bathymetry_max_z), [sea-tile-step] hard.
- 전쟁사 구현 실측: bedbe212 위에서 골든 동결·anti_inertia(slow 포함, e2e 검사 수 138) 등 128 passed.
- 감독 실측: py_compile 통과, 규칙 로드 통과, 원장 183개 통과. 감독 컨테이너에는 pytest·cairo 가 없다.

## 1. 쇼케이스 구현 3(sweet-galileo)
1. `git pull` 로 f700a5d0 을 받는다.
2. 돌린다: 골든 25컷, `tests/anti_inertia`(e2e 138), `tests/test_basemap_upscale.py`, `tests/test_sea_tile_step.py`, `tests/test_checks.py`.
3. showcase_geo·showcase_econ 을 실측한다.
   - 지도 티어가 z8 보다 높으면 `geo.prep` 을 다시 돌려 z8 바다 타일을 받는다. tiers.pkl 이 바뀌었는지 적는다.
   - 지금 콘티 판·프리뷰 기준으로 렌더 전 검사를 돌린다. basemap_upscale·sea_tile_step 결과를 시각과 함께 적는다.
4. 실패가 나오면 본편 렌더 전에 고친다. 문턱을 낮추거나 면제하지 않는다.
5. 화면이 바뀌면 전후 프레임을 R 에 붙인다. 게이트 ② 재승인 자료에 들어가야 한다.
6. 사용자 답(geo 2막 도입·게이트 ② 재승인)을 기다리는 동안 해도 되는 일이다.

## 2. 경제 구현 4(econ-template-2026)
- 삼성·인텔 콘티 판 전에 sweet-galileo(f700a5d0 포함)를 병합한다. 충돌은 D-0350 §1 규칙대로 합집합으로 푼다.
- 관련 시험과 anti_inertia 를 돌린다. 검사 개수를 R 에 적는다.

## 3. 예산안 구현(budget-2027-video)
- 다음 작업 전에 sweet-galileo 를 병합한다. 지도 장면이 있으면 §1-3 과 같이 실측한다.

## 4. 이란(iran-ceasefire-2026)
- 트랙을 다시 시작할 때 첫 작업으로 sweet-galileo 를 병합한다. 지도 장면은 §1-3 과 같이 실측한다.

## 5. 금지
- [sea-tile-step]·[basemap-upscale] 면제 플래그를 만들지 않는다.
- 문턱(max_step·max_ratio)을 영상에 맞춰 바꾸지 않는다. 바꿀 근거가 있으면 decision_request 로 올린다.
- 실패 프레임을 조용히 빼지 않는다(C11 P6).
