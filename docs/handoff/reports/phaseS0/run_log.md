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
