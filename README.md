# artifacts/speed-pipeline-v7.4.0 (back_and_forth D-1000·D-1001)

- `map_event_covered/` — D-1001 §3 눈 검증. 건마다 가림 최대 시각 프레임(콘티 판 레이어: 사진·영상 = 자리표시 상자, 기사·인용 = 화면 전체 덮개).
  빨강 = 사건 상자, 파랑 = 덮개 상자. `<pid>.json` = 종류·이름·창·가림 비율·시각·문장 id. 만든 명령: `python tools/map_event_sheet.py <proj> <out> --animatic [--limit 4]`.
- iran = 실제 음성·정렬(콜드 오픈 면제 뒤 3건), showcase_geo·diesel_road_2026·china = plan.json 시각 + 합성 정렬(china 는 12건 중 무작위 4, seed 1000).
