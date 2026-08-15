# portrait_cutout — 라이브러리용 인물 컷아웃 표준 프롬프트 (v1, 2026-08-15)

**라이브러리에 등록할 인물 자산은 본 템플릿으로 만든다.** 산출물은 배경·섀도가 없는
고대비 모노톤 인물 1장이며, 섀도·종이 배경·이름표는 전부 영상 렌더러가 런타임에 얹는다
(17 §1.7.0 — 사용자 확정 2026-08-15 "방식 B").

> **`portrait_panel.md` 와의 차이**: `portrait_panel.md` 는 **검수용 비교 시트**를 만드는
> 템플릿이라 종이 배경 + 섀도까지 그린다. 그건 눈으로 스타일을 판정하기 위한 것이고,
> **라이브러리 자산이 아니다.** 배포 자산은 반드시 본 템플릿을 쓴다 — 섀도가 구워지면
> 액센트 색이 영상마다 달라지는 설계(17 §1.7.1)가 깨진다.

`{ }` 슬롯만 치환해 사용.

---

> **프롬프트 본문은 영어다** (v1.0.13 전환). 이유 두 가지 — ① 한글 프롬프트를 셸
> 파이프로 codex 에 넘기면 인코딩이 깨진다(실측 2026-08-15: codex 가 mojibake 를
> 감지하고 스스로 영어로 재작성했다). ② 이미지 생성 모델이 영어 지시를 더 정확히
> 따른다. 설명·검수 기준 등 사람이 읽는 부분은 한국어를 유지한다 (C1 상 혼용 허용).

```
$imagegen

IMPORTANT:
Do not create this using HTML, CSS, SVG, Canvas, Pillow, matplotlib,
or other programmatic drawing methods.
Use the native image generation tool.
The final deliverable must be a generated raster image.

Input image 1 (style_anchor_portrait_v1.png) is the reference for TEXTURE AND TONE ONLY.
Follow only the portrait treatment from that sheet: high-contrast monochrome print texture.
Do NOT copy the paper background, the colored offset shadow, the colored outline,
the panel layout, or any labels from that sheet.

Input image 2 ({person_photo}) is the real photograph of {person_name}.
Preserve {person_name}'s real facial identity, proportions, expression, hair shape,
and recognizable facial details. Do NOT invent a new face.

Create:
- {person_name} only, upper body from the chest upward, vertical 4:5 aspect ratio.
- High-contrast monochrome editorial portrait.
- Newspaper print / halftone / engraving texture.
- Strong black-and-white contrast, clean white highlights, no gray haze.
- Preserve facial detail; do not rebuild the face as loose line art.

Background (critical):
- Pure white #FFFFFF solid background.
- No paper texture, grain, shadow, vignette, or gradient.
- No colored silhouette and no outline behind the subject.
- The subject edge must be crisp and clearly separated from the white background
  so the figure can be cut out later.

Forbidden:
- No text, names, labels, numbers, or watermark anywhere in the image.
- No color accents; pure black and white only.
- No frame, border, or corner decoration.

High resolution. Final output is a single generated raster portrait image.
```

## 슬롯

| 슬롯 | 값 | 예 |
|---|---|---|
| `{person_name}` | 인물 표기 (영문 권장 — 생성기 인식률) | `Xi Jinping` |
| `{person_photo}` | `references/` 안의 실사진 파일명 | `photo_xi_jinping.jpg` |

## 산출·등록

```
공방 산출:   output/{person_id}_mono_v{NN}.png  +  같은 이름 .prompt.txt
배경 제거:   → 알파 채널 컷아웃
라이브러리:  assets/library/people/{person_id}_mono_v{NN}.png
```

`person_id` 는 17 §0.8 규약 (로마자 lowercase snake — `xi_jinping`, `jensen_huang`).

## 검수 기준

1. **얼굴이 그 사람인가** — 실사진과 대조. 닮은 다른 사람이 되면 반려 (G4).
2. **프로 인쇄물로 보이는가** — "이목구비 식별 가능" 수준은 불합격 기준이다
   (v0.45.0 반려 교훈).
3. **오려낼 수 있는가** — 인물 가장자리가 흰 배경과 뚜렷이 분리되는가.
   머리카락이 배경에 녹아 있으면 배경 제거가 실패한다.
4. **금지 요소가 없는가** — 섀도·종이·텍스트·컬러가 하나라도 있으면 반려.
