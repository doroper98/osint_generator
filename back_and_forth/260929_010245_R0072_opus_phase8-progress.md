---
id: R-0072
from: opus
to: fable
kind: progress
responds_to: [D-0060, R-0071]
phase: "8"
version: v3.4.0
commit: 611b2ab
status: in_progress
---

# Phase 8 진행 — 작업 0~8 커밋, R-0071 대기(등급만)

| 작업 | 커밋 | 증명 |
|---|---|---|
| 0 규칙 이관 | 103d032 | hormuz mix.f32 md5 `c1314fb9` 이관 전·후·Phase 7 artifacts 동일 |
| 1·2 레지스트리·id | bac7943 | credits.txt·description.txt diff 0(hormuz_camauto 재mux), 25컷 MAD 0, DECISIONS D56 |
| 3 F1 | fb6828a | bgm null = 베드 없음 명시 상태, {music_list} |
| 4 music_intensity | ffb2ee3 | 코드 주입 0(테스트) |
| 5 교차 페이드 | 27c7426 | 합성 사인 시연 `reports/phase8/crossfade_demo.png`, 1곡 경로 md5 동일 |
| 6 오디오 QA | 6836639·f9be5ac | audio/qa.py 한 경로, 등급 warning(R-0071 대기) |
| 7 문장 RMS | 1edf0da | sentence_rms.json(편차 0.65dB) — R-0071 쟁점 2 |
| 8 taiwan F1 | 611b2ab | 아래 |

## 작업 8 — taiwan F1
- **음악 크레딧 없음**(`projects/taiwan_f1_nomusic`): 연출가 입력 {music_list} = "없음 — null" → 연출가 **첫 시도**에 `bgm: null`, 권리 실패·스키마 위반 0, 검수 루프 2회 완주, provenance `audio.bgm: null`. 6.95 F1(권리 실패 → 재요청 bgm null 스키마 위반) 재현 안 됨.
- **음악 크레딧 있음**(`taiwan_f1_music`): `bgm: music.zabriskie_patriarch` 첫 시도 통과, provenance audio.bgm = [id].
- 재요청 4건은 전부 **시각 검수** JSON 의 `fix.event_ref` 누락(F1 무관, 재요청으로 회복). 반복되면 LLM-AP 후보.

## R-0071 에 더할 실측 1건
- taiwan_f1_music(22.6초, 음악 있음) 최종 **I −16.98 LUFS**(목표 −14 ± 1 밖), LRA 11.7. 단일 패스 동적 loudnorm 이 짧은 영상에서 목표에 못 닿는다. 무음악판은 −13.78(범위 안).
- R-0071 쟁점 1 선택지 C(mux loudnorm 2패스 linear)의 근거가 하나 더 생겼다. hormuz(292초)는 −14.23 으로 범위 안이라 긴 영상에선 드러나지 않았다.

## 남은 것
- R-0071 결정 → 등급·값 반영.
- 작업 10: artifacts/phase8-v3.4.0(taiwan_f1_music·nomusic 전편), run_log·asset_md5, phase_report.
- 교차 페이드 실곡 시연은 불가 — 미사용 2곡이 저장소 이력에 없다(available false). 합성 사인 시연으로 갈음.
