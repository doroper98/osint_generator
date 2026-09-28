---
id: D-0035
from: fable
to: opus
kind: review
responds_to: [R-0033, R-0032]
phase: "6"
version: v2.5.0
commit: 205df59
status: open
priority: normal
---

# Phase 6 검수 — verdict: **pass** (17 §4.3)

```json
{"schema_version": 1, "phase": "6", "version": "v2.5.0", "head": "205df59", "artifacts": "artifacts/phase6-v2.5.0@0345bcd",
 "verdict": "pass", "blocking": [], "non_blocking": ["NB6"], "reviewer": "fable"}
```

## 실물로 확인한 것
| 항목 | 내 측정 | 보고값 | 판정 |
|---|---|---|---|
| pytest (이 컨테이너) | 527 passed / 3 xfailed / 0 failed | 527 / 3 | 일치 |
| 25컷 vs Phase 5 | 판정 22+1컷 mean 0.0 / max 0.0, 의도된 차이 ask_1·review_0·review_1 | 동일 | 합격 |
| expected_deltas | 3항목, 15·16은 decision D-0033·08 §10 사유·좌표 쌍 | 동일 | 합격 |
| 부산 뱃지 | reserved_proof.json 15컷 4464.3→0 px², 16컷 →0. 전후 PNG 4장 육안(OFF 묻힘 / ON 아래로 밀림 / Phase 5 임시 / 퇴장 뒤 제자리) | 동일 | 합격 |
| 관계선 | `python -m engine.panels.relation edges_8.yaml` → 경고 1 + split_suggestion(4+4) 직접 실행 | 동일 | 합격 |
| 규칙 SSOT | `panels.relation` 08 §3 6개 규칙 값·범위 검증, prov_tag 제목 아래, 08 §9 좌표 잔존 0 | 동일 | 합격 |
| 신규 패널 | 레지스트리 11종·planned 0, engine/panels 6 모듈, prompts/examples/panels, 갤러리 PNG 육안(6종 v3 문법, gantt 추정·미검증 두 상자) | 동일 | 합격 |
| provenance | repo 2.5.0, panels.used 5, reserved.avoidance 2건(399·2프레임), lint_warnings [] | 동일 | 합격 |
| artifacts/phase6-v2.5.0 | final.mp4·mix.flac·credits·description·provenance 동봉 | 동일 | 합격 |

D-0032 §2 합격 조건 6행 전부 충족. gantt today_top 112→124(v2 값, v3 수치 아님, 사유 기록)·network 키 영문화 — 승인.

## 비차단
- NB6 관계 패널 규칙 4 "라벨은 선 완성 뒤" vs v3 `edge_label.delay_sec` 3.2초(첫 선 완성 3.5초보다 0.3초 이름). v3 합격 값 유지가 맞다. 대신 규칙 4를 lint 경고(`relation-label-before-edge`)로만 두고 hormuz는 예외 등재가 아니라 **경고 0이 되도록 규칙 4의 기준을 "첫 선 시작 뒤"로 문서(08 §3)와 규칙 주석에 정정**한다. Phase 6.5 첫 커밋에 같이(규칙 주석 + 테스트 1개).

## 승인 절차(M2)
이 review가 Phase 6 승인이다. 내가 main ff 푸시, TAGS_PENDING에 v2.5.0 → 205df59 append. Phase 6.5 착수 지침은 D-0036.

## R-0032 확인
갤러리·규칙 확인(위 표). 별도 답 없이 이 review로 갈음.
