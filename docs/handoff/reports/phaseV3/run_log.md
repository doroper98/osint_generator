<!--
tier: 3
last_synced_with: v5.17.0
ssot_for: [phaseV3-run-log]
depends_on: [docs/handoff/reports/phaseV2/run_log.md, script/plan.py, script/lint_waivers.py, tools/v3_cut_table.py, tools/click_sample.py, config.yaml]
last_review: 2026-10-11
-->

# Phase V3 실행 기록 — 호르무즈 Supertonic + MMS 재현 (v5.17.0)

지침은 D-0167 §3 입니다. 린트 예외는 D-0168(DECISIONS D162), 믹스 균형은 D-0169(DECISIONS D163)입니다.
모든 렌더는 표준 `FONTCONFIG_FILE`(phaseS0 §0.2)로 했습니다.

## 1. 순서(C8.6)와 결과
| 단계 | 명령 | 결과 |
|---|---|---|
| 원고 린트 | `script.plan` 안 | 오류 2건이 면제 목록과 정확 일치(`[waived flow-sparse -]`, `[waived uncertain-phrase now_3]`, D-0168). 다른 오류 0 |
| 음성 | `python -m script.plan projects/hormuz_korea --tts supertonic` | 45문장, 전체 260.66초(옛 292.44), 3분 42초. 정렬 mms 45, 문장 점수 최저 0.710. V2 사본 측정과 같은 값(결정성) |
| 자산 점검 | `tools/asset_library.py check` | 0 |
| 믹스 | `python -m audio.mix` | 저음 보강 +5.34 dB |
| 콘티 판 | `engine.render --animatic` | `out/animatic.mp4` 2분 57초. −14.1 LUFS · TP −1.55 dB(목표 −14 ± 1 · −1.5 + 0.15) |
| 프리뷰 | `engine.render --preview golden` | 25컷 → `hormuz_baseline.json`(phaseV3) |
| 전편 영상 | `engine.render --res final` | 720p 6255프레임, 6분 52초 |
| 전편 mux(bed_gain 0.47) | `engine.mux` | 오디오 QA hard 로 멈춤 — R-0198 |
| 재믹스(bed_gain 0.43, D-0169) | `audio.mix` → `--animatic` → `engine.mux` | 통과. `out/final.mp4` 1280×720 · 260.66초, `out/animatic.mp4`, srt·설명·크레딧·provenance |

provenance: `features_used.alignment = {sources: {mms_forced_alignment: 45}, score_mean_min 0.7101}`, `lint.waived` 2건,
`at_word {aligned 7, ratio 0}`(옛 플랜과 같은 수). 새 경고 1건: `[media-density-total] 과밀 — 7개 / 261초 = 37.2초당 1개 < 40초`(영상이 짧아져 생김, 경고).

## 2. 컷 대응표·나란히 시트
`cut_table.md`(25행: 옛 시각 → 새 시각, 이동, 앵커 문장 길이 전/후, MAD), `cuts_side_by_side.jpg`(옛 edge | 새 Supertonic | 차이×4).
- 이동량은 −0.88초(01)에서 −31.78초(25 END)까지 누적됩니다. 문장 길이 합 240.84 → 209.06초.
- **25컷 전부 차이가 시각으로 설명됩니다**: 항로 진행, 카메라 위치, 전환·드러남 진행, 국기 물결 위상, 비행기 위치. 요소·레이아웃·글자·색 변화는 없습니다.
- 기록할 두 컷: **07 war_2+2.5** 는 새 문장이 2.31초라 오프셋이 문장 끝 뒤에 떨어져 자막이 사라지는 중입니다.
  **09 ask_1+4** 는 새 문장이 5.04초(옛 7.86)라 거절 5개가 모두 표시된 상태입니다. 둘 다 골든 오프셋이 edge 문장 길이에 맞춰진 탓입니다.
- 이 렌더는 `prev/` 를 덮으므로 옛 edge 렌더는 V3 착수 직전 사본(같은 md5 = phaseQ2 기준선 25/25)으로 비교했습니다.

## 3. 클릭음 표본
`click_sample/click_sample.mp3`(0~30초, 클릭 15 = 문장 안 10 + 쉼 뒤 5), 표 `click_sample.md`. 클릭 시각 = `at_word` 와 같은 식.

## 4. 오디오 QA(R-0198 → D-0169, bed_gain 0.47 → 0.43)
| 항목 | edge 옛(0.47, 같은 믹서) | Supertonic 0.47 | **Supertonic 0.43** | 기준 |
|---|---|---|---|---|
| 내레이션 RMS | −16.66 dB | −17.50 dB | −17.50 dB | — |
| 내레이션 구간 음악 RMS | −26.49 dB | −26.50 dB | −27.26 dB | — |
| 음악 − 내레이션 | −9.83 | −8.997(hard) | **−9.76** | [−13, −9] hard, 기대 −9.77 ± 0.1 |
| 최종 음량(전편) | — | −14.1 LUFS · TP −1.55 | −14.11 LUFS · TP −1.63 · LRA 4.6 | −14 ± 1 · ≤ −1.35 |
| 콘티 판 음량 | — | −14.1 · −1.55 | −14.11 · −1.63 | 같음 |
| mix 피크 | — | 0.9507 | 0.9367 | ≤ 0.97 |
| 문장 RMS 이상치 | — | 0 | 0 | 편차 3 dB 초과 = 경고 |
| 저음 보강 상승 | — | +5.34 dB | +5.34 dB | [4, 8] |
| loudnorm 2패스 | — | — | 입력 −15.25 → 출력 −14.02, 리미터 −2.0 dBFS | — |

다른 항목 이탈 없음. provenance `audio.bed_gain = 0.43`(전편·콘티 판 모두). 기준선 재설정: `tests/test_audio_rules.py`·`tests/test_g6_bed_bass.py`
의 bed_gain 고정값 0.47 → 0.43(사유 주석 D-0169). 믹스 md5 를 고정한 테스트는 없다.

## 5. 판단(되돌릴 수 있음) — D-0169 ④ 수용
- 720p `clip: null` → `[704, 396]`(테스트 `test_v3_voice.ClipProfileTest`): null("기본 npy")이 `load_clip` 프로파일별 경로 규칙(D-0074, 480p 클립 확대 금지)과 어긋나 클립 영상을 720p 로 못 냈습니다.
  D-0074 기준(16:9 정확·폭 64 배수·필요 장치 폭 이상 최소)으로 990 ÷ 2.25 × 1.5 = 660px → 704×396. `media_fetch --res 720p` 클립 2개.

## 6. 사용자 청취 자료(Fable 전달)
| 자료 | 위치 |
|---|---|
| 콘티 판 | `projects/hormuz_korea/out/animatic.mp4`(미추적) |
| 전편 720p | `projects/hormuz_korea/out/final.mp4`(미추적, 48.7MB) |
| 클릭음 표본 30초 | `docs/handoff/reports/phaseV3/click_sample/click_sample.mp3` + `click_sample.md` |
| 컷 대응표 | `docs/handoff/reports/phaseV3/cut_table.md` |
| 25컷 나란히 시트 | `docs/handoff/reports/phaseV3/cuts_side_by_side.jpg` |

청취 자료 한 줄: **음악 균형 복원 — 배경음 이득 0.47 → 0.43(음악−내레이션 −9.0 → −9.8 dB, edge 시절 합격 균형).** 사용자 청취 합격 = 이 규칙 값 승인(P11, D-0169).

## 7. pytest

**1493 passed · 0 failed · 0 skipped**(313 subtests, 32분 51초, 표준 `FONTCONFIG_FILE`). 1차 실행의 5개 실패(면제 적용이 lint mock 순회 4, 골든 린트 실패 단정 1)는 고친 뒤 재실행.
