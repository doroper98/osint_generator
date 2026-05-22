<!--
tier: 2
last_synced_with: v0.3.3
ssot_for: [pre-production-debug-layer, scene-provenance]
depends_on: [05_DATA_SCHEMA_SPEC.md, 10_RENDERING_PIPELINE_SPEC.md]
last_review: 2026-05-19
-->

# ADDENDUM 02 — Pre-production Debug Layer

## 1. 목적

초기 운영 기간 동안 Worker별 품질을 튜닝하기 위해, 각 scene이 어떤 Worker / 어떤 source / 어떤 asset에서 만들어졌는지를 영상 안에 **눈으로 확인 가능한 형태**로 띄운다.

## 2. 적용 매트릭스

| 렌더 모드 | Debug Layer | 산출물 |
|---|---|---|
| `debug` | **표시** | `draft_debug.mp4` |
| `preview` | 미표시 | `draft_preview.mp4` |
| `final` | **금지** | `final.mp4` |

> `final.mp4`에 Debug Layer가 포함되면 [GOAL.md G4-6](../GOAL.md#g4-금지사항-prohibitions) 위반. CI/git hook 검증 대상.

## 3. 표시 위치

화면 **왼쪽 상단**, 폭 30%, 반투명 검정 배경 + 흰 글씨, 폰트 크기 작게.

## 4. 표시 정보 (한 scene당)

```
sc_0042 | video_frame_scene
worker: video_acquisition_worker
src: src_0012, src_0018
asset: ast_0033
qa: rights_review_required
risk: graphic_content
```

다음 필드를 `SceneEntry.worker_provenance`에서 직접 읽는다:

| 라벨 | 데이터 |
|---|---|
| 1행 | `scene_id` \| `scene_type` |
| 2행 | `worker: {primary_worker}` |
| 3행 | `src: {source_ids[:3]}` |
| 4행 | `asset: {asset_ids[:3]}` |
| 5행 | `qa: {qa_status}` |
| 6행 | `risk: {risk_flags}` |

## 5. 구현

- **Remotion 컴포넌트**: `remotion/src/DebugOverlay.tsx`
- **활성 조건**: `props.renderMode === "debug"`
- **데이터 소스**: `RemotionJob.scenes[].worker_provenance`
- **컴포지션**: 모든 scene 위에 절대 위치(`position: absolute`)로 합성

```tsx
// 의사 코드
if (props.renderMode === "debug") {
  return <DebugOverlay provenance={scene.worker_provenance} />;
}
return null;
```

## 6. 운영상 이점

1. **Worker 튜닝**: "이 장면이 어색하다" → Debug Layer에서 어떤 Worker가 만들었는지 즉시 확인.
2. **소스 추적**: 미검증 정보가 어떤 source에서 왔는지 검토.
3. **권리 점검**: `risk_flags`가 빨갛게 표시되어 누락 점검.
4. **scene_id 충돌 발견**: 동일 scene_id 중복이 화면에서 즉시 보임.

## 7. 안전장치

- Render Worker는 `render_mode=final`이면 `RemotionJob`에 `debug_layer.enabled=false`를 **강제로** 덮어쓴다.
- CI 단계에서 `final.mp4`에 대해 OCR 또는 메타데이터로 Debug Layer 흔적이 없음을 검증한다. (Phase 9 후속)

## 8. 비활성화 시점

전체 채널이 Phase 11까지 안정화되어 평균 사람 개입 시간이 일정 수준 이하로 떨어지면, 본 기능을 끄는 옵션을 운영자가 선택할 수 있도록 한다. 단, 기본값은 항상 **debug 렌더 시 활성**.
