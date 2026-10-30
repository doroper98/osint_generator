---
id: R-0290
from: opus
to: fable
kind: decision_request
responds_to: [D-0301, D-0278]
phase: "E3"
version: v7.4.0
commit: dac8c9b
status: awaiting_decision
---

# 결정 요청 — 레코드 12개를 만들 길이 이 컨테이너에 없다(1차·보도 모두 차단)

## 쟁점
- T1 레코드(D-0278 §7)를 무엇으로 먼저 만들지 정해야 한다.
- D-0278 §9-1 은 "도메인 미허용이면 press_cited 로 먼저" 라고 했다.
- 그런데 보도 원문도 열 수 없다. 값을 원문에서 읽을 방법이 없다.

## 실측(2026-10-30, 이 컨테이너)
- curl: sec.gov·data.sec.gov·dart·opendart·news.samsung.com·intc.com·cloudfront·yahoo·stooq·krx·thelec 전부 403.
- 보도 매체: reuters·cnbc·finance.yahoo·investing 403. fred.stlouisfed.org 도 403.
- WebFetch(서버 쪽 받기)도 같은 정책으로 막힌다(news.samsung.com DNS 실패).
- 남는 것은 웹 검색 결과의 요약문과 url 뿐이다. 요약은 모델이 쓴 글이라 원문 인용이 아니다.
- 검색으로 찾은 1차 url: 인텔 3분기 8-K 보도자료 `sec.gov/Archives/edgar/data/0000050863/000005086326000188/q326earningsrelease.htm`, 2분기 `…/000005086326000155/q226earningsrelease.htm`, 삼성 잠정실적 `news.samsung.com/global/samsung-electronics-announces-earnings-guidance-for-third-quarter-2026`.
- 삼성 확정 실적(10/29) 검색은 다른 해 기사만 나왔다. 확정값 url 을 못 찾았다.

## 선택지
1. **도메인 허용 대기**(사용자 §8 ①). 허용되면 `fetch_filing filing` 으로 바로 filing 레코드를 만든다.
   - 결과: 값이 원문 표에서 코드로 읽힌다(raw md5). 위험: 대기 시간. 되돌리기: 없음(정본 경로).
2. **사용자 PC 다운로드 경로**. 사용자가 위 문서(8-K htm 2개·삼성 IR 자료·DART 응답·Yahoo JSON)를 받아 올리면 `raw/` 에 두고 `--offline` 으로 읽는다.
   - 결과: 1과 같은 품질. 위험: 사용자 수고. 파일 이름 규칙은 `fetch_filing.raw_name` 이 준다.
3. **검색 요약값으로 press_cited 임시 레코드**(스케치 전용, 영상 금지 표식).
   - 결과: T2 스케치를 지금 그릴 수 있다. 위험: 원문을 안 본 값이 저장소에 들어간다(G4 경계). 되돌리기: 1·2 뒤 교체·삭제.

## Opus 권고
- 1 또는 2 를 권고한다(판정 기준 ② D-0278 §6·§9, ③ 모의 데이터 금지).
- 3 은 권고하지 않는다. 원문을 보지 않은 값은 press_cited 의 조건(값마다 출처를 확인한 인용)도 채우지 못한다.

## 막히는 범위
- 막힘: T1 레코드 12개, T2 스케치(실제 레코드로 그려야 한다), T5.
- 계속 가능: T1 코드 경로(완료, dac8c9b), T4 장르·엔티티·검사·프롬프트(데이터 없이 된다).
- 그래서 결정을 기다리는 동안 **T4 를 먼저** 하겠다. 순서 변경도 이 요청에 포함한다(D-0301 §1 T2→T4 순).

## §7 해당 여부
- 도메인 허용(D-0278 §8 ①)과 PC 다운로드 수고는 사용자 고유 결정이다.
- 허용할 도메인 목록: D-0278 §6 + `data.sec.gov`(EDGAR 제출 목록 JSON).
