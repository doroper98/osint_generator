<!--
tier: 2
last_synced_with: v4.0.0
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

레이어 순서는 v3와 같다. 베이스 → 국경 → 지도 레이어 → 라벨 → 하부 암전 → 패널 → 사진·영상 → 카드·기사 → 날짜 → 전면 카드 → 자막 → 상부 암전 → 전체 페이드.
비네팅은 없다(G4-15). 연출(`direction.yaml`)은 선언형 YAML이고 코드로 실행하지 않는다(`tests/anti_inertia/test_no_code_direction.py`).
이벤트 타입·패널 종류·미디어 형태는 레지스트리(`rules:registries`)에 있어야 하고, 레지스트리에 있으면 렌더러가 있어야 한다(15 P10).

## 3. 프리뷰와 두 게이트

| 게이트 | 상태 | 사람이 보는 것 |
|---|---|---|
| ① 원고 승인 | `SCRIPT_APPROVAL` | 장면 목록·원고 전문·출처 표·린트·미디어 후보(`orchestrator/gate_view.py`) |
| ② 프리뷰 승인 | `PREVIEW_APPROVAL` | `prev/sheet.jpg`·`checks.json`·시각 검수 판정·provenance |

프리뷰 샘플 규칙은 `rules:preview.min_body_cuts`(auto 모드), 골든 모드는 문장 앵커 25컷이다.
결정적 검사 12항목은 [07](07_VIDEO_STYLE_GUIDE.md) §8, 판정 흐름(시각 검수 루프·게이트 ② 사람 판정)은 [12](12_QA_AND_REVIEW_SPEC.md) §2다.
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
- 1080p는 480p와 같은 비율이어야 한다. `tools/res_compare.py`가 1080p를 축소해 컷별 MAD를 재고 상한은 `rules:golden.res_compare_mad_max`다.

## 5. 청크 병렬과 성능

`--jobs` 기본은 `config:engine.render.jobs`(null = CPU 수)다. 사용 가능 메모리 ÷ 프로파일의 청크당 메모리로 줄인다.
N 조각을 병렬로 렌더한 뒤 이어 붙인다(handoff 11 §3). 부분 재렌더 절차는 handoff 11 §3.1.
실측(4 CPU·15GB 컨테이너, 480p·1080p 전편 시간·청크 피크 RSS·지오 티어 크기)은 `docs/handoff/reports/phase10/perf.json`에 있다.
긴 렌더 중에는 같은 워크트리의 코드·규칙을 바꾸지 않는다(PIPELINE-AP, Phase 10 운영 기록).

## 6. provenance — 이번 영상에 실제로 쓰인 것 (15 P5)

프리뷰와 전편은 `provenance.json`을 남긴다. 필수 키는 `rules:provenance.required_keys`, drops가 있으면 실패다(`rules:provenance.fail_if_drops`).
돌지 않은 단계는 기록하지 않는다. 주요 절은 규칙·프롬프트 해시, `features_used`, `stages`, `render.resolution`(프로파일·k·pad_x·crf·preset), 오디오 QA·loudnorm 기록, 번들 이관 기록이다.
`tests/anti_inertia/test_provenance_e2e.py`가 hormuz 프리뷰로 검증한다.

## 7. 인코딩과 먹싱

영상은 프로파일의 crf·preset으로 인코딩한다. 음성 합치기·2패스 loudnorm·자막·설명문은 [08](08_AUDIO_AND_TTS_SPEC.md) §6·§8이다.
최종 산출물 목록은 [GOAL.md](../GOAL.md) G1이다.
