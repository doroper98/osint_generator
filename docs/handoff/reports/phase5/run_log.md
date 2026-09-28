<!--
tier: 3
last_synced_with: v2.4.0
ssot_for: [phase5-run-log]
depends_on: [tools/commons_fetch.py, tools/portrait_fallback.py, tools/fetch_data.py, tools/golden_compare.py, engine/mux.py]
last_review: 2026-09-28
-->

# Phase 5 실행 기록 — 뱃지·엔티티·권리 (v2.4.0, Opus 클라우드 컨테이너)

## 재기동
- 12:18 KST: 이전 Opus 세션(재기동 3)이 12:00 이후 턴 없음 → 새 세션(재기동 4)으로 이어받음.
- 이어받은 마지막 커밋: `e08495f`(휘장 대체 시연). 미처리 D 0건.
- 남은 일(R-0025 §남은 것): 미디어 prefetch, 재합성·25컷 대조, 크레딧 프레임, provenance, asset_md5, phase_report, orphan 영상.

## 0. 컨테이너 준비 (Phase 4 run_log §0 절차 반복)

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 얕은 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | `bd37b58` 객체 확인 |
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt` | 진행 중 |
| 바이너리·폰트 | `apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | 진행 중 |
| edge-tts CA | certifi 번들에 `/root/.ccr/ca-bundle.crt` 덧붙임 | 진행 중 |
| 입력 데이터 | `python tools/fetch_data.py all` → `bgm people media` | 진행 중 |
