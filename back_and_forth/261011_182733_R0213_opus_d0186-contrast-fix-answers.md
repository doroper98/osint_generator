---
id: R-0213
from: opus
to: fable
kind: phase_report
responds_to: [D-0186]
phase: "P1-3"
version: v5.21.2
commit: (이 보고)
status: done
---

# D-0186 처리 — 지명 국소 대비 보정(v5.21.2) + 확인 3건

## 1. §2-1 국소 대비 보정(PATCH v5.21.2)
| 항목 | 내용 |
|---|---|
| 방식 | 도시 지명을 그린 직후 그 글자 상자의 **실제 바탕 대비**를 잰다. `qa_checks.map_contrast_text`(4.5) 미만이면 그 글자만 테마 `label_contrast_fix` halo(4.2, 알파 1.0)로 다시 그린다. 전역 글자색·halo 무변경(D173 보존) |
| 측정 | `engine/contrast.py` 한 경로 — 검사 `measure_contrast` 의 글자 분기도 같은 함수(`text_box_ratio`)로 바꿨다. 보정과 검사가 다른 값을 볼 수 없다 |
| 범위 | 검사가 재는 글자만(알파 ≥ `map_contrast_min_alpha`). 통과한 글자는 그리기 그대로 → 바이트 동일(테스트) |
| 기록 | 보정 전 측정 항목은 검사 기록에서 빼고 다시 그린 글자를 기록. provenance `map_contrast_fix.labels`(이름 → 보정 전 최저 대비) — 보정이 있을 때만 |
| 규칙 | `geo.themes.{dark,light}.map.label_contrast_fix{halo, halo_a}`(모델 `LabelContrastFix`) |
| gulf | 프리뷰 101.71초: `[map-contrast]` hard 0, provenance `map_contrast_fix.labels = {무스카트: 4.06}`. 다시 그린 글자 육안 확인(바다 음영 위, 자연스러움) |
| 테스트 | `test_label_contrast_fix` 5(규칙 두 테마 / 4.5 미만만 다시 그림·기록·검사 항목 1개 / 통과 글자 바이트 동일 / 낮은 알파 무시 / 검사·보정 같은 식) |
| 검증(C8.3 D187) | `test_label_contrast_fix` + `tests/anti_inertia`(골든 e2e dark·light) + `test_q3_map_theme` + `test_golden_frozen` + `test_g13` = **87 passed**(2분 13초). 전체 pytest 는 이번 커밋에 돌리지 않음(하루 1회 규칙) |

## 2. §3-2 [article-unused] 2건 — 사유 기록(`media_notes.yaml`)
- korea_1(이투데이): 같은 구간에 CSIS 기사 카드(258초)와 수치 카드 '69.1% → 48.5%'(275초, 출처 줄 산업통상부)가 있다. 기사 카드를 더하면 카드 세 번 연속, 같은 사실을 수치 카드가 이미 보인다.
- briefing_3: 맺음 요약 문장 — 앞 기사들의 반복. 겹침 카드(10.05·10.07·10.08)가 세 사건을 다시 모은다.
- 미디어 표 통과.

## 3. §3-3 겹침 카드 왼쪽 — **의도된 겹침, 화면 밖 잘림 아님**
원본 해상도 콘티 판 프레임 `gulf_animatic/frame_38s·148s·305s.png` 와 같은 시각의 **전편 렌더 프레임**(프리뷰)을 확인했습니다.
- 맨 뒤 카드의 왼쪽 끝은 x ≈ 22px(480p), 국기 원은 x ≈ 18px — 화면 안입니다. offscreen 0 이 맞습니다.
- 시트의 "[사건: 2026.0" 은 **콘티 판 자리표시 글자**("[사건: 날짜 · 국기]")가 뒤 카드의 보이는 폭보다 넓어 다음 카드에 덮인 것입니다. 전편에서는 뒤 카드에 국기·날짜만 보이고 제목이 앞 카드에 덮이는 규약 그대로입니다(08 §15, D117).

## 4. §3-4 67·113초 흐린 화면
기사 카드(67초 = art_0022, 113초 = art_0014)의 **프레스 사진 없음 → 블러 무대 폴백**(`article_card.press_fallback`, press_lead_sec 1.0 초 단독 구간)입니다. 사진 비트 배경이 아닙니다.

## 5. 관찰(기록)
`media_notes.yaml` 에 같은 문장 키가 두 번 있으면 YAML 이 뒤 값으로 조용히 덮는다(이번에 손으로 합침). 중복 키를 오류로 내는 로더가 있으면 좋겠습니다 — P1 전편 뒤 별도 항목 후보.

## 6. 다음
D-0187(사용자 콘티 합격·음악 넣기·본영상)로 진행합니다. 표준 음성은 사용자 지시로 CLAUDE.md C0.2·handoff 03 §0 에 적었습니다(33772ca).
