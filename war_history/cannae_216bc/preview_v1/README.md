# 칸나이 프리뷰 v1 (720p, D-0632) — 게이트 ② 자료

- 프레임 24장: `p_*.png`(자동 14장 + 전후 비교 8장 + 확대 컷 전후 111.5·113.0초), `sheet.jpg`(프리뷰 시트)
- 전후 비교: `before_after_v1.jpg` — 왼쪽 콘티 판 v2(480p), 오른쪽 프리뷰 v1(720p), 같은 시각
- 렌더 전 검사: `checks.json` — 140개 중 hard 0, warning 20(shots 6·media_beats 7·media_upscaled 2·endcard_roll 1·geo_unsourced 4)
  - basemap_upscale 0, terrain3d_seam 0, glyphs 0, narration_clarity 0, battle_sfx_missing 0, bgm_highlight 0
- 믹스(`clarity.json`): 명료도 최저 15.65 dB(encirclement_9), 음악 −20.89 dB, 하이라이트 겹침 63%, bed_gain 0.43
- 3D 프레임: 720p, 2배 그리기 후 LANCZOS 축소(seg00~03 지문 일치)
- 권리: `rights_registry.json`(프로젝트, 저장소 미추적 사본)

이번 판에서 바뀐 연출(D-0631 §2-3 대안, D744):
- prelude_10 확대는 폭 3.2 → 0.32 까지(G 원천 1.12배 이하)
- deployment_0 에서 2D 컷으로 폭 0.09(K 1.19배), deployment_1 에서 같은 화면으로 3D 들어감

## 추가(D745 요청) — 컷 이음 프레임·review_sheet·uf_checklist
- `cuts/`: 109.75(2D 폭 0.32) · 109.90(deployment_0 2D 컷 직후 폭 0.09) · 112.50 · 113.40(3D 직전, 2D) · 113.50(3D 들어감) · 114.00 · 114.70.
  seg00 첫 줄(폭 0.317)은 화면에 나오지 않는다(113.40 = 2D 폭 0.09, 113.50 = 같은 화면의 3D). 이 판 검사 hard 0/140(basemap_upscale·camera_continuity·camera_speed·static_camera·terrain3d_seam·glyphs 모두 0)
- `review/`: review_sheet --every 3(4장 123칸, 프레임 원천 = out/animatic.mp4 v2 — 도구가 preview 는 prev/ 만 읽어 720p 프리뷰를 못 본다). 요소 표 10행, 지도 사건 가림 최대 0%, 완전 노출 최소 6.03초
- `uf_checklist.md`: 720p 프리뷰 provenance 기준 — 자동 pass 88 · fail 0 · 눈 확인 98 · 미실행 4
