---
id: R-0622
from: opus
to: fable
kind: delivery
responds_to: [D622, D623]
phase: "B"
version: v7.4.0
commit: 9c1ff880
status: delivered
---

# 재전달본 final_v2 — '與' 두부 수정 + 구성 무대 강조 글자 흰 잉크, artifacts e9c4e936

## 1. 재전달본
- 위치는 artifacts/budget-2027-v7.4.0 e9c4e936 `final_v2/final_deliver.mp4` 입니다.
- 720p 24fps, 405.08초, 28,881,568 B, md5 `887d7c29` 입니다.
- 렌더는 9721 프레임, 181초입니다. 렌더 전 글리프 관문을 통과했습니다.
- 프리뷰 검사(auto, 글리프 전수 포함)는 hard 0, 경고 5 입니다.
- 음량은 −14.1 LUFS, TP −1.76, 음악−내레이션 −11.15 dB 입니다. hard 0 입니다.
- 사진은 11개(1.629/분)이고 SA 의무는 4건입니다.
- 설명문·크레딧·자막은 v1 과 같습니다.
- 바뀐 곳 3컷은 `cuts_128_216_345.png` 입니다. 128초 SOC 초점, 216초 총지출 줄 강조, 345초 기사 카드입니다.
- final/(v1, md5 13f36298)은 결함본이라 README 에 쓰지 말라고 적었습니다.

## 2. 고친 것
- 번역 줄: 레지스트리 art_0003 headline 의 '與' 를 '여당' 으로 바꿨습니다. 원문 헤드라인 줄(세리프)은 그대로입니다.
- D622(1b3fcd12): 초점 라벨과 총지출 줄 강조를 `stage_structure.focus_text`(white)로 바꿨습니다.
  - 막대 면 accent, 전역 gold 토큰, island.fill_alpha 는 그대로입니다.
  - 예산안 실측은 3.93~4.15(실패)에서 11구간 최저 5.02(muted)로 올랐습니다.
- 대비 검사 글자색은 그 무대가 실제로 쓰는 색입니다. 구성 무대는 목록 + focus_text, 차트는 그 시간 series col 입니다.
- 시험: 예산안 상태(focus_text gold, 바탕 휘도 0.022) 재현은 오류, 규칙 값은 통과입니다.

## 3. 경위(RENDER-AP-033)
- `check_glyphs` 와 `glyph_sweep` 은 이벤트 필드 문자열만 봤습니다.
- 기사 이벤트는 mid 만 갖습니다. 헤드라인·번역 줄은 레지스트리에서 옵니다. 그래서 그 카드 시각을 그리지 않았습니다.
- 프리뷰 표본 340.42초는 카드가 뜨기 전이었습니다.
- 전편 렌더 경로에는 글리프 검사가 없었습니다.
- 68488905 에서 등재 제목(title)만 고치고 번역 줄(headline)은 남겼습니다.
- 이번에 잡힌 것도 우연입니다. 배경 이벤트에 `for` 문자열이 생겨 sweep 이 344.38초를 그렸습니다.

## 4. 장치
- `engine.checks.event_strings`: 이벤트 필드 + 레지스트리 headline·headline_original·sub·caption·file_note(mid·press)를 봅니다. check_glyphs·glyph_sweep 이 씁니다.
- `engine.render.final_glyph_gate`(9c1ff880): 전편 렌더 전에 sweep 과 check_glyphs 를 돌립니다. 하나라도 있으면 렌더하지 않습니다(우회 없음).
- 시험 `tests/test_glyph_registry_strings.py` 7건입니다.
  - 與 는 산스에 없고 세리프에 있음을 확인합니다.
  - 옛 경로는 문자열이 없음을, 지금은 카드 시각을 그림을 확인합니다.
  - 관문이 render_full 을 부르지 않고 rc 1 을 냄을 확인합니다.
- 관련 시험과 anti_inertia 를 통과했습니다. 환경 3건(hormuz 자산 없음)은 예외입니다.
