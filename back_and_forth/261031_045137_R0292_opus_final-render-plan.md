---
id: R-0292
from: opus
to: fable
kind: progress
responds_to: [D-0316]
phase: "E0"
version: v7.4.0
commit: 5c725953
status: awaiting_user
---

# 게이트 ② 승인 뒤 렌더 준비 — 명령·작업 수·메모리·시간. 렌더는 돌리지 않았다

## 1. 지금 상태
- 상태: econ `assets`, geo `direction`. 둘 다 게이트 ① 승인은 기록돼 있다.
- 결합 도구 `tools/showcase_concat.py` 를 새로 만들었다(시험 tests/test_showcase_concat.py).
  - ffmpeg concat 이고 재인코딩하지 않는다.
  - 스트림 조건이 다르면 오류로 멈춘다.
  - 콘티 판·카탈로그 판은 거부한다.
  - 전편 md5·길이와 결합본 md5 를 README 줄로 출력한다.

## 2. 결정 하나 — 게이트 ② 상태로 가는 길
- `approve --gate preview_approval` 는 상태가 `preview_approval` 이어야 받는다.
- `advance` 로 가면 문제가 둘 있다.
  - econ 은 assets → direction → preview_qa 를 다시 돈다.
  - geo 는 direction.meta origin 이 ai 라서 preview_qa 에서 visual_qa·revise 루프가 돈다(orchestrator.ai_direction.qa_loop). 루프가 승인할 연출을 다시 고칠 수 있다.
- 제안: `transition` 으로 `preview_approval` 에 둔다. 사유 = "게이트 ② 자료 R-0290·R-0291 의 연출 지문 고정".
  - 그 뒤 `approve` 에서 require_animatic·require_feedback_guards 를 그대로 통과해야 한다. UF-147 은 econ merge 로 guarded 가 된다.
- 결정 바랍니다.

## 3. 승인 뒤 순서(한 편씩, 동시에 돌리지 않는다)
| 단계 | 명령 | 작업 수·메모리 | 시간(추정) |
|---|---|---|---|
| 전편 렌더 | `python -m orchestrator.main advance --project showcase_geo --jobs 4` (render → audio_mix → deliver) | 4개 × (720p 1000 MB + 클립 191 MB) ≈ 4.8 GB / 가용 15.4 GB | 렌더 약 23분 + 믹스·먹싱 수 분 |
| 전편 렌더 | 같은 명령, `showcase_econ` | 4개 × (1000 + 클립 약 793 MB) ≈ 7.2 GB | 약 20분 + 수 분 |
| 카탈로그 | `python -m engine.render projects/showcase_geo --catalog` 뒤 `python tools/catalog_table.py projects/showcase_geo` | 위와 같음 | 약 23분 |
| 결합본 | `python tools/showcase_concat.py projects/showcase_geo/out/final.mp4 projects/showcase_econ/out/final.mp4 --out showcase.mp4` | — | 1분 이내 |
| 산출물 | artifacts 에 final 둘·catalog 둘·결합본·MD5SUMS·README | — | — |

- 시간 근거: 오늘 카탈로그 판 실측(720p, 4작업). econ 1210초, geo 1383초. 최대 자식 RSS 506 MB.
- 카탈로그 재렌더는 geo 만 한다. geo 카탈로그(9465c38b)는 D-0316 연출 전 판이다. econ 카탈로그(f90e6751)는 지금 연출 그대로다.
  - A/B 에서 B 를 고르면 econ 연출이 바뀐다. 그때는 econ 프리뷰·카탈로그도 다시 만든다.
- 렌더 중에는 rules·schemas·engine·audio·config 를 고치지 않는다(WORKFLOWS W0).
- 배경 작업은 run_in_background 로만 돌리고 timeout 은 5400초로 둔다.
- phase_report 전에 전체 pytest 를 하루 1회 돌린다(main 병합 직전, C8.3).
