---
id: R-0617
from: opus
to: fable
kind: progress
responds_to: [D616, D617, 감독 04:02Z 점검]
phase: "B"
version: v7.4.0
commit: 4157f6c2
status: awaiting_user
---

# 국회·세종청사 실사 확보 — 변형 A 사전 검사 hard 0·실사 11

## 0. 기한 누락
- 03:40Z 보고를 놓쳤습니다. 5분 감시가 계속 429 를 받는 동안 다음 단계로 넘어가지 않았습니다. 감시는 15분 간격으로 바꿨습니다.

## 1. Openverse(60초 제한, 검색어당 1회)
- "National Assembly Proceeding Hall Seoul": 200(48초). Flickr 개인 계정 CC BY-SA 2.0 만 나왔습니다. 정부·군 공식 계정 조건 밖이라 쓰지 않습니다.
- "National Assembly Building Korea": 200(35초). Commons 3건이 나왔습니다(BY-SA 4.0·3.0·3.0).
- "Government Complex Sejong": 1회차 500 → 검색어를 바꾼 "Sejong Government Complex" 1회는 200(7초)입니다. Commons BY-SA 4.0 여러 건과 Korea.net Flickr(D613 거부)가 나왔습니다.

## 2. 원본 쪽 재확인(Commons 파일 쪽 200 — 검색 API 만 429) → 원본 출처에서 받기
| mid | 파일 | 촬영 | 작가 | 라이선스 | 별도 조건 |
|---|---|---|---|---|---|
| bud_assembly_ext_2014 | National Assembly Building of the Republic of Korea.png | 2014-09-08 | clumsyforeigner(Own work) | CC BY-SA 4.0 | 없음 |
| bud_sejong_complex | Government Complex Sejong (N).jpg | 2015-03-19 | Minseong Kim(Own work) | CC BY-SA 4.0 | 없음 |
| bud_mohw | Ministry of Health and Welfare(South Korea).JPG | 2014-12-05 | Minseong Kim | CC BY-SA 4.0 | 없음 |
| bud_motie | Ministry of Trade, Industry and Energy(South Korea).JPG | 2014-12-02 | Minseong Kim | CC BY-SA 4.0 | 없음 |

- 2010·2007 국회 사진은 15년을 넘어 뺐습니다.
- 받기는 upload.wikimedia.org 표준 폭 1280 이고 200 으로 받았습니다. 레지스트리 등재: modifications "자르기·크기 조정·색 보정", source_hash 를 기록했습니다.
- 눈 확인: 국회 외관 정면(돔·잔디)입니다. 세종청사는 원경(청사 + 아파트 단지)입니다. 두 부처는 청사 외관입니다.

## 3. 변형(렌더 안 함 — 사전 검사만, `direction.vA.yaml`·`direction.vB.yaml`)
- **A**(권장): 배경 cold = 국회, act1 = 세종청사, act2 앞 = 산업통상자원부, act2 뒤 = 서해안고속도로, act3 = 웨이퍼, act4~ending = 국회입니다. 지하철·아파트·셔틀 배경은 뺐습니다(셔틀은 act2_11 사진, 아파트는 act2_15 사진으로만).
  - act4_0("10월 말 예정처 … 세 가지 논의", 숫자 없음)은 국회 사진입니다. 구성 무대는 act4_1 부터입니다.
  - **실사 11 / 11(분당 1.63)**, 사전 검사 hard 0, warning 5 입니다.
- **B**: 주제 어긋난 배경 3개를 빼고 무대 바탕입니다. **실사 7 / 11(분당 1.04)**, hard 1([media-density]).
- 현재 direction.yaml 은 D616 ①② 반영본 그대로입니다(실사 10). 재승인·흐름 의견 뒤 A 를 direction.yaml 로 올리고 렌더합니다.
- 보건복지부 청사 사진(bud_mohw)은 등재만 했고 쓰지 않았습니다. act2_17 은 구직급여·모성보호(고용노동부 소관)라 대상이 어긋납니다.

## 4. 대기
- 사용자 흐름 의견 + act5 날짜(2026.12.02 → 11.03) 게이트 ① 재승인입니다. 그 뒤 렌더합니다(콘티 판 v2 → 프리뷰).
