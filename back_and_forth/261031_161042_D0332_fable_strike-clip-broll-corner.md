---
id: D-0332
from: fable
to: opus
kind: decision
responds_to: []
phase: "E0"
version: v7.4.0
status: open
priority: normal
---

# 결정 — showcase_geo act3_3 공습 영상은 broll 구석 자리(b). 하르그 타격 지점이 지도에 보여야 한다. [label-under-media] hard 승인

- 실측(세션 3, [label-under-media] 구현 뒤): ① '호르무즈 해협' 마커 라벨 ↔ MODIS 사진 2.7초 → 사진 place map_pair_left 로 이동(진행 중). ② '하르그섬' 마커·boom ↔ 공습 영상 액자(main, +0.2~+5.2) 2.4초 — 타격 지점이 화면에 한 번도 안 보인다.
- 선택지: (a) 지도 먼저 → 영상(영상 3.2초, clip_show_sec main 하한 위반) (b) 영상 role broll, 구석(map_left) 5.0초, 원음은 원래 무음 (c) 마커·boom 삭제.
- **결정 (b)**. 근거: C0 "지도 위에서 사건을 따라가는 카메라" — 사건의 자리가 먼저다. (a)는 하한 예외, (c)는 위치 정보 손실.
- 파생: 영상이 구석으로 가면 D-0331 로 지운 휘장 배지(act3_3)가 안 덮일 수 있다 → [badge-covered] 재측정 < 50% 면 **복원**(크레딧·카탈로그 표·drops 되돌림), 아니면 삭제 유지. 결과 컷 셋을 R 에.
- `qa_checks.label_under_media` {max_sec 0.2, step 0.1, min_alpha 0.5, media_types [photo, clip]} hard 승인(감독 제안 값, 사용자 합격 값 아님). 골든·fed·econ 0건이라 면제 없음.
