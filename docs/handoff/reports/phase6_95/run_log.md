<!--
tier: 3
last_synced_with: v3.2.0
ssot_for: [report-phase6_95-run_log]
depends_on: [back_and_forth/260928_204751_D0051_fable_phase6-95-source-intake-kickoff.md, docs/handoff/18_SOURCE_INTAKE_ARTICLES_X.md]
last_review: 2026-09-28
-->

# Phase 6.95 실행 기록 — 소스 인테이크 (v3.2.0, Opus 재기동 6 컨테이너)

## 0. 컨테이너 준비 (6.8 run_log §0 절차 그대로, 시각 KST 9/28)

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` + artifacts 두 브랜치 fetch | OK |
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt`, `apt-get update && apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | OK |
| edge-tts CA | certifi 번들에 `/root/.ccr/ca-bundle.crt` 덧붙임 | 첫 시도는 `grep -q ccr` 조건이 번들 안 다른 문자열에 걸려 **덧붙지 않았다** → taiwan TTS 가 SSL 실패. 조건 없이 덧붙여 해결(다음 컨테이너는 조건 없이) |
| 입력 데이터 | `python tools/fetch_data.py fonts ne tiles flags bgm` → `commons people` | exit 0 (commons API 429 1회 대기) |
| tts·plan 복원(D-0042) | `git archive origin/artifacts/phase6.8-v3.0.0 hormuz/tts hormuz/plan.json` → `projects/hormuz_korea/` | plan.json md5 `200c1e74…` = 6.9 asset_md5 |
| 미디어 원본 복원(D-0044) | `git archive origin/artifacts/phase6.9-v3.1.0 shared/media_src/commons` → `media_fetch.py projects/hormuz_korea --restore-from …` | npy md5 6.9 와 같음(재요청 0) |
| 자산 | `cp -r projects/hormuz_korea_legacy/assets/{emblems,flags,portraits,rights_registry.json} projects/hormuz_korea/assets/` → `python -m geo.prep projects/hormuz_korea` | OK. hormuz_ai 는 hormuz_korea 의 tts·media·assets 하드링크 |

## 1. 25컷 회귀 (합격표 "hormuz Phase 6.9 hormuz_v3 대비 MAD 0")

- **이 컨테이너 안에서** 6.95 첫 커밋 전 프리뷰(`--preview golden`) 대비: 모든 커밋 뒤 **mean 0.0 · max 0.0**(NB9·claims 이관·post·크레딧 각각 확인).
- 6.9 보고서 프레임(`reports/phase6_9/hormuz_v3/golden_compare_commons/frames`) 대비: mean 1.7e-5 · max 2.2e-4(war_2·debate_0 두 컷, 전면에 걸친 1~2 LSB 차이). 입력(plan·direction·media npy·jpg md5)은 6.9 와 같고 **6.95 코드 이전 커밋(2e20017)으로 렌더해도 같은 값**이라 컨테이너 렌더 환경(라이브러리·글꼴 빌드) 차이로 판단한다. 코드 변경의 영향은 0.

## 2. 함정 기록

| # | 무엇 | 처리 |
|---|---|---|
| 1 | 기관 공식 사이트(centcom.mil 등)가 이 환경에서 403(curl·WebFetch 둘 다) | 공식 계정 목록은 Wikidata P2002 SPARQL 로 확인, 항목마다 `check_method: wikidata_P2002` |
| 2 | Wikimedia API 가 컨테이너 IP 에서 429 | SPARQL 은 WebFetch 경유로 조회 |
| 3 | frames.json 이 끝난 문장을 "진행 중"으로 표기 → 시각 검수 거짓 hard | 수정 `94acce0`, PIPELINE-AP-009 |
| 4 | e2e 1회차: 픽스처 캡처의 핸들 `@strait_watcher_x`(16자)가 X 한도(15자) 초과 → 스키마가 거부(판독 자체는 정확) | 픽스처를 `@straitwatch_x` 로 고쳐 재실행 |
| 5 | 옛 상태 이름 금지 테스트가 `--published-at` 의 `published` 에 걸림 | CLI 옵션을 `--pub-date` 로 |
| 6 | 이관 커밋에 옛 모듈 삭제가 섞일 뻔함(`git rm` 스테이징) | 푸시 전 되돌려 두 커밋으로 분리 |
