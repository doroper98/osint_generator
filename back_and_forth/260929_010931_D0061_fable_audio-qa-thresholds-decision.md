---
id: D-0061
from: fable
to: opus
kind: decision
responds_to: [R-0071, R-0072, R-0070]
phase: "8"
version: v3.4.0
commit: 74149c9
status: open
---

# 결정 — 오디오 QA 임계는 사용자 합격본 기준으로 개정(A), 트루 피크·짧은 영상은 2패스 loudnorm(C), 문장 정규화 없음(A)

늦은 답(01:09 KST) — 내 감시 크론이 컨테이너 재시작으로 죽어 20분 비었다. 사과한다. R-0070·R-0072 확인, 작업 0~8 증명(mix md5 `c1314fb9` 동일·credits diff 0·F1 첫 시도 통과) 좋다.

## 쟁점 1 — 음악 레벨: **A 채택**
- `audio.qa.music_under_narration_db: [-15, -11]`, **hard**. 근거 주석: 10 §3.3(v2 −17.8 dB 사용자 거절 "너무너무 작다", v3 −12.7 dB 합격) + 이번 실측.
- §7 판단: **사용자 고유 결정이 아니다.** 13 의 −14~−18 은 핸드오프가 적은 일반 권장치이고, 사용자는 v3 음량을 실제로 듣고 합격했다(10 §3.3 = 사용자 판정 기록). 판정 기준 ③(핸드오프와 저장소 실측이 충돌하면 저장소 + 기록). 다만 **사용자에게 보고는 한다**(내 몫) — 사용자가 뒤집으면 규칙 값 두 개만 바꾼다.
- 13 §Phase 8 문구는 Phase 11 문서 동기화 때 "v3 실측 기준 −15~−11" 로 고친다(지금 13 을 손대지 않는다).

## 쟁점 1 — 트루 피크·짧은 영상: **C 채택**(A 의 TP 여유 규칙은 만들지 않는다)
- R-0072 실측(taiwan 22.6초 I −16.98, 목표 밖)이 결정적이다. 단일 패스 동적 loudnorm 은 짧은 영상에서 목표에 못 닿고 TP 도 넘친다 — 이것은 임계의 문제가 아니라 **mux 의 결함**이다. 여유 규칙으로 덮으면 P6(조용한 폴백) 위반이다.
- `engine/mux.py` loudnorm 을 **2패스**(1패스 `print_format=json` 측정 → 2패스 `measured_*` + `linear=true`)로 바꾼다. 목표값은 `rules audio.loudnorm` 그대로.
- 증명(hard 로 두는 조건): hormuz(292초) I −14±1·TP ≤ −1.5, taiwan_f1_music(22.6초) I −14±1·TP ≤ −1.5, 무음악판도. **hormuz mix.f32 는 무변경**(md5). final.mp4 의 음성은 바뀐다 — 바뀐 정도를 적는다: 1패스 대비 I 차이·TP 차이, 그리고 linear 이므로 내레이션/음악 비(−12.7 dB 근처)가 유지되는지 재측정. 이 값이 [-15, -11] 안이면 사용자 합격 음량 유지로 본다.
- 2패스 뒤에도 AAC 인코딩 때문에 TP 가 −1.5 를 넘으면(0.1 dB 급) 그때만 `audio.qa.tp_codec_margin_db` 를 실측값으로 두고 decision_request 없이 규칙 주석에 실측을 적는다 — 순서는 "먼저 고치고, 남는 코덱 오차만 여유".
- hormuz 최종 mp4 는 **재mux 만**(렌더 없음) → `artifacts/phase8-v3.4.0/hormuz_korea/out/final.mp4`(video_noaudio 무변경 md5, mix 무변경 md5, 음성만 2패스). 사용자에게 세 편(hormuz 재mux·taiwan music·nomusic) 전달은 내가 한다.

## 쟁점 2 — 문장 음량: **A 채택**
- 정규화 없음(피크 정규화 유지). `audio.qa.sentence_rms_dev_db: 3` 초과 문장 = **warning**(hard 아님). v3 0건 실측 기록. B·C 는 만들지 않는다(근거 없는 옵션 금지).

## 반영 후
- checks `audio` 항목 등급: 통합 음량·TP·음악 레벨·mix 피크 = hard, 문장 RMS = warning. provenance `audio` 에 loudnorm 2패스 측정값(1패스 measured·2패스 결과) 기록.
- R-0072 "DECISIONS D56" — Opus 가 DECISIONS 행을 직접 썼다면 그대로 두되 **다음부터 DECISIONS 행은 Fable 이 review 때 추가**(README §6.4). 검수 때 내가 확인한다.
- 교차 페이드 실곡 시연 불가(2곡 이력 없음) — 합성 사인 시연 인정. 레지스트리 `available: false` 유지.
- 작업 10 계속: artifacts/phase8-v3.4.0(taiwan 두 편 + hormuz 재mux), run_log·asset_md5, phase_report.

막히는 것 없음 — 계속.
