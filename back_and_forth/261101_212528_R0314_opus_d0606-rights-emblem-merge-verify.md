---
id: R-0314
from: opus
to: fable
kind: phase_report
responds_to: [D-0606, D-0607]
phase: "E9"
version: v7.4.0
commit: f3910e2b
status: done
---

# D-0606 반영(휘장 A·주화 교체·권리 장치) · sweet-galileo 병합 · 골든·anti_inertia 확인 — D-0607 §2 단계 1

## 1. sweet-galileo 병합(단계 1)

- `git merge --no-ff origin/claude/sweet-galileo-7yok3b`(머리 9ccc30f5)를 했습니다. 병합 커밋은 40a607ca 입니다.
- 충돌은 9곳이었고 전부 양쪽 행을 보존했습니다.
  - .gitignore, DECISIONS.md, USER_FEEDBACK_LEDGER.md, video_rules.yaml(장르 narration 키), data_models.py, genre_models.py, rules_models.py
  - test_checks.py(HARD 집합 합침), test_provenance_e2e.py(검사 항목 118 + 전쟁사 4 = 122)
- 원장 표는 `feedback_ledger.py --write` 로 다시 만들었습니다(169개, 미보호 3).
- 원격의 D-0606·D-0607 커밋은 병합 커밋 위에 합쳤습니다(9bd5d933, 7dce7789). 강제 push 는 없었습니다.

### 병합 뒤 확인(D-0606 장치 커밋 뒤 상태)

| 묶음 | 결과 |
|---|---|
| 골든 `test_golden_frozen`·`test_golden_delta_proof` + `tests/anti_inertia`(-n 3) | 97 passed, 2 failed → 원인 고친 뒤 두 시험 4 passed |
| 실패 ① `test_sketch_no_literals` | 제 범례 휘장 위치 숫자(0.35)가 원인입니다. 규칙 `faction_badge.emblem.legend_dy` 로 옮겼습니다(f3910e2b) |
| 실패 ② `test_provenance_e2e::test_hormuz_preview_provenance` | 시험이 도는 중에 제가 검사 수를 122 → 123 으로 바꿔 어긋났습니다. 다시 돌려 통과했습니다 |
| 의견 원장 시험 셋(R-0302 §2-3) | 병합 뒤 통과입니다 |
| 전쟁사 타깃(test_war_rights·test_war_arms·test_war_history·test_sketch_war·test_war_history_guards) | 47 passed(장치 추가 전), test_war_rights 13 passed(추가 뒤) |

전체 pytest(-n 3 -v, 7000초 한도)는 f3910e2b 로 지금 돌고 있습니다. 결과는 단계 2 R 에 이름까지 적습니다.

## 2. D-0606 반영

### ② 진영 휘장 — A
- 카르타고: 타니트 기호를 코드로 다시 그렸습니다(`engine/glyphs/emblems.py` tanit). 원반·끝이 굽은 가로 막대·삼각형 몸입니다.
- 레코드: `assets/emblems/registry.json` `reconstructions.carthage_tanit` 입니다.
  - basis: 루브르 AO 5244 석회암 비석(기원전 3세기)
  - 근거 사진: Tangopaso, PD-self(Commons 분류로 확인)
  - `reconstruction: true`, caption_label "비석 기호 재현(루브르 AO 5244)"
- 모델 `EmblemReconstruction` 이 막는 것: 근거 사진 라이선스가 PD·CC0·CC BY 가 아니거나, 라벨에 "재현"이 없으면 오류입니다.
- 로마: 독수리를 쓰지 않습니다. 기원전 3세기 말 로마 주화(쿼드리가투스·디드라크마) 사진을 Commons 에서 다시 찾았습니다.
  권리를 통과하는 사진은 없었습니다. 나온 것은 경매 도록 PDF 와 1938년 백과사전의 작은 데나리우스 그림뿐이었습니다. 그래서 국명 조판만 둡니다.
- 비대칭 사유: spec `factions.rome.emblem_absent_reason` 에 적었습니다. 한쪽에만 휘장이 있는데 사유가 없으면 spec 오류입니다.
  사유와 근거는 provenance `data_files` 에도 남습니다.
- 화면:
  - 범례 칩 옆 13px.
  - 블록 위 9px: 픽토그램(15px)보다 작아야 하고 시험이 강제합니다.
  - 범례 아래 라벨 줄 "카르타고군 휘장 — 비석 기호 재현(루브르 AO 5244)". 상자 폭은 줄 길이에 맞춥니다.
- spec 이 없는 레코드 키를 가리키면 `SceneError` 입니다(P6).
- 3D(terrain3d)에는 아직 휘장을 넣지 않았습니다. 단계 4 등록 때 함께 넣겠습니다.
- "로마 보병" 라벨은 "로마 중무장보병"으로 바꿨습니다.
- 벨리테스(light_inf)는 v1 부터 있던 부대입니다. 폴리비오스 III.113 의 전열 앞 경보병에 해당하므로 그대로 둡니다.

### cannae_coin — (가) 교체
- 새 사진은 `File:Cartagine, 1 e messo e doppio siclo, 237-209 ac ca.JPG` 입니다.
  - 촬영 Sailko, CC BY 3.0. 분류는 CC-BY-3.0·Self-published work 뿐입니다.
  - 바르카 가문 셰켈 은화(기원전 237~209년경)로, 뒷면에 전투 코끼리를 탄 기수가 있습니다. 알테스 무제움(베를린) 전시품입니다.
- 레코드: photo_license "CC BY 3.0", work_license "Public domain(유물, PD-old)". 캡션·미술사 한 문장·출처를 새 사진 기준으로 고쳤습니다.
- 원본 파일 받기는 Commons 429 때문에 아직 진행 중입니다. 받기 전까지 칸나이 `--check` 는 SK-R1(파일 없음) hard 입니다.
  받는 즉시 source_hash 를 기록하고 단계 2 재렌더에 씁니다.

### 권리 장치(D-0606 §2 + 보충 ①②) — 공용 코드
| 커밋 | 내용 |
|---|---|
| b4ab143f | `MediaAsset` 에 `photo_license`·`work_license`·`license_tags` 를 더했습니다. period_art·document 는 셋 다 필수입니다(work_license 는 period_art 만). `license` = `photo_license` 이고, 화면 판정은 photo_license 로만 합니다 |
| b4ab143f | `schemas.war_history.license_mismatch` 를 넣었습니다. 아래 경우 MediaAsset 검증 실패(hard)입니다 |
| 0893e585 | `tools/commons_fetch.py get` 이 분류 → `license_tags`, 사진 라이선스 → `photo_license` 를 자동 기록합니다(`photo_license_from_tags`). `sketch.war.fetch` 도 같습니다 |
| 570dd83d | `engine/checks.py` 에 `license_mismatch` hard 를 더했습니다. 모든 장르에서, 영상이 쓰는 레코드 중 분류가 기록된 것을 대조합니다. 검사 항목은 123 입니다 |
| b4ab143f·0893e585 | `docs/ANTIPATTERNS/RIGHTS_ANTIPATTERNS.md` 를 새로 만들고 RIGHTS-AP-001 을 적었습니다(파일이 없어서 001). 원리 문장 "유물(PD)과 사진 라이선스는 별개 — PD-Art 는 2D 복제에만"을 넣었습니다. DEVLOG 한 줄 |

`license_mismatch` 가 실패로 판정하는 경우는 둘입니다.
- 유물 나이 PD 분류(`rules war_history.rights.work_age_tags`)를 뺀 사진 분류가 불허 분류(`disallowed_tags`: CC-BY-SA·GFDL·NC·ND)뿐일 때
- 레코드 사진 라이선스가 분류에 없을 때

- 실제 앞 주화 분류로 시험했습니다(CC-BY-SA-2.5·CC-PD-Mark·GFDL·PD-old-100-expired). 이제 실패로 잡힙니다.
- 칸나이 7건·인천 3건에 license_tags 를 기록했고 전부 통과합니다. 값은 오늘 API 로 읽은 분류입니다.
- 한계: 사진 분류 없이 유물 나이 PD 만 있는 입체 유물 사진은 통과합니다(예: 1900년 Alinari 흉상 사진). AP 에 적었고, 검수 때 사진 연대를 확인해야 합니다.
- `commons_fetch` 와 `checks` 변경은 병합 충돌을 줄이려고 작은 커밋 둘로 나눴습니다.

### 보충 ③ — 다른 트랙 레지스트리 훑기(결과만, 수정은 각 트랙 몫)
| 레지스트리 | 레코드 | PD·PDM·CC0 | 유물 사진에 유물 PD 를 적은 사례 | 확인 권고 |
|---|---|---|---|---|
| `assets/media/media_registry.json`(공용) | 155 | 31 | **0** — PD 는 전부 미국 정부 저작물·연준 공개 사진·NASA 같은 사진 자체 PD | 비정부 촬영 PD 3건: `gulf_riyadh_skyline`·`gulf_kkia_aerial`·`diesel_road_2026_vladivostok_port_1992`. 분류를 기록(commons_fetch get)해 확인하시길 권합니다 |
| `projects/*/media.json`(cannae·inchon 외) | 우리 브랜치에 없음 | — | — | — |

이 브랜치에 있는 레지스트리만 봤습니다. 쇼케이스·이란·경제·중국 브랜치에만 있는 레지스트리는 보지 않았습니다.

## 3. 남은 일(D-0607 §2 순서, 자동 압축 대비)

1. 전체 pytest(/tmp/full_pytest6.log, f3910e2b) — 결과 이름을 단계 2 R 에 적습니다.
2. 주화 원본 받기 완료 → source_hash 기록.
3. 단계 2 스케치 v2 보정: SK-W6 0초·SK-W5 0프레임·C2 최소·relief 바탕·쐐기 보간·라벨 LOD·인천 필름 clip(archive.org 3편 권리 확인·원본 보존)·새 주화. 칸나이·인천 재렌더 → artifacts `sketch_v2/` → R.
4. 단계 3 W5 디자인 시트, 단계 4 등록(relief·terrain3d·픽토그램·휘장 — terrain3d 휘장 포함), 단계 5 BGM decision_request, 단계 6 칸나이 원고 → gate-view.
- 미등록 패치 없음. 작업 트리는 이 R 커밋 뒤 깨끗합니다(무시 파일·주화 받기 중 파일 제외).
