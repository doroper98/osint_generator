---
id: R-0123
from: opus
to: fable
kind: decision_request
responds_to: [D-0105, R-0122]
phase: "G6.5"
version: v4.7.0
commit: 5f97401
status: in_progress
---

# G6.5 결정 요청 — 엔딩 카드 넘침: 롤(dmz 브랜치) vs 오류(G5 D-0098), 크레딧 인물 표기

D-0105(G6 합격) 확인했습니다. 병합은 0fb7e6d·5f97401 로 올렸습니다(DECISIONS: 그 브랜치 D87 → **D95**, Fable D94 와 겹쳐서).
vibrant-mendel 브랜치에는 R0111·R0112 말고 **R0113(엔딩 카드 보고)** 도 있었습니다. D-0104 에 없던 파일이라 다음 빈 번호 **R-0122** 로 옮겼습니다(R-0120·R-0121 은 이 세션이 씀).

## 쟁점 1 — 크레딧이 한도를 넘을 때

두 브랜치가 같은 문제를 반대로 풀었습니다.
- G5(D-0098 §2, Fable 결정): 넘치면 `EndCardOverflowError`, checks `[endcard-overflow]` hard. credits.yaml 을 고쳐야 렌더된다.
- vibrant-mendel(그 세션 D87 → D95): 넘치면 2.5초 멈춘 뒤 목록 전체가 위로 흐르는 롤(`scroll_top 140 ~ scroll_bottom 424`, 가장자리 18px 페이드, 끝 2초 멈춤). 잘림은 없다.
- dmz_mine_2026 실측(R-0122 §1): 오른쪽 열 바닥 752px, 왼쪽 449px, 한도 약 428~436. 열 재배치·절 합치기로는 들어가지 않는 양입니다(보도 19줄).

**병합에서 한 일**: 충돌이라 G5 오류 방식을 그대로 두고 롤 코드·`scroll_*` 키 5개를 뺐습니다. `hold_black_after`(카드 뒤 영상 끝까지 검정)는 충돌 밖이라 반영했습니다. 되돌리기 쉬운 쪽(현 상태 유지)입니다.

- **1-A**: G5 오류 유지. dmz 는 크레딧을 줄여야 렌더된다(예: 보도 목록을 설명란으로만). 영상 쪽 코드 변화 없음.
  - 위험: 긴 보도 목록이 필요한 영상(다국 매체 비교)마다 크레딧을 손으로 줄인다.
- **1-B**: 넘치면 롤. `[endcard-overflow]` 는 hard 에서 기록(provenance `end_card.roll_px`)으로 바꾼다. 넘치지 않는 영상(hormuz·fed_policy·랫클리프·데모)은 모양이 같다.
  - 위험: 롤 속도 상한이 없어 아주 긴 목록은 읽을 수 없게 빨리 흐른다.
- **1-C (권고)**: 롤을 받되 상한을 둔다. 롤 속도(px/초)가 규칙 상한(예: `end_card.scroll_max_px_per_sec`)을 넘으면 G5 와 같은 오류. 조용한 넘침·읽을 수 없는 롤을 둘 다 막는다.
  - 근거: 판정 기준 ① 되돌리기(규칙 값 하나로 1-A·1-B 양 끝), P6(잘림 없음). dmz 752−424 = 328px 를 카드 11초 중 6.5초에 흘리면 약 50 px/s 입니다.
  - 상한 값은 실측으로 정할 몫입니다(숫자 권고: 60 px/s — 480p 기준 한 줄 14px 를 초당 약 4줄).

## 쟁점 2 — `auto: people` 크레딧이 파일명·id 를 표기(R-0122 §1 끝)

그 세션은 dmz credits.yaml 을 수동 행으로 바꿔 피했습니다. 다른 프로젝트도 같은 결함이 있습니다(hormuz 는 people 절을 수동 행으로 씀 — 확인 필요).
- **2-A**: 권리 레지스트리 people 에 `name` 추가(스키마 변경, 기존 레지스트리 재생성).
- **2-B (권고)**: `auto: people` 이 `assets/entities.yaml` 의 표기 이름을 쓴다. 이름의 SSOT 가 이미 entities 이므로 새 필드가 없다. entities 에 없는 인물 = 오류(조용히 id 를 쓰지 않음, P6).

## 그 밖의 보고

- **dmz 프리뷰 6컷(D-0104 §3)**: 이 컨테이너에는 dmz 의 plan.json·tts·초상·rights_registry 가 없습니다(D-0104 보존 경고 그대로). 프리뷰를 만들려면 `script.plan --tts edge`(음성 새로 생성, 원본과 다름)와 초상·권리 재수집이 필요합니다. 이 결정 전까지 dmz 프리뷰는 보류하고, 나머지 병합 작업(D2(a)·D2(b)·D3·D4·D5·S1)은 계속합니다.
- **post_limiter 재측정**: 병합 뒤 hormuz·fed_policy audio_qa 를 다시 재서 G6.5 보고에 넣습니다.

## 막히는 범위

- 결정 대기: 롤 코드 재반영 여부(쟁점 1), `auto: people` 수정(쟁점 2), dmz 프리뷰.
- 계속: D-0104 §2 커밋들, 회귀(hormuz 25/25 등), 오디오 재측정.
- §7 해당 없음.
