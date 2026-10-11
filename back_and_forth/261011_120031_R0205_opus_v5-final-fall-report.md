---
id: R-0205
from: opus
to: fable
kind: phase_report
responds_to: [D-0175]
phase: "V5"
version: v5.20.0
commit: (이 보고와 같은 커밋)
status: done
---

# V5 완료 — 문장 끝 억양 보정(끝 3글자 4반음 선형 하강, D169 시안 C)

상세는 `docs/handoff/reports/phaseV5/run_log.md` 입니다.

## 1. 합격 조건
| 조건 | 결과 |
|---|---|
| 모듈·위치 | `script/tts/prosody.final_fall` — D-0175 §1 시제품 순서·값 그대로. `script.plan` 디코드 → 보정 → 트림 → npy. mp3·`.align.json` 무변경 |
| 규칙(P3) | `rules tts_rules.prosody.final_fall{…}`, `FinalFallRules` extra=forbid, 모듈 값 상수 0(테스트) |
| 기록(P5) | plan row `prosody.final_fall` → `features_used.prosody.final_fall{applied_n 45, skipped_n 0}` |
| 의존성 | `pyworld>=0.3`(MIT, 0.3.5 설치), 없으면 `ProsodyError` |
| 결정성·길이 | 같은 입력 2회 바이트 동일, 길이 = 원본 |
| 테스트 ≥ 7 | `test_v5_prosody` 9(구간 선택·비해당 바이트 동일·구간 앞 바이트 동일·끝 −4반음 ±1·결정성·트림 자리·규칙 상수·pyworld 없음 오류·provenance) |
| 게이트 영향 0 | 게이트는 mp3 를 읽음 + 보정 음성의 음향 발화 시작 45/45 원음과 같음 |
| 호르무즈 재현 | 260.66초 그대로, 프리뷰 **phaseV3 25/25**, 전편 720p·mux 통과, audio_qa 네 판정 통과(−14.11 LUFS · TP −1.66 · 음악−내레이션 −9.75 dB, 문장 RMS 변화 ≤ 0.10 dB) |
| 전체 pytest | **1530 passed · 0 · 0**(dark·light 골든 25/25) |

## 2. 기록할 판단·결함
- **트림 자리 = 원음(판단, 되돌릴 수 있음)**: 첫 실행에서 보정 음성을 그대로 트림하니 총길이가 260.66 → 260.86초로 바뀌었습니다(합성 꼬리 잡음이 무음 문턱을 넘음). 타임라인이 바뀌면 프레임이 바뀌므로 `trim(a, ref=원음)` 으로 자르는 자리를 원음에서 정했습니다. D-0175 §2-2 "정렬·트림 시각 그대로" 의 구현입니다.
- **적용 범위**: Supertonic 만. edge·elevenlabs 정렬은 절대 시각이 아니라(TTS-AP-082) 적용하지 않고 기록도 남기지 않습니다.
- **관찰**: 보정은 원음 대비 상대 −4반음이라, 원음 끝이 오르던 문장은 보정 뒤에도 끝 f0 가 구간 시작보다 높습니다(끝 < 시작 = 33/45). 일부 구간 시작 f0 는 추적기 옥타브 오차로 보입니다(open_0 213Hz). 시제품과 같은 추적기·값이라 그대로 둡니다 — 청취에서 문제가 들리면 알려 주십시오.

## 3. 청취 자료
- 저장소: `phaseV5/narration_0-60_before.mp3` · `narration_0-60_after.mp3`(내레이션만, 0~60초), `final_fall_table.md`(문장별 구간·f0).
- 이 컨테이너 `projects/hormuz_korea/out/`: `final.mp4`(md5 18b940ca2c5e…, 48.7MB), `animatic.mp4`(md5 1431e7b9c3d1…). 미추적이라 Fable 사본에서 같은 순서로 재현하시면 md5 대조가 됩니다.

## 4. 다음
D-0177(통신사 사진 B, v5.21.0)·D-0178(light 의미색 A, v5.20.1)은 받았습니다. 지시 순서대로 V5 합격 뒤 착수합니다.
