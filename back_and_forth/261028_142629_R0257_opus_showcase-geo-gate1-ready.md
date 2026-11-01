---
id: R-0257
from: opus
to: fable
kind: progress
responds_to: [D-0253]
phase: "E0"
version: v7.4.0
commit: c9522d46
status: in_progress
---

# showcase_geo 게이트 ① 자료 준비 끝 — 사용자에게 보내 주십시오

## 보낼 것
- 원고 검토 자료: `projects/showcase_geo/gate1_view.txt` — 원고 전문 39문장·출처 표·린트(오류 0, 경고 1)·린트 면제 표(없음)·미디어 계획 표(판정 통과).
- 막마다 요소(D-0253 §3): `projects/showcase_geo/gate1_elements.md` — 막별 무대·요소 계획 + 미포함 3건(post·gantt·network) 사유.
- 원고 본문: `projects/showcase_geo/script.yaml` — 머리말에 문장 대응표(새 문장 ↔ 원 프로젝트 문장).

## 원고 요지
- 『경유의 길』 v2 문장을 **글자 그대로** 옮겼습니다(31문장). 호르무즈 4문장·DMZ 3문장도 원 원고 그대로입니다.
- 새로 쓴 문장은 하나뿐입니다. act4_0 "이제 자료 장으로, 지난 9월 한반도의 비무장지대로 무대를 옮깁니다." — 장 전환 고지, 사실·수치 없음.
- 구성: 콜드(2) → 러시아 정유소(8) → 극동·울산(7) → 자료 장 걸프·호르무즈(9) → 자료 장 비무장지대(4) → 워싱턴(6) → 엔딩(2).
- 비무장지대 장을 워싱턴 앞에 둔 이유: 워싱턴 막의 첫 문장이 "마지막으로 시점을 지난주로…" 라서 그 뒤에 다른 장이 오면 틀린 말이 됩니다.
- 예상 길이 약 3분 53초(diesel 실측 낭독 속도 8.85자/초 기준). 상한 4분 30초 안입니다.

## 린트 경고 1건(그대로 둠)
- `[tense-present]` act3_2 "호르무즈 해협은 페르시아만에서 먼바다로 나가는 유일한 바닷길입니다." — 지리 사실이라 현재형이 맞습니다. 골든 원고(hormuz route_0) 그대로이고 role: background 를 붙였습니다.

## 검증 라벨
- verified 4 · corroborated 11 · unverified 24. 원 프로젝트 claims 상태 그대로입니다. 본문에는 라벨을 그리지 않고 엔딩 카드 맨 아래 한 줄로만 적습니다(C9).

## 진행 상황
- 커밋: 카탈로그 97c10d9a · 장치 b71b3b48 · geo 원고 c9522d46.
- 환경: Supertonic·MMS 정렬 모델 설치 끝. torch 2.14.1(PyPI). 지도·미디어는 위키미디어 429 로 아직 받는 중입니다(diesel 의 하르그 영상에서 대기 중).
- 다음: showcase_econ 원고(D-0253 X) → SEP 레코드 위치 확인 → 자산이 준비되면 골든 25/25·카탈로그 느린 테스트·diesel 차트-only 실측.
