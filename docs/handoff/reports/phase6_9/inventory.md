<!--
tier: 3
last_synced_with: v3.0.0
ssot_for: [phase6_9-inventory]
depends_on: [docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, projects/hormuz_korea/direction.py, engine/events.py, rules/video_rules.yaml]
last_review: 2026-09-28
-->

# Phase 6.9 준비 — AI 연출가·시각 검수 인벤토리 (조사, 코드 없음 — back_and_forth D-0044 §3d)

정본: 17 전체, 13 §Phase 6.9. 저장소 v3.0.0 실측.

## 1. 현재 연출 = `projects/hormuz_korea/direction.py` (146줄, 파이썬)
- `direct(tb) -> Director`: `cam(t, lon, lat, w, dur, mode)` 6회, `dip(t, lon, lat, w[, under])` 5회, `ev(type, t0, t1, **fields)` 44회
  (marker 8·badge 8·card 7·panel 5·route 4·photo 2·clip 2·article 2·cutout·country·boom·barrier·ships·tanker_loop 각 1).
- 시각은 전부 앵커 함수 `S(sid, off)`·`E(sid, off)`·`SC(scene)`·`SC_END(scene)`·`at_word(sid, word)`·`tb.card(kind)`·`tb.total` 로만 쓴다(02 §1) — 17 §2 앵커 문법과 1:1 대응 가능.
- 상수 `PL`(지명 좌표 8)·`ROUTE`(20점)·`CHEONG`(18점) — YAML 에서는 `places:`·`paths:` 이름표로.
- `sound(tb) -> dict`: bgm·장면별 intensity 키프레임·효과음 cue — 17 §2 예시에 없음. **direction.yaml 에 `sound:` 블록이 필요**(없으면 audio.mix 가 오류 — taiwan e2e 실측, R-0046).
- 로더 `engine.project.load_direction`: 파이썬 모듈 실행(`exec_module`). 17 §2 "코드 실행 없음" 과 반대 → 6.9 에서 YAML 로더로 교체, 옛 경로 삭제(P2).

## 2. direction.py → direction.yaml 변환기 설계 (초안)
| 항목 | 방식 |
|---|---|
| 도구 | `tools/direction_to_yaml.py`(1회용 이관) — direction.py 를 **기록용 Timebase**(앵커 호출을 기호로 돌려주는 가짜 tb)로 실행해 `cam/dip/ev` 호출을 앵커 식 그대로 포착 → YAML |
| 앵커 | `S(sid,off)`→`{sid, off}` · `E`→`{sid, off, edge: end}` · `SC`/`SC_END`→`{scene_start|scene_end, off}` · `at_word`→`{word: {sid, text}}` · `tb.card("title").t0`→`{card: title, edge: start}` · `tb.total`→`{total, off}` |
| 산술 | 앵커 + 상수 덧셈만 허용(`off`). 곱셈·앵커끼리 연산이 나오면 변환기가 오류(수동 판단) |
| 좌표 상수 | `places:`/`paths:` 이름표, 이벤트는 `at_place: hormuz` 또는 좌표 |
| 검증 | 변환 결과를 새 YAML 로더로 읽어 만든 이벤트·카메라 키가 **옛 direction.py 결과와 dict 단위 동일**(시각은 같은 plan 에서 float 동일) + 25컷 MAD 0 |
| 산출 | `projects/hormuz_korea/direction.yaml` + `prompts/examples/hormuz_direction.yaml`(17 §5.3 예시, parity 테스트 대상) |
| 스키마 | `engine/direction.py:Direction`(parity PENDING_6_9 에 이미 이름 예약: `engine.direction:Direction`) |

배치 슬롯(17 §2 `place:`): 미디어는 `engine/media_plan.fill_placement`(14 §10.3-5, `rules media_beats.placement` 슬롯 `photo_map`·`photo_panel`·`clip_*` 등)가 이미 있다. 뱃지·카드 슬롯은 없음 → 6.9 에서 슬롯 표를 rules 로.

## 3. `checks.json` (17 §3) — 항목별 현 코드
임계는 `rules qa_checks`(overlap_core_elements 0 · offscreen_clip 0 · missing_glyphs 0 · labels_per_frame_max 18 · subtitle_lines_max 2 · rights_missing 0 · forbidden_components 0 · visual_qa_loop_max 2)에 **이미 있으나 읽는 코드가 없다**.

| 검사 | 현 코드 | 6.9 할 일 |
|---|---|---|
| 요소 겹침 | `engine/reserved.py` 카드 영역 회피·`avoidance_report`, `media_plan.placement_warnings` | 프레임 샘플별 교차 계산 → 수치화 |
| 화면 밖 잘림 | 없음 | 뱃지 R×3.3·라벨 폭 경계 |
| 글리프 누락 | 없음(fontTools 는 fetch_data 에서만) | 그릴 문자열 전부 × 폰트 cmap |
| 숏 규칙 | rules `shot_grammar` 값 있음, 검사 없음(Phase 7 린트와 겹침) | 숏 길이·장면당 이동·암전 빈도 |
| 미디어 비트 | `media_plan.density_report`(D38) | 결과 편입 |
| 라벨 밀도 | 지오 라벨 LOD 있음, 프레임별 수 검사 없음 | 프레임 라벨 수 ≤ 18 |
| 날짜 | 없음 | 날짜 배지 문자열 = 문장 date |
| 자막 | `script.lint subtitle-lines`(경고) | 편입 |
| 권리 | `engine.credits` 권리 점검(오류), `validate_media`(RightsError) | 편입 |
| 금지 컴포넌트 | `tests/anti_inertia`·registry(도장 등 미등재 = RegistryError) | 편입 |
Hard 실패면 LLM 검수 호출 없이 연출 LLM 에 오류만(AP-V5-29).

## 4. 시각 검수 워커 입력 형식 (17 §4.1)
- 이미지: `prev/sheet.jpg`(v3.0.0 preview 가 이미 씀 — 4열 427×240, `engine/sheet.py`) + 전환 연속 컷 시트(`tools/contact_sheet.py transitions` — 엔진으로 옮길 후보).
- 컷별 JSON: `prev/provenance.json preview.times` + 각 시각의 문장(sid·text)·활성 이벤트 목록(`load_project` 이벤트 t0≤t<t1) — 새로 만들 `prev/frames.json`.
- `checks.json` 요약.
- BaseLLMWorker 이미지 첨부: 없음. `claude -p` 에 파일 경로 전달(17 §4.1) — 훅 추가 필요. 재요청 1회 후 중단(16 §3)도 없음(현재 validation_failed 면 바로 실패).
- 출력 `QAVerdict`(17 §4.3): parity 예약 이름 `engine.qa:QAVerdict`. `evidence` 필수, 검수자는 연출 파일을 고치지 않는다.

## 5. 프롬프트 5종 현황
| 프롬프트 | 파일 | 상태 |
|---|---|---|
| research | `prompts/research.md` 있음 | 출력 모델 `script.schema:Facts` 미정(PENDING) — 18(6.95) 소스 레코드와 경계 |
| script | `prompts/script.md` | v3.0.0 Script 로 전환(D-0040 작업 5). 17 §5.2 자기점검 목록·v3 발췌 예시는 6.9 문안 개정 |
| director | 없음 | 새로. 예시 = 변환기 산출 hormuz YAML |
| visual_qa | 없음 | 새로 |
| revise_direction | 없음 | 새로. `changelog[]`, 지적 안 받은 부분 불변(회귀 테스트) |

## 6. 결정 필요 후보 (6.9 착수 때)
1. direction.py 로더 삭제 시점(변환기 검증 직후, P2) — taiwan_strait direction.py 도 같이 변환.
2. `sound:` 블록을 direction.yaml 에 둘지, 별도 `sound.yaml` 로 둘지.
3. 시각 검수 이미지 전달: `claude -p` 파일 경로 vs API(17 §4.1).
4. checks 의 "숏 규칙" 을 6.9 에 둘지 Phase 7(카메라 자동화 린트)과 합칠지.
