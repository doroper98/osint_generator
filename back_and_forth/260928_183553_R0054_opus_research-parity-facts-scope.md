---
id: R-0054
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "6.9"
version: v3.1.0
commit: 506cfbe
status: in_progress
---

# 작업 7 — research 프롬프트 파리티 대상: 워커가 실제로 검증하는 ResearchDossier vs 새 Facts

## 쟁점
D-0047 작업 7 은 "research 는 17 §5.1 문안 개정 + Facts 모델 최소 정의, 파리티 PENDING 해제"다.
그런데 `prompts/research.md` 를 쓰는 `ResearchWorker.response_model` 은 **ResearchDossier**(claims·evidence·seeds, v0.x 부터 intake→source→research 흐름과 D-0043 라벨 계산이 쓰는 도시어)다. 파리티 원칙(D33, 15 P4)은 "그 프롬프트를 쓰는 워커가 **실제로** 검증하는 모델"이다.
17 §5.1 의 `facts: [{id, text, date, place, actors, numbers, source_ids, confidence, contested, sides}]` 는 18(6.95 소스 인테이크)의 claims.json 과 맞물린다.

## 선택지
**A. 6.9: research 파리티 = ResearchDossier(현 워커), research.md 에 완전한 도시어 예시 + 17 §5.1 원칙(출처 없는 수치 금지·논쟁 사실은 양측)을 문안에. `script.schema:Facts` 는 최소 모델만 정의하고 픽스처로 파리티 검사(워커 연결 없음). 워커 출력 전환(Dossier→Facts)은 6.95(권고)**
- 지금 도시어를 바꾸면 intake→research→script(D-0043 라벨: 도시어 claim status)가 함께 바뀐다 — 6.9 범위 밖(D-0047 §3 "소스 인테이크·claims(6.95) 하지 않음"). 되돌리기 쉬움.
**B. 6.9 에서 ResearchWorker 를 Facts 로 전환** — 라벨 계산·ScriptWorker 입력·테스트 연쇄 변경, 6.95 설계를 앞당긴다.

## Opus 권고
**A.** ① 되돌리기 쉬움 ② 6.9/6.95 경계(D-0047 §3) ③ 파리티 D33 원칙(실제 검증 모델).

## 막히는 범위
- 막힘: research.md 개정·Facts 모델.
- 계속: director·visual_qa·revise_direction 프롬프트·모델(QAVerdict·Revision), script.md 문안 개정.

## §7 해당 여부
아니다.
