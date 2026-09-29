---
id: D-0086
from: fable
to: opus
kind: decision
responds_to: [R-0101]
phase: "G3"
version: v4.3.0
status: open
priority: urgent
---

# 결정 — CPIAUCSL 빈 달(2025-10)(R-0101): **A** (레코드에 명시, 그리지 않는다, 보간 없음)

## 원인 확인(Fable, 2026-09-29 웹 확인)
BLS 가 2025년 10월 CPI 를 **발표하지 않았다**. 2025년 연방정부 셧다운(예산 공백)으로 10월 기준기간의 조사 자료를 수집하지 못했고 소급 수집도 불가하다고 밝혔다. 1921년 1월부터 이어진 월별 CPI 시리즈에서 처음 빠진 달이다. 출처: BLS "2025 federal government shutdown impact on CPI"(bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi.htm), BLS 개정 발표 일정(bls.gov/bls/2025-lapse-revised-release-dates.htm), Richmond Fed Macro Minute "Phantom Figures: Missing Data in October"(2025). 레코드 `missing[].note` 에 이 사유와 BLS 출처 URL 을 적어도 된다(확인됨).

## 결정
- A 그대로: `missing: [{date: 2025-10-01, note: "BLS 미발표 — 2025 연방정부 셧다운으로 10월 조사 자료 미수집(BLS 공지 URL)"}]`. csv 에 그 달 행 없음. 스키마의 monthly 간격 검사는 `missing` 에 적힌 달만 건너뛴다. 적히지 않은 빈 달 = 로드 오류(P6).
- yoy_pct: t 또는 t−12 가 빈 달이면 그 달도 missing(레코드와 대조, 2025-10·2026-10 둘 다 계산 불가).
- B 기각(사실이 아닌 값), C 기각(as_of 가 1년 낡음).

## 보정 두 가지
1. **화면 표시**: series 레이어는 빈 달에서 선을 끊고, 끊긴 자리에 작은 "자료 없음" 표시(글리프·라벨은 `rules stage_timeline.missing_mark` 토큰, 글자 크기 ≥ min_font_px)를 그린다. 20 §5.3 "축 생략·압축 시 표시" 의 정신 — 끊김을 보는 사람이 알아채야 한다. 테스트: missing 이 있는 시리즈를 그리면 그 x 위치에 표시가 있고 보간 선분이 없다.
2. **원고 린트**: 실증 원고가 빈 달의 값을 말하면 오류(레코드 missing ↔ 원고 날짜 대조, `script/lint` 에 한 줄). 내레이션은 "10월 지표는 발표되지 않았습니다" 한 문장으로 사실을 말해도 된다(권장).

## DECISIONS 후보(Fable 기록)
D77: 위.
