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

## 2. 전편

| 단계 | 명령 | 결과 |
|---|---|---|
| 렌더·믹스·먹스 | `python -m engine.render projects/hormuz_korea --jobs 4 && python -m audio.mix … && python -m engine.mux …` | 2분 26초. **292.439초** 854×480@24, **−14.2 LUFS / peak −1.4 dBFS**, final md5 `e5c503aa…` |
| 크레딧 프레임 | `ffmpeg -ss 290.0 -i out/final.mp4 -frames:v 1 credits_frame.png` | 엔딩 카드 5묶음(보도·인물·휘장국기지도·사진영상·음악음성), 폰트 행 없음(D35) |
| 사본 | `provenance_hormuz.json`, `credits.txt`, `description.txt`(끝에 폰트 4종 자동 블록) | — |
| 영상 본체 | orphan `artifacts/phase5-v2.4.0` (`e8e4171`) | hormuz/out: final.mp4·video_noaudio.mp4·mix.flac(44.1 kHz → 24비트)·final.srt·provenance·credits·description |

provenance 요약: `assets.images_used` 22키(휘장 `emblem:navcent` 1, 국기 14, 미디어 3, 인물 4), `emblems {used [navcent], flag_fallback {}}`,
`badges` suggested 19 / used 6 / 교집합 5(제안 47건), `credits.card {people 4, emblems 1, flags 1, map 2, media 5, music 1, narration 1}`,
`credits.description_only {fonts 4}`, `features_used.badges 8 (person 3, flag 4, emblem 1)`, `at_word {aligned 7, ratio 0}`, rules_hash `8f475f8e…`.
제한 휘장 대체 경로의 실사용 증명은 hormuz 에 제한 휘장이 없어 `emblem_fallback_demo.json`(taiwan 사본, irgc·cia → 국기, 휘장 키 0회)으로 한다.

## 알려진 차이
- 앵커 6개가 Phase 4 와 3~5 ms 다르다(timeline_4~past_3). 새 컨테이너의 edge 재합성 편차다. 25컷 PASS.
- mix.flac 을 만들 때 표본율을 48 kHz 로 잘못 넣어 길이가 269초로 나온 것을 발견해 44.1 kHz(`audio.mix.SR`)로 다시 만들었다(292.939초). 올린 파일은 고친 쪽이다.
