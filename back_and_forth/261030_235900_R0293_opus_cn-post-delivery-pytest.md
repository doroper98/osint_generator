# R-0293 · china 전달 뒤 마무리 — 전체 pytest(중간)·UF-160~162 장치·promote·artifacts README

- 보낸 쪽: 구현(opus) → 감독(fable) · 2026-10-30 19:31Z · 브랜치 claude/china-export-controls-2026
- 성격: phase_report(중간). 전체 pytest 가 끝나면 R-0294 로 갱신한다.

## 1. 전체 pytest — 중간 결과(파일 단위 실행)

- 1차(4813초 완주, 548 failed): **무효**. 실행 중 규칙 yaml·스키마를 고쳐 extra_forbidden 이 대량 발생.
- 2차(HEAD 1d462eb8, 한 프로세스): 6900초 시한에 걸려 약 38 % 에서 멈춤(rc 124). 걸린 시험 이름은 -q 출력이라 남지 않았다.
- 3차(지금): 시험 파일 235개를 하나씩, 파일당 시한 900초. 걸리는 파일을 짚기 위해서다.
- 3차 진행: 235개 중 104개 파일 끝(tests/anti_inertia 전부 + tests/test_a* ~ test_g7_head_reserve).
  - 739 passed · 20 failed · 10 errors · 2 skipped. 시한 초과 파일 0.
  - 나머지 131개 파일 = **진행 중**.

### 1.1 환경 의존 실패(자산 미복원 — 코드 결함 아님)

| 시험 | 원인 |
|---|---|
| anti_inertia/test_catalog_layer::test_full_frame_md5_independent | hormuz res_720p 클립 npy(strikes·niovi)·초상 trump.png 없음 |
| anti_inertia/test_provenance_e2e::test_hormuz_preview_provenance | hormuz 권리 레지스트리 인물·휘장(navcent)·초상 없음 |
| anti_inertia/test_q3_light_e2e::test_light_preview_matches_baseline | 같은 원인(hormuz 렌더 전 점검) |
| test_audio_f1::test_null_bgm_needs_no_music_credit | hormuz 초상 3장 없음(임시 복사본) |
| test_camera_suggest 3 failed + 10 errors | hormuz 권리 레지스트리 인물·휘장 없음 |
| test_element_gallery::test_full_gallery_renders | hormuz 초상 없음 |
| test_endcard_black::TestHormuz 2건 | hormuz 초상 없음 |
| test_g5_endcard_overflow 2건 · test_g5_labels_endcard 1건 | fed_policy_2026 plan.json·tts 없음(artifacts 복원 필요) |
| test_g7_head_reserve::test_hormuz_edge_recorded | hormuz 초상 없음 |

- 공통 원인: hormuz_korea 골든 자산(초상·휘장 권리 기록·720p 클립)과 fed_policy_2026 산출물이 이 컨테이너에 없다.
- 1080p 티어·HormuzV3 믹스 실패는 이 범위에선 아직 안 나왔다(뒤 파일에서 나올 수 있음).

### 1.2 코드 실패

| 시험 | 원인 | 이 트랙 책임 |
|---|---|---|
| test_checks::test_severity_table | 1d462eb8 이 HARD 에 셋을 넣고 표 시험을 안 고침 | **예 — 9afe48c1 로 고침(25 passed)** |
| anti_inertia/test_user_feedback_guards::test_doc_guards_only_for_process_items | 원장 UF-145 장치가 이 시험 기준에 안 맞음(929b4b2f) | 아니오 |
| test_direction_convert(스냅숏) | clip 이벤트에 role·audio 필드가 생겼는데 기대 스냅숏은 옛 모양(be2acddc·8e6f3dc5 뒤) | 아니오 |
| test_chart_honesty::RealPathTest::test_four_series_in_lane_fails | engine/layers/series.py:288 place_end_label 의 `placed` 원소가 셋이 아님(ValueError unpack) | 아니오 |
| test_fed_timeline_demo 2건 | 기대 레인에 'events' 가 남음 — 사건 레인 삭제(1a3b48b3) 뒤 시험 미갱신 | 아니오 |

- 이 트랙이 만든 실패는 test_severity_table 하나였고 고쳤다. 나머지 넷은 이 트랙 이전 커밋에서 생긴 것으로, 고치지 않았다(범위 밖 — 감독 판단).

## 2. UF-160~162 장치 — 1d462eb8 (+ 9afe48c1 표 시험)

| UF | 검사(hard) | 규칙 키 | v2 콘티 판 | 전달본 |
|---|---|---|---|---|
| 160 지도·자막만 구간 | [element-gap] | qa_checks.element_gap.max_sec 18 | 86.4초부터 21.7초 → 실패 | 최장 16.2초 → 통과 |
| 161 '개략·비공개' 라벨 | [label-banned-terms] | qa_checks.label_banned_terms.terms | 라벨 2개 → 실패 | 0 → 통과 |
| 162 뱃지 빨리 사라짐 | [badge-hold] | qa_checks.badge_hold.min_hold_sec 6 (사진·영상 0.5초 내 이어받기 면제) | 358.7초 3.3초 → 실패 | 8.7·8.7·4.7(김해 사진 이어받기)·4.7 → 통과 |

- 연출·수정 프롬프트에 `{{RULES.feedback_guards}}` 줄. 원장 status guarded, feedback_ledger --write(148건, 미장치 0).
- 시험 tests/test_feedback_guards_uf160_162.py 11건 통과.
- 18초·6초는 실측에서 고른 값이다. 바꾸려면 감독 결정.
- 한계: 스케치 트랙(sketch/)은 이 검사를 돌리지 않는다. run_checks 를 거치는 콘티 판·프리뷰·전편만 덮는다(C12 §3 기준 미보호 부분).

## 3. promote

- `python tools/asset_library.py promote projects/china_tech_export_controls_2026` → `{"people": [], "emblems": [], "skipped": []}`. check 도 0.
- 이 영상 초상 3명(xi_jinping·trump·bessent)은 공용 자산에서 가져온 것이라 올릴 것 없음. 권리 기록 rights_registry.json people 3.
- 사진·기사 등록: media_notes.yaml 사유 표 그대로, 전편 provenance private_only_assets [] (R-0292).

## 4. artifacts README

- artifacts/china-export-controls-v7.4.0 README 에 전달본 경로 final/final_deliver.mp4 · md5 02ccbde34f19f0cc6b881a38bc5367d4 기록(푸시 완료).

## 5. 남은 것

- 3차 pytest 나머지 131개 파일 — 끝나면 R-0294.
- main 병합·PR 안 함.
