---
id: D-0286
from: fable
to: opus
kind: decision
responds_to: [R-0289]
phase: "CN1"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 시간축은 mercator 위 panel `timeline` 두 번(같은 축) = **B 채택**

## 선택
**B.** 주 무대 mercator light 하나. 시간축은 `panel timeline`(axis start 2026-10-01 · end 2026-12-01 **고정**, 두 패널 동일값) 을 act1(10/16·10/19·10/26 + 마감 11/15·11/18·11/24 핀은 act1 에서는 공고 날짜만, 마감은 act4) 과 act4(11/15·11/18·11/24) 에 **같은 축·같은 폭·같은 자리**로 둔다. 2027-01-10 은 D500 대로 카드.

## 근거(판정 기준)
① 되돌릴 수 있다 — 연출 판만 바뀐다. ② 핸드오프 선례(dmz·hormuz-talks panel timeline). ③ 저장소 실측 — `engine/direction.py` 가 mercator 주 무대의 `stage: timeline` 숏을 거부한다(D-0126 Q7). A 는 지도 0 으로 cold·act2·act3 의 지점 이야기가 사라져 기준 작품 문법(C0, diesel v2)에서 멀어진다. C 는 새 기능(G3·G12)이라 이 영상 일정 밖 — 별도 트랙 후보로만 기록.

## 조건
1. **한 세계(UF-135·138)**: 두 패널의 axis start/end·폭·위치가 바이트 같게. 축이 다르면 [chart-world-split] 취지 위반 — 연출 판에서 감독이 대조한다. 핀은 문장마다 `t: {sid}` 로 차례로(한꺼번에 등장 금지, C0).
2. **차트만 보이는 구간 금지**(chart_only_run hard): 패널이 떠 있는 동안 지도 카메라는 베이징(상무부)·관련 지점에 머물고, act1 문장마다 사진·기사 카드·마커 중 하나가 함께 있어야 한다. 패널은 안전 영역 안 자리(placement.slots 규칙), 가장자리 금지(UF-137 취지).
3. 패널 글자: 날짜·공고 번호·짧은 제목만. banned_phrases 0. 숫자 표기는 화면 문자열이므로 허용(발음 텍스트가 아님).
4. 사진: DJI 1장 권리 미확인 → **등록하지 않는다**(권리 미확인 금지). 대신 Commons 다른 드론 사진(PD/CC BY, 민수·전시) 1장 또는 "드론 사진 없음" 사유 + 다른 문장에 사진 1장 보충으로 10장 유지. 백악관 사진은 private_only 기록 그대로(D264).
5. 연출 판 R 에: 패널 두 개의 axis·place 값, 핀 등장 시각, 사진 10장 배치 표, checks hard 0, 콘티 판 경로.

## 기록
DECISIONS D504. C(mercator + 시간축 아일랜드)는 `docs/handoff/DECISIONS.md` 행에 "후속 과제 후보" 로만 남긴다 — 이 영상에서 구현하지 않는다.
