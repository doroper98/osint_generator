<!--
tier: 3
last_synced_with: v3.5.0
ssot_for: [phase9-run-log]
depends_on: [bundle/load.py, bundle/entities.py, bundle/to_sources.py, bundle/to_script.py, bundle/to_direction.py, orchestrator/bundle_service.py, tools/bundle_corpus_stats.py]
last_review: 2026-09-29
-->

# Phase 9 실행 기록 — 번들 어댑터 (v3.5.0)

새 Opus 클라우드 컨테이너. 시각은 KST. 지침 D-0063, 결정 D-0064.

## 0. 컨테이너 준비

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | OK |
| 의존성 | `pip install -r requirements.txt -r requirements-engine.txt`, `apt-get update && apt-get install -y ffmpeg fontconfig fonts-noto-cjk` | OK |
| edge-tts CA | certifi 번들에 `/root/.ccr/ca-bundle.crt` 조건 없이 덧붙임 | OK |
| 자산 복원 | `git archive origin/artifacts/phase7-v3.3.0 shared` → hormuz_korea `tts/`·`plan.json`·`media/` | OK |
| 입력 데이터 | `python tools/fetch_data.py fonts ne tiles flags bgm` → `commons people` | exit 0(Commons 429 대기 2회) |
| 미디어 | `fetch_data media` 는 **중단**했다 — 복원한 media_src 를 Commons 에서 다시 받으려 해 429 대기만 반복. 복원본으로 충분(Phase 7 ARTIFACT_README) | — |
| hormuz 자산 | legacy `assets/{emblems,flags,portraits,rights_registry.json}` 복사 → `python -m geo.prep projects/hormuz_korea` | land-miss 없음 |
| 기준선 | `pytest` | 675 passed · skip 0(= Phase 8) |

### 0.1 실증 프로젝트 자산(ratcliffe2026)
기존 도구 함수만 썼다: `tools.fetch_data.download`+`build_flag_pngs`(국기 16종 SVG→PNG), `tools.portrait_fallback.library_portrait`
(trump·putin·zelensky 라이브러리 가공본), `tools.commons_fetch.record_rights`·`record_bundles`(rights_registry). 그 뒤 `python -m geo.prep projects/ratcliffe2026`
(W 티어 −88~70°E·12~66°N ppd 24, G 티어 유럽 동부 ppd 96 — 번들 마커 8곳 전부).

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 첫 커밋 | `49b3b80` | corpus_load.json 68 pass, 미지 필드 8경로(당시 조용히 버려짐) |
| 1 엔티티 조인 | `74f2dab` | test_bundle_entities 5 |
| 쟁점 1 A 로더 forbid | `f3283f6` | 68 pass·미지 0, 옛 무시 테스트 2 → 거부 테스트 2 |
| 2 출처·claim 후보 | `865769b`·`b515543` | test_bundle_sources 10, 랫클리프 이관 11·미해결 5 |
| 3 원고 초안 | `e236e7e` | test_bundle_script 9, 코퍼스 59/63 장면 수 ≠ 섹션 수 |
| 4 연출 재료 | `28c1536`·`560dbc7` | test_bundle_direction 7, 번들 패널 갤러리(추정 태그 4/4) |
| 5 import-bundle·웹·provenance | `6da026b` | test_bundle_import 4 |
| 7 D7 문서 | `c07f5e9` | corpus_stats.json·ratcliffe_stats.json |
| 6 실증 | `fe18b52`·`0fb1232`·`97883d8`, artifacts `211cdbc` | ratcliffe/·rw_demo/, final.mp4 |
| 실증에서 찾은 결함 | `b515543`(인용 제목 아포스트로피), `560dbc7`(미등재 국기 ua), `fe2f82f`(레지스트리 푸틴·젤렌스키 국기 보강) | 각 커밋 메시지 |

## 2. 명령 (랫클리프)

```bash
python -m orchestrator.main new-project ratcliffe2026 --title "모스크바에 내린 수송기 한 대" --category geopolitics --topic-summary "…"
python -m orchestrator.main plan-intake ratcliffe2026
python -m orchestrator.main import-bundle ratcliffe2026 --file samples/ratcliffe2026/analysis_20260829_115457_ec53e620b2.bundle.json
python -m orchestrator.main confirm-source ratcliffe2026 --id src_art_00NN --by "opus-e2e(…대행…)"   # 11건
python -m orchestrator.main submit-intake ratcliffe2026
python -m orchestrator.main verify-sources ratcliffe2026        # claims 17: corroborated 6 · unverified 7 · disputed 4
python -m orchestrator.main build-research ratcliffe2026
python -m orchestrator.main build-script ratcliffe2026          # 초안 블록 사용(script.meta.json draft_sha1)
python -m orchestrator.main transition ratcliffe2026 --to script_approval && python -m orchestrator.main gate-view --project ratcliffe2026
python -m script.plan projects/ratcliffe2026 --tts edge         # 38문장 226.44초
python tools/ai_direction_run.py projects/ratcliffe2026 --preview auto   # 1차 실패(아래 §4), 2차 1,465초
python tools/panel_gallery.py --proj projects/ratcliffe2026 --materials projects/ratcliffe2026/intake/bundle_materials.json --out docs/handoff/reports/phase9/ratcliffe/bundle_panels
python -m engine.render projects/ratcliffe2026 --jobs 4 && python -m audio.mix projects/ratcliffe2026 && python -m engine.mux projects/ratcliffe2026
python tools/bundle_corpus_stats.py json samples/{bom_rnd,hualien2024,neasia2026,semicon2026,skt_aidc,spacex2026} --out docs/handoff/reports/phase9/corpus_stats.json
```

**사용자 확인 대행**: 18 §7 의 사용자 확인은 실증 운영자(Opus)가 대행했다(`confirmed_by` 에 대행임을 적음). 매체·제목·게시일을 가져온 본문 첫머리와 대조만 했다.
실사용에서는 사람이 확인한다.

## 3. 측정

| 항목 | 값 |
|---|---|
| 코퍼스 | 68 로드 pass(fail-closed, 미지 0). 초안 63(narration 없는 5 = 명시 오류), 장면 수 ≠ 섹션 수 59/63 |
| 랫클리프 초안 | 섹션 12 → 장면 7(경계 근거 주석), rewrite_required 0, 엔티티 unmatched 14, timeline 날짜 대응 2/52 |
| 랫클리프 최종 원고 | ScriptWorker 1회: 9장면 38문장, 섹션 제목 화면 0, 금지 문구 0, 린트 오류 0·경고 5. 초안 문장 그대로 남은 것 0(전부 facts 근거로 다시 씀) |
| 출처 | 16 → 기사 11 · 미해결 5(타임아웃 1·403 3·월까지만 날짜 1). 게이트 ① 뷰에 이관·미해결 줄 |
| AI 연출 | 3판, 검수 hard 7 → 1 → 1, 선택 v3(checks hard 0·warning 1(미디어 없음)). 연출가는 번들 패널 대신 timeline·versus 를 골랐다(재료는 강제 아님, P8) |
| 번들 패널 | network·dots·gantt·dual_line 4종 전부 "추정 · 출처 미기재" 태그(bundle_panels/) |
| 전편 | final.mp4 md5 `8145bf2c…`, 226.44초, I −14.01 LUFS · TP −1.69(2패스 linear), bgm null, drops 0 |
| 재작성 실증(bundle_rw_demo) | 초안 rewrite_required 1("전선의 승부는 …") → ScriptWorker 1회 뒤 최종 20문장 금지 문구 0·린트 오류 0 |
| hormuz 무영향 | 25컷 MAD 평균·최대 0(Phase 8 `182963f` 워크트리 대비, 같은 자산) |

## 4. 실증에서 찾은 결함(고침)
1. 인용 문자열 제목의 아포스트로피("Director's")에서 제목이 잘림 → 첫 따옴표~마지막 같은 따옴표(`b515543`).
2. 번들 재료가 레지스트리에 없는 국기(ua)를 넘겨 연출가 검증이 실패 → 재료는 레지스트리 국가만, 국가 4개 등재(`560dbc7`).
3. 라이브러리 인물 푸틴·젤렌스키에 국기가 비어 인물 뱃지 검증 실패(연출가 2회 실패, 1차 실행) → 레지스트리 보강(`fe2f82f`). 라이브러리 인물 22명이 같은 상태(후속 후보).
