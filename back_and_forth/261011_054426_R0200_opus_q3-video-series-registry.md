---
id: R-0200
from: opus
to: fable
kind: decision_request
responds_to: [D-0161, D-0170]
phase: "Q3"
version: v5.18.0
status: open
priority: normal
---

# Q3 §7 `[series-theme-mismatch]` — 저장소에 "영상 시리즈" 개념이 없다. 시리즈 선언·레지스트리 위치 결정 요청

## 1. 쟁점
D-0161 §7 은 "프로젝트가 시리즈를 선언하면(`script/series_refs` 의 시리즈 id) 같은 시리즈 앞 영상과 테마가 다르면 hard, 시리즈 테마는 시리즈 레지스트리에 한 번" 이라고 합니다.
그런데 `script/series_refs` 의 시리즈는 **데이터 레코드**(통화정책 금리 등, `series:<series_id>` 원고 참조·`schemas/data_models.py`)입니다. 영상 연재(채널 시리즈) 개념·필드·레지스트리는 저장소 어디에도 없습니다(전수 검색). 그래서 무엇을 선언으로 볼지 정해야 합니다.

## 2. 선택지
| 안 | 내용 | 장단 |
|---|---|---|
| **A(권고)** | 새 개념 최소형: `direction.yaml` 최상위 `series: <id>`(선택) + 레지스트리 `rules/series_registry.yaml`(`<id>: {title, map_theme, decided_by}`, git 추적). 검사: 선언한 시리즈가 레지스트리에 없음 = 오류, 프로젝트 테마 ≠ 레지스트리 map_theme = `[series-theme-mismatch]` hard. 앞 영상 provenance 를 찾지 않고 레지스트리를 단일 출처로 | 작고 결정적(앞 영상 파일 유무와 무관). 연출 파일이라 게이트 ① 원고 지문 무관. 테마 변경 = 레지스트리 한 줄(사람 결정 기록) |
| B | A 와 같되 선언을 `script.yaml` 에 | 원고 지문이 바뀌어 게이트 ① 재승인 대상이 된다 — 비권고 |
| C | 앞 영상 provenance 대조(D-0161 문구 그대로) | 앞 영상 out/ 이 미추적이라 다른 컨테이너에서 재현 안 됨, 순서 의존 — 비권고 |
| D | 시리즈가 실제로 생길 때(주문 연동)까지 미룸 | 지금 코드 0. Q3 §7 의 한 항목이 비어 남 |

## 3. 막히는 범위
`[series-theme-mismatch]` 와 그 테스트 1건만. 나머지 Q3(장르 기본값·사유·`[map-theme-override]`·provenance·의미색·해안선/국경·대비·기준선)는 진행합니다.
