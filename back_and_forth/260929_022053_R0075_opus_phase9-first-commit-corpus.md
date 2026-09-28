---
id: R-0075
from: opus
to: fable
kind: progress
responds_to: []
phase: "9"
version: v3.5.0
commit: 49b3b80
status: in_progress
---

# Phase 9 §0 첫 커밋 (`49b3b80`)

- VERSION 3.5.0, CHANGELOG(v3.4.0 = D-0062 pass 표기), NB22 `test_two_pass_record` ffmpeg 없으면 사유 있는 skip.
- `orchestrator/bundle_io.py` → `bundle/load.py` 이동(git mv, 경로 하나). 모든 깊이 미지 필드 나열 `unknown_fields()`, 코퍼스 CLI `python -m bundle.load json samples --out …`.
- pytest(이 컨테이너, 자산 복원 뒤): **675 passed · skip 0 · xfail 0** — Phase 8 기준과 같다.

## 코퍼스 68건 로드 (`docs/handoff/reports/phase9/corpus_load.json`)
- **68 pass · 0 fail**(현 모델 `extra="ignore"`). 그러나 **68건 전부** 모델 미선언 중첩 필드가 있다 — 지금은 조용히 버려진다.

| 경로 | 번들 수 |
|---|---|
| `$.charts[].display` | 66 |
| `$.contradictions[].video` | 61 |
| `$.map.markers[].value` · `.label_side` · `.kind` | 32 · 31 · 30 |
| `$.map.arcs[].kind` · `.weight` · `.label_t` | 30 · 30 · 28 |

- 최상위 키는 전부 모델과 일치(D-0063 실측과 같음). claims 는 69건(랫클리프 포함) 전부 빈 목록.
- 결정 요청은 다음 파일(R-0076) — 로더 엄격도·번들 출처 변환·claim 후보·원고 sources 4건.
- 랫클리프 번들: `https://analysis-reports.pages.dev/…ec53e620b2.bundle.json` **받음**(200, 264,023 B). 작업 6 커밋에 넣는다.
