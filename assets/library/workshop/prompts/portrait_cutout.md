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

```
$imagegen

IMPORTANT:
Do not create this using HTML, CSS, SVG, Canvas, Pillow, matplotlib,
or other programmatic drawing methods.
Use the native image generation tool.
The final deliverable must be a generated raster image.

첨부 이미지 1 (style_anchor_portrait_v1.png)은 **질감과 톤의 기준**이다.
그 시트의 인물 처리 방식(고대비 모노톤 인쇄 질감)만 따르고,
**시트에 보이는 종이 배경과 컬러 섀도는 따라 그리지 마라.**

첨부 이미지 2 ({person_photo})는 {person_name}의 실제 사진이다.
이 인물의 얼굴 특징을 정확히 유지한 채 아래 스타일로 가공하라.
얼굴을 새로 지어내지 마라.

만들 것:
- {person_name} 한 사람만. 상반신 (가슴 위), 세로 4:5
- high-contrast monochrome editorial portrait
  — 신문 인쇄물 / halftone / engraving 질감
  — 강한 흑백 대비, 하이라이트는 깨끗한 흰 면, 회색 안개 금지
  — 얼굴 디테일은 보존한다 (획으로 재구성하지 마라)

배경 (중요):
- 배경은 **순백(pure white #FFFFFF) 단색**으로 한다
- 배경에 종이 질감, 그레인, 그림자, 비네트, 그라데이션을 넣지 마라
- 인물 뒤에 어떤 색 실루엣도, 어떤 외곽선도 넣지 마라
- 인물 윤곽이 배경과 명확히 분리되어야 한다 (인물 가장자리가 흰색으로
  흐려지면 안 된다 — 오려낼 수 있게 경계가 뚜렷할 것)

금지:
- 이미지 안에 어떤 텍스트도 넣지 않는다 (이름·라벨·숫자·워터마크 금지)
- 컬러 액센트 금지 — 순수 흑백만
- 프레임, 테두리, 모서리 장식 금지

Aspect ratio 4:5. 고해상도. 완성된 단일 인물 이미지로 생성한다.
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
