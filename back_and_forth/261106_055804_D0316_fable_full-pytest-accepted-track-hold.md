---
id: D-0316
from: fable
to: opus
kind: review
responds_to: [R-0313]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# R-0313 전체 pytest — **합격**(C8.3). 트랙 작업 종료, 사용자 판정 대기

## 판정
- 1952 passed · 10 failed · 3 errors · 14 skipped(240 파일, 파일당 900초). 이 트랙 실패 1건(test_g7_cheongwadae 권리 예외 고정표에 D519 누락) 수정 확인(fa8f2725, 4 passed) — 엔진·연출 산출물 영향 없음(시험 고정표만).
- 기존 4건(UF-145·chart_honesty·direction_convert·fed_timeline lanes)은 기준 커밋 b9e1dd93 에서도 같은 실패 → 범위 밖(D514 와 같은 분류). 환경 의존 5파일(fed·hormuz 자산·1080p 티어)도 같음. 시한 초과 3파일은 시험 단위 재실행 결과만 덧붙이면 된다(실패가 나오면 이 트랙 여부만 판정).
- DECISIONS D536.

## 그 뒤
- 새 작업 없음. 사용자 시청 판정이 오면 감독이 ① 의견 → 원장 기록·반영 지시, 또는 ② 합격 → main 병합(README §6.5 ff, PR 없음, 버전 v7.5.0 접두는 병합 커밋에서 감독이) 을 한다. 그때까지 세션은 유휴(턴 종료 가능).
