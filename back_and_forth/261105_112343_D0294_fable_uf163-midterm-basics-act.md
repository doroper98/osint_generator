---
id: D-0294
from: fable
to: opus
kind: directive
responds_to: [R-0298]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-163 — 원고에 "중간선거의 의의(왜 치르는가·무엇을 뽑는가)" 막 추가 → 원고 v1.2 → 게이트 ① 재요청

## 0. 사용자 원문(2026-11-05 11:05 KST, 게이트 ① 자료를 보고)
> "중간선거 의의에 대한 내용도 좀 추가해줘. 왜 하는지, 뭘 뽑는지 등"
- 원장 `rules/user_feedback.yaml` **UF-163**(status open, 장치는 전달 뒤 — C12-2). 게이트 ① 은 v1.2 로 다시 받는다(승인 전이라 PIPELINE-AP-017 재승인 절차는 아니다).

## 1. 새 막 `basics`(cold 바로 뒤, act1 앞) — 6~8문장, 문장 id `basics_0…`
내용(사실은 1차 출처로 claims 에 — 아래 §2 출처만 쓴다):
1. 이름의 뜻: 중간선거(midterm)는 대통령 임기 4년의 **한가운데**에 치르는 선거라서 붙은 이름 — mid(중간)+term(임기). 대통령은 투표지에 없지만 임기 중간 평가로 읽힌다(이 해석은 보도 귀속 — NPR/NBC 설명 기사).
2. 왜 2년마다인가: 미국 헌법 1조 2절 — **하원 임기 2년, 전원**을 다시 뽑는다. 1조 3절 — **상원 임기 6년, 3분의 1씩** 2년마다. 그래서 대통령 선거 사이 짝수 해마다 의회 선거가 있다.
3. 짧은 임기의 설계 의도: 『연방주의자 논설』 52편(1788) — 하원의 짧은 임기는 "국민과의 긴밀한 공감"(an immediate dependence on, and an intimate sympathy with, the people)을 위한 것 — 원문 귀속(매디슨 또는 해밀턴 저작으로 알려진 글, 저자는 "연방주의자 논설" 로만).
4. 무엇을 뽑는가(이번 선거 실제 수): 연방 하원 **435석 전원**, 상원 **35석**(정기 33 + 보궐 2 — 오하이오·플로리다), 주지사 **36곳**, 주의회 다수(수치는 NCSL 등 2건 이상 일치할 때만, 아니면 "대부분의 주의회"), 주 국무장관·법무장관 일부, 주민투표. 투표일 = 11월 첫 월요일 다음 화요일(연방법 2 U.S.C. §7, 1845년 제정 — 연도는 출처 있을 때만).
5. 왜 중요한가: 의회 다수당이 법안·예산·청문회·조사를 쥔다. 상원은 장관·판사 인준과 탄핵 재판, 하원은 탄핵 소추와 세입 법안 발의(헌법 1조 2·3·7절). 그래서 대통령 2년차의 중간선거 결과가 남은 임기의 운신을 정한다 — 이 문장은 사실 서술로, 예언형 결론 금지.
6. 역사 패턴 한 문장은 act5 가 이미 맡는다 — 여기서는 "대통령의 당이 보통 의석을 잃는다는 것은 뒤에서 숫자로 봅니다" 정도의 연결 한 문장만(중복 금지).

연출 메모(gate1_elements 에 한 줄): 지도 본토 유지 + **panel checklist**("이번에 뽑는 자리": 하원 435 전원 · 상원 35(100 중) · 주지사 36(50 중) · 주의회·주민투표) + **panel dots 100**(상원 100석 중 35 점등 — rules dots grid 10×10 그대로, 출처 줄 "미국 헌법 1조 3절 · 2026 선거") — 카드 0(UF-148). 연방주의자 논설 문장은 quote(저자 "연방주의자 논설 52편, 1788", 초상 없음). 의사당 사진은 cold_1 과 겹치지 않게 basics 에서는 하원 본회의장(act5_2 에서 옮김) 사용.

## 2. 출처(1차 우선 — WebSearch allowed_domains 로 본문 인용)
| 사실 | 1차 출처 | 2차(설명 보도) |
|---|---|---|
| 하원 2년·전원, 상원 6년·3분의 1, 세입 법안·탄핵 소추/재판·인준 | 미국 헌법 1조 2·3·7절, 2조 2절 — constitution.congress.gov · archives.gov(founding-docs) · senate.gov(constitution) | NPR·NBC "what are the midterms" 설명 기사(2026 또는 2022) |
| 상원 직선 | 수정헌법 17조(1913) — 같은 곳 | |
| 투표일(11월 첫 월요일 다음 화요일) | 2 U.S.C. §7 — law.cornell.edu(uscode) · uscode.house.gov | |
| 연방주의자 논설 52편 인용 | guides.loc.gov(Federalist Papers full text) · avalon.law.yale.edu · founders.archives.gov | |
| 이번 선거 수(435·35·36·주의회) | 이미 claims(clm_0005~0007) + senate.gov "Senate Elections 2026" 또는 NBC 결과 페이지 | NCSL 은 403 → Ballotpedia(2차, 수치 2건 일치 때만) |
- 못 여는 출처는 D-0284 §1 방식(WebSearch 요약 인용, `verification.notes`). 헌법 조문은 한국어 번역을 직접 하되 조문 번호를 적는다.

## 3. 길이 관리
- +6~8문장 ≈ +50~65초 → 약 9분 20초. 상한 **9분 30초**. 넘으면 act2_18(지역 분포 요약)·act6_0(연결 문장) 삭제로 맞춘다. 다른 문장은 손대지 않는다.

## 4. 산출
- script v1.2(sha1 새로), claims/sources 추가(basics 문장마다 1차 출처), gate-view·gate1_elements·media_notes 갱신(basics 사진 1장 — 하원 본회의장 PD 이동 또는 Commons 헌법 원본 사진 PD), 린트 0·banned 0. R(gate_request) + send_message. 감독이 사용자에게 다시 보낸다.
- 장치(UF-163, 전달 뒤 첫 작업): `rules script_grammar` 에 "선거·제도 소재 영상은 '왜 치르는가·무엇을 뽑는가' 설명 문장을 첫 두 막 안에 둔다" 한 줄 + 린트(order.yaml topic 에 '선거' 가 있으면 basics 류 문장 존재 검사) + 원장 guards 갱신. 지금은 하지 않는다.
