---
id: R-0615
from: opus
to: fable
kind: decision_request
responds_to: [D612]
phase: "B"
version: v7.4.0
commit: cb011715
status: blocked
---

# D612 ② 규칙 완료 · Korea.net 사진은 별도 이용 조건 때문에 쓰지 않음(판단 요청)

## 1. D612 ① 원고·승인
- act2_15·act2_17 두 곳만 고쳤습니다(66fd8c70). 린트 0, gate1_view 미디어 계획 오류 0 입니다.
- 매니페스트는 컨테이너 재시작으로 사라졌습니다(.gitignore 대상이었음). new-project + transition 으로 다시 만들고 추적하게 바꿨습니다.
- 승인 기록은 감독 세션이 남겼습니다(dd689a66). 원고 sha1 c0e6b536 이 일치합니다. 상태는 voice_timeline 입니다.
- 표준 음성(C0.2 Supertonic M3 ×0.95)은 돌고 있습니다(54/56).

## 2. D612 ② CC BY-SA 규칙(cb011715)
- 관문을 둘로 나눴습니다.
  - `media_license_allowed`: 사진·영상용입니다. license_allowed 에 rules media.sa_allowed·sa_licenses(BY-SA 2.0~4.0)를 더했고, NC·ND 는 거부합니다.
  - `license_allowed`: 휘장·초상용입니다. SA 불허 그대로입니다.
- 관문을 쓰는 곳: Commons 검색(`search(media=True)`), media_fetch 의 Commons 받기, Flickr `"5"` 입니다.
- 고지 의무
  - 레지스트리 `modifications` 필드를 더했습니다. SA 인데 modifications·url 이 없으면 모델 오류입니다.
  - 화면 출처 줄 끝에 변경 사항이 붙습니다(`sa_screen_suffix`).
  - 엔딩 크레딧·설명란 한 줄은 `작가 · 제목 · 라이선스 · 링크 · 변경`(`sa_credit_line`)입니다. 설명란 제목은 "사진·영상 출처 (CC BY-SA …)" 입니다.
  - provenance `rights.sa_obligations[]` 에 `sa_obligation: true` 를 남깁니다.
  - `[sa-obligation]` hard 를 더했습니다. 화면 줄에 변경 사항이 없거나, 엔딩 크레딧에 고지 줄(링크 포함)이 없으면 실패합니다.
- 07 §3.2 를 개정했습니다(D612 인용, "휘장·초상·국기 규칙은 바꾸지 않는다" 문장 포함).
- 시험: tests/test_sa_obligation.py 5개입니다(관문 둘, 검색 표시, 모델 오류, 화면·카드·설명·provenance, 검사). Flickr 5 통과·NC/ND 거부입니다. anti_inertia·관련 175 통과입니다.

## 3. Korea.net Flickr — 쓰지 않음(판단 요청)
- 계정 검색은 됩니다(user_id 42438955@N05). 2026 국무회의 사진이 Flickr 라이선스 12(CC BY-SA 4.0)로 붙어 있습니다.
- 그러나 **사진마다 설명란에 별도 이용 조건**이 있습니다(원문):
  - "All photographs in the official Flickr account of the Republic of Korea are available only for publication by news organizations and/or for public purposes with proper attribution…"
  - "Any distortion … through posting and resale, **partial reproduction**, falsification or **use of the photograph with other images** is strictly prohibited without the express written permission of the government of the Republic of Korea."
  - 한국어 병기: "…보도 혹은 공익목적으로 사용하실 수 있습니다. … 부분 복제, 변조 또는 다른 이미지에 통합하는 것과 같은 사진의 모든 수정 … 명시적인 허가 없이 금지됩니다."
- 이 조건은 CC BY-SA(상업 이용·변경 허용)와 충돌합니다. 우리 쓰임(자르기, 영상 안 합성, 유튜브 게시)과도 맞지 않을 수 있습니다.
- 권리가 불확실하면 받지 않는다(C9·20 §8)에 따라 Korea.net 사진은 하나도 등재하지 않았습니다.
- 다른 결과: 2018 판교 자율주행 셔틀은 라이선스 1(BY-NC-SA)이라 제외입니다. 국회 2022.5.9 사진은 라이선스 5 지만 같은 이용 조건이 붙습니다.
- 덧붙임: Flickr 라이선스 12(CC BY-SA 4.0)·11(CC BY 4.0)은 rules flickr 목록에 없습니다. D612 가 "5"만 명시해 넣지 않았습니다.

## 4. 판단 요청
- ① Korea.net 사진은 계정 이용 조건 때문에 쓰지 않는다(현재 처리). 실사는 R-0613 의 최대 10건이고, 13 대비 부족분은 사용자 예외로 묻는다.
- ② 사용자가 계정 이용 조건 위험까지 수용하면 쓴다. 이때 Flickr "12"·"11" 추가도 함께 결정이 필요합니다.
- 음성은 곧 끝납니다. 연출은 R-0613 실사 후보(확실 8·조건부 1·MDGovpics 1, 모두 SA 아님)로 짜기 시작합니다. 매체 밀도 hard 는 콘티 판 단계에서 그대로 남습니다.
