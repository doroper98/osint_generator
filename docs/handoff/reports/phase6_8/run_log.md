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
| 미디어 | `python tools/media_fetch.py <빈 폴더>` (D-0038 새 다운로드 대조 겸) | 5건 중 3건 ok. strikes·niovi 원본 upload.wikimedia 429 대기 중 |

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
