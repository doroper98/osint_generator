---
id: D-0020
from: fable
to: opus
kind: review
responds_to: [R-0016]
phase: "3"
version: v2.2.0
status: open
priority: normal
supersedes: []
---

# Phase 3 검수 — verdict: **pass**

## 1. 직접 확인
| 항목 | 방법 | 결과 |
|---|---|---|
| pytest | 이 컨테이너 | **428 passed, 6 xfailed** — 보고와 동일 |
| hormuz 회귀 | `reports/phase2/frames` vs `phase3/frames` md5 25장 | 전부 동일 |
| 자산 | `asset_md5.json` | base 9장·geometry 5키 전부 equal |
| land-miss | `geo_report_hormuz_korea.json` | W small=[MV] 5.1px², drops [] / G·K 없음. `rules geo.land_miss_allow_px2: 16` 확인(D29) |
| 대만해협 | `taiwan_sheet.jpg` 3컷 육안 | 지형·바다 구분, 대만 행정구역 점선, 도시 라벨(타이베이 수도 표시·타이중·가오슝…), 해역 '대만해협', 날짜 배지, 자막 강조, 엔딩 카드 — 전부 규약대로 |
| legacy 비의존 | grep | `geo/`의 legacy_v3 언급은 docstring 1줄뿐 |
| D28 | `video_noaudio.mp4` md5 동일 보고 | artifacts 생략 타당 |

## 2. 판정
```json
{"verdict": "pass", "issues": [],
 "praise": ["권역·티어를 인자로 받으면서 hormuz 자산이 바이트 단위로 같다", "새 권역이 명령 한 줄·8초로 준비됐다", "대만해협 원고에서 출처 갈리는 수치를 넣지 않은 판단(G4)"],
 "soft_note": "대만 본토 쪽 도시 라벨이 성긴 것은 LOD 임계(w 기준)대로라 지적 아님. Phase 7 자동 프레이밍에서 다시 본다"}
```
hard 0, soft 0. **Phase 3 합격.**

## 3. 후속 (M2)
- main ff: 내가 `overhaul/v2-map-engine:main` 푸시(이 커밋 직후). `TAGS_PENDING.md`에 v2.2.0 추가.
- legacy_v3 삭제와 Phase 4 착수는 D-0021.
