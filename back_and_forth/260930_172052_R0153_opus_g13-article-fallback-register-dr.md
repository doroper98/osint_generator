---
id: R-0153
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G13"
version: v5.2.0
commit: ca80d0a
status: awaiting_decision
---

# G13 결정 요청 3건 — 기사 폴백 블러 분리 · fed 기사 4건 등재 · panel 의 주 아일랜드 여부

## Q1. 기사 프레스 폴백 블러 값(§A 부수 효과)
- 쟁점: `engine/layers/article.py` 의 프레스 사진 없음 폴백이 `stage_backdrop.blur_px·dim` 을 같이 쓴다. §A 값(6·0.38)을 그대로 따르면 hormuz(mercator) 기사 골든 2컷(15_review_0·19_debate_0)이 바뀐다. 지침은 "hormuz 영향 0".
- A(권고·적용 중): 폴백 값을 `layout_480p.article_card.press_fallback: {blur_px: 18, dim: 0.55}` 로 분리. G12 값 그대로라 hormuz 불변. 기사 글자 뒤는 강한 블러가 가독에 맞다.
- B: 폴백도 새 값(6·0.38)을 따름 → hormuz 2컷 재등재.
- 막히는 범위: 없음(A 로 진행 중, B 면 규칙 한 줄).

## Q2. fed 보도 인용 카드 → article 전환 재료(§B·§D)
- 실측: fed v9 연출 카드 35개 중 매체 보도 인용 카드 10개(CNN·NBC·ABC·폭스비즈니스). 미디어 레지스트리의 fed 기사는 2건(cnn_0729·fox_0916)뿐이고 둘 다 이미 article 이벤트로 쓰였다. 재료가 없으면 연출가가 카드를 article 로 바꿀 수 없다.
- intake/sources.json 에 검증된 기사 출처 4건이 더 있다(원문 헤드라인·게시일·URL, verification verified): src_art_0002 Fox 0729, src_art_0003 CNN 0916, src_art_0005 NBC 0916, src_art_0006 ABC 0916.
- A(권고): 이 4건을 G4 의 cnn_0729·fox_0916 과 같은 모양(kind article, rights_clear, 헤드라인 번역·요지 자체 조판, headline_original 원문, 원문 인용 15단어 미만)으로 레지스트리·credits 에 등재. 한국어 번역 헤드라인·부제는 내가 원문에서 옮기고 번역 표기 유지.
- B: 등재하지 않음. 연출가는 기존 2건만 쓰고, 나머지는 차트·프리미티브로 주 아일랜드를 채운다(카드→article 전환 수 ≈ 0).
- 막히는 범위: §D fed 연출가 재실행. 결정 전에는 §A~§C 커밋·스윕 시트만 진행한다.

## Q3. backdrop 패널의 주 아일랜드 여부
- 쟁점: 지침 main_kinds = [chart, primitive, photo, clip, article]. backdrop 무대 패널은 panel_box 아일랜드(766×362, 화면 대부분)인데 목록에 없다 → 패널만 있는 구간이 3초를 넘으면 hard 가 된다.
- A(권고): 지침 그대로(패널 제외). fed 는 패널을 쓰지 않아 영향 없다. 필요해지면 규칙 한 줄.
- B: main_kinds 에 panel 추가.
- 막히는 범위: 없음.
