<!--
tier: 3
last_synced_with: v5.7.0
ssot_for: [phaseS0-run-log]
depends_on: [back_and_forth/261009_210629_D0140_fable_sketch-skills-track-s0-s4-kickoff.md, back_and_forth/261009_212241_D0141_fable_decision-sk-c1-second-difference-thresholds.md, rules/video_rules.yaml, sketch/]
last_review: 2026-10-09
-->

# Phase S0 실행 기록 — 스케치 패키지 뼈대·규칙·검사 틀 (v5.7.0)

지침 D-0140(스케치 스킬 트랙 착수) §5 S0, 결정 D-0141(SK-C1 1차 + 2차 차분, 임계값).

## 0. 컨테이너 준비

새 클라우드 컨테이너(Python 3.13.16, ffmpeg 6.1.1, 4 코어). 기준 커밋 `4afb42f`.

| 단계 | 명령 | 소요 |
|---|---|---|
| 의존성 | `pip install -r requirements-engine.txt -r requirements.txt pytest pytest-asyncio svgelements` | 44초(글꼴 포함) |
| 시스템 글꼴 | `apt-get update && apt-get install -y fonts-noto-cjk` — **update 없이는 "Unable to locate package"** | 7초 |
| 프로젝트 글꼴 | `python tools/fetch_data.py fonts` | (위 44초 안) |
| 지오 자산 | `python -m geo.prep projects/d1_missile_sketch` · `--res 720p` · `projects/d1_missile_sketch/globe_tex` · `projects/uranus_sketch` · `--res 720p` | 1분 33초(타일 새로 받음, land-miss 는 globe_tex `AW` 1건뿐 — 아루바, 전 지구 ppd 8 텍스처라 무관) |

- libcairo2 는 설치돼 있었다. svgelements 1.9.6.
- EEZ WFS 원본(CONVENTIONS §1 URL)과 Commons 도해는 S0 에서 받지 않았다(`eez.json`·`media/` 는 저장소에 있다). S1 에서 `prep_eez` 를 이식할 때 받는다.

### 0.1 테스트 기준선 (D-0053 삭제 조정 기준선)

`4afb42f` 트리(작업 트리 = 4afb42f + back_and_forth 교신 파일 2개뿐)에서 `python -m pytest -q`:

| passed | failed | skipped | xfail | 시간 |
|---|---|---|---|---|
| 1279 | 7 | 23 | 0 | 14분 38초 |

실패 7개는 전부 **저장소 미추적 프로젝트 자산 부재**다(코드 결함 아님).

| 테스트 | 없는 자산 |
|---|---|
| `test_provenance_e2e::test_hormuz_preview_provenance` | hormuz_korea |
| `test_element_gallery::test_full_gallery_renders` | hormuz_korea plan.json·tts·assets·media |
| `test_fed_timeline_demo::test_preview_checks_and_provenance` | fed_timeline_demo plan.json·tts·rights_registry |
| `test_g5_endcard_overflow` 2개 | fed_policy_2026 plan.json·tts |
| `test_g5_labels_endcard::ProjectPreviewNoLabelTest` | fed_policy_2026 |
| `test_g7_head_reserve::test_hormuz_edge_recorded` | hormuz_korea plan.json |

복원(`artifacts/*` 브랜치 → 프로젝트 폴더, HANDOFF §4·phaseG7 §0)은 §0.2 에 적는다.

### 0.2 테스트 자산 복원 (하위 에이전트, HANDOFF §4·phaseG7·G10·G12 §0)

`S` = 세션 임시 폴더. 저장소 추적 파일은 바꾸지 않았다.

| # | 명령 | 소요·확인 |
|---|---|---|
| 1 | `cat /root/.ccr/ca-bundle.crt >> $(python -c "import certifi;print(certifi.where())")`(무조건) | BEGIN CERT 121 → 248 |
| 2 | `git fetch origin artifacts/phase7-v3.3.0 artifacts/phaseG3-v4.3.0 artifacts/phaseG4-v4.4.0 artifacts/phase9-v3.5.0` → `git archive origin/artifacts/<b> shared \| tar -x` | 2초 |
| 3 | hormuz: phase7 `shared/` → `tts/`·`plan.json`·`media/` | tts 135, media 12, plan `200c1e74…` |
| 4 | `git fetch --unshallow origin`(bgm 이 커밋 `bd37b58` 필요) | 2초 |
| 5 | `python tools/fetch_data.py fonts ne tiles flags bgm` | 44초 |
| 6 | `python tools/fetch_data.py commons people` | 102초(Commons 429 대기 1회) |
| 7 | `projects/hormuz_korea_legacy/assets/{emblems,flags,portraits,rights_registry.json}` → hormuz assets | 34 파일 |
| 8 | `python -m tools.commons_fetch emblems projects/hormuz_korea --only cheongwadae` | `513c0785…` 일치 |
| 9 | `python -m geo.prep projects/hormuz_korea` | 25초, 480p 11/11 = phaseG7 `asset_md5.json` |
| 10 | fed_timeline_demo: phaseG3 `shared/` → tts·plan, `tools.commons_fetch bundles` | tts 30, plan `8ffbb682…` |
| 11 | fed_policy_2026: phaseG4 ARTIFACT_README 대로 tts·plan·media_src·assets·intake_bodies, us 국기 | tts 144, us_4x3 `66d6da8e…` |
| 12 | `tools/media_fetch.py projects/fed_policy_2026 --only fed_presser_0916,fed_presser_0916_b,fed_presser_0729 --no-sheets` | 3 ok |
| 13 | 같은 도구 `--only fed_eccles_ext,fed_boardroom,fed_eccles_atrium`(G12 배경 사진 — 아티팩트에 없음, Flickr) | 3 ok |
| 14 | ratcliffe2026(G5 테스트가 함께 읽는다): phase9 `shared/` → tts·plan | tts 114, plan `12f97dfc…` |
| 15 | ratcliffe 국기·번들·인물(phase9 §0.1·G2 절차 재현 스크립트) + `python -m geo.prep projects/ratcliffe2026` | 51초, 480p 8/8 = G7 |
| 16 | fed trump 초상(G12 §0): ratcliffe 초상 복사 + 권리 기록 | 네 프로젝트 `load_project` OK |

**글꼴 렌더 환경 차이(발견).** 이 컨테이너 이미지에는 비표준 `/etc/fonts/conf.d/12-unhinted-grayscale.conf` 가 있다.
힌팅 없음·서브픽셀 없음으로 표준 `10-hinting-slight`·`10-sub-pixel-rgb` 를 덮는다. cairo 글자만 달라져
`test_hormuz_preview_provenance` 의 25컷 md5 가 `phaseG17/hormuz_baseline.json` 과 0/25 일치한다.
v4.11.0 코드를 따로 렌더해 G10 기준과 대조했다: 기본 설정 0/25, 이 파일을 뺀 표준 설정 25/25. 코드·자산 문제가 아니다.
대처: `/etc` 는 건드리지 않고 테스트만 `FONTCONFIG_FILE=$S/fontconfig/fonts.conf` 로 돌린다(`/etc/fonts/conf.d/*` 중 이 파일만 뺀 링크 폴더를 include).
`fc-match -v` → hinting True, hintstyle 1. 다음 컨테이너도 같은 이미지면 같은 처리가 필요하다.
| 17 | `python -m geo.prep projects/hormuz_korea --res 1080p` · `python tools/media_fetch.py projects/hormuz_korea --res 1080p --no-sheets`(test_phase10_scale 3개 — 자산이 생기자 skip 이 아니라 실행됨) | 65초 · 8초 |

## 1. 작업 커밋

| 커밋 | 내용 |
|---|---|
| `7f990f5` | R-0173 ack |
| `473cf9b` | R-0174 결정 요청(SK-C1 정의·임계값) |
| `91d620c` | §0: VERSION 5.7.0·헤더 34개·CHANGELOG·svgelements·이 기록 §0 |
| `346ae65` | `rules sketch:` + `SketchRules`(extra=forbid) — 묶음 camera·fade·text·tag·eez·sensors·launch_track_impact·profile·card·globe·campaign·checks |
| `97a035b` | `sketch/common`(spec·geodesy·camera·draw·render·checks·cli) + CLI 2개 + `tests/test_sketch_common.py` |
| `325f0e7` | `tests/test_sketch_render.py`(렌더 루프·그리기 연기) |
| `ba0addd` | `tests/anti_inertia/test_sketch_no_literals.py` + `test_single_config.SCANNED_ROOTS` 에 sketch |
| `b48c744` | `.claude/skills/{missile-event-map,campaign-front-map}/SKILL.md` 초안 |

## 2. SK-C1 실측(D-0141 조건 2) — 사용자 검토본 두 카메라, 24fps 전 구간

| 카메라 | `|Δ ln w|` | `|Δ² ln w|` | `|Δ² x|/w` | `|Δ² y|/w` | 판정 |
|---|---|---|---|---|---|
| 미사일(검토본) | 0.06228 | 0.00392 | 0.00126 | 0.00036 | 통과 |
| 미사일 옛 재시작 재현 | 0.06395 | **0.03568** | 0.00123 | 0.00036 | SK-C1 위반 |
| 천왕성(검토본) | 0.04061 | 0.00256 | 0.00112 | 0.00169 | 통과 |
| 천왕성 옛 재시작 재현 | 0.04204 | **0.03047** | 0.00110 | 0.00166 | SK-C1 위반 |

임계 0.07 / 0.01. 중심 2차 차분 검토본 최대 0.0017 — 0.01 아래라 decision_request 불필요.
측정 보조 함수는 `tests/test_sketch_common.py`(`reviewed_paths`·`_RestartPath`·`_Patched`).
`CameraPath.at` 는 4d9dc65 `sketch_d1.camera()` 와 1344 프레임 전부 1e-9 안에서 같다(`test_matches_reviewed_missile_camera`).

## 3. 메모

- `rules sketch:` 값은 4d9dc65 스크립트 리터럴을 옮겼다. 파생 값 하나: `fade.date_hide_lead_sec` 0.2 = 날짜가 엔딩 카드보다 먼저 물러나는 폭(미사일 4.6−4.4, 천왕성 5.2−5.0 — 두 스크립트 같은 값). 새 키 `tag.reserve_min_alpha` 0.05 = 원본 `if a > 0.05`.
- 묶음은 뼈대다. S1~S3 이식 때 같은 묶음 안에 키를 더한다(예: 천왕성 물 색 `(0.42, 0.66, 0.86)` 은 토큰 `water` 와 다름 — S3 에서 처리).
- `draw.hatch` 반복 끝을 `x1` 로 했다(원본 미사일은 `x0 + span` — 넘는 선은 클립 밖이라 화면 같음).
- 렌더 인코딩은 출력 프로파일의 crf·preset(19·faster)이다. 원본 스크립트는 18·medium 을 직접 적었다(D-0140 §3 "출력 프로파일 = engine.style.output_profile").

## 4. 테스트 결과 (S0 끝, `FONTCONFIG_FILE` 표준 설정)

| 시점 | passed | failed | skipped | xfail | 수집 |
|---|---|---|---|---|---|
| 기준 `4afb42f`, 자산 없음 | 1279 | 7 | 23 | 0 | 1309 |
| S0 끝, 자산 복원 | **1330** | **0** | **0** | 0 | 1330 |

- 새 테스트 21개(요구 ≥ 8): `test_sketch_common` 16(geodesy 4·camera 2·SK-C1 4·spec 2·checks 틀 1·rules 2·CLI 1), `test_sketch_render` 2, `test_sketch_no_literals` 3.
- P2 삭제 0개(S0 는 옛 스크립트를 지우지 않는다). 삭제 조정 기준 = 1309 − 0 + 21 = 1330 수집, 전부 통과.
- 기준선 skip 23 은 자산 복원으로 전부 실행됐다(skip 0).
- 골든: `test_hormuz_preview_provenance` 25컷 md5 = `phaseG17/hormuz_baseline.json`(표준 글꼴 설정에서). 엔진 무변경.
- 합격 확인: `python -m sketch.missile --help`·`python -m sketch.campaign --help` 종료 0(`CliHelpTest`), `load_rules()` 통과.
