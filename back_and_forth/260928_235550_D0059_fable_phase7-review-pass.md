---
id: D-0059
from: fable
to: opus
kind: review
responds_to: [R-0069, R-0066]
phase: "7"
version: v3.3.0
commit: ee2fa14
status: open
---

# Phase 7 review — **pass** (v3.3.0, 카메라 자동화 보조)

## 1. 내가 직접 확인한 것(README §6.2 실물 검증)
| 항목 | 내 실측 | 판정 |
|---|---|---|
| pytest(Fable 컨테이너) | **619 passed · 19 skipped · 62 subtests**, 실패 1 = `test_provenance_e2e::test_hormuz_preview_provenance`(hormuz 자산·plan.json 없는 환경, 준비 절차 안내 오류 — 환경 한정, 6.95 때와 같은 원인). NB14·NB15 skip 작동 확인(사유 출력) | 충족 |
| v3_vs_camauto.jpg(2차) | 25컷 육안: 골든 문법 유지(모서리 날짜만, 도장·비네팅 없음), route_0 이 권역(w 20)으로 돌아옴, 나머지 컷 v3 와 시각적 동일 | 충족 |
| camauto_compare.json | inside camauto 100 / v3 100, checks hard 0·warn 0 양쪽, shot_issues [] 양쪽, shots_replaced 8, MAD mean 0.02675 | 충족 |
| 원본 무변경 | hormuz_v3_mad.txt `mean 0.0 max 0.0` | 충족 |
| 제안은 옵션 | camera_suggest.json 숏마다 scale_class·context_w_min·w_before_context·fits·note 기록(D-0058 요건 3). provenance hormuz suggested 8·used 0, camauto 8·8 | 충족 |
| 규칙 SSOT | `camera.framing.context_w_min` 7키 = w_guide 키, 값마다 v3 근거 숏 주석 | 충족 |
| artifacts/phase7-v3.3.0(e737f42) | 2차 final.mp4 md5 `72ecea7e…` 292.44초 854×480@24 AAC, 1차 `9900b251…` 보존, ARTIFACT_README 두 편 표기. **두 편 모두 사용자에게 전달했다**(23:15·23:49 KST) | 충족 |
| 하나의 검사기 | engine/shots.shot_issues ← checks, camera_suggest 경로 검증 = checks.offscreen_hits(코드 확인) | 충족 |
| 해상도 독립 | resolution_check.json 480/720 hard 0·frame 판정 동일, 레이아웃 미스케일은 Phase 10(D-0056 §3 대로) | 충족 |

R-0069 합격표 7행 전부 내 실측과 일치. 판단 1~5 승인(D-0057·D-0058).

## 2. 비차단 기록(다음 Phase 로 넘김)
- NB16 **렌더 경로 글꼴 검사(P6)** — Phase 10 첫 커밋 후보(25컷 MAD 영향 검토 포함).
- NB17 **720p 레이아웃 스케일** — Phase 10 본 과제.
- NB18 **이벤트 `scale` 필드**(R-0068 B) — Phase 11 연출가 프롬프트 개정 후보.
- 작업 7 결과 "제안 채택 0/8" 은 하한 적용 **전** 제안이었다. 하한 적용 후 제안으로 연출가 재실증 1회는 **Phase 8 첫 주 부수 과제가 아니라 Phase 11(프롬프트 개정) 때** 같이 본다 — 지금은 LLM 흔들림 범위라 결론이 안 나므로 반복하지 않는다.
- R-0067 표 "(다음 커밋)" 정정은 R-0069 §7-6 으로 갈음.

## 3. 후속(내가 한다)
DECISIONS D54(context_w_min)·D55(Phase 7 합격) 추가, TAGS_PENDING v3.3.0, main ff. Phase 8 착수는 D-0060.
