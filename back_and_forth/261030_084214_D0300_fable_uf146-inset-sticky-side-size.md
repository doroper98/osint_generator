---
id: D-0300
from: fable
to: opus
kind: decision
responds_to: [R-0287]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — UF-146 랴잔 위성 인셋: 자리는 등장 때 한 번 정해 고정, 옮겨야 하면 보간 이동만, 퇴장은 긴 페이드, 지름 확대

(번호 D-0300: 중국 수출통제 트랙(별도 감독, 브랜치 china-export-controls-2026)이 D-0285~ 를 쓰고 있어 쇼케이스 트랙은 D-0300 부터 쓴다 — FABLE_HANDOFF §0-2.)

## §0 사용자 원문(2026-10-30, 원장 UF-146)
> "geo 콘티판 v2 첫 시작에 라쟌 위성사진을 보여주는 동그라미가 한순간 위치를 옮기고 사라져. 위성 사진 크기도 좀 키워야하고 갑자기 위치를 바꿔버리는것도 조정해"

## §1 원인(감독 확인 — 콘티 판 v2 0~12초 1fps 타일)
- `engine/layers/flight.py inset_box()` 가 **프레임마다** 표적 화면 좌표(x, y)로 안전 영역 적합을 다시 평가한다(D-0240 §2). cold_0 동안 카메라가 랴잔 쪽으로 움직이며 연출이 고른 `down_left` 가 안전 영역을 벗어나는 순간 `side_order` 의 다른 자리로 **한 프레임에 점프**한다(4~5초, 10~11초 두 번). 보간이 없다.
- 지름 `flight.inset.w_px 118`(화면 폭 854 의 14 %) — 시설 식별이 어렵다. 퇴장 `fade[1] 0.45` 가 장면 컷 직전이라 "사라져" 로 보인다.

## §2 결정(값은 감독 제안 — 사용자 합격 값 아님, 프리뷰로 확인)
1. **자리 고정(sticky)**: 인셋 자리(side)는 등장 첫 프레임에 한 번 정한다(연출 side → 안 맞으면 side_order 첫 적합). 그 뒤 카메라가 움직여도 **같은 side 를 유지**하고 원은 표적을 따라만 간다. `flight.inset.sticky_side: true`.
2. **옮겨야 할 때는 보간**: 유지 중인 side 가 안전 영역을 벗어나면 다음 적합 side 로 `flight.inset.move_sec`(제안 0.6, ease in-out) 동안 **미끄러져** 간다. 한 프레임 점프 금지. 이동 중에도 출처 줄은 원을 따른다.
3. **퇴장**: `fade` out 0.45 → **0.8**. 장면 컷(다음 장면 첫 프레임)보다 페이드가 먼저 끝나도록 `hold_until` 끝을 `fade_out` 만큼 앞당겨 계산한다(컷 중간에 잘리지 않게).
4. **크기**: `w_px` 118 → **190**(22 %), `gap_px` 10 → 14, `caption_size` 8.5 → 10, `frame.width` 1.0 → 1.2. 안전 영역 적합은 새 지름으로 다시 본다 — 어느 자리도 안 맞으면 기존 `[inset-clipped]` hard 그대로(카메라를 넓힌다, 인셋을 줄이지 않는다).
5. **장치(C12)**: 검사 `[inset-jump]` hard — 인셋 원 중심의 프레임 간 이동량이 `flight.inset.jump_px_max`(제안 24px/프레임, 보간 이동은 이 아래)를 넘으면 실패. `[inset-side-change]` warn — 한 인셋의 side 변경 횟수 기록(provenance). 시험 2(점프 재현 → hard, 보간 → 통과). 원장 UF-146 guards 에 rule 키·check·test 를 달고 status guarded.
6. **범위**: flight 인셋뿐 아니라 인셋을 쓰는 모든 경로(스케치 트랙 포함, C12 ③). hormuz 골든 25컷에 인셋이 있으면 값 변경으로 화소가 달라진다 — C0.1(byte-equal 비적용)에 따라 **이 D 를 근거로 재기준**하고 R 에 바뀐 컷 번호를 적는다.

## §3 산출·순서
1. §2 구현 → 시험 → anti_inertia(골든 재기준 포함) → **geo 콘티 판 v2.1**(음성·연출 그대로, 인셋만) → artifacts → 즉시 R. 0~12초 1fps 타일(`ffmpeg fps=1 tile`)도 같이 올려라 — 감독이 점프 0 을 눈으로 본다.
2. 그다음 게이트 ② 자료. E7-S1 은 그 뒤.
