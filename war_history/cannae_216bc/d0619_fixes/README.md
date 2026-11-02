# D-0619 ①② 수정 증거 — 칸나이 콘티 판(480p 프레임, render_frame 실측)

- seam_before_after.jpg — 구간 경계 이웃 프레임 쌍. before = 콘티 판 v1(이음 없음·조명 지면), after = 지면 relief 텍스처 + 1.2초 이음.
  들어감 2722→2723(113.42초), 나옴 6149→6150(256.21초). 원본 PNG 8장 같이.
- seam_mid_fade.jpg — 이음 창 가운데(들어감 2737, 나옴 6136): 같은 색조 지면 위로 부대·강이 녹아 들고 걷힘.
- 이음 창 이웃 프레임 MAD 최댓값: before 들어감 71.29 · 나옴 72.39 → after 1.51 · 1.55 (상한 qa_checks.terrain3d_seam_mad_max 12.0).
