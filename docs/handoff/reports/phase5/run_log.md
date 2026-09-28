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
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt` | ok |
| 바이너리·폰트 | `apt-get update && apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | ffmpeg 6.1.1. 첫 시도는 패키지 404 → `apt-get update` 뒤 ok |
| edge-tts CA | certifi 번들에 `/root/.ccr/ca-bundle.crt` 덧붙임 | ok(저장소 무변경) |
| 입력 데이터 | `python tools/fetch_data.py all` | fonts·ne·tiles·flags ok. commons 는 429 연속(60~90초 대기 반복, 약 30분). strikes.webm 도 upload 서버 429 뒤 받음. **최종 2건 실패**(roh_moo_hyun·p8 — `commons 429 지속`, 6회 재시도 소진) → exit 1 |
| commons 재실행 | `python tools/fetch_data.py commons` | 캐시로 받은 것은 건너뜀, 남은 2건 ok, exit 0 |
| 인물·국기·미디어 | `python tools/fetch_data.py bgm people media` | exit 0(첫 시도는 commons_v3.json 없음으로 실패). ffmpeg `File ended prematurely` 경고는 길이에 영향 없음 — strikes 24.6초·niovi 59.421초(Phase 1 참조와 동일) |
| 재현성 | people_md5.json 대조 | 인물 4·국기 28·휘장 1 **33/33 동일**(새 도구, 새 컨테이너) |
| 프로젝트 복사·지오 | Phase 4 §0 과 같음 | base 9장 md5 = Phase 3 전부 동일. `asset_md5.json` 42/42 |
| edge-tts CA 주의 | — | pip 설치 뒤 certifi 가 `/root/.local` 에 새로 깔려 CA 를 다시 덧붙여야 했다(`SSLCertVerificationError`) |
| pytest(자산 없이) | `python -m pytest -q` | **489 passed / 3 xfailed / 0 failed** (Phase 4: 457) |

## 1. 대조

| 단계 | 명령 | 결과 |
|---|---|---|
| 원고·음성 | `python -m script.plan projects/hormuz_korea --tts edge` | ok, 292.439초(Phase 4 292.439). 새 컨테이너라 45문장 재합성 |
| 25컷 | `python tools/golden_compare.py --engine new --proj projects/hormuz_korea --reference frames --ref docs/handoff/reports/phase4/injoon_aligned/frames --out docs/handoff/reports/phase5/hormuz_25` | **mean 0.0033 · max 0.0474 /255 PASS**(합격선 0.01·0.1). 17컷 MAD 0.0 |
| 시트 | `python tools/contact_sheet.py sheet --dir .../phase5/hormuz_25` | `hormuz_25/sheet.jpg` |

뱃지 컷(8개 뱃지가 보이는 컷): open_1·route_3·war_1·war_3 는 MAD **0.0**(픽셀 동일). review_0 0.047·decision_0 0.0011·now_0 0.0005·now_3 0.0083.
0이 아닌 컷은 전부 앵커 시각이 Phase 4 와 3~5 ms 다른 컷이다(timeline_4~past_3, edge 재합성의 문장 길이 편차). 뱃지 코드 차이가 아니라 시각 차이다.
review_0 의 큰 차이 80픽셀(>30)은 (485–505, 387–396) 한 곳에 모여 있다 — 항로를 따라 움직이는 배 아이콘의 4 ms 위치 차(육안 확인). "부산에서 출항" 국기 뱃지는 두 프레임이 같다.
