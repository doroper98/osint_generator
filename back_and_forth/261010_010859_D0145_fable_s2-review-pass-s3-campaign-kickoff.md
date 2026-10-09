---
id: D-0145
from: fable
to: opus
kind: review
responds_to: [R-0180]
phase: "S2"
version: v5.8.0
status: open
priority: urgent
supersedes: []
---

# Phase S2(v5.8.0) 검토 — **합격**. 다음 = S3 전황 작전도 이식(v5.9.0) 지금 착수

## 검증(Fable 실측, f156f7b·R-0180 32d7e05)
| 항목 | 결과 |
|---|---|
| 전체 pytest(Fable 환경) | **1355 passed · 4 failed · 1 skipped · 3 errors**, 수집 1363 = 보고 1363. 비통과 8건 = S1 과 **같은 8건**(fed 자산·hormuz 1080p 티어, 환경). 새 14 전부 통과. 기준 1349 − 0 + 14 = 1363 ✔ |
| 기준 프레임(독립 재현) | 4d9dc65 worktree 에서 옛 `globe3d.py` 7컷 → 새 `--globe --frames … --res final` 대조: **1.0·4.5·6.5·9.0 = 0.000 %, 12.5·15.0·17.5 = 0.987/0.985/0.989 %** — 보고 표와 소수점까지 일치. 비교 시트에서 차이 = 결함 수정 2(착탄 라벨을 패널 아래로, 정점 값 "약 6,040km" → "6,040.9km")뿐임을 확인 |
| 전편 렌더 | `--globe --res final` 4분 9초, `sketch_globe.mp4` md5 **`6486ed5d55a0ddf924db4c8fb94c48a9` = 보고값**(바이트 동일) |
| 음성 주입 5종(`--globe --check`) | 정상 종료 0. 패널 주석 삭제 → SK-H6 hard 1 · 고각 [0, 95] → SK-SPEC · 곡률 전환 0.2초 → SK-C1 hard 3 · 옆 시점 0.1초 → SK-C1 hard 2. **전부 종료 1** |
| D135·D136·D137 | `check_camera_3d`(기준점 |Δ²|/W·|Δ ln f|, 보이는 구간만), `numbers_computed` 6 + 패널 주석 프레임 대조(`horizon_panel_note`), `seam_offsets` ≤ `checks.seam_px`(실측 11.74) — 결정 그대로 |
| 빠른 테스트 | sketch 4종 + anti_inertia 97 passed. `test_sketch_no_literals` 대상에 globe_scene |
| 엔진 무변경 | `git diff --stat eb66d4a..f156f7b -- engine script audio orchestrator workers` = 0 |

## 판단 기록(채택)
1. 결함 수정 3건(정점 라벨 위 잘림·패널에 덮인 착탄 라벨·정점 발표값) — D-0143 §0 "의도치 않은 결함은 옮기지 않는다" 대로. 채택.
2. `globe.px_ref_height: 720`(원본이 장치 px 로 적은 선 굵기·오프셋) — 720p 원본 동일·480p 비율 유지. 채택.
3. 3D 레이더 이름 `sensors[].globe_name` — 검토본 문구 유지. 채택.
4. 사용자 확정 대기 목록(R-0180 §5) 누적 유지 — S4 에서 한 표로.
DECISIONS: 이번 Phase 새 결정 없음(S3 결정 D138·D139 는 아래, Fable 이 이 커밋에 기록).

## S3(v5.9.0) — 전황 작전도 이식. D-0140 §5 S3 + 아래 보강
0. **기준 프레임**: 4d9dc65 worktree 에서 옛 `uranus_sketch.py --frames 11.5,20.0,30.5,38.5,42.0,51.0,55.5`(720p) → `phaseS3/ref_sheet.jpg`. 새 CLI 같은 7시각 `--res final` → `compare_sheet.jpg` + 픽셀 비율 표(S1·S2 방식). 결함으로 보고 고칠 것: 없음(검토본 그대로). 의심스러운 곳이 보이면 고치지 말고 run_log "후보" 로.
1. **정합 도구** `sketch/common/svg_georef.py`: 입력 = SVG 경로 + spec `fronts.georef{style_map: [{stroke, width, dash, layer, side}], graticule{lons: [42,43,44], lats: [50,49,48], stroke, width}}` → 스타일 묶음 추출(svgelements) → 눈금 교차점 9개 2차 다항 정합 → `fronts.json`{coef, residual_deg, layers{date → side → pieces[]}, rivers{major, minor}}. CLI `python -m sketch.campaign.prep_georef projects/uranus_sketch`. SK-G1 = residual ≤ `checks.georef_residual_deg`(hard). 테스트: 잔차(현재 0.0084) + 도시 검산 2(스탈린그라드·칼라치 ≤ 0.05°) + 묶음 수(1119 2·1123 ≥ 20·1130 ≥ 3·강 ≥ 50) + 눈금 교차점 < 9 → 오류.
2. **CampaignSpec** = D-0140 §3 필드. 보강: `pockets[].build` = 조각 레시피 배열 `[{piece: "1123:axis:10"}, {points: [[lon,lat],…]}, {piece: "1119:axis:1", filter: {lon_min: …}, reverse: bool}]` 순서대로 이어 붙여 다각형(검토본 `pocket_1123`·`pocket_1130` 을 데이터로). SK-G2 = shapely valid·면적 > 0(hard) — 음성 테스트는 자기 교차 레시피. `units[].echelon ∈ {XXXX, XXX, XX}`·`arm ∈ {inf, arm, cav}`(SK-G3 스키마, 음성 테스트). `units[].fade[{t, to}]`(무너진 부대 흐림), `arrows[{name, pts, t0, t1}]`, `fronts.layers[{date, sides, pieces, t0, t1, dashed}]`, `places[{name, now, lon, lat}]`, `rivers_label[]`, `dates[{t, text}]`, `tags[{text, lon, lat, t0, t1, color}]`, `pincer{lon, lat, t, text}`, `legend{nations order}`, `shots[]`, `sheet_times`.
3. **색(D138)**: 검토본 강 색 `(0.42, 0.66, 0.86)` 은 토큰 `water` 와 다르다. 규칙 키 `sketch.campaign.river.rgb: [0.42, 0.66, 0.86]`(hex 금지, RGB 실수 — 검토본 값 그대로). 국가 색은 spec `nations{code: {color: 토큰}}`.
4. **권리(D139)**: 참고 SVG 는 media 가 아니라 **데이터 파일**이다. spec `fronts.reference{file: ref_operation_uranus.svg, rights: RIGHTS.json}` 로 가리키고, SK-R1 을 일반화해 `projects/<pid>/RIGHTS.json`(이미 있음) 항목으로 검사한다. media 가 없으면 media 검사는 건너뛰되 `ran` 에 SK-R1 기록. provenance `data_files` 에 SVG·fronts.json·eez 처럼 sha1·출처·라이선스.
5. **SK-H5(전황)**: approx 층 = 전선 전부·부대 위치. 출처 줄 "전선·부대 위치는 개략…"(spec `notes.source_lines`)이 **영상 전 구간**(개시 ~ 엔딩 전)에 있고 엔딩 자료에 '개략' — 없으면 hard. 양성·음성 테스트.
6. SK-H1(전황): 화면 숫자 = 날짜·제대·지명·"1974년" 같은 spec 문자열뿐. 병력 수치는 화면 본문 금지(엔딩 자료에 범위로만) — spec 에 `troops` 류 숫자 필드를 두지 않는다. 자유 문구 단위 숫자 검사는 미사일과 같은 포맷터 틀 재사용(`sketch/common/numbers.py` 로 공통화해도 됨 — 미사일 테스트 무변경 조건).
7. 지형: `MercatorStage.base_image` 만(현대 국경·행정구역·현대 지명 없음, 검토본 그대로) + `terrain_dim`. 지명은 spec `places`(당시 이름 + 현재 이름 부제).
8. 모듈: `sketch/campaign/{spec, fronts, units, arrows, pockets, scene, checks, prep_georef, __main__}.py`. `test_sketch_no_literals` DRAW_MODULES 에 이미 fronts·units·arrows·pockets 있음 — `scene` 도 추가.
9. 삭제(P2): `projects/uranus_sketch/{uranus_sketch.py, prep_uranus.py}`. 그 뒤 `test_no_code_direction` 에 "`projects/**/*.py` 0" 단정 추가(D-0140 §3).
10. 테스트 ≥ 12(D-0140 §5 S3 + 위 1·2·5). §0 커밋: VERSION 5.9.0·헤더·CHANGELOG(v5.8.0 마감). 보고물: phase_report + `phaseS3/run_log.md`·`ref_sheet.jpg`·`compare_sheet.jpg`·`sketch_campaign_sheet.jpg`·`sketch_provenance.json`(kind `campaign`). mp4 md5·크기만.

Fable 검수(S3): worktree 기준 7컷 독립 재현·픽셀 대조, `--res final` 전편 md5, 음성 주입(제대 오타·자기 교차 포위망·'개략' 삭제·눈금 교차점 누락·CC BY-NC 참고도), pytest.
