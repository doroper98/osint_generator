# R-0294 · 전체 pytest 최종 집계 (R-0293 갱신)

- 보낸 쪽: 구현(opus) → 감독(fable) · 2026-10-31 · 브랜치 claude/china-export-controls-2026
- 실행: 파일 단위 235개(파일당 900초) → 시한 초과 3파일은 시험 단위(300초 → 1200초) 재실행. 코드 기준 1d462eb8~fe750883(시험 파일 외 엔진 변경 없음).

## 1. 집계

| 수집 | passed | failed | errors | skipped | 미완 |
|---|---|---|---|---|---|
| 1,956 | 1,901 | 24 | 15 | 15 | 1 |

- 미완 1: tests/test_g8_animatic.py::AnimaticMapRenderTest::test_deterministic_md5 — 1200초 안에 안 끝남.
- 멈춤(stall)은 없었다. 시한 초과 3파일(test_g8_animatic·test_gates_pipeline·test_v740_rollback_script_draft)은 시험마다 준비에 3~11분이 걸려 파일 합이 900초를 넘은 것이다. 네트워크 대기 아님. 고치지 않음(범위 밖).
- 2차 한 프로세스 실행이 6900초 시한에 38 % 에서 멈춘 것도 같은 이유(느린 시험 누적)로 본다.

## 2. 실패 표

### 2.1 환경 의존 — failed 18 · errors 13

| 원인 | 시험 |
|---|---|
| hormuz_korea 골든 자산 없음(초상 trump·roh_moo_hyun·lee_jae_myung, 권리 레지스트리 인물·휘장 navcent, res_720p 클립 npy) | anti_inertia/test_catalog_layer 1 · anti_inertia/test_provenance_e2e 1 · anti_inertia/test_q3_light_e2e 1 · test_audio_f1 1 · test_camera_suggest 3F+10E · test_element_gallery 1 · test_endcard_black 2 · test_g7_head_reserve 1 · test_phase10_label_hidden 1 · test_phase10_scale 3E · test_placement_slots 1 · test_source_credits 1 |
| fed_policy_2026 plan.json·tts 없음(artifacts 복원 필요) | test_g5_endcard_overflow 2 · test_g5_labels_endcard 1 |
| HormuzV3 전편 산출물(믹스) 없음 | test_v3_voice::HormuzV3Test 1 |

- 1080p 티어 실패는 이번에 나오지 않았다(720p 티어는 앞서 geo.prep 로 복원).

### 2.2 분기점 기존 코드 실패 — failed 5 · errors 2 (4건, 손대지 않음)

| 건 | 시험 | 원인 |
|---|---|---|
| ① UF-145 원장 | anti_inertia/test_user_feedback_guards::test_doc_guards_only_for_process_items | UF-145 장치가 시험 기준과 안 맞음(929b4b2f) |
| ② 연출 변환 스냅숏 | test_direction_convert 1 | clip 이벤트 role·audio 필드 추가 뒤 기대 스냅숏 미갱신 |
| ③ 끝값 라벨 | test_chart_honesty::RealPathTest::test_four_series_in_lane_fails | engine/layers/series.py:288 place_end_label `placed` 원소 수 불일치(ValueError unpack) |
| ④ fed_timeline_demo | test_fed_timeline_demo 2F · test_g8_animatic::AnimaticRunTest 2E | 예제 연출이 사건 레인 삭제(1a3b48b3)·뒤 hard 검사([media-density]·[plot-height]·[axis-empty-band])에 안 맞음. 이 트랙 검사 셋은 해당 없음 |

### 2.3 이 트랙 코드 — 0

- test_checks::test_severity_table 은 1d462eb8 누락이었고 a2924c88 로 고쳤다(재실행 통과). 최종 집계 24 failed 에는 고치기 전 실행분 1건이 들어 있다 — 고친 뒤 기준으로는 23.

## 3. 끝

- 새 작업 없음. main 병합·PR 안 함.
