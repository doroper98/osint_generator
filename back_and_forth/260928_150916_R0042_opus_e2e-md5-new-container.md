---
id: R-0042
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "6.8"
version: v3.0.0
commit: 644ca38
status: in_progress
---

# e2e 합격 "최종 mp4 md5 = 94d39281…(Phase 6.5)" 는 새 컨테이너에서 도달할 수 없다 + StageResult 필드 차이

## 쟁점 1 — md5 기준
D-0040 §2 e2e 행은 오케스트레이터 경유 final.mp4 md5 = Phase 6.5 artifacts `94d39281…` 을 요구한다.
- 이 컨테이너(재기동 5)에는 `tts/` 캐시가 없다. artifacts 브랜치 6개 모두 `hormuz/out` 만 있고 tts·plan 은 없다(`git ls-tree` 확인).
- 그래서 `script.plan --tts edge` 가 45문장을 재합성한다. Phase 5 run_log §1 실측: 재합성은 문장 길이가 3~5 ms 달라지고 25컷 MAD 0.003 수준 차이가 난다. final md5 는 반드시 달라진다.
- Phase 6.5 의 "Phase 6 과 바이트 동일"은 같은 컨테이너(tts 캐시 유지)였기 때문에 가능했다.

### 선택지
**A. 같은 컨테이너 대조로 바꾼다(권고)**
- 이 컨테이너에서 엔진 CLI 를 직접 돌린 final.mp4 md5 = Command Center 경유 final.mp4 md5(같은 plan·tts). "오케스트레이터 경유 = CLI 직접"이라는 기준의 취지를 그대로 증명한다.
- 추가: 25컷 Phase 6.5 대비 mean ≤ 0.01 · max ≤ 0.1(재합성 편차 허용선, Phase 5 선례), provenance features_used 동일.
- 추가: 이번 artifacts(`artifacts/phase6.8-v3.0.0`)에 `hormuz/tts/`·`plan.json` 도 넣는다. 다음 컨테이너부터 복원하면 바이트 동일 대조가 다시 가능하다(재현성 구멍을 닫음).
- 위험: 전편 렌더 2회(시간). 되돌리기: 합격표 한 행.
**B. tts 를 다시 만들지 않고 기다린다** — 복원할 tts 가 어디에도 없다. 불가.
**C. md5 조건 삭제, 25컷만** — 오케스트레이터가 엔진 입력을 바꾸지 않았다는 증명이 약해진다. 권고하지 않는다.

## 쟁점 2 — StageResult 필드 (D-0040 작업 4 "차이가 있으면 decision_request")
- 16 §4: `ok, artifacts, provenance, drops, errors`. 저장소 `schemas/engine_models.py:95`: 같은 다섯 + `stage`(필수, Phase 2) + `warnings`(v2.3.0 optional). 16 §4 필드는 전부 같은 뜻·같은 타입이고, drops·errors 가 있으면 ok=False 검증도 있다.
- **권고: 저장소 모델 그대로(추가 필드 유지).** 16 §4 는 최소 계약으로 읽는다. engine_service 는 `stage` 가 요청한 단계와 같은지도 검사한다.

## 쟁점 3 — `engine.validate` 대체(D-0040 작업 4 지시 이행 방식, 보고)
- `direction_validate` 단계 = `python -m script.lint <proj>`(새 CLI: `script.yaml` 을 `script.schema:Script` 로 로드 + 린트, 오류 있으면 ok=False). 연출·레지스트리·예약영역 검사는 종전대로 `engine.render --preview` 의 `load_project` 가 한다(16 §4 표에 주석).
- 이견 있으면 알려 달라. 지시 범위 안이라 진행한다.

## 막히는 범위
- 쟁점 1: 작업 10 의 e2e 합격 판정만. 작업 4~9 는 계속한다. 컨테이너 자산 준비(fonts·ne·tiles·flags·bgm)는 지금 시작했다. Commons(인물·미디어)는 429 가 계속되고 있어 e2e 준비가 늦어질 수 있다.
- 쟁점 2: 막힘 없음(권고안이 현 상태).

## §7 해당 여부
아니다.
