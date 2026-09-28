<!--
tier: 3
last_synced_with: v4.0.0
ssot_for: [phase11-run-log]
depends_on: [GOAL.md, tests/test_goal_g3.py, tests/test_docs_sync.py, docs/handoff/reports/phase11/legacy_refs.json]
last_review: 2026-09-29
-->

# Phase 11 실행 기록 — 문서·정리·GOAL G3 개정 (v4.0.0)

새 Opus 클라우드 컨테이너. 시각은 KST. 지침 D-0072, 결정 D-0073(v1 잔재 코드 삭제 A)·D-0074(NB28 A, 1024×576).

## 0. 컨테이너 준비

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | OK |
| 자산 복원 | `artifacts/phase7-v3.3.0 shared` → hormuz_korea `tts/`·`plan.json`·`media/` | OK |
| 의존성·CA | phase9 run_log §0 그대로(pip 두 파일, apt ffmpeg·fontconfig·fonts-noto-cjk, certifi + `/root/.ccr/ca-bundle.crt`) | OK |
| 입력 데이터 | `fetch_data fonts ne tiles flags bgm` → `commons people`(media 는 돌리지 않음) | exit 0 (Commons 429 대기 몇 번) |
| hormuz 자산 | legacy `assets/{emblems,flags,portraits,rights_registry.json}` 복사 → `geo.prep projects/hormuz_korea` | land-miss W=[MV] 만 |
| 1080p 티어 | `geo.prep projects/hormuz_korea --res 1080p` | **처음에 빠뜨려** 첫 pytest 에서 test_phase10_scale 3건이 AssetError. 만든 뒤 통과(환경 준비 누락, 코드 결함 아님) |
| 기준선 pytest | `pytest` | **763 passed**(Phase 10 760 + NB27 3) |
| 기준선 프리뷰 | `engine.render projects/hormuz_korea --preview golden` | 25컷 md5 → `hormuz_mad_baseline.json`(commit 18072d4 렌더 코드) |

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·NB27·기준선 | `d4dcbce` | `tests/_fonts.py`, test_phase11_nb27 3 |
| 1 GOAL G3 v2 | `e294cc5`·`465c53d` | 17행 + 검증 방법 열, legacy 34 보존, G3-2 게이트 기록 실측 정정 |
| 2 test_goal_g3 | `e40b10b` | 9 테스트, `g3_map.json` |
| 3~6 docs/07·08·09·10 | `9448ec9`·`0b863c9`·`df9d295`·`6ce2e80` | 규칙 키 인용(값 복사 0), handoff 13 §Phase 8·09 §2 동기화 주석 |
| 7 docs/12·03·05 | `0af808f` | 게이트 2개·워커 표 실측·산출물 인덱스 실측 |
| 9 폐기 확인 | `d28f06f` | `legacy_refs.json`, ADDENDUM_02·RUN_LOCAL 삭제 |
| 나머지 Tier 2 동기화 | `1af8ff2` | 00·01·02·04·06·11·13·14·15·16·ADDENDUM_01·03·04·번들 계약 2 |
| D-0073 v1 잔재 삭제 | `f52e1e3` | tts_backends·ApprovalLog/Entry·ThumbnailManifest/Entry·agents/·docs/11, 금지 목록 +3, 25컷 md5 = 기준선 |
| 10 README·HANDOFF·CHANGELOG·DEVLOG·AP | `5e47422` | Released 대장, PIPELINE-AP-010 |
| 8 test_docs_sync | `2ecaec4` | 8 테스트, 주입 검사 4건 실패 확인 후 원복, `docs_sync.json` |
| 11 NB24 | `58dd75e` | `nb24_flags.json`(3 등재·17 비움) |
| 11 NB21 | `a5c2290` | test_phase11_nb21 5, LLM-AP-008 |
| 11 NB28 | `47520bb` | `nb28_media.json`, 컷 3장, 1080p media_upscaled 2 → 0, test_phase11_nb28 7 |
| 레거시 검사 위반 수정 | `7f3e3ae` | test_docs_sync 의 삭제 경로 문자열 → `DELETED_DOC_PATHS` 로 이동(전체 pytest 2 failed → 0) |

작업 순서: D-0072 는 8 → 9 → 10 순이지만, test_docs_sync 가 커밋 시점에 통과하려면 문서 정리(9·10)가 먼저여야 해서 9 → 문서 동기화 → 10 → 8 로 커밋했다.

## 2. 명령

```bash
python -m pytest -q tests/test_goal_g3.py tests/test_docs_sync.py tests/test_phase11_nb21.py tests/test_phase11_nb27.py
python -m engine.render projects/hormuz_korea --preview golden     # 25컷 md5 대조(hormuz_mad_baseline.json)
python -m engine.render projects/hormuz_korea --jobs 4               # 480p video_noaudio md5 대조
```

## 3. 측정

| 항목 | 값 |
|---|---|
| pytest | **792 passed** · skip 0 · xfail 0. Phase 10 760 − 삭제 0 + 새 32(nb27 3·goal_g3 9·docs_sync 8·nb21 5·nb28 7) |
| hormuz 480p 25컷 | 기준선 대비 MAD 최대 **0.0**(`hormuz_480p_mad.json`), md5 25/25 동일 |
| hormuz 480p 전편 | `video_noaudio.mp4` md5 **692f228e** = Phase 6.9·8·10 (jobs 4, 156초) |
| 1080p 프리뷰 | checks hard 0 · warning 0(`media_upscaled` 2 → 0) |
| G3 | 17항목 · 테스트 id 45 · checks 8 · 게이트 2 · 예정 1(`g3_map.json`) |
| 문서 | Tier 1·2 26개 v4.0.0, 규칙 키 인용 188, 폐기 배너 0(`docs_sync.json`) |
| 삭제 | 문서 3(ADDENDUM_02·RUN_LOCAL·11), 코드 v1 잔재 5(tts_backends·ApprovalLog/Entry·ThumbnailManifest/Entry·agents/) |
| NB24 | 24명 중 국기 7(기존 4 + 근거 3), 비움 17 |

## 4. 결정 기록

- R-0087 → D-0073: 사용처 0 v1 코드 삭제(A).
- R-0088 → D-0074: NB28 은 엔진 `load_clip` 한 함수 + `media_fetch --res`(A, 1024×576). 1080p 클립 npy(212MB×2)는 artifacts 에 넣지 않고 복원한 webm 에서 `python tools/media_fetch.py projects/hormuz_korea --res 1080p --no-sheets` 로 재현(md5 `nb28_media.json`).

## 5. 운영 기록

- 1080p 티어 준비 누락(§0) — HANDOFF §4 컨테이너 준비에 `--res 1080p` 를 넣었다.
- 긴 실행(pytest 전체) 중에는 코드·규칙을 바꾸지 않고 문서·보고서만 썼다(PIPELINE-AP-010).
