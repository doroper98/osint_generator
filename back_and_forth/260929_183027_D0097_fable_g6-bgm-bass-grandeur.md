---
id: D-0097
from: fable
to: opus
kind: directive
responds_to: []
phase: "G6"
version: v4.6.0
status: open
priority: normal
---

# G6 — 배경음악 저음 보강·웅장한 베드 (v4.6.0, 사용자 결정 D86)

사용자 지시(2026-09-29 18:2x KST): "배경음악에 베이스를 좀 더 풍부하게 넣어서 좀 웅장한 느낌이 드는 배경음악이 깔리도록 해."
사용자 결정이므로 v3 합격 mix(md5 c1314fb9)는 **바뀌어도 된다**(README §7.2 예외 — 근거 = 사용자 지시, 되돌리는 방법 = 해당 커밋 revert). DECISIONS D86 은 Fable 이 기록했다.

**착수 시점: G5(D-0096) phase_report 제출 → Fable 합격 D 이후.** 그 전에는 G5 만 한다. 이 D 는 사전 예고이며 G5 보고 전 ack 불필요.

## 배경(저장소 실측)
- 쓸 수 있는 곡은 `music.zabriskie_patriarch` 하나(피아노 앰비언트, 조성·BPM 미실측). 새 곡 도입은 권리·파일이 없어 **범위 밖**(사용자가 곡을 주면 별도 D).
- 베드 처리는 `audio/mix.py bed()/segment_bed()` → 피크 정규화 → `bed_gain 0.47 × intensity × 덕킹`. 저역 장치는 없다.
- `projects/fed_policy_2026` 는 `sound.bgm: null`(무음악) 이었다. 사용자가 들은 영상에 음악이 없었던 셈이다.
- v1 절차 합성(10 §6: 서브 베이스 근음 사인 + 2·3배음, 킥 스윕)은 폐기됐지만 설계는 참고 가능. 단 **조성을 모르는 곡에 고정 근음 드론을 깔지 않는다**(불협 위험, 추측 금지).

## 설계(결정 — 되돌릴 수 있는 쪽)
저음 보강은 **곡을 따라가는 처리 두 가지**로 한다. 값은 전부 `rules audio.bed_bass` 에, 코드 상수 0(P3).

1. **로우 셸프 EQ**(`shelf: {freq_hz: 110, gain_db: 5.0, q: 0.7}`) — scipy biquad(`scipy.signal` 계수, `lfilter`) 로 베드 저역을 올린다. 정규화 **전**에 적용.
2. **서브 옥타브 층**(`sub: {band_hz: [55, 220], out_lp_hz: 110, gain: 0.35, env_attack_sec: 0.03, env_release_sec: 0.25}`) — 베드 모노합을 밴드패스 → 영교차 2분주(부호 토글, 벡터화) → 로우패스 → 원 대역 포락선(attack/release) 곱 → gain → 양 채널에 더한다. 곡의 실제 저음 한 옥타브 아래를 만들므로 조성을 몰라도 맞는다.
3. **장면 시작 스웰**(`swell: {sec: 2.5, depth: 0.35}`) — 첫 장면 제외, 장면 시작 시각에서 서브 층 이득이 `1+depth` 로 올랐다가 `sec` 동안 1 로 내려온다(선형·결정적). 타이틀 카드 boom 은 그대로.
4. 처리 순서: 디코드 → (교체 베드는 곡마다) 셸프 → 서브 층 합산 → 피크 정규화(기존) → bed_gain·intensity·덕킹(기존, 값 불변). 내레이션·효과음 경로는 손대지 않는다.
5. 초기값은 위 숫자로 시작하되 **합격표의 실측 범위에 들도록 Opus 가 조정**하고 조정 근거를 rules 주석과 phase_report 에 남긴다. `bed_gain 0.47`·`duck_depth 0.5` 는 그대로(test_user_approved_bed_values_unchanged 유지).

## 작업(한 커밋 한 의도, `v4.6.0:` prefix, 커밋 전 전체 pytest 로그에 failed 없음)
0. VERSION 4.6.0·CHANGELOG(v4.5.0 종결).
1. 규칙 `audio.bed_bass` 블록 + `audio.qa.bed_bass_ratio_db: [-6, 0]`(아래 측정 정의) + Pydantic 모델(extra forbid).
2. `audio/mix.py`: `process_bed(bg, scene_starts)` 신설, `bed()`·`segment_bed()` 양쪽이 통과. 무음악(`bgm null`) 경로는 **바이트 동일**(test_audio_f1 통과, F1 mix md5 무변경).
3. `audio/qa.py`: 베드 저역 비율 검사 신설 — 처리 후 베드(내레이션 제외, 믹서가 `out/bed_stats.json` 에 기록)의 30–120 Hz 대역 RMS − 200–2000 Hz 대역 RMS(dB). 처리 전 값도 함께 기록해 **상승폭**을 남긴다. 범위 밖 = hard 실패. 기존 검사(I·TP·music_under_narration·문장 RMS)는 그대로 통과해야 한다.
4. `projects/fed_policy_2026/direction.yaml`: `sound.bgm: music.zabriskie_patriarch`(intensity 곡선은 이미 있음) + `decision` 장면 시작(금리 인상 결정 문장)에 `boom` 큐 v 0.5(hormuz war_0 과 같은 방식). hormuz 는 연출 무변경.
5. provenance: `audio.bed_bass` 에 적용 값·측정치 기록(P5). 안 돈 단계는 기록하지 않는다.
6. 테스트 ≥ 6: 규칙 리터럴 0 · 백색잡음에 셸프 → 저역 상승 ≥ gain_db−1 dB · 110 Hz 사인 → 55 Hz 성분이 최대 피크 · 스웰 시각·길이 · QA 범위 밖 hard 실패 · 무음악 경로 바이트 동일.
7. 회귀·산출물 `reports/phaseG6/`: hormuz·fed_policy 각각 처리 전/후 `bed_stats` 표, 30초 A/B 클립 4개(`ab_{hormuz,fed}_{before,after}_30s.m4a`, 내레이션 포함 실제 믹스 구간 — 장면 시작 스웰이 든 구간으로), 스펙트럼 그림 1장(전/후, 30–2000 Hz 대역 RMS 막대면 충분). **전편 재렌더**: fed_policy 480p·1080p(mix+mux) → artifacts `phaseG6-v4.6.0`; hormuz 는 mix·QA 재실행 + 새 mix md5 기록(전편 재렌더는 480p 만). 골든 PNG 25/25 무변경(오디오만 바뀜).
8. 문서: handoff 10 에 "v4.6.0 저음 보강" 절(측정 정의 포함), docs/10(요약본) 한 줄, CHANGELOG·DEVLOG. GOAL·CLAUDE.md 무변경.

## 합격
| 조건 | 검증 |
|---|---|
| 저역 상승 | hormuz·fed_policy 베드 저역 비율 처리 후 − 처리 전 ≥ +4 dB, 결과 [-6, 0] dB 안 |
| 기존 QA 유지 | I −14±1 · TP 여유 · music_under_narration [-15, -11] · 문장 RMS 경고 0(hormuz) |
| 내레이션 불변 | 내레이션 구간 내레이션 스템 RMS 변화 ≤ 0.3 dB(마스터 피크 스케일러가 내레이션을 깎으면 sub.gain 을 낮춘다) |
| 무음악 불변 | F1 mix 바이트 동일 |
| 영상 | fed_policy 480p·1080p·hormuz 480p 새 md5, A/B 클립 4개 — Fable 이 사용자에게 전달, **청감 판정은 사용자** |
| pytest | 로그에 failed 없음, 새 ≥ 6 |

## decision_request 로 올릴 것
- 저역 목표를 맞추면 music_under_narration 이 범위를 벗어나는 경우(bed_gain 은 못 바꾸므로 sub.gain·shelf 로 못 맞추면 보고).
- 서브 2분주가 곡의 화음 구간에서 잡음성(밴드 안 여러 음)으로 측정되면(포락선 대비 고조파 왜곡 수치로 보고) — 대안 = 셸프만.

## 하지 않는 것
새 곡·절차 합성 음악 도입, 고정 근음 드론, 내레이션·효과음 처리 변경, bed_gain·duck 값 변경, 골든 PNG 교체, GOAL·CLAUDE.md 변경.
