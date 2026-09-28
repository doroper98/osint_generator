<!--
tier: 3
last_synced_with: v3.0.0
ssot_for: [phase6_8-run-log]
depends_on: [orchestrator/engine_service.py, orchestrator/pipeline.py, orchestrator/gate_view.py, tools/e2e_command_center.py]
last_review: 2026-09-28
-->

# Phase 6.8 실행 기록 — 오케스트레이터 통합 (v3.0.0, Opus 재기동 5 컨테이너)

## 0. 컨테이너 준비 (Phase 6.5 run_log §0·§4 절차)

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | bgm `bd37b58` 객체 |
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt` | OK |
| 바이너리·폰트 | `apt-get update && apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | update 먼저(안 하면 404) |
| edge-tts CA | certifi 번들(`/root/.local/.../certifi/cacert.pem`)에 `/root/.ccr/ca-bundle.crt` 덧붙임 | 저장소 무변경 |
| 입력 데이터 | `python tools/fetch_data.py fonts ne tiles flags bgm` | 전부 exit 0 (15:08~15:09) |
| Commons·인물 | `python tools/fetch_data.py commons people` | exit 0 (15:28~15:30, API 429 1회 33초) |
| 프로젝트 복사 | `cp -r $L/assets/{emblems,flags,portraits,rights_registry.json} $P/assets/` | L=projects/hormuz_korea_legacy, P=projects/hormuz_korea |
| 지오 | `python -m geo.prep projects/hormuz_korea` | ok, land-miss W=[MV](종전과 같음) |
| 원고·음성 | `python -m script.plan projects/hormuz_korea --tts edge` | **새 컨테이너 재합성** 45문장, 292.44초 |
| 미디어 | `python tools/media_fetch.py <빈 폴더>` (D-0038) → `python tools/media_fetch.py projects/hormuz_korea --variant dvids --restore-from <보존본>` | 사진 3 = Commons(새 다운로드 md5 6/6 = Phase 6.5). 영상 2 = DVIDS 1차 출처(D-0045, `dvids_match.md`) — Commons 원본은 환경 차단(§5) |

tts 캐시는 artifacts 브랜치에 없었다(D-0042). 이번 artifacts 에 `hormuz/tts/`·`plan.json` 을 넣어 다음 컨테이너부터 복원한다.

## 5. Commons 원본 영상 차단 기록 (D-0044 §1 — 한 번에 파일 하나, 30분 간격, 1회 시도)

| 시각(KST) | 파일 | 결과 |
|---|---|---|
| 15:41~16:32 | strikes 원본 webm | 429 × 7(600초 대기 6회, 옛 재시도 정책) → FAIL. 서버 문구 "instead use thumbnail images" — 원본 요청 IP 단위 차단으로 판단 |
| 16:32 | niovi 원본 webm | API 429 48초 1회 뒤 upload 429 → D-0044 정책으로 전환하며 중지 |
| 16:38 | strikes (30분 정책 1회차) | API 429 18초 뒤 upload 429(서버 Retry-After 600초) → FAIL. 다음 17:19 |
| 17:19 | strikes (2회차) | API 통과, upload 429(Retry-After 600초) → FAIL. 다음 ~17:59 |

이후 시도는 `media_fetch.py <빈 폴더> --only <mid> --tries 1` 을 30분 간격으로 한다(아래 행 추가). 받는 즉시 원본·npy 를
`artifacts/phase6.8-v3.0.0/hormuz/media_src/` 에 보존한다(D-0044 B, 복원 = `--restore-from`).

## 1. 커밋 단위 (D-0040 작업)

| 작업 | 커밋 | 비고 |
|---|---|---|
| 1 VERSION 3.0.0·NB7 | 4dab126 | |
| 2 상태 머신 | 5d573c3 | xfail c 해제 |
| 3 옛 상태 사용처 | ef4ac44 | 옛 상태 문자열 0 테스트 |
| 4 engine_service | 768f04d | script.lint CLI |
| 6 게이트 | 3ac933e | advance·gate-view·TUI 키 |
| 5 Script 전환 | 692a233 | D-0043 라벨 코드 계산 |
| 7 preview provenance | b5fddec · d1f429c | xfail provenance_e2e 해제(D-0041) |
| 8 병합 삭제 | bdd2371 | rules tts_risk·pronounce |
| 문서 C7 | c3e26f9 | 02·03·05 |
| 10 e2e 드라이버 | 0124772 · 9a6335b | taiwan 실패 시 머묾 실측 |
| 미디어 | 5945a20 · 874b2b0 | restore·tries·variant(D-0044·D-0045) |
| 10 산출물 | fe7aec3 | |

## 2. 증명

| 항목 | 명령 | 결과 |
|---|---|---|
| pytest | `python -m pytest -q` | **609 passed / 0 xfailed / 0 failed**(Phase 6.5: 564 / 2) |
| provenance e2e | `tests/anti_inertia/test_provenance_e2e.py`(`--preview golden`) | 통과 — 뱃지 8·패널 5종·미디어 2/2/1/2·label_lod·drops []·stages render/mix/mux false·25컷·sheet |
| 25컷 | `python tools/golden_compare.py --engine new --proj projects/hormuz_korea --reference frames --ref docs/handoff/reports/phase6_5/hormuz_25/frames --out docs/handoff/reports/phase6_8/hormuz_25` | 판정 22컷 mean **0.0158** · max 0.0976. 클립 컷 2(war_2 niovi 0.090, timeline_4 strikes 0.0976 — DVIDS 원본) 제외 시 mean **0.0080** · max 0.0828(now_3). 나머지 차이는 edge 재합성 시각 편차(292.441 vs 292.439초) |
| 엔진 CLI 직접 | `engine.render --jobs 4 → audio.mix → engine.mux` (`direct_cli.log`, 4분 12초) | final md5 `003df086a1d6627cbdcfd3c773ffb0b2` |
| Command Center e2e | out/·prev/·manifest 삭제 뒤 `python tools/e2e_command_center.py hormuz_korea --reject-demo` (`e2e_hormuz.log`) | CREATED → DONE, StageResult 7단계 전부 ok, 반려 2회(script_approval→script_draft, preview_approval→direction) 뒤 재승인. **final md5 `003df086…` = CLI 직접(바이트 동일)**, plan.json 불변(`200c1e74…`) |
| provenance | `provenance_hormuz.json` | features_used = Phase 6.5 와 동일, stages plan·geo·preview·render·mix·mux true(ai_direction·visual_qa false = 6.9), drops [], media used 7·density 경고 0·lint [] |
| 게이트 화면 | `gate_script_approval.txt`·`gate_preview_approval.txt` | e2e 중 TUI 가 띄운 텍스트 그대로 |
| 영상 본체 | orphan `artifacts/phase6.8-v3.0.0` (`0e64045`) | out + **tts·plan**(D-0042) + **media_src**(DVIDS 원본·npy·사진 원본, D-0044 B) + 복원 절차 |
