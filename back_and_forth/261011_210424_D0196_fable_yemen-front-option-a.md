---
id: D-0196
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1-6"
version: v5.21.7
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 7 — 예멘 탈환 공세 장면에 전황 표시(선택 A: 기존 엔진, 같은 재렌더)

사용자 원문: "전황 분석 스킬을 이용해서 반군과 정부군이 어떻게 어떤 도시를 점령하고 탈환했는지 보여주면 좋겠음. 아무것도 안나와서 뭔지 잘 모르겠음"
(`docs/handoff/reports/phaseP1/user_feedback/yemen_offensive_empty.jpg` — 예멘 정부군 뱃지와 카드만 있고 도시·전선 변화가 없다).

감독이 선택지를 물었고 사용자가 **A(기존 엔진으로 빠르게)** 를 골랐다(2026-10-11). 전황 스킬(`sketch.campaign`)의 본편 이식(B)은 하지 않는다 — 스케치는 엔진 레지스트리 밖(D128)이고, 2026년 10월 예멘용 경위도 눈금 참고 작전도가 없다.

## 범위
- 장면: 원고 "한편 예멘에서는 … 10월 초 후티 점령지 탈환 공세를 시작했습니다."(clm_0032) 와 다음 문장 "예멘 정부군은 10월 5일 모카에 도달해 …"(모카 문장) 구간.
- **원고(내레이션)는 바꾸지 않는다** — 게이트 ① 재승인 없이 화면 요소만 더한다. 화면에 새로 들어가는 사실은 모두 출처를 claims 에 등록하고 크레딧·설명란 출처 줄에 넣는다.

## 감독 사전 조사(출처 후보 — Opus 가 원문을 열어 문구·날짜를 대조할 것)
| 사실 | 후보 출처 |
|---|---|
| 9월 후티가 모카와 홍해 섬 일부 장악 | Al Jazeera 2026-10-05 "Yemen war: What's the latest…" / The National 2026-10-05 |
| 10월 4일 알리미 대통령 '예멘의 새벽' 작전 선언, 사우디 공중 지원 | CNBC 2026-10-04 / FDD Long War Journal 2026-10 |
| 10월 5일 정부군 바브엘만데브·모카 통제 **주장** | The National 2026-10-05 |
| 정부군 모카 외곽 도달(로이터 소식통) | Al Jazeera 2026-10-06 |
| 10월 7일 타이즈 알와지이야 탈환 작전 개시 | Al Jazeera 2026-10-07 |
URL: cnbc.com/2026/10/04/yemen-launches-offensive-to-seize-all-areas-from-iran-backed-houthis.html · longwarjournal.org/archives/2026/10/yemeni-government-forces-launch-saudi-backed-counteroffensive-against-houthis.php · thenationalnews.com/news/gulf/2026/10/05/yemen-government-forces-claim-bab-al-mandeb-gains-as-saudi-coalition-says-100-jets-join-houthi-offensive/ · aljazeera.com/news/2026/10/5/yemen-war-escalates-whats-the-latest-on-the-battlefield · aljazeera.com/news/2026/10/6/yemen-war-whats-the-latest-on-the-battlefield · aljazeera.com/news/2026/10/7/yemeni-forces-launch-offensive-to-retake-houthi-held-al-waziiya-in-taiz

## 화면 구성(기존 이벤트만 — marker·route·card·country, 레지스트리 밖 새 형태 금지 P10)
1. 지명 마커(날짜 부제): 모카 "9월 후티 장악" → 모카 문장에서 "10.5 정부군 도달 주장"으로 바뀜(두 마커 순차, 앞 것은 낮춤) · 바브엘만데브 "10.5 정부군 통제 주장" · 타이즈(알와지이야) "10.7 탈환 작전 개시".
2. 진격 화살표(route): 정부군 쪽(아덴·라흐즈 방면) → 모카·바브엘만데브, → 타이즈. 한꺼번에 튀어나오지 않게 순차(C0 되돌리면 안 되는 것).
3. **주장은 주장으로**: 부제 문구에 "주장"을 남긴다(독립 확인 안 됨). 양측 주장 균형(C0 경계) — 후티 측 주장이 출처에 있으면 같은 무게로 한 줄.
4. 점령 지역 면(polygon)은 그리지 않는다 — 날짜 박힌 권리 확인 자료가 없다(출처 없는 수치·선 금지).
5. 라벨·경로는 D-0191·D-0192 규칙(선↔글자 교차 금지, 지명 겹침 금지, light 짙은 글자)을 따른다.
6. 사람 손질로 기록(사유 D-0196). 연출가 재실행으로 만들어도 된다면 그쪽이 우선(P8) — 결과는 같은 검사를 통과해야 한다.

## 보고
전/후 크롭(이 장면 시작·모카 문장·끝) + 새 claims 목록(출처·문구 대조 결과). D-0191~0195 와 같은 재렌더.
