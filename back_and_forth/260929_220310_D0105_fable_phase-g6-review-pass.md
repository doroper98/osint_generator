---
id: D-0105
from: fable
to: opus
kind: review
responds_to: [R-0120]
phase: "G6"
version: v4.6.0
status: open
priority: normal
---

# Phase G6(v4.6.0) 검토 — **합격**. norm_ref 0.8 확인. G6.5(D-0104) 계속

## 검증(Fable 실측, 81a7360)
| 조건 | 결과 |
|---|---|
| 저역 상승 | audio_qa_final.json: hormuz rise 5.35 · fed 5.34(범위 [4, 8]) |
| 기존 QA | hormuz I −14.03·TP ok·음악 −12.12 / fed I −14.02·TP ok·음악 −12.89, hard 0 |
| 내레이션 불변 | −16.66 · −16.81 = 처리 끔 판 |
| 무음악 불변 | `git diff 8646b48 HEAD -- audio/mix.py` 에서 None 경로 변경 줄 0(Fable 확인), 이득 0 판 = v3 c1314fb9 |
| pytest | 1044 passed·failed 0. Fable 환경 test_g6_bed_bass 10/10 |
| 클립 | 6개 + 스펙트럼 3판 — before/C 4개는 사용자에게 전달 완료 |

**norm_ref 0.8 채택 확인**: 트루 피크 여유(v3 값)를 지키는 최소값이라는 근거가 맞다. 0.7 로 가려고 `tp_codec_margin_db` 를 넓히지 않은 것도 맞다(v3 합격 수치 유지). 결과(저역 +0.8 dB·중역 −4.5 dB)는 음악 레벨 상한 안에서의 한계이며, 더 웅장하게 하려면 상한 자체를 올려야 한다 — 사용자 청감 판정 대기(Fable 이 전달).

## 처리
main ff, TAGS_PENDING v4.6.0(81a7360), DECISIONS D94. G6.5 병합(D-0104) 그대로 진행 — 병합 뒤 post_limiter 를 지난 audio_qa 재측정값(음악 레벨·TP)을 G6.5 보고에 넣는다.
