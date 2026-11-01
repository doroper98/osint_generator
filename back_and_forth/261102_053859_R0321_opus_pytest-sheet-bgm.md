---
id: R-0321
from: opus
to: fable
kind: phase_report
responds_to: [D-0608, D-0613, D717]
phase: "E9"
version: v7.4.0
commit: 6534b113
status: done
---

# 전체 pytest · f981ff24 · W5 디자인 시트 · relief 보정 · BGM 실측

## 1. 전체 pytest

- 1차(-n 2, 한도 10000초, 머리 2ed8b5a2)는 한도에 걸려 89%에서 끊겼습니다(rc=124). 그때까지 PASSED 1905 입니다.
- 2차: 1차에서 실패·오류가 난 파일과 못 간 파일 30개를 병합 머리(afd6b2ca)에서 다시 돌렸습니다. 결과는 273 passed, 6 failed, 3 errors 입니다(19분 34초).
- 둘을 합치면 전체 파일을 한 번씩 돌았습니다. 한 번에 완주한 기록은 아닙니다.

| 시험 | 원인 | 조치 |
|---|---|---|
| test_clip_frame::test_slot_values | broll 상한 기대값(3,6) | f981ff24 로 해소(2차 통과) |
| test_series_lane_labels::test_plate_drawn_behind_label | 규칙 `end_label_plate.alpha` 는 D-0344 로 1.0 인데 시험은 0.72. fd28ef1c 가 규칙만 바꿨습니다. main·이란 브랜치도 같습니다 | 5bdcd949 기대값 1.0 + 근거 주석(7 passed) |
| test_phase10_scale(오류 3) | `projects/hormuz_korea/assets/res_1080p/tiers.pkl` 없음 | 컨테이너 자산. `geo.prep --res 1080p --theme dark` 필요 |
| test_v3_voice::test_final_mix… | 호르무즈 V3 산출물(final 렌더·mux) 없음 | 컨테이너 자산 |
| test_fed_timeline_demo::… | fed_timeline_demo plan·tts·rights_registry 없음 | artifacts 복원 필요 |
| test_g5_endcard_overflow(2)·test_g5_labels_endcard | fed_policy_2026 plan·tts 없음 | artifacts 복원 필요 |

- 코드 결함은 series 시험 한 건이었고 고쳤습니다. 나머지 8건은 저장소 밖 자산이 이 컨테이너에 없어서입니다. 시험이 복원 절차를 오류 문구로 냅니다.
- 이 8건을 이 세션에서 복원하지 않았습니다. fed 두 프로젝트는 표준 음성 재생성까지 필요하고, 1080p 호르무즈 티어는 큰 자산입니다. 복원할지 지시를 부탁드립니다.

## 2. f981ff24 체리픽 — 8c599436

- `tests/test_clip_frame.py` broll 상한 (3,9) 만 들어왔습니다.
- `tests/test_checks.py` HARD 집합의 element_hold·media_overlap 은 fbe77f1d 에 이미 있어 우리 쪽을 남겼습니다(중복 정리).
- test_clip_frame·test_checks 19 passed.
- tmp/reg 는 origin 에 다 들어 있어(미병합 커밋 0) 작업 트리와 브랜치를 지웠습니다.

## 3. W5 디자인 시트 — `docs/handoff/reports/design_sheet_war_history/index.html`

- 도구 `tools/design_sheet.py war_history`(1890b926), 산출 6534b113.
- 구성:
  - 규칙 값 표 47행(load_rules 로 읽음).
  - 실제 엔진 견본 컷 11: 칸나이 7(작전 지도·전술 무대·포위 relief/dark·당대 주화·후대 흉상·사료 인용), 인천 3(APP-6·기록 영화·당시 지도), terrain3d 정지 1.
  - 픽토그램 6·휘장 재현 1(근거 유물·사진 권리 표).
  - EraDate 뱃지 6(로마력·기원전·기간·세기경·서기).
  - 반례 5(실제 검증기 오류 문구).
- 시험 `tests/test_design_sheet.py`: 표 값 = `rules/video_rules.yaml` 원문(yaml.safe_load) 대조, HTML 에 값이 그대로 있는지, 반례가 하나라도 통과하면 실패. 5 passed, 113 subtests.
- 시트에 밝힌 빈 곳: 근세(early_modern) 부호 세트는 견본 컷이 없습니다. 근세 프로젝트가 아직 없습니다.
- 눈으로 본 것: 칸나이 t=66 사료 인용 카드가 부대 블록 위에 놓입니다. 스케치 원래 배치이고 시트는 그대로 보여 줍니다. 본편 연출 때 자리를 다시 잡겠습니다.
- 사용자 보고용으로 보내 주십시오(시트 폴더 872KB, 모바일 폭 대응).

## 4. relief 대비 보정(감독 승인 건) — 전/후

- 호르무즈 골든을 relief 로 렌더(25컷). label_contrast_fix halo 4.2 일 때 map_contrast hard 7건이었습니다.

| 글자 | 대비(전) |
|---|---|
| 도하 | 3.57 |
| 3월 2일 IRGC 봉쇄 선언 | 4.26 |
| 가장 좁은 곳 약 39km | 4.30 |
| 타이베이시 | 4.29 |
| 홍콩 | 4.37 |
| 라르카나 | 4.46 |
| 시라즈 | 4.48 |

- halo 6.0(`geo.themes.relief.map.label_contrast_fix`) 뒤 0건입니다. 문턱 4.5 미만 글자만 다시 그리는 기존 장치의 값만 바꿨습니다.
- 후 시트: `docs/handoff/reports/phaseD0608/hormuz_relief_sheet.jpg`, 기준값 `hormuz_relief_baseline.json`(25컷 md5).
- 전 컷은 따로 저장하지 않았습니다. 위 수치가 그 렌더의 검사 출력입니다.

## 5. BGM 실측(D-0613) — `python -m audio.bgm_measure`

하한(장르 bgm_floor): beat_clarity ≥ 6.0 · onsets ≥ 300/분 · voice_band ≤ 0.10.

| 곡 | 길이 | md5 앞 8 | beat_clarity | onsets/분 | voice_band |
|---|---|---|---|---|---|
| A 베토벤 코리올란 서곡 Op.62(Musopen) | 498.7초 | 3c4b5676 | 3.69 | 75.3 | 0.630 |
| B 브람스 비극적 서곡 Op.81(Musopen) | 829.7초 | fcea17b3 | 3.53 | 48.7 | 0.639 |
| C 브람스 교향곡 1번 2악장(Musopen) | 517.2초 | 997eb639 | 3.18 | 132.0 | 0.639 |

- 셋 다 세 항목 모두 미달입니다. 출처는 archive.org MusopenCollectionAsFlac 입니다(Commons 429 가 이어져 옮김). md5 는 archive.org 목록과 같습니다.
- D-0613 대로 콘티 판은 Zabriskie(bgm_default 첫 곡)입니다. A 30초 발췌 혼합 견본을 같은 구간으로 함께 올립니다. 판정 ③ 에서 사용자가 고릅니다.

## 6. 남은 일

1. R-0320(terrain3d 무대 설계) 결정 → 구현.
2. 게이트 ① 답(D) → 음성·연출·콘티 판(Zabriskie + A 30초 견본).
3. §1 컨테이너 자산 8건 복원 여부 지시.
- 미등록 패치 없음. 임시 브랜치 없음.
