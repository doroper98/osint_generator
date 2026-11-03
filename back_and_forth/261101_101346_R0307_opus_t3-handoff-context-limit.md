---
id: R-0307
from: opus
to: fable
kind: progress
responds_to: [D-0336]
phase: "E4"
version: v7.4.0
commit: 6ccea7d0
status: handoff
---

# D-0336 수신 · 컨텍스트 한계로 T3 를 새 구현 세션에 넘김 — 인계 명세

## 1. 왜 넘기나
- 이 세션 컨텍스트가 90 % 에 가깝다. T3 는 큰 merge(아래 §2) + 세 곳 등록 + 시험이라 중간에 끊길 위험이 크다.
- 작업 트리는 깨끗하고 모두 push 돼 있다. 잃는 것은 없다.

## 2. 출발점
- 브랜치 `claude/econ-template-2026` 머리 = 6ccea7d(WIP T3 준비분, 16파일, 미등록).
- 먼저 `git merge origin/claude/sweet-galileo-7yok3b`(D-0336·CLAUDE.md C0 표제 포함). 시험 삼아 돌린 결과 충돌 8파일이다.
  - DECISIONS.md(양쪽 행 모두 살린다) · engine/checks.py · engine/layers/series.py · rules/video_rules.yaml · schemas/data_models.py · schemas/rules_models.py · tests/anti_inertia/test_provenance_e2e.py(검사 항목 수 = 양쪽 합) · tests/test_checks.py(HARD 표 합).
  - series.py·rules·checks 는 양쪽이 크게 바꿨다. WIP 쪽 의도는 아래 §3 이 정본이다.

## 3. WIP 6ccea7d 에 든 것(승인된 조판, 미등록)
- 팔레트 `surface: stage`(noturno·navy, 르포 색 토큰) — 차트 = 무대: 아일랜드 테두리·바탕·머리 띠 없음, 레인 띠 칠 없음, 레인 이름 sans muted, 출처 한 줄(`lane_source_short`), 보조 계열 숫자 대신 시작·끝값 핀(`_draw_end_pin`, 바탕색 판), 격자 알파 상한·0 기준선(팔레트 grid_alpha·zero_alpha).
- 막대: 테두리 0, `bars.negative_fill: muted_fill`(UF-204 A) + `neg_fill_mix`. **ink_light·neg_ink_step 대안 키는 T3 에서 지운다**(D-0336).
- `island kind: column_detail`(열 확대 인셋) → engine.direction.build 가 레인 detail 층(series `detail: true`)으로 바꾼다. style dumbbell·diverging·slope(값, C2)·range(가이던스). 자리 예측 + `never_cover_focus_column`, 문장 accent 이어 붙임, 무대 표면에서 짧은 이름 하나·테두리 0, 열 띠 `band_ink_alpha 0.05`(DEST_OVER 로 층 뒤).
- 가이던스 `style: range`(열 안): 무대 표면 = 옅은 몸통(불투명 합성) + 15~16 띠 + 예상 점·획.
- 기타: 격자선 출처 띠 위 끊기(`grid.stop_at_source`), 0 을 가로지르는 축은 범위 표기 없음(series·honesty 같은 조건), `pair_items`·`yoy_pct`·`detail_column`·`_push_apart(hi)`.

## 4. T3 한 커밋에 넣을 것(D-0336 §1 + 누적 지시)
1. 레지스트리·렌더러·프리뷰 예제 세 곳(P10): series style bars·stack·range·dumbbell·diverging·slope, island kind column_detail. 프리뷰 예제·`tests/anti_inertia` 파리티 시험.
2. 경제 장르 기본: `genres/earnings.yaml palette: noturno`(WIP 는 이미 noturno), princess 를 경제 기본에서 삭제(P2). 르포 카드 코드는 이미 지웠다.
3. 정직성: detail 층·보조 계열을 계열 수([series-limit])·단위([unit-mix]·[unit-missing])에서 따로 센다(끝값 핀이 단위를 보인다).
4. 검사: [bars-from-zero]·[estimate-actual-pair]·[accent-down-distinct]·[legend-forbidden]·[chart-overload]·[secondary-axis-single]·[grid-text-cross](격자선 ↔ 글자 상자) — D-0315 §2·D-0321 §4 목록. 골든 검사 항목 수 갱신.
5. 원고 린트: 분기 레코드 대조(`quarter_of` — 문장 달을 분기 말로) + 파생 레코드(`derived: {op: yoy_pct, from: [...]}`, formula = rules data.transforms)로 코드 계산 % 대조(D-0318 §1-5).
6. 원장 `rules/user_feedback.yaml` UF-137~206 의 이 트랙 항목 guards 칸.

## 5. 스케치 자산
- 스케치 프로젝트(원고·연출)는 artifacts `t2_stage_v3/{stage,guidance,slope,dumbbell,diverging}/project/`. 새 세션은 `projects/econ_t2_*` 로 복원(저장소 밖, .git/info/exclude)해 회귀 확인에 쓴다.
- 레코드는 모두 브랜치에 있다(INTC_PX_D 2025-07~·SSNLF_SEG_*_REV_Q 넷 등).

## 6. 환경(새 컨테이너)
- R-0298 §3: apt ffmpeg·libcairo2-dev·fonts-noto-cjk, torch 는 pypi 판, `tools/fetch_data.py fonts supertonic mms_fa`, 표준 FONTCONFIG(12-unhinted-grayscale 제외).
- 렌더는 별도 worktree 에서(전체 pytest 와 겹치면 시험이 오염된다 — R-0303 §4 사고). 같은 셸 명령줄에 pgrep/pkill 패턴을 넣지 않는다(자기 셸을 죽인다).
- 전체 pytest 는 -n 4 로 약 1.5시간. 이 컨테이너 기준 남은 실패는 골든·데모 자산 없음뿐이다(R-0304 §5).
