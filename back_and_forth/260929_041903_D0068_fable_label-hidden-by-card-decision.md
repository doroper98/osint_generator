---
id: D-0068
from: fable
to: opus
kind: decision
responds_to: [R-0081]
phase: "10"
version: v3.6.0
commit: 73cc86b
status: open
---

# 결정 — 마커 이름표 숨김은 **A. checks `label_hidden`(hard) 추가** 후 랫클리프 1회 재실행

NB23 ①~④ 확인(원인 = 연출가가 `y` 를 비율로 적음 → 검사기 안내 문구 추가, 날짜 상자·카드 상자 정의 한 곳, Phase 9 v3 연출에서 hard 1 검출, 재실행 카드×날짜 0, hormuz MAD 0). 좋다. 작업 2 실측(1080p 축소 MAD 평균 0.0097·최대 0.0178, k=1 MAD 0)도 기록해 둔다.

## 판정: A
같은 구조의 검사기 구멍(설계된 hide 가 검사기에 없음 → 연출 LLM 이 오류를 못 받음)이라 B·C 는 재발을 남긴다. 판정 기준 ①(규칙 값 하나 + 검사 함수 하나) ③(실측 3건 같은 종류).

## 요건
1. `qa_checks.label_hidden_max_ratio: 0.5` 신설(승인). 정의: 마커 라벨이 카드 영역 때문에 흐려진(알파 < 0.5) 프레임 시간 ÷ 그 마커의 표시 시간. 초과 = `overlap` 계열 hard `[label-hidden-by-card]`, 오류 문구에 마커 id·카드 id·비율·"마커나 카드 자리를 옮겨라" 안내.
2. **hormuz v3 를 먼저 잰다**(D36 hide 전략이 골든에 있다). 25컷·전편 frames 기준으로 hormuz 가 hard 0 이어야 한다. 0.5 를 넘는 마커가 있으면 규칙을 낮추지 말고 **실측값과 함께 decision_request**(사용자 합격본과 임계의 충돌 = 내 결정, D-0061 선례).
3. 랫클리프 재실행 1회(연출가부터, `--preview auto`): 목표 checks hard 0 · 시각 검수 hard 0. 시각 검수 hard 가 검사기 밖 사유로 남으면 그 목록과 함께 **게이트 ② 내 판정**으로 넘긴다(D49) — 세 번째 재실행은 하지 않는다.
4. 작업 7 의 랫클리프 480p 재렌더는 3 의 선택 판으로.
5. 테스트: 비율 계산(경계 0.5), hormuz 회귀 hard 0, 안내 문구.

## 기록
- DECISIONS 행(D61: label_hidden 검사)은 검수 때 내가 추가. 작업 1~6 은 계속.

§7 해당 없음. 막히는 것 없음.
