<!--
tier: 3
last_synced_with: v3.6.0
ssot_for: [phase10-run-log]
depends_on: [engine/style.py, engine/render.py, engine/projection.py, engine/assets.py, engine/checks.py, geo/prep.py, tools/res_compare.py, config.yaml]
last_review: 2026-09-29
-->

# Phase 10 실행 기록 — 해상도·성능 (v3.6.0)

새 Opus 클라우드 컨테이너(4 CPU · 15GB). 시각은 KST. 지침 D-0066, 결정 D-0067(px = 장치 변환 한 곳)·D-0068(label_hidden)·D-0069(glyph_size).

## 0. 컨테이너 준비

| 단계 | 명령 | 결과·주의 |
|---|---|---|
| 클론 | `git fetch --unshallow origin overhaul/v2-map-engine` | OK |
| 의존성·CA | phase9 run_log §0 그대로 | OK |
| 자산 복원 | `artifacts/phase7-v3.3.0 shared` → hormuz_korea `tts/`·`plan.json`·`media/`, `artifacts/phase9-v3.5.0 shared` → ratcliffe2026 `tts/`·`plan.json` | OK |
| 입력 데이터 | `fetch_data fonts ne tiles flags bgm` → `commons people`(media 는 돌리지 않음) | exit 0 |
| hormuz 자산 | legacy `assets/{emblems,flags,portraits,rights_registry.json}` 복사 → `geo.prep projects/hormuz_korea` | land-miss 없음 |
| hormuz 1080p 티어 | `python -m geo.prep projects/hormuz_korea --res 1080p` | 70초, `assets/res_1080p/` 30.2MB |
| ratcliffe 자산 | phase9 §0.1 함수 그대로(라이브러리 초상 3·`build_flag_pngs`·`record_bundles`) + 레지스트리 국가 국기 11종(om·ae·sa·qa·iq·kw·bh·ye·kp·ru·ua) SVG `download` → `geo.prep projects/ratcliffe2026` | 국기 PNG 50 |
| 기준선 | `pytest` | 710 passed(= Phase 9) |
| 비교 기준 | `git worktree add … 99a84b7` 에서 hormuz `--preview golden` | 25컷 기준 PNG(MAD 0 판정용) |

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 NB23·NB16 | `bcaea3c` | Phase 9 v3 연출 → `[card-over-date]` hard 1, hormuz MAD 0, 테스트 10 |
| §0-2 ④ 재실행 1회차 | `5317cba` | checks hard 0·카드×날짜 0(3판), 시각 hard 10→6→3 → R-0081 |
| 1 출력 프로파일 | `b68b13b` | test_phase10_profile |
| 2 장치 변환 | `5616965` | test_phase10_scale·test_device_space, k=1 MAD 0 |
| 3 지오 티어 | `b870842` | test_phase10_geo, 480p base md5 9/9 동일 |
| D-0068 label_hidden | `3a2aa9a` | test_phase10_label_hidden, hormuz 0% |
| 4 1080p 골든 | `2b39af2` | `res_compare.json`(평균 0.0107·최대 0.0181 ≤ 0.02, 위치 차 0/16, frames.json 동일), `v480_vs_1080.jpg`, 원본 3컷 |
| 재실행 2회차(D-0068 §3) | `1f6bd56` | v1 checks 2 → v2 checks 0·시각 hard 7 → v3 checks 1, 선택 v2 → R-0083 게이트 ② |
| 6 성능 | `b558ef8` | test_phase10_profile JobsTest, `perf.json` |
| 5 glyph_size | `65fe1cd` | test_phase10_glyph_size, `glyph_size.json`(hormuz·ratcliffe hard 0) |
| 7 전편 | artifacts `e336af1` | hormuz 1080p `e194d84a`, ratcliffe 480p `75b92192` |

## 2. 명령

```bash
python -m engine.render projects/hormuz_korea --preview golden                 # prev/ (480p)
python -m engine.render projects/hormuz_korea --preview golden --res 1080p     # prev_1080p/
python tools/res_compare.py projects/hormuz_korea --out docs/handoff/reports/phase10
python -m engine.render projects/hormuz_korea --res 1080p && python -m audio.mix projects/hormuz_korea && python -m engine.mux projects/hormuz_korea
python tools/ai_direction_run.py projects/ratcliffe2026 --preview auto         # direction.yaml·v*.yaml 을 치운 뒤(연출가부터)
python -m engine.render projects/ratcliffe2026 && python -m audio.mix projects/ratcliffe2026 && python -m engine.mux projects/ratcliffe2026
```

## 3. 측정

| 항목 | 값 |
|---|---|
| 1080p 축소 MAD(25컷) | 평균 0.0107 · 최대 0.0181(p_0214.46) — 1080p 티어 전에는 평균 0.0097·최대 0.0178. 차이는 지형·사진 선명도 |
| 위치 | place_over 상자 16/16 동일, frames.json 동일 |
| 480p 무변경 | 25컷 MAD 0, 전편 video_noaudio md5 `692f228e` = Phase 6.9·8 artifacts |
| 렌더 시간(jobs 4, 7,018프레임) | 480p 149.9초 · 1080p 328.1초(×2.19) |
| 청크 피크 RSS | 480p 190MB · 1080p 446MB |
| mix | hormuz mix.f32 `c1314fb9`(무변경), 2패스 loudnorm 그대로 |
| 1080p 전편 | 1920×1080@24, 292.44초, 95.0MB, 오디오 QA hard 0(I −14.03 · TP −1.47) |
| 랫클리프 480p | 226.44초, 오디오 QA hard 0(I −14.01 · TP −1.69), mix.f32 `f3a5c880`(Phase 9 와 같다) |
| 최소 글자 | 9.5 미만은 전부 `end_card`·`media_meta`(7.5·7.8·8.5·9.2, 1080p 환산 16.9~20.7px) — glyph_size.json |
| media_upscaled | hormuz 1080p 클립 2(원본 `_480.npy` 480px < 675·990px). 원본 webm 에서 1080 추출은 후속 후보 |
| pytest | 760 passed · skip 0 · xfail 0(Phase 9 710 + 새 50, 삭제 0) |

## 4. 운영 기록(실수와 조치)
1. 480p 성능 렌더 1회차가 청크 실패로 끝났다. 실행 중 같은 워크트리의 엔진 코드를 고쳐, 늦게 import 하는 청크가 반쯤 바뀐 모듈을 읽었다. 단독 재실행 정상.
2. 랫클리프 재실행 2회차 첫 시도가 연출 워커 입력 오류로 판 없이 멈췄다. 실행 중 본 트리에 규칙(`golden`)을 옮겨, 이미 떠 있던 프로세스의 옛 스키마가 새 규칙을 거부했다. 같은 2회차를 다시 시작(로그 `ratcliffe_run2/aborted_attempt.log`).
3. 1회차 보고서 사본(`nb23/ratcliffe/provenance.json`·`direction.meta.json`)에 모델 식별자가 들어간 채 푸시됐다(`5317cba`). 새 커밋에서 `config.yaml llm.model` 참조로 바꿨다(이력은 고치지 않음).
→ 긴 실행(AI 연출·전편 렌더) 중에는 그 트리의 코드·규칙을 바꾸지 않는다. 개발은 별도 워크트리에서 한다.
