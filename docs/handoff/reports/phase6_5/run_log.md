<!--
tier: 3
last_synced_with: v2.5.5
ssot_for: [phase6_5-run-log]
depends_on: [assets/media/media_registry.json, schemas/media_models.py, engine/layers/media.py, engine/media_plan.py, tools/media_fetch.py, tools/media_report.py, tools/fetch_data.py]
last_review: 2026-09-28
-->

# Phase 6.5 실행 기록 — 사진·영상·컷아웃·기사 (v2.5.5, Opus 클라우드 컨테이너)

## 0. 컨테이너
Phase 5·6 컨테이너(재기동 4)를 그대로 썼다. 자산·plan 은 Phase 5 run_log §0 과 같다.

## 1. 커밋 단위 검증 (25컷 = `golden_compare --reference frames --ref docs/handoff/reports/phase6/hormuz_25/frames`)

| 작업 | 커밋 | 25컷 | 비고 |
|---|---|---|---|
| 1 VERSION·NB6 | c6dc296 | — | 관계 패널 규칙 4 "첫 선 시작 뒤", lint |
| 2 레지스트리 | 5a49702 | 0 / 0 | 엔진이 저장소 레지스트리를 읽음 |
| 3 권리 게이트 | 512832b | 0 / 0 | 이벤트 mid 만 — 화면 문구가 레지스트리에서 와도 픽셀 동일 |
| 4 media_fetch | d405331 | — | 이 컨테이너 원본 5개 재가공 → 가공 파일 md5 5/5 = Phase 6 |
| 5 부트스트랩 삭제 | 483a01c | — | `tools/bootstrap_assets/` 없음 |
| 6 배치·밀도·제안 | 352c60c | 0 / 0 | hormuz 경고 0(배치·밀도) |

## 2. 증명

| 항목 | 명령 | 결과 |
|---|---|---|
| 미디어 7종 재현 | `python tools/media_report.py projects/hormuz_korea --old-rev 615ddd7 --out docs/handoff/reports/phase6_5` | 7/7 화면 문구 = 레지스트리 조립 = 옛 연출 문자열(글자 단위). `media_reproduction.{md,json}` |
| 밀도 | `engine.media_plan.density_report` → `media_density_report.json` | 7개 / 292.4초 = 41.8초당 1개, 40초 창 최대 2개(strikes·p8), 경고 0종(D38) |
| 검수 시트 | `tools/media_fetch.py` → `thumbsheet_strikes.jpg`·`thumbsheet_niovi.jpg` | 12장, 사용 구간(strikes 1.5–6.5 / niovi 28–33초) 초록 테두리 |
| 기본 배치 | 테스트 `test_defaults_reproduce_v3` | x·y·w 를 지우면 기본 배치가 v3 4건 좌표와 같다 |

## 3. 전편

| 단계 | 명령 | 결과 |
|---|---|---|
| 렌더·믹스·먹스 | `python -m engine.render projects/hormuz_korea --jobs 4 && python -m audio.mix … && python -m engine.mux …` | 292.439초, −14.2 LUFS / peak −1.4 dBFS, **final md5 `94d39281…` = Phase 6 과 바이트 동일** |
| provenance | `provenance_hormuz.json` | `media.suggested` 15문장, `used` 7, `suggested_and_used` 6장면(now·past·review×2·timeline·war — debate 기사만 트리거 밖), `density.warnings []`(40초 창 최대 2 — strikes·p8), `placement` explicit 4, `lint_warnings []`, rules_hash `45e152ac…`(D-0037 반영 뒤 mux 재실행, final md5 불변) |
| 영상 본체 | orphan `artifacts/phase6.5-v2.5.5` (`120ae9c` → provenance 갱신 `7c8dd60`) | hormuz/out 전편 |

## 4. 재기동 5 (2026-09-28 14:43 KST~, 새 컨테이너)

| 단계 | 명령 | 결과 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | 얕은 클론 해제(bgm `bd37b58` 대비) |
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt` | OK |
| 바이너리·폰트 | `apt-get update && apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | ffmpeg 6.1.1. **update 없이 install 하면 archive 404 로 실패**. ffmpeg 가 없으면 `ThumbSheetTest::test_twelve_frames` 가 FileNotFoundError |
| pytest | `python -m pytest -q` | **564 passed / 2 xfailed** (재기동 4 값과 같음) |
| phase_report | R-0038 (`8fb525f`) | 새 다운로드 md5 = pending |
| 새 다운로드 md5 | `python tools/media_fetch.py <빈 폴더> --report <빈 폴더>/../fresh_report.json` | 14:47:55 시작. hormuz_transit ok, rok_iraq 원본에서 upload.wikimedia 429 — 600초 대기(1/6). 끝나면 가공 파일 md5 를 `asset_md5.json media_files` 와 대조 → `fresh_media_md5.json` + progress(responds_to D-0038) |
