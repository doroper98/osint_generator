<!--
tier: 3
last_synced_with: v4.5.0
ssot_for: [phaseG5-run-log]
depends_on: [engine/fullcards.py, engine/credits.py, engine/checks.py, engine/subtitles.py, rules/video_rules.yaml, projects/fed_policy_2026/credits.yaml]
last_review: 2026-09-29
-->

# Phase G5 실행 기록 — 검증 라벨 본문 제거·엔딩 카드 한 줄 (v4.5.0)

지침 D-0096(사용자 결정 D85, C9 개정), 결정 D-0098(엔딩 카드 넘침·갤러리 gantt)·D-0099(크레딧 A). 시각은 KST.
작업 0~5 는 재기동 16 세션, D-0098 §2·§4 이후는 재기동 17 세션(새 컨테이너)이 했다.

## 0. 컨테이너 준비(재기동 17)

phaseG4 run_log §0 그대로(하위 에이전트 수행). 차이만 적는다.

| 단계 | 결과·주의 |
|---|---|
| pip·apt(ffmpeg 6.1.1, fonts-noto-cjk)·certifi 에 프록시 CA 덧붙임 | OK. edge-tts 실호출 확인 |
| fetch_data all·people | OK(Commons 429 대기 3회). `fetch_data media` 는 phase9~11 대로 건너뜀(media_src 복원으로 충분) |
| hormuz geo.prep 480p·1080p, ratcliffe geo.prep | `ok:true`(1080p 한 번에 끝남) |
| 자산 복원 | artifacts phase7(hormuz)·phase9(랫클리프)·G3(데모)·G4(fed_policy shared + `out/mix.flac`). G5 브랜치에는 shared 가 없다(입력 = G4) |
| fed_policy 믹스 | `mix.flac` → `ffmpeg … -f f32le -ar 44100 -ac 2 out/mix.f32`. audio.mix 를 다시 돌리지 않았다(§3 오디오 스트림 md5 로 확인) |
| AI 연출 기록 | G5 ARTIFACT_README 절차(run2·run3 사본 → prev/, direction.meta.json) |
| 지오 자산 대조 | phaseG2 `asset_md5.json` hormuz 21/21(480p·1080p)·랫클리프 15/15 |

재기동 16 이 stash 해 둔 D-0098 §2 코드는 커밋되지 않아 컨테이너 회수로 사라졌다. R-0113 의 설계(함수 이름·규칙 키·검사 태그)대로 다시 짰다.

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| 0 VERSION·CHANGELOG | b3fa673 | 1016 passed |
| 1 규칙 notice_unverified | e57bec2 | 1016 passed |
| 2 렌더 라벨 제거·엔딩 한 줄 | 38d72a2 | 1016 passed |
| 3 검사·테스트 12 | ac9bc27 | 1028 passed |
| 4 회귀·첫 재렌더 | 3a2b8e1 | label_off_diff(랫클리프·fed_policy), 갤러리 33/34 |
| 5 문서 | 0487a6b | test_docs_sync |
| D-0098 §2·§4 + D-0099 A | 3a24242(WIP 표기로 먼저 푸시) · b558eac(검증 완결) | 1034 passed, test_g5_endcard_overflow 6 |
| 재렌더·산출물 | 이 커밋 | §3 |

## 2. 명령

```bash
# 크레딧 배치 실측(엔딩 카드 두 열 마지막 기준선, 한도 = H−44 − bottom_margin = 428)
python -c "from pathlib import Path; from engine.project import load_project; from engine import fullcards as f; \
P=load_project(Path('projects/fed_policy_2026')); s=f.project_credit_sections(P.R); \
print(f.endcard_layout(s,[x.column for x in P.R.credits.sections])[1])"          # [415.0, 423.0]
# 전후 프리뷰: G5 직전 코드 e57bec2 + 직전 credits.yaml(git worktree, 자산은 심볼릭 링크) vs 현재
git worktree add /tmp/wt_old e57bec2
python -m engine.render projects/fed_policy_2026 --preview <auto 22 시각>        # 두 트리에서 각각
python -m engine.render projects/fed_policy_2026 --preview 301.12 --res 1080p   # endcard_after.jpg
python -m audio.mix projects/fed_policy_2026      # G4 mix.flac 을 f32 로 풀어 쓰지 않는다(§4)
python -m engine.render projects/fed_policy_2026 --jobs 4 && python -m engine.mux projects/fed_policy_2026   # → final.mp4 를 final_480p.mp4 로 옮긴 뒤
python -m engine.render projects/fed_policy_2026 --jobs 4 --res 1080p && python -m engine.mux projects/fed_policy_2026
```

## 3. 측정

| 항목 | 값 |
|---|---|
| 크레딧 마지막 기준선(한도 428) | fed_policy 415·423(D-0099 A), hormuz 405·347, 랫클리프 215·278, 데모 244·301 — 넘침 0 |
| 자료 절 | 4줄 → 3줄(FEDFUNDS·목표 범위 레코드가 같은 줄). 다른 세 편 합칠 줄 0 |
| 프리뷰 22컷 전후(e57bec2 기준) | 변경 5컷(자막 3·엔딩 2), 영역 밖 0 — `label_off_diff_fed_policy_2026.json`. 엔딩 2컷 bbox y 151~479(옛 판이 화면 아래까지 그렸다) |
| checks | fed_policy hard 0 · warning 2(media_beats, G4 와 같음) |
| 회귀 | hormuz 골든 25/25(END 컷 포함)·랫클리프 20/20·데모 12/12, 모두 hard 0 — `endcard_regression.json` |
| 전편 | 480p `3eb4ae2a8eb48886dac23caedb9d1862`, 1080p `a65ac872bae31f6f9ba37e492f7ca9aa`, 307.12초. 오디오 스트림 md5 `06324317…` = G4, I −14.02 LUFS · TP −1.59 |
| provenance | 첫 판(3a2b8e1)과 차이 = rules_hash 한 칸. final.srt·description.txt 첫 판과 같음, credits.txt 는 자료 줄 합침·절 순서·"사진 · 기사 카드" |
| 산출물 | `endcard_before.jpg`(첫 판 1080p 엔딩 — 국기·음성 절 잘림)·`endcard_after.jpg`(1080p t=301.12)·`fed_policy_sheet.jpg`·`asset_md5.json`, artifacts/phaseG5-v4.5.0 d437214 |
| pytest | 1034 passed · failed 0 · xfail 0(G5 작업 3 1028 + 새 6, 삭제 0) |

## 4. 운영 기록

- 재기동 16 이 R-0113 결정 대기 중 미커밋 코드를 stash 로 두고 멈췄고, 컨테이너 회수로 잃었다. 이번 세션은 자산 복원을 기다리는 동안 코드를 `WIP` 커밋(3a24242)으로 먼저 푸시했다. 이력 재작성 금지라 그 커밋을 고치지 않고, 복원 뒤 전체 pytest 통과를 b558eac 에 적었다.
- 전편 렌더 명령을 480p·1080p 한 줄로 이어 돌려 1080p mux 가 `out/final.mp4` 를 덮었다(mux 출력 이름은 하나). 480p 를 다시 렌더·mux 했다.
- 복원한 G4 `mix.flac`(s32)를 f32 로 풀어 mux 하니 오디오 스트림 md5 가 G4 와 달랐다(18a562f4). G5 첫 판과 같이 `python -m audio.mix` 로 다시 계산하자 `06324317…` 로 G4 와 같아졌다. 그 판으로 두 해상도를 다시 만들었다.
- 프리뷰가 넘치는 엔딩 컷에서 예외로 멈추면 checks.json 이 쓰이지 않아 `[endcard-overflow]` 가 연출 루프에 닿지 않는다. 그래서 프리뷰는 그 컷을 건너뛰고(로그 한 줄) checks offscreen hard 로 남긴다. 전편 렌더는 같은 오류로 멈춘다(D-0098 §2(b) 범위 안의 배선, phase_report 에 보고).
