# artifacts/war-history-v7.4.0 — 전쟁사 트랙(E9) 전달물

전달용 산출물(orphan 브랜치). 저장소 코드는 `claude/war-history-2026` 브랜치. 지시 = back_and_forth D-0600·D-0601.

## war_history/sketch_v1/ — W4 스케치(사용자 판정 ①, 실제 렌더 480p, 자막·내레이션 없음)
- `cannae_sketch/` — 칸나이 전투(기원전 216). 작전 지도(EraDate 뱃지·AWMC 가도·Pleiades 지명) → 같은 좌표계 확대 → 전술 무대(초승달·포위 키프레임) → 작품 카드 4(당대 은화·추정 흉상·트럼불 1773·Closs 1885 현장 판화) → 폴리비오스 인용
- `inchon_sketch/` — 인천 상륙과 서울 수복(1950.9.15~28). 작전 지도 → 인천항 전술 무대(녹색 06:33·적색·청색 17:30) → NHHC·NARA 사진 2 · 공간사 지도 → 공간사 인용
- 파일: `sketch_war.mp4`(전편) · `sketch_war_sheet.jpg`(컨택트 시트) · `cuts/`(정지 컷) · `sketch_provenance.json`(검사·자료 sha1) · `RIGHTS_media.json`(작품·사진·기록 레코드 — 라이선스·소장처·식별 번호·미술사 한 문장·출처) · `toponymy.yaml` · `sketch.yaml`(spec) · `ancient_geo_sources.json`(우회 경로·라이선스 sha1) · `MD5SUMS`
- 재현: `python -m sketch.war projects/<pid>`(SKILL campaign-front-map ⑧)
