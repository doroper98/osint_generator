---
id: R-0151
from: opus
to: fable
kind: progress
responds_to: [D-0127]
phase: "G12"
version: v5.1.0
commit: 7f2cab49
status: done
---

# D-0127 후속 결과 — v11 미채택(v9 유지), fed 480p 재렌더, mix.f32 원인 확인

## (a) WIP 8b0ad34 확정
- 컨테이너를 G12 run_log §0 대로 복원했습니다. 지오 자산은 hormuz 21/21·랫클리프 15/15 가 일치하고, 휘장도 `513c0785` 로 같습니다.
- 8b0ad34 를 포함한 트리(5c4a17f)의 전체 pytest 결과는 **1207 passed · failed 0 · skipped 0** 입니다.
- 추가 수정은 없어서 확정용 커밋은 따로 만들지 않았습니다(8b0ad34 그대로).

## (b) fed 연출 수정 회차 1회 → **v9 유지**
qa_loop 함수를 그대로 썼고 `visual_qa_loop_max` 만 1로 두었습니다(스크래치 드라이버, 저장소 코드는 바꾸지 않음).
순서는 v9 재프리뷰 → 재검수 v3 → 수정 LLM 1회 → v11 → 프리뷰입니다. 코드로 w·위치를 고치지 않았습니다(P8).

| 판 | checks hard | 검수 hard | 검수 soft | 비고 |
|---|---|---|---|---|
| v9(재검수 v3) | 0 | 5 | 4 | p_0108.39·p_0071.40·p_0249.80·p_0290.40 겹침, p_0268.41 트럼프 뱃지 잔류. press_lead 예외가 적용돼 p_0215 empty 는 지적되지 않았습니다 |
| v11 | **3** | — | — | `island_overlap`: map_right_low 에 넣은 photo 3개(fed_presser_0916 ×2·fed_eccles_ext)가 차트 아일랜드와 632px² 교차. 검수는 돌지 않았습니다 |

- 판정: 기준(checks hard 0·검수 hard ≤ 1) 미달이라 **v9 를 유지**합니다. 코드가 v9 를 복원하고 다시 프리뷰했습니다(checks hard 0).
- 사유: 수정 LLM 이 ①② 외에 soft(media 밀도)에도 답했습니다. 그러면서 photo 아일랜드 3개를 추가했고, 이것이 hard 로 이어졌습니다.
- 시트로 보면 v11 은 ①② 를 대부분 고쳤습니다.
  - p_0249.80 점도표 카드: 2장으로 나누고 place card_right 로 옮겨 아일랜드를 가리지 않습니다.
  - p_0290.40: 9월 16일 마커를 빼서 라벨이 겹치지 않습니다.
  - p_0071.40·p_0268.41 도 해소됐습니다.
  - p_0108.39 는 워시 마커 두 개가 아직 붙어 있습니다.
- 기록 커밋: 7f2cab49(`direction.v11.yaml`). revision·checks·시트는 artifacts 에 있습니다.

### 제안(결정은 Fable) — 두 건
1. **카드 ↔ 아일랜드 교차 검사(warning)**: 추가를 권고합니다.
   - 근거: v9 p_0249.80 카드에는 place 가 없었고, 기본 자리가 아일랜드 오른쪽 위를 덮었습니다. v11 에서는 수정 LLM 이 place card_right 를 주자 해소됐습니다.
   - 방식: 카드 예약 영역과 아일랜드 상자의 교차를 결정적으로 잡아 `[card-island]` warning 으로 남깁니다. 그러면 검수 LLM 보다 먼저 수정 입력에 들어갑니다.
   - hard 가 아닌 이유: 카드 위치는 연출 몫이고(P8), 작은 교차는 가독성에 영향이 없습니다.
2. **v11 을 기준으로 한 수정 회차 1회 더**(photo place 만 고칠 것)는 선택지로만 적습니다.
   - A: v9 유지로 종결(현재 상태).
   - B: v11 기준으로 1회 더 돌려 ①② 해소분을 살립니다.
   - 권고는 A 입니다. D-0127 이 회차를 1회로 정했기 때문입니다. B 가 필요하면 지침으로 주십시오.

## (c) fed 480p 재렌더(v9) → artifacts `phaseG12-v5.1.0` 69b5b3ad
| 산출물 | md5 | 길이 | 음량·검사 |
|---|---|---|---|
| `fed_policy_2026/followup_d0127/final_480p.mp4` | `c833024f8ceb012c774850b3d20c75b6` | 307.66초 | I −14.08 LUFS · TP −1.65 · 음악 −10.27 dB · checks hard 0 · warning 2(media_beats·endcard_roll 그대로) |
| `sheets/fed_v9_vs_v11_d0127.jpg` | — | — | v9·v11 6컷 대조(시트 1장) |

- mix.f32 는 `f4ff0ad2` 입니다. G12 §2 대로 `script.plan --tts edge` 를 다시 돌렸고 plan total 은 307.66초로 같습니다.
- 직전 전편 8ff240ed 와 연출(v9)은 같습니다. 이번 판은 press_lead 예외가 들어간 트리에서 뽑았습니다.
- provenance 에 기록되는 모델 이름 값은 artifacts 사본에서 가렸습니다(단일 출처는 config.yaml).

## (d) `mix.f32` md5 가 G7 과 다른 원인 — 한 줄
**G10 §2(44f799a)의 `audio.bed_bass.norm_ref` 0.7 → 0.4 변경이 원인입니다.** 베드 이득만 약 +1.7 dB 바뀌었습니다. 스크래치에서 hormuz 를 norm_ref 0.7 로만 다시 섞으면 `60ba8a98` 로 G7 과 바이트까지 같고, 0.4 로 섞으면 `96f9ebb7` 로 현재 값과 같습니다. fed 에는 G12 §D 재합성 9문장 차이도 겹칩니다. 코드는 바꾸지 않았습니다.

## 다음
새 지침을 기다립니다. 위 제안 1·2 의 결정이 있으면 그대로 따르겠습니다.
