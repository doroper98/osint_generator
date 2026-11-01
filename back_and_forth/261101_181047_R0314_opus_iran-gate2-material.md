---
id: R-0314
from: opus
to: fable
kind: gate_request
responds_to: [D-0456, D-0459]
phase: "IR2"
version: v7.4.0
commit: HEAD
status: awaiting_decision
---

# 게이트 ② 자료 — 콘티 판 v4(연출 v8) · 프리뷰 hard 0 · econ-template 병합

## 1. 자료(artifacts/iran-ceasefire-v7.4.0 5096dbf)
- `iran_ceasefire_2026/animatic_v4/animatic_v4.mp4` — 27.9 MB(영상 250 kbps·`-c:a copy`), 483.0초, md5 `f89cd4b95c42346d992f4d822fdea3d7`.
- 같은 폴더: `animatic_v4_sheet.jpg`(24초 간격 20컷), `animatic_v4_panels.jpg`(패널 8컷 확대), checks, provenance, MD5SUMS.
- `iran_ceasefire_2026/preview/`: `preview_sheet.jpg`(18컷), `preview_checks.json`, `preview_provenance.json`, MD5SUMS.
- script_sha1 `4a47c0a2…`(게이트 ① 지문과 같음). direction_sha1 `3525efd4…`(v8).
- 콘티 판 v3(연출 v7)도 hard 0 이었습니다. D-0459 지적 3곳이 그 판에 남아 있어 올리지 않았습니다. v4 가 대체합니다.

## 2. checks
| 판 | hard | warning | label-in-body(forbidden) |
|---|---|---|---|
| 콘티 판 v4 | 0 | 46 | 0 |
| 프리뷰(--preview auto, 병합 뒤 엔진) | 0 | 48 | 0 |

- provenance `user_feedback_guards` 83건이 돌았습니다. UF-170 → `forbidden: 0`.
- 프리뷰 warning 은 콘티 판과 같은 항목에 `map_contrast_shape` 2건(394초·421초 항로선 gold 대비 2.54·2.88)이 더해졌습니다.

## 3. 바뀐 컷(콘티 판 v2 → v4)
- v7(D-0458): 2003 소해함 사진을 지웠습니다. 그 자리에 IRGC·CENTCOM quote 두 줄을 넣었습니다. 앙카라 전용기 사진, 루비오·샤리프 뱃지, act6_0~1 한국 강조를 넣었습니다. 푸자이라를 지명 사전에 등재했습니다.
- v8(D-0459) ① 시간축 10/11 "레자이 '불충분'" 을 -2단에서 -1단으로 내렸습니다. 제목·부제 줄과 겹치지 않습니다(176초 컷). `label_collision`·`island_label_overlap` 0.
- v8 ② 보험료를 한 계열로 바꿨습니다(0.25 → 6.00, 이름 "선가 대비(범위 하단)"). 부제는 "10월 6~10% 중 하단 표시" 입니다. 시작 라벨은 한 번만 나옵니다.
  - 상단 계열을 빈 값으로 두는 안은 스키마가 거부했습니다(계열당 값 2점 이상).
  - 과장을 피하려고 상단이 아니라 하단을 남겼습니다. 상단 10% 는 부제와 내레이션에 있습니다.
- v8 ③ 휘발유 축을 0~2,000(500 간격)으로 바꿨습니다.

## 4. 남은 warning 사유
- `portrait_unused` 12: act2 문장 9건은 시간축 패널이 화면을 덮는 구간입니다. 뱃지를 올리면 `badge_over_panel` hard 가 납니다.
- act3_1·act3_4 는 versus 패널 구간이고, act3_0~1 에 아라그치 사진이 있습니다. cold_2 트럼프 자리에는 루비오 뱃지와 기사 카드가 있습니다.
- act5_4 "하메네이" 는 모즈타바 하메네이입니다. 공용 초상 khamenei 는 알리 하메네이라 쓰지 않았습니다(인물 오인 방지). quote 카드로 보입니다.
- `geo_unsourced` 8 은 모두 path 입니다(israel_iran·gulf_in·doha_tehran·hz_ulsan·fuj_ulsan·yanbu_ulsan·korea_doha·tehran_doha). 지명 사전은 설계상 path 를 대조하지 않습니다(`geo/gazetteer.py` 10행). 양 끝 지명은 모두 사전과 맞았습니다.
- `media_beats` 17(기사 후보 미사용·40초 창 6개), `shots` 6, `tempo_density` 1, `article_press_missing` 1, `endcard_roll` 1(51.5 px/s ≤ 60) 은 v2 와 같은 성격입니다.

## 5. D-0456 병합(71a36ebb)
- `git merge --no-ff origin/claude/econ-template-2026`. 바뀐 파일은 192개입니다.
- 충돌 2곳:
  - `docs/handoff/DECISIONS.md`: 양쪽 행을 모두 살렸습니다(econ D314~D316·D400~D401, iran D550~D559).
  - `docs/handoff/USER_FEEDBACK_LEDGER.md`: `python tools/feedback_ledger.py --write` 로 다시 만들었습니다. 167개, 미보호 0.
- `rules/user_feedback.yaml` 은 자동 병합됐습니다(충돌 0).

## 6. 시험
- `pytest tests/anti_inertia`(병합 뒤): 82 passed, 3 failed, 9 subtests passed. 원장 시험(`test_user_feedback_guards`)은 통과했습니다.
- 실패 3건은 모두 hormuz 골든 자산이 없어서 났습니다.
  - `test_provenance_e2e::test_hormuz_preview_provenance`(골든 25 앵커)
  - `test_q3_light_e2e::test_light_preview_matches_baseline`
  - `test_catalog_layer::test_full_frame_md5_independent`
- 준비 절차(run_log §0·§4)를 돌렸습니다. 사진·초상·geo.prep(기본·720p dark)·script.plan(Supertonic)은 마쳤습니다.
- 클립 2개(strikes·niovi)는 받지 못했습니다. DVIDS cloudfront 는 프록시가 거부했고(connect_rejected), Commons 는 429 입니다.
- **골든 25 는 이 컨테이너에서 판정하지 못했습니다.** hormuz 클립이 있는 감독 컨테이너에서 위 3건을 돌려 주시거나, 클립 받는 방법을 정해 주십시오.
- 클립 재시도(media_fetch, 20분 한도)는 지금 배경에서 돌고 있습니다. 성공하면 결과를 따로 보고하겠습니다.

## 7. 결정 요청
1. 콘티 판 v4 + 프리뷰로 게이트 ② `approve --gate preview_approval` 여부(감독이 칩니다).
2. 골든 25 판정 경로(감독 컨테이너 실행 / 클립 확보 방법).
3. 승인되면 720p 전편 → `final_deliver.mp4`(≤30 MB) → artifacts `final/` → 최종 phase_report R(전체 pytest 1회 포함) 순서로 갑니다.
