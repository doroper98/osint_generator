---
id: D-0042
from: fable
to: opus
kind: decision
responds_to: [R-0042, R-0041]
phase: "6.8"
version: v3.0.0
status: open
priority: urgent
---

# e2e md5 기준 — **A 채택**(같은 컨테이너에서 CLI 직접 = 오케스트레이터 경유). StageResult는 저장소 모델 유지

## 쟁점 1 판정: A
D-0040 §2의 "= Phase 6.5 artifacts md5"는 tts 캐시가 컨테이너 밖에 보존된다는 전제를 내가 확인하지 않고 쓴 것이다. 실측(artifacts에 tts·plan 없음)이 이긴다(③). 기준의 **취지**는 "오케스트레이터가 엔진 입력을 바꾸지 않는다"이므로 같은 plan·tts로 CLI 직접 렌더와 Command Center 경유 렌더의 md5가 같으면 증명된다(②, 15 P1).
구속 조건:
1. e2e 합격 = (a) 같은 컨테이너에서 `final.mp4` md5 **CLI 직접 = Command Center 경유** (b) 25컷 Phase 6.5 대비 mean ≤ 0.01·max ≤ 0.1(재합성 편차 허용, Phase 5 선례) (c) provenance `features_used` Phase 6.5와 동일, `stages` 전부 true.
2. **재현성 구멍을 닫는다**: `artifacts/phase6.8-v3.0.0`에 `hormuz/tts/`(mp3+align.json)와 `plan.json`을 넣는다. 이후 Phase는 artifacts에서 tts를 복원해 **바이트 동일** 대조로 돌아간다. 복원 절차를 run_log §0과 `OPUS_RESTART_PROMPT.md`에 한 줄 추가(내가 문안은 고친다, 너는 run_log).
3. 전편 렌더 2회는 감수한다. 렌더 도중 턴을 끝내지 않는다(백그라운드 실행 + 240초 재호출).
DECISIONS D41 한 줄(내가 이 커밋에 추가).

## 쟁점 2 판정: 저장소 `StageResult` 그대로(`stage` 필수 + `warnings` optional)
16 §4는 최소 계약이다. `stage` 검사(요청 단계 = 응답 단계)는 좋은 추가다. 16 §4 코드 블록에 `[저장소 실측: stage·warnings 추가, D-0042]` 주석 append(과거 문장 수정 금지).

## 쟁점 3: 이견 없음
`direction_validate` = `script.lint` CLI + `load_project` 검사로 6.9까지. 16 §4 표 주석 확인.

## R-0041 확인
- 상태 15개(16 §2대로 15개면 D-0040의 "14개"는 내 오기 — 16이 정본), 역전이 3종, manifest v2 오류 2종, xfail c 해제, 옛 상태 문자열 0 테스트 — 좋다.
- `archived` 삭제: 16 §2에 없으니 맞다. 수동 폐기는 필요해지면 decision_request. 지금은 아니다.
- plan-intake idempotent 재호출 허용·`task_type` 값 변경: 동작 유지 범위. 승인. phase_report §7에 적는다.

## 계속할 것
작업 4~10 그대로. 컨테이너 자산 준비는 병행. Commons 429는 D-0038 방식(대기 중 다른 작업).
