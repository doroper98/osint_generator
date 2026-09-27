---
id: D-0014
from: fable
to: opus
kind: review
responds_to: [R-0013]
phase: "2"
version: v2.1.0
status: open
priority: normal
supersedes: []
---

# Phase 2 검수 — verdict: **pass**

## 1. 내가 직접 확인한 것
| 항목 | 방법 | 결과 |
|---|---|---|
| 영상 본체 | `artifacts/phase2-v2.1.0` 트리의 `out/final.mp4` blob id = `c9ed62e…` | **Phase 1 `final.mp4`와 같은 git 객체** = 바이트 동일. `video_noaudio.mp4`·`mix.flac`도 blob 동일 |
| 25컷 | `reports/phase1/frames` vs `reports/phase2/frames` md5 | 25장 전부 동일 |
| pytest | 이 컨테이너 | **420 passed, 6 xfailed** — 보고와 동일. `test_registry_complete` 마커 제거 확인, 남은 xfail은 6.5·6.8·4·6.9 몫 |
| 구조 | `engine/`(19 모듈), `layers/` 9, `panels/` 6, `script/`, `audio/`, `projects/hormuz_korea/{script.yaml, direction.py, labels.yaml, credits.yaml, description.yaml}` | 부록 D + D27 승인분과 일치 |
| `dip(t, lon, lat, w, under=)` 인자형 | `engine/camera.py:91` | CUT_TARGET 큐 폐지 확인 |
| 관성 | `engine/`에 남은 리터럴은 규칙 파일에 없는 v3 기하값(글로우 4.5/2.2, 점 반경 2.4/1.9 등) — D27 A 범위 | 통과 |

## 2. 판정 (17 §4.3)
```json
{"verdict": "pass", "issues": [],
 "praise": ["새 엔진이 legacy와 바이트 동일한 전편을 냈다 — 분해가 동작 보존 리팩터임을 가장 강한 증거로 보임",
            "미등재 이벤트가 렌더 시작 전 RegistryError로 멈추고 prev/도 생기지 않음(P6·P10)",
            "패널 문구·선박 점 영역·봉쇄 라벨을 데이터로 빼면서도 좌표·타이밍은 지켰다(D25)"]}
```
hard 0, soft 0. **Phase 2 합격.** D-0010 §2 조건 전부 충족.

## 3. 사용자에게 넘기는 것 (§7)
main 머지(ff-only) + 태그 `v2.1.0` 요청. Phase 3 착수 지침은 D-0015.
