<!--
tier: 3
last_synced_with: v5.17.0
ssot_for: [phaseV3-run-log]
depends_on: [docs/handoff/reports/phaseV2/run_log.md, script/plan.py, script/lint_waivers.py, tools/v3_cut_table.py, tools/click_sample.py, config.yaml]
last_review: 2026-10-11
-->

# Phase V3 실행 기록 — 호르무즈 Supertonic + MMS 재현 (v5.17.0) — 진행 중

지침은 D-0167 §3 입니다. 린트 예외는 D-0168(DECISIONS D162), 믹스 범위는 R-0198(대기)입니다.
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
| 전편 mux | `engine.mux` | **오디오 QA hard 로 멈춤 — R-0198** |

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

## 4. 오디오 QA(R-0198)
| 항목 | edge(옛, 같은 믹서) | Supertonic | 기준 |
|---|---|---|---|
| 내레이션 RMS | −16.66 dB | −17.50 dB | — |
| 내레이션 구간 음악 − 내레이션 | −9.83 | **−8.997** | [−13, −9] hard |
| 최종 음량(전편 디코드) | — | −14.1 LUFS · TP −1.55 | −14 ± 1 · ≤ −1.35 |
| mix 피크 | — | 0.9507 | ≤ 0.97 |

## 5. 판단(되돌릴 수 있음)
- 720p `clip: null` → `[704, 396]`: null("기본 npy")이 `load_clip` 프로파일별 경로 규칙(D-0074, 480p 클립 확대 금지)과 어긋나 클립 영상을 720p 로 못 냈습니다.
  D-0074 기준(16:9 정확·폭 64 배수·필요 장치 폭 이상 최소)으로 990 ÷ 2.25 × 1.5 = 660px → 704×396. `media_fetch --res 720p` 클립 2개.
