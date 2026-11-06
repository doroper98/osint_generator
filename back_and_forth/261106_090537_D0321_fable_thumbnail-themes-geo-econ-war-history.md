---
id: D-0322
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: high
supersedes: []
---

# 사용자 판정 UF-178 / D542 — 썸네일 합격, 장르 테마(색조만) 두 가지 + CLAUDE.md C13

## 0. 사용자 원문
> "썸네일 아주 만족해. 지정경제학적 테마와 전쟁사/역사물에 대한 테마는 색조만 살짝 다르게 적용할 수 있도록 저장소 최상위 규칙에 적어두고, 일관된 디자인이 유지 될 수 있도록 해."

감독이 **CLAUDE.md C13** 을 신설했다(헌법 먼저, P7). 썸네일 초안(6d082b2, png md5 b8830301)은 **사용자 합격 기준**이다 — 지금 구성·수치를 바꾸지 않는다.

## 1. `rules thumbnail.themes` — 색 값만, 두 가지
```yaml
thumbnail:
  ...(기존 title_scale·title_line_gap·border 그대로)
  theme_default_by_genre: {geopolitics: geo_econ, economy: geo_econ, earnings: geo_econ, military: war_history, war_history: war_history, history: war_history}   # 실제 장르 프로필 키에 맞춰라(genre_prompt·genre_profiles). 없는 장르 = geo_econ
  themes:
    geo_econ:      # 현행 = us_midterms 합격본과 byte-equal 이어야 한다
      gradient_rgb: [0.01, 0.015, 0.03]     # 타이틀 카드 그라데이션 색(현행 fullcards 값)
      gold: null                            # null = C["gold"] 그대로
      subtitle_rgb: [0.92, 0.90, 0.88]
    war_history:   # 살짝 따뜻하게 — 색조만
      gradient_rgb: [0.03, 0.02, 0.012]
      gold: [0.78, 0.63, 0.36]
      subtitle_rgb: [0.93, 0.89, 0.84]
```
- 테마는 **색 값 키만** 가질 수 있다(스키마로 강제 — 기하·크기 키가 들어오면 모델 오류). 그라데이션 alpha 스톱·제목 흰색·날짜 글꼴·테두리 기하는 공통.
- `tools/thumbnail.py --theme` 로 덮어쓸 수 있고(사유 필수, provenance `thumbnail.theme_reason`), 기본은 `order.yaml genre` → 매핑.
- 타이틀 카드 본편 렌더(`draw_fullcards`)는 **바꾸지 않는다** — 테마는 썸네일에만(영상 본편 색은 C0 합격 값).

## 2. 테스트
- `tests/test_thumbnail.py`: ① geo_econ 썸네일 = 테마 인자 없이 만든 것과 byte-equal ② 두 테마로 만든 썸네일의 **글자 픽셀 마스크(흰 제목)·테두리 위치가 동일**(색만 다름) ③ 매핑에 없는 장르 → geo_econ ④ 테마에 기하 키 → 오류.
- 원장 UF-178 guards 에 연결, status guarded.

## 3. 산출·보고
- us_midterms 썸네일은 geo_econ 으로 재생성해 md5 b8830301 과 같음을 R 에 적는다. 확인용으로 같은 프레임을 war_history 로도 한 장 만들어 artifacts `delivery/thumbnail_theme_war_history_sample.png` 에 올린다(전달본 아님, 감독 눈 확인용).
- D-0320 작업(전달 패키지)과 같은 R 로 묶어도 된다. 완료 후 **적용 커밋 해시 목록**(fullcards 분리·thumbnail.py·deliver_package.py·rules·tests·description.yaml 스키마)을 R 에 적어라 — 전쟁사 트랙이 cherry-pick 한다.
