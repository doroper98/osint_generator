<!--
tier: 2
last_synced_with: v4.3.0
ssot_for: [render-pipeline-index]
depends_on: [docs/handoff/11_RENDER_QA_PERFORMANCE.md, docs/handoff/16_ORCHESTRATOR_INTEGRATION.md, docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, orchestrator/engine_service.py, rules/video_rules.yaml, config.yaml]
last_review: 2026-09-29
-->

# 10 — 렌더 파이프라인 명세 (v4.0.0 재작성)

엔진 단계와 산출물의 안내도다. 정본은 handoff 11(렌더·QA·성능)·16(오케스트레이터 통합)·17(연출·시각 검수)이다.
옛 판(v0.3.3 — Remotion debug/preview/final 3모드, `remotion_job_*.json`)은 v2.0.0에서 삭제됐다. 보존본은 `archive/hyperframes-briefing` 브랜치다.

---

## 1. 엔진 단계 (CLI)

오케스트레이터는 엔진을 **서브프로세스 CLI로만** 부른다(15 P1). 각 CLI는 표준 출력 마지막 줄에 `StageResult` JSON(`schemas/engine_models.py`)을 낸다.
어댑터는 `orchestrator/engine_service.py`다. 엔진 입력 파일을 만들거나 고치지 않는다(AST 테스트 `tests/test_engine_service.py`).
종료 코드·단계 이름·JSON이 서로 맞지 않으면 실패다(15 P6).

| 단계 | 명령 | 산출물 |
|---|---|---|
| plan | `python -m script.plan <proj> --tts edge\|elevenlabs` | `plan.json`, `tts/` |
| assets | `python -m geo.prep <proj> [--res 1080p]` | `assets/geo.pkl`, `tiers.pkl`, `base_*.png`, `geo_report.json` |
| direction_validate | `python -m script.lint <proj>` | 린트 결과(게이트 ① 뷰에서도 씀) |
| validate | `python -m engine.validate <proj>` | 연출 점검(스키마·앵커·레지스트리·엔티티·슬롯·예약 영역) |
| preview | `python -m engine.render <proj> --preview auto\|golden\|t1,t2,… [--res …]` | `prev/p_*.png`, `sheet.jpg`, `checks.json`, `frames.json`, `provenance.json` |
| render | `python -m engine.render <proj> [--jobs N] [--res …]` | `out/video_noaudio.mp4`, `out/render.json` |
| mix | `python -m audio.mix <proj>` | `out/mix.f32` |
| deliver | `python -m engine.mux <proj>` | `out/final.mp4`, `final.srt`, `description.txt`, `provenance.json` |
| camera_suggest | `python -m engine.camera_suggest <proj>` | 카메라 제안(보조, P8) |

상태 머신과 단계의 대응(`STATE_STAGES`)은 `orchestrator/engine_service.py`와 handoff 16 §2가 정본이다.

## 2. 프레임 루프와 레이어 순서

레이어 순서는 v3와 같다. 무대 배경(베이스 → 국경) → 지도 레이어 → 라벨 → 하부 암전 → 패널 → 사진·영상 → 카드·기사 → 날짜 → 전면 카드 → 자막 → 상부 암전 → 전체 페이드.
비네팅은 없다(G4-15). 연출(`direction.yaml`)은 선언형 YAML이고 코드로 실행하지 않는다(`tests/anti_inertia/test_no_code_direction.py`).
이벤트 타입·패널 종류·미디어 형태는 레지스트리(`rules:registries`)에 있어야 하고, 레지스트리에 있으면 렌더러가 있어야 한다(15 P10).

### 2.1 무대(Stage) — v4.1.0

카메라와 `View` 는 무대의 월드 좌표 (x, y, w)만 안다. 연출의 앵커(지도 = 경위도)는 `stage.to_world` 로만 월드 좌표가 된다.
무대 목록은 `rules:registries.stages`, 구현은 `engine/stage.py`(`Stage` 프로토콜·`MercatorStage`). 배경(`render_base`)과 라벨 LOD(`draw_labels`)는 무대가 그린다.
direction 의 최상위 `stage`·숏 단위 `shots[].stage` 로 고르고, 없으면 장르 프로필의 주 무대(기본 장르 지정학 = mercator)이며 provenance `stage.declared` 가 false 다. 무대 연속성은 결정적 검사 `stage_continuity`(`rules:stage`)가 본다.
투영 수식이 `engine/stage.py` 밖에 없음은 `tests/anti_inertia/test_stage_isolation.py` 가 고정한다. 정본은 handoff 20 §2.3.

### 2.2 장르 프로필과 프리미티브 — v4.2.0

장르 층(handoff 20 §1.2)은 `genres/<genre>.yaml`(`schemas/genre_models.py:GenreProfile`, 로더 `genres/load.py`)이 선언한다. 무대·요소·검사 이름은 `rules:registries`(`stages`·`stages_planned`·`primitives`·`primitives_planned`)와 `rules:qa_checks.planned` 안에서만 쓸 수 있고, approved 프로필은 구현된 것만 참조한다.
direction 의 `genre`(없으면 geopolitics, provenance `genre.declared` false)가 주 무대 기본값과 허용 무대를 정하고, 결정적 검사 `genre_elements` 가 연출이 쓴 요소를 프로필과 대조한다.
새 시각 요소(프리미티브)는 `engine/primitives/<id>.py` 계약(SCHEMA·COLOR_KEYS·draw·PREVIEW_FIXTURE)을 지키고 이벤트 `{type: primitive, id}` 로만 불린다. 카드 층의 무대 무관 오버레이이고, 크기는 `rules:primitives`, 색은 장르 프로필 `color_semantics` 에서 온다.
등록 요소 전부는 `tools/element_gallery.py` 가 실제 엔진으로 그린다. 정본은 handoff 20 §3·§4.

### 2.3 시간축 무대와 데이터 레코드 — v4.3.0

시간축 무대(`engine/stage_timeline.py:TimelineStage`)의 월드 x 는 무대 시작일로부터의 일수이고, y 는 레인이다. 세로 척도는 무대가 고정한다 — 카메라 폭은 시간 폭만 바꾼다(`rules:stage_timeline.lane_h`, D-0085). 압축 구간은 화면에 물결과 "압축" 라벨이 반드시 보인다.
카메라 앵커는 `{date, lane?, w}`, 핀은 `marker {date, lane}`(레인 id)이다. 무대 설정은 direction `stage_config.timeline`(레인 기본값 = 장르 프로필)이고 눈금 LOD·물결·레인 토큰은 `rules:stage_timeline` 이다.
수치 시리즈는 데이터 레코드(`data/series/<id>.yaml`+`.csv`, `schemas/data_models.py:SeriesRecord`, 허용 목록 `rules:data`)에서만 온다. `series` 이벤트가 레코드에서 직접 그리고, 빈 달(`missing`)은 끊고 "자료 없음"을 표시한다. 원고는 `sources: [series:<id>]` 로 레코드를 가리키고 린트가 수치를 대조한다(D-0088).
지도를 쓰지 않는 영상은 지형 자산을 읽지 않는다. 엔딩 카드는 `auto: series` 절로 레코드의 출처·라이선스 표기·기준 시점을 적는다. 정본은 handoff 20 §2.3·§5·§6.

## 3. 프리뷰와 두 게이트

| 게이트 | 상태 | 사람이 보는 것 |
|---|---|---|
| ① 원고 승인 | `SCRIPT_APPROVAL` | 장면 목록·원고 전문·출처 표·린트·미디어 후보(`orchestrator/gate_view.py`) |
| ② 프리뷰 승인 | `PREVIEW_APPROVAL` | `prev/sheet.jpg`·`checks.json`·시각 검수 판정·provenance |

프리뷰 샘플 규칙은 `rules:preview.min_body_cuts`(auto 모드), 골든 모드는 문장 앵커 25컷이다.
결정적 검사 18항목은 [07](07_VIDEO_STYLE_GUIDE.md) §8, 판정 흐름(시각 검수 루프·게이트 ② 사람 판정)은 [12](12_QA_AND_REVIEW_SPEC.md) §2다.
반려는 되돌림 규칙(handoff 16 §2)으로 앞 상태로 간다.

## 4. 출력 프로파일과 해상도

| 항목 | 키 |
|---|---|
| 프로파일 표(폭·높이·fps·crf·preset·청크당 메모리) | `config:engine.output.profiles` |
| 기본 프로파일 | `config:engine.output.default` |
| 별칭(트라이얼·최종) | `config:engine.trial`, `config:engine.final` |
| 설계 좌표 | `rules:layout_480p.base` |

- `--res`가 기본 프로파일이 아니면 프리뷰는 `prev_<이름>/`에 쓴다.
- 해상도 변환은 렌더 진입 장치 변환 한 곳이다(`translate(pad_x)·scale(k)`, k = 출력 높이 ÷ 480, D60). k = 1이면 변환을 걸지 않는다.
- 장치 크기를 읽는 모듈은 허용 목록으로 제한된다(`tests/anti_inertia/test_device_space.py`).
- 글자 폭 측정은 설계 480p 측정 컨텍스트에서 한다. 해상도에 따라 줄바꿈·카드 폭·라벨 충돌이 바뀌지 않게 하기 위해서다.
- 영상 클립도 래스터다. 기본이 아닌 프로파일은 `media/res_<프로파일>/{file}.npy`(크기 `config:engine.output.profiles.1080p.clip`, 16:9)를 읽고, 없으면 오류다(480p 클립을 늘려 쓰지 않는다, D-0074). 준비: `python tools/media_fetch.py <proj> --res 1080p`.
- 1080p는 480p와 같은 비율이어야 한다. `tools/res_compare.py`가 1080p를 축소해 컷별 MAD를 재고 상한은 `rules:golden.res_compare_mad_max`다.

## 5. 청크 병렬과 성능

`--jobs` 기본은 `config:engine.render.jobs`(null = CPU 수)다. 사용 가능 메모리 ÷ 프로파일의 청크당 메모리로 줄인다.
N 조각을 병렬로 렌더한 뒤 이어 붙인다(handoff 11 §3). 부분 재렌더 절차는 handoff 11 §3.1.
실측(4 CPU·15GB 컨테이너, 480p·1080p 전편 시간·청크 피크 RSS·지오 티어 크기)은 `docs/handoff/reports/phase10/perf.json`에 있다.
긴 렌더 중에는 같은 워크트리의 코드·규칙을 바꾸지 않는다(PIPELINE-AP, Phase 10 운영 기록).

## 6. provenance — 이번 영상에 실제로 쓰인 것 (15 P5)

프리뷰와 전편은 `provenance.json`을 남긴다. 필수 키는 `rules:provenance.required_keys`, drops가 있으면 실패다(`rules:provenance.fail_if_drops`).
돌지 않은 단계는 기록하지 않는다. 주요 절은 규칙·프롬프트 해시, `features_used`, `stages`, `stage`(무대 이름·declared·인스턴스, v4.1.0), `render.resolution`(프로파일·k·pad_x·crf·preset), 오디오 QA·loudnorm 기록, 번들 이관 기록이다.
`tests/anti_inertia/test_provenance_e2e.py`가 hormuz 프리뷰로 검증한다.

## 7. 인코딩과 먹싱

영상은 프로파일의 crf·preset으로 인코딩한다. 음성 합치기·2패스 loudnorm·자막·설명문은 [08](08_AUDIO_AND_TTS_SPEC.md) §6·§8이다.
최종 산출물 목록은 [GOAL.md](../GOAL.md) G1이다.
