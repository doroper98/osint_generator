---
id: R-0297
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "US1"
version: v7.4.0
commit: HEAD
status: open
---

# 결정 요청 2건 — ① 골든 e2e 의 badge_hold hard ② "확정(called)" 의 기준

## ① hormuz 골든 연출이 badge_hold(UF-162) hard 3건으로 렌더 rc 1
- **쟁점**: `tests/anti_inertia/test_provenance_e2e`·`test_q3_light_e2e` 가 렌더 rc 0 을 먼저 본다. 1d462eb(UF-162 장치)가 hormuz 골든 연출의 짧은 뱃지('울산' 1.6초·'중국' 4.6초·'인도' 4.2초)를 hard 로 잡아 두 테스트가 실패한다. 픽셀은 25/25 일치(R-0296).
- **선택지**
  - A. `qa_checks.badge_hold` 에 `exempt_projects: [hormuz_korea]`(element_gap·chart_only_run 과 같은 방식, v3 골든 = 사용자 합격본) + 테스트. 되돌리기 = 목록에서 지움.
  - B. 골든 direction 의 뱃지 t1 을 늘린다 → 25컷 중 일부 픽셀이 바뀌어 기준선 재작성(사용자 합격본 변경 — C0 되돌리면 안 되는 것과 충돌 위험).
  - C. 그대로 두고 이 트랙 범위 밖으로 기록(골든 e2e 계속 실패).
- **Opus 권고 A** — ① 되돌릴 수 있고 ② D511 이 element_gap 에 같은 면제를 둔 선례 ③ 골든은 회귀 기준(화소)이라 새 연출 규칙의 대상이 아니다(C0).
- **막히는 범위**: 없음(이 영상은 badge_hold 를 지킨다). 최종 R 의 anti_inertia 수치에만 영향.
- §7 사용자 고유 결정 아님.

## ② "확정(called)" 의 기준 — AP 콜만인가, NBC 결정데스크 추정 포함인가
- **쟁점**: D-0290 §4-1 "AP 콜이 있는 결과만 확정". apnews.com 은 컨테이너(403)·WebSearch(400) 모두 차단이라 AP 콜은 2차 보도 인용으로만 확인된다. 현재 `data/state_results.yaml` 은 뒤집힌 상원 5곳·주지사 4곳 등 주요 레이스의 called_by 를 "AP(NPR 등 인용)" 로, 나머지 안전한 레이스 다수를 "NBC 결정데스크 추정(projection)" 으로 적고 둘 다 status called 로 둔다(콜드 오픈 area 가 35곳을 칠하려면 필요).
- **선택지**
  - A. called = AP 콜(2차 인용) **또는** NBC 결정데스크 추정. called_by 에 주체를 그대로 적고, 엔딩 표기 행에 "확정 = 에이피·엔비씨 추정" 한 줄. 되돌리기 = 데이터 파일 status 일괄 변경.
  - B. AP 인용 확인된 곳만 called, 나머지는 counting(빗금) → 콜드 오픈 지도 대부분이 빗금(사실과 다른 인상 — 안전한 주도 미확정처럼 보인다).
  - C. 남은 safe 레이스마다 AP 콜 2차 인용을 찾는다(약 25건 WebSearch, 반나절) — 결과는 A 와 같은 그림.
- **Opus 권고 A** — 방송사 결정데스크 추정은 미국 선거 보도의 표준 '콜'이고 출처·주체를 데이터에 남기며, 실제로 결과가 안 난 4곳만 빗금이 된다(D-0290 §7 취지). 미확정 2곳(MS·AK)은 NBC 도 콜하지 않았다.
- **막히는 범위**: 연출 v1 의 cold area 색. 게이트 ① 원고 문장에는 영향 없음(원고는 "엔비씨 집계" 귀속).
- §7 아님.
