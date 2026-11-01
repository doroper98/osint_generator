---
id: R-0303
from: opus
to: fable
kind: phase_report
responds_to: [D-0605]
phase: "E9"
version: v7.4.0
commit: e029c8f7
status: needs_decision
---

# 구상 컷 v2(D-0605) — ③ 병종 픽토그램·① 입체감 완료, ② 휘장은 결정 요청 · 기존 주화 레코드 권리 문제(긴급)

## 0. 먼저 보실 것 — 기존 레코드 권리 문제(긴급)

W4 칸나이 스케치의 `cannae_coin`(카르타고 4분의 1 셰켈 은화)은 화면 허용 라이선스 밖입니다.
레코드에는 "Public domain"으로 적혀 있습니다. 그러나 이는 주화(유물) 자체의 PD-old-100 입니다.
사진은 CNG 가 찍은 입체 유물 사진입니다. 그래서 사진 자체의 라이선스가 따로 붙습니다.
Commons API 로 직접 확인했습니다(2026-11-01). 붙은 틀은 Template:CNG·Template:GFDL 입니다.
분류는 Category:CC-BY-SA-2.5·GFDL 입니다. 사진은 CC BY-SA 2.5 / GFDL 입니다.
rules war_history.rights.allowed_licenses 에 들지 않습니다. CC BY-SA 는 저장 안 하는 참고 정합에만 허용입니다.
이 컷은 판정 ① 용으로 이미 보냈습니다(sketch_v1). 제가 권리를 잘못 판정했습니다.
처리 방안은 결정을 받겠습니다(§3-3). 그 전까지 이 레코드로 새 렌더를 만들지 않습니다.

## 1. 산출 — artifacts `ce7acab8`, `war_history/concept_v2/`

| 파일 | 내용 |
|---|---|
| `relief_cannae_t36_v2.png` | 2D relief 480p, 병종 픽토그램·입체 블록·대열 격자 |
| `dark_cannae_t36_v2.png` | 같은 시각 dark 테마 |
| `relief_v1_vs_v2.png` | 왼쪽 concept v1 · 오른쪽 v2 |
| `terrain3d_still_v2.png` · `terrain3d_orbit_8s_v2.mp4` | 3D 박스·바닥 그림자·대열 기둥 380개·병종 빌보드, 8초 궤도 240프레임 |
| `arms_glyph_gallery.png` | 글리프 6종 × 규칙 크기·2배·5배 × 진영색 둘 |
| `rules_v2.json` | 이 컷에 쓴 규칙 키 값 전부 |
| `spec_v1_reclassified.yaml` | v1 spec 에서 부호 이름만 새 분류로 바꾼 것(위치·키 그대로) |
| provenance 두 개 · RIGHTS.md · MD5SUMS | |

v1 과 바로 비교되도록 concept v1 과 같은 v1 spec 을 썼습니다. 부호 이름만 바꿨습니다.
저장소의 `projects/cannae_sketch/sketch.yaml`(v2 spec)도 같은 분류로 고쳤습니다.

## 2. 구현 — 규칙 키 표

### ③ 병종 픽토그램

| 규칙 키 | 값 | 비고 |
|---|---|---|
| `war_history.symbol_sets.ancient.units` | heavy_inf·light_inf·heavy_cav·light_cav·skirmisher·elephant | v1 이름(infantry_block 등)은 지웠습니다(P2) |
| `…ancient.shapes` | 보병 = block, 기병 = wedge, 투석병 = dots, 코끼리 = big_dots | 근세·현대 세트도 shapes 를 갖습니다 |
| `…ancient.glyphs` | 병종 → `engine.glyphs.arms.GLYPHS` | 없는 이름은 오류입니다(시험) |
| `war_history.symbol_sets.glyph` | size_px 15, halo_px 1.4, alpha 0.95, dy −4 | 크기는 제 제안 값입니다. dy 는 이름 줄과 겹치지 않게 넣었습니다 |

- 글리프는 코드 벡터입니다. 중보병 = 방패 뒤 볏 투구와 세운 창, 경보병 = 투창 든 사람입니다.
- 기병은 둘입니다. 중기병 = 말·기수·앞으로 겨눈 긴 창·방패, 경기병 = 말·기수·치켜든 투창입니다.
- 투석병 = 머리 위 투석끈, 코끼리 = 윤곽입니다.
- 갤러리: `python tools/element_gallery.py --arms <png>`. 시험이 GLYPHS 전부가 칸에 있는지 봅니다.
- 칸나이 분류 근거는 spec 주석에 적었습니다. 폴리비오스 『역사』 III.113(배치), III.114.1(리비아 보병 로마식 장비), III.114.2~4(히스파니아·켈트 장비)입니다.
- 절 번호는 III.114 만 세부 절까지 적었습니다. III.113 의 세부 절은 원문으로 확인하지 못해 장 단위로만 적었습니다.
- "아프리카 보병" 라벨은 "아프리카 중무장보병"으로 바꿨습니다.

### ① 입체감

| 규칙 키 | 값 | 비고 |
|---|---|---|
| `war_history.symbol_sets.depth` | side_ratio 0.12, side_min_px 1.5, side_dark 0.55, top_alpha 1.0, shadow_alpha 0.35, shadow_px [3,3], rim_alpha 0.5, rim_w 0.9 | 감독 제안 값 그대로이고, side_min_px·side_dark·top_alpha 는 제가 더했습니다 |
| `…rank_grid` | gap_px 3.2, max_lines 6, w 0.6, alpha 0.4, inset 0.18, shapes [block, wedge] | 고정 간격입니다. 병력 입력이 없습니다 |
| `sketch.war.terrain3d` 추가 | unit_height_m 110, shadow_offset_m 70, dot_r_m 28, rank {gap_m 70, post_h_m 22, post_w_m 12, max_posts 600}, glyph_px 30 | 전부 제 제안 값입니다(사용자 합격 값 아님) |

- 2D 순서: 바닥 그림자 → 보이는 단면(진영색 × 0.55) → 윗면(불투명) → 대열 격자 → 어두운 윤곽 → 빛 받는 변 밝은 선.
- 단면은 아래·오른쪽입니다. 회전한 블록·쐐기는 변마다 바깥 법선으로 판정해 같이 돕니다.
- 보병 격자는 정면과 나란한 줄, 기병 격자는 진행 방향 줄입니다.
- 윗면을 불투명으로 바꿨습니다. 반투명이면 단면이 비쳐 탁해집니다. v1 의 fill_alpha 0.82 와 다릅니다.
- 3D: 2D 와 같은 윤곽을 ExtrudeGeometry 로 세웠습니다. 윗면 = 진영색, 옆면 = 진영색 × 0.55 입니다.
- 3D 바닥은 윤곽 아래 지표 최저점입니다. 비탈에서도 뜨지 않습니다.
- 바닥 그림자는 해 반대쪽 70 m 입니다. 대열 기둥은 InstancedMesh 이고, 고정 간격 격자 중 윤곽 안 점입니다.
- 병종 그림은 2D 와 같은 글리프를 PNG 로 굽습니다. 화면 위 겹 그림(빌보드)으로 윗면 위에 둡니다.
- R-0301 §3 의 "3D 는 사각 면" 문제는 해소됐습니다. 쐐기는 3D 에서도 쐐기입니다.

## 3. 결정 요청 — ② 진영 휘장

권리 조건을 통과하고 유물에 근거한 벡터 도안은 Commons 에 양쪽 모두 없었습니다.
Tanit SVG 둘·"Aquila Romana"는 CC BY-SA 4.0 입니다. "Carthaginian Empire flag"는 현대 창작 깃발입니다.
남는 것은 유물 사진과, 그 사진을 근거로 한 코드 재작도입니다.

### 3-1. 사실 문제 — 로마 독수리는 시대가 맞지 않습니다
플리니우스 『박물지』 X.16 에 따르면 마리우스가 기원전 104년에 독수리를 유일한 군단 표지로 정했습니다.
그 전에는 독수리·늑대·미노타우로스·말·멧돼지 다섯 표지가 있었습니다.
기원전 216년 로마군 진영 휘장으로 독수리 하나를 내세우면 시대가 맞지 않습니다.
찾은 독수리 도안은 전부 마리우스 이후입니다. 셋 다 CC BY 2.0 입니다.
- 안토니우스 군단 데나리우스 뒷면, 기원전 32~31년, 독수리와 군기 둘. 최선 후보입니다.
- 같은 종류 다른 개체 하나. 위조 가능성이 기록에 있습니다.
- 포스투미우스 데나리우스, 기원전 81년. 독수리가 작습니다.

### 3-2. 카르타고 후보
- 타니트 기호 비석(루브르 AO 5244, 기원전 3세기, 석회암): Public domain(PD-self)입니다. 시대가 맞습니다.
- 출토지는 기록에 없습니다. 토펫 출토는 확인되지 않았습니다.
- 타니트 기호 비석(루브르 AO 23068): CC0 입니다. 설명 칸이 비어 있습니다.
- 시칠리아·카르타고 주화(말과 종려나무, 기원전 320~280년경): CC BY 2.0 입니다.

### 3-3. 선택지(구현 세션 권고 = A)
- **A. 둘 다 당대 상징만.** 카르타고 = 타니트 기호를 루브르 AO 5244 근거로 코드 재작도합니다. 캡션은 "비석 기호 재현"입니다.
  로마 = 독수리를 쓰지 않습니다. 기원전 3세기 말 로마 주화 도안(예: 쿼드리가투스)을 찾습니다.
  아직 찾지 않았습니다. 권리 조건을 통과하는 사진이 없으면 로마는 국명 조판만 둡니다.
  양쪽 표기가 달라지면(한쪽만 휘장) 그 사유를 기록합니다.
- **B. 독수리를 후대 도안으로 표기하고 씁니다.** 안토니우스 데나리우스 근거로 재작도하고 캡션은 "후대(기원전 1세기) 주화 도안 재현"입니다. 카르타고는 A 와 같습니다.
- **C. 휘장 없이 갑니다.** 진영명 조판과 색만 둡니다(v1 그대로). 대신 병종 픽토그램이 정체성을 맡습니다.

같이 결정이 필요한 것 — `cannae_coin` 처리(§0):
- (가) 같은 바르카 가문 주화의 PD·CC BY 사진을 다시 찾아 바꿉니다.
- (나) 이 카드를 빼고 다른 period_art 로 증거 층을 채웁니다.
- 어느 쪽이든 판정 ① 에 보낸 sketch_v1 의 해당 컷을 사용자에게 정정 고지해야 하는지도 판단을 부탁드립니다.

## 4. 검증

- 관련 시험: `tests/test_war_arms.py`(신규 8건)·test_war_history·test_war_history_guards·test_sketch_war·test_sketch_common·test_sketch_integration → 53 passed, 6 skipped.
- 신규 시험이 보는 것: 레지스트리 대조, 고대 병종 전부 글리프, 갤러리 칸, 없는 글리프 오류, 모양 조회, v1 부호 이름 삭제, 대열 기둥 고정 간격·윤곽 안·결정적.
- tests/anti_inertia(-n 4): 88 passed, 3 failed. 실패 셋은 의견 원장 시험이고 R-0302 §2-3 과 같습니다(감독 소관).
- 커밋 직후 원장 표가 재생성됐습니다(1a7d7d67). 이 시험 셋이 지금도 실패하는지는 아래 전체 pytest 에서 봅니다.
- 전체 pytest(-n 3 -v, 시간 한도 7000초)는 지금 돌고 있습니다. 끝나면 실패·오류 이름 전부를 다음 R 에 올립니다.
- 골든 영향: 바뀐 규칙은 war_history·sketch.war 뿐이고 본 엔진 경로는 바뀌지 않았습니다. 골든은 전체 pytest 결과로 확인합니다.
- slop_check: 이 R 0건.

## 5. 남은 일(자동 압축 대비)

1. ② 휘장 — §3 결정 대기. 결정이 오면 레지스트리 레코드(basis·reconstruction)·범례 옆·블록 위 작은 휘장·캡션 라벨 장치를 붙입니다.
2. `cannae_coin` 처리 — §3-3 결정 대기.
3. 전체 pytest(/tmp/full_pytest5.log) 결과 R.
4. 사용자 판정 ①(W4 스케치·구상 컷) 대기. W5·W6 금지 그대로.
5. v1 spec SK-W6·SK-W5 위반 수정, 유적 층 CC BY-SA 질문, 인천 필름 권리 확인 — 지시 대기.
- 미등록 패치 없음. 브랜치 head = 이 R 커밋.
