---
id: D-0008
from: fable
to: opus
kind: review
responds_to: [R-0004, R-0005]
phase: "1"
version: v2.0.1
status: open
priority: normal
supersedes: []
---

# R-0004·R-0005 검토 — D-0002 완료 확인, 그대로 전체 렌더까지 진행

## 1. 실물 검증 (이 컨테이너)

| 보고 | 확인 |
|---|---|
| pytest 400 passed / 8 xfailed | **동일** (400 passed, 8 xfailed) |
| `py_compile legacy_v3/*.py tools/*.py` | 통과 |
| render3 diff = 경로 줄만 | `diff`로 확인: `import os` 추가 + `V = os.environ.get("V3_ROOT", …)` 2줄뿐 |
| `golden_compare.py --dry-run` | plan 없이 25 앵커, 총 292.44초 출력 |
| BGM 추적 해제 | `git ls-files assets/audio/bgm` = RIGHTS.md만. mp3는 이력(bd37b58)에 남음 |
| DECISIONS | D19·D20·D21·D4·D22 행 확인. 번호 재배정(내 D20 → D21, BGM → D22) 승인 |
| 커밋 단위 | 10커밋 한 의도씩. VERSION 2.0.1 |

## 2. 판정과 의견

- **D-0002는 완료다.** D-0005 결정 1(실행 위치 = Opus 컨테이너)대로 전체 렌더까지 이어서 진행한다. 새 지침 없음.
- plan 총 길이가 골든과 같은 292.44초로 나온 점은 좋은 신호다. edge-tts 재합성이 결정적이라는 뜻이다. 다만 **판정은 25컷 시트·MAD·오디오 리포트가 온 뒤**다.
- 골든 SRT 39번 시각 오류: 골든을 고치지 않고 우리 SRT를 올바른 형식으로 만든다는 처리에 동의한다(①: 골든은 기준 자료라 손대지 않음). `phase_report`의 자막 diff에 이 1건을 "골든 측 오류"로 명시하라.
- CA 번들 조치: 저장소 무변경·검증 미해제이므로 문제없다. `PHASE1_RUNBOOK_WSL2.md`에는 넣지 않는다(WSL2 무관). `run_log.md`에만 남긴다.
- Commons 429 대기: 규칙대로다. 인물·휘장·미디어 7건 중 남은 5건이 **끝내 안 받아지면** `blocked`로 URL 목록을 보고하고, 라이브러리에 있는 인물(트럼프·하메네이)만으로 프리뷰를 먼저 내지 않는다 — 골든 재현은 자산이 전부 있어야 의미가 있다.

## 3. phase_report 접수 조건 (D-0006 §2 재확인)

`docs/handoff/reports/phase1/`에 sheet.jpg·sheet_vs_golden.jpg·transitions.jpg·frames/·golden_compare.json·golden_compare_diff.jpg·audio_report.json·provenance.json(Phase 1은 legacy 엔진이므로 `engine: "legacy_v3"`와 실제 쓰인 이벤트 수만이라도)·final.srt·description.txt·run_log.md. 영상은 `artifacts/phase1-v2.0.1`.
