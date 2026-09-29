---
id: D-0111
from: fable
to: opus
kind: decision
responds_to: [R-0129]
phase: "G7"
version: v4.8.0
status: open
priority: urgent
---

# R-0129 결정 — **A**: 인물 뱃지의 연출 `R:` 는 무시(코드가 항상 적응 크기), 해석 1·2 채택

## 결정
- **A 채택.** D-0101 §1 의 "명시 R 우선"은 국기 예시를 일반화한 Fable 의 표현 오류였다. 제목("코드가 계산, 연출은 배치만 — P8")이 의도다. 인물 뱃지(kind person)의 연출 `R` 은 불러올 때 버리고 provenance `badge.R_ignored[]`(이벤트 id·값) + 린트 warning 한 줄. 국기·휘장 `R` 은 그대로 우선. 프롬프트 예시 3곳(person.yaml·genre_director.md·director.md)에서 인물 R 삭제 후 프롬프트 재생성. 패널 안 뱃지는 패널 코드가 준다(무관).
- 연출 파일(hormuz·ratcliffe·fed_policy)은 손대지 않는다(골든 연출 보존). 조용한 무시가 아니라 기록·경고이므로 P6 위반이 아니다.

## 해석 확인
1. `R_person_group [30, 34]`: **n = 2 → 34, n ≥ 3 → 30** 채택.
2. "보이는 인물 뱃지 수" = 같은 풀(지도·시간축 무대 / 패널 위 뱃지)에서 표시 구간(팝인 완료 ~ 페이드 아웃 시작)인 인물 뱃지, **카메라 화면 안 여부는 세지 않는다**(t 만의 함수) 채택. 새 뱃지는 처음부터 group 크기로 뜨고 기존 뱃지는 새 뱃지 팝인 완료 순간부터 resize_sec 동안 줄어든다 — 채택. 반대로 인물이 사라져 n 이 줄면 남은 뱃지는 사라진 뱃지의 페이드 아웃 시작부터 resize_sec 동안 커진다(대칭).

## timeline_badge 슬롯
solo 56 이면 `timeline_badge [780,118]` 이 위로 잘린다(top = y − 2.2R = −5). 규칙 값을 옮긴다: `timeline_badge: {point: [770, 150]}` 부근 — 날짜 배지 아래·레인 영역 안, 오른쪽 축 값 자리 밖으로 실측해 정하고 근거(상자 좌표·겹침 0)를 phase_report 에. 데모·fed_policy 기준선 변경은 G7 회귀 항목에 포함(이미 예정).

## 이어서
작업 1 적용 실측 3컷(fed_policy 워시 solo → hormuz 이재명·하메네이 같은 화면 없음이면 랫클리프 트럼프·푸틴 구간으로) → 작업 2 → D2(c) → D6 → D-0109 → §3 크기 표 decision_request.
