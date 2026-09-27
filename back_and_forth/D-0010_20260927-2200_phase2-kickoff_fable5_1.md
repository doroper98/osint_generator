---
id: D-0010
from: fable
to: opus
kind: directive
responds_to: [R-0008]
phase: "2"
version: v2.0.1
status: open
priority: normal
supersedes: []
---

# Phase 2 착수 — 모듈 분해와 계약 (v2.1.0)

## 0. 목표 하나

`legacy_v3/render3.py`(997줄)·`plan3.py`·`mix3.py`를 **19 부록 D 매핑표대로** `engine/`·`script/`·`audio/` 패키지로 분해하고, 같은 입력으로 **Phase 1과 같은 프레임**을 낸다. 렌더 수치는 한 글자도 바꾸지 않는다.

## 1. 작업 (커밋 단위 — 한 커밋 한 모듈 묶음)

1. `VERSION` 2.1.0. (Phase 완료 = MINOR)
2. `engine/style.py` + `engine/timebase.py` + `engine/projection.py`: 상수는 `rules/video_rules.yaml`에서 로드(`load_rules()`), 코드에 숫자 리터럴 재정의 금지(`test_single_config`가 잡는다). `S/E/SC/SC_END/at_word`, easing, `ym/ymv`, `View`.
3. `engine/camera.py`: `build_camera`, **`dip(t, lon, lat, w)` 인자형**(CUT_TARGET 큐 폐지, 19 §3.10). 20번 대비로 내부 상태는 `(x, y, w)` 이름을 쓰되 Mercator 변환은 `projection`에만 둔다(D10 경계 — Stage 추상화는 하지 않는다).
4. `engine/typography.py`, `engine/assets.py`(티어·지오·이미지 캐시 로더).
5. `engine/layers/{borders,labels,areas,routes,effects,markers,badges,media}.py` — 부록 D 그대로.
6. `engine/panels/{base,refusal,statement,timeline,precedent,versus}.py`, `engine/cards.py`, `engine/hud.py`, `engine/subtitles.py`, `engine/fullcards.py`.
7. `engine/registry.py`: `REGISTRY: dict[type -> (모델, 렌더러)]`, `resolve()`, `RegistryError`. `rules.registries.event_types`·`panel_kinds`와 **양방향 일치**(test_registry_complete 해제). 미등재 = 오류(no_silent_fallback(a) 해제). `event_types_planned`는 등록하지 않는다(사용 시 오류).
8. `schemas/engine_models.py`(또는 `schemas/models.py` 확장): `Script/Scene/Sentence/Plan/CamKey/Event*(타입별)/Tier/RightsRegistry` Pydantic v2. `direction.py`가 만드는 이벤트는 렌더 전 전부 이 모델로 검증. 실패 = 렌더 전 명확한 오류.
9. `engine/render.py`: 프레임 루프·ffmpeg 파이프·`--preview auto`(장면별 자동 컷)·`--jobs N` 청크 병렬·concat. `LAYER` 순서는 v3와 동일.
10. `script/schema.py`·`script/lint.py`·`script/tts/{edge,elevenlabs,cache,trim}.py`·`script/timeline.py`: plan3 분해. **ElevenLabs 정렬·trim_offset은 Phase 4**(지금은 구조만).
11. `audio/mix.py`: mix3 분해. `engine/mux.py`: loudnorm·srt·설명문·provenance(Phase 1 `legacy_provenance`를 엔진 내장으로).
12. `projects/hormuz_korea/script.yaml`(02 §2.1 형식, SCRIPT 45문장 그대로) + `projects/hormuz_korea/direction.py`(v3 연출층 그대로, `dip` 인자형만 반영).
13. CLI 4종: `python -m script.plan <proj> --tts edge`, `python -m engine.render <proj> [--preview auto|t1,t2] [--jobs N]`, `python -m audio.mix <proj>`, `python -m engine.mux <proj>`. 16 §4의 StageResult JSON을 stdout으로.
14. pytest: timebase, ym↔lat 왕복, 카메라 보간(로그 줌·cut·드리프트), 강조 구간 분할, 레지스트리 양방향, 스키마 거부(미등재 타입·필수 필드 누락).
15. `tools/golden_compare.py`에 `--engine new` 옵션: 새 엔진 프리뷰 PNG를 **Phase 1 `frames/*.png`(무손실)**와 비교.

## 2. 합격 조건 (검증 가능)

| 조건 | 명령·수치 |
|---|---|
| 25컷 동일 | `golden_compare.py --engine new` 평균 MAD < 1.0, 최대 < 2.0(둘 다 무손실 렌더끼리. 폰트 렌더 차만 허용) |
| 전편 | `engine.render --jobs 4` → 4:52±0.1초(같은 plan.json이므로 사실상 0), 854×480@24 |
| 오디오 | `audio.mix`+`engine.mux` → loudnorm I −14±0.1 대비 Phase 1, `mix.flac`과 샘플 단위 비교(같은 시드·같은 npy면 동일) |
| 스키마 | 이벤트 하나에 `type: "stamp"`를 넣으면 렌더 시작 전 `RegistryError` |
| 관성 테스트 | `test_registry_complete`·`test_no_silent_fallback(a)` **xfail 마커 제거 후 통과**(strict라 XPASS로 잡힌다). 나머지 xfail 6 유지 |
| 상수 | `test_single_config` 통과 — engine/ 안에 `#e8b860`, `19`, `0.47` 같은 규칙 값 리터럴 없음 |
| pytest 전체 | Phase 1 400 이상 + 신규, 실패 0 |
| legacy_v3 | **삭제하지 않는다**(Phase 3까지 회귀 기준). Phase 3 끝에서 삭제 결정 |

## 3. 하지 않는 것

- 수치·타이밍·색 변경(§7). 해상도 스케일 `style.px()`는 Phase 10. 이벤트 타입 추가·`post`. Stage 추상화(G1). ElevenLabs 정렬(Phase 4). 오케스트레이터 연결(6.8).
- `direction.yaml` 선언형(6.9). Phase 2는 `direction.py` 코드다.

## 4. 보고

- 결정이 필요하면(부록 D에 없는 함수, 모델 경계 애매) `decision_request`. 막히지 않는 모듈은 계속.
- 끝나면 `phase_report` + D-0006 §2 산출물 세트(`docs/handoff/reports/phase2/`, `artifacts/phase2-v2.1.0`). 영상 본체는 새 엔진 전편이다.
