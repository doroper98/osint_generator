# artifacts/showcase-v7.4.0 — E0 쇼케이스(back_and_forth D-0251)

## showcase_econ 콘티 판 v2 (검토용 · 배포 금지) — 사용자 흐름 검토 대상
- `showcase_econ/animatic.mp4` — 154.25초, 480p, 표준 음성, checks hard 0(콘티 프로파일). 문법 A1(사진 배경 + 차트 아일랜드 하나, left_tall, w 420 하나 — D-0265·D-0268·D-0270)
- 금리·기록 두 레인, 금리 범위 3~5%(눈금 0.5), 전망 점(SEP 2026.9), 실사 12(배경 5 + 사진 7, 클립 0) / 2.57분 = 분당 4.67
- `animatic_v2_sheet.jpg` — 12컷(3~140초)

## showcase_econ 콘티 판 v1 (보존 — 문법 B)
- `showcase_econ/animatic_v1.mp4` — 154.3초, 480p, 표준 음성(Supertonic 3 M3 ×0.95), checks hard 0(콘티 프로파일)
- 문법 B(시간축 한 세계). 차트·카드만 보이는 최장 구간 10.8초(상한 12초)
- `preview_sheet.jpg` — 같은 연출의 프리뷰 컷 12장(480p)

## showcase_geo 콘티 판 v1 (검토용 · 배포 금지)
- `showcase_geo/animatic.mp4` — 240.9초, 480p, 29.2 MB, 표준 음성, checks hard 0(콘티 프로파일, [media-density] 포함)
- 실사 8(사진 7·클립 1 — 콘티 판은 자리표시) / 4.0분 = 분당 2.0. 게이트 ① 원고 지문 9e9ee0b6 와 같음
- `sheet_20s.jpg` — 20초 간격 12컷

## showcase_econ 프리뷰 v5(A1 — 사진 배경 + 차트 아일랜드 하나, D-0265) — 감독 확인용
- `showcase_econ/preview_v5.jpg` — 프리뷰 12컷, checks hard 0. `preview_v5_zoom.png` — 아일랜드 금리 레인 확대(52초·124초)

## showcase_econ A/B 비교 구간 (검토용 · 배포 금지, D-0253 §2·D-0265·D-0272)
- `showcase_econ/prev_ab/A.mp4`(본편 A1) · `B.mp4`(시간축 전면 틀, v1 문법 — 사진·카드 없음) — 29.4~54.9초(act1_2~act1_5 — 10월·12월 인하, 동결, 이란 전쟁, D-0273), 같은 mix.f32 구간
- `sheet.jpg` — 같은 초 6컷, 왼쪽 A · 오른쪽 B. 프리뷰 hard A 0 · B 0(media_density 만 비교 구간 전용 면제 — 구조상 사진 자리 없음)
- `provenance.json` — ab_compare {sentences, t0, t1, direction_a_sha1, direction_b_sha1, checks_hard, b_exempt}

## 게이트 ② 자료 준비분 (사용자 흐름 승인 전 — 아직 보내지 않음, D-0273)
- `showcase_{econ,geo}/gate2/`: `preview_sheet.jpg`(프리뷰 auto 컷) · `preview_checks.json`·`preview_provenance.json`(hard 0) · `catalog.mp4`(카탈로그 판 720p, 배포 금지) · `catalog_table.md`(카탈로그 판 기록에서 만든 요소·글꼴 표) · `catalog_checks.json`(hard 0) · `media_summary.md`
- econ 프리뷰는 축 값 라벨 예약 열(cd314ea) 반영. 콘티 판 v2(animatic.mp4)는 그 이전 렌더

## showcase_econ 연준 회견 클립 조각 (D-0275 — 다음 컨테이너 복원용)
- `showcase_econ/media_src/<mid>_segment.mp4`(레지스트리 segment 구간만, h264 crf 18) · `<mid>_clip.wav`(원음, 44.1kHz 스테레오) · MD5SUMS
- 원본(9.16 1722초 · 7.29 2704초, 966 MB)은 올리지 않는다 — 레지스트리 tool.params(Brightcove 플레이어 주소·video id·yt-dlp 버전)와 source_hash 로 다시 받는다
- npy(480p 84~154 MB · 720p 181~332 MB)는 GitHub 파일 한도(100 MB)로 올리지 않는다 — 원본 또는 조각에서 `tools/media_fetch.py` 로 다시 만든다
