<!--
tier: 3
last_synced_with: v4.8.0
ssot_for: [phaseG7-run-log]
depends_on: [rules/video_rules.yaml, tools/golden_delta_proof.py, docs/handoff/golden/expected_deltas.json, back_and_forth/260930_010857_D0113_fable_g7-scale-table-a.md]
last_review: 2026-09-30
-->

# Phase G7 실행 기록 — 요소 크기 (v4.8.0)

지침 D-0101, 결정 D-0111·D-0112·D-0113, D-0104 D2(c)·D6, D-0109. 재기동 20(작업 1~2·D2(c)·D6·D-0109·D-0111·D-0112·§3 1단계·R-0131)과 재기동 21(D-0113 적용~보고) 세션.

## 0. 컨테이너 준비(재기동 21)

phaseG6_5 run_log §0(= G6·G5·G4 §0) 그대로(하위 에이전트). 차이만 적는다.

| 단계 | 결과·주의 |
|---|---|
| pip(requirements·requirements-engine)·apt(ffmpeg 6.1.1·fonts-noto-cjk)·certifi 에 프록시 CA | OK, edge-tts 실호출 확인. pytest-timeout 없음 |
| 자산 복원 | phase7(hormuz)·phase9(랫클리프)·G3(데모)·G4(fed_policy shared + `out/mix.flac`), G5 README 의 AI 연출 기록 복원 |
| fetch_data all·people, hormuz geo.prep 480p·1080p, `media_fetch --res 1080p` | `ok:true`(첫 실행에 끝남). Commons 429 대기 2회 |
| 랫클리프 | 국기 SVG 11개국 curl → `build_flag_pngs` 50, `library_portrait` 3 + `record_rights`, `record_bundles`, geo.prep 480p·1080p |
| **청와대 휘장(새 단계)** | `python -m tools.commons_fetch emblems projects/hormuz_korea --only cheongwadae` — D-0109 에서 생긴 자산이라 앞선 §0 에 없다. 없으면 `test_element_gallery` 가 실패한다(첫 전체 pytest 에서 발견) |
| 지오 자산 대조 | hormuz 21/21(G2)·랫클리프 15/15(480p 8 = G2, 1080p 7 = G1) — `asset_md5.json` |

재기동 20 이 R-0131 을 올린 뒤 컨테이너가 회수됐다. 미커밋 작업은 없다고 보고 D-0113 부터 다시 했다. 자산 복원 중 규칙 값을 WIP 커밋(c392328)으로 먼저 올리고, 전체 pytest 뒤 확정 커밋(e9f73c8)에 기준선을 붙였다.

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·CHANGELOG | 9f6efc3 | docs 테스트 |
| 작업 1 인물 배지 적응 크기 | f9549a2 · 47ef349 | 새 테스트 11, `badge_solo_group.jpg` |
| D2(c) 패널 장면 뱃지 자리 | 24bcc81 | 테스트 |
| 작업 2 기사 카드 조판 | 1d8c4cc · d4162c4 | 새 테스트 7, `article_before_after.jpg` |
| D6 켄 번스 연속 변환 | aec89c5 | 프레임 간 차이 14.6 → 0.41 |
| D-0109 청와대 휘장 | 91e67f1 · 5b9f069 | 테스트 2, 갤러리 36 |
| D-0111·D-0112 R 무시·머리 예약 실측 | 2dd47d1 | hormuz 골든 offscreen hard 3 → 0 |
| §3 1단계 리터럴 → 규칙 | 20bc020 | 골든 25컷 바이트 동일 |
| §3 결정 요청·시트·도구 | 47ef349 · 8ba5504 | R-0131, `scale_before_after.jpg`, `tools/golden_delta_proof.py` |
| 문서(07 §8·08 §12·14) | dafe526 | test_docs_sync |
| **D-0113 A 적용** | c392328(WIP) · e9f73c8 | 1099 passed, hormuz 기준선 24/25 변경 hard 0 |
| 골든 expected_deltas `g7_scale_d0101` + 증명 | 90f1c72 | 1100 passed, `golden_delta/golden_delta.json` |
| 랫클리프·fed_policy·데모 기준선 | 2abfc14 | `regression_baselines.json`, `subtitle_lines.json` |
| 갤러리 36 | d4cfe12 | `gallery.json`·`gallery.jpg` |
| 문서(09 §9·08·docs/07·CHANGELOG·DEVLOG) | 6e10acf | 1100 passed |
| 전편 480p 2편 | artifacts/phaseG7-v4.8.0 35195e9 | §3 |

## 2. 명령

```bash
# 골든 증명 — 기준 = v4.7.0 엔진(4777c50) 렌더(git worktree, 자산·글꼴·data/geo 심볼릭 링크) = G1 기준선 25/25
git worktree add /tmp/wt_old 4777c50
(cd /tmp/wt_old && python -m engine.render projects/hormuz_korea --preview golden \
   && python tools/golden_delta_proof.py boxes projects/hormuz_korea --out boxes_old.json)   # 도구는 새 트리에서 복사
python -m engine.render projects/hormuz_korea --preview golden
python tools/golden_delta_proof.py boxes projects/hormuz_korea --out boxes_new.json
python tools/golden_delta_proof.py prove --ref <옛 prev> --new projects/hormuz_korea/prev \
    --boxes boxes_old.json boxes_new.json --out docs/handoff/reports/phaseG7/golden_delta
# 기준선 — 두 트리에서 같은 시각
python -m engine.render projects/ratcliffe2026 --preview auto          # 20
python -m engine.render projects/fed_policy_2026 --preview auto        # 22
python -m engine.render projects/fed_timeline_demo --preview 6.40,15.70,22.10,26.40,31.50,34.70,40.00,44.50,47.40,53.50,58.00,71.50
python tools/element_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG7/gallery
# 전편 480p
python -m audio.mix projects/fed_policy_2026 && python -m engine.render projects/fed_policy_2026 --jobs 3 && python -m engine.mux projects/fed_policy_2026
python -m audio.mix projects/hormuz_korea && python -m engine.render projects/hormuz_korea --jobs 3 && python -m engine.mux projects/hormuz_korea
```

## 3. 측정

| 항목 | 값 |
|---|---|
| 자막 2줄 수(19 → 21) | hormuz 3 → 15/45, fed_policy 1 → 7/48, 랫클리프 5 → 7/38, 데모 0 → 0/10. 3줄 0 |
| hormuz 골든 25 | 변경 24(25_END 무변경), 변경 픽셀 요소 영역 안 **99.24%**. 밖 4컷: 61.25 캡션 바 38→42 + 도시 라벨 도하 자리바꿈, 65.13 경로 라벨 12.5, 164.59 도시 라벨 하이데라바드 숨김(커진 기사 카드 예약), 170.52 마커 부제 12(화면 왼쪽 끝). checks hard 0 · warning 11(geo_unsourced) |
| 랫클리프 auto 20 | 변경 20(자막만 2), 옛 렌더 = G5 기준선 20/20, hard 0 |
| fed_policy auto 22 | 변경 21(자막만 2), hard 0 · warning 2(media_beats) |
| 데모 12 | 변경 10(자막만 1, 타이틀·엔딩 무변경), 옛 렌더 = G4 기준선 12/12, hard 0 |
| 엔딩 카드 컷 | 랫클리프·fed 엔딩 컷 변경 bbox 는 엔딩 어둠 밑으로 사라지는 카드 — 엔딩 카드 자체 무변경 |
| 갤러리 | 36 = G6.5 35 + 청와대 휘장. 같음 13 · 바뀜 22 |
| 전편 | fed_policy 480p `6920c35d5b4e025147c5e312bcb7af5e` 307.12초, I −14.04 · TP −1.83 · 음악 −12.31. hormuz 480p `9d00319d0651ebeb0b05b90e577fd3ac` 292.44초, I −14.05 · TP −1.72 · 음악 −11.55. 두 편 오디오 QA hard 0(= G6.5 `audio_qa_norm_ref07.json`) |
| pytest | 1100 passed · failed 0 · 262 subtests(재기동 21 새 테스트 1 — g7 골든 등재) |

## 4. 운영 기록

- 새 컨테이너 첫 전체 pytest 2 실패: 청와대 휘장 자산 없음(§0 새 단계로 해결), hormuz 기준선 불일치(규칙 값 적용 뒤 기준선 미갱신 — 확정 커밋에서 재생성).
- `test_golden_frozen.test_kz_cuts_are_intended_deltas` 의 "06_war_1 은 등재하지 않는다"는 KZ 항목 한정 뜻이었다. G7 이 06 을 정당하게 등재해 KZ 항목 한정 검사로 좁혔다(의미 무변경).
- 1080p 전편은 만들지 않았다(재기동 21 지시 — 480p 2편).
