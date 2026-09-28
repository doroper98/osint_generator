---
id: R-0019
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "4"
version: v2.3.0
commit: f3d4736
status: in_progress
---

# 작업 6 — `prompts/script.md`에 `Script` 예시를 넣으면 프롬프트가 두 형태를 가르친다

## 진행 상황 (D-0021)
| 작업 | 커밋 |
|---|---|
| 1 VERSION 2.3.0 | `dda018e` (D30 삭제는 R-0018 대기) |
| 2·7 린트 + 테스트 | `fee558b` |
| 3 ElevenLabs·trim_offset | `4152a48` |
| 5 TTS-AP-064~066, xfail 2건 해제 | `278273b` |
| 4 at_word 정렬 + 실측 픽스처 3문장 | `f3d4736` |

pytest 446 passed, xfail 4. ElevenLabs 실합성 3문장(ask_1·ask_4·past_3) 완료 — 비율 추정과 정렬값 차이 최대 0.37초(ask_1 "한국"). 표는 phase_report에.

## 쟁점
`prompts/script.md`는 **지금 살아 있는 ScriptWorker의 system prompt**다. 가르치는 출력은 `schemas.models:FullScript`(chapters·segments JSON)이고, 워커의 `response_model`도 FullScript다.
D-0021 작업 6은 여기에 `script.schema:Script`(script.yaml 형태) 예시를 넣어 파리티를 통과시키라고 한다.
그러면 한 프롬프트가 본문으로는 FullScript를, 예시 블록으로는 Script를 가르친다. 파리티 테스트는 예시 블록만 검사하므로 **통과하지만 실제 LLM 출력 계약은 검사하지 않는다** — 15 P4(CHART-AP-44 재발 방지)의 취지와 반대다.
ScriptWorker를 Script로 바꾸는 것은 오케스트레이터 연결(Phase 6.8)이고 D-0021 §3이 제외했다.

## 선택지
| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| A | 지침 문면대로 `prompts/script.md`에 Script YAML 예시(v3 5문장) 추가, 파리티 script→Script | xfail 해제. 살아 있는 LLM 입력에 모순된 두 스키마. 테스트가 실제 계약을 안 봄 | 블록 삭제 |
| B | 파리티 `script` 대상을 **워커가 실제로 검증하는 모델**(`schemas.models:FullScript`)로 바꾸고, 프롬프트의 스키마 설명 아래에 FullScript 완전 예시를 ```json 블록으로 추가(v3 5문장을 segments로). Phase 6.8에서 ScriptWorker가 Script로 바뀔 때 대상도 Script로 | xfail 해제. 파리티가 진짜 계약을 검사. LLM 입력은 기존 계약의 예시만 늘어남(펜스 출력 위험은 추출기 LLM-AP-005가 처리) | 매핑 한 줄 + 블록 삭제 |
| C | 파리티는 xfail 유지, Script 예시는 6.8에 | 가장 보수적. 합격 조건 "남은 xfail 3" 불충족 | — |

## Opus 권고: B
- ① 한 줄 매핑과 블록 하나라 되돌리기 쉽다.
- ② 15 P4 "프롬프트가 가르친 모양 = 검증기가 받는 모양"이 테스트의 목적이다. 19 부록 B의 script→Script 매핑은 워커가 Script를 내는 최종 상태를 가정한 것이다.
- ③ 실측: `workers/script_worker.py` `response_model = FullScript`, 프롬프트 본문 "FullScript JSON 스키마".
- research/director/visual_qa는 지침대로 6.9까지 제외(파라미터화).

## 막히는 범위
- 막힘: 작업 6 커밋만.
- 계속함: 작업 8·9(SunHi 전편 재합성·렌더·시트·표), 자산 재생성.

## §7 해당 여부
없음. Fable 전결.
