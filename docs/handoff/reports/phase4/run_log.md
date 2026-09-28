<!--
tier: 3
last_synced_with: v2.3.0
ssot_for: [phase4-run-log]
depends_on: [script/plan.py, script/tts/align.py, engine/timebase.py, tools/golden_compare.py, tools/voice_swap_report.py, tools/fetch_data.py]
last_review: 2026-09-28
-->

# Phase 4 실행 기록 — 원고·음성 (v2.3.0, Opus 클라우드 컨테이너)

## 0. 컨테이너 준비 (새 세션 — 자산이 남아 있지 않다)

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt` | — |
| 바이너리·폰트 | `apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | ffmpeg 6.1.1(Phase 1 과 같은 판). imageio-ffmpeg 만으로는 `ffmpeg` 가 PATH 에 없어 plan 이 실패한다 |
| edge-tts CA | certifi 번들에 `/root/.ccr/ca-bundle.crt` 덧붙임 | Phase 1 run_log §2 와 같음. TLS 검증은 끄지 않는다. 저장소 무변경 |
| 입력 데이터 | `python tools/fetch_data.py all` | fonts·ne·tiles·flags·commons OK(Commons 429 로 약 25분). **bgm 실패**: 얕은 클론이라 `bd37b58` 객체 없음 → `git fetch --unshallow origin overhaul/v2-map-engine` 뒤 재실행 OK |
| 환경 점검 | `python tools/check_env.py` | 20 ok / 0 missing |
| 인물·국기·미디어 | `python tools/fetch_data.py bgm people media` | **삭제 커밋 `4933bd5` 뒤 새 위치(`tools/bootstrap_assets/`)로 실행**, exit 0 (D-0024 검증 8) |
| 프로젝트 복사 | `cp -r $L/assets/{emblems,flags,portraits,rights_registry.json} $P/assets/; cp -r $L/media $P/` | L=projects/hormuz_korea_legacy, P=projects/hormuz_korea |
| 지오 | `python -m geo.prep projects/hormuz_korea` | ok, land-miss W=[MV] small. base 9장 md5 = Phase 3 `asset_md5.json` 전부 동일 |

## 1. 원고·음성

| 단계 | 명령 | 결과 |
|---|---|---|
| 린트 리포트 | (lint_report.json) | hormuz 45문장 오류 0, 경고 source-missing 45(v3 원고에 sources 없음), 자막 3줄 이상 0. taiwan 2문장 0/0 |
| 기준 목소리(정렬 전) | `python -m script.plan projects/hormuz_korea --tts edge` | 292.45초(Phase 2 292.44 — edge 재합성 편차) |
| ElevenLabs 3문장 | `python tools/tts_align_probe.py projects/hormuz_korea --sids ask_1 ask_4 past_3 --out align_probe.json --fixtures tests/fixtures/tts` | 실합성 3문장만(D31). 픽스처 = alignment + 문장 메타(음성·voice_id 없음, D-0022) |
| edge 단어 경계 실측 | `python tools/edge_word_probe.py projects/hormuz_korea --sids ask_1 ask_4 past_3 --voices ko-KR-InJoonNeural ko-KR-SunHiNeural --out edge_word_probe.json` | 비율 추정 오차 최대 0.97초(InJoon ask_1 "한국") → R-0020 → D34 |
| 기준 목소리(정렬) | `python -m script.plan projects/hormuz_korea --tts edge` | 정렬 없는 캐시 45 → 재합성(`tts_resynthesized` 45), **292.44초** |
| 교체 목소리 | `python -m script.plan projects/hormuz_korea_sunhi --tts edge --edge-voice ko-KR-SunHiNeural` | 293.93초, 재합성 45 |

`projects/hormuz_korea_sunhi/`(gitignore)는 원 프로젝트 파일(script·direction·labels·credits·description·geo, assets·media)의 **심볼릭 링크**다.
direction.py 는 한 파일이다 — `git diff projects/hormuz_korea/direction.py` 0, sha1 `3411936a3cec…` 양쪽 동일.

## 2. 대조·증명

| 단계 | 명령 | 결과 |
|---|---|---|
| 정렬 영향 컷 특정 | 같은 plan 의 mp3 경로만 바꾼 비교 프로젝트(정렬 없음 → 비율)와 정렬 프로젝트를 각각 25컷 렌더 | 차이 컷 **09_ask_1 하나**(MAD 0.0983). `docs/handoff/golden/expected_deltas.json` 등재, `golden_delta/09_ask_1_{aligned,ratio}.png` |
| InJoon ↔ Phase 2 | `python tools/golden_compare.py --ref docs/handoff/reports/phase2/frames --out .../phase4/injoon_aligned` | 평균 0.0074 · 최대 0.078 /255 PASS (의도된 차이 1컷 제외, 그 컷도 0.098) |
| 골든 PNG | `python tools/golden_compare.py --reference golden --out .../phase4/vs_golden` | 평균 1.833 · 최대 3.10 (Phase 3 1.825 — 09 컷 1.77 포함 참고값) |
| SunHi ↔ InJoon | `python tools/golden_compare.py --proj projects/hormuz_korea_sunhi --ref .../phase4/injoon_aligned/frames --out .../phase4/sunhi` | 같은 앵커 평균 0.14 · 최대 0.75 — 같은 구성 |
| 증명표 | `python tools/voice_swap_report.py --a projects/hormuz_korea --b projects/hormuz_korea_sunhi --eleven tests/fixtures/tts --out .../phase4/voice_swap` | direction 동일 · 전환−경계 ≤1 ms(7단어×3목소리) · Δ전환=Δ경계 7/7 |
| 시트 | `contact_sheet.py sheet --dir .../injoon_aligned`, `contact_sheet.py versus --dir .../injoon_aligned --dir2 .../sunhi --out .../voice_swap/sheet_injoon_vs_sunhi.jpg` | 25쌍 육안 동일 구성 |
| 거절 전환 스트립 | 각 국가 경계 −0.15 / +0.35초 프리뷰(두 목소리) → `voice_swap/refusal_sync.jpg` | 10쌍 모두 −0.15초 미전환, +0.35초 전환 |

## 3. 전편

| 단계 | 명령 | 결과 |
|---|---|---|
| SunHi | `python -m engine.render projects/hormuz_korea_sunhi --jobs 4 && python -m audio.mix … && python -m engine.mux …` | 293.925초 854×480@24, −14.2 LUFS / TP −2.3, final md5 `36a1faca…` |
| InJoon | 같은 명령, projects/hormuz_korea | 292.439초, final md5 `761b3ae6…` (Phase 2 와 다름 — 09 컷 부근 전환 시각, D34) |
| 영상 본체 | orphan `artifacts/phase4-v2.3.0` (`ba7280d`) | sunhi/·injoon/ 각 final.mp4·video_noaudio.mp4·mix.flac·final.srt·provenance.json |

provenance(두 편 공통): `word_anchor: aligned`, `features_used.at_word {aligned 7, ratio 0}`, `tts.resynthesized` 45, badges 8,
rules_hash `9b55a204…`. 사본 `provenance_{injoon,sunhi}.json`.

## 알려진 차이
- InJoon 전편은 Phase 2 와 바이트가 다르다. 원인 두 가지: (1) 정렬 재합성으로 mp3 가 새로 만들어졌다(총 길이는 292.44 로 같음) (2) 국가별 "거절" 전환이 발음 시각으로 옮겨졌다(의도, D34). 25컷 대조는 PASS.
- 음악-내레이션 차는 Phase 2 와 같은 v3 이득 0.47(Phase 8 과제).
