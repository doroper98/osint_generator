<!--
tier: 3
last_synced_with: v4.1.0
ssot_for: [phaseG1-run-log]
depends_on: [engine/stage.py, engine/projection.py, engine/shots.py, geo/prep_geometry.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
-->

# Phase G1 실행 기록 — 무대 추상화 (v4.1.0)

새 Opus 클라우드 컨테이너(재기동 12). 시각은 KST. 지침 D-0076, 결정 D-0077(무대 연속성 입력·판정)·D-0078(국가 키 충돌 긴급 수정)·D-0079(골든 불변·등재).

## 0. 컨테이너 준비

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | OK |
| 의존성·CA | phase9 run_log §0 그대로(pip 두 파일, apt ffmpeg·fontconfig·fonts-noto-cjk, certifi + `/root/.ccr/ca-bundle.crt`) | OK |
| 자산 복원 | `artifacts/phase7-v3.3.0 shared` → hormuz `tts/`·`plan.json`·`media/`, `artifacts/phase9-v3.5.0 shared` → ratcliffe `tts/`·`plan.json` | OK |
| 입력 데이터 | `fetch_data fonts ne tiles flags bgm` → `commons people` | exit 0(Commons 429 대기) |
| hormuz 자산 | legacy 복사 → `geo.prep projects/hormuz_korea` + `--res 1080p`, `media_fetch --res 1080p --no-sheets` | OK |
| ratcliffe 자산 | phase9 §0.1·phase10 §0 대로: 국기 SVG(`fetch_data.download` 가 멈춰 같은 URL 을 curl 로 받음) → `build_flag_pngs`, `library_portrait` 3, `record_rights`·`record_bundles` → `geo.prep` | 국기 PNG 50 |
| 기준선 | `engine.render hormuz --preview golden` | 25컷 = Phase 11 기준선 25/25(`hormuz_baseline_prefix.json`) |

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·CHANGELOG·NB29·기준선 | `2233392` | `hormuz_baseline_prefix.json`(당시 이름 hormuz_baseline) |
| 1~3 Stage·MercatorStage·호출부 | `4123cf0` | 옛 자산 25컷 25/25, 랫클리프 20/20, camera_suggest 동일, `test_stage_isolation`·`test_stage` |
| D-0078 국가 키 충돌 | `f8e507a`·`55a7471` | `geo_fix_diff.json`·`geo_fix_before_after.jpg`·`ratcliffe_kz_after.jpg`, 새 기준선, `test_geo_key_collision` |
| D-0079 골든 등재 | `e8f845b` | `expected_deltas.json geo_kz_d0078`, `golden_delta/`, `test_golden_frozen`, `golden_compare_reference.json` |
| 4 direction stage 키 | `2da3ad6` | `test_stage_direction`, 프리뷰 예제 `stage_mercator.yaml` |
| 5 stage_continuity | `d6edd90` | `stage_continuity_{hormuz,ratcliffe,synthetic}.json`, `test_stage_continuity` |
| 7 문서 | `5fcde9c` | docs 07·09·10·12·16·ADDENDUM_03, handoff 05·20 |
| 6 회귀 | `17c3241` | `hormuz_after`·`res_compare_1080`·`ratcliffe_mad`·`camera_suggest_diff`·`perf` |

작업 1~3 을 한 커밋으로 묶었다(중간 상태가 import 되지 않아서). D-0079 가 C5.5 위반으로 지적 — 이후 작업은 나눴다.

## 2. 명령

```bash
python -m engine.render projects/hormuz_korea --preview golden          # 25컷 md5 ↔ hormuz_baseline.json
python -m engine.render projects/hormuz_korea --jobs 4                  # 전편 f19d21ad(새 자산)
python -m engine.camera_suggest projects/hormuz_korea                   # 제안 JSON ↔ 리팩터 전·Phase 7
python tools/res_compare.py projects/hormuz_korea --out DIR             # 1080p 축소 비교
# 옛(결함 포함) 지오 자산 재현 — 렌더 코드만의 무변경 증명
git worktree add /tmp/wt_prefix 2233392 && ln -s $PWD/data /tmp/wt_prefix/data
(cd /tmp/wt_prefix && python -m geo.prep $OLDPWD/projects/hormuz_korea_g1prefix [--res 1080p])
python -m engine.render projects/hormuz_korea_g1prefix --jobs 4        # 692f228e
```

## 3. 측정

| 항목 | 값 |
|---|---|
| hormuz 480p 25컷 | 새 자산: 새 기준선 25/25. 옛 자산(복사 프로젝트): 옛 기준선 25/25 |
| hormuz 전편 | 옛 자산 **692f228e**(Phase 6.9~11 과 같음), 새 자산 f19d21ad |
| 1080p | 옛 자산 PNG 25/25(리팩터 전과 동일), res_compare 평균 0.01067·최대 0.01808(옛·새 자산 모두 Phase 10 과 같음) |
| 랫클리프 20컷 | 옛 자산 20/20, frames.json = Phase 10 v2. 새 자산은 KZ 가 보이는 7컷만 변경 |
| camera_suggest | hormuz·랫클리프 JSON 리팩터 전과 완전 동일, hormuz shots = Phase 7 artifacts |
| 렌더 시간 | 같은 프로젝트·같은 컨테이너: 옛 코드 130.4초 → G1 코드 131.1초(+0.5%) |
| 지오 자산 | 옛 자산 480p base 9장 = Phase 10 asset_md5 9/9. 새 자산은 W 티어 3장만 다르다(G·K 동일) — `asset_md5.json` |
| checks | hormuz·랫클리프 hard 0, 13항목(stage_continuity 0) |

## 4. 결정 기록

- R-0091 → D-0077: `shots[].stage`, ③ teleport = 같은 무대 cut + auto_transition dip, ④ = 전환 수 hard + 인스턴스 기록.
- D-0078(Fable 지시): 같은 ISO 키 합집합, 면적 커버리지, 골든 교체 → R-0092 → D-0079: 골든 PNG 불변·등재(A).

## 5. 운영 기록

- `fetch_data.download` 가 raw.githubusercontent SVG 에서 멈췄다(curl 은 즉시 200). 같은 URL 을 curl 로 받아 해결. 코드 변경 없음.
- 긴 실행(전편 렌더·pytest·geo.prep) 중에는 그 트리의 코드를 고치지 않았다(PIPELINE-AP-010). 옛 자산 geo.prep 은 별도 워크트리.
- 복사 프로젝트 `projects/*_g1prefix` 는 검증용(gitignore 아님 — 커밋하지 않았다).
