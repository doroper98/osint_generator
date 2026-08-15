# AGENTS.md — 자산 공방 (codex 이미지 가공 작업 규칙)

본 디렉토리는 osint_generator 쇼츠 콜라주의 **자산 공방(workshop)**이다. 여기서 codex 는
코드를 짜는 것이 아니라 **이미지를 생성·가공**한다. 상위 정책: 저장소 root `GOAL.md` G4-10
(v1.0.0) 및 `docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md` §2.0.

## 절대 규칙

1. **이미지 산출은 반드시 네이티브 이미지 생성 기능(`$imagegen`)으로 만든다.**
   HTML, CSS, SVG, Canvas, Pillow, matplotlib 등 프로그램적 드로잉으로 "그리는 것" 금지.
   최종 산출물은 생성된 래스터 이미지(PNG)여야 한다.
2. **실존 인물·로고·사물은 실사진 입력이 있을 때만 가공한다.** 참고 사진 없이 상상으로
   실존 대상을 생성하는 것 금지 (G4-10). 입력 사진은 `codex -i` 로 첨부되거나
   `references/` 에 있다.
3. **이미지 안에 텍스트(이름·수치·라벨)를 넣지 않는다.** 자막·이름표·검증 라벨은 영상
   렌더러가 코드로 얹는다. (검수용 비교 시트의 패널 라벨만 예외.)
4. **스타일 앵커 준수**: `references/style-reference.png` (사용자 검수 통과본)와 같은
   시각 시스템 — warm ivory/beige crumpled newsprint 배경, high-contrast monochrome
   editorial portrait(halftone/engraving 인쇄 질감), 인물 뒤 단일 accent color 의
   silhouette(offset) 또는 outline(감싸는 키라인), 채움은 solid/hatch/dots 중 하나.
   FT·Bloomberg Businessweek·Economist 계열의 정제된 에디토리얼 무드. 패널당 액센트 1색.
5. **산출 규격**: 라이브러리용 단일 인물 = 세로 4:5, 고해상도. 명명은
   `docs/17_COLLAGE_DESIGN_SHEET.md §0.8` 규약을 따른다.

   | 단계 | 경로 | 비고 |
   |---|---|---|
   | 공방 산출 (검수 대기 후보) | `output/{person_id}_{shadow_shape}_{fill}_v{NN}.png` | 검수용이라 섀도가 구워져 있어도 된다 |
   | 라이브러리 승격본 | `assets/library/people/{person_id}_{style}_v{NN}.png` | **섀도를 파일명에 넣지 않는다** — 17 §1.7 상 섀도는 런타임 합성이고, 파일명에 박으면 액센트가 영상마다 달라지는 설계와 모순된다 |

   `person_id` 는 로마자 lowercase snake (§0.8) — 예: `xi_jinping`, `jensen_huang`.
   사용한 프롬프트 전문은 산출물과 같은 경로에 `{같은이름}.prompt.txt` 로 저장한다
   (G4-10 기록 의무 — 등록 시 manifest 의 `tool="codex_imagegen"`, `prompt_ref` 로 연결됨).
6. **권리**: 입력 사진의 출처·라이선스가 `references/RIGHTS.md` 에 없으면 작업을 멈추고
   보고한다. 산출물은 입력 사진의 권리를 승계한다.

## 표준 작업 흐름

```
codex -i "references/style-reference.png" -i "references/{인물사진}"
→ prompts/portrait_panel.md 의 템플릿에 인물·섀도 파라미터만 치환해 입력
→ 산출 PNG + prompt.txt 를 output/ 에 저장
→ (오케스트레이터/사용자) 검수 → 통과본만 assets/library/people/ 로 승격 등록
```

## 사전 점검 (세션마다 1회)

`/skills` 로 imagegen 노출 확인 → 안 보이면 작업 중단 후 보고 (알려진 Windows/CLI 이슈 —
계획 §2.0.1, 폴백은 OpenAI Images API).
