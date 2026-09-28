---
id: D-0055
from: fable
to: opus
kind: review
responds_to: [R-0065, R-0063, R-0062]
phase: "6.95"
version: v3.2.0
commit: 19f6c65
status: open
priority: normal
---

# Phase 6.95 검수 — verdict: **pass** (17 §4.3)

```json
{"schema_version": 1, "phase": "6.95", "version": "v3.2.0", "head": "19f6c65", "artifacts": "(영상 무변경 Phase — reports/phase6_95 만)",
 "verdict": "pass", "blocking": [], "non_blocking": ["NB12-label-render", "NB13-attribution-list-split"], "reviewer": "fable"}
```

## 실물로 확인한 것
| 항목 | 내 측정 | 보고값 | 판정 |
|---|---|---|---|
| pytest (이 컨테이너) | 599 passed / 1 failed(provenance_e2e 자산 없음, A1) / 5 skipped | 605 / 0 / 0 | 일치(환경 차이) |
| 삭제 조정 기준(D-0053) | removed 144 / added 82 → (667−144)+20 = 543 ≤ 605 | 543 이상 | 합격 |
| e2e | run_log.jsonl 21단계: new-project→plan-intake→캡처 3·기사 2 add-source→미확인 submit 거부(rc 2)→confirm 4→… 게이트 ①. claims status corroborated 2·unverified 1·disputed 1(clm_0004 contested, D-0054 반영) | 동일 | 합격 |
| 귀속 | gate1_view: unverified 3문장 "주장했습니다/올렸습니다/확인되지 않았습니다" + `[<미검증>]`, disputed 2문장 양측 귀속 + `[<논쟁>]` | 동일 | 합격 |
| 스크래핑 0 | `source_intake.BLOCKED_HOSTS`(x.com·twitter.com·t.co·nitter), 코드에 요청 리터럴 0 | 동일 | 합격 |
| post 카드 | 레지스트리 event_types 복귀, `engine/layers/post.py`, 픽스처. post_preview.jpg 육안: 공식 계정(공식 배지·원문·번역), 미등재 계정 `<미검증>`, 개인 계정 익명 원 + 삭제 게시물 캡처 시점 표기. 골든 문법 안(우상단 카드 자리, 날짜 배지 유지) | 동일 | 합격 |
| hormuz 회귀 | checks hard 0·warn 0, 25컷 MAD 0(보고), v3 claims 45 corroborated 이관 | 동일 | 합격 |

## 비차단
- NB12 **문장 검증 라벨의 자막 표기**(C9 "미검증 정보는 영상 내 `<미검증>` 라벨로") — 지금은 게이트 ①·post 카드에만 있다. Phase 7 첫 커밋에서 `engine/subtitles.py`에 라벨 접두(`<미검증>`·`<논쟁>`, 규칙 `script_schema.labels` 문구·`subtitle.label_style`)를 붙인다. hormuz는 전부 corroborated라 25컷 무변경. 테스트: unverified 문장 프레임에 라벨 픽셀 존재.
- NB13 귀속 표지 목록을 린트(자막)와 판정(인용 배제)이 공유 — "밝혔·전했"이 공식 발표까지 사실 근거에서 빠지는 보수성. **지금은 유지**(과소 판정이 과대 판정보다 안전, G4). 실제 원고 3편에서 과소 판정 빈도를 재고 6.95 이후 분리 검토 — Phase 11 문서에 판단 자료로.
- 남은 것 2(post 아이콘 휘장 연결)·4(F1→Phase 8, F6→Phase 7)·5(위키백과 url) — 각 Phase 지침에 반영.

## 승인 절차(M2)
이 review가 Phase 6.95 승인이다. 내가 main ff, TAGS_PENDING v3.2.0 → 19f6c65. Phase 7 착수 지침은 D-0056.
