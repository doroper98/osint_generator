<!--
tier: 3
last_synced_with: v3.3.0
ssot_for: [report-phase7-hormuz_ai-camera-suggest-qa-compare]
depends_on: [engine/camera_suggest.py, workers/director_worker.py, prompts/director_user.md, orchestrator/ai_direction.py]
last_review: 2026-09-28
-->
# hormuz_ai 재실증 — 카메라 제안값을 입력으로 준 AI 연출 (D-0056 작업 7)

## 무엇을 했나
1. 6.9 실행 2의 선택 판 `projects/hormuz_ai/direction.v2.yaml` 로 `python -m engine.camera_suggest` → 제안 8/10 숏(엔딩 풀백·장소 없는 숏 제외).
2. 사본 `projects/hormuz_ai_cam/`(원고·plan·자산만, direction 없음 + `prev/camera_suggest.json`)에서
   `python tools/ai_direction_run.py projects/hormuz_ai_cam --preview golden` — 6.9 와 같은 연출가·검사·검수·수정 루프(상한 2).
3. 연출가 프롬프트의 `{camera_suggest}` 칸에 제안값만 들어갔다(이전 연출 카메라 값 없음, P9).
   `direction.meta.json camera_suggest_sha1` = `481a7603…` = 입력 파일 sha1. provenance `camera.given_to_director: true`.

자료: `hormuz_ai_cam/`(qa_loop.json, qa_verdict.v1·v2, checks.v1~v3, sheet.v1~v3, revision.v2·v3, direction.v1~v3, camera_suggest_input.json, ai_run.jsonl, provenance.json).

## 결과 비교 (6.9 실행 2 ↔ 이번)

| 판 | 6.9 실행 2 checks hard | 이번 checks hard | 6.9 검수 hard / soft | 이번 검수 hard / soft |
|---|---|---|---|---|
| v1 연출가 초안 | 1 (offscreen 호르무즈 마커 8px) | **2** (offscreen 하메네이 뱃지 13px · 호르무즈 마커 16px) | — (checks hard 로 검수 생략) | — |
| v2 수정 1회 | 0 | 0 | 1 / 7 | 1 / 6 |
| v3 수정 2회 | 1 (offscreen 서울 마커 11px) | 0 | — | 2 / 7 |
| **선택 판** | v2 (0 · 1 · 7) | v2 (0 · 1 · 6) | | |

### 카메라 관련 지적 수
기준: 화면 밖(checks offscreen), 모서리·날짜 영역에 붙은 배치, 줌 폭(너무 넓음·좁음)을 말한 검수 지적.

| | 6.9 실행 2 | 이번 |
|---|---|---|
| checks offscreen(전 판 합) | 2 (v1 1 · v3 1) | 2 (v1 2) |
| 검수 지적(선택 판 기준) | 1 (p_0164.59 아시아 전역 넓은 지도, 매체 없음 — 매체 지적과 겹침) | 1 (p_0164.59 한국 뱃지가 날짜 아래 모서리) |
| 검수 지적(다른 판) | — | 1 (v1 검수 p_0045.03 경로 끝이 날짜 '2025' 아래) |

## 제안 채택
연출가 v1 카메라 10개 중 제안값과 같은 것 0. 가까운 것(중심 1° 안·w 10% 안) 2개 — open 첫 숏(6.6 ↔ 제안 6.69), war(14.0 ↔ 14.2).
연출가는 호르무즈 한 점 숏을 w 24 로 두었다(제안 2.5). debate 3.4(제안 2.5), review·now 90(제안 80.7). 전환도 제안 dip 대신 자기 문법(원래 cut·move)을 유지했다.
→ **제안은 옵션으로 작동했다**(P8). 연출가가 받아들이지 않은 값은 그대로 두었다. provenance `used: 0`.

## 판단
- 선택 판 기준 결과는 같거나 조금 낫다(soft 7→6, hard 동일, checks 0 동일). 차이가 LLM 흔들림(6.9 실측: 같은 초안 네 번 검수 지적 수 8~11) 범위 안이라 **제안 입력의 효과는 확인되지 않았다**.
- v1 offscreen 2건(하메네이 뱃지 위로 13px, 호르무즈 마커 왼쪽 16px)은 연출가 자신의 카메라·배치 결과다. 제안값은 6.9 v2 초안의 장소 배치로 계산·경로 검증한 값이라, 배치가 다른 이번 v1 에 대해 '제안을 따랐으면 담겼다'고는 말할 수 없다(검증하지 않음).
- 연출가가 제안을 거의 따르지 않은 이유 후보: ① 제안이 '참고용, 강제 아님'으로 적혀 있다. ② 단일 장소 숏의 w 2.5 는 맥락 폭이 없는 값이라 연출 의도(권역 보여 주기)와 어긋난다.
  ②는 R-0067 '단일 장소 숏 w 하한' 안건과 같은 뿌리다.
- 수정 2회차가 더 나빠지는 패턴(v3 hard 2)은 6.9 와 같다 — 판 선택(D-0049)이 v2 를 골랐다.
