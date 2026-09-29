---
id: D-0090
from: fable
to: opus
kind: directive
responds_to: []
phase: "G4"
version: v4.4.0
status: open
priority: urgent
---

# Phase G4 착수 — 첫 비지정학 영상 (v4.4.0)

정본: **docs/handoff/20 §3(프로필 확정)·§4(새 요소 절차, 최대 3)·§5.2(전망 귀속·투자 권유 금지)·§7(원고 차이)·§8(미디어)·§9(시각 검수 루브릭 7)·§10(예시 설계)·§11(주문 템플릿)·§12 G4(합격 = 두 게이트 + 루브릭 + 사용자 판정 "슬라이드가 아니라 다큐")**, 03·05·16·17, 15 P3·P4·P8·P11·P12, GOAL G3-17. 현재: TimelineStage·series·정직성 검사 18·genre_elements, macro_monetary(proposed), statement_diff(등록, 사용자 승인 대기), fed_timeline_demo. 버전 **v4.4.0**.

## 사용자 결정(§7) — Fable 이 사용자에게 물었다. 답이 오면 D 로 전달한다. 답이 없으면 아래 기본값으로 진행하고 provenance 에 "사용자 미확정" 을 남긴다
| 항목 | 기본값 |
|---|---|
| 주제 | "연방준비제도의 최근 금리 정책"(20 §10·§11 예시 주제) |
| macro_monetary status | proposed 유지(승인 전 approved 로 바꾸지 않는다) |
| 새 요소 승인(statement_diff·dot_plot) | 미승인 — 등록·스케치·프리뷰까지 하고, 최종 렌더의 provenance `elements.approval: pending` |
| 영상 판정 | Fable 1차 판정 → 사용자 최종 |

## 0. 첫 커밋
`VERSION` 4.4.0 + CHANGELOG(v4.3.0 종결). 갤러리 `event_series` 예제 레인 라벨을 레코드 라벨로(D-0089 지적 ①). `reports/phaseG4/` 시작.

## 1. 커밋 순서(한 커밋 한 의도, `v4.4.0:` prefix, 커밋 전 전체 pytest "failed 없음")
1. **장르 프롬프트 층**(P3): research·script·director·revise·visual_qa 프롬프트가 **장르 프로필 + 무대 문법을 규칙 파일에서 생성해 받는다**(`prompts/*.md` 템플릿 + `rules`·`genres/<genre>.yaml` 치환, 코드 상수 0). 시간축 문법(20 §6), 원고 차이(§7: 용어 첫 등장 정의 1문장·인과 귀속·문장당 숫자 ≤ 2), 경제 상투어 금지 목록(`rules banned_phrases` 에 §7 예 3개 추가 — 사람 승인 = 이 D), 루브릭 추가 7항목(§9)을 visual_qa 프롬프트에. 파리티 테스트(예시 출력 → 스키마) 확장. 지정학 프롬프트 산출은 **바이트 동일**(프롬프트 생성 결과 md5 before/after — 장르 geopolitics 는 추가 문단 0).
2. **데이터**: 레코드 추가 — `DFEDTARU`·`DFEDTARL`(연방기금 목표 범위 상·하한, Board of Governors, us_gov_public_domain, 일별 → 월 마지막 관측으로 `transform` 명시) → 레인 "기준금리(목표 범위)" 는 **series style `band`**(두 레코드 사이 띠, `rules stage_timeline.band`) — `primitives_planned.target_band` 는 series band 로 대체 주석. 점도표 데이터: 최근 SEP(연준 공식, federalreserve.gov, public domain) 참가자별 전망 레코드(`kind: scatter`, SeriesRecord 확장 — 연도별 값 목록, 출처 URL·retrieved_at·as_of). 성명서 원문 2건(federalreserve.gov press release, 인용은 `verification.quote_max_chars` 안).
3. **새 요소(20 §4.1 절차, 최대 3)**: ① `statement_diff` — 단어 단위 diff 로 개선(공통 접두·접미 + 중간 토큰 대조, 골든 회귀 무관, 갤러리 갱신) ② `dot_plot` 프리미티브(참가자별 전망 점, 연도 열, 중앙값 표시, "참가자별 전망이며 약속이 아님" 고정 문구 — §5.2, 출처·as_of 줄, 계약 §4.2·AXIS value·정직성 대상) — 스케치 3컷 실제 렌더 → `reports/phaseG4/dot_plot_sketch.jpg`(사용자 승인용) ③ 세 번째는 만들지 않는다(yield_curve_shift 는 chart_wall 무대가 필요 — G4 밖). `primitives: [statement_diff, dot_plot]`, planned 정리 주석.
4. **주제 영상 `projects/fed_policy_2026/`** — 주문 템플릿 §11 그대로 채워 `order.yaml` 로 저장(주제·장르·불변 층·데이터·미디어 요구). 리서치 워커(prompts/research) → 소스 인테이크(기사·공식 발표, D50 인용 대조) → 원고(ScriptWorker, §7 규칙·series 참조·게이트 ① 뷰) — **게이트 ① 원고 승인은 Opus 대행**(`confirmed_by` 명시, 실사용은 사람) → TTS → **AI 연출(DirectorWorker, 시간축 문법 프롬프트)** → checks 18 hard 0 → 시각 검수 루프(루브릭 §9 포함, 상한 규칙대로) → 게이트 ② 판정 요청(R 로: 시트·잔여 지적·루브릭 7항목 자기 평가). 미디어 비트: 기자회견 사진(권리 레지스트리 확인, 연준 공식 사진은 출처·라이선스 기록, 불확실하면 쓰지 않음), 기사 카드, 공식 계정 게시물(권리 규칙). 엔딩 카드 "투자 권유가 아닌 정보 제공 목적".
5. **보조 무대 없음**: chart_wall 은 G4 범위 밖(주 무대 timeline 하나). 성명서 변화는 statement_diff 오버레이, 시장 반응은 기사 카드·패널로. 프로필 `secondary: [chart_wall]` 는 그대로(planned).
6. **회귀**: hormuz 25/25·랫클리프 20/20·fed_timeline_demo 12컷 md5 동일(§0 기준선 = phaseG3 demo_frames), 갤러리 34(dot_plot).
7. **문서**: docs/03·09·10·12·16·17 에 장르 프롬프트·새 요소·G4 절차 단락(수치 없음), handoff 20 §4·§7·§9·§11 "구현됨(v4.4.0)" 주석, GOAL G3-17 검증 열 `pending:G4` 는 **남긴다**(사용자 판정 뒤 Fable 이 닫는다). CHANGELOG·DEVLOG.
8. **테스트 ≥ 25**: 프롬프트 생성(장르 치환·지정학 바이트 동일·파리티), band series, scatter 레코드, dot_plot 계약·정직성, statement_diff 단어 diff, order.yaml 스키마, 루브릭 프롬프트 파리티, 회귀.
9. **산출물** `reports/phaseG4/`: fed_policy 시트(선택 판 + v1~vn)·qa_loop·rubric_self_check.json·dot_plot_sketch·gallery·chart_honesty_fed_policy·hormuz_after·ratcliffe_mad·demo_after·perf·run_log·asset_md5. artifacts `artifacts/phaseG4-v4.4.0`(tts·media_src·final.mp4 480p + 1080p). **전편 mp4 는 Fable 이 사용자에게 전달한다.**

## 2. 합격 조건(20 §12 G4 + 보정)
| 조건 | 검증 |
|---|---|
| 두 게이트 | 게이트 ① 대행 기록, 게이트 ② Fable 1차 판정(R 시트) |
| 루브릭 §9 | 시각 검수 워커 출력에 7항목 판정 + Fable 육안(원본 해상도 컷, README §6.2-4) |
| 정직성·연속성 | checks 18 hard 0, 원고 린트(series 대조·상투어) 0 |
| 새 요소 절차 | 2개 등록(계약·예제·테스트·스케치), 승인 상태 provenance 기록 |
| 지정학·데모 불변 | 25/25·20/20·12/12 |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 25 |
| 사용자 판정 | 별도(Fable 전달 후). 이 조건은 Opus 합격표 밖 |

## 3. 하지 않는 것
chart_wall·flow·structure·document 무대, yield_curve_shift, 프로필 status 변경, 렌더 수치 변경, 골든·기존 예제 변경, 시장 독점 데이터, 사실 장면 AI 생성.

## 4. 보고
커밋 단위 progress, 게이트 ② 는 decision_request(시트 경로·잔여 지적·루브릭 자기 평가), 완료 시 phase_report(mp4 경로). 결정 대기면 R 을 푸시하고 턴을 끝낸다.
