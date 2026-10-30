---
id: D-0278
from: fable
to: opus
kind: plan
responds_to: []
phase: "E7"
version: v7.4.0
status: open
priority: normal
---

# 계획 — E7 기업 실적 발표(earnings) 영상 템플릿: 첫 사례 삼성전자·인텔 Q3 2026

감독(Fable) 작성 2026-10-30. **착수 순서는 §9** — D-0277(preview_v10)·geo 콘티 판 v2 가 먼저다. 이 문서는 E7 의 정본이고, D-0251 §2 표에 E7 행을 추가한다.

## §0 사용자 요청(원문, 2026-10-30) → DECISIONS D274
> "기업 실적 발표에 대한 영상 템플릿도 만들어봐. 일단 최근에 발표한 삼성전자와 인텔을 갖고 만들어보자. 실적 예상치와 실제 실적발표 결과, 그리고 가이던스와 주가 반응, 그리고 이를 둘러싼 지경학적 관계등을 아우르는 그런 템플릿을 만들면 좋겠는데."

요구 요소 다섯: **① 예상치(컨센서스) ② 실제 발표 ③ 가이던스 ④ 주가 반응 ⑤ 지경학 맥락.** 이 다섯이 템플릿의 고정 막(act) 이 된다(§3).

## §1 사실 묶음 — 감독 웹 수집(2026-10-30, 2차 보도 중심 · **1차 출처 대조 필수**)
감독 컨테이너는 news.samsung.com·dart.fss.or.kr·intc.com·sec.gov·yahoo·stooq 가 프록시 차단(curl 000)이라 **1차 문서를 직접 읽지 못했다**. 아래 수치는 intake 초안이지 claims 가 아니다 — 검증 단계(verify_sources)가 1차 출처(§6 도메인)로 대조한 뒤에만 원고에 들어간다(G4). 출처가 엇갈리는 칸은 ⚠ 로 표시.

### 1.1 삼성전자(005930.KS) — 2026년 3분기
| 항목 | 값 | 출처(2차) | 1차 대조처 |
|---|---|---|---|
| 잠정 실적 발표 | 10월 8일 — 영업이익 107.4조, 매출 195조 | CNBC 10/08, news.samsung.com 잠정실적 | news.samsung.com/kr 잠정실적 · DART 잠정 공시 |
| 잠정 전 컨센서스 | 영업이익 106.1조(LSEG) ⚠ 글로벌이코노믹은 105.8조 | TradingKey·글로벌이코노믹 | 로이터/연합인포맥스 보도 원문(press_cited) |
| 확정 실적 발표 | 10월 29일 — 매출 195.3조, 영업이익 107.4조(분기 사상 최대, 전년 12.17조 대비 ≈8.8배) | news.samsung.com 실적 발표 · 내외일보 | DART 분기보고서(11월)·IR 발표 PDF `images.samsung.com/kdp/ir/events/2026/2026_3Q_conference_kor.pdf` |
| 부문 | DS 매출 147.1조·영업이익 106.5조(전사의 99 %) · DX 영업이익 0.8조 ⚠(KuCoin 은 "DX 영업손실 0.8조" — 부호 확인) · 매출 52.1조 | news.samsung.com · 경향 | IR PDF |
| 순이익 | 75.1조 — 컨센서스 미달 ⚠ | Yahoo | IR PDF |
| 가이던스(정성) | 4분기 반도체 중심 성장 · 2027 HBM 공급 완판 · DRAM 비트 출하 10 % 중후반 ↑ · HBM4 매출 전분기 3배↑, HBM 매출 중 60 % | 디일렉 컨콜 전문 · IR | 컨콜 전문(thelec) · IR PDF |
| 주주환원 | 3분기 배당 주당 4,601원(총 30조) · 2026년 총 90~110조, 잔여 55~75조 집행은 내년 1월 확정 | 내외일보 · SBS | DART 배당 공시 |
| 주가 반응 | 10/08 장중 −0.7 % · 10/29 **종가 232,000원 −4.13 %**(장중 고가 249,000 ⚠ 장중 +1.45 % 보도도 있음 → 일중 반전) · 코스피 5,937.66(6000 반납) | 한국일보·네이트 마감시황·fxstreet | KRX 일별 시세 |
| 하락 이유(보도) | 추가 자사주 매입·소각 부재, 환원 집행 1월로 연기, 기관 순매도 ⚠(외국인 방향 엇갈림: 순매도 3,077억 vs 순매수 681억) | 한국일보·뉴스핌 | KRX 투자자별 매매 |
| 환율 | "환율 하락(원화 강세) 영향으로 전사 영업이익 전분기 대비 약 10조 감소" ⚠(내외일보 한 곳) | 내외일보 | 컨콜 전문 |

### 1.2 인텔(INTC) — 2026년 3분기(10월 29일 장 마감 뒤)
| 항목 | 값 | 출처(2차) | 1차 대조처 |
|---|---|---|---|
| 실제 | 매출 165억 달러(+21 % y/y) · non-GAAP EPS 0.52 · GAAP EPS 0.60 · GAAP GM 43.0 % / non-GAAP 44.1 % | 8-K Ex.99.1 · intc.com 보도자료 | sec.gov 8-K(accession 0000050863-26-000188) · intc.com |
| 컨센서스 | EPS 0.41(0.4059) · 매출 ≈165억(16.48~16.54 ⚠ 출처별) | Investing.com·MarketBeat | 로이터(LSEG) 보도 원문 |
| 부문 | DCAI 73억(+78 %) · CCG 81억(전분기 −9 %, 메모리 부족·IT 예산) · Intel Foundry 67억(+58 % y/y ⚠ 전분기 +16 %, 영업손실 19억, 외부 고객 매출 4.11억) | 보도자료·GuruFocus | 8-K |
| 가이던스 | 4분기 매출 **150~160억**, non-GAAP EPS **0.25** vs 컨센서스 170.8억 / 0.43 · PC 둔화 내년 상반기까지 · 4분기 CCG −25 % y/y | 8-K · CNBC | 8-K |
| 이스라엘 Fab 28(키르얏갓) | 폭발 사고(2명 사망·1명 중상) → 2주 가동 중단, 4분기 매출 −3억 달러·GM −200bp, 1분기까지 합계 ≈6억 | Calcalist·로이터(지역지 전재)·Notebookcheck | 8-K/컨콜 전문 |
| 주가 반응 | 10/29 시간외 **−14 %~−23 % ⚠(시각별 상이: 로이터 −14→−18→−21, CNBC −21, KuCoin −23.04 % $70.86)** · 발표 전 YTD +150 %, 10월 −23 % | CNBC·로이터·TradingKey | **10/30 정규장 종가(아직 없음)** — stooq/Yahoo 일별 |
| 경영진 발언 | 탄 CEO "Our Q3 results demonstrate improving execution…" · 진스너 CFO "PC slowdown continuing at least through the first half of next year" | 보도자료·CNBC | intc.com·컨콜 전문 |

### 1.3 지경학 맥락(두 편을 잇는 고리 포함)
- **고리**: 삼성의 메모리 호황(DRAM ASP +20 %, HBM4 완판)이 곧 인텔 CCG 의 역풍("memory shortages" 로 PC 출하 둔화). 한 편의 호재가 다른 편의 악재 — 템플릿 §3 act5 의 핵심 장면.
- 삼성: 미·한 무역합의(2025-07 틀 → 2025-11 세부: 15 % 관세, 반도체 232조는 "타국 이상으로 불리하지 않게" 조항) · 반도체 232조 관세 25 %(2026-01-15 발효 ⚠ 2차 블로그) · 중국 시안·쑤저우 VEU 취소(2025-08/09) → 2026년 연간 허가 · 시안 = 낸드 40 % · 테일러 170억 달러 · 원화 강세.
- 인텔: 미 정부 9.9 % 지분(89억 달러, CHIPS 전환, 2025-08) + 워런트 5 % · 엔비디아 50억 달러(≈4 %) · 14A 고객 미확정(PDK 10월) · 이스라엘 Fab 28 · PC 수요·메모리 부족.
- 공용 초상 보유: trump·bessent·jensen_huang·musk·chey_tae_won·lee_jae_myung. **없음**: 립부 탄, 데이비드 진스너, 삼성 대표(전영현·노태문) — Commons 검색 뒤 없으면 회사명 배지로.

## §2 설계 원칙(C0 그대로)
1. **차트는 하나의 연속 세계**(C0·chart_world): 분기 실적과 주가는 **같은 시간축** 위 두 레인(w 고정, 날짜 이동만). 예상치·실제·가이던스는 **같은 레인·같은 축척** 위의 표식이다 — 독립 차트·게이지·도넛 금지.
2. 기준작 『경유의 길』 문법: 사진·클립 배경 + 차트 아일랜드 하나(A1, D-0272), 사건마다 카메라 이동, 핀은 값 선 위, 영상 소스(발표·인터뷰·공장) 액자(clip_frame main, 원음). 지경학 막은 **mercator 무대**로 간다(보조 무대 1).
3. 숫자는 코드가 그린다: 예상 대비 차이(%)·전년 대비·가이던스 중앙값은 레코드에서 **코드 계산**(P8). LLM 은 문장만 쓴다.
4. 정확성: 컨센서스는 **집계기관+보도 귀속**(press_cited, "LSEG 집계·로이터 보도"), 실적은 **공시(filing)** 귀속, 주가 반응은 **창 명시**(시간외 / 종가) — 출처가 엇갈린 수치는 양쪽 다 적거나 쓰지 않는다. 투자 권유 금지, 엔딩 투자 고지 줄 hard.

## §3 템플릿 막 구성(고정 막 — order.yaml instructions 로 강제, 장르 프로필 `earnings`)
| 막 | 내용 | 무대·요소 | 길이 제안 |
|---|---|---|---|
| cold | 발표 당일 한 컷의 모순("사상 최대인데 −4 %" / "예상 넘었는데 시간외 −20 %") | backdrop(현장 사진) + 주가 레인 핀 | 8~12초 |
| TITLE | | | |
| act1 예상 vs 실제 | 분기 레인에서 그 분기 막대가 0에서 자라고, 예상 표식(빈 점+짧은 가로선)과 만난다 → 차이 라벨(코드) | island chart · series bars+estimate · marker | 25~35초 |
| act2 어디서 나왔나 | 부문 분해(DS/DX · DCAI/CCG/Foundry): 같은 막대가 **쌓임(stacked)** 으로 갈라진다 · 경영진 발언 quote · IR 자료 article | series bars stacked · quote · article | 25~35초 |
| act3 가이던스 | 다음 분기 열에 회사 가이던스 범위(띠)·컨센서스 표식 · 정성 가이던스는 quote | series band(projection 색) · estimate · quote | 20~30초 |
| act4 주가 반응 | 주가 레인으로 pan: 발표 전 추세 → 발표일 핀 → 시간외/종가 반응 라벨(창 명시) · "왜" 기사 카드 | series line · marker · article · photo | 20~30초 |
| act5 지경학 | mercator: 공급망·정책 지도(관세·수출통제·정부 지분·공장·사고) · 다른 회사와의 고리(삼성↔인텔) | mercator · route · marker · badge · photo/clip | 30~45초 |
| ending | 한 문장 정리 + 엔딩 카드(출처·권리·**투자 고지**) | | 10초 |
한 편 2.5~3.5분(사용자 결정 ③, §8).

## §4 새 요소·데이터 계약(E3·E4·E5 를 E7 이 끌어당긴다 — 20 §4.1 절차: 제안 → 실제 렌더 스케치 → 사용자 승인 → 등록)
### 4.1 series 스타일 추가(`engine/events.py SeriesEvent.style`, 렌더러 `engine/layers/series.py`, 규칙 `stage_timeline.series.bars`)
- `bars`: 분기 레코드(frequency quarterly) → 분기 열마다 **0에서** 자라는 막대(막대 폭 = 분기 폭 × `bar_w_ratio` 제안 0.55). 옵션 `stack: [SERIES_A, SERIES_B…]`(부문 레코드 — 합이 전사 레코드와 ±0.5 % 안에 맞지 않으면 오류, P6). 검사 **[bars-from-zero]** hard(레인 축 하한 0 강제 — lane_range fit 예외: bars 레인은 min 0).
- `estimate`: 컨센서스 레코드(press_cited, 분기 날짜) → 분기 열에 빈 점 + 짧은 가로선 + 라벨 "예상". 같은 열의 `bars` 실제값과 쌍 → 코드가 차이 %(`(실제/예상 − 1)×100`, 소수 1자리) 를 핀 라벨로. 검사 **[estimate-actual-pair]** hard(발표 분기에 실제만 있고 예상이 없으면 오류 — "예상치 없음" 을 레코드 `missing` 으로 적으면 통과).
- 가이던스 범위 = 기존 `band`(lower·upper 레코드, 미래 분기 한 열) + 색 `forecast`(amber) — 새 스타일 아님. 정성 가이던스 = quote.
- 주가 = 기존 `line`(frequency `daily`) + marker 핀(발표일) + 반응 라벨(코드: `(종가/전일 종가 − 1)` 또는 press_cited 시간외 값 — 라벨에 창 이름 **"시간외"/"종가"** 를 코드가 붙인다. 검사 **[price-window-label]** hard).
- 스케치(20 §4.1 ②): 실제 엔진으로 3컷 — ① bars+estimate ② stacked ③ band 가이던스 + 주가 레인. 목업 금지. 사용자 승인 뒤 등록(등록 커밋 = 레지스트리·스키마·렌더러·프리뷰 예제·테스트 한 번에).
### 4.2 데이터 계약(`schemas/data_models.py`·`rules data`)
- `frequencies` += `quarterly`(값 날짜 = 분기 **마지막 날**, 막대 중심 = 분기 중앙), `daily`(거래일, 빈 날 = 휴장 — missing 아님).
- `units` += `조 원`, `십억 달러`, `달러`(EPS), `억 달러` 는 있음.
- `source_kind` += `filing`(E3): 값마다 `filing {form, accession_or_rcept_no, filed_on, item, locator, url}`; `transform.op filing: "공시 표의 값 그대로(단위 환산만: 백만 달러→십억 달러, 억 원→조 원 소수 1자리)"`; 라이선스 `public_filing`(E3 ⑤ 이름 — **감독 결정: `public_filing`**, license_note 에 "공개 공시 기록(DART/EDGAR) — 사실 데이터, 저작권 대상 아님" 원문 메모). `sources_allowed` += `dart.fss.or.kr`, `opendart.fss.or.kr`, `www.sec.gov`, `news.samsung.com`, `images.samsung.com`, `www.intc.com`, `d1io3yog0oux5.cloudfront.net`.
- 컨센서스 = `press_cited`(기존) — outlet "로이터(LSEG 집계)" 등, 값마다 url.
- 주가 = `source_kind fetched`, 출처 **Yahoo chart API(`query1.finance.yahoo.com/v8/finance/chart/<ticker>`)**: 키 없음·JSON·KRX(005930.KS)·나스닥(INTC) 둘 다. 라이선스 `private_only_market_data`(licenses_allowed 추가, D264 비공개 시청 — license_note 에 Yahoo 약관 재배포 제한 메모). 대안(사용자 결정 ②): stooq.com CSV, KRX 정보데이터시스템. **시간외 값은 fetched 가 아니라 press_cited**(API 가 안 준다).
- `tools/fetch_series.py`(또는 새 `tools/fetch_filing.py`): EDGAR 8-K Ex.99.1 표 → pandas.read_html, DART 는 OpenDART API(키 `.env`, C9)로 분기 보고서 재무제표 또는 잠정실적 공시 본문 표. 받은 원문은 `data/series/raw/` md5 기록.
### 4.3 장르 프로필 `genres/earnings.yaml`(E5 corporate 를 earnings 로 구체화, status proposed)
- stage primary backdrop, secondary [mercator] — **mercator 보조 무대 전환 1회**(act5). timeline lanes: `{id: results, label: 분기 실적, kind: bars, unit: 조 원|십억 달러}`, `{id: price, label: 주가, kind: line, unit: 원|달러}` → `TimelineLane.kind` 에 `bars` 추가(genre_models).
- color_semantics: beat `green`, miss `ru`, actual `gold`, estimate `muted`, guidance `forecast(amber)`, segment 색 3개(accents 토큰만).
- narration: define_terms_once, attribute_causality, numbers_per_sentence_max 2, forecast_attribution, **company_metric_attribution**(비GAAP·회사 산정 지표는 "회사 기준" 귀속)·**consensus_attribution**(집계기관+보도)·**price_window_attribution**(시간외/종가) — `GenreNarration` 에 bool 셋 추가 + `rules genre_prompt.narration` 문장.
- media preferred: [official_photo, press_video, ir_document, article]; qa_extra: [chart_honesty, bars_from_zero, estimate_actual_pair, price_window_label, invest_notice_missing, units_visible, as_of_visible].
- `EntityIn.kind` += `company`(name·ticker·exchange, 배지 = 코드 조판 회사명 + 국기 원; 로고는 private_only 권리 기록 시만 — D264). `[invest-notice-missing]` hard(엔딩 카드 마지막 줄 고정 문구 `rules end_card.notice_invest`).
- `prompts/intake_planner_category_guidance.yaml` 에 `earnings` 항목(잠정·확정 공시, 컨센서스 보도, 가이던스, 주가 창, 부문, 지경학 연결). `prompts/script_*.md` 는 규칙에서 생성(P3) — 템플릿 막 §3 을 `rules genre_prompt.earnings.acts` 로.

## §5 미디어·권리(D264: 기록만, 막지 않는다)
- 영상: 삼성 IR 컨퍼런스콜(음성) · 인텔 실적 웹캐스트(intc.com, 음성+슬라이드) → 발언 구간 `clip_frame main` 원음(UF-141) — 영상이 없으면 **quote + 현장 사진** 으로. 뉴스 영상(CNBC·YTN 등)은 사용자 PC 다운로드 경로(D-0275 선례).
- 사진: 삼성 뉴스룸 보도자료 사진(평택·테일러·HBM4)·인텔 뉴스룸 프레스킷(Fab 28·오하이오·립부 탄) — "editorial use" → `rights_status restricted + scope private_only`. Commons PD/CC 우선(`media_fetch search`).
- 기사 카드: CNBC(인텔 −21 %), 로이터(Fab 28), 한국일보(6000 반납), 경향 영문(30조 배당) — 등재 절차 그대로(article_register).

## §6 환경 — 사용자에게 허용 요청할 도메인(감독·구현 컨테이너 공통)
`news.samsung.com` `images.samsung.com` `www.samsung.com` `dart.fss.or.kr` `opendart.fss.or.kr` `www.intc.com` `d1io3yog0oux5.cloudfront.net` `www.sec.gov` `query1.finance.yahoo.com` `query2.finance.yahoo.com` (`stooq.com` `data.krx.co.kr` 은 대안) `www.thelec.kr`(컨콜 전문). 허용 전까지는 1차 대조 불가 → claims 가 `unverified` 로 남아 원고에 못 들어간다(G4).

## §7 공정(W0 그대로, 프로젝트 둘)
`projects/samsung_q3_2026`, `projects/intel_q3_2026` — order.yaml `genre: earnings`, `tempo: breath`, data.series 목록(§4.2 레코드 id: `SSNLF_REV_Q`·`SSNLF_OP_Q`·`SSNLF_OP_Q_EST`·`SSNLF_SEG_DS_Q`·`SSNLF_SEG_DX_Q`·`SSNLF_PX_D` / `INTC_REV_Q`·`INTC_EPS_Q`·`INTC_EPS_Q_EST`·`INTC_SEG_*_Q`·`INTC_GUIDE_REV_LO`·`INTC_GUIDE_REV_HI`·`INTC_PX_D`), instructions = §3 막 + §2 원칙. 공정: intake → research → verify → script → **게이트 ①(사용자)** → plan(표준 음성) → media → direction → audio.mix → **콘티 판(사용자 흐름 검토)** → 프리뷰 → **게이트 ②** → final + catalog. 두 편 공통 엔딩 컷(고리: 삼성 메모리 → 인텔 PC)은 선택(사용자 결정 ④).

## §8 사용자 결정 대기(README §7 — 감독이 대신 정하지 않는다)
① §6 도메인 허용 ② 주가 데이터 출처(기본 제안 Yahoo chart API) ③ 길이(제안 한 편 2.5~3.5분) ④ 두 편 따로 + 공통 고리 컷(제안) vs 한 편 비교 ⑤ 새 요소 `bars`·`estimate` 승인 — **실제 렌더 스케치 3컷을 보고** ⑥ 인텔 10/30 종가는 장 마감 뒤 채운다(act4 라벨 창 결정).

## §9 착수 순서·단계(각 단계 R 보고, 변경마다 타깃 테스트 + anti_inertia + 골든 25컷)
0. **선행**: D-0277 preview_v10 → geo 콘티 판 v2 → (게이트 ① 재승인 오면) econ 콘티 판 v3. E7 은 **사용자 승인 대기 시간에 끼워 넣는다**.
1. **E7-S1 데이터 계약**(§4.2): rules data(frequencies·units·licenses·sources_allowed·transforms filing) · SeriesRecord filing 분기 · fetch_filing(EDGAR 8-K 표 + OpenDART) · Yahoo chart fetch · 두 회사 레코드 12개 + raw md5. 도메인 미허용이면 `press_cited` 로 먼저 만들고 filing 은 허용 뒤 교체(기록에 남김).
2. **E7-S2 새 요소 스케치**(§4.1): bars·estimate·stacked·band 가이던스 실제 렌더 3컷(삼성 레코드) → artifacts → 사용자 승인 요청(감독 경유).
3. **E7-S3 등록**(승인 뒤 한 커밋): registries·SeriesEvent.style·렌더러·프리뷰 예제·검사 3개([bars-from-zero]·[estimate-actual-pair]·[price-window-label])·테스트.
4. **E7-S4 장르·엔티티**(§4.3): genres/earnings.yaml · EntityIn company · [invest-notice-missing] · genre_prompt earnings acts · intake 가이드 · prompts 재생성 + 파리티 테스트(P4).
5. **E7-S5 프로젝트 둘 W0**: intake→verify→script → 게이트 ① … (§7). 삼성 먼저(한국어 1차 자료, 사용자 검토 용이), 인텔 둘째.
6. **E7-S6 카탈로그 갱신**: showcase_econ 카탈로그 표에 새 요소 추가(P12 — 영상으로 증명).

## §10 하지 않는 것
- 게이지·도넛·의사결정 매트릭스(C0 "보고서 화면") · 독립 차트 번갈아 띄우기(UF-135) · 주가 예측·목표주가 단정 · 컨센서스 수치 지어내기(출처 없으면 "예상치 없음" 기록) · 로고 무단 사용(권리 기록 없이) · 아직 열리지 않은 종가 쓰기.
