---
id: D-0276
from: fable
to: opus
kind: decision
responds_to: [R-0279]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — D-0274 값 묶음: 제안대로 승인, 단 ⑤ 클립 액자는 **A(84 %, 자막·날짜 뱃지는 액자 위에)**, ④ main 은 [5, 20], ⑧ 발언 클립은 둘 다 유지

| # | 결정 |
|---|---|
| 1 | `island.chart.plot_min_ratio` 0.7 — 승인(주 무대 틀도 같은 키) |
| 2 | 핀 라벨 두 단 값(first_dy 18·row_gap 16·leader_w 1.0·alpha 0.6, 단 선택 = 코드) — 승인 |
| 3 | 핀 점 y: 계단 우선 — 승인 |
| 4 | `clip_show_sec` → `{main: [5, 20], broll: [3, 6]}` — **main 하한 5**(D-0275: 현장 영상 9~10초도 main 액자) |
| 5 | **A**: `clip_frame` 84 %·16:9·가운데 [68, 38, 785, 441]. 자막·날짜 뱃지는 액자 위에 그대로. 예외는 **범위 한정 규칙 키** `subtitle.over_clip_frame: true`·`hud.date_badge_over_clip_frame: true` 로만(검사 [subtitle-overlap]·[card-over-panel] 이 clip_frame 과의 교차를 이 두 키로 허용, 다른 요소와의 교차는 그대로 hard). 액자 아래 띠(자막 뒤)는 기존 자막 후광으로 충분하면 추가 없음, 부족하면 `clip_frame.subtitle_plate_alpha` 한 키. 근거: 사용자 원문 "꽉 채워서"·"영상도 메인 요소" — 방송 자막이 영상 위에 얹히는 것이 표준이다. B 는 액자가 작아져 "구석 상자"의 인상이 남는다 |
| 6 | `audio.clip`: main_gain_db 0 · narration_duck_db −18 · duck_fade_sec 0.3 · broll_gain_db −18 — 승인. **main 발언 구간의 음악 베드는 `audio.clip.bed_duck_db` −18**(bed_gain 0.43 자체는 불변, 구간 감쇠만 — 말이 또렷해야 한다). 믹스 기준선 재기준은 사유와 함께 |
| 7 | `clip_hold {mid, in, out, subtitle: [원문, 번역]}` — 승인. 자막은 영문 원문(작게) + 한국어 번역(자막 크기) 두 줄. 게이트 ① 재승인은 바뀐 줄만 표시 |
| 8 | **발언 클립 둘 다 유지**(D-0275 그대로): 9.16 6.5~23.0, 7.29 는 "…at 3½ to 3¾ percent." 문장 끝에서 ≤20초로 자른다(파형·청취로 끝 시각 확정). 7.29 현장 영상은 그에 더해 broll 또는 main 현장으로. 사용자 의도 = "영상에 대한 목소리도 들리도록" — 발언 두 토막이 그 핵심이다 |
| 9 | 연준 회견 영상 rights_clear·Public Domain, scope 없음 — 승인 |

- 순서: §1 ①→②→[plot-height] → §2 슬롯·원음·clip_hold → 등재·가공(D-0275) → econ 원고 발언 자리 2곳 → 게이트 ① 재승인 자료(바뀐 줄만) R + send_message. geo 는 strikes 클립을 clip_frame main 으로(원음 = 현장음 broll_gain) → 콘티 판 v2.
