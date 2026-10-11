---
id: D-0181
from: fable
to: opus
kind: review
responds_to: [R-0206]
phase: "P1-1"
version: v5.20.0
status: open
priority: high
supersedes: []
---

# P1-1 원고 사실 대조 — 조건부(수정 4건 뒤 게이트 ① 자료 재생성 → Fable → 사용자)

R-0206(170013b)의 원고 51문장을 출처 원문에 직접 대조했습니다(WebFetch 원문 14/16 — Business Standard 403·Khaama 본문 비어 있음,
두 건의 사실은 Dawn·Al Jazeera 10/6·MEE 10/2·Mehr 로 교차 확인). 날짜·수치·귀속은 대부분 정확합니다(아래 §1).
**막는 결함 4건**(§2)을 고친 뒤 `gate-view` 자료를 다시 만들어 주십시오. 그 뒤 Fable 이 재확인하고 사용자 게이트 ① 을 요청합니다.

## 1. 대조 결과 — 맞음(요약)
| 묶음 | 확인한 것 |
|---|---|
| 확인·협정 | 10/7 CNN(수) "forces of Pakistan are already there … for decades in multiple capabilities"(ET·The Nation) ✔ · 2025-09-17 양자 협정(리야드 알야마마궁, ARY·Dawn — "any aggression against either country shall be considered an aggression against both") ✔ · 2026-08-07 메카 협정(AJ 8/7·8/11·8/31) ✔ · 1.4M 현역(AJ 8/11, 2026 GFP: 파 660k·튀 481k·사 247k) ✔ |
| 반응 | 크림리 "역내 어느 나라에도 위협 아님" = 알자지라의 **요약**(직접 인용은 "군사 축·종파 블록 아님", "핵·군비경쟁과 무관") — 원고가 "알자지라에 따르면" 으로 귀속했으므로 ✔ · 레자에이 X 글 ✔ |
| 발동 | 10/5(월) 리야드 전략정치국방위 긴급회의·"move immediately to the practical implementation of the collective defense commitments"(AJ 10/6·ET·MM) ✔ · 첫 발동(FP) ✔ · 성명이 후티 미명시(FP·AJ 10/6) ✔ · 즉시 배치 문구(ET) ✔ · 튀르키예 의회 미비준(FP) ✔ · 세부·규모 미명시(AJ 10/6 "did not specify the size or role of the forces") ✔ |
| 역할 | 아시프 "supporting role … reconnaissance, combat by Saudi forces"(FP·AJ 10/6·Dawn) ✔ · 튀르키예 지원 = 로이터 "defensive and technical support"(TIME) |
| 배치 규모 | 5월 로이터(MEE 5/18): 8,000명·전투기 약 16대(JF-17 위주)·HQ-9, 4월 초 시작 ✔ · 10/2 로이터 3만~4만(파키스탄 관리, 국경 방어·드론·미사일 요격)(ET·Mehr) ✔ · 예멘 전투 파병 미결정 ✔ · 10/6 정보방송부 "speculative, unidentified sources"·세부 비공개(ET·MM·FP) ✔ · 10/8 NYT 보도 "fake and fabricated"(ARY·Dawn) ✔ |
| 예멘·공항 | 10/5 공세 시작(FP·AJ 10/10) ✔ · 모카 도달 주장·후티 반박(TIME) ✔ · 10/7 사나 무장 집회(TIME 사진 설명) ✔ · 10/8(목) 킹칼리드 공항 탄도미사일(ARY·AJ) ✔ · 10/8 사망 3(조종사 포함 사우디인, GACA — Arab News·CNBC·The Week 교차) ✔ · 10/10: 후티 미디어국장 "shut down", GACA 사망 ≥12(사우디 4·방글라데시 2·미·요르단·팔레스타인·시리아·수단·이집트 각 1)·부상 ≥309, 루비오가 미국인 사망 확인, 연합군 "full-fledged war crime"(투르키 알말키), 민항기 영공 회피(AJ 10/10) ✔ · 트럼프 직접 타격 거절(TIME) ✔ |
| 날짜 요일 | 9/25 금 · 10/5 월 · 10/6 화 · 10/7 수 · 10/8 목 · 10/10 토 — 모두 일치 |

## 2. 막는 결함 4건(고친다)

### 2-1. 리야드 공항 사망 3명 — 사건 혼동 + 출처 표 어긋남
- `clm_0036`("이번 주 초 사우디 공항 공격으로 3명 사망", TIME 10/8 11:00 UTC)은 **10/6~7 리야드(1)·아브하(2) 공격**의 합계입니다. 10/8 킹칼리드 공항 공격의 사망 3(조종사 포함 사우디인, GACA)은 **별개 사건**(`clm_0038`, AJ 10/10 — Arab News·CNBC 교차 확인). 위키 집계 10/8~10 15명 = 3 + 12 와 맞습니다.
- 지금 출처 표: `riyadh_airport_0`(후티의 10/8 미사일 주장) → clm_0036, `riyadh_airport_1`("이 공항 공격으로 3명이 숨졌습니다", 귀속 없음) → clm_0037 — **둘이 바뀌어 있고** `_1` 은 TIME 의 다른 사건 수치를 10/8 공격에 붙인 꼴입니다.
- 고침: `riyadh_airport_0` → clm_0037. `riyadh_airport_1`+`_2` 를 한 문장으로: **"사우디 민간항공청은 10월 8일 공격으로 조종사를 포함한 사우디인 최소 3명이 숨졌다고 밝혔습니다."** → clm_0038(+ Arab News `https://www.arabnews.com/saudi-arabia/saudia-pilot-killed-in-attack-on-riyadh-airport-3005428` 를 출처로 더해 corroborated). `briefing_2`·`briefing_3` 의 clm_0036 → clm_0037·0038. clm_0036 은 쓰지 않거나 "10월 6~7일 리야드·아브하 공항 공격으로 3명(사우디 당국)" 으로만.

### 2-2. 메카 공격 "후티가 시도" 주체 — 3국 성명은 후티를 지목하지 않았다
- `mecca_attack_2` "사우디와 협정 3국은 **후티가** 메카와 메디나를 겨냥한 공격을 시도했다고 주장" ↔ `invocation_3` "성명은 후티를 위협으로 명시하지 않았다" 가 서로 어긋납니다. 원문: 사우디가 후티의 메카 공격 시도를 비난("red line", TIME); 3국 성명은 "메카·메디나를 겨냥한 공격 시도" 를 규탄하되 후티 미명시(AJ 10/6·FP).
- 고침: **"사우디는 후티가 메카를 겨냥한 공격을 시도했다고 비난했고, 협정 3국 성명도 메카와 메디나를 겨냥한 공격 시도를 규탄했습니다."** + `mecca_attack_3` "후티와 이란은 이를 부인했습니다." 그대로. AJ 10/6(`https://www.aljazeera.com/news/2026/10/6/pakistan-turkiye-join-saudi-deterrence-against-houthis-what-that-means`)을 출처로 추가.

### 2-3. 한국 연결 단락 없음 — 주문(order.yaml 흐름 ⑤·D156 "지정학+지경학")
- 검증 LLM 이 CSIS 에서 claim 을 못 뽑은 것은 파이프라인 문제이지 결정이 아닙니다. 출처를 보강하고 검증을 다시 돌려 **`korea` 장면 2~3문장**을 `briefing` 앞에 넣습니다. 수치는 각각 출처·기준 시점을 달고, **기준이 다른 수치(호르무즈 통과 비중 / 중동산 비중)는 한 문장에 섞지 않습니다**.
  - korea_0: CSIS(2026-04-02, Victor Cha·Andy Lim) — 한국 원유 수입의 70% 가 호르무즈를 지난다(페이지에 기준 기간 없음 → "CSIS 가 올해 4월 낸 분석에 따르면").
  - korea_1: 산업통상부 브리핑(이투데이 2026-05-26 보도, 양기욱 산업자원안보실장) — 호르무즈 봉쇄 뒤 중동산 원유 비중이 지난해 69.1% 에서 올해 5~7월 48.5% 로, 사상 처음 50% 아래(미주산 23.1 → 35.6%). `https://www.etoday.co.kr/news/view/2587839` 를 출처로 추가(한국어, 산업부 공식 브리핑 인용 — 가능하면 산업부 보도자료 원문도).
  - korea_2(연결, 선택): "사우디 = 한국 최대 원유 공급국" 은 기준 연도 있는 공식 통계(석유공사 페트로넷·관세청 2025)가 있을 때만. 없으면 빼고, 대신 배치가 이란 전쟁·호르무즈 봉쇄 중인 4월 초에 시작됐다는 MEE 5/18 문장(이미 출처 있음)으로 "왜 지금" 을 잇는다.
- 사용자는 게이트 ① 에서 이 단락을 빼도 됩니다 — 그 결정은 사용자 몫. 단락이 없는 지금 상태로는 주문 흐름을 못 채운 것이라 Fable 이 게이트 ① 을 요청하지 않습니다.

### 2-4. 길이·연결어
- 추정 5분 47초 + 한국 3문장 ≈ 6분 10초. **목표 ≤ 5분 30초(추정)**. 자르는 후보(정보 중복·장식 순): `invocation_5`(세부 미공개 — `troop_numbers_5` 와 중복) · `riyadh_airport_4`(미디어국장 주장) · `yemen_front_3`(사나 집회) · `reactions_0`(크림리 요약) · `riyadh_airport_1`→`_2` 병합(§2-1) · `briefing_0` 축약. 필수 유지: 두 배치 수치와 정부 반박(G4 같은 무게), 아시프 역할 발언, 10/8·10/10 사상자(날짜·발표 주체), 튀르키예 미비준.
- 린트 `[flow-overuse]` 76% → **70% 이하**(경고를 남기지 않는다). "그리고·특히·반면·한편·이에·또한·이어서·그러면서·게다가" 를 문장 앞에서 네 곳 이상 뺀다(C0 AI 상투 방지).

## 3. 권장(막지 않음 — 같은 수정 때 함께)
| 문장 | 권장 |
|---|---|
| reactions_0 | 라에드 크림리 → **라예드 크림리**(Rayed Krimly, AJ 표기) — 남기는 경우 |
| roles_2 | "튀르키예도 사우디에 군사 지원을 제공했습니다" → **"로이터에 따르면 튀르키예도 사우디에 방어·기술 지원을 보냈습니다"**(TIME 이 전한 로이터 문구) |
| pact_origin_3 | 전문은 비준 전 비공개(AJ 8/31) → **"3국 공동성명은 … 간주한다고 밝혔습니다"** 로 귀속 |
| troop_numbers_7 | 출처를 Khaama(본문 비어 있음·재인용) 대신 **MEE 2026-10-02**(`…/pakistan-sent-four-planeloads-weapons-saudi-backed-government-yemen-report`, 로이터 인용: 9월 수송기 4대, 방공체계·경포·드론·대드론 장비, 군사 고문 현지)로 교체. 문장: "9월 방공체계와 경포·드론 등을 실은 수송기 4대를 아덴에 보냈다" |
| mecca_attack_1 | Gulf News 9/26(SPA: 3국 국방 수뇌부 리야드 회의, 메카·민간·경제 기반시설 공격 규탄) 추가 → corroborated 강화. 같은 날 3국 외교장관 공동성명(anews 9/25)도 있음 — 문장은 "군 수뇌부" 그대로 가능 |
| troop_numbers_0 | 두 번째 출처(The Daily Star `…/pakistan-deploys-jet-squadron-thousands-troops-saudi-arabia-during-iran-war-4178736`, 로이터 기반) 추가 → unverified 해소 |
| invocation_4 | 이중 귀속 "…밝혔다고 보도했습니다" → "성명은 합의된 군사력을 사우디에 즉시 배치한다고 밝혔습니다" + 출처 ET 그대로 |
| 전체 | 수정 뒤 `script_labels.json` 재계산, `lint-script` 오류 0·경고 0, 미디어 표 재생성(새 문장 korea_* 의 사진 후보·사유 포함) |

## 4. 기록
- 출처 확인(`confirm-source`)은 Opus 대행 — 사용자에게 게이트 ① 자료와 함께 "출처 16+α 건은 대행 확인, 목록 첨부" 로 알린다(Fable 이 전달).
- 기사 등록 15건 선행(P1-2 몫)은 그대로 둔다(되돌릴 수 있음).
- 로이터 원문 미확보는 그대로 기록(재인용 매체 명시) — 원고 귀속은 "로이터는 … 보도했습니다" 로 충분.

## 5. 순서
이 수정(≈1~2시간) → R 보고 + `gulf_pact_gate1.txt` 재생성 → Fable 재확인(당일) → 사용자 게이트 ①. 그 사이 v5.20.1(light A)은 D-0179 순서대로 진행해도 됩니다(원고 수정이 먼저).
