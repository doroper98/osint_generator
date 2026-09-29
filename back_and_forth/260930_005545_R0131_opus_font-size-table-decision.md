---
id: R-0131
from: opus
to: fable
kind: decision_request
responds_to: [D-0112]
phase: "G7"
version: v4.8.0
commit: c574813
status: in_progress
---

# 결정 요청 — §3 화면 글자 크기 전수 표와 제안 값 (D-0101 §3 1단계)

D-0112 는 반영했다(14f90ed — head_top 실측 1.03~1.08R, 가장자리 보정, hormuz 골든 프리뷰 hard 0). 리터럴 → 규칙 이동(값 무변경, 골든 25컷 바이트 동일)은 c574813.
배지 적응 실측 3컷: `docs/handoff/reports/phaseG7/badge_solo_group.jpg`(랫클리프 푸틴 solo R 56 → 트럼프 팝인 완료 +0.3s 푸틴 R 44.8 → 둘 다 R 34).

**전/후 시트**: `docs/handoff/reports/phaseG7/scale_before_after.jpg` — hormuz 6컷(7.82·61.25·80.70·136.97·193.22·258.61) + fed_policy 6컷(5·32·104.5·117·160·270), 왼쪽 BEFORE·오른쪽 AFTER(아래 표의 "제안" 전부 적용, 규칙 사본으로 렌더 — 저장소 규칙은 무변경).

## 1. 표 — D-0101 명시 항목(제안 기준: 본문 ≥ 12, 메타 ≥ 9)
| 규칙 키 | 지금 | 제안 | 비고(연동 기하) |
|---|---|---|---|
| layout_480p.subtitle.size | 19 | **21** | 2줄 자막 hormuz 3 → 15/45, fed 1 → 7/48, 랫클리프 5 → 7/38, 3줄 0(wrap 700px). 2안: 20 |
| card.line_size | 13 | 15 | line_gap 21 → 24 |
| card.tag_size | 10.5 | 12 | |
| card.src_size | 9.5 | 11 | src_gap 18 → 20 |
| card.cap_size(큰 숫자 캡션, 옛 리터럴 11) | 11 | 12 | |
| panel.subtitle_size | 11 | 12.5 | |
| media_caption.caption_size(사진·영상 캡션) | 10.5 | 12 | 캡션 바 media_beats.caption_bar_px 38 → 42, caption_dy 16 → 18 |
| media_caption.credit_size(출처 줄) | 7.8 | 9 | credit_dy 30 → 34 |
| media_caption.tag_size(PHOTO·VIDEO) | 7.5 | 9 | tag_h 14 → 16, tag_dy 10 → 12 |
| media_caption.cutout_credit_size | 8.5 | 9 | |

## 2. 표 — 그 밖의 본문 < 12 · 메타 < 9 (D-0101 "전수")
| 규칙 키 | 지금 | 제안 | 비고 |
|---|---|---|---|
| marker.sub_size(지점 부제) | 10.5 | 12 | sub_dy 15 → 16 |
| route_label.route_size | 11.5 | 12.5 | |
| post_card name·handle·chip·body·orig·foot | 11.5·8.5·7.5·12·8·7.8 | 13·9.5·9·14·9·9 | body_line 18 → 20. 이번 두 영상엔 없음(시트 밖) |
| panels.relation.edge_label.size | 11 | 12 | |
| panels.timeline(패널) date·label·month·band_label | 11·11.5·10.5·10.5 | 12·12.5·11·11 | 시간축 **무대**(stage_timeline, D-0092 B)는 제외 |
| panels.charts.dual_line x_label·value | 11·11 | 12·12 | tick 10(축 메타) 유지 |
| panels.charts.fork.body.size | 11.5 | 12.5 | |
| panels.charts.dots.note_caption.size | 11 | 12 | |
| panels.charts.network.label.size | 9.5 | 11 | |
| panels.precedent line·caption | 11.5·10.5 | 12·11 | 카드 상자 172×212 고정(v3) — 더 키우면 넘친다 |
| 인물 뱃지 이름표 group 역할 | 10 | 10(유지) | G7 작업 1 에서 정함(solo 15/11 · group 12/10) |

## 3. 유지 제안(바꾸지 않음)
| 대상 | 값 | 이유 |
|---|---|---|
| 엔딩 카드(item 9.2·license 7.8·notice 7.8)·타이틀 카드·시간축 무대 글자·모서리 날짜 | — | D-0101 제외 목록 |
| 지도 바탕 글자(engine/layers/labels.py 바다 11/12·행정구역 9.5·도시·국가 LOD) | — | 지도 질감(09 LOD). 키우면 지도 혼잡·라벨 충돌 증가. 리터럴 규칙화도 이번엔 하지 않음(값 무변경 원칙 밖 — 원하면 G8) |
| 메타 ≥ 9 인 것: panels.prov_tag 10, gantt note 9.5·year 10.5·today 10.5, dual_line tick 10, versus src 10, dot_plot tick 9.5, statement_diff label 10 | — | 이미 메타 기준 이상 |
| primitives.site_diagram(9.5~14) | — | dmz 자산 없음 — 시감 불가. G8 콘티 판에서 |
| article_card | — | 작업 2 에서 확정(15·10·18·12·9) |

## 4. 선택지
| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| **A** | 표 1·2 제안 전부(자막 21) | 사용자 지시("전체적으로 너무 작다")에 가장 가깝다. 2줄 자막 늘어남(시트 hormuz 136.97·fed 270) | 규칙 값 revert |
| B | 표 1·2 전부, 자막만 20 | 2줄 증가 절반쯤(측정은 결정 뒤) | 같음 |
| C | 표 1(D-0101 명시 항목)만, 자막 21 | 패널·차트 작은 글자 남음 | 같음 |

## Opus 권고 — A
- ② D-0101 §3 제안 기준(본문 ≥ 12, 메타 ≥ 9, 자막 21 검토)을 그대로 수치로 옮겼다.
- 시트에서 2줄 자막은 두 줄 모두 자막 구역(y ≥ 410) 안에 들어간다(t 136.97·270 AFTER). 3줄 0.
- ① 전부 규칙 값이라 한 커밋 revert 로 되돌린다.

## 막히는 범위
- 막힘: §3 2단계(값 적용) → 골든 expected_deltas `g7_scale_d0101`·골든 diff 증명·랫클리프·데모·fed 기준선 재등록·갤러리 36·전편 480p 2편·문서.
- 계속: 기사 카드 전/후 시트(article_before_after.jpg)·run_log·asset_md5 초안, 골든 diff 도구 준비.

## §7 해당 여부
아니다(사용자 결정 D89 범위 안 — 값은 Fable 결정, D-0101 §3).
