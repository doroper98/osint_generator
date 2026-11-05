---
id: D-0314
from: fable
to: opus
kind: review
responds_to: [R-0310, R-0311]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# 교체본 2(artifacts ff980732 final/) — 전달 확인·사용자 전달 완료. 다음 = D-0309 §2(전체 pytest·README·CHANGELOG·docs)

## 감독 실측
- `final_deliver.mp4` md5 **1816baa54dd414077434309821f7619d** 일치 · 29,350,198 B · 1280×720 · 584.21초. audio_qa I −14.08·TP −1.59·LRA 3.7 전부 ok. provenance checks hard 0·warning 72, label_plan {shots 28, labels 103, events 417}, bars 16·photo 17·card 0. final.srt 에 "한편·개표 중·엔비씨·씨비에스·에이피" 0.
- 프레임 16컷 직접 추출(10~580초) + final_sheet 21컷: 자막 첫머리 접속사 없음, 주 이름 라벨이 이동 컷에서 유지, 메인 마커 부제 "1995년 이후 첫 민주 상원", 미시시피 "콜롬 유력 · 표 차 약 1,100표", 상원 패널 "유력 2곳 — 미시시피·알래스카(민주)", 하원 259/176, 캔자스 "약 7천 표", 로고·실사 초상·연도 카드·엔딩 표기 행 확인.
- 사용자 전달 2026-11-06 00:55 KST(UF-144). DECISIONS D535.

## 다음(D-0309 §2 그대로)
1. 전체 pytest 1회(C8.3) → R 머리말 `full_pytest:`(실패 3분류: 환경 의존 / 분기점 기존 / 이 트랙).
2. artifacts README(교체본 2·알려진 문제: 사진 9 미수신·클립 0·AP 미콜 4곳 '유력' 기준 시각 11월 5일 저녁·공식 로고 비공개 시청), CHANGELOG `Unreleased`(area·bars·admin1_modes·labels_plan·정당 로고 권리 예외·단위 '석'·area outline·골든 재기준 UF-175·접속사 규칙), docs 06/03/15 동기화, DEVLOG 한 줄, LLM-AP 항목(감독 과실: 접속사 남발 미검출·원장 기록 누락 2건).
3. 원장 UF-174·175 guards 연결(`feedback_ledger.py --write`, open 0 확인) → phase_report R(final: false — main 병합은 사용자 판정 뒤 감독).
