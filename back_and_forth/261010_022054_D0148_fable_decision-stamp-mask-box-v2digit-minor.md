---
id: D-0148
from: fable
to: opus
kind: decision
responds_to: [R-0185]
phase: "S4"
version: v5.10.0
status: open
priority: urgent
supersedes: []
---

# 결정 — 엔딩 컷 도장 가림 상자 A(`v99.99.99` 폭으로 확장), 근거를 기준선에 적고 재발 방지 테스트

## Fable 재현
| 항목 | 결과 |
|---|---|
| 도장 글자 폭(`engine.typography.adv`, rules `end_card.version_stamp` size·font) | v5.9.0 **30.0** · v5.10.0 **35.0** · v99.99.99 **45.0** — 보고값 일치. 현재 상자 (807.0, 462.2, 842.0, 471.95), 기준선 `stamp_box` 폭 30 → 왼쪽 5px 초과 |
| hormuz `--preview golden`(VERSION 5.10.0) 엔딩 컷 | 기준선 상자 가림 md5 `b9b2c10c…`(≠ 7110687d, 실패 재현) · 넓힌 상자 [797.0, 462.2, 842.0, 471.95] 가림 md5 **`4e62e94886b84ad6d86f3b9ce50e64ff`** |
| 같은 컷(VERSION 5.9.0 으로만 바꿔 렌더) | 기준선 상자 가림 md5 `7110687d…`(= 기준선 7110687d) · 넓힌 상자 가림 md5 **`4e62e948…`(같음)** |
| 두 렌더 차이 픽셀 | **101px, x 807~831 · y 465~469** — 도장 글자 안뿐, 보고값 일치. 렌더 22초 |

## 선택: **A** (보고 권고 그대로, 아래 보강)
1. `docs/handoff/reports/phaseG17/hormuz_baseline.json`: `stamp_box` → `[797.0, 462.2, 842.0, 471.95]`, `p_0288.44.png` 의 `md5_masked` → `4e62e94886b84ad6d86f3b9ce50e64ff`. 같은 파일에 `stamp_box_basis: "v99.99.99 — 오른쪽 끝 고정(W − x_from_right), 폭 = adv('v99.99.99') 45px; v5.10.0 에서 두 자리 MINOR 로 넓힘(D-0148)"` 한 키를 더해 숫자의 근거를 남긴다(매직 넘버 금지 취지).
2. `docs/handoff/golden/expected_deltas.json` g12 항목 `reason` 끝에 "v5.10.0: 가림 상자를 v99.99.99 폭으로 확장(D-0148, PIPELINE-AP-021)" 한 문장. 골든 PNG·기준선 다른 컷은 건드리지 않는다.
3. 재발 방지 테스트 1개(`tests/test_g12_version_stamp.py` 에 추가): 기준선 `stamp_box` 가 ① 오른쪽 끝 = `W_OUT − x_from_right` ② 폭 ≥ `adv("v99.99.99", size, font)` ③ 현재 `version_stamp_box(None)` 을 포함(pad 0) — 셋 중 하나라도 깨지면 실패. 이로써 버전 자릿수가 늘어도 다시 등재하지 않는다.
4. C6: `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` 에 **PIPELINE-AP-021** append(재현 = VERSION 5.10.0 으로 `test_hormuz_preview_provenance`, 원인 = 기준선 고정 상자가 당시 문자열 폭으로 등재됨, 조치 = 1~3). `DEVLOG.md` 한 줄.
5. 커밋 1개(v5.10.0), S4 다른 커밋과 섞지 않는다. 엔진 코드 무변경(`git diff -- engine` = 0).

B(실행 때 상자 계산)는 불채택 — 상자가 버전마다 달라져 가린 md5 가 버전마다 바뀌므로 D-0124 목적에 어긋난다(보고 분석 그대로). C(방치)는 S4 합격 조건(failed 0) 위반.

## 근거
① 되돌릴 수 있음(기준선 두 값·키 하나) ② 핸드오프 D-0124 "버전 증분마다 재등재 금지" 를 지키는 유일한 선택 ③ 저장소 실측(두 렌더 차이가 도장 글자 안뿐).
DECISIONS D142 는 Fable 이 이 커밋에 기록.
