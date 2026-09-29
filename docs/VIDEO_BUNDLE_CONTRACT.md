<!--
tier: 2
last_synced_with: v4.5.0
ssot_for: [video-bundle-contract]
depends_on: [05_DATA_SCHEMA_SPEC.md]
last_review: 2026-09-29
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
| narration | string[] | 2~4문장, 문장당 ≤ **75자** (1차 검수 개정 — 축약하지 말고 말하듯 풀어쓸 것). 해당 섹션 구간의 자막·음성 대본 |
| narration_tts | string[] | (선택) 발음 안전 표기 버전. 자막=narration, 음성=narration_tts |
| highlights | string[] | 1~3개, 항목당 ≤ 40자. 스테이트먼트 씬용 key takeaway |
| emphasis | string[] | highlights/narration 의 정확한 부분 문자열만. 액센트 강조 |

### report.video

| 키 | 타입 | 용도 |
|---|---|---|
| intro_narration | string[] | 타이틀 씬 대본 1~2문장 |
| outro_narration | string[] | 클로징 씬 대본 1~2문장 |

### timeline.video (1차 검수 개정으로 추가)

| 키 | 타입 | 용도 |
|---|---|---|
| narration | string[] | 타임라인 씬 대본 3~4문장 — 분기점 라벨 낭독 금지, 이야기로 연결 |
| narration_tts | string[] | 발음 표기 버전 |

## 작성 규칙 (요약 — 1차 음성 검수 개정 반영, 2026-06-12)

1. **사실 근거**: 모든 수치·날짜·고유명사는 같은 섹션 prose 또는 번들
   구조 데이터에 존재해야 함. (v4.0.0: 영상 쪽은 번들 문장을 최종 원고로 쓰지 않는다 — 아래 소비 규칙)
2. **풀어쓰기**: 자막용 요약문이 아니라 성우가 읽는 구어체 대본. 명사 나열
   대신 주어-동사 문장. 축약하려고 조사·서술어를 삭제하지 말 것.
3. **날짜는 조사로 연결**: "{날짜}, {문장}" 나열 금지 → "{날짜}에는 ~했습니다".
4. **제목·라벨 낭독 금지**: 화면이 보여주는 텍스트를 따라 읽지 말 것.
5. **narration_tts 발음 강화**: 숫자 전부 한글("32개월"→"삼십이 개월",
   "7개"→"일곱 개"), 경음화 소리 나는 대로("해지권"→"해지꿘"), 영문 약어
   한글 표기. 원칙: "한글로 받아쓴 발음 그대로".
6. 다큐 브리핑체, 과장 금지, 미검증 주장은 `<미검증>` 표기 (C9/G4).
7. 한 문장 ≈ 화면 4~6초.

## 영상 쪽 소비 규칙 (osint_generator v3.5.0 번들 어댑터 — v4.0.0 동기화)

- 번들은 **재료**다(handoff 12 §5). `bundle/to_script.py`가 `video.narration`·`narration_tts`를 원고 **초안**(`script.draft.yaml`)으로 옮긴다.
  `narration_tts`는 그대로, 없으면 발음 규칙(handoff 03 §4)으로 만든다. highlights·섹션 heading은 챕터명·강조 후보로만 쓴다.
- 최종 원고는 ScriptWorker가 사실 목록(`facts.json`)과 claims로 다시 쓴다. 문장마다 claim id 출처가 필요하다.
- 금지 문구(`rules/video_rules.yaml banned_phrases`)가 걸린 문장은 초안에 `rewrite_required` 주석만 단다. 코드가 몰래 고치지 않는다.
- **템플릿 폴백은 없다**(G4-20, 15 P6). 옛 "불일치 시 문장 폐기 + 템플릿 폴백" 규칙은 v2.0.0 에서 폐기됐다.
- `video` 부재 시: 초안 없이 소스 인테이크 경로(sources·claims → facts → 원고)로 간다.

## 이력

- 2026-06-12: 초안 작성, 사용자가 agents_reviewer 세션에 전달 (v0.37.2).

- 2026-06-12: agents_reviewer 구현 확인 (전 섹션 video + narration_tts),
  osint_generator 소비 구현 (v0.38.0) — 계약 확정.
- 2026-06-12: 1차 음성 영상 검수 개정 — narration ≤ 75자, 풀어쓰기/날짜 조사/
  제목 낭독 금지/발음 강화 규칙, timeline.video 신설. 양측 배포:
  agents_reviewer (A 패키지), osint_generator v0.38.2~3 (B 패키지 — 템플릿
  cue tts/유월·시월 날짜 발음/숨소리 컷/자막 75자+폰트 축소/캘린더/억양 문맥).
