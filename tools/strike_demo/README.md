# strike_demo — 타격 애니메이션 + 위성 인셋 시험본(지도 없음)

D-0206(`back_and_forth/261017_204122_D0206_fable_flight-event-sat-inset.md`) flight 이벤트 기하의 독립 시제품입니다.
본편 엔진과 무관한 scratch 스크립트이며 레지스트리에 등록하지 않습니다(사용자 샘플 목적, 2026-10-17).

```bash
pip install pycairo fonttools brotli
python tools/fetch_data.py fonts            # IBM Plex Sans KR(raw.githubusercontent.com·cdn.jsdelivr.net 허용 필요)
python tools/strike_demo/render_demo.py   # → tools/strike_demo/out/ (strike_demo.mp4 · strike_demo_sheet.png · frames/)
```

- 위성 인셋: `EVENTS[i]["inset_png"]` 에 PNG 경로를 넣으면 자리표시 대신 그 이미지를 띄웁니다.
- 위성 인셋 원본·출처는 공용 보관본 `assets/library/insets/`(+ `inset_sources.json`)를 읽습니다.
- 출력물은 `out/` 아래에만 쓰며 추적하지 않습니다(`.gitignore`).
- v7.3.0 에서 `projects/strike_demo_2026/` 에서 옮겼습니다(`projects/` 아래 .py 금지 — test_no_py_in_projects).
