<!--
tier: 3
last_synced_with: v4.9.0
ssot_for: [phaseG8-run-log]
depends_on: [rules/video_rules.yaml, engine/layers/animatic.py, back_and_forth/260929_230617_D0108_fable_animatic-routine.md]
last_review: 2026-09-30
-->

# Phase G8 실행 기록 — 콘티 판(animatic) 루틴 (v4.9.0)

지침 D-0108(사용자 결정 D97), 착수 D-0114. 재기동 22 세션. 결정 요청 R-0135(막지도 자료, 권고 A 로 진행 — 답 대기).

## 0. 컨테이너 준비

phaseG7 run_log §0 그대로(하위 에이전트, 청와대 휘장 단계 포함). 지오 자산 hormuz 21/21·랫클리프 15/15(G7 `asset_md5.json`).
fed_policy `out/mix.f32` 는 처음에 mix.flac 을 풀어 만들었다가 `python -m audio.mix` 로 다시 계산했다 → md5 `0b664780…` = G7.

## 1. 작업과 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION·동기화 | 3f98761 | docs 테스트 |
| 1 규칙·스키마·막지도 자료 | fe04592 | `rules animatic`, `data/geo_flat/ne_110m_countries.json`(157KB, 177국 + 크림 고리) |
| 2 렌더 `--animatic` | 6fec425 | 진입 `load_project(animatic=True)` 한 곳, `render_frame` 은 `P.layers` 만 봄 |
| 3 provenance·deliver 거부 | d2f0fbd | `AnimaticDeliverError`, provenance `animatic` |
| 4 문서 | 1294977 | WORKFLOWS W0, handoff 11 §9·16 §7 |
| 5 테스트 10 | ea2dee0 | 1110 passed(= 1100 + 10), failed 0 |
| 6 실측 2편 | artifacts/phaseG8-v4.9.0 4f66348 | §3 |

## 2. 명령

```bash
python -m audio.mix projects/fed_policy_2026 && python -m engine.render projects/fed_policy_2026 --animatic --jobs 4
python -m engine.render projects/hormuz_korea --animatic --jobs 4          # 2회(결정성)
python -m engine.render projects/{fed_policy_2026,hormuz_korea} --animatic --preview auto   # 시트
# 자산 없는 폴더: git 추적 파일 + plan.json + out/mix.f32 만 /tmp 로 복사 → 같은 명령
```

## 3. 측정(4코어, 다른 작업 없이 단독)

| 영상 | 길이 | 벽시계 | 렌더 | 음성(2패스 loudnorm+AAC) | 크기 | md5 | checks |
|---|---|---|---|---|---|---|---|
| fed_policy 콘티 판 | 307.12초 | **124.4초** | 72.1초 | 43.1초 | 17.1MB | `bfb93d18…` | hard 0 · warning 2 · skipped 9 |
| hormuz 콘티 판 | 292.44초 | **117.9초 · 118.7초** | 67.7초 | 42.6초 | 17.7MB | `c5c8fb2e…` 3회 동일 | hard 0 · warning 11(geo_unsourced) · skipped 9 |
| hormuz, 자산 없는 폴더 | 292.44초 | 111초 | 62.8초 | 40.5초 | — | `1175f426…` | images_used [] |

- 목표 = 5분 영상 4코어 3분(`rules animatic.cost_target_sec_per_300s` 180). 300초 환산 fed 121.5초·hormuz 121.0초 — 목표 안.
- 시간의 약 3분의 1 이 음성 단계(loudnorm 2패스)다. 전편과 같은 음량 절차를 지키려고 줄이지 않았다.
- 자산 없는 폴더 영상은 7018프레임 중 엔딩 카드 구간(281.9~292.1초) 245프레임만 다르다. 권리 레지스트리(생성 자산)가 없어 크레딧 auto 절이 빈다.
- 자리표시 수 — fed: card 34·article 2·badge 2·photo 2·primitive 2·panel 1, hormuz: badge 8·card 7·panel 5·article 2·clip 2·photo 2·cutout 1.
- 시트: `hormuz_animatic_sheet.jpg`(24컷)·`fed_policy_animatic_sheet.jpg`(22컷).

## 4. 판단 기록(되돌릴 수 있는 선택)

| 쟁점 | 선택 | 근거 |
|---|---|---|
| 막지도 자료 | 저장소 추적 NE 110m(R-0135 A, 결정 대기) | D-0108 "이미 있음" 이 실측과 다름 |
| 컷아웃 높이 | 폭 × `cutout_h_ratio` 0.4 | 레지스트리에 비율 없음(p8 실측 0.37), 파일을 열지 않기 위해 |
| 초상 머리 예약 | 상한(reserve_top_factor) | 초상 실측은 파일을 열어야 함. 가장자리 보정 위치가 전편과 몇 px 다를 수 있다 |
| checks hard | 렌더 전 실패 | 프리뷰 게이트와 같은 규칙(P6) |
| 권리 레지스트리 없음 | 엔딩 카드 license_ref 자리에 `animatic.missing_license` | 전편은 RightsError 그대로 |
| 오케스트레이터 | 상태·engine_service 무변경 | W0 는 direction 안의 사람 루프, 16 §7 |
