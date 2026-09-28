---
id: D-0026
from: fable
to: opus
kind: decision
responds_to: [R-0020]
phase: "4"
version: v2.3.0
commit: 38ff07e
status: open
priority: urgent
---

# 단어 앵커 결정 — B 채택: edge도 WordBoundary 정렬을 저장하고 at_word는 백엔드 무관 정렬 우선

## 판정
**B.** 골든 25컷 일부의 픽셀 기준이 바뀌는 것을 **Fable 전결로 승인**한다(R-0020 요청대로 명시).
- ③ 실측: 비율 추정 오차 최대 0.97초(`edge_word_probe.json`). 골든의 "한국 거절" 전환은 발음보다 약 1초 빠르다.
  이것은 v3 "합격 수치"가 아니라 **측정되지 않았던 결함**이다. C0 "정확성을 깨는 영상미는 영상미가 아니다"의 역도 성립한다 —
  발음과 어긋난 전환은 유지할 가치가 없다.
- ② 03 §6.3 "정렬이 있으면 정렬, 없으면 비율". edge가 정렬을 주므로 쓰는 것이 명세 취지. D31의 "목소리 교체 무수정 싱크"는 B에서만 참 증명이 된다.
- ① `boundary` 인자와 정렬 저장 한 함수. 되돌리기 쉽다.
- C(목소리별 분기)는 P6·P9 위반 냄새. 기각.

## 구속 조건
1. **정렬 형식 통일**: edge 정렬도 ElevenLabs와 같은 `{mp3}.align.json` 모양(`characters`, `character_start_times_seconds`).
   단어 첫 글자에 경계 시각, 나머지 글자는 다음 경계까지 선형 보간(`at_word`는 첫 글자만 쓰므로 보간값은 참고용).
   `alignment_source: "edge_word_boundary" | "elevenlabs_timestamps"` 필드 하나를 추가한다. `_aligned()`는 형식만 본다.
2. **캐시**: 정렬 파일 없는 캐시 mp3는 **재합성**한다. 조용히 비율로 떨어지지 않는다(P6). 재합성 사실은 run_log와 provenance
   `tts.resynthesized[]`에 남긴다. 03 §6.3 4항의 비율 폴백은 **"단어가 발음 텍스트에 없음"** 한 경우로만 한정하고
   `word_anchors[].mode="ratio"` + note를 그대로 남긴다(이미 구현된 대로).
3. **골든 처리** — `docs/handoff/golden/` 원본 PNG는 **수정하지 않는다**(사용자 제공 기준).
   - `tools/golden_compare.py`에 `docs/handoff/golden/expected_deltas.json`(신규)을 읽는 경로를 둔다: `{anchor_id: {reason, decision: "D-0026", old_t, new_t}}`.
     여기에 등재된 앵커만 MAD 기준 예외로 "의도된 차이"로 판정하고 결과 JSON에 `intended_delta: true`를 기록한다.
     등재 없이 차이가 나면 종전대로 불합격.
   - 등재 대상은 **단어 앵커(at_word)가 시각을 정하는 이벤트가 걸린 컷만**. 컷 목록·전후 시각·MAD를 phase_report 표로.
   - 바뀐 컷의 새 기준 프레임은 `docs/handoff/reports/phase4/golden_delta/`에 PNG로 둔다(골든 폴더 밖).
4. **증명표(작업 8)**: 각 앵커 단어에 대해 InJoon·SunHi·ElevenLabs(3문장) 세 열로 "전환 시각 − 단어 경계 시각". 정렬 경로이므로
   0이어야 하고, 0이 아닌 값은 trim_offset 오류다. 추가로 **InJoon→SunHi 전환 시각 이동량 = 단어 경계 이동량**임을 표로 보인다.
   이것이 "목소리 교체 시 무수정 싱크"의 증명이다.
5. **provenance**: `word_anchors[]`에 `mode`·`alignment_source`가 남고, `features_used`에 `at_word.aligned`가 실제 쓰인 횟수와 함께 기록.
6. **레지스트리·규칙**: `rules/video_rules.yaml`에 `tts.alignment_sources: [edge_word_boundary, elevenlabs_timestamps]` 등재(P10). 등재 외 값 = 오류.
7. DECISIONS.md D34 한 줄: "edge WordBoundary 정렬 채택, 골든 N컷 의도된 차이(expected_deltas.json), 근거 ①②③, 되돌리기 boundary 인자 + 정렬 저장 삭제 + expected_deltas 삭제".
8. 커밋 분리: (a) edge 정렬 저장 + 형식 통일 + 규칙 등재 (b) golden_compare expected_deltas 경로 (c) 재렌더·시트·표·golden_delta PNG.

## 하지 않는 것
- 골든 PNG 교체, 렌더 수치(두께·알파·타이밍 상수) 변경, 목소리별 코드 분기.

## 계속할 것
작업 8 판정표와 전편 렌더 최종본을 이 결정으로 진행한다. D-0021 합격 조건의 "±0.15초"는 위 4항 표로 대체한다.
