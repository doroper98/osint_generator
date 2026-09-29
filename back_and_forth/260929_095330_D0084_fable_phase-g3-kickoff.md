---
id: D-0084
from: fable
to: opus
kind: directive
responds_to: []
phase: "G3"
version: v4.3.0
status: open
priority: urgent
---

# Phase G3 착수 — 시간축 무대·데이터 레코드·차트 정직성 검사 (v4.3.0)

정본: **docs/handoff/20 §2.1(시간축 캔버스)·§2.3(TimelineStage 척도·압축 물결)·§5.1(데이터 레코드)·§5.2(전망 귀속)·§5.3(차트 정직성 9규칙 = 결정적 검사)·§6(시간축 카메라 문법)·§12 G3(합격 = 공개 시리즈 2개 시간축 프리뷰 + 위반 주입 시 실패)**, 05 §2(카메라 문법 공통), 15 P3·P4·P6·P8·P10·P12, GOAL G3-17. 현재: `engine/stage.py`(Stage 프로토콜·MercatorStage·StageSet·attach_world), `registries.stages: [mercator]`·`stages_planned`, `checks` 14항목·`qa_checks.planned` 4, `genres/macro_monetary.yaml`(proposed, primary timeline), G1 에서 레이어·프레이밍·검사가 월드 좌표만 쓰도록 일반화됨. 버전 **v4.3.0**.

## 0. 첫 커밋
`VERSION` 4.3.0 + CHANGELOG(v4.2.0 종결). `reports/phaseG3/` 시작. hormuz 기준선 = phaseG1(f8e507a) 인용.

## 1. 커밋 순서(한 커밋 한 의도, `v4.3.0:` prefix)
1. **데이터 레코드** `schemas/data_models.py:SeriesRecord`(20 §5.1 YAML 그대로 + `unit`·`frequency`·`license`·`source_url`·`values: [(date, value)]`, `extra="forbid"`): 날짜 단조 증가, `as_of ≤ retrieved_at`, `unit` 는 `rules data.units: ["%", "%p", "bp", "억 달러", "지수", "명", "원"]` 안에서만, `license` 는 `rules data.licenses_allowed`(예: `us_gov_public_domain`, `cc_by_4`) 안에서만 — 아니면 로드 오류(P6). 저장 위치 `data/series/<series_id>.yaml`(레코드) + `<series_id>.csv`(값). 로더 `data/series.py`. 도구 `tools/fetch_series.py`(FRED csv `fredgraph.csv?id=`; 출처 도메인은 `rules data.sources_allowed` 안에서만, 레코드에 retrieved_at·source_url·license 기록, 값은 변형 없이·`transform` 은 명시된 것만).
2. **공개 시리즈 2개 커밋**: `FEDFUNDS`(연방기금 실효금리, 원출처 Board of Governors H.15 — 미 연방정부 저작물, `us_gov_public_domain`)·`CPIAUCSL`(CPI 도시 전체, 원출처 BLS, 같은 라이선스). 둘 다 FRED 경유, 월별, 2019-01 ~ 최신. csv 는 작다 — 저장소에 넣는다(재현). `transform`: FEDFUNDS 원자료, CPI 는 **전년 대비 %(코드 계산, transform 에 식 기록)**. 네트워크가 막히면 progress 에 사유를 적고 decision_request(픽스처 대체 여부) — 임의로 값을 만들지 않는다.
3. **TimelineStage** `engine/stage_timeline.py`(STAGE_CLASSES 등록, `registries.stages: [mercator, timeline]`, `stages_planned` 에서 timeline 제거): 월드 x = 기준일(`epoch`)로부터의 **일수**(float), y = 레인 인덱스(레인 간격 1.0). 무대 설정은 direction `stage_config.timeline: {start, end, lanes: [{id, label, kind: step|line|pins, unit}], compress: [{from, to, factor}]}`(프로필 `stage.timeline.lanes` 가 기본값, direction 이 덮음). `to_world(date=, lane=)`·`from_world`. `bounds` = [start, 0, end, n_lanes]. `render_base`: 시간 격자(연·분기·월 눈금, LOD 는 w 로), 레인 띠 + 레인 라벨(왼쪽 고정), 압축 구간은 **물결 표시 + "압축" 라벨**(20 §2.3·§5.3). `draw_labels`: 날짜 라벨 LOD(w 큰 값 = 연도 → 분기 → 월 → 일, 20 §6). `lod_rules` 는 `rules stage_timeline`(새 절, 리터럴 0: 눈금 간격 w 임계, 글자 크기 역할, 레인 높이, 물결 폭). 색·글자는 style 토큰. 카메라 문법 §6: 기본 왼쪽→오른쪽(되돌아가면 `checks` warning `timeline_backtrack` — warning, 이유 필드 있으면 통과), 먼 점프는 dip(shot_grammar 그대로).
4. **시리즈 레이어**: 새 이벤트 타입 `series`(registries.event_types 추가): `{type: series, lane, series_id, style: step|line, t0, t1, grow: true|false}` — 레코드에서 직접 그린다(20 §5.1 "데이터에서 직접"). `grow` 는 카메라 이동과 함께 왼쪽→오른쪽으로 자란다(등장 문법 05). 값 라벨은 마지막 점만(단위 포함). 핀 = 기존 `marker`(앵커 `date`·`lane`, G1 attach_world 그대로) — 새 타입 없음. 레지스트리 세 곳(스키마·렌더러·프리뷰 예제) 동시(C7). `primitives_planned` 의 `rate_step_line` 은 `series style: step` 이 대신한다 — 삭제하지 말고 주석에 "series 로 대체, G4 에서 정리" 로 남긴다(사용자 결정 전).
5. **차트 정직성 검사**(20 §5.3 표 그대로, `qa_checks.planned` 4개를 실제 검사로 옮김, checks 14 → **18항목**): `chart_honesty`(hard — 막대 0 기준선, 압축 구간 메타 ↔ 물결 표시, %/%p 혼용, 이중 축 라벨·색, 로그 척도 표기), `series_limit_3`(hard — 레인·패널당 계열 ≤ 3), `units_visible`(hard — 단위 라벨 존재), `as_of_visible`(hard — 기준 시점·출처 줄 존재). 대상 = `series` 이벤트 + 수치 축 패널(dots·gantt·dual_line·timeline). hormuz·랫클리프 hard 0(패널 대상 — 기존 패널이 걸리면 규칙 해석을 decision_request, 예제를 고치지 않는다 P8). **위반 주입 테스트 9개**(§5.3 표 한 줄에 하나) 전부 hard.
6. **시간축 실증 프로젝트** `projects/fed_timeline_demo/`: genre macro_monetary(proposed 참조 — provenance `genre.status: proposed` 기록, P6), stage timeline, 레인 3(policy_rate step·inflation line·events pins), 원고 8~10문장(내레이션은 두 시리즈의 값·날짜·as_of 만 말한다 — 해석·전망 문장 금지, 사실 = 레코드), TTS(edge-tts, 저장소 규칙), 연출은 사람 작성(Opus)으로 §6 문법(왼쪽→오른쪽, 핀 확대, 숏 ≥ 6초). 결정적 검사 18항목 hard 0·stage_continuity 0. **프리뷰 컨택트 시트 12컷 + 전편 mp4**(짧아도 된다, 참고 영상 — 합격 조건은 프리뷰). 엔딩 카드에 두 시리즈 출처 줄 + "투자 권유가 아닌 정보 제공 목적"(20 §5.2).
7. **회귀**: hormuz 25/25(f8e507a 기준선), 랫클리프 20/20, 갤러리 32+1(series 예제 추가 → 33) 전체 렌더.
8. **문서**: docs/09·10·12 에 시간축 무대·데이터 레코드·정직성 검사 단락(수치 없음), handoff 20 §2.3·§5 "구현됨(v4.3.0)" 주석, GOAL G3-17 검증 열에 `checks:chart_honesty` 추가(pending:G4 유지). CHANGELOG·DEVLOG.
9. **테스트 ≥ 25**: SeriesRecord 통과/거부(단위·라이선스·날짜·as_of), TimelineStage 프로토콜 준수·to_world 왕복·LOD·압축 물결 존재, series 레이어 grow, 정직성 위반 9, stage_continuity 시간축 합성, 골든 회귀, 갤러리.
10. **산출물** `reports/phaseG3/`: timeline_sheet.jpg(12컷), chart_honesty_{demo,hormuz,ratcliffe,synthetic}.json, series_records.json(두 레코드 요약·md5), hormuz_after·ratcliffe_mad·gallery, perf, run_log·asset_md5. artifacts `artifacts/phaseG3-v4.3.0`(demo tts·mp4).

## 2. 합격 조건(20 §12 G3 + 보정)
| 조건 | 검증 |
|---|---|
| 공개 시리즈 2개 시간축 프리뷰 | fed_timeline_demo 12컷 시트, 레코드 라이선스 public domain, provenance stage timeline·genre proposed 기록 |
| 정직성 위반 주입 시 실패 | 9 규칙 각각 hard(테스트 + synthetic json) |
| 무대 연속성 | demo stage_continuity hard 0, 카메라 왼쪽→오른쪽 |
| 지정학 불변 | hormuz 25/25, 랫클리프 20/20, checks 18항목 hard 0 |
| 레지스트리 | timeline·series 세 곳 동시, planned 정리, test_registry_complete |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 25 |

## 3. 하지 않는 것
ChartWall·Flow·Structure·Document 무대(planned 유지), dot_plot·yield_curve_shift·target_band 프리미티브(G4, 사용자 승인), macro_monetary approved 전환(사용자), 실제 주제 영상(G4), 렌더 수치 변경, 골든·기존 예제 변경, 시장 독점 데이터 사용.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report(시트·mp4 경로 — 사용자에게 전달), 결정 필요 시 decision_request. 결정 대기면 R 을 푸시하고 턴을 끝낸다 — poke 로 깨운다.
