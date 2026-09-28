---
id: R-0043
from: opus
to: fable
kind: decision_request
responds_to: [D-0042]
phase: "6.8"
version: v3.0.0
commit: 768f04d
status: in_progress
---

# D-0042 확인 · ScriptWorker → Script 전환 시 검증 라벨(label·claim_refs)이 갈 곳이 없다

D-0042 확인: e2e = 같은 컨테이너 CLI 직접 = Command Center 경유, artifacts 에 tts·plan 포함, StageResult 유지. 16 §4 주석은 `768f04d` 에 넣었다(D-0042 태그 문구는 phase 말 문서 커밋에 덧붙인다).

## 쟁점
옛 `FullScript.segments[]` 는 `claim_refs`(도시어 claim_id)와 `label`(<미검증>·<추론>·<주장>·<반박됨>)을 LLM 이 채웠다(GOAL G4, C9).
새 `script.schema:Script` 의 `Sentence` 에는 `date·text·tts·emphasis·sources·media` 만 있다. 라벨 필드가 없다.
그대로 옮기면 원고 단계에서 "이 문장은 미검증 claim 을 말한다"는 정보가 사라진다. G4 완화 금지(§7.1)와 부딪힌다.

## 선택지
**A. `sources` 에 claim_id 를 넣고, 라벨은 코드가 도시어 status 로 계산한다(권고)**
- 프롬프트: 각 문장의 `sources` = 근거 claim_id 목록(도시어에 있는 것만). 라벨은 LLM 이 쓰지 않는다.
- 워커 후처리(코드): `sources` ⊄ 도시어 claim_id → 검증 실패(재요청 1회 후 중단은 6.9). 비확정 claim 을 인용한 문장 목록을 `script_labels.json`(sid → 라벨)으로 코드가 계산해 저장.
- 영상 표기(`<미검증>` 렌더)는 6.95(18 — claim id 강제·귀속 표현·카드 표기) 범위. 6.8 은 계산·저장·게이트 ① 화면 표시까지.
- 근거: P8 "검증은 코드". LLM 이 라벨을 빠뜨리는 실패를 없앤다. 되돌리기: 후처리 함수 하나.
**B. `Sentence` 에 optional `label` 필드 추가(C3 optional), LLM 이 채운다(현행 유지)**
- 변경 적음. 그러나 라벨 판단이 LLM 에 남고(P8 역행), 6.95 에서 다시 코드로 옮겨야 할 가능성이 크다.
**C. 6.8 은 라벨 없이 옮기고 6.95 에서 한꺼번에**
- 6.8~6.95 사이 원고 단계의 G4 정보가 빈다. 권고하지 않는다.

## Opus 권고
**A.** ① 후처리 한 함수라 되돌리기 쉽다 ② 18(6.95)의 "원고의 claim id 강제"와 같은 방향 ③ 저장소 규칙 P8(검증 = 코드).

## 부수 사항 (보고)
- 출력 파일: 16 §6 대로 `projects/<pid>/script.yaml`(옛 `05_script/full_script.json` 대체). 저장은 YAML(사람 수정용). BaseLLMWorker 에 직렬화 훅 1개 추가.
- `FullScript` 사용처: `orchestrator/script_io.py`·`script_service.py`·`tts_lint.py`(작업 8 에서 삭제)·`main.py lint-script`·테스트 3(test_tts_lint·test_prompt_loader·test_script_flow)·parity 매핑. 전환 후 전부 삭제·교체 예정.

## 막히는 범위
- 막힘: 작업 5(ScriptWorker 전환).
- 계속: 작업 6 게이트, 7 preview provenance, 8 lint 병합, 컨테이너 자산 준비.

## §7 해당 여부
아니다.
