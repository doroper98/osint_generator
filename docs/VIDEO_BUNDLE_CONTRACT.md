<!--
tier: 2
last_synced_with: v0.38.0
ssot_for: [video-bundle-contract]
depends_on: [05_DATA_SCHEMA_SPEC.md]
last_review: 2026-06-12
-->

# VIDEO_BUNDLE_CONTRACT — agents_reviewer ↔ osint_generator 영상 필드 계약

> 상태: **확정** (2026-06-12). agents_reviewer 구현 완료
> (analysis_20260606_114653 번들부터), osint_generator 소비 구현 v0.38.0.

## 목적

- 영상 자막/내레이션의 템플릿 문장 탈피 (옵션 C 2차) — 생성 주체를
  보고서 작성 시점의 agents_reviewer LLM 으로 이동.
- 차트 없는 서술(prose) 전용 섹션의 영상 누락 해소.
- 영상 파이프라인은 LLM 무호출 결정론 유지.

## 스키마 (전부 optional / additive — schema_version 1 유지)

### sections[i].video

| 키 | 타입 | 규칙 |
|---|---|---|
| narration | string[] | 2~4문장, 문장당 ≤ 58자. 해당 섹션 구간의 자막·음성 대본 |
| narration_tts | string[] | (선택) 발음 안전 표기 버전. 자막=narration, 음성=narration_tts |
| highlights | string[] | 1~3개, 항목당 ≤ 40자. 스테이트먼트 씬용 key takeaway |
| emphasis | string[] | highlights/narration 의 정확한 부분 문자열만. 액센트 강조 |

### report.video

| 키 | 타입 | 용도 |
|---|---|---|
| intro_narration | string[] | 타이틀 씬 대본 1~2문장 |
| outro_narration | string[] | 클로징 씬 대본 1~2문장 |

## 작성 규칙 (요약 — 전문은 전달 프롬프트와 동일)

1. **사실 근거**: 모든 수치·날짜·고유명사는 같은 섹션 prose 또는 번들
   구조 데이터에 존재해야 함. 위반 문장은 영상 쪽 검증기가 폐기 후
   템플릿 폴백 (G4).
2. 다큐 브리핑체, 과장 금지, 문장 간 연결 의식.
3. 미검증 주장은 문장 내 `<미검증>` 표기 (C9/G4).
4. 한 문장 ≈ 화면 4~6초.

## 영상 쪽 소비 규칙 (osint_generator 구현 의무)

- `video` 존재 시: highlights → 스테이트먼트 씬, narration → 구간 자막.
  차트 섹션의 narration 은 해당 차트 씬 자막으로 사용 (템플릿 대체).
- `video` 부재 시: 기존 동작 (하위 호환).
- **검증기**: narration/highlights 의 수치·날짜·고유명사를 번들과 대조,
  불일치 시 해당 문장 폐기 + 템플릿 폴백 + 로그. (구현 예정 — 본 계약
  확정 후 착수)

## 이력

- 2026-06-12: 초안 작성, 사용자가 agents_reviewer 세션에 전달 (v0.37.2).

- 2026-06-12: agents_reviewer 구현 확인 (전 섹션 video + narration_tts),
  osint_generator 소비 구현 (v0.38.0) — 계약 확정.
