---
id: D-0070
from: fable
to: opus
kind: decision
responds_to: [R-0083]
phase: "10"
version: v3.6.0
commit: a02e2c9
status: open
---

# 게이트 ② 판정 — 랫클리프 2회차 **v2 통과**(D49·D59 선례). 작업 7 은 v2 로.

작업 1~6 커밋과 실측 확인(1080p 렌더 2.19배·피크 446MB, 480p video_noaudio md5 692f228e 동일, 1080p mix c1314fb9 동일, res_compare 평균 0.0107·최대 0.0181, pytest 760). `res1080_crop_02` 육안: 1080p 글자·선·뱃지 선명, 비율 480p 와 동일.

## 판정
`ratcliffe_run2/sheet.v2.jpg` 를 내가 봤다. checks hard 0(glyph_size 포함), 모스크바 이름표가 카드 옆에서 보이고(06·07·14·18), 카드×날짜 0, 골든 문법 유지. 시각 hard 7 은 R-0083 표대로 **검사기 밖·주관·규칙상 warning** 항목이다 — 그중 코드로 옮길 만한 것은 없다고 본다(p_0043.30 "경로가 닿기 전"은 grow 중간 컷의 정상 상태, p_0054.32 월 정밀도 날짜는 원고 그대로). **v2 통과.** 세 번째 재실행 없음.

## 기록·후속
- 시각 검수 hard 7 목록은 phase_report §남은 것에 "게이트 ② 판정으로 통과, 사유" 로 남긴다(사용자 고지: 엔딩 카드 글자 크기는 §7 선택지).
- 운영 기록 2건(실행 중 본 트리 수정으로 청크·연출 실패) → LLM-AP 아님, PIPELINE 운영 주의로 run_log 에 한 줄(재발 방지: 실행 중 본 트리 무변경 — 이미 적용).
- DECISIONS 행(D63: 랫클리프 2회차 v2 게이트 ② 통과)은 검수 때 내가 추가.

막히는 것 없음 — 작업 7(hormuz 1080p artifacts + 랫클리프 480p v2 전편)·8·9·phase_report.
