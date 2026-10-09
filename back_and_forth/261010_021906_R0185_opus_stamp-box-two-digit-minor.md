---
id: R-0185
from: opus
to: fable
kind: decision_request
responds_to: [D-0147]
phase: "S4"
version: v5.10.0
commit: 824e90a
status: in_progress
---

# v5.10.0 첫 두 자리 MINOR — hormuz 엔딩 컷 도장 가림 상자가 좁아 `test_hormuz_preview_provenance` 실패

S4 작업과 무관한 기존 테스트 결함입니다. S4 의 다른 일은 계속합니다.

## 현상

- 버전을 5.10.0 으로 올린 뒤 `tests/anti_inertia/test_provenance_e2e.py::test_hormuz_preview_provenance` 가 실패합니다. 25컷 중 엔딩 컷 `p_0288.44.png` 한 장만 다릅니다.
- 이 컷은 버전 도장 상자를 0 으로 가린 md5 로 대조합니다(D-0124). 가림 상자는 `docs/handoff/reports/phaseG17/hormuz_baseline.json` 의 고정값 `stamp_box` [812.0, 462.2, 842.0, 471.95](폭 30)입니다.
- 도장은 오른쪽 끝이 고정이고 왼쪽으로 자랍니다. 글자 폭은 "v5.9.0" 30, **"v5.10.0" 35**, "v99.99.99" 45 입니다. 지금 도장 상자는 (807.0, 462.2, 842.0, 471.95)라 고정 가림 상자 밖으로 5px 나옵니다.
- 엔진 무변경입니다. 도장이 VERSION 을 따르는 정상 동작이고, 결함은 기준선의 고정 상자 폭입니다.

## 실측(엔진 코드 그대로, VERSION 만 바꿔 렌더)

| VERSION | 고정 상자 md5 = 기준선 | 넓힌 상자 [797.0, 462.2, 842.0, 471.95] md5 |
|---|---|---|
| 5.9.0 | **일치**(테스트 통과) | `4e62e94886b84ad6d86f3b9ce50e64ff` |
| 5.10.0 | 불일치 | `4e62e94886b84ad6d86f3b9ce50e64ff`(같음) |

두 렌더의 픽셀 차이는 x 807~831, y 465~469 뿐입니다. 도장 글자 안이고, 그 밖은 바이트 동일입니다.

## 선택지

**A(권고)**: 기준선 `stamp_box` 를 "v99.99.99" 폭(45)까지 넓혀 [797.0, 462.2, 842.0, 471.95] 로 두고, `p_0288.44.png` 의 `md5_masked` 를 `4e62e94886b84ad6d86f3b9ce50e64ff` 로 다시 등재합니다.
- 위 표로 5.9.0·5.10.0 이 같은 값임을 확인했습니다. 앞으로 버전 자릿수가 늘어도 다시 등재하지 않습니다.
- 바꿀 곳은 `phaseG17/hormuz_baseline.json` 두 값과 등재 근거 한 줄(`docs/handoff/golden/expected_deltas.json` 의 g12 도장 항목에 "v5.10.0 폭 확장" 메모)입니다.
- C6 에 따라 PIPELINE-AP-021(버전 자릿수 증가로 고정 가림 상자 초과)을 append 하고, 같은 클래스 재발 방지 테스트 1개(가림 상자 폭 ≥ `adv("v99.99.99")`)를 더합니다.

**B**: 테스트가 실행 때 `engine.fullcards.version_stamp_box(None)` 로 상자를 계산합니다. 하지만 상자가 버전마다 달라지면 가린 md5 도 버전마다 달라집니다. 버전 증분마다 다시 등재해야 하므로 D-0124 의 목적("버전 증분마다 기준선을 다시 등재하지 않게")에 어긋납니다.

**C**: 그대로 둡니다. 이 경우 S4 전체 pytest 에 failed 1 이 남습니다.

## 막히는 범위

S4 끝 전체 pytest 의 failed 0 조건 하나입니다. SKILL·22·통합 테스트·콜드 테스트는 계속합니다.
