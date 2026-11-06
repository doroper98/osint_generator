---
id: D-0322
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: high
supersedes: []
---

# 사용자 지시(2026-11-06) — 지난 두 영상의 썸네일·전달 패키지: 『휴전안의 한 달』(iran_ceasefire_2026)·『제품은 팔고, 능력은 안 판다』(china_tech_export_controls_2026)

> 사용자 원문: "미국 이런 휴전안 정리 영상 세션과, 중국 기술 수출 통제 세션을 찾아서 각 영상의 썸네일과 제목, 설명, 태그를 이 세션에 나한테 줘."

제목·설명·태그는 감독이 썼다(아래 ④). 구현은 **썸네일 2장 + description.yaml 값 반영 + 전달 패키지**다. D-0320·D-0321 이 끝난 뒤 착수. 영상 본편은 건드리지 않는다.

## 1. 입력(둘 다 out/ 준비물 없음 → `tools/thumbnail.py --from-video` 모드, D-0320 예고 §(3))
| 영상 | 전달본(artifacts) | md5 | plan.json | 장르/테마 |
|---|---|---|---|---|
| iran_ceasefire_2026 | `origin/artifacts/iran-ceasefire-v7.4.0` : `iran_ceasefire_2026/final_v3b/final_deliver.mp4` | 0ec9d9f37ae91396628721ff7eafef68 | `origin/claude/iran-ceasefire-2026` : `projects/iran_ceasefire_2026/plan.json`(script·description.yaml 도 그 브랜치) | geopolitics → geo_econ |
| china_tech_export_controls_2026 | `origin/artifacts/china-export-controls-v7.4.0` : `china_tech_export_controls_2026/final/final_deliver.mp4` | 02ccbde34f19f0cc6b881a38bc5367d4 | 우리 브랜치 `projects/china_tech_export_controls_2026/plan.json` | geopolitics → geo_econ |

- 큰 아티팩트 브랜치는 `git fetch --depth 1 --filter=blob:none origin <branch>` 뒤 `git show <ref>:<path> > 파일` 로 필요한 blob 만 받는다(감독 실측: 통째 fetch 는 early EOF).
- `--from-video`: 타이틀 카드 t0 는 plan.json cards(kind title).t0. 바탕 = 영상의 t0 − 1/fps 프레임(카드 그라데이션 alpha 0 인 원 장면). 그 위에 **같은 draw_title_card**(제목 = plan title, 부제·날짜 = plan) 를 alpha 1 로 그린다. provenance `thumbnail.source: {mode: from_video, file, md5, frame_t}`.
- iran 프로젝트 폴더는 `git checkout origin/claude/iran-ceasefire-2026 -- projects/iran_ceasefire_2026` 로 우리 브랜치에 가져온다(script·direction 은 수정 금지, description.yaml 만 ④ 값 추가).

## 2. 산출
- 각 artifacts 브랜치에 `delivery/`: thumbnail.png·jpg, title.txt, description.txt, tags.txt, thumbnail.json, MD5SUMS (us_midterms 와 같은 구성). 전달본 mp4 는 그대로(재업로드 금지).
- 감독 확인용으로 두 썸네일 png 경로를 send_message 로 먼저 알린다.

## 3. ④ 값 — description.yaml 에 넣을 것(감독 작성, 사용자에게 이미 전달)
### iran_ceasefire_2026
- title: 미국·이란 휴전안 한 달 정리 — 7일안·이틀안·밴스 서한, 무엇이 먼저 풀려야 하나 | 호르무즈·양측 조건·한국 접점
- alt_titles: ["휴전안의 한 달 — 미국과 이란, 무엇이 먼저 풀려야 하나", "호르무즈는 다시 열릴까 — 미국과 이란이 밝힌 조건과 지켜볼 신호 다섯 | 휴전안 한 달 정리"]
- hashtags: [#미국이란휴전, #호르무즈해협, #이란전쟁]
- tags: 미국 이란 휴전, 미국 이란 전쟁, 이란 전쟁 2026, 호르무즈 해협, 휴전안, 7일안, 이틀안, 카타르 중재, 도하 협상, 파키스탄 중재, 이슬라마바드 양해각서, 아라그치, 밴스 서한, 레자이, 모즈타바 하메네이, 트럼프 이란, 해상 봉쇄, 동결 자금, 원유 제재, 브렌트유, 전쟁 위험 보험료, 울산 원유 수입, 장금상선, 중동 정세, 국제 정세, 지정학, Iran ceasefire, Strait of Hormuz, US Iran war 2026
- 설명 전문: 감독 스크래치 `youtube_description_iran_ceasefire_2026.txt`(아래 ⑤에 그대로 수록) — 챕터 9줄(타이틀 포함), 유의 3줄, 자료 요약, 주요 링크 4, 사진·영상 13(credits.txt 와 같은 목록), 인물 4, 지도·Music·표기, 해시태그 3.

### china_tech_export_controls_2026
- title: 중국, 열흘 사이 수출통제 5건 — AI·바이오·태양광 기술 40개 금지·제한 초안, 드론·터널굴착기 허가제 | 희토류 이후 1년, 한국 접점
- alt_titles: ["제품은 팔고, 능력은 안 판다 — 중국 기술 수출통제 열흘, 그리고 한국", "중국산 터널굴착기, 11월 18일부터 허가제 — 중국 기술 수출통제가 한국 공사 현장과 태양광에 닿는 곳"]
- hashtags: [#중국수출통제, #터널굴착기, #미중기술패권]
- tags: 중국 수출통제, 중국 기술 수출통제, 수출통제 기술 목록, 터널굴착기, TBM, 드론 수출통제, 준설선, 영업비밀 특별규정, 인공지능 수출통제, 페로브스카이트, 탠덤 태양전지, 생물의약, 희토류 통제, 미중 휴전, 부산 미중 정상회담, 중국 상무부, 한화큐셀, 동아지질, 전력구 공사, 중국철건중공, 헤렌크네히트, 마노즈 조시, 옵서버연구재단, 미중 기술 패권, 경제 안보, 지정학, 국제 정세, China export controls, tunnel boring machine, perovskite
- 설명 전문: ⑤ 수록. 챕터 7줄, 자료 요약, 주요 링크 4(상무부 공고 48·50·49호, Global Trade Alert), 사진 11(credits.txt 목록), 인물 2, 지도·Music·표기, 해시태그 3.

## 4. 절차·보고
- 순서: iran 폴더 가져오기 → description.yaml 두 개에 ④ → thumbnail.py --from-video ×2 → deliver_package.py ×2(설명문은 ⑤ 전문과 같아야 한다 — 도구 생성 결과가 다르면 다른 점을 R 에 표로) → artifacts delivery/ ×2 → R + send_message.
- 커밋 prefix v7.4.0:, 모델명 금지, PR 금지, 영상 본편·음성·direction 수정 금지.

## 5. 설명 전문
### 5.1 iran_ceasefire_2026
```
미국·이란 휴전안 한 달 정리 — 7일안·이틀안·밴스 서한, 무엇이 먼저 풀려야 하나 | 호르무즈·양측 조건·한국 접점

2026년 10월 31일, 이란 대표단이 카타르 도하에 도착했습니다. 2월 28일 개전부터 이어진 여덟 달의 전쟁, 9월 24일 이란의 7일안부터 도하 협의까지 휴전안의 한 달, 양측이 밝힌 조건, 호르무즈 해협의 지금, 한국과 닿는 접점을 지도와 시간축 위에 정리했습니다.

휴전 가능성은 예측하지 않았습니다. 양측이 이미 밝힌 조건을 나란히 두고, 지켜볼 신호 다섯 가지(해협 통항, 전쟁 위험 보험료, 카타르에 묶인 자금, 중재 일정, 레바논 전선)를 제시했습니다. 기준 시점은 2026년 11월 1일입니다.

챕터
0:00 10월 31일 도하
0:22 타이틀
0:28 여덟 달 — 2월 28일부터 8월 17일까지
1:53 휴전안의 한 달 — 7일안에서 도하 협의까지
3:30 양측이 밝힌 조건
4:12 호르무즈 지금 — 통항·기뢰 주장·유가
5:05 가능성 — 조건과 신호 다섯
6:14 한국 — 원유 수입·동결 자금·장금상선
7:21 정리

유의
· 카타르 초안의 세부와 미국의 역제안 내용은 익명 관리가 전한 보도에 근거합니다. 밴스 부통령 서한의 내용은 공개되지 않았습니다.
· 10월 29일 기뢰 피격 주장과 미 중부사령부의 반박은 어느 쪽도 독립적으로 확인되지 않았습니다.
· 전쟁 위험 보험료 그래프는 10월 범위(6~10%) 가운데 하단만 선으로 표시했습니다.

자료: Al Jazeera(2.28~10.31), CNBC, The National, Asharq Al-Awsat, France 24/AFP, SCMP, Xinhua, Axios, Haaretz, Reuters(Al Arabiya·Arab News·U.S. News·Iran International 경유), IRNA, CNN, The Washington Post, NPR, Euronews, Middle East Eye, Gulf News, The New Arab, Britannica, U.S. EIA, Insurance Business, 한국해양진흥공사, 울산세관, 오피넷, 연합뉴스, 서울경제, 한국일보, 뉴스1, 파이낸셜뉴스, 세계일보, 경향신문 (전체 72건 링크는 고정 댓글)

주요 링크
이란 대표단 도하 도착(Al Jazeera 10.31) https://www.aljazeera.com/news/2026/10/31/iran-fm-says-us-outreach-a-positive-step-as-delegation-in-qatar-for-talks
이란의 7일안(Al Jazeera 9.25) https://www.aljazeera.com/news/2026/9/25/whats-in-irans-seven-day-plan-to-reopen-the-strait-of-hormuz
양해각서 만료(Al Jazeera 8.17) https://www.aljazeera.com/news/2026/8/17/us-iran-memorandum-of-understanding-expires-how-and-why-it-fell-apart
기뢰 피격 주장과 미군 반박(Gulf News 10.30) https://gulfnews.com/world/mena/us-military-rejects-iranian-mine-strike-claims-says-hormuz-transit-lanes-remain-clear-1.500727648

사진·영상: '에픽 퓨리' 작전 타격 영상(2026.3.1, 미 국방부, Public domain) · 호르무즈 해협 위성 사진(2020, NASA, Public domain) · 이슬라마바드 회담장 입구(2026.4.11, 메흐르통신 Hamed Malekpour, CC BY 4.0) · 미 해군 헬기의 봉쇄 작전 감시(2026.4.25, 미 해군 중부사령부, Public domain) · 봉쇄 작전 중인 상륙함 뉴올리언스(2026.4.28, 미 국방부, Public domain) · 미 중부사령부 보복 타격 영상(2026.7.7, Public domain) · 봉쇄 검문 미 해병대 헬기(2026.7.16, 미 해군 중부사령부, Public domain) · 취재진 앞의 아라그치 외무장관(모스크바 2026.4.27, kremlin.ru, CC BY 4.0) · 국제우주정거장에서 본 호르무즈 해협(2016, NASA, Public domain) · 모흐센 레자이 사무총장(2020, khamenei.ir, CC BY 4.0) · 페르시아만 원유 터미널의 유조선(2005, 미 해군, Public domain) · 파테메 모하제라니 대변인 브리핑(2026.1.27, Mehr News Agency·Fatemeh Mirahmadi, CC BY 4.0) · 호르무즈 일대 부대를 찾은 미 중부사령관(2026.10.23, 미 중부사령부, Public domain)
인물 사진: 아라그치(kremlin.ru, CC BY 4.0) · 알리 하메네이(khamenei.ir, CC BY 4.0) · 도널드 트럼프(백악관, Public domain) · 페제시키안(Ayoub Ghaderi, CC BY 4.0)
기사 인용: 헤드라인 번역과 요지를 자체 조판(기사 화면 캡처·로고 없음)
지도: Natural Earth(Public domain) · 지형: AWS Terrain Tiles(Mapzen terrarium) · 국기: flag-icons(MIT)
Music: "Mario Bava Sleeps In a Little Later Than He Expected To" — Chris Zabriskie (CC BY 4.0) · 내레이션: AI 음성 합성 · 사실 장면에 AI 생성 이미지는 쓰지 않았습니다
표기: 호르무즈 통항·기뢰 주장은 양측 발표로 독립 확인되지 않았으며, 해석은 각 기관의 견해입니다.

#미국이란휴전 #호르무즈해협 #이란전쟁
```
### 5.2 china_tech_export_controls_2026
```
중국, 열흘 사이 수출통제 5건 — AI·바이오·태양광 기술 40개 금지·제한 초안, 드론·터널굴착기 허가제 | 희토류 이후 1년, 한국 접점

중국 상무부는 2026년 10월 16일부터 26일까지 열흘 남짓 사이 다섯 건의 수출통제 공고를 냈습니다. 인공지능·생물의약·태양광 기술 40개를 수출 금지·제한 목록에 넣는 초안(금지 후보 14개, 제한 후보 26개), 드론·터널굴착기·준설선 수출 관리(11월 18일 시행), 그리고 영업비밀 특별규정 초안입니다.

2025년 10월 희토류 통제 확대와 부산 미중 정상회담 뒤의 유예, 2027년 1월 10일까지 연장된 미중 휴전을 배경에 두고, 중국산 터널굴착기가 들어간 경기도 전력구 공사와 진천의 페로브스카이트 시험 라인 등 한국 접점을 지도로 정리했습니다. 기술 목록 개정과 영업비밀 규정은 의견 수렴 중인 초안이며, 민감 국가 명단은 공개되지 않았습니다. 기준 시점은 2026년 10월 30일입니다.

챕터
0:00 터널굴착기 허가제
0:29 타이틀
0:35 열흘 — 다섯 공고
2:37 제품과 능력 — 희토류 이후 1년과 양측 해석
4:11 한국 — 공사 현장과 공장
5:27 다음 날짜 — 11월 15일·18일·24일, 1월 10일
6:08 정리

자료: 중국 상무부·과학기술부·해관총서 공고 원문(2026년 제48·49·50호)과 대변인 문답, 영업비밀 특별규정 초안, Reuters, CGTN, Xinhua, Global Times, Al Jazeera, CNBC, Global Trade Alert, 옵서버연구재단(ORF), China Global South Project, Tunnelling Journal, 연합뉴스, 이투데이, EBN, 토요경제, 아이뉴스24, 대한경제, 메디파나뉴스, AI타임스 (전체 링크는 고정 댓글)

주요 링크
상무부·과기부 공고 제48호 — 수출 금지·제한 기술 목록 개정 초안 https://www.mofcom.gov.cn/zwgk/zcfb/art/2026/art_0a31a3c9ac404f7a9b0e917ce3412997.html
상무부·해관총서 공고 제50호 — 터널굴착기 등 수출통제 https://www.mofcom.gov.cn/zwgk/zcfb/art/2026/art_9ce34ccfa6c040d7a4f7622f89133be5.html
공고 제49호 — 드론 수출통제 조정 http://www.mofcom.gov.cn/zwgk/zcfb/art/2026/art_f71c27f81b8f4097b876818abbd19851.html
Global Trade Alert — 중국 수출통제 1년 https://globaltradealert.org/blog/china-export-controls-a-year-on

사진: 중국철건중공 터널굴착기 전시(2021, Huangdan2060, CC BY 3.0) · 해체 중인 터널굴착기 커터헤드(뉴욕 2019, MTA Capital Construction, CC BY 2.0) · 데이터센터 서버실(2013)과 서버 기판(2011) (Intel Free Press, CC BY 2.0) · 줄기세포 시료 처리(국제우주정거장 2026, NASA, Public domain) · DJI 드론(루마니아군 대드론 훈련 2026, NATO·DVIDS, Public domain) · 희토류 산화물(2009, 미 농무부 ARS Peggy Greb, Public domain) · 트럼프·시진핑 김해공항 회담 2장(2025.10.30, 백악관 Daniel Torok, Public domain) · 중국 태양광 발전 단지 위성 영상(2017, NASA 지구관측소, Public domain) · 페로브스카이트 태양전지 시료(2022, NREL Dennis Schroeder, Public domain)
인물 사진: 시진핑(아제르바이잔 대통령 공보실, CC BY 4.0) · 도널드 트럼프(백악관, Public domain)
기사 인용: 헤드라인 번역과 요지를 자체 조판(기사 화면 캡처·로고 없음)
지도: Natural Earth(Public domain) · 지형: AWS Terrain Tiles(Mapzen terrarium) · 국기: flag-icons(MIT)
Music: "Mario Bava Sleeps In a Little Later Than He Expected To" — Chris Zabriskie (CC BY 4.0) · 내레이션: AI 음성 합성
표기: 기술 목록 개정과 영업비밀 규정은 의견 수렴 중인 초안이며, 일부 한국 접점은 단일 보도에 근거합니다. 굴착기 운송 경로와 공사 지점은 개략 표현입니다. 해석은 각 기관의 견해입니다.

#중국수출통제 #터널굴착기 #미중기술패권
```
