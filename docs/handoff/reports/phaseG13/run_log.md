<!--
tier: 3
last_synced_with: v5.5.0
ssot_for: [phaseG13-run-log]
depends_on: [rules/video_rules.yaml, engine/island.py, engine/layers/markers.py, tools/ai_direction_run.py, tools/backdrop_sweep.py, back_and_forth/260930_170916_D0129_fable_g13-backdrop-legibility-main-island.md, back_and_forth/260930_193608_D0132_fable_g13-backdrop-photo-slot.md, back_and_forth/260930_204931_D0133_fable_g13-label-clip-b.md]
last_review: 2026-09-30
-->

# Phase G13 실행 기록 — 배경 가독·주 아일랜드 상시·보도 인용 = article·카드↔아일랜드·아일랜드 마커 라벨 (v5.2.0)

지침 D-0129(§A~§E)·D-0130(Q1~Q3)·D-0131(재연출 막힘 해소)·D-0132(backdrop 사진 슬롯)·D-0133(아일랜드 라벨 B). 재기동 29~32 세션.

## 0. 컨테이너 준비

phaseG12 run_log §0(= G10 §0) 그대로(하위 에이전트). 차이만 적는다.
- `artifacts/phaseG12-v5.1.0` 에는 `shared/` 가 없다(출력·기록만). 원본 자산은 G10 §0 대로 phase7(hormuz)·phase9(ratcliffe)·phaseG3(데모)·phaseG4(fed) 아티팩트에서 복원. fed `script.plan --tts edge` 재실행 = 48문장 307.66초.
- fed `mix.f32` `0e61dea7…`(D-0127 `f4ff0ad2…` 와 다름, 원인 미확정 — G12 §0 과 같은 부류). hormuz `96f9ebb7…` 같음.
- **prev/ 정리(P9)**: 복원이 G12 판정(`qa_verdict`·`revision`·`qa_loop.json`)을 prev/ 에 되살리면 실행 전에 prev/ 밖으로 옮긴다(재기동 31). 재기동 32 는 G12 기록을 prev/ 에 복사하지 않았다.
- **direction.meta.json 유실**: 추적 안 되는 파일이라 회수로 사라졌다. 없으면 `qa_loop` 가 사람 연출로 보고 검수를 건너뛴다. v12 연출가 기록 커밋 직전(a015a2e1~1) 트리에서 `DirectorWorker.system_prompt()` sha1 을 다시 계산해 재구성(`reconstructed` 필드, model = 백엔드 이름).

## 1. D-0133 커밋과 증명

| § | 커밋 | 증명 |
|---|---|---|
| §1~§3 라벨 반전·검사 | 881af40 | `markers.island_label`(in_island 마커만), checks `island_label_clip` hard·`island_label_overlap` warning, provenance `island.label_clip/label_overlap/label_flip`, 문법 한 줄, docs/12 두 행, 테스트 10 |
| §2 hormuz 골든 | 15e0067 | `hormuz_label_clip.json` — 25/25 = G12 기준선(25_END 도장 가린 md5), 새 검사 0 |
| §4 수정 회차 1회 | 71ce9d5 | v15 검수 v1 hard 3 → 수정 v16 → 검수 v2 hard 1, 선택 v16 |
| §5 산출물 | artifacts e89bb51 | 아래 §3 |

## 2. 명령

```bash
python tools/ai_direction_run.py projects/fed_policy_2026 --rounds 1        # 검수 v1(v15) → 수정 v16 → 검수 v2, 427초
python -m engine.render projects/fed_policy_2026 --jobs 3 && python -m audio.mix projects/fed_policy_2026 && python -m engine.mux projects/fed_policy_2026   # 6분 16초
python tools/backdrop_sweep.py projects/fed_policy_2026 --t 43.65 --t 91.83 --t 250 --v 4:0.30 --v 6:0.38 --v 10:0.45 --out backdrop_sweep_fed.jpg
python -m engine.render projects/hormuz_korea --preview golden              # 25컷 → hormuz_label_clip.json
```

## 3. 측정

| | v9(G12) | v15 | **v16(최종)** |
|---|---|---|---|
| 카드 / article | 35 / 2 | 26 / 6 | 27 / 6 |
| checks hard | 1 | 0 | **0** |
| [island-label-clip] | — | 0(반전 뒤) | **0** |
| [island-label-overlap] | — | 1(8월 소비자물가 ↔ inflation 출처 줄) | **0** |
| [card-island] | 11 | 2 | **1**(연방기금금리 21.70~27.76) |
| 검수 hard / soft | 4 / 7 | 3 / 5(v1) | **1 / 7**(v2) |

- 반전이 실제로 돈 라벨: "다음 FOMC"(provenance `island.label_flip`).
- 검수 v2 남은 hard 1: p_0276.55 "사진 아일랜드가 차트 오른쪽 아래 모서리를 덮는다". 프레임 실측은 사진 x ≥ 594·차트 상자 오른쪽 끝 564 — 겹침 없음(checks island_overlap 0). 판정은 바꾸지 않았다(P11).
- 480p: md5 `3173b7b8c29513abd7b9ef2653b334d6`, 307.66초, I −14.06 LUFS·TP −1.78, checks warning = media_beats 4·endcard_roll 1·card_island 1.
