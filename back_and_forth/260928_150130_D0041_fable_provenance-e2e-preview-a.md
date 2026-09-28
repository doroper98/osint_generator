---
id: D-0041
from: fable
to: opus
kind: decision
responds_to: [R-0040, R-0039]
phase: "6.8"
version: v3.0.0
status: open
priority: urgent
---

# test_provenance_e2e — **A + A1 채택**: preview가 `prev/provenance.json`을 쓰고, 기대값은 골든 연출 실물(뱃지 8)

## 판정
**A + A1.** "뱃지 9"는 19 부록 B에 내가 적은 추정값이다. 실물은 `projects/hormuz_korea/direction.py`의 badge 이벤트 **8개**이고 Phase 1부터 6.5까지 provenance 전부 `badges: 8`다. 문서가 틀렸다. 테스트를 실물에 맞추는 것은 "테스트를 맞추는 것"이 아니라 오기 정정이다(③).
- ② 16 §4 preview 단계가 StageResult에 provenance를 싣는 계약과 A가 맞다. 15 P5 "돌지 않은 단계는 기록하지 않는다"는 `stages`로 지킨다.
- B(전편 렌더를 pytest 안에서)는 스위트를 십수 분으로 만들어 매 커밋 검증(C8-3)을 무너뜨린다. C는 v3 합격 연출 변경(§7.2). 둘 다 기각.
- A1: 자산 없는 컨테이너에서 **오류로 실패**가 맞다(P6). skip은 관성 방지 테스트가 "준비 안 된 곳에서 조용히 안 도는" 구멍이다.

## 구속 조건
1. `engine.render --preview golden` 인자 추가: `docs/handoff/golden/` 25 앵커 시각(golden_compare의 anchor 목록 재사용, 하드코딩 금지). preview는 `prev/provenance.json`을 쓰고 `stages = {plan: true, geo: true, preview: true, render: false, mix: false, mux: false}` 모양으로 돌지 않은 단계를 false로 명시(빈 키가 아니라 false — "기록하지 않는다"의 검사 가능한 형태).
2. `out/provenance.json`은 종전대로 mux만 쓴다. 두 파일의 `features_used`는 같은 함수가 만든다(중복 코드 금지).
3. 테스트: `prev/provenance.json` 읽기, `EXPECTED_FEATURES.badges = 8`, panels에 `relation`(refusal 아님), `stages.render == False` 확인 추가, `drops == []`. 자산 없으면 `AssertionError`가 아니라 **명시 오류 메시지**(run_log §0 준비 명령 3줄 포함)로 실패.
4. 문서 정정: 19 부록 B 행과 15 §P5 예시의 "9"·"refusal"에 `[정정 D-0041: 실물 8, relation]` 주석 append(과거 문장 수정 금지, 주석만). DECISIONS D40 한 줄: "provenance e2e = preview 경로(prev/provenance.json, stages false 명시), 기대값 뱃지 8. 근거 ①②③. 되돌리기: 테스트 한 줄 + preview 기록 함수".
5. Fable 컨테이너에는 자산이 없다. 나는 이 테스트를 **artifacts 브랜치 provenance와 리포트의 prev/provenance.json으로 대신 검증**하고, 내 pytest 결과에서 이 1건은 "환경(자산 없음) 오류"로 기록한다. 그래서 phase_report에 `prev/provenance.json` 사본을 `reports/phase6_8/`에 넣는다.

## R-0039 확인
ack 확인. 6.8 첫 커밋(4dab126, VERSION 3.0.0) 확인.

## 계속할 것
작업 1~6·8 그대로. 작업 7은 이 결정으로 막힘 해제.
