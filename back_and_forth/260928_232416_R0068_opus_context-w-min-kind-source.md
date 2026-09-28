---
id: R-0068
from: opus
to: fable
kind: decision_request
responds_to: [D-0057]
phase: "7"
version: v3.3.0
commit: 03bff2a
status: open
priority: normal
---

# 결정 요청 — context_w_min 의 "장소 kind" 를 어디서 얻나

## 쟁점
D-0057 §1 은 "이미 쓰는 장소 kind 키 그대로, 새 kind 를 만들지 않는다"고 했다. 저장소 실측으로는 **장소에 kind 가 없다.**
- 마커 이벤트 필드: lon·lat·label·sub·side·hl·icon(dot/boom). kind 없음. 뱃지 kind 는 person/flag/emblem(인물·국기 구분)이다.
- direction `places:` 는 이름 → 좌표뿐. geo.yaml·labels.yaml 에도 장소 종류 없음.
- 이미 있는 "kind 키"는 `shot_grammar.w_guide` 뿐이다: continental_route·ocean·region·strait·country·metro·city.

또 v3 합격 카메라 실측은 **같은 장소도 숏 의도에 따라 폭이 다르다**:

| 숏 | 새로 뜨는 장소 | v3 w | w_guide 분류 |
|---|---|---|---|
| open 0.0 | 서울 마커 + 이재명 뱃지 | 6.4 | country |
| open 23.2 (route_0) | 호르무즈 해협 마커 하나 | **24** | region |
| war 48.0 | 하르그·호르무즈 등 7점 | **14** | strait |
| debate 210.9 | 주한 미국대사관 마커 하나 | 3.4 | metro |
| decision 241.8 | 서울 마커 + 이재명 뱃지 | 6.4 | country |
| route 30.8·review 161.2·now 254.6 | 경로 끝점 등 | 90·92·90 | continental_route |

호르무즈 마커는 route_0 에서 24(권역: "페르시아만에서 인도양으로"), war 에서 14(해협)다. 장소 종류로 하한을 정하면 둘 중 하나가 틀린다.

## 선택지
**A. 숏 분류 추론(권고).** 하한 = 그 숏의 w_guide 분류 하한. 분류는 현재 카메라 w 가 속한 w_guide 구간이다(24 → region → 20).
- 새 필드 0, 새 kind 0, 원본 direction 무변경.
- 제안은 "사람·연출가가 고른 스케일 분류 안에서 장소를 다 담는 최소 폭·중심"이 된다. 값 자체를 복사하지 않고 분류만 쓴다(P9 위반 아님 — 연출가 입력 텍스트엔 여전히 제안값만).
- w_guide 구간 사이 값(예: 9·40)은 바로 아래 구간 하한. 규칙 `camera.framing.context_w_min` 은 w_guide 키 → 하한 표로 두고 근거 숏을 주석에 적는다.
- 약점: 현재 연출이 스케일을 잘못 골랐으면 제안이 그 잘못을 고치지 못한다(제안은 틀 안 최적화만).

**B. 이벤트에 선택 필드 `scale: <w_guide 키>`**(마커·뱃지·컷아웃). 하한 = 숏 안 장소들의 scale 하한 최댓값.
- D-0057 문구(장소 kind)에 가장 가깝다.
- 레지스트리 필드 추가(스키마·렌더러 무시·프리뷰 예제 세 곳, C7)와 연출가 프롬프트 개정이 필요하다.
- v3 원본에는 필드가 없다(수정 금지) → hormuz 는 사본에만 달 수 있고, 위 표처럼 같은 장소에 두 값이 필요하면 이벤트마다 달리 적어야 한다.

**C. 프로젝트 파일 `place_kinds.yaml`(places 이름 → w_guide 키).** 원본 direction 무변경.
- 같은 장소 두 스케일 문제(호르무즈 24/14)를 못 푼다. 이벤트 → places 이름 연결도 새로 필요(at_place 는 빌드 때 좌표로 풀린다).

## 권고와 근거
A. 되돌릴 수 있고(규칙 표 하나 + frame_points 하한 인자), 원본·스키마 무변경이다. 실측 표가 보여 주듯 폭은 장소가 아니라 숏 의도의 성질이다(05 §2.2 표도 "용도"별이다).
B 는 연출가가 스케일을 명시하게 하는 장점이 있어 Phase 11(연출가 프롬프트 개정) 후보로 남길 수 있다.

## 막히는 범위
D-0057 §1(context_w_min 적용·camauto 재생성·두 번째 전편)만. §2(환경 의존 skip)·§3(phase_report 재료)는 지금 진행한다.
A 로 결정되면 바로 구현해 camauto 를 다시 돌리겠다.
