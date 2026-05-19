<!--
tier: 2
last_synced_with: v0.2.1
ssot_for: [tts-spec, audio-spec, pronunciation-policy]
depends_on: [ANTIPATTERNS/TTS_ANTIPATTERNS.md]
last_review: 2026-05-19
-->

# 08 — Audio & TTS Spec

## 1. 음성 톤

- 낮고 굵은 남성.
- 차분함.
- 느리지만 또박또박.
- **과장된 예고편 톤 금지**.
- 사과·당부 구간은 톤 다운, 결론 구간은 톤 안정.

## 2. 발음 사전 (`pronunciation_ko.yaml`)

별도 YAML 파일을 두며 Worker가 TTS 호출 전 본 파일로 normalize 한다.
SSOT: `config/pronunciation_ko.yaml` (Phase 8에서 생성).

초기 항목 (예시):

```yaml
F-16: "에프 식스틴"
F-35: "에프 서른다섯"
Su-34: "수호이 서른넷"
Su-57: "수호이 쉰일곱"
MiG-29: "미그 스물아홉"
S-400: "에스 사백"
ATACMS: "에이태킴스"
HIMARS: "하이마스"
16시: "오후 네 시"
17시: "오후 다섯 시"
2차전지: "이차전지"
c-DN: "씨디엔"
R&D: "알앤디"
L/T: "리드타임"
3.5kg: "삼점오 킬로그램"
2026.05.19: "이천이십육년 오월 십구일"
```

## 3. TTS Pronunciation QA (필수)

흐름:
1. 원문 텍스트.
2. `pronunciation_ko.yaml` 적용 → normalized text.
3. TTS 생성 → wav.
4. ASR 재인식.
5. 원문 / 발음 사전 정답과 비교.
6. 실패 segment 자동 재생성.

본 단계 없이 최종 음성을 확정할 수 없다 (GOAL G4-9).

## 4. AI 티 안티패턴

본 시스템은 [docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md](ANTIPATTERNS/TTS_ANTIPATTERNS.md)에 정리된 항목을 모두 회피한다. Worker는 다음을 자동 검사한다.

- 숫자/단위/날짜 정규화 적용 여부
- 약어 발음 사전 일치
- 기호(/, -, →, :, ~, (), [], ※, ▲, ▼) 제거 또는 변환
- 문어체 → 구어체 변환
- URL / 파일 경로 음성 미낭독 (자막으로 우회)

## 5. 음성용 대본 vs 자막용 대본 분리

- **음성용 대본**: 발음형으로 정규화된 텍스트 (`narration_segments.json`).
- **자막용 대본**: 화면에 보이는 표기 (`scene_manifest`의 caption).
- 같은 문장이라도 둘은 다를 수 있다. 예: 자막 "16시", 음성 "오후 네 시".

## 6. BGM

- **생성형 음악 사용**. 유료 라이브러리 사용 안 함.
- 테마: 공포 / 긴장 / 격화 / 개전 / 협상 / 정보전 (chapter별 선택).
- 형식: 20–30초 루프.
- 악기: 느린 피아노, 첼로, 드론, 북소리.
- 매우 낮은 볼륨. 내레이션 방해 금지.

## 7. 믹싱

- 룸톤(미세 노이즈) 일부 유지 → 너무 매끈하지 않게.
- 치찰음 dampening.
- 문장 끝 잔향 살짝 유지.
- 압축 과도 사용 금지 (라디오 광고 톤 회피).

## 8. 호흡 / 리듬

- 긴 문장 강제 분할.
- 매 쉼표 동일 멈춤 회피 (Antipattern TTS-AP-08 참조).
- 문장 끝 톤이 매번 같지 않도록.

## 9. 운영 절차

[WORKFLOWS.md](../WORKFLOWS.md)의 W3, W4를 따른다.
