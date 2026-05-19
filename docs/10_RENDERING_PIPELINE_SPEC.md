<!--
tier: 2
last_synced_with: v0.2.1
ssot_for: [rendering-pipeline]
depends_on: [05_DATA_SCHEMA_SPEC.md, ADDENDUM_02_PRE_PRODUCTION_DEBUG_LAYER.md]
last_review: 2026-05-19
-->

# 10 — Rendering Pipeline Spec

## 1. 렌더 엔진

- **Remotion** (Node 20 LTS). React 기반 코드형 영상 합성.
- **FFmpeg**. 트랜스코딩·오디오 믹싱·자막 burn-in (필요 시).

## 2. Render Mode 3종

| 모드 | 입력 manifest | 산출물 | Debug Layer |
|---|---|---|---|
| `debug` | `remotion_job_debug.json` | `draft_debug.mp4` | **표시** |
| `preview` | `remotion_job_preview.json` | `draft_preview.mp4` | 미표시 |
| `final` | `remotion_job_final.json` | `final.mp4` | 금지 |

## 3. 빌드 순서

```
scene_manifest.json
asset_manifest.json
audio_manifest.json
music_manifest.json
annotation_manifest.json
       │
       ▼
workers/remotion_job_builder.py
       │
       ├──→ remotion_job_debug.json   ─→ workers/render_worker.py ─→ draft_debug.mp4
       ├──→ remotion_job_preview.json ─→ workers/render_worker.py ─→ draft_preview.mp4
       └──→ remotion_job_final.json   ─→ workers/render_worker.py ─→ final.mp4
```

## 4. RemotionJob 핵심 필드

`schemas/models.py:RemotionJob` 참조. 핵심 필드 요약:

| 필드 | 설명 |
|---|---|
| `schema_version` | 1 |
| `episode_id` | project_id와 연결 |
| `render_mode` | `debug` / `preview` / `final` |
| `composition` | Remotion composition 이름 |
| `format` | `mp4` / `webm` |
| `style` | font / 자막 / 색상 토큰 |
| `scenes` | `SceneEntry[]` (worker_provenance 포함) |
| `audio` | narration wav 경로 + 동기화 정보 |
| `music` | BGM loop 경로·구간 |
| `subtitles` | `srt` 또는 inline 자막 |
| `source_links` | 화면 하단 출처 표기용 |
| `debug_layer` | `{enabled, position, opacity}` (final은 enabled=false 강제) |

## 5. Remotion 컴포넌트 카탈로그

| 파일 | 책임 |
|---|---|
| `remotion/src/LongformBriefingComposition.tsx` | 메인 composition |
| `remotion/src/MapScene.tsx` | 지도 장면 |
| `remotion/src/XSourceCardScene.tsx` | X Source Card |
| `remotion/src/TelegramSourceCardScene.tsx` | Telegram Source Card |
| `remotion/src/ArticleCaptureScene.tsx` | 기사 캡처 장면 |
| `remotion/src/VideoSourceFrameScene.tsx` | 원본 영상 액자 |
| `remotion/src/ChartScene.tsx` | 차트 장면 |
| `remotion/src/ImageScene.tsx` | 정지 이미지 + slow zoom |
| `remotion/src/ChapterDivider.tsx` | 챕터 구분 |
| `remotion/src/SubtitleLayer.tsx` | 자막 |
| `remotion/src/SourceLinkLayer.tsx` | 우하단 출처 표기 |
| `remotion/src/AnnotationLayer.tsx` | 형광펜·동그라미·화살표 |
| `remotion/src/InferenceBadge.tsx` | `<추론>` / `<미검증>` 라벨 |
| `remotion/src/DebugOverlay.tsx` | Pre-production Debug Layer |
| `remotion/src/ThumbnailComposition.tsx` | 썸네일 composition |

## 6. 렌더 파라미터

- 해상도: 1920×1080 (16:9). 16분 영상 기준 약 30분–2시간 렌더.
- 프레임 레이트: 30fps 기본, 60fps 옵션.
- 코덱: H.264 + AAC (mp4).
- CRF: debug 28, preview 23, final 18.
- threads: `config.yaml:render.threads`.

## 7. 안전장치

- `render_mode=final`이면 `debug_layer.enabled=False`를 강제 덮어쓰기 (Render Worker 책임).
- `final.mp4` 생성 직후 OCR/메타데이터 검증 (Phase 9 후속).
- 렌더 실패 시 `render_report.json`에 stderr 끝부분 100줄 저장.

## 8. 운영 명령

```bash
python -m workers.render_worker \
  --project-id {pid} \
  --render-mode debug
```
