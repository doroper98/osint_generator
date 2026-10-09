---
id: D-0140
from: fable
to: opus
kind: directive
responds_to: [R-0085, R-0090, R-0093, R-0095, R-0097, R-0099, R-0103, R-0106, R-0107, R-0111, R-0114, R-0116, R-0118, R-0119, R-0121, R-0126, R-0128, R-0132, R-0134, R-0137, R-0139, R-0140, R-0142, R-0145, R-0147, R-0149, R-0150, R-0152, R-0156, R-0158, R-0163, R-0164, R-0165, R-0166, R-0167, R-0168, R-0169, R-0170, R-0171, R-0172]
phase: "S0"
version: v5.6.0
status: open
priority: urgent
supersedes: []
---

# 스케치 스킬 트랙(S0~S4) 착수 — 미사일 2D→3D 전환·전황 작전도를 저장소 스킬로

사용자 지시(2026-10-09): "미사일 발사 2D→3D 전환 부분과 천왕성 작전 작전도 부분을 저장소에 스킬로 만들어 둬라.
Fable 이 계획을 세우고, Opus 5.5 가 스크립트·단위 테스트를 짜고, 통합 테스트 검수와 통과 판정은 Fable 이 한다.
back_and_forth 폴더 작동 방식 그대로."

`responds_to` 의 R-0085~R-0172 는 **확인만**(README §5.2). 지난 사용자 직접 지시 회차는 사용자가 main 에 이미 머지했다(5582e6c).

## 0. 이번 트랙의 교신 규칙 (README 와 다른 점만)

| 항목 | 값 |
|---|---|
| 교신·작업 브랜치 | **`claude/bold-mccarthy-ttmagk`** (README §1 의 `overhaul/v2-map-engine` 은 v5.3.0 에서 멈춰 main 보다 64 커밋 뒤 — 이번 트랙은 쓰지 않는다. D129) |
| 기준 커밋 | `4d9dc65`(main 5582e6c + 스케치 5 커밋). 이 위에 이어서 커밋한다 |
| 버전 | S0·S1 = **v5.7.0**, S2 = v5.8.0, S3 = v5.9.0, S4 = v5.10.0 (C5.4 MINOR = Phase 완료). Phase 첫 커밋이 VERSION·`orchestrator/__init__.py`·Tier 1·2 헤더·CHANGELOG 증분 |
| 보고 | Phase 마다 `phase_report` R 1개 + `docs/handoff/reports/phaseS{n}/run_log.md`(§0 컨테이너 준비 포함) + 컨택트 시트 |
| main 머지 | Fable 이 S4 `review` pass 뒤에만 한다. Opus 는 main 에 푸시하지 않는다 |
| 결정 | README §6.4 그대로. 아래 §7 에 미리 내린 결정은 다시 묻지 않는다 |

## 1. 원본과 목표

원본(사용자 검토 완료, 2026-10-05~06, 전부 `4d9dc65`):

| 파일 | 내용 | 줄 |
|---|---|---|
| `projects/d1_missile_sketch/sketch_d1.py` | 2D: EEZ(중첩 빗금·공동 점무늬·서해 NLL/북한선 중첩), 탐지 자산(공개/비공개/함정), 발사·대원 궤적·착탄 불확실성 원, 고도 단면 패널, 미사일 도해 카드, 카메라 | 851 |
| `projects/d1_missile_sketch/globe3d.py` | 3D: 평면→지구본 곡률 전환(접점 kR 구), 실제 축척 고각 궤적, 레이더 부채 볼륨, 수평선 최소 고도 패널 | 535 |
| `projects/d1_missile_sketch/prep_eez.py` | Marine Regions WFS → eez.json(서해 남북 재분할) | 114 |
| `projects/uranus_sketch/prep_uranus.py` | 참고 작전도 SVG → 경위도 눈금 정합 → 전선·강 json | 102 |
| `projects/uranus_sketch/uranus_sketch.py` | 전황: 부대 부호(국가·제대), 진격 화살표, 날짜별 전선, 포위망, 1942 지명 | 523 |
| `projects/d1_missile_sketch/CONVENTIONS.md` | 표현 규약(사실 표기·탐지 자산·EEZ·카메라·3D) | — |

목표: 위 다섯 스크립트를 **데이터 주도(spec YAML) 패키지 `sketch/` + CLI** 로 옮기고, 에이전트용 스킬 2개를 `.claude/skills/` 에 둔다.
다음 북한 발사·다음 전역 영상은 **코드를 고치지 않고** spec 만 써서 같은 화면 스케치를 낸다. 화면 결과는 사용자 검토본과 같아야 한다(§6 판정).

## 2. 설계 결정 (Fable 전결, DECISIONS D128~D131 — 다시 묻지 않는다)

**D128 스케치 계층.** `sketch/` 는 **엔진 레지스트리에 아무것도 등록하지 않는** 독립 패키지다(P1). 산출물은 사용자 검토용 화면 스케치(`docs/handoff/20` §4.1 2단계)이지 본편이 아니다 — `engine.render`·`direction.yaml`·오케스트레이터 경로에 섞지 않는다.
근거: ① 되돌릴 수 있다(패키지 삭제로 원복) ② 20 §4.1 "스케치 → 승인 → 등록" 순서 ③ 지구본은 (x, y, w) 2D 카메라 모델 밖이라 무대 등록은 별도 설계가 필요하다. 본편 등록(이벤트 `arc`·`occupied`·`arrow`, 무대 `globe`)은 이 트랙 밖이며 S4 보고에 후보 목록만 남긴다.
`engine/` 밖에 두는 이유: `tests/anti_inertia/test_stage_isolation`(engine 안 경위도 산술 금지)·`test_device_space` 와 충돌하기 때문이다. 대신 §3 의 스케치 전용 AST 검사를 **같은 강도**로 건다.

**D129 교신 브랜치** = `claude/bold-mccarthy-ttmagk`(§0).

**D130 수치 SSOT.** 스케치의 모든 화면 수치(px·알파·초·간격·각도 폭·색 토큰 이름)는 `rules/video_rules.yaml` 새 최상위 `sketch:` 한 곳. 사실·연출 값(좌표·시각·발표 수치·문구)은 spec. 코드에는 둘 다 없다.

**D131 스킬 위치** = `.claude/skills/<name>/SKILL.md`(Claude Code 프로젝트 스킬 규격: 머리말 `name`·`description`, 본문 절차). 스킬 안에 코드를 두지 않는다 — CLI 를 부르는 절차서다.

## 3. 패키지 계약 (S0 에서 뼈대, S1~S3 에서 채움)

```
sketch/
  __init__.py
  common/
    spec.py         공통 spec 베이스(Pydantic v2, extra="forbid"): schema_version·kind·title·date·sources[]·shots[]·media[]
    geodesy.py      순수 함수(구면 R=6371): dest·bearing·gc_dist·gc_path·sector·horizon_altitude(d) = R(1/cos(d/R)−1)
    camera.py       shots → camera(t). 이동은 앞 숏 끝 상태(푸시인 포함)에서 시작(멈칫 교훈, CONVENTIONS §5)
    draw.py         공통 그리기(label2·tag·hatch·dots·polyline) — engine.typography·engine.style 토큰만
    render.py       프레임 루프 → mp4 + 컨택트 시트 + out/sketch_provenance.json. 출력 프로파일 = engine.style.output_profile
    checks.py       결정적 검사(§4). hard 위반 = SketchCheckError 로 중단(P6), warning 은 provenance 기록
    svg_georef.py   SVG 선 추출(스타일 묶음) + 눈금 교차점 2차 다항 정합 + 잔차 보고(S3)
  missile/
    __main__.py     CLI(아래)
    spec.py         MissileSpec
    eez.py sensors.py launch.py(발사·궤적·착탄) profile.py card.py
    prep_eez.py     CLI: WFS GeoJSON → eez.json(남북 서해 재분할 포함)
    globe.py        S2
  campaign/
    __main__.py
    spec.py         CampaignSpec
    fronts.py units.py arrows.py pockets.py
    prep_georef.py  CLI: 참고 SVG + spec georef 블록 → fronts.json
```

CLI(프로젝트 폴더 = 인자, spec = `projects/<pid>/sketch.yaml`):

```
python -m sketch.missile projects/d1_missile_sketch                 # 2D → out/sketch_2d.mp4 · out/sketch_2d_sheet.jpg · out/sketch_provenance.json
python -m sketch.missile projects/d1_missile_sketch --globe         # S2: 3D 전환편 → out/sketch_globe.mp4 · 시트 · provenance
python -m sketch.missile projects/d1_missile_sketch --frames 5,27   # 정지 화면(검사·테스트용)
python -m sketch.missile projects/d1_missile_sketch --check         # 렌더 없이 검사만(종료 코드 ≠ 0 = hard 위반)
python -m sketch.missile.prep_eez <wfs.geojson> projects/d1_missile_sketch
python -m sketch.campaign projects/uranus_sketch [--frames …] [--check]
python -m sketch.campaign.prep_georef projects/uranus_sketch
```
`--res` 기본 = `config engine.output.trial`(480p, 테스트), 사용자 전달본은 `--res final`(720p).

**spec 의 범위(연출·사실)** — 아래 필드는 전부 spec 에 있고 코드에는 없다.
- MissileSpec: `launch{label, sub, lon, lat, t}` · `track{ref{name, lon, lat}, bearing_deg, distance_km, approx: bool, uncertainty_km, flight_sec, t0, t1}` · `announced{jcs{…}, mod{…}}`(두 기관 나란히) · `sensors[{name, sub, kind: radar|ship, lon, lat, location_public, range_km|null, az_width_deg|null, el_deg|null, tag, color, t}]` · `eez{file, show[], overlaps[{code, kind, label, sub, at, anchor}], claim_lines[{code, label, sub, color, dash}], label_at{}}` · `media[{file, credit, license, caption, t0, t1}]` · `shots[{t0, t1, lon, lat, w}]` · `globe{texture_project, center, k_max, keyframes…}`(S2) · `notes{source_lines[{text, t0, t1}]}`
- CampaignSpec: `nations{code{color, label}}` · `units[{nation, echelon: XXXX|XXX|XX, arm: inf|arm|cav, name, lon, lat, t, fade[{t, to}]}]` · `fronts{file, georef{style_map, graticule{lons, lats}}, layers[{date, side, pieces[], t0, t1, dashed}]}` · `arrows[{name, pts, t0, t1}]` · `pockets[{name, build[piece refs·inline pts], t0, t1}]` · `places[{name, now, lon, lat}]` · `rivers_label[]` · `dates[{t, text}]` · `tags[{text, lon, lat, t0, t1, color}]` · `shots[]`

**rules `sketch:`** — 묶음: `camera`(push_in·move_min_sec·max_dlogw_per_frame) · `fade` · `text`(label·sub·tag·source·hud·panel 크기) · `eez`(채움·선·대시·빗금 간격/굵기·점무늬) · `sensors`(부채꼴 알파·눈금·스캔·비공개 흐림 겹 수) · `launch_track_impact` · `profile` · `card` · `globe`(k_max·fov·키프레임 높이·조명·림) · `campaign`(부호 크기·제대 글자·화살표 폭·전선 이중선 간격·빗금) · `checks`(georef_residual_deg·horizon_tol_km·label_overlap_px). 값은 **현재 스크립트 리터럴 그대로**(사용자가 본 화면). `schemas/rules_models.py` 에 `SketchRules`(extra=forbid) 추가.

**스케치 전용 관성 방지 검사(테스트, S0 에서 만들고 S1~S3 에서 통과 유지)**
- `tests/anti_inertia/test_single_config.SCANNED_ROOTS` 에 `sketch` 추가.
- 새 `tests/anti_inertia/test_sketch_no_literals.py`: (a) `sketch/**/draw·eez·sensors·launch·profile·card·globe·fronts·units·arrows·pockets.py` 의 `text(`·`tw(` size 인자 리터럴 0 (b) 같은 모듈 함수 본문의 숫자 리터럴은 허용 집합 {0, 1, 2, 3, 0.5, 90, 180, 360} 뿐(`test_no_magic_numbers` 와 같은 AST 방식) (c) hex 색 리터럴 0 (d) `sketch/` 가 `orchestrator`·`workers`·`engine.render`·`engine.project` 를 import 하지 않는다(P1 방향 고정) (e) `geodesy.py`·`svg_georef.py` 는 (b) 면제(수식).
- `projects/**/*.py` 금지는 S3 뒤 `test_no_code_direction` 에 "projects 아래 .py 0" 으로 확장(옛 스케치 삭제 뒤).

## 4. 결정적 검사(`sketch/common/checks.py`) — 각각 **양성·음성 테스트** 필수

| ID | 검사 | 판정 |
|---|---|---|
| SK-H1 announced_only | 화면 숫자 문자열은 spec `announced`·`track`·`sensors.range_km` 값에서만 조립. 계산값(gc_dist 등)을 포맷해 그리면 위반. provenance `numbers_shown[]` 와 spec 집합 대조 | hard |
| SK-H2 impact_area | `track.approx` 이면 `uncertainty_km > 0` 이고 점이 아닌 영역으로 그렸다는 provenance 기록 | hard |
| SK-H3 undisclosed_sensor | `location_public: false` → 기준점(점·사각) 그리지 않음 + tag 필수. `range_km: null` → 범위 도형 없음 | hard |
| SK-H4 overlap_two_colors | kind overlap 다각형은 청구국 색 ≥ 2 의 빗금. 단색 채움 = 위반 | hard |
| SK-H5 approx_note | approx 로 표시된 층(NLL 재구성·전선·부대 위치)이 보이는 동안 출처 줄에 "개략" 포함, 엔딩 자료 카드에 나열 | hard |
| SK-H6 horizon_formula | 패널 값 = horizon_altitude(d) ± `checks.horizon_tol_km` | hard |
| SK-C1 camera_continuity | 연속 프레임 `|Δ ln w|` ≤ `checks.max_dlogw_per_frame`, 숏 경계 포함(멈칫 재발 방지) | hard |
| SK-C2 label_overlap | 새 라벨 예약 상자끼리 겹침(AABB) | warning |
| SK-R1 rights | media·참고 SVG 마다 `RIGHTS.json` 항목(source_url·author·license ∈ 허용 목록). 없으면 중단 | hard |
| SK-G1 georef_residual | 눈금 적합 최대 잔차 ≤ `checks.georef_residual_deg` | hard |
| SK-G2 polygon_valid | 포위망·중첩 다각형 shapely valid · 면적 > 0 | hard |
| SK-G3 echelon | units.echelon ∈ {XXXX, XXX, XX}, arm ∈ {inf, arm, cav} | hard(스키마) |

provenance(`out/sketch_provenance.json`, P5): `schema_version, kind, spec_sha1, rules_hash, data_files[{path, sha1, source, license}], features_drawn{type: n}, approximations[], numbers_shown[], checks{hard: [], warnings: []}, render{profile, frames, duration_sec, elapsed_sec}`. 돌지 않은 단계는 기록하지 않는다.

## 5. Phase 계획과 합격 기준

### S0 (v5.7.0) 뼈대·규칙·검사 틀 — 테스트 ≥ 8
1. §0 커밋: VERSION 5.7.0·헤더·CHANGELOG(대장 행 D-0140)·`docs/handoff/reports/phaseS0/run_log.md` §0(컨테이너 준비: `pip install -r requirements-engine.txt -r requirements.txt pytest`, `apt fonts-noto-cjk`, `tools/fetch_data.py fonts`, `geo.prep` ×3 프로젝트(+ `--res 720p`), EEZ WFS 다운로드 URL 은 CONVENTIONS §1, Commons 는 `tools/commons_fetch.py` UA·간격 준수).
2. `sketch/common/{spec, geodesy, camera, draw, render, checks}.py` + `rules sketch:` + `SketchRules` + `.claude/skills/{missile-event-map, campaign-front-map}/SKILL.md` **초안**(절차 뼈대만).
3. 테스트: geodesy 4(dest↔gc_dist 왕복·bearing 기지값·horizon_altitude(425)≈14.2·(1260)≈127), camera 2(연속성 통과/실패), spec 1(extra 거부), checks 음성 1(SK-C1), anti_inertia 2(test_sketch_no_literals 빈 패키지 통과·SCANNED_ROOTS).
합격: pytest failed 0·xfail 0, `python -m sketch.missile --help`·`python -m sketch.campaign --help` 동작, rules 로드 통과.

### S1 (v5.7.0) 미사일 2D 이식 — 테스트 ≥ 14
1. `sketch_d1.py`·`prep_eez.py` → `sketch/missile/*`. `projects/d1_missile_sketch/sketch.yaml` 작성(현재 값 그대로: 2022.11.18 화성-17형). `media/RIGHTS.json` 을 SK-R1 형식으로.
2. 검사 SK-H1~H5·C1·C2·R1 구현 + 양성/음성 테스트 각 1(= 16).
3. 옛 `sketch_d1.py`·`prep_eez.py` **삭제**(P2). `CONVENTIONS.md` 는 그대로 두고 S4 에서 옮긴다.
4. 렌더: `--res final` 전편(56초) + 시트 → `docs/handoff/reports/phaseS1/`(시트 jpg + provenance json 커밋, mp4 는 커밋하지 않음 — 크기·md5 만 run_log).
합격: 시트 9컷이 사용자 검토본(`4d9dc65` 의 `sketch_d1.py` 출력, Fable 이 보관)과 구도·요소·문구 동일(픽셀 동일 요구 아님 — 글꼴 힌팅 차이 허용). 검사 hard 0. 음성 주입 7종 전부 SketchCheckError.

### S2 (v5.8.0) 미사일 3D 전환 — 테스트 ≥ 10
1. `globe3d.py` → `sketch/missile/globe.py`. spec `globe{}` 블록. `--globe` 로 19초 전환편.
2. 테스트: to_local 거리 보존(k=1·k=80, 임의 점 10개 오차 < 1 m), k→큰 값에서 평면 근사 수렴, visible()(구 뒤 점 가림), radar_volume in_volume 경계, SK-H6 양성/음성, 카메라 업벡터 보간 연속성, 2D→3D 첫 3D 프레임의 지상 궤적 화면 좌표가 2D 마지막 프레임과 ≤ 2px(이음새).
3. 삭제: `globe3d.py`. `globe_tex` 는 spec `globe.texture_project` 로 참조.
합격: 시트 7컷 사용자 검토본 동일, 수평선 패널 값 14·68·127 km, 검사 hard 0, 렌더 시간 ≤ 480p 60초.

### S3 (v5.9.0) 전황 작전도 이식 — 테스트 ≥ 12
1. `prep_uranus.py`·`uranus_sketch.py` → `sketch/common/svg_georef.py`·`sketch/campaign/*`. `projects/uranus_sketch/sketch.yaml`(부대·화살표·전선 층·포위망 구성·지명·태그 전부 데이터). `RIGHTS.json` SK-R1 형식.
2. 테스트: georef 잔차 ≤ 0.01°(현재 0.0084) + 도시 검산(스탈린그라드·칼라치 ≤ 0.05°), 스타일 묶음 추출 수(1119 2·1123 ≥ 20·1130 ≥ 3·강 ≥ 50), 포위망 유효성(SK-G2) 양성/음성, 제대 검증(SK-G3) 음성, 부호 그리기 예약 상자 크기, 화살표 성장 prog 단조, 전선 이중선 오프셋 부호, SK-H5(전선 개략) 양성/음성.
3. 삭제: 옛 두 스크립트. `test_no_code_direction` 확장(projects 아래 .py 0).
합격: 시트 7컷 사용자 검토본 동일, 검사 hard 0.

### S4 (v5.10.0) 스킬·문서·통합 — 테스트 ≥ 6
1. `SKILL.md` 완성(§8 규격). `CONVENTIONS.md` → `docs/handoff/22_SKETCH_TRACK.md`(tier 2: 계층 결정·spec 계약·검사표·데이터 출처·권리·남은 과제=본편 등록 후보) 로 옮기고 원본 삭제. `docs/handoff/19` §3 판정표 행·`CLAUDE.md` C7 표에 `sketch/ → docs/handoff/22` 한 행(헌법 변경은 이 한 행뿐).
2. 통합 테스트 `tests/test_sketch_integration.py`: 두 프로젝트를 `--frames` 3컷·480p 로 끝까지(검사 → 렌더 → provenance). 자산 없으면 사유 있는 skip(conftest 글꼴 skip 과 같은 방식) — **Opus·Fable 환경에서는 skip 이 아니라 통과해야 한다**(보고에 skip 0 명시).
3. 스킬 콜드 테스트: Opus 가 새 하위 에이전트에게 SKILL.md 만 주고 **가상의 새 사건**(spec 값만 다른 두 번째 미사일 사건, 예: 2023.4.13 화성-18형 — 발표값은 보도에서 수집·출처 기록) 스케치를 만들게 한다. 코드 수정 0 으로 mp4·시트·provenance 가 나와야 한다. 결과 시트를 `phaseS4/` 에.
합격: 위 전부 + Fable 콜드 테스트(§6) 통과.

### 공통 합격 조건(모든 Phase)
pytest 전체 failed 0·xfail 0, passed ≥ 직전 기준 − 삭제 수 + 새 테스트 요구치(D-0053 삭제 조정 기준선, 삭제 목록 표). 기준선은 S0 §0 에서 `4d9dc65` 로 측정해 run_log 에 적는다(Fable 도 같은 커밋으로 측정해 대조). 골든 25컷·hormuz·fed 산출물 **무변경**(스케치는 엔진을 건드리지 않으므로 변경 0 이 정상 — 바뀌면 그 자체가 결함).

## 6. Fable 검수 절차 (각 phase_report 마다 — 보고서 문장을 믿지 않는다, 15 P12)
1. pull → 전체 pytest(내 환경) → 보고 수치와 대조.
2. 두 CLI 를 spec 으로 **내 컨테이너에서 직접 렌더**(`--res final`) → 시트를 사용자 검토본과 나란히 보고 구도·요소·문구 대조. 새 프레임이 나오면 720p 원본 1장 이상 열어 지리(육지·수역·경계)가 맞는지 본다(README §6.2-4).
3. 음성 주입: spec 을 일부러 깨뜨린 사본(계산 거리 표기·단색 중첩·비공개 자산 점·approx 문구 삭제·echelon 오타)으로 `--check` → 전부 종료 코드 ≠ 0 확인.
4. AST 검사·provenance 키·`drops`·rights 확인.
5. S4: 내가 SKILL.md 만 읽고 세 번째 사건 spec 을 써서 코드 수정 없이 결과가 나오는지 콜드 테스트.
6. `review` D: verdict pass → 다음 Phase directive / revise → 수정 목록(번호). S4 pass 뒤 main ff·TAGS_PENDING·DECISIONS.

## 7. 미리 내린 결정·금지
- 스케치 수치는 사용자가 본 값 그대로 옮긴다. "더 좋아 보이게" 바꾸지 않는다. 바꿀 이유가 있으면 decision_request(전/후 컷 첨부).
- 음성·자막·내레이션 없음(사용자 요청 범위). TTS·script 패키지를 건드리지 않는다.
- 독도 문구·NLL 좌표(개략)·레이더 사양 값은 spec 에 있고 **사용자 확정 전**이다 — spec 주석에 "사용자 확정 대기" 표시, 바꾸지 않는다.
- Commons·WFS 요청은 저장소 도구의 UA·간격을 쓴다. 사용자 계정 식별 정보를 UA 에 넣지 않는다.
- 새 외부 패키지 추가 금지(현재 의존성: svgelements·shapely·scipy·cairo·numpy·PIL 안에서). svgelements 는 `requirements-engine.txt` 에 추가(이미 쓰고 있으나 미기재 — S0 §0 에서).
- 모델 식별자를 산출물·커밋에 넣지 않는다. PR 생성 금지. force push 금지.

## 8. SKILL.md 규격(S0 초안 → S4 완성)
머리말: `name`, `description`(언제 쓰는지 한 문장 — 트리거 문구 포함: "북한 미사일 발사", "탄착", "탐지 자산", "EEZ" / "전황", "작전도", "전선", "제대 배치").
본문 절: ① 쓰는 때·안 쓰는 때 ② 수집할 사실 체크리스트(출처 포함: 합참·방위성 발표, Marine Regions, Commons 도해·작전도, 공개 레이더 사양) ③ 프로젝트 폴더 준비(geo.yaml 티어 권장값·geo.prep·EEZ·georef) ④ spec 작성 규칙(approx 표시, announced 만 화면, 비공개 자산 처리, 중첩 표현, 독도·NLL 같은 사용자 확정 항목) ⑤ 실행 명령(--check → --frames → 전편) ⑥ 사용자 전달물(mp4·시트·provenance·확정 대기 목록) ⑦ 금지·한계(본편 아님, 등록 전 요소). 수치는 **규칙 키 이름으로만** 인용(값 복사 금지, C0).

## 9. 착수
S0 §0 커밋을 먼저 푸시하고 `ack` R. 이 D 의 §5 S0 를 끝내면 `phase_report`(S0). S0 검수와 S1 착수 directive 는 Fable.
