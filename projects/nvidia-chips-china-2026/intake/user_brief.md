# 르포 초안 — 젠슨 황 사임과 엔비디아 GPU의 중국 유입 경로 (사용자 제공 문서, 2026-11-17)

원문: https://claude.ai/artifact/KJNjMyyZtxSZuEBkBFoDie (Claude Doc, rev 69). 아래는 본문 전사(링크는 괄호 안 URL).

## 편집자 주
- 공개 보도와 법원·정부 자료만으로 쓴 르포 초안. 현장 취재·인터뷰 없음.
- 전제 확인: 젠슨 황은 11월 8일 외도를 인정했고 12일 CEO에서 물러났다(확정).
- 구도: 외도 상대가 메가스피드 전 임원이라 스캔들과 유입 경로가 같은 인물로 연결된다.
- 확정과 의혹의 구분: 외도와 사임은 확정. 스파이 의혹, 메가스피드의 밀수 관여, 밀수 총량은 모두 미확정.
- 실명이 나오는 혐의는 대부분 재판 전이거나 익명 보도. 단정 표현은 명예훼손 위험.

## 1. 3월의 창고 사진과 11월 8일의 사과문
- 미국 검찰이 지난 3월 공개한 감시 사진: 동남아 어느 창고에서 한 여성이 붉은 헤어드라이어로 서버 포장 상자의 일련번호 스티커를 떼는 장면. (Bloomberg https://www.bloomberg.com/news/features/2026-10-01/nvidia-faces-questions-over-china-ai-chip-smuggling-cases)
- 이 사진은 슈퍼마이크로 공동창업자 월리 리아우(Yih-Shyan "Wally" Liaw) 사건에서 나왔다. 엔비디아 GPU를 실은 서버 약 25억 달러어치가 동남아 위장 회사를 거쳐 중국으로 갔다는 혐의. 검찰은 감사인을 속이려고 작동하지 않는 모형 서버 수천 대를 창고 세 곳에 쌓아 뒀다고 주장. 리아우는 무죄 주장. (Fortune https://fortune.com/2026/11/10/2-scandals-1-destination-why-nvidia-cant-shake-china-smuggling-allegations/)
- 11월 8일 젠슨 황은 임직원에게 사과문을 보냈다. 배우자에게 충실하지 못했다고 인정. 상대 이름은 적지 않음. 자신의 처신이 보도로 제기된 국가안보 우려와 닿아 있음을 스스로 밝힘. 나흘 뒤 이사회는 사임을 받아들였고 CFO 콜렛 크레스가 임시 CEO. (TechCrunch https://techcrunch.com/2026/11/13/nvidia-ceo-jensen-huangs-affair-with-alleged-chinese-spy-a-timeline/)
- 뉴욕타임스와 로이터는 11월 11~12일 추가 외도 의혹 보도. 상대 앨리스 황은 싱가포르 AI 인프라 기업 메가스피드의 전 임원. 메가스피드는 엔비디아의 동남아 최대 구매자로 보도됐고, 미국과 싱가포르 당국의 수출통제 위반 조사 대상.
- 미 정보당국이 그를 중국 국가안전부에 포섭된 인물로 본다는 보도. 앨리스 황 본인의 공개 입장은 확인되지 않음. 메가스피드는 위법 행위 부인. 미 법무부도 그가 스파이인지 아직 결론 내리지 않았다고 밝힘. 어느 혐의도 법정에서 입증되지 않음.

## 2. 미국 수출통제의 연혁과 두 가지 허점
- 미국 수출통제 당국은 이 현상을 '전용(diversion)'이라 부른다(라틴어 divertere, '옆으로 돌리다').
- 연혁 표:
  - 2022년 8~10월: A100·H100 등 첨단 칩의 중국 수출에 허가제 도입
  - 2023년 10월: 기준 강화. 중국용으로 낮춘 A800·H800도 막힘
  - 2025년 1월: 바이든 행정부, 중국 유입 차단을 겨냥한 잠정 최종 규칙 발표
  - 2025년 4월: H20에도 수출 허가 요구
  - 2025년 5월: 트럼프 행정부 상무부, 1월 규칙 철회
  - 2025년 8월: H20 일부 수출 허가
  - 2025년 12월: H200의 중국 판매 허용 방침. 매출의 25%는 미 정부 몫
  - 2026년 1~2월: H200 사례별 허가 시작. 블랙웰은 계속 금지
  - 2026년 11월 16일: 해외 데이터센터 원격 접속에 허가제. 동남아 4개국과 브라질 추가
  - 출처: 엔비디아 10-Q https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000052/nvda-20260426.htm , CBS https://www.cbsnews.com/news/howard-lutnick-commerce-department-chips-chaos-former-employees/ , Reuters https://live.euronext.com/en/financial-news/exclusive-military-linked-chinese-university-bought-nvidia-h200-chips-despite-us , Fortune https://fortune.com/2026/11/16/new-commerce-rule-nvidia-chip-singapore-malaysia-china/
- 허점 ① 집행: CBS가 만난 전직 상무부 관리들에 따르면 수출통제 명단(Entity List) 추가는 2025년 10월 9일 이후 1년간 멈췄다. 18년 만의 공백. 동남아 현장에서 수상한 정황을 찾고도 윗선이 움직이지 않았다는 증언. 상무부는 CBS 질의에 답하지 않음.
- 허점 ② 설계: 규칙은 칩의 물리적 이동을 통제했고 칩을 누가 쓰는지는 묻지 않았다. 칩이 말레이시아에 있으면 베이징 기업이 원격으로 써도 위반이 아니었다. 원격 사용 규제 규칙은 2026년 11월 16일에 처음 나왔다.

## 3. 밀수 수법 다섯 가지
- Epoch AI: 2025년 말까지 중국에 밀반입된 연산 능력을 H100 환산 66만 개로 추정(90% 신뢰구간 29만~160만). 기소장·탐사보도로 드러난 물량만은 약 30만 개. (https://epoch.ai/blog/chip-smuggling) 한계: 혐의 상당수 미입증, 적발률 가정에 민감, 전용된 칩이 모두 중국에 닿았다는 보장 없음.
- 하나, 통과 법인: 슈퍼마이크로 사건. 서버는 동남아의 한 업체를 최종 수요자로 내세워 출하. 이 업체는 방콕의 AI 인프라 회사로 보도됐고 기소되지 않음. 슈퍼마이크로 법인도 기소되지 않았고 스스로 피해자라고 말함. Epoch 정리 공소장 내용으로 2025년 4~5월에만 5억 1,000만 달러어치가 중국에 닿음. (Fortune 11/10)
- 둘, 미국 안의 대리 구매자: 텍사스 하오글로벌 대표는 2025년 10월 유죄 인정. 2024년 10월~2025년 5월 H100·H200 최소 1억 6,000만 달러어치를 반출했거나 반출하려 함. 대리 구매자, 미국 내 창고, 상표 바꿔 달기. 중국에서 송금된 돈 5,000만 달러 초과. (Arnold & Porter https://www.arnoldporter.com/en/perspectives/blogs/enforcement-edge/2025/12/doj-shutdown-of-major-china-linked-ai-tech-smuggling-network) 플로리다 사건: 탬파의 가짜 부동산 회사, A100 약 400개가 태국·말레이시아를 거쳐 나갔다는 혐의. (Fortune https://fortune.com/2026/05/13/nvidia-chip-smuggling-china-russia-iran-export-controls-supermicro/)
- 셋, 서류: 조지아 사건 피고인 3명은 최종사용자 증명서를 꾸미고 태국의 가짜 구매자를 세웠다는 혐의. 그럴듯한 웹사이트와 재무 기록. 메신저 대화에 중국 언급을 지우자는 내용. 다만 2023년 10월의 1억 7,000만 달러짜리 주문은 판매사 컴플라이언스에 걸려 무산.
- 넷, 내부자: 대만 지룽 지검은 8월 엔비디아의 현지 고위 관리자 장(Chang) 씨를 기소. B300 칩을 실은 서버 74대가 일본과 인도네시아를 거쳐 중국으로 갔다는 혐의. 나머지 56대는 5월 대만 해경이 압수. 죄명은 문서 위조와 배임. 블룸버그는 엔비디아가 대만 정치권 인사들에게 이 기소에 대한 우려를 전했다고 보도. (TNW https://thenextweb.com/news/taiwan-indicts-nvidia-manager-chip-smuggling-eu-gap , Bloomberg https://www.bloomberg.com/news/articles/2026-11-15/nvidia-sought-taipei-s-help-over-employee-s-chip-smuggling-case)
- 다섯, 통관 신고가: Epoch이 양국 무역통계 대조. 2024년 4월~2025년 6월 중국은 말레이시아산 서버 38억 달러어치 수입 기록, 말레이시아의 대중 수출 기록은 6억 달러. 대수는 비슷, 가격이 다름: 말레이시아 수출 신고가 대당 1만 7,000달러, 중국 수입 신고가 10만 6,000달러. (https://epoch.ai/data-insights/malaysia-china-chip-smuggling) 이 흐름은 2025년 7월 말레이시아가 AI 칩 수출 허가제를 도입하자 몇 주 만에 급감. Epoch은 밀수와 맞아떨어지는 정황일 뿐 증거는 아니라고 밝힘.
- 국경을 넘은 칩은 중국 안에서 다시 팔린다. 중국 국내에서 이 거래는 불법이 아니다.

## 4. 칩을 옮기지 않는 우회로
- 해외 데이터센터 임차: 칩은 제3국에 두고 중국 기업이 데이터를 가져가거나 원격 접속.
- 2025년 3월, 중국인 엔지니어 네 명이 베이징에서 말레이시아로. 각자 여행가방에 하드디스크 15개씩. 회사는 현지 데이터센터에서 엔비디아 서버 약 300대를 빌려 둔 상태. (WSJ https://www.wsj.com/tech/china-ai-chip-curb-suitcases-7c47dab1)
- 이것은 밀수가 아니었다. CNBC는 지난 8월 문샷AI, 바이트댄스, 알리바바, 텐센트가 태국·말레이시아·일본 등의 데이터센터를 통해 제한 칩의 연산력을 확보했다고 보도. (Quartz https://qz.com/chinese-ai-firms-nvidia-chips-southeast-asia-data-centers-081926)
- 미국 싱크탱크 IFP: 중국이 원격으로 쓰는 해외 연산력 올해 H100 환산 약 100만 개, 2027년 말 전망 280만 개. (SCMP https://scmp.com/tech/tech-war/article/3371929/chinas-ai-compute-surge-heavily-reliant-us-chips-offshore-cloud-access-report)
### 메가스피드: 이력과 의혹
- 2015년 중국 게임 개발사의 해외 법인으로 싱가포르에 설립(당시 7로드 인터내셔널). 2023년 3월 개명, 지분이 영국령 버진아일랜드의 황러 리미티드로. 황러는 앨리스 황의 다른 이름. 총자산은 2023년 말~2024년 사이 약 90배로 불어 30억 달러에 육박. (ABC https://www.abc.net.au/news/2026-11-16/alice-huang-megaspeed-departure/107388304)
- NYT 2025년 보도: 메가스피드는 2년간 엔비디아 칩 48억 달러어치 구매. 그중 20억 달러 가까이는 말레이시아·인도네시아 데이터센터에 설치돼 중국 고객이 원격 사용. 미 상무부 관리가 2024년 말레이시아의 한 데이터센터에서 상자도 뜯지 않은 엔비디아 장비를 봤다는 대목. 톰 코튼 상원의원은 2025년 10월 상무장관에게 조사 요구. (Fortune 11/10, 코튼 의원실 https://www.cotton.senate.gov/news/press-releases/cotton-to-lutnick-investigate-chinese-government-spin-off-megaspeed-for-skirting-us-export-laws)
- WSJ 11월 14일: 메가스피드가 중국 기업을 위해 약 120억 달러어치 주문 주선(2024년 3월~2025년 6월). 그 문서로는 실제 인도 물량을 알 수 없음. 블룸버그: 앨리스 황이 세운 중국 회사가 밀수 칩을 조달해 상하이 데이터센터에 설치. (Asia Times https://asiatimes.com/2026/11/china-hoards-nvidias-ai-chips-as-us-curbs-remote-access/ , Bloomberg https://www.bloomberg.com/news/articles/2026-11-13/banned-nvidia-chips-installed-at-china-data-center-linked-to-alice-huang)
- 관계사가 엔비디아의 우대 클라우드 파트너 지위까지 얻었다는 보도. 디인포메이션: 이 관계망을 거친 구매가 75억 달러. (TechCrunch 타임라인)
- 메가스피드는 부인: 합법적 사업, 보도에 검증 가능한 증거 없음. 앨리스 황은 2025년 8월 30일 떠났다고 밝힘. 싱가포르 당국은 2025년 2월 조사에 나섰지만 그의 범죄를 입증할 증거는 부족하다고 봄. 회사 조사는 계속.
### 허가받은 H200의 간접 반입
- 로이터: H200 약 60만 개가 홍콩에 쌓여 있다. 베이징이 대량 수입을 승인하지 않아서. 소량은 중개상과 간접 경로로 본토에. (Fortune 11/16, Reuters)
### 11월 16일 규칙과 해외 용량 선점
- 스캔들 보도 이후 중국 AI 기업들은 해외 데이터센터 용량을 서둘러 예약. 엔비디아가 클라우드 파트너의 중국 고객 비중을 49%로 제한하고 아시아 승인 구매자 명단을 절반 넘게 줄였다는 보도. 11월 16일 상무부 규칙: 대형 데이터센터가 중국 본사 기업에 접속을 내주려면 허가 필요. 기존 고객을 둔 곳에는 90일. (Quartz https://qz.com/chinese-ai-firms-overseas-nvidia-capacity-crackdown-111226 , Asia Times)

## 5. 어디에 쓰이는가
- Epoch: 2022년 이후 세계에 풀린 AI 연산력의 72%가 미국에 도착, 중국 몫은 10% 미만. (https://epoch.ai/data/ai-chip-imports-documentation/methodology)
- 최신 공개 모델: 11월 12일 전 오픈AI 연구원 윌 디퓨의 포렌식 보고서. 공개된 모델 가중치로 훈련에 쓴 GPU를 식별할 수 있다는 주장. 딥시크, 문샷AI, 미니맥스, 앤트그룹의 모델 6종에서 블랙웰의 지문. 백악관 기술고문 마이클 크라치오스도 올해 초 문샷이 수출금지 칩을 썼다고 말함. (The Register https://www.theregister.com/ai-and-ml/2026/11/13/chinese-ai-labs-are-training-models-on-nvidias-blackwell-despite-export-controls-says-ex-openai-engineer/5309891 , TechCrunch https://techcrunch.com/2026/11/13/export-banned-nvidia-chips-are-behind-chinas-most-powerful-ai-models-uh-oh-jensen/) 다만 지문은 접근 정황일 뿐 칩 위치는 말해 주지 않는다.
- 군 연계 대학: 로이터가 중국 조달·법인 기록 26건 검토. 시안의 서북공업대학(미 수출통제 명단)은 10월 지역 업체를 통해 H200 두 개를 87만 4,700위안에 구매. 1월에는 H200 8개짜리 서버 접속권을 7개월 단위로 계약. 베이항대는 4월 A800 네 개를 48만 9,000위안에. (Reuters via Euronext)
- 시간 단위 임대: 중국과학원대학 관련 정부 공고에 H800 사용료 칩당 시간당 10위안.
- 고쳐 쓰는 칩: 선전의 수리 업체. 로이터 2025년 취재: 한 업체 한 달 최대 500개 수리, 수리비 개당 1만~2만 위안. (Reuters https://ca.finance.yahoo.com/news/china-repair-demand-banned-nvidia-210306863.html)

## 6. 반론과 한계
- 엔비디아 입장: 젠슨 황은 2025년 5월 컴퓨텍스에서 전용의 증거가 없다고 말함(데이터센터용 시스템은 한 대가 2톤에 가깝다). (Tom's Hardware https://www.tomshardware.com/tech-industry/artificial-intelligence/nvidia-ceo-jensen-huang-says-theres-no-evidence-of-any-ai-chip-diversion) 엔비디아는 자사 실사가 여러 기소에 기여했고 전용된 시스템에는 지원을 하지 않는다고 밝힘. 메가스피드는 직접 방문해 점검했고 전용을 찾지 못했다고 함. 슈퍼마이크로 공소장도 엔비디아의 위법을 주장하지 않음. (Fortune 11/10)
- 스파이 프레임 미확정: 미 법무부는 결론 내리지 않음. 트럼프 대통령도 아직 판단된 바 없는 것으로 안다고 답함. 싱가포르 당국은 범죄 증거 부족. 베이징은 근거 없는 주장이라고 반박. (ABC) 엔비디아 이사회는 국가안보나 회사 기밀이 침해됐다고 볼 근거가 없다고 밝힘. (Axios https://www.axios.com/2026/11/08/nvidia-ceo-jensen-huang-admits-affair-board-to-launch-investigation , Fortune 11/16)
- 우회와 위법은 다르다: 해외 데이터센터 임차는 11월 16일 이전까지 미국 규칙 안.
- 베이징 정부와 중국 기업의 이해는 다르다: 베이징은 H200 대량 수입을 승인하지 않고 화웨이 어센드 같은 국산 칩 사용을 압박. (Fortune 11/16)
- 통제가 밀수를 낳는다는 주장: 체인센트리(ChainSentry) 그레그 토머스 CEO — 통제가 인위적 희소성을 만들고 차익이 밀수 동기. (Fortune 5/13) 미국외교협회 조슈아 커란츠윅 — 새 규칙이 말레이시아에 치명적일 수 있다. (Fortune 11/16) Epoch — 화웨이가 2026년 생산하는 AI 연산력은 엔비디아의 4% 미만. 조지타운대 CSET 한나 도먼 — 중국은 아직 수요를 자력으로 채울 능력이 없다, 규칙 개정만으로 밀수가 멈추지 않는다(집행 필요). (https://epoch.ai/topics/geopolitics , Fortune 11/16)

## 7. 맺음: 의회 증언과 후속 조치
- 젠슨 황은 추수감사절 전에 의회에서 증언하기로 함(비공개 유력). 하원 위원장 3명은 그와 중국 정보기관의 관계에 대한 브리핑 요구. 와이든 상원의원과 닐 하원의원은 H200 중국 판매 허용 결정 조사를 상무장관에게 요청.
- 젠슨 황 사임 나흘 뒤인 11월 16일 상무부는 원격 접속 규칙을 냄. 하원 위원장 3명은 수출통제 법안 4건의 신속 처리를 요구.
- 홍콩에는 허가받은 H200 약 60만 개. 중국 고객을 둔 해외 데이터센터에는 허가 취득까지 90일.

## 취재 메모(발췌)
- 블룸버그 3건·NYT·WSJ·FT·디인포메이션은 원문 미대조(검색 요약·2차 보도).
- TechCrunch는 밀수 규모를 '약 200만 개'로 썼지만 Epoch 원문 중앙값은 H100 환산 66만 개.
- WSJ 문서는 주문 기준이라 120억 달러를 '밀수액'으로 쓰면 틀림.
- A800·H800은 2023년 10월 이전에는 합법 수출품.
- 한국 접점: 한국은 11월 15일 팍스 실리카 '샌프란시스코 선언'에 서명한 파트너국(미취재).
- 그 밖의 출처: Tom's Hardware 원격 접속 규칙 https://www.tomshardware.com/tech-industry/artificial-intelligence/new-us-rules-aim-to-restrict-remote-access-to-ai-servers-and-infrastructure-seeks-to-combat-cloud-rental-workarounds-to-gpu-export-controls
