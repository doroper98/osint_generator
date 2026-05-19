<!--
tier: 2
last_synced_with: v0.1.1
ssot_for: [thumbnail-system]
depends_on: [07_VIDEO_STYLE_GUIDE.md]
last_review: 2026-05-19
-->

# 11 — Thumbnail System Spec

## 1. 원칙

- 어두운 배경.
- 강한 한글 폰트.
- 실사 대표 이미지 사용.
- 지도 또는 차트 보조 사용.
- 카테고리별 색상 시스템 ([07_VIDEO_STYLE_GUIDE.md §4](07_VIDEO_STYLE_GUIDE.md#4-색상-시스템)) 적용.
- **AI 생성 이미지 사용 금지**.
- 영상 제목과 썸네일 문구 중복 금지.

## 2. 문구 규칙

- 2–5단어, 최대 7단어.
- 모바일에서 읽혀야 함.
- 미검증 주장 금지.
- 과장 금지 (`경악`, `충격` 등 어휘 회피).

## 3. 레이아웃 2–3개 고정

본 채널은 시간이 지나도 인지도가 누적되도록 **고정 레이아웃**을 유지한다.

| 레이아웃 | 구성 |
|---|---|
| L1 | 좌측 대표 이미지 + 우측 큰 문구 |
| L2 | 상단 문구 + 하단 지도 |
| L3 | 풀스크린 사진 + 하단 띠 문구 |

## 4. 산출물 파이프라인

```
full_script.json
project_manifest.json
       │
       ▼
Thumbnail Agent → thumbnail_brief.json
       │
       ▼
Thumbnail Worker (Remotion ThumbnailComposition)
       │
       ├──→ 시안 2–4개 (thumbnail_manifest.json)
       │
       ▼
사용자 선택 (Review Gate 8)
       │
       ▼
thumbnail.png
```

## 5. QA 항목 (`thumbnail_qa.json`)

- 미검증 정보 포함 여부
- 카테고리 색상 일치 여부
- 권장 폰트 사용 여부
- 문구 글자 수 제한 준수
- 모바일 가독성 시뮬레이션 결과

## 6. Remotion 컴포넌트

`remotion/src/ThumbnailComposition.tsx`. 1920×1080.

상세 데이터 모델: `schemas/models.py:ThumbnailManifest`.
