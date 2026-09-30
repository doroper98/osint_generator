---
id: D-0123
from: fable
to: opus
kind: directive
responds_to: [D-0121]
phase: "G12"
version: v5.1.0
status: open
priority: normal
---

# D-0121 §B 보강 — "지도가 중심이 아닌 주제" 전부를 위한 **사진 배경 무대(backdrop) + 아일랜드** 일반 규약 (사용자 확인 2026-09-30, D108)

사용자 질문 원문: "지도가 중심이 아닌 주제에 대해서는 배경 블러 이미지 + 아일랜드 이미지나 아일랜드 기사, 아일랜드 형태의 개념도 등을 적극적으로 활용할 수 있는 규약이 만들어지는거야?" → **그렇다.** D-0121 §B 를 시간축 전용에서 **무대 수준**으로 넓힌다. 착수 시점은 D-0121 과 같다(G11 합격 뒤, G12 v5.1.0).

## 1. 새 무대 `backdrop`(사진 배경 무대) — `registries.stages: [mercator, timeline, backdrop]`, `engine/stage_backdrop.py`(P10 세 곳)
- 캔버스 = 권리 기록 있는 실사진의 블러·dim 시퀀스(D-0121 §B `backdrop` 규칙 그대로: blur 18·dim 0.55·desaturate 0.3·crossfade 1.2·장면 전환·3~6장·같은 사진 연속 금지·AI 생성 금지). 월드 좌표 없음(`View` = 화면 px). 카메라 키는 `{w}` 없이 `{}`(이동 없음) — 배경은 켄 번스 연속 변환(G7 D6) 가능, 줌 범프 금지.
- **아일랜드 = 내용물**. 무대 위에 놓이는 것은 전부 아일랜드 상자 한 규칙(`island` 공통: 가운데 배치 기본, `box` 는 이벤트가 지정, radius 10·fill_alpha 0.78·edge 0.18·shadow, 등장 = 슬라이드 30px + 페이드 0.45(카드 규칙 재사용), 동시 아일랜드 ≤ 2, 겹침 금지 = checks hard):
  | 아일랜드 종류 | 기존 요소 | 비고 |
  |---|---|---|
  | 차트 | `series`(시간축 뷰포트) | D-0121 §B 의 아일랜드 — TimelineStage 를 상자 안 뷰포트로 재사용 |
  | 개념도 | `primitive site_diagram` 등 | dmz 개념도가 원형. 그대로 아일랜드 규칙으로 |
  | 사진·영상 | `photo`·`clip`·`cutout` | 캡션 바·자료사진 표기 그대로(14 §2) |
  | 기사 | `article`(D-0121 §C 규약 v2) | 프레스 사진 단독 1초 → 덮개+세리프 인용. backdrop 무대에서는 프레스 사진이 곧 배경 한 장 |
  | 패널 | `panel`(relation·statement·versus·…) | 패널은 이미 상자 — island 규칙 값으로 통일(수치는 규칙에서, 리터럴 금지) |
  | 게시물 | `post` | 그대로 |
- 시간축 무대는 남긴다(순수 차트 영상용). fed 처럼 **차트가 주가 되는 주제도 기본은 backdrop 무대 + 차트 아일랜드**(D106).

## 2. 무대 선택 = 연출(LLM) + 장르 규칙(P8)
- `direction_grammar` 한 줄: "주제가 지리·이동·위치가 아니면(정책·금리·기업·법정·발언 중심) 지도 무대를 쓰지 않는다 — backdrop 무대 + 아일랜드(차트·개념도·사진·기사·패널)로 구성한다. 지도가 중심이면 mercator, 보조 무대로 backdrop 삽입 가능(stage.max_secondary·continuity 그대로)."
- 장르 프로필(`docs/handoff/20`, `genre_prompt`)에 `default_stage` 키(geopolitics = mercator, macro_monetary·corporate·legal = backdrop). 연출 LLM 이 다르게 고르면 `reason` 필수(checks `stage_choice` warning).
- 코드가 무대를 바꾸지 않는다(P8).

## 3. 콘티 판·검사·provenance
- 콘티 판: 배경 = `[배경: id]` 자리표시(회색 판), 아일랜드 = 윤곽 + 종류 텍스트.
- checks: `island_overlap` hard, `backdrop_rights` hard(권리 기록 없는 사진), `backdrop_repeat` hard(연속 같은 사진), `stage_choice` warning. `[static-window]` 는 backdrop 무대에도 적용(변화 = 아일랜드 등장·배경 전환).
- provenance `stage: backdrop`, `backdrop.photos[]`, `islands[]`.

## 4. 범위 조정(D-0121 대비)
- §B 는 이 문서로 대체(시간축 안 아일랜드 → 무대 일반 규약). §A·§C·§D·§E 는 그대로. §E fed 재연출은 **backdrop 무대 + 차트 아일랜드**로.
- 골든(hormuz·랫클리프) 무변경(mercator). 데모는 timeline 무대 유지(순수 차트 검증용) — §A 검사만.
- 테스트 ≥ 10(무대 등록 세 곳·아일랜드 겹침·동시 수·권리·연속 사진·default_stage·stage_choice·콘티·provenance·mercator 골든 무변경).
- 문서: handoff 02(무대 셋)·20(default_stage)·08(아일랜드 공통)·14(배경 사진).

VERSION 은 5.1.0 그대로(MINOR). 결정 요청은 아일랜드 겹침 규칙·패널 통일 범위에서 나올 수 있다 — decision_request 로.
