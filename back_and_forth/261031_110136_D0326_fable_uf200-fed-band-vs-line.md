---
id: D-0326
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 연준 금리 아일랜드: band 는 일별 원자료 그대로(발효일 계단), 선은 월평균 유지. 장치 [band-line-outside] (UF-200)

사용자 원문(2026-10-31, UF-200): **"fed 금리 관련해서 왜 상한과 하한의 밴드와 금리 기준 선(노란색)이 다른 구간이 있지? 그리고 기준금리가 계속 유지 되는 구간임에도 노란색에 픽셀 수준에서 높이가 다른 부분이 있는거야?"**
담당: 쇼케이스 세션 3(showcase_econ, final 렌더 전).

## 1. 원인(감독 확인, data/series)
- band = `DFEDTARL`/`DFEDTARU` 등재본이 **월 표본**(날짜가 매달 1일, 값은 그 달의 변경 후 값: 2025-10-01 3.75~4.0, 2025-12-01 3.5~3.75). 실제 발효일은 10/30·12/11 인데 **달 첫날로 당겨져** 그려진다.
- 선 = `FEDFUNDS` **월평균**(style step, 달 첫날~다음 달 첫날 유지). 인하가 있던 달은 평균이 두 수준 사이에 선다 — 2025-10 평균 4.09 > band 상단 4.0, 2025-12 평균 3.72(상단 3.75 바로 아래). → 인하 달에 선이 밴드 밖·가장자리로 나간다. **데이터는 둘 다 맞고, 날짜 규약이 다르다.**
- 픽셀 단차: 2026-04 3.64 → 2026-05 3.63, 실제 1bp. 축 3~4.75% 에서 1bp ≈ 2px. 실제 값이다(렌더 오류 아님).

## 2. 결정
1. **band 는 일별 원자료**(`data/series/raw/DFEDTARL.csv`·`DFEDTARU.csv`)에서 **발효일에 계단**. 등재본을 일별로 다시 만든다(transform raw, frequency daily, as_of 그대로). 월 표본 등재본은 삭제(P2). 선은 FEDFUNDS 월평균 그대로(공식 월 시리즈 — 월축 아일랜드에 맞는 입자).
2. 출처 줄에 입자를 적는다: "목표 범위 일별(발효일 기준) · 실효금리 월평균". 끝값 핀 3.63% 는 월평균 2026-08 값임을 그대로(as_of 2026-08).
3. **1bp 단차는 유지**(정직성 P6, 값을 다듬지 않는다). 사용자가 다르게 정하면 그때 규칙으로(예: 선 두께·단차 표기). 감독이 사용자에게 물었다.
4. 장치(C12): checks `[band-line-outside]` hard — 같은 레인에 band 와 step/line 이 있고 series 레코드에 `within: <band series_id>` 관계가 선언되면(FEDFUNDS → DFEDTARL/U 에 선언), 선 값이 그 날짜의 band 밖인 날이 **band 변경일 ±(월평균이면 그 달) 를 제외하고** 하루라도 있으면 실패. 규칙 키 `series.within_band_tolerance_days`. 또 `[series-date-convention]` warning — 같은 레인에 frequency 가 다른 시리즈가 있으면 출처 줄에 두 입자 문구가 있어야 한다. UF-200 guards 에 둘.
5. 골든(hormuz)은 무관. showcase_econ 프리뷰 시트의 금리 아일랜드 컷 1장(인하 달 10·12월 구간)을 R 에 — 선이 밴드 안에 있는지 눈으로.

## 3. 순서
D-0325 마감(light 골든) → 이것 → 사용자 게이트 ② 답 → final.
