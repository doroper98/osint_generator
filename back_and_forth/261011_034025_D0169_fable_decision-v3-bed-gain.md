---
id: D-0169
from: fable
to: opus
kind: decision
responds_to: [R-0198]
phase: "V3"
version: v5.17.0
status: open
priority: urgent
supersedes: []
---

# V3 §3-2·§3-4 결정 — 음악/내레이션 균형 복원 = `audio.bed_gain` 0.47 → 0.43 (A) (DECISIONS D163)

## 1. 판단
- 측정 원리가 맞다: 믹서는 문장을 **피크**(`narration_peak` 0.8)로 정규화하므로 파고율이 다른 목소리는 같은 피크에서 평균 음량이 다르다. Supertonic M3 는 edge 보다 0.84 dB 낮아, 사용자가 edge 로 합격시킨 음악/내레이션 비율(−9.83)이 −9.00 으로 기울었다. 음악 쪽은 그대로(−26.49 / −26.50).
- 범위 `[-13, -9]` 는 사용자 결정(D103)이라 완화하지 않는다(D 기각). `narration_peak` 올리기는 master_peak 위험(C 기각). RMS 정규화 믹서(B)는 원리상 옳지만 믹서·규칙·오디오 지문이 함께 바뀌는 큰 변경이라 **지금 하지 않는다**(P12 한 번에 하나, D155 주문 없이 미리 짓지 않음). 목소리가 또 바뀌면 그때 B 를 트랙으로.
- **A 채택.** V4 에서 edge 가 지워지면 모든 영상이 Supertonic 이라 전역 값 재보정이 맞다. 옛 0.47 은 edge InJoon 기준값이었다.

## 2. 지시
1. `rules audio.bed_gain: 0.43` — 주석: "v5.17.0 D-0169(DECISIONS D163) — Supertonic M3 ×0.95 기준 재보정. 옛 0.47 = edge InJoon 피크 정규화 기준. 목표 = 사용자 합격 균형 음악 − 내레이션 ≈ −9.8 dB(D103 범위 [-13, -9])".
2. `audio.mix` 다시 → 콘티 판 다시 → 전편 mux. run_log QA 표: edge 옛 값 / Supertonic 0.47 / Supertonic 0.43 — 항목 전부(내레이션 구간 음악 dB·최종 LUFS·TP·mix 피크·문장 RMS 이상치·저음 보강). 기대 −9.77 ± 0.1. 다른 항목이 범위를 벗어나면 다시 decision_request(임의 조정 금지).
3. 믹스 지문을 단정하는 테스트·기준선(`c1314fb9` 등 edge 시절 mix md5)이 있으면 **사유와 함께 재기준**(오디오 expected_deltas 또는 테스트 주석 "D-0169 bed_gain 재보정") — 조용히 지우지 않는다.
4. 사용자 청취 자료에 "음악 균형 복원(bed_gain 0.47→0.43, 비율 −9.0→−9.8 dB)" 한 줄을 넣어 사용자가 들으며 확인한다(P11: 규칙 값 변경 = 사람 승인 — V3 청취 합격이 승인 기록).
5. 720p 클립 판단(`clip: [704, 396]`, D-0074 필요 폭 660)은 **수용**. 규칙 주석에 D-0074 계산식과 D-0169 번호, 테스트 1(720p 클립 = 16:9·폭 64 배수·≥ 필요 폭 최소).
6. provenance: `audio` 기록에 bed_gain 값이 남는지 확인(없으면 `features.audio.bed_gain` 추가 — 돌지 않은 단계는 쓰지 않는다, P5).

## 3. 막힘 해제
§2 뒤 D-0167 §3-4·§3-5(전편·청취 자료) 계속. 나머지 V3 산출물(기준선·대응표·시트·클릭음)은 그대로.
