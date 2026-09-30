<!--
tier: 3
last_synced_with: v4.11.0
ssot_for: [phaseG10-run-log]
depends_on: [rules/video_rules.yaml, engine/pacing.py, tools/norm_ref_sweep.py, tools/golden_delta_proof.py, back_and_forth/260930_084925_D0118_fable_g10-pacing-music-size-g11-goal-g4.md]
last_review: 2026-09-30
-->

# Phase G10 실행 기록 — 정적 구간·음악 상한·글자 크기 2차 표 (v4.11.0)

지침 D-0118(사용자 위임 D103). 재기동 24 세션.

## 0. 컨테이너 준비

phaseG7 run_log §0 그대로(하위 에이전트). 차이만 적는다.
- artifacts/phaseG8·G7 브랜치에 `shared` 가 없다 → G7 §0 이 가리키는 원 출처(phase7 hormuz, phase9 랫클리프, G3 데모, G4 fed_policy + G5 AI 연출 기록)로 복원.
- certifi 에 프록시 CA 가 "이미 있다"고 건너뛰었는데 edge-tts TLS 가 실패 → 무조건 덧붙여 해결.
- 지오 자산 hormuz 21/21·랫클리프 15/15(G7 `asset_md5.json`), 청와대 휘장 `513c0785…`, fed `mix.f32` `0b664780…`(= G7) 일치.

## 1. 작업과 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·헤더·CHANGELOG | 0d19adc | docs 테스트 |
| §1 정적 구간·creep·변화 사다리 | 6a1af05 | 새 테스트 10, 골든 창 0 → hormuz 25컷 기준선 바이트 동일 |
| §2 음악 상한 [-13, -9]·norm_ref 0.4 | 44f799a | `norm_ref_sweep.jsonl`, 새 테스트 2 |
| §3 자막 22·카드 line 16 | 26b9d9a · 24bd727 | `golden_delta/`, `hormuz_baseline.json`, `regression_baselines.json`, `subtitle_lines.json`, `scale_before_after.jpg`, 새 테스트 4 |
| 전편 480p 두 편·A/B 4 | artifacts/phaseG10-v4.11.0 548a63b | §3 |

## 2. 명령

```bash
python tools/norm_ref_sweep.py projects/hormuz_korea hormuz 0.7 0.6 0.5 0.4 0.3 0.2 0.1 0.0     # fed 도 같게
# 골든 증명 — 전 = §2 커밋(44f799a) 렌더(규칙 값 적용 전, 같은 트리)
python -m engine.render projects/hormuz_korea --preview golden && python tools/golden_delta_proof.py boxes projects/hormuz_korea --out boxes_old.json
#   (규칙 §3 적용 뒤 같은 두 명령 → boxes_new.json)
python tools/golden_delta_proof.py prove --ref <전 prev> --new <후 prev> --boxes boxes_old.json boxes_new.json --out docs/handoff/reports/phaseG10/golden_delta
# 전편 + A/B(음성만 교체)
python -m audio.mix P && python -m engine.render P --jobs 3 && python -m engine.mux P       # after
# before = v4.10.0 mix.f32·bed_stats.json 을 out/ 에 두고 engine.mux 만 다시 → final_before
ffmpeg -ss 40 -i final_{before,after}.mp4 -t 30 -c:v libx264 -crf 20 -c:a aac -b:a 192k ab_hormuz_*_30s.mp4   # fed 는 -ss 15
```

## 3. 측정

### 3.1 정적 구간(§1)

| 프로젝트 | 45초 이상 지도 구간 | 창 | 45초 창 최소 변화 |
|---|---|---|---|
| hormuz(골든) | 없음(최장 26.2–69.3 = 43.1초, 패널·카드로 끊김) | 0 | — |
| 랫클리프(골든) | 34.2–76.3, 127.2–214.6 | 0 | 9(137.8–183.1) |
| fed_policy | 시간축 무대(지도 없음) | 0 | — |
| 데모 | 시간축 무대 | 0 | — |

creep 0 → expected_deltas `g10_pacing_d0118` 불필요. §1·§2 뒤 렌더 = G7 기준선: hormuz 25/25·랫클리프 20/20·fed 22/22·데모 12/12.

### 3.2 음악 상한(§2) — `audio_qa_g10.json`

| 영상 | 음악(내레이션 구간) | I LUFS | TP dBTP | 베드 저역 상승 | hard |
|---|---|---|---|---|---|
| hormuz before(v4.10.0) | −11.55 | −14.05 | −1.72 | +5.35 | 0 |
| hormuz after | **−9.83** | −14.06 | −1.58 | +5.35 | 0 |
| fed before(v4.10.0) | −12.31 | −14.04 | −1.83 | +5.34 | 0 |
| fed after | **−10.57** | −14.07 | −1.65 | +5.34 | 0 |

TP 한도 −1.5 + 0.15 = −1.35 안(리미터가 잡음) → decision_request 없음. norm_ref 스윕: 0.3 은 hormuz −9.26(여유 0.3 밖), 0.4 가 최소.

### 3.3 글자 크기(§3)

| 항목 | 값 |
|---|---|
| 2줄 자막(21 → 22) | hormuz 15 → 17/45, fed 7 → 11/48, 랫클리프 7 → 10/38, 데모 0 → 0/10. 3줄 0 |
| 카드 넘침 | 0 — 최대 폭 fed 436px(x ≥ 394), 아래 끝 ≤ 204 |
| hormuz 골든 | 23컷 변경(02_TITLE·25_END 무변경), 요소 영역 안 100 %, checks hard 0 · warning 3(geo_unsourced) |
| 랫클리프 auto 20 | 18 변경(자막만 10), hard 0 |
| fed auto 22 | 20 변경(자막만 13), hard 0 |
| 데모 12 | 10 변경(전부 자막만), hard 0 |

### 3.4 전편

| 영상 | md5 | 길이 | 렌더 벽시계(jobs 3) | checks(프리뷰) |
|---|---|---|---|---|
| fed_policy 480p | `b818566c6bba830193cbff190dbde0b1` | 307.12초 | 88초 | hard 0 · warning 2(media_beats) |
| hormuz 480p | `ec33e813b48e42385fd786d94bb30eb0` | 292.44초 | 172초 | hard 0 · warning 3(geo_unsourced) |

A/B 클립 md5: hormuz before `72bd6aad…`·after `180fab33…`, fed before `2939e596…`·after `af7b34ed…`(각 30.00초).

## 4. 판단 기록(되돌릴 수 있는 선택)

| 쟁점 | 선택 | 근거 |
|---|---|---|
| 지도 구간 | 숏 무대 mercator, 전면 카드(±0.3초)·패널 덮개 밖 | 패널이 덮는 동안은 "같은 지도 뷰"가 아니다 |
| 강조·하이라이트 | country·boom | tanker_loop·ships·barrier 는 지속 애니메이션(등장 순간이 아님) |
| 창 격자 | 시작 0.1초 격자, 닫힌 구간, 겹친 창 병합(changes = 최소) | 결정적·단순, 경계 테스트 |
| creep 중 이동 | 이동 중엔 없음, 이동 끝부터 다시 누적 | 이동이 줄어든 w 에서 출발 → 끊김 없음 |
| A/B 영상 | before·after 같은 v4.11.0 영상, 음성만 교체 | 청감 판정이 화면 변화(§3)에 흔들리지 않게 |
| norm_ref 도구 | `tools/norm_ref_sweep.py` 로 저장소에 | G6 스윕은 /tmp 스크립트라 재현 불가였다 |

## 5. 테스트

전체 pytest 1149 passed · failed 0 · 262 subtests(기준선 1133 + 새 16: g10_static_window 10·music_ceiling 2·scale 4). 삭제 0. 기대값 갱신: 검사 항목 수 22 → 23(3곳), WARN 집합, provenance e2e 기준선 phaseG7 → phaseG10.
