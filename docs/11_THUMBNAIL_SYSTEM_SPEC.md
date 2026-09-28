<!--
tier: 2
last_synced_with: v4.0.0
ssot_for: [thumbnail-system]
depends_on: [07_VIDEO_STYLE_GUIDE.md, ../GOAL.md]
last_review: 2026-09-29
-->

# 11 — Thumbnail System Spec

> **구현 상태(v4.0.0 실측)**: v2 엔진에는 썸네일 생성 단계가 아직 없다. GOAL G1 의 `out/thumbnail_candidates/` 는 목표 산출물이고, 지금 파이프라인(DELIVER)은 만들지 않는다.
> 아래 §1~§3·§5 는 편집 원칙으로 유지한다. v1 파이프라인(Thumbnail Agent → Remotion `ThumbnailComposition`, Review Gate 8)은 v2.0.0 에서 삭제됐다.

## 1. 원칙

- 어두운 배경.
- 강한 한글 폰트.
- 실사 대표 이미지 사용.
- 지도 또는 차트 보조 사용.
- 색 토큰은 영상과 같다(`rules/video_rules.yaml colors`, [07](07_VIDEO_STYLE_GUIDE.md) §5).
- 사실 장면을 AI로 생성하지 않는다. AI 가공은 실자료 입력 가공만(GOAL G4-10), 글자는 코드 렌더.
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

미구현(위 구현 상태). 만들 때는 엔진 CLI 단계로 넣고([10](10_RENDERING_PIPELINE_SPEC.md) §1), 사람 게이트 ② 또는 별도 선택 화면에서 고른다. 미검증 정보를 제목·썸네일에 쓰지 않는다(G4-7).

## 5. QA 항목 (`thumbnail_qa.json`)

- 미검증 정보 포함 여부
- 카테고리 색상 일치 여부
- 권장 폰트 사용 여부
- 문구 글자 수 제한 준수
- 모바일 가독성 시뮬레이션 결과

## 6. (v2.0.0 삭제) Remotion 컴포넌트

`remotion/` 은 삭제됐다(보존본 `archive/hyperframes-briefing`). v1 모델 `schemas/models.py:ThumbnailManifest` 는 지금 쓰는 코드가 없다.
