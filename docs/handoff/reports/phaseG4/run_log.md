<!--
tier: 3
last_synced_with: v4.4.0
ssot_for: [phaseG4-run-log]
depends_on: [workers/prompt_loader.py, schemas/order_models.py, engine/primitives/dot_plot.py, engine/layers/series.py, engine/placement.py, docs/handoff/20_GENRE_EXTENSION_FREE_PRODUCTION.md]
last_review: 2026-09-29
-->

# Phase G4 실행 기록 — 첫 비지정학 영상 (v4.4.0)

새 Opus 클라우드 컨테이너(재기동 15 뒤). 시각은 KST. 지침 D-0090, 보강 D-0091, 결정 D-0092(시간축 글자 B)·D-0093(게이트 ② 1차 반려).

## 0. 컨테이너 준비

phaseG3 run_log §0 그대로(하위 에이전트가 수행). hormuz 25/25·랫클리프 20/20·데모 12/12, HEAD(§0) pytest 956 passed.
hormuz 1080p `geo.prep` 첫 실행이 도중에 멈춰 W 티어만 쓰였다 — 같은 명령을 다시 돌려 `ok:true`(종료 코드를 보지 않고 시간 줄만 본 탓).

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 | 7d017a4 | 갤러리 series 예제 레인 라벨 |
| 1 장르 프롬프트 층 | a85ea81 | `prompt_md5.json`(지정학 5개 전후 동일), test_genre_prompts, 파리티 |
| 1 금지 문구 승격 | eb77fef | 원고 3편 해당 0 |
| 2 데이터 | 37ae66b | DFEDTARU·DFEDTARL·SEP_20260916(원자료 재적용), test_series_band_scatter |
| 3 새 요소 | fb56378 | `dot_plot_sketch.jpg`, test_primitive_dot_plot |
| D-0091 ② | d67fd58 | 데모 시트 md5 동일 |
| D-0092 | 4fa735f | `demo_frames.json`·`demo_label_diff.json`(라벨 영역 밖 0) |
| 4 보강 | 785204a | test_g4_project_inputs |
| 4 산출물·게이트 ② 요청 | ded7f27 | `fed_policy/`, R-0109 |
| 6 회귀 | 2577449 | hormuz_after·ratcliffe_mad·demo_after·gallery 34 |
| D-0093 | 8406c3f·415e57c | 시간축 자리, 루프 보정 |
| 7 문서 | f60bcf0 | test_docs_sync |
| 4·9 전편·산출물 | 이 커밋 | artifacts/phaseG4-v4.4.0(16df82d·b1684f4) |

## 2. 명령

```bash
python tools/fetch_series.py DFEDTARU --start 2019-01 --transform month_last --unit % --source "FRED(세인트루이스 연은) · 원출처 연준 이사회" --license us_gov_public_domain --revision-note "…"
python tools/fetch_sep.py 20260916 --license-note "미국 연방정부 기관(연준 이사회) 공식 발표 — 사이트에 별도 저작권 표기 없음(2026-09-29 확인)"
python tools/primitive_sketch.py dot_plot --proj projects/hormuz_korea --genre macro_monetary --extra tests/fixtures/primitives/dot_plot_columns.yaml --out docs/handoff/reports/phaseG4/dot_plot_sketch.jpg
python -m orchestrator.main new-project fed_policy_2026 --title "연준, 다시 금리를 올리다" --category economy --duration-min 4 --topic-summary "…"
# order.yaml(20 §11) → add-source document 9(연준 본문) · article 6(--fetch) → confirm-source(대행) → plan-intake → submit-intake
python -m orchestrator.main verify-sources fed_policy_2026 && python -m orchestrator.main build-research fed_policy_2026 && python -m orchestrator.main build-script fed_policy_2026
python -m orchestrator.main approve --project fed_policy_2026 --gate script_approval --by "opus-g4(게이트 ① 대행 …)"
python -m script.plan projects/fed_policy_2026 --tts edge
python tools/media_fetch.py projects/fed_policy_2026 --only fed_presser_0916,fed_presser_0916_b,fed_presser_0729 --no-sheets   # Flickr license 코드 확인
python tools/ai_direction_run.py projects/fed_policy_2026 --preview auto        # run1(폐기)·run2(게이트 ② 1차)·run3·run4(D-0093)
python -m engine.render projects/fed_policy_2026 --jobs 4 && python -m audio.mix projects/fed_policy_2026 && python -m engine.mux projects/fed_policy_2026
python -m engine.render projects/fed_policy_2026 --jobs 4 --res 1080p && python -m engine.mux projects/fed_policy_2026
python tools/element_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG4/gallery
```

## 3. 측정

| 항목 | 값 |
|---|---|
| 소스·주장·사실 | 소스 15(연준 성명 8·모두발언 1·기사 6) → claim 42(verified 20·corroborated 8·unverified 11·disputed 3) → 사실 31(CME FedWatch 확률 claim 은 장르 데이터 원칙으로 빠짐) |
| 원고 | 11장면 50문장 → 게이트 ① 대행 48문장 307.1초(edge-tts), 린트 오류 0·경고 8(`보도했습니다` 귀속을 휴리스틱이 못 읽음), series 대조 2문장 통과 |
| AI 연출 | run1 폐기(입력 결함 5 — 785204a). run2 v1→v3 checks hard 3→1→0, 검수 hard 3(루브릭 3 false) → 게이트 ② 1차 반려(D-0093). run3 v4→v5: 사진·카드 겹침 hard 가 고정 자리 때문에 연출로 안 풀림 → `timeline_photo` 보정. run4 v4→v7 checks 0→2→0, 검수 hard 3·3(루브릭 3 ok, 5 false) → 국면 창 6→2 보정 |
| 선택 판 | direction v7, checks hard 0(warning media_beats 2), 정직성 4항목 hard 0 |
| 전편 | 480p md5 16f6e945, 1080p md5 9e68c8d7, I −14.02 LUFS · TP −1.59, bgm null, drops 0 |
| 회귀 | hormuz 25/25(checks 18 hard 0), 랫클리프 20/20(hard 0), 데모 12/12(D-0092 새 기준선), 갤러리 34 |
| pytest | 1016 passed · skip 0 · xfail 0(G3 956 + 새 60, 삭제 0) |

## 4. 운영 기록

- 검증 실행 중에 규칙 파일(`rules media.flickr`)을 고쳐 verify-sources 가 check_parsed 에서 실패했다(PIPELINE-AP-010 재발) — 다시 돌렸고, 이후 긴 실행 중에는 규칙·코드를 고치지 않았다.
- 작업 1~3 을 한 작업 트리에서 만든 뒤 커밋을 나누면서 `git apply --unidiff-zero` 로 조각을 올리다 파일이 틀어졌다(푸시 전, 전체 pytest 가 잡음) — 파일별 단계 사본으로 다시 나눠 각 커밋마다 전체 pytest.
- 첫 커밋 분리 시도에서 stash 를 잘못 돌려 작업을 백업(`git diff` + 추적 안 된 파일 tar)에서 복원했다. 손실 없음.
- artifacts 첫 커밋(16df82d)의 provenance 사본에 모델 식별자가 들어갔다 — b1684f4 에서 `config.yaml llm.model` 참조로 바꿨다(이력은 고치지 않음, phase10 run_log §4-3 와 같은 처리).
- 게이트 ② 1차 반려 뒤 D-0093 이 정한 뱃지 자리 [780, 118] 은 채택. 사진 자리는 Fable 이 좌표를 주지 않아 Opus 가 [520,150,250] 으로 넣었다가 카드 자리와 겹쳐 [540,196,240] 으로 옮겼다(되돌리기 = 규칙 값 1개).
