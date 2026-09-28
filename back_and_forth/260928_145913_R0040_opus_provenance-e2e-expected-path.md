---
id: R-0040
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "6.8"
version: v2.5.5
commit: 54002af
status: awaiting_decision
---

# test_provenance_e2e — 기대값(뱃지 9)과 경로(`--preview golden` → out/provenance.json)가 실측과 다르다

## 쟁점
D-0040 합격 조건은 `test_provenance_e2e` 통과(xfail 0)다. 그런데 테스트(19 부록 B, 15 §P5 예시)가 실측과 세 곳 다르다.
1. **뱃지 수** — 테스트 `badges: 9`. v3 골든 연출(`projects/hormuz_korea/direction.py`)의 badge 이벤트는 **8개**다. Phase 1(v3 직접 재현)부터 6.5까지 provenance 전부 `badges: 8`(person 3·flag 4·emblem 1). 9는 문서 추정값으로 보인다.
2. **`--preview golden`** — `engine.render --preview` 는 `auto` 또는 초 목록만 받는다. `golden` 인자 없음.
3. **provenance 위치** — provenance 는 `engine.mux` 만 쓴다(`out/provenance.json`). preview 는 쓰지 않는다. 15 P5 "돌지 않은 단계는 기록하지 않는다" 때문에 preview 가 `out/` 에 쓰면 mux·mix 를 한 것처럼 보인다.
(나머지 키 camera_moves 5·dips 4·panels 5종(relation 포함)·media 2/2/1/2·label_lod true·drops [] 는 일치.)

## 선택지
**A. preview 에 provenance 를 쓰게 하고 테스트를 그 경로로(권고)**
- `--preview golden` = `docs/handoff/golden` 25 앵커 시각(golden_compare 의 anchor_time 재사용). preview 는 `prev/provenance.json` 을 쓴다. `stages` 는 preview 만 true(render·mix·mux false).
- 테스트: `prev/provenance.json` 을 읽는다. `badges` 기대값 8. 15 §P5 예시·19 부록 B 의 "9"와 "refusal" 은 문서 주석으로 정정(과거 문서는 주석만).
- 위험: 테스트 기대값 변경 = "테스트를 맞춘다" 의심. 근거가 골든 연출 실물(8)이라 방어 가능. 되돌리기: 테스트 한 줄 + preview provenance 쓰기 제거.
**B. 테스트를 전편 경로(render→mix→mux)로 — out/provenance.json 그대로**
- 292초 전편 렌더를 pytest 안에서 돈다(이 컨테이너 수 분~십수 분). 테스트 스위트가 느려지고 CI·Fable 컨테이너 부담.
- 뱃지는 A 와 같이 8 로 정정 필요.
**C. 기대값 9 유지, 뱃지 1개를 연출에 추가**
- 골든 25컷이 바뀐다(v3 합격 값 변경, §7.2 — 기본 유지). 권고하지 않는다.

## 추가 쟁점 (같이 결정 요청)
테스트는 `projects/hormuz_korea` 의 plan.json·tts·지오 자산이 필요하다(저장소에 없고 `fetch_data`·`script.plan`·`geo.prep` 로 만든다). 자산이 없는 컨테이너에서:
- **A1(권고)**: 오류로 실패(P6 — 조용히 넘기지 않음). 메시지에 run_log §0 준비 명령. Fable 컨테이너도 준비가 필요하다.
- A2: `skipif(자산 없음, reason=…)`. 리포트에 사유가 남지만 관성 방지 테스트가 준비 안 된 곳에서 돌지 않는다.

## Opus 권고
**A + A1.** ① 되돌리기 쉬움(테스트 한 줄·preview 기록 한 함수) ② 16 §4 `preview` 단계가 StageResult 에 provenance 를 싣는 계약과 맞는다 ③ 기대값은 저장소 실물(골든 연출 8)이 문서 추정(9)보다 우선.

## 근거 자료
- `tests/anti_inertia/test_provenance_e2e.py:21-44`, `engine/render.py:160-185`, `engine/provenance.py:26`
- `docs/handoff/reports/phase{1,2,5,6,6_5}/provenance*.json` `badges: 8`
- `docs/handoff/reports/phase6_8/inventory.md` §5

## 막히는 범위
- 막힘: 작업 7 의 xfail 해제·테스트 수정, preview provenance 쓰기.
- 계속: 작업 1~6, 8(상태 머신·engine_service·Script 전환·게이트·병합).

## §7 해당 여부
아니다(Fable 전결).
