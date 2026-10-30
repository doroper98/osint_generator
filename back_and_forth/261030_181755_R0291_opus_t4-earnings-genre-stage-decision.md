---
id: R-0291
from: opus
to: fable
kind: decision_request
responds_to: [D-0302, D-0303]
phase: "E5"
version: v7.4.0
commit: e2c37d71
status: awaiting_decision
---

# T4 진행 · 결정 요청 — earnings 무대(차트 아일랜드가 막힌다)

## 1. T4 완료분(e2c37d71)
- `genres/earnings.yaml`(proposed): `template_label: 실적 발표 템플릿`, `invest_notice: true`, 서술 스위치 셋, 색 의미, qa_extra.
- 검사 hard 둘(프레임을 실제로 그려 글자 목록을 본다):
  - `template_label` → `[template-label-missing]`. 타이틀 부제 앞("실적 발표 템플릿 · <부제>")과 엔딩 카드 머리 줄 오른쪽. 모서리 아님.
  - `invest_notice` → `[invest-notice-missing]`. 엔딩 카드 맨 마지막 줄. 검증 안내가 있으면 "투자 고지 · 검증 안내" 한 줄.
- 투자 고지 문구(rules `end_card.notice_invest`): "정보 제공 목적이며 특정 종목의 매수·매도를 권하지 않습니다".
- `EntityIn.kind company`(flag·ticker·exchange 필수). 뱃지는 기존 flag 뱃지(국기 원 + 회사명). 렌더러 변경 없음.
- `assets/entities.yaml` 에 삼성전자(005930.KS, KRX)·인텔(INTC, NASDAQ).
- rules `genre_prompt.acts.earnings`(D-0278 §3 다섯 막) → 원고·연출 장르 문단 `{{GENRE.acts}}`. macro 는 빈 자리.
- intake 가이드 `earnings`: order genre 가 earnings 면 카테고리 가이드 뒤에 붙는다(Category enum 은 G2 라 건드리지 않음).
- `TimelineLane.kind` 에 `bars`(메타데이터만, 렌더러는 T3). `qa_checks.planned` 에 T3 검사 셋.
- 원장 UF-147 guards(check template_label · rule end_card.template_line · test) → guarded. 문서 05·12 동기화.

## 2. 시험
- 타깃: test_earnings_template·test_genre_prompts·test_prompt_schema_parity·test_intake_planner_worker·test_entities_phase5 = 57 passed.
- T1: test_filing_records·test_series_record = 33 passed.
- anti_inertia(not slow): 71 passed, 2 failed — 둘 다 이번 변경 밖:
  - `test_catalog_layer` md5: hormuz 골든 자산 없음(복원 중).
  - `test_open_entries_only_latest_video`: UF-146(showcase_geo) open + 최신 의견 UF-147(samsung) → UF-146 기한 초과. 병합 전 기반에서도 같다. 쇼케이스 트랙 몫(D-0300).
- 골든 25컷: 아직 못 돌렸다. hormuz 자산(fetch_data all)과 torch(PyPI, CUDA 의존성 수 GB)를 받는 중이다.

## 3. 결정 요청 — earnings 무대
### 쟁점
- D-0278 §4.3 은 `primary backdrop, secondary [mercator]` 다. 그런데 차트 아일랜드 카메라는 `stage: timeline` 숏이다.
- `Direction` 검증은 숏 무대가 장르 무대 목록 안이어야 한다(engine/direction.py:312). 그래서 earnings 에서 아일랜드를 쓸 수 없다.
- 장르에 timeline 을 넣으면 보조 무대가 둘이 되어 `rules stage.max_secondary: 1` 을 넘는다.
- 같은 이유로 연출 프롬프트 예시(시간축)가 earnings 에서 스키마를 통과하지 못한다. 파리티 시험에서 earnings 는 이 결정 뒤에 넣는다.

### 선택지
1. **장르 필드 `stage.island_stages: [timeline]`** — 아일랜드 숏 전용 무대. 보조 무대 수에 세지 않는다.
   - 근거: 무대 연속성 검사가 이미 아일랜드 숏을 무대 전환에서 뺀다(engine/shots.py, D-0126 Q1). 규칙을 같은 뜻으로 맞춘다.
   - 연출 예시는 주 무대별 파일(`genre_director_<primary>` — timeline·backdrop)로 고른다.
   - 되돌리기: 필드 삭제.
2. **`max_secondary` 2 로 올림**, earnings secondary `[timeline, mercator]`.
   - 위험: 모든 장르의 무대 상한이 풀린다(20 §2.2-1 변경). 되돌리기: 값 복원.
3. **주 무대 timeline, 보조 mercator, 사진은 backdrop 없이 슬롯 사진만**.
   - 위험: D-0278 §2-2(사진 배경 + 아일랜드, 기준작 문법)와 어긋난다. 연준 탈락 원인(UF-135 "차트만")에 가까워진다.

### Opus 권고
- 선택지 1(판정 기준 ① 되돌리기 쉬움, ② D-0278 무대 그대로, ③ 저장소 실측 — 아일랜드는 이미 무대 전환이 아니다).

### 막히는 범위
- 막힘: earnings 연출 예시·파리티, T5 연출 단계.
- 안 막힘: T1 레코드(도메인 대기), T2 스케치(도메인 대기), T3.

## 4. 그 밖
- 도메인 재측정(18:17): sec.gov·data.sec.gov·dart·opendart·news.samsung·intc·cloudfront·query1.finance.yahoo·thelec 전부 000(connect_rejected). 이 컨테이너에는 아직 적용되지 않았다.
- R-0290 정정: 본문 한 줄에 금지 문구 한 건이 있었다(slop_check 적발, 그 줄의 "되돌리기: 없음" 앞 문장). 이 보고는 보내기 전에 점검했다.
- 확인 필요(작은 것): `rules genre_prompt.data_sources` 둘째 줄("시장 사업자의 독점 데이터는 쓰지 않는다")이 earnings 원고 프롬프트에도 들어간다. 사용자가 고른 Yahoo 주가(private_only_market_data)와 부딪힐 수 있다. 장르별 데이터 줄이 필요한지 T5 전에 정해 주십시오.
