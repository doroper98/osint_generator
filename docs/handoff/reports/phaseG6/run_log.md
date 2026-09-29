<!--
tier: 3
last_synced_with: v4.6.0
ssot_for: [phaseG6-run-log]
depends_on: [audio/mix.py, audio/qa.py, engine/mux.py, rules/video_rules.yaml, projects/fed_policy_2026/direction.yaml, projects/fed_policy_2026/credits.yaml]
last_review: 2026-09-29
-->

# Phase G6 실행 기록 — 배경음악 저음 보강 (v4.6.0)

지침 D-0097(사용자 결정 D86), 결정 D-0102, 종료 지시 D-0103. 시각은 KST. 재기동 18 세션.

## 0. 컨테이너 준비

phaseG5 run_log §0 그대로(하위 에이전트). 차이: `fetch_data bgm` sha1 c0ddb7b3… 일치, 랫클리프 1080p geo 도 만듦(phaseG1 15/15 대조). HEAD(WIP 코드 포함) pytest 1043 passed.

## 1. 측정 정의와 결과

- 베드 저역 비율 = 베드(내레이션·효과음 제외) 모노 30–120 Hz RMS − 200–2000 Hz RMS(dB, rfft 파워). 믹서가 처리 전·후를 `out/bed_stats.json` 에 쓴다.
- 원곡(931초) 대역: 30–60 −23.8 · 60–120 −15.4 · 120–200 −27.0 · 200–500 −24.4 · 500–1000 −28.6 · 1000–2000 −36.4 dB. 처리 전 비율 +11.8 dB → D-0097 절대 범위 [−6, 0] 폐기, 상승폭 판정(D-0102 1-A).

| norm_ref | hormuz 저역·중역 절대(dB) | hormuz 음악 레벨 | hormuz 최종 TP | fed 음악 레벨 |
|---|---|---|---|---|
| 처리 끔 | −13.62 · −25.39 | −12.67 | −1.47 | −13.35 |
| 0.5 | −11.04 · −28.17 | −10.41 ✗ | — | −11.15 ✗(여유) |
| 0.6 | −11.62 · −28.76 | −10.98 ✗ | — | −11.73 |
| 0.7 | −12.21 · −29.34 | −11.55 | −1.34 ✗ | −12.31 |
| **0.8(채택)** | **−12.80 · −29.93** | **−12.12** | **−1.40** | **−12.89** |
| 0.9 | −13.38 · −30.51 | −12.69 | −1.40 | −13.47 |
| 1.0 | −13.97 · −31.10 | −13.26 | −1.47 | −14.04 |

- 상승폭 hormuz +5.35·fed +5.34(norm_ref 와 무관 — 정규화는 비율을 바꾸지 않는다). 리미터 전 mix 피크 ≤ 0.93, 내레이션 RMS 변화 0.
- 서브 층 잡음성: 에너지 90.2% 가 원곡 대역 피크 8개 절반 주파수 ±2 Hz, 평탄도 0.06(원 대역 0.023), 110 Hz 위 누설 −26.3 dB.
- 최종(`audio_qa_final.json`): hormuz I −14.03·TP −1.40·음악 −12.12·문장 RMS 경고 0, fed I −14.02·TP −1.42·음악 −12.89. hard 0.

## 2. 명령

```bash
python -m audio.mix projects/hormuz_korea            # out/mix.f32 + out/bed_stats.json
python /tmp/…/sweep.py <proj> <tag> 0.5 … 1.0       # norm_ref 만 바꿔 mix() 를 메모리에서(프로젝트 out/ 에 쓰지 않음)
python /tmp/…/tpcheck.py <total> <mix.f32…>          # mux 와 같은 2패스 loudnorm + AAC 로 최종 TP
```

## 3. 운영 기록

- 옛 코드(8646b48 worktree)로 fed_policy 무음악 mix 를 다시 만들어 바이트 대조하려던 명령은 권한 분류기가 막았다. 우회하지 않았다. D-0102 가 단위 테스트(bgm null 이면 process_bed·측정 미호출)로 갈음했다. 대신 "이득 0" 판이 v3 합격본 c1314fb9 와 같음을 두 번(norm_ref 1.0·0.8 코드) 확인했다.
- norm_ref 0.7(음악 레벨 조건만) 로 hormuz 480p 를 mux 하자 트루 피크 −1.34 > −1.35 로 hard 실패했다. 오디오 경로 재현으로 0.8 을 골랐다(코덱 여유 v3 값 유지).
- 전편 재렌더는 사용자 지시(D-0103)로 중단했다. fed 480p(0.7 믹스, md5 ca86d8e2)·hormuz 480p 산출물과 1080p 렌더 조각은 지웠다.
- 1080p 렌더가 `out/video_noaudio.mp4` 를 480p 판 위에 덮어쓴다(출력 이름 하나). 다음에 두 해상도를 연달아 돌릴 때 주의.
