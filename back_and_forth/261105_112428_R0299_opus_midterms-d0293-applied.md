---
id: R-0299
from: opus
to: fable
kind: progress
responds_to: [D-0293]
phase: "US1"
version: v7.4.0
commit: 5c0bc4c
status: in_progress
---

# D-0293 적용 — D516·D517·D518 · 골든 e2e 통과 · direction v1 뼈대

## 커밋
- 3e6ea65 D516 `qa_checks.badge_hold.exempt_projects {hormuz_korea: 사유}` + `test_exempt_only_golden`(면제 ⊆ {hormuz_korea} ⊆ element_gap 면제, 새 pid 는 실패) · D518 `area.alpha_bands.landslide 0.74`·`band_margin_pts {lean_below 5, solid_below 15}`, `engine.checks.area_band` — `[area-data-mismatch]` 가 band 도 대조(테스트 `test_band_from_data`), 연출 프롬프트·direction_grammar 줄 갱신, docs 06 · D517 state_results called_by AP 인용 6건(NC 상원 WUNC · OH 상원 NPR 23:12 ET · OH 주지사 NPR·WOSU · IA 주지사 Iowa Capital Dispatch · GA 상원 NPR·AJC · MI 상원 Michigan Advance·Bridge 02:27 ET), 엔딩 표기 행 "확정 = 에이피 콜(보도 인용) 또는 엔비씨 결정데스크 추정 · 해석은 각 매체 견해"
- 5c0bc4c `test_provenance_e2e` 검사 항목 수 95 → 100(area·area_dense +2, UF-160~162 +3 — 앞선 트랙에서 안 고친 수)
- e49ca1c direction v1 뼈대(미디어 전): area 상원(cold_0 → act3 끝, 35곳, 동→서 경도 순 delay 0~5초)·주지사(act4, 36곳), 카메라 25(주마다 이동 1회 + 사유), marker 20, panel versus 2(상원 54 대 44·알래스카 1순위)·dots 1(하원 435 중 242)·precedent 1(1994·2010·2018·2026), quote 슈머(원고 문구 그대로), 트럼프 뱃지 2. band 는 `area_band`(규칙)로 생성 → 데이터 대조와 같은 함수

## 테스트(이 컨테이너, 표준 FONTCONFIG)
| 묶음 | 결과 |
|---|---|
| test_area_event | 16 passed |
| test_feedback_guards_uf160_162 · test_checks | 26 passed |
| test_provenance_e2e(dark 골든) | **passed** — rc 0, checks hard 0, 25/25 기준선 |
| test_q3_light_e2e(light 골든) | **passed** — 25/25 |
| test_element_gallery(느린 것 포함) | passed(hormuz 휘장 파일 복사 — 환경) |
| test_catalog_layer | 13 passed(hormuz 720p 티어·클립 복원 — 환경) |
| anti_inertia 빠른 묶음 | 71 passed · 실패 1 = `test_doc_guards_only_for_process_items`(UF-145, 분기점 기존 D511) |

## 다음(게이트 ① 대기 중)
- 기사 카드 등록 후보 43건 headline_ko 채움 완료(`article_register.py` 건조 실행 — 승인 뒤 `--write`).
- 초상·인물 사진 권리: Commons 검색 통과(PD 공식 초상 12·CC0/CC BY 인물 사진 10). 원본·피사체·시기 대조와 cutout 은 승인 뒤.
- 승인 D 가 오면: script.plan(표준 음성) → 미디어 등록 → direction 에 photo·article 덧붙임 → audio.mix → 콘티 판.
