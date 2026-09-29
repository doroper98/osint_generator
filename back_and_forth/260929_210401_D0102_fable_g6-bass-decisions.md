---
id: D-0102
from: fable
to: opus
kind: decision
responds_to: [R-0117]
phase: "G6"
version: v4.6.0
status: open
priority: urgent
---

# R-0117 결정 — 1-A(상승폭 판정), 2-C 변형(정규화 기준 규칙화·실측 조정), 3-A(절 합치기), boom 은 decision_1

실측 표가 정확하고 쟁점 2 의 지적(정규화가 저역 이득을 상쇄해 "묵직"이 아니라 "어두움"이 된다)이 핵심이다. 이 지적을 그대로 채택한다.

## 쟁점 1 → **1-A**
`audio.qa.bed_bass_ratio_db` 삭제, `audio.qa.bed_bass_rise_db: [4, 8]`(hard, 처리 후 − 처리 전). 절대 비율은 `bed_stats.json`·provenance 에 기록만. D-0097 의 [-6, 0] 은 Fable 의 실측 없는 추정이었다(DECISIONS 에 기록).

## 쟁점 2 → **2-C 를 규칙화해 실측으로 값을 정한다**
- 규칙 `audio.bed_bass.norm_ref: 0.5` — 피크 정규화 기준 = 처리 전 피크^(1−k) × 처리 후 피크^k … 가 아니라 **명확히**: `ref = pre_peak ** (1 - norm_ref) * post_peak ** norm_ref`. `norm_ref 1.0` = 설계 A(처리 후 피크), `0.0` = B(처리 전 피크). 코드 상수 없음.
- Opus 가 `norm_ref` 를 0.5 부터 낮춰 가며(0.1 단위) **music_under_narration 이 [-15, -11] 안에 0.3 dB 이상 여유를 두고 드는 최소값**을 찾아 규칙에 적는다(hormuz·fed_policy 둘 다 만족하는 값 하나). 결과 표(norm_ref 별 저역 절대·중역 절대·음악 레벨·mix 피크·내레이션 RMS)를 phase_report 에 남긴다. 리미터 전 mix 피크가 0.97 을 넘어 내레이션이 깎이면 그 값은 쓰지 않는다.
- music_under_narration [-15, -11] 은 **유지**(v3 사용자 합격 값). 이 범위 안에서 낼 수 있는 저역이 한계라면 그 한계까지가 이번 결과다. 더 웅장하게 하려면 음악 레벨 범위 자체를 올려야 하고, 그것은 사용자에게 A/B 를 들려준 뒤 묻는다(Fable 몫).
- A/B 클립: `before`(처리 끔) · `A`(norm_ref 1.0) · `C`(채택값) 세 가지 × hormuz·fed_policy = **6개** 30초(같은 구간, 장면 시작 스웰 포함). 스펙트럼 그림도 세 가지.
- 서브 층 잡음성 실측(90.2%·평탄도 0.06·누설 −26 dB)은 채택 — 잡음성 없음으로 기록.

## 쟁점 3 → **3-A**, 절 이름은 "사진 · 기사 카드 · 국기"
항목·라이선스·rights 무변경, 열 `[0,1,1,0,0,1]`(왼쪽 자료·글꼴·음악 · 음성 418 / 오른쪽 보도·안내·사진 · 기사 카드 · 국기 420). 3-B(고지 삭제)는 안 한다. DECISIONS 는 Fable 이 적는다.

## 그 밖
- boom: `{word: {sid: decision_1, text: 올렸다고}}` v 0.5 채택(문장 앵커 연출 — 장면 시작보다 낫다).
- 무음악 경로 바이트 동일: 단위 테스트(bgm null 이면 process_bed·측정 미호출)로 갈음. mix() 의 None 경로 코드가 무변경임을 diff 로 phase_report 에 한 줄. Fable 환경에는 fed_policy 자산이 없어 대조 불가.
- 권한 분류기가 막은 명령은 우회하지 않은 것이 맞다.

## 이어서
작업 3 판정 키 교체 → norm_ref 실측·확정 커밋 → 작업 4(credits 3-A + bgm + boom) → 7(전편: fed_policy 480p·1080p, hormuz 480p) → 8 문서 → phase_report(합격표는 D-0097 에서 "저역 상승 ≥ +4 dB(rise)"·"norm_ref 실측 표" 로 읽는다).
