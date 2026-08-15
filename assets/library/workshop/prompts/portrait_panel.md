# portrait_panel — 검수용 인물 패널 프롬프트 (v1, 2026-08-15)

> ⚠️ **본 템플릿은 라이브러리 자산용이 아니다** (v1.0.9 정정). 종이 배경과 컬러 섀도까지
> 그려 넣기 때문에 섀도 색이 파일에 굳어져(baked), "액센트는 영상마다 카테고리·아트
> 디렉터가 고른다"는 설계(17 §1.7.1)가 깨진다.
>
> | 용도 | 템플릿 |
> |---|---|
> | **라이브러리 등록용 인물 자산** | **[`portrait_cutout.md`](portrait_cutout.md)** ← 이걸 쓸 것 |
> | 스타일 검수용 비교 시트 (눈으로 톤 판정) | 본 문서 |

인물 1명 패널. `{ }` 슬롯만 치환해 사용. 원형은 사용자 제작 4인물 시트
(2026-08-14 검수 통과)의 프롬프트 어휘를 정식화한 것.

---

```
$imagegen

IMPORTANT:
Do not create this using HTML, CSS, SVG, Canvas, Pillow, matplotlib,
or other programmatic drawing methods.
Use the native image generation tool.
The final deliverable must be a generated raster image.

첨부 이미지 1 (style_anchor_portrait_v1.png)은 스타일·레이아웃 참고용이다.
첨부 이미지 2 ({person_photo})는 인물의 실제 사진이다 — 이 인물의 얼굴 특징을
정확히 유지한 채 아래 스타일로 가공하라. 얼굴을 새로 지어내지 마라.

구성:
- 단일 인물 패널 (세로 4:5)
- warm ivory/beige crumpled newsprint paper background
  — 실제 종이를 구겼다가 다시 펼친 듯한 큰 주름과 작은 주름이 함께 보이는 crease texture
- 인물은 high-contrast monochrome editorial portrait
  — 신문 인쇄물 / halftone / engraving 질감, 하이라이트는 깨끗한 흰 면
- 인물 뒤에 {accent_color} 의 {shadow_desc}
- 전체적으로 Financial Times, Bloomberg Businessweek, Economist
  editorial illustration 계열의 정제된 분위기
- 패널에 accent color 는 한 가지만 사용한다
- 이미지 안에 어떤 텍스트도 넣지 않는다 (이름·라벨·숫자 금지)

Aspect ratio 4:5. 고해상도. 완성된 단일 panel image 로 생성한다.
```

## {shadow_desc} 값 (17 §1.7.1 섀도 3축)

| 조합 | 문구 |
|---|---|
| offset + solid | solid offset silhouette (한쪽으로 밀린 실루엣, 경계 명확) |
| offset + hatch | offset silhouette filled with diagonal hatch texture |
| offset + dots | offset silhouette filled with regular dot pattern |
| outline + solid | thick solid outline hugging the figure (스티커 키라인, 경계 명확) |
| outline + dots | dotted outline ring hugging the figure |

## {accent_color} 가이드

카테고리 액센트(07 §4) 또는 인물 `accent_hint`. 예: muted red `#B03A2E`,
mustard/ochre `#C9862B`, cyan/teal `#3E6E8E`, deep red `#8B2E2E`.

## 검수용 비교 시트가 필요할 때

위 본문을 "2x2 인물 포스터, 두꺼운 charcoal-black 외곽 프레임과 중앙 divider" 구성으로
바꾸고 패널별 인물·섀도 조합을 나열한다 (이때만 패널 라벨 텍스트 허용 — condensed/grotesk
bold sans-serif). 원형: 사용자 4인물 시트 프롬프트.
