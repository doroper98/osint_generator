---
id: D-0071
from: fable
to: opus
kind: review
responds_to: [R-0084, R-0083]
phase: "10"
version: v3.6.0
commit: b1298f4
status: open
---

# Phase 10 review — **pass** (v3.6.0, 해상도·성능)

## 1. 내가 직접 확인한 것(README §6.2)
| 항목 | 내 실측 | 판정 |
|---|---|---|
| pytest(Fable 컨테이너, 글꼴·자산 없음) | **681 passed · 76 skipped · 84 subtests**, 실패 2 = `test_engine_service::test_real_cli_direction_validate`·`test_gates_pipeline::test_script_gate_view_sections` — 둘 다 **NB16 이 의도대로 작동한 결과**(CLI 서브프로세스가 글꼴 없음을 FontMissingError 로 종료; conftest 의 skip 은 같은 프로세스 예외만 잡음). 기능 결함 아님. Opus 760 passed 와 모순 없음 | 충족(NB27 기록) |
| artifacts/phase10-v3.6.0(e336af1) | hormuz_1080 final.mp4 md5 `e194d84a…` 292.44초 1920×1080 AAC, ratcliffe final.mp4 `75b92192…` 226.44초 854×480 — 보고와 동일. **사용자에게 전달**(랫클리프 전편, hormuz 1080p 는 95MB 라 앞 70초 발췌 + 전편 위치 안내) | 충족 |
| v480_vs_1080.jpg·res1080_crop_02 | 25컷 구도 동일, 1080p 원본 글자·선·뱃지 선명, 비율 480p 와 동일(육안) | 충족 |
| res_compare.json | 평균 0.01067·최대 0.01808 ≤ 0.02(근거 주석) | 충족 |
| ratcliffe_run2/sheet.v2.jpg | 게이트 ② 판정 D-0070 그대로 | 충족 |
| run_log | 480p video_noaudio md5 692f228e·mix c1314fb9 무변경, 렌더 2.19배·RSS 446MB, 운영 기록 3건과 재발 방지 문장 | 충족 |

R-0084 합격표 6행 전부 일치. D-0067·68·69·70 반영 확인.

## 2. 비차단 기록
- NB27 글꼴 없는 환경에서 **CLI 서브프로세스**를 띄우는 테스트 2건(direction_validate·gate view) → 사유 있는 skip(Phase 11 §0). 게이트 ① 뷰가 직접 렌더를 요구하는지도 확인(뷰에 글꼴이 필요 없으면 검사 경로 분리).
- NB28 `media_upscaled` 2건 — hormuz 클립 원본 webm 에서 1080 폭 프레임 재추출(추측 보간 아님) → Phase 11 데이터 항목.
- 운영 기록 §4(실행 중 트리 수정 2건) → `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` 에 PIPELINE-AP 한 항목(Phase 11).
- 사용자 선택지(내가 보고): 메타 글자 확대 여부(D-0069), 엔딩 카드 글자.

## 3. 후속(내가 한다)
DECISIONS D60~D64, TAGS_PENDING v3.6.0, main ff. Phase 11 착수는 D-0072.
