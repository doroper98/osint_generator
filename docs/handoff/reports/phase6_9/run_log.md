<!--
tier: 3
last_synced_with: v3.1.0
ssot_for: [phase6_9-run-log]
depends_on: [engine/direction.py, engine/checks.py, orchestrator/ai_direction.py, tools/ai_direction_run.py]
last_review: 2026-09-28
-->

# Phase 6.9 실행 기록 — 선언형 연출·결정적 검사·AI 연출 루프 (v3.1.0)

같은 Opus 클라우드 컨테이너(Phase 6.8 재기동 5 이어서). 시각은 KST.

## 1. 작업 순서와 증명 (D-0047 §1)

| 작업 | 커밋 | 증명 |
|---|---|---|
| 1 VERSION·NB8 | `c065cf8` | expected_deltas 클립 컷 2 등재(뒤에 §4 에서 제거) |
| 2 Direction 스키마·로더 | `c4eacc8` | `tests/test_direction_schema.py` — 17 §2 문법 전부 |
| 3 변환기 | `551d48a` | `hormuz_v3/convert_check.jsonl` 이벤트·카메라 키 dict 동일, 25컷 MAD 0 |
| 4 옛 direction.py 삭제 | `96de4a1` | `tests/test_no_code_direction.py` — exec 경로 0 |
| 5 배치 슬롯 | `bbd6778` | `tests/test_placement_slots.py` |
| 6 checks.json | `2a973eb` → hard 배선 | `tests/test_checks.py` 10항목 + PreviewHardFailTest. v3 뱃지 잘림 2건 검출 → D-0048 수정 `3e7801d` |
| 7 프롬프트 5종 | `92d874f`·`3bc0197` | 파리티 5종 ACTIVE, PENDING 0 |
| 8 워커 3종·루프 | `137a1a1`·`25f498a` | `tests/test_ai_direction.py`(상한·hard 잔존·사람 연출 무루프·판 선택) |
| 9 provenance | `cc51c33` | `tests/test_ai_provenance.py` — 워커 산출 파일이 있을 때만 true |
| 10 실증 | `b076e55`·`0c0bc22` | `hormuz_ai/qa_loop.md` |
| D-0049 반영 | `3e0dcbc`·`0ff24e4` | 마커 잘림 hard, 시각표·루프 이력, 판 선택, chosen_version |

pytest 667(Phase 6.8 609 → +58), xfail 0.

## 2. 함정 기록

### 2.1 YAML 1.1 `off` → false (D-0048 요청)
direction.yaml 앵커의 `off:` 키를 PyYAML 기본 로더가 **불리언 false** 로 읽는다(YAML 1.1 은 on/off/yes/no 도 불리언).
`{sid: open_0, off: 0.2}` 가 `{sid: open_0, False: 0.2}` 가 되어 앵커가 조용히 0초 오프셋이 된다.
조치: `engine/direction.py` 전용 안전 로더 — bool 해석을 `true/false` 만 남기고 나머지 규칙은 SafeLoader 그대로(코드 실행 없음).
덤퍼도 같은 해석표를 써서 `'off'` 를 따옴표로 내보낸다. 테스트 `test_direction_schema.py`.

### 2.2 AI 실행에서 드러난 코드 버그 (전부 수정·테스트·AP)
| 증상 | 원인 | 조치 |
|---|---|---|
| 슬롯 배치 뱃지가 lon/lat 누락으로 거부, 틀린 재요청 | 저장 전 점검 ≠ 렌더 경로 | `load_project(direction=)` — PIPELINE-AP-007 |
| 시각 검수 단계 실패 | LLMCallRecord.mode 에 vision 없음 | LLM-AP-007 |
| 정당한 수정이 "지적 없이 변경"으로 거부 | 지적 표지 형식 불일치(`badge:이름` ↔ 키, 컷 표지, `검사id:상세`) | `engine.qa.resolve_refs` — PIPELINE-AP-008 |
| 수정 기록을 못 찾음(루프 이력 비어 있음) | `latest()` 가 v1 부터 연속 번호 가정(수정 기록은 v2 부터) | glob 최대 번호 |
| 골든 route_2·3 MAD 0.09 | 검사용 상자 확장이 렌더 예약 영역까지 바꿈 | `marker_box(with_sub=)` — RENDER-AP-003 |

RENDER-AP-003 은 hormuz_ai 실행 2 가 돈 뒤에 잡았다. 실행 2 의 프리뷰·검수는 넓어진 예약 영역(도시 라벨 회피만 다름)으로 찍혔다.
판정 대상(뱃지·패널·클립·마커 위치)은 같다. 최종 시트·v3_vs_ai.jpg·영상은 고친 엔진으로 다시 렌더했다(§5).

### 2.3 LLM 출력 계약 위반 (재요청으로 처리 — 버그 아님)
- 수정 LLM 이 `sound` 블록 뒤에서 최상위 객체를 닫고 `,"changelog"` 를 이어 씀(JSON Extra data) 2회 → 예시 키 순서 changelog → direction.
- 수정 LLM 이 영상·사진을 점 슬롯에 둠 → 수정 프롬프트에 슬롯 표(kinds).
- 검수 LLM 이 없는 필드 `suggest_note` 를 붙임 → 재요청 1회로 통과.

## 3. hormuz_ai 실행 (tools/ai_direction_run.py — 파이프라인과 같은 함수)
`python tools/ai_direction_run.py projects/hormuz_ai --preview golden`. 입력 = hormuz_korea 의 script.yaml·plan.json·자산(tts·media·assets 하드링크).
연출가 1회 224초(재요청 0). 실행 1 네 번째 시도에서 루프 완주, 실행 2(D-0049 반영)는 두 번째 시도에서 완주. 상세 `hormuz_ai/qa_loop.md`.

## 4. Commons 원본 영상 (D-0044 §1 루프 → D-0045 §4 닫힘)
| 시각 | 파일 | 결과 |
|---|---|---|
| 16:38 · 17:19 · 17:59 · 18:39 | strikes | 429 |
| **19:19** | strikes | **ok** — strikes.webm md5 `64db2809…` = 레지스트리 source_hash |
| 19:19 | niovi | 429 |
| **19:59** | niovi | **ok** — niovi.webm md5 `2c2ec4ca…` = 레지스트리 source_hash |

- 루프는 scratchpad 별도 폴더에 받았다(프로젝트 media 무변경). 복구: `python tools/media_fetch.py projects/hormuz_korea --restore-from <받은 폴더>`(Commons 호출 0).
- source_hash 대상 5/5 일치(사진 3·영상 2, 나머지 2 항목은 기사 — 원본 파일 없음). 가공 npy 2 = Phase 6.5 `asset_md5` 바이트 동일.
- expected_deltas DVIDS 2항목 제거(`294c6cc`). 골든 25컷 `hormuz_v3/golden_compare_commons/`: 판정 21컷 mean **0.0077** · max 0.0828(now_3), 클립 컷 war_2 0.0001 · timeline_4 0.0000.
- DVIDS 원본·가공본은 artifacts `media_src/dvids/` 에 함께 보존(D-0044 B).

## 5. 최종 렌더 (`asset_md5.json`)
두 프로젝트 모두 같은 plan·tts(edge 재합성 292.441초)·Commons 원본 영상, 고친 엔진(`9f87dbb` 이후). 854×480@24.

| 프로젝트 | 연출 | final.mp4 md5 | provenance stages |
|---|---|---|---|
| hormuz_korea (v3) | 사람(골든 변환 + D-0048 뱃지) | `fc5dbe0cf64f08ef3004c91b54aacfe0` | ai_direction·visual_qa false |
| hormuz_ai | AI 실행 2, 코드 선택 v2 (`direction.yaml` = `direction.v2.yaml`) | `a3bd2bacd237ef3051c53989d630e324` | ai_direction·visual_qa true, used_version 2 |

명령: `python -m engine.render P --preview golden` → `python -m engine.render P` → `python -m audio.mix P` → `python -m engine.mux P`.
v3 영상은 Phase 6.8(`003df086…`)과 다르다 — D-0048 뱃지 위치(08 war_3 구간)와 Commons 원본 복구(클립 2) 때문이다. 골든 25컷은 §4 대로 합격.
영상 본체는 orphan `artifacts/phase6.9-v3.1.0`.
