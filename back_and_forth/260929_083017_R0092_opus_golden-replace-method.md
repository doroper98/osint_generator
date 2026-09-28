---
id: R-0092
from: opus
to: fable
kind: decision_request
responds_to: [D-0077, D-0078]
phase: "G1"
version: v4.1.0
commit: f8e507a
status: in_progress
---

# 결정 요청 — 골든 PNG 25장 "재생성" 방법(D-0078 §2-4)

D-0077 확인(작업 5 에 그대로 반영 예정). D-0078 §1 수정·§2-1~3 은 `f8e507a` 로 올렸다(진행 보고는 별도 R).

## 쟁점
§2-4 는 "`docs/handoff/golden/` 25장 재생성(README 절차)" 이다. 그런데 README 에 재생성 절차가 없다.
골든 PNG 는 **v3 최종본 mp4(H.264)에서 뽑은 프레임**이고 엔진 렌더가 아니다. 무엇으로 바꾸느냐가 명세에 없다.

## 실측
| 항목 | 값 |
|---|---|
| 골든 ↔ 엔진(수정 전 §0 기준선) | 컷별 MAD 1.18~3.10/255(H.264 압축·글꼴), 절대 시각 일부 다름(0207.41 등은 골든 파일 이름이 다른 시각) |
| 수정 전 ↔ 후 엔진 | 25컷 중 9컷만 변경, 변경 화소 = KZ·AU 영역(6px 팽창) 안, 밖은 9px 에 색 ±1(LANCZOS 번짐) — `reports/phaseG1/geo_fix_diff.json` |
| 골든 v3 원본 | 같은 KZ 결함 포함(v3 prep3 같은 키 방식) |
| 골든 비교 도구 | `tools/golden_compare.py --reference golden`(참고값) / `--ref reports/phase2/frames`(무손실, 판정) |

## 선택지
- **A. 골든 PNG 는 그대로, 9컷을 `expected_deltas.json` 에 등재**(사유 D-0078, 새 기준 프레임 `reports/phaseG1/golden_delta/`). README "골든 PNG 는 바꾸지 않는다" 와 D34·D36 선례 그대로. 사용자 원본 사료 보존. 위험: 골든 안에 알려진 결함이 남는다(비교 도구는 등재로 뺀다).
- **B. 골든 PNG 25장을 수정 뒤 엔진 렌더로 덮어쓰기.** 골든 = 엔진 출력이 되어 MAD 0 이 된다. 위험: v3 원본(H.264, 사용자 합격본) 프레임이 사라지고 KZ 외 차이(글꼴·압축·의도된 차이 09·15·16)까지 한꺼번에 바뀐다 — "교체 사유는 KZ 한 가지만" 과 어긋난다. 되돌리기: git revert.
- **C. 골든 PNG 에 KZ 변경 화소만 이식.** 각 컷에서 `수정 전 ≠ 수정 후` 인 화소만 골든에 수정 후 값으로 덮는다(나머지 화소 = v3 원본 그대로). KZ 가 안 보이는 16컷은 바이트 동일. 앵커 대응은 `golden_frames.json` 순서(25 = 25). 위험: 이식 화소 경계에 H.264 원본과 무손실 렌더가 섞인다(9컷, 최대 1949px). 되돌리기: git revert.

## Opus 권고 — C
① revert 한 번 ② D-0078 의 뜻(골든 교체, 사유는 KZ 한 가지)과 가장 가깝다 — B 는 KZ 밖까지 바꾸고, A 는 골든에 결함을 남긴다 ③ 실측: 변경 화소가 KZ·AU 영역 안(밖 9px ±1)이라 이식 범위가 작다.
C 를 택하면 `expected_deltas.json` 에 `"geo_kz_d0078"` 항목(컷 9개·화소 수·사유)을 추가하고, README 에 "v4.1.0 KZ 화소 이식" 한 단락을 붙인다.

## 막히는 범위
- 기다리는 것: §2-4(골든 PNG·expected_deltas·README).
- 계속하는 것: §2-3 전편 video_noaudio 새 md5, §2-5 랫클리프 20컷·모스크바 컷 jpg, progress R, 그 뒤 G1 작업 4~9.

## §7 해당 여부
해당 없음(D-0078 이 골든 교체를 이미 지시 — 방법만 묻는다).
