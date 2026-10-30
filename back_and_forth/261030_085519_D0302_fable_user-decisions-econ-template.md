---
id: D-0302
from: user
to: opus
kind: decision
responds_to: [R-0288]
phase: "E3"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 결정 — 경제 템플릿 다섯 항목(D-0278 §8) 답

사용자 원문(2026-10-30, 감독 세션 대화):
> "1. 전부 허용해. 2. A 3. 여기서 말한 길이는 데모용 길이를 말하는거야? 4. 여기서 말하는것도 데모용을 말하는건가? 5. B. 영상에 어떤 주제의 템플릿으로 만든 영상인지 알 수 있게 텍스트로 넣어줘."

## 효력
1. **도메인 허용**: 사용자가 환경 네트워크 설정에 추가한다(news.samsung.com · images.samsung.com · www.samsung.com · dart.fss.or.kr · opendart.fss.or.kr · www.sec.gov · www.intc.com · d1io3yog0oux5.cloudfront.net · query1/query2.finance.yahoo.com · www.thelec.kr). 구현은 **새 세션 컨테이너에서만 정책이 적용**될 수 있으니(지난 선례: brightcove), 허용 뒤 curl 로 재확인하고 안 되면 R 에 적는다 — 감독이 세션 재기동을 판단.
2. **주가 출처 = A Yahoo chart API**(`query1.finance.yahoo.com/v8/finance/chart/<ticker>`), 라이선스 `private_only_market_data`(비공개 시청, D264). 시간외 값은 press_cited.
3·4. 사용자 질문("데모용 길이·구성인가?") → **감독 답**: 데모가 아니라 **템플릿의 기본값**이다(삼성·인텔 편은 템플릿 첫 실증). 감독 제안 기본값: 한 회사 = 한 편, 2.5~3.5분(order.yaml 이 덮어쓸 수 있음), 두 편을 잇는 공통 고리 컷은 이번 짝에만. **사용자 확인 전까지 이 기본값으로 진행**(되돌릴 수 있는 선택 — 길이는 원고 단계에서 바뀐다).
5. **새 요소 승인 = B(요소마다 따로)**: 막대(쌓임)·예상치 표식·가이던스 띠·워터폴·생키 — 각각 실제 렌더 스케치 1~2컷을 따로 올리고 감독이 하나씩 사용자에게. 한 요소가 막혀도 다른 요소는 진행.
   **+ 템플릿 표시 텍스트(UF-147)**: 영상 안에 "어떤 주제의 템플릿으로 만든 영상인지" 글자로 넣는다. 자리: **타이틀 카드 부제 줄**("실적 발표 템플릿 · 삼성전자 2026년 3분기" 식)과 **엔딩 카드 한 줄** — 모서리 금지(C0: 모서리에는 날짜만). 장르 프로필이 `template_label` 을 가지면 코드가 조판하고, 없으면 `[template-label-missing]` hard. 쇼케이스 두 편(showcase_geo·econ)도 같은 줄("쇼케이스 템플릿 · 지경학/경제")을 갖게 한다 — 쇼케이스 트랙 세션 3 에 별도 통보.
