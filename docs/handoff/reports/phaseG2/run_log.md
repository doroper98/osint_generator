<!--
tier: 3
last_synced_with: v4.2.0
ssot_for: [phaseG2-run-log]
depends_on: [genres/load.py, schemas/genre_models.py, engine/primitives/__init__.py, tools/element_gallery.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
-->

# Phase G2 실행 기록 — 장르 프로필과 새 요소 파이프라인 (v4.2.0)

새 Opus 클라우드 컨테이너(재기동 13 뒤). 시각은 KST. 지침 D-0081, 결정 D-0082(D73).

## 0. 컨테이너 준비

phaseG1 run_log §0 그대로. 차이만 적는다.

| 단계 | 결과·주의 |
|---|---|
| 의존성·CA·자산 복원·fetch_data·hormuz geo.prep(480p·1080p)·media_fetch 1080p | OK, 막힘 없음 |
| ratcliffe 자산 | legacy `flags_svg` 복사 + 11개국 SVG curl(`fetch_data.FLAG_URL`) → `build_flag_pngs`, `library_portrait` trump·putin·zelensky + `record_rights`, `record_bundles` → `geo.prep` |
| 지오 자산 | hormuz 21/21·ratcliffe 480p 8/8 = G1 `asset_md5.json`(`reports/phaseG2/asset_md5.json`). ratcliffe 1080p 는 만들지 않음 |

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 | 0e66d1c | reports/phaseG2 시작 |
| 1 스키마·로더 | 3f706c9 | test_genre_profile 17 |
| D-0082 | d35aeb5 | primitives_planned |
| 2 프로필 | acfdf51·0cc9849 | test_genre_profiles_files 3 |
| 3 genre·genre_elements | b9126bb·04ef559·eaef3c2 | test_genre_direction 8, e2e 14항목·provenance genre |
| 4 프리미티브 계약 | 79f2dc9 | test_registry_complete +5 |
| 5 statement_diff | 788bd0f | test_primitive_statement_diff 7, `statement_diff_sketch.jpg` |
| 6 갤러리 | e04a617 | test_element_gallery 3, `gallery.jpg` 32 |
| 7 회귀 | 068d052 | hormuz_after·ratcliffe_mad·genre_elements_* |
| 8 문서 | 4132f4d | test_docs_sync·test_goal_g3 |

## 2. 명령

```bash
python tools/primitive_sketch.py statement_diff --proj projects/hormuz_korea --genre macro_monetary \
    --extra tests/fixtures/primitives/statement_diff_long.yaml --out docs/handoff/reports/phaseG2/statement_diff_sketch.jpg
python tools/element_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG2/gallery
python -m engine.render projects/hormuz_korea --preview golden          # 25컷 md5 ↔ phaseG1/hormuz_baseline.json
git worktree add /tmp/wt_g1 5326b10                                     # G1 합격 코드
(cd /tmp/wt_g1 && python -m engine.render $OLDPWD/projects/ratcliffe2026 --preview auto)   # 기준 20컷
python -m engine.render projects/ratcliffe2026 --preview auto           # G2 코드 20컷 → md5 대조
```

## 3. 측정

| 항목 | 값 |
|---|---|
| hormuz 25컷 | 25/25(phaseG1 기준선), checks hard 0·14항목·genre_elements 0 |
| 랫클리프 20컷 | 20/20(G1 코드 대비), frames.json 동일, checks hard 0(warning shots 1·media_beats 1 = G1 과 같음) |
| provenance 차이 | genre(추가)·rules_hash(규칙 파일 변경)·repo_version |
| 갤러리 | 32/32 렌더(예제 누락 0) |
| statement_diff 스케치 | 3컷, glyph_size 0, 그린 글자 최소 9.5px |
| pytest | 881 passed · skip 0 · xfail 0(G1 838 + 새 43, 삭제 0) |

## 4. 운영 기록

- 작업 3 에서 `DEFAULT_STAGE` 를 지우고 부분 테스트만 돌려 커밋했다 — `bundle/to_direction.py` 참조와 `test_checks` 심각도 표가 깨진 채 푸시됐다. 후속 커밋 2개로 고치고, 이후 커밋은 전체 pytest 뒤에 올렸다.
- 갤러리 첫 실행에서 marker·badge_person 이 비어 보였다 — 예제 시각의 t1−1 에는 hormuz 카메라가 걸프로 이동한 뒤였다. 예제에 `gallery.t` 를 적었다(요소 표시 구간 안).
- 긴 실행(pytest·렌더) 중에는 코드를 고치지 않았다(PIPELINE-AP-010).
