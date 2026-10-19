---
id: R-0244
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "P3-1"
version: v7.4.0
commit: 92f30b9c
status: awaiting_decision
---

# 결정 요청 — 도로·강 레이어가 골든 16컷을 바꾼다(D-0229 §2.1 (d)·§7)

## 쟁점
D-0229 는 골든 25컷 무변화를 요구했고 바뀌면 전후 컷을 올리라고 했다(§7).
도로·강 레이어(UF-106)를 기본으로 켜면 hormuz 골든 dark·light 각 16컷이 바뀐다(나머지 차이 = 버전 도장뿐, R-0243 §4).
근접 숏(w 3.3~6.4)에는 도로·강, w 13~24 숏에는 큰 강이 더해진다. 수도 상시는 골든 차이 0.

## 선택지
| | 내용 | 결과 | 위험 | 되돌리기 |
|---|---|---|---|---|
| A | 기본 켬 + 골든 기준선 갱신(phaseV740, expected_deltas `v740_roads_rivers` 16컷) | 모든 영상에 도로·강(UF-106 "이번 지도에도 적용") | 이 컨테이너는 main 도 V3 md5 를 못 맞춰 **새 md5 를 여기서 만들면 다른 환경에서 재현되지 않을 수 있다** — 기준선은 V3 를 재현하는 컨테이너에서 만들어야 한다 | 기준선 파일 되돌림 |
| B | 프로젝트 단위 끔: `direction stage_config.mercator.map_layers: [roads, rivers]` 기본 켬, 골든 hormuz 만 `[]`(사유: v3 골든 사용자 합격본) | 골든 바이트 불변, 새 영상 전부 켬 | stage_config 키 1개 추가(P10 레지스트리 검사 대상). 골든에는 영원히 도로가 없다 | 키 삭제 |
| C | 기본 끔, 영상이 켬 | 골든 불변 | 새 영상이 안 켜면 미보호(C12 3) — UF-106 재발 | 기본값 바꿈 |

## Opus 권고
**B.** 골든은 사용자 합격본(v3, MAP_REASON 처럼 dark 고정 사유가 이미 있음)이라 바이트 불변이 기본이고(①·C0 "되돌리면 안 되는 것" 에 준함), 새 영상은 기본으로 켜져 UF-106 장치가 유지된다(C12 3). A 는 기준선 재현 환경 문제(§4)가 먼저 풀려야 해 지금 고르면 되돌리기 비용이 크다.

## 근거
- R-0243 §4 화소 비교(같은 컨테이너·같은 자산, main 372be03 대 브랜치 92f30b9c, 도로·강 끈 렌더로 분리).
- 시트: `docs/handoff/reports/phaseV740/golden_dark_before_after.jpg`·`golden_light_before_after.jpg`·`p_0006.95_roads_crop_x2.png`.

## 막히는 범위
- 막힘: 골든 e2e 두 테스트의 기준선 처리, 전체 pytest 판정(E).
- 계속: B 원고 v2(게이트 ① 사용자 검토 대기), C 연출 준비(diesel 은 dark, 도로·강 켬).

## §7 해당 여부
v3 합격 수치 변경에 해당(README §7.2 "유지가 기본, 바꾸려면 decision_request") — Fable 전결.
