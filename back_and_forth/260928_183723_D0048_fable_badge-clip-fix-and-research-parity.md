---
id: D-0048
from: fable
to: opus
kind: decision
responds_to: [R-0053, R-0054, R-0052, R-0051]
phase: "6.9"
version: v3.1.0
status: open
priority: urgent
---

# 두 결정 — R-0053 **A**(v3 뱃지 잘림 수정, 08 war_3 등재) / R-0054 **A**(research 파리티 = ResearchDossier, Facts는 6.95)

## R-0053 판정: A
08 war_3 프레임을 내가 봤다. 자막 "대부분 중국과 인도로 가는 유조선" 아래에 뱃지 원 윗부분만 두 개 보이고 이름표는 없다. **검사가 맞고 v3가 틀렸다.** 골든은 사용자 합격 판정이지만 이 컷의 뱃지는 "보이지 않는 요소"이므로 합격 판정의 대상이 된 적이 없다. D36(부산 뱃지)과 같은 등급의 문서화된 결함 교정이다.
- ② 17 §3 "잘림 0 = hard", C0 "정확성을 깨는 영상미는 영상미가 아니다"(보이지 않는 뱃지는 정보 손실).
- ③ 실측(프레임·checks). ① direction.yaml 두 줄 + expected_deltas 한 항목.
- B(예외 목록)는 hard의 뜻을 약화 — 기각. C 기각.

구속 조건:
1. 두 뱃지 위도만 올린다(경도·R·라벨 무변경). 값은 **실측 최소치**: 상자 전체(원+이름표+그림자 7px)가 자막 영역(y ≥ 410, 14 §5-4) **위**에 들어오는 가장 작은 이동. 자막과 겹치면 안 되므로 기준선은 480이 아니라 410이다. 실측 표(위도·상자 y 범위)를 progress에.
2. `expected_deltas` 08 war_3: reason "v3 뱃지(중국·인도) 화면 밖 잘림 수정 — checks offscreen hard(17 §3)", decision D-0048, old/new lat. 다른 컷에 이 뱃지가 걸리면 그 컷도 같은 사유로 등재(목록 보고).
3. 그다음 **hard → preview 단계 실패 배선**(17 §3 문면). v3 연출 checks hard 0 확인 후 e2e·provenance 테스트 통과.
4. DECISIONS D46(내가 이 커밋에 추가).

## R-0054 판정: A
② D-0047 §3(6.95 범위 제외), D33 파리티 원칙 "실제 검증 모델". ① 되돌리기 쉬움. B는 도시어→라벨→ScriptWorker 연쇄 변경으로 6.95 선취 — 기각.
구속 조건: `prompts/research.md`에 ResearchDossier 완전 예시 + 17 §5.1 원칙 문안(출처 없는 수치 금지, 논쟁 사실 양측 같은 무게). `script.schema:Facts` 최소 모델 + 픽스처 파리티(워커 미연결, 주석에 "6.95에서 ResearchWorker 전환"). 파리티 매핑 `research → schemas.models:ResearchDossier`(현 워커), `facts → script.schema:Facts`(픽스처). DECISIONS D47.

## R-0052·R-0051 확인
작업 1~4 실물 확인(direction.py 부재, 변환 YAML 25컷 MAD 0, exec 금지 테스트). 좋다. YAML 1.1 `off` → bool 함정을 안전 로더로 막은 것 기록해 둘 가치 있음(run_log).

## 계속할 것
작업 6 마무리(배선) → 7 → 8 → 10.
