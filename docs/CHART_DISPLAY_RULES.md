<!--
tier: 2
last_synced_with: v0.34.16
ssot_for: [chart-display-classification]
depends_on: [CLAUDE.md, orchestrator/hyperframes_compose.py, hyperframes/lib/charts]
last_review: 2026-06-06
-->

# 보고서 번들 차트 판독 규칙 — 보조차트(strip) vs 메인차트(full)

`compose-hyperframes` (orchestrator/hyperframes_compose.py) 가 agents_reviewer
`analysis_<id>.bundle.json` 을 읽어 영상을 만들 때, 각 차트(`charts[]`)가 **메인 차트**인지
**보조 차트**인지 반드시 구분해서 배치한다. 사용자 결정(v0.34.16) 으로 박은 규칙이다.

> **왜**: v0.34.15 영상이 보고서의 **보조차트(티커 스파크라인) 6종을 각각 풀스크린 메인처럼**
> 5초씩(총 30초) 할애했다. 보고서에선 작은 한 줄 묶음(ticker strip)인데 영상에서 메인 비주얼로
> 과대 표현된 것. 보조차트는 **묶어서 작게 한 컷**으로, 메인차트만 **크게 개별 컷**으로.

---

## 판단 순서 (항상 이 순서, display 가 있으면 그걸로 끝)

### 1순위 — `charts[].display` 필드를 그대로 따른다 (이게 정답)

| `display` | 의미 | 영상 배치 |
|---|---|---|
| `"full"`  | **메인 차트**. 본문에 크게 박히는 단일 시각물 | 한 컷에 하나씩, **크게(풀/하프스크린) 개별 비주얼** |
| `"strip"` | **보조 차트**. 보고서에서 작은 sparkline 한 줄(티커 스트립)로 묶이는 보조 지표 | **단독 풀스크린 금지**. 여러 개를 **"지표 묶음(티커 보드)" 한 컷**으로 작게 |

### 2순위 — `display` 가 없으면(구버전 번들) 추론

1. 같은 보고서 `analysis_<id>.json` 의 `composed_report.sections[].charts[].role` 을
   **같은 순서로** 본다. `role == "compact"` → 보조(strip), 그 외/없음 → 메인(full).
   (※ 현재 컨버터는 bundle.json 만 받으므로 이 단계는 해당 JSON 이 함께 주어질 때만.)
2. 그것도 없으면 **type 휴리스틱**:
   - `line` / `area` 가 **같은 섹션에 2개 이상 연속**으로 묶여 있으면 → 보조(strip)
   - 그 외 모든 경우 → 메인(full)
   - **`candle` 은 strip 후보가 아니다(v0.34.17 보정)**. candle 은 sparkline 이 아니라 상세
     OHLC 단일 종목 차트이므로 **기본 메인(full)**. (사용자 피드백: 엔비디아 candle 을 티커
     스파크라인으로 축소한 건 잘못 — 최소한 그 정도는 메인이어야 한다.) display 가 strip 이면
     그때만 보조.

### type 별 기본 성격 (참고 — 단, display 가 우선)

- **거의 항상 메인(full)**: bar, donut, stacked, stacked_bar, bubble, heatmap, gantt, network,
  dual_line, forecast, choropleth, scatter, stacked_area, lollipop, slope, small_multiples,
  waterfall, range_bar, sankey
- **보조(strip)로 묶이는 후보 (시장 시계열)**: line, candle, area
  ← **단, `display=="strip"` 일 때만 보조. 단독으로 쓰이면 메인.**

---

## 절대 규칙

- **type 만 보고 메인/보조를 단정하지 마라.** line 한 개가 메인일 수도 있다.
- 판단 순서는 항상 **display → role → type 휴리스틱**. display 가 있으면 그걸로 끝.
- **"strip" 차트를 풀스크린 메인 비주얼로 키우지 마라** (보조 지표 묶음으로만).
- **지도는 `charts[]` 가 아니라 별도 `map` 객체**에 있다 (차트로 세지 마라).
- **모든 차트(메인·티커보드)는 footer 에 출처·기간·시작~끝을 표기한다** (아래 메타데이터 규칙).
- **같은 종목 중복 금지(dedupe)**: 같은 섹션에서 메인으로 이미 그린 종목명은 티커보드에서 제외
  (예: NVDA candle 이 메인이면 NVDA line 은 보드에 또 넣지 않는다).

---

## 메타데이터 표기 규칙 (필수)

차트의 신뢰성은 출처·기간이 보여야 성립한다. 모든 차트 컴포넌트는 **footer 한 줄**에 다음을
번들에서 뽑아 표기한다 (없으면 해당 항목만 생략):

| 항목 | 출처(번들) | 예 |
|---|---|---|
| 출처 | `chart.provenance.sources[0].provider` (+ `code`) | `출처 · YAHOO (NVDA)` |
| 기간(시작~끝) | `chart.data[].date`(candle) / `.x`(line) 의 첫·끝 | `2026-03-05 ~ 2026-06-05` |
| 인터벌 | 날짜 간격 추론(일/주/월봉) | `일봉` |
| 단위 | `provenance.sources[0].unit` | `$` (축에 이미 표기 시 생략 가능) |

티커보드는 묶인 지표들의 **공통 출처·기간**을 보드 footer 에 한 번 표기한다.

---

## 인터벌(해상도) 규칙 — 영상 차트는 더 촘촘하게

보고서의 보조차트가 예컨대 **1년 기간 · 주별 종가**로 그려져 있더라도, 영상에 나오는 차트는
화면에서 더 크게 보이므로 **가능한 한 더 촘촘한 인터벌(예: 일별 종가)** 로 반영되어야 한다.

- **원칙**: 영상 차트는 번들이 제공하는 **최대 해상도 데이터를 그대로** 쓴다. strip 의 sparse
  한 인터벌은 *보고서의 작은 크기용*이지 영상의 제약이 아니다. 다운샘플 금지.
- **현 구현**: 컨버터는 `chart.data` 를 손실 없이 사용한다. agents_reviewer 실 번들은 이미
  일별 데이터를 싣는다(예: NVDA 64 일봉). 번들이 sparse(주별)만 줄 경우 더 촘촘한 데이터를
  새로 받아오는 것은 데이터 소스 연동이 필요한 **후속 과제**(현재는 번들 해상도를 따른다).

---

## 구현 매핑 (v0.34.16)

| 분류 | 영상 씬 |
|---|---|
| full 메인 차트 | `lib/charts/<type>.html` 개별 풀스크린 chart 씬 (candle/line/bar/donut). 미지원 type 은 prerendered_svg 폴백 또는 텍스트. |
| strip 보조 차트(섹션 내 연속 묶음) | `lib/charts/tickerboard.html` **한 컷** — 미니 스파크라인 그리드(티커명 + 종가 + 등락% + sparkline). candle 은 종가선으로 축약. |

`orchestrator/hyperframes_compose.py:_classify_display()` 가 본 규칙을 코드로 구현한다.
