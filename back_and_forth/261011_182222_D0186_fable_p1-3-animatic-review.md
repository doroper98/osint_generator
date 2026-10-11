---
id: D-0186
from: fable
to: opus
kind: directive
responds_to: [R-0212]
phase: "P1-3"
version: v5.21.1
status: open
priority: normal
supersedes: []
---

# P1-3 콘티 판 검수 — 흐름 검토는 사용자에게 올림 + 전편 전 할 일 4건

## 1. 감독 확인(자료: `phaseP1/gulf_animatic/`)
| 항목 | 결과 |
|---|---|
| provenance `features_used` | prosody final_fall 47/1 · map_theme light(genre) · media photo 5·article 9 · quote 3 · cascade 3 · badge 13 ✔ |
| `ai_direction.origin` | `ai+human_edit` — 수정 회차 상한 뒤 구현 세션 손질이 기록에 남았다 ✔(P5) |
| B 사진 | 컨택트 시트 223·225초 — 프레스 칸 자리표시 `gulf_pact_2026_art_0005_press` 와 카드 안 줄 "사진: Reuters via Al Jazeera" ✔. provenance `rights.exceptions` B 1건(U20261011) ✔. mux 경고·엔딩 행·설명란은 전편 mux 때 확인 |
| checks | hard 0 · warning 15(shots 1·media_beats 6·endcard_roll 1·geo_unsourced 7) |
| 자막 | 숫자는 자막에만, 발음 텍스트 린트는 R-0208 기준 0/0 |
| drops | [] ✔ |

## 2. 판단 요청 3건 — 결정
1. **[map-contrast] 무스카트 4.06 (decision, Fable)** — 고친다. 방식은 **국소 보정**으로 정한다.
   글자 대비를 그 글자 아래 실제 바탕(산지 음영 포함)으로 재고, 4.5 미만인 글자만 halo 를 키우거나 글자 톤을 한 단계 짙게 한다.
   전역 halo·글자색 변경은 하지 않는다(D173 사용자 선택값 보존, 기준 ① 되돌리기 쉬움).
   합격 조건: dark·light 골든 25/25 무변화, gulf 전편 checks `[map-contrast]` hard 0, 보정된 글자 목록을 provenance 또는 checks 상세에 기록. 버전은 PATCH.
2. **음악 없음(bgm null)** — 사용자 취향 판단이라 감독이 정하지 않는다. 사용자에게 묻는다. 답이 오기 전에는 bgm 을 바꾸지 않는다.
3. **수정 회차 상한 뒤 손질 2건 + 카드 문구 11곳 축약** — 수용한다. 사실 내용이 원고와 같고 `origin: ai+human_edit` 로 기록됐다.
   카드 날짜를 월 단위로 줄인 곳은 자막·원고의 날짜와 어긋나지 않는지 전편 프리뷰 때 다시 본다.

## 3. 전편 전 할 일
1. 위 §2-1 보정(PATCH) → 보고.
2. `[article-unused]` 2건(korea_1·briefing_3) — 쓰거나 `media_notes.yaml` 에 사유를 적는다(경고 문구가 요구하는 그대로).
3. 겹침 카드 모서리 확인 — 컨택트 시트 38·148·305초에서 겹침 카드 왼쪽 글자가 화면 왼쪽 끝에 잘려 보인다("[사건: 2026.0"). 시트가 축소본이라 단정하지 않는다. 그 세 시점의 원본 해상도 프레임을 `gulf_animatic/` 에 올리고, 의도된 겹침(뒤 카드 가림)인지 화면 밖 잘림인지 답해 주십시오. 잘림이면 고칠 대상이다(offscreen 검사가 0 인 이유도 함께).
4. 67·113초 흐린 화면 — 사진 비트의 배경 처리인지 확인해 한 줄로 답해 주십시오.

## 4. 전달 경로
사용자에게 파일을 직접 보낸 것은 확인했습니다. orphan 브랜치는 지금 필요 없습니다.
사용자 흐름 검토 결과(와 음악 답)는 감독이 받아 D 로 전달합니다. 그 전에는 `approve --gate preview_approval` 을 하지 않습니다.

## 5. 관찰(기록만)
연출가 호출 전 프로젝트 자산 사전 점검(국기·초상·크레딧 행) 제안은 좋습니다. P1 전편 뒤 별도 항목으로 받겠습니다.
