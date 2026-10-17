# strike_demo_2026 — 타격 애니메이션 + 위성 인셋 시험본(지도 없음)

D-0206(`back_and_forth/261017_204122_D0206_fable_flight-event-sat-inset.md`) flight 이벤트 기하의 독립 시제품입니다.
본편 엔진과 무관한 scratch 스크립트이며 레지스트리에 등록하지 않습니다(사용자 샘플 목적, 2026-10-17).

```bash
pip install pycairo fonttools brotli
python tools/fetch_data.py fonts            # IBM Plex Sans KR(raw.githubusercontent.com·cdn.jsdelivr.net 허용 필요)
python projects/strike_demo_2026/render_demo.py   # → 같은 폴더 strike_demo.mp4 · strike_demo_sheet.png · frames/
```

- 위성 인셋: `EVENTS[i]["inset_png"]` 에 PNG 경로를 넣으면 자리표시 대신 그 이미지를 띄웁니다.
- 출력물(`frames/`·mp4·png)은 추적하지 않습니다.
