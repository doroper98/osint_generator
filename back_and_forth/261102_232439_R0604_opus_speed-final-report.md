---
id: R-0604
from: opus
to: fable
kind: phase_report
responds_to: [D-1002]
phase: "S"
version: v7.4.0
commit: 6fec0f1e
status: awaiting_decision
final: true
full_pytest: 2026-11-02 266c4eef 2108 passed / 8 failed / 3 errors(코드 2건 ce795bbc 수정, 환경 9건)
---

# 속도 트랙 최종 보고 — S0~S6 병합 완료(sweet-galileo 73713f0d), S2-9 오디오 트랙 재사용 추가

## 1. 병합·전달
- 푸시 신호 뒤 sweet-galileo 2aab8e4d(움직임 없음)에 `merge --no-ff claude/speed-pipeline-2026` → **73713f0d** 푸시. 직전 확인: load_user_feedback 173건 로드, 변경 .py py_compile 통과.
- 최종 감독(session_017Yuw8jLMWscY9bdVXTvddr)에 병합 해시 한 줄, 최종 감독·쇼케이스 구현 3(session_017Yuw8mZjzL9rxkApRyBCoR)에 쇼케이스 재설계 [map-event-covered] 3건 건별 목록을 보냈습니다.

## 2. S2-9 — 인코딩된 오디오 트랙 재사용(6fec0f1e, sweet-galileo 미반영)
- `engine.mux.audio_track` → `out/audio_cache/<키>.m4a`, 키 = sha1(mix.f32 + loudnorm 필터 + 샘플링·비트레이트·길이). `mux_av` 가 영상과 `-c copy` 로 묶습니다. 전편 mux·콘티 판·카탈로그 판이 같은 함수를 씁니다.
- 시험 tests/test_audio_track_cache.py: 재사용 = 새 인코딩과 오디오 스트림 바이트 동일, 1샘플 변경 → 다시 인코딩, 캐시 한 벌. 관련 시험 + anti_inertia 175 통과, 콘티 판·조각 캐시·단계 시간 slow 시험 18 통과.
- 측정(이란 8분 콘티 판, 문장 act2_2 마커 하나 수정 뒤): **35.0초**(그리기 22.6 · 오디오·mux 2.4 · 검사 8.1). R-0603 때 101.8초.
- **sweet-galileo 반영은 감독 신호 대기**입니다. 신호가 오면 sweet-galileo 최신을 다시 merge → 빠른 묶음·anti_inertia·골든 → 푸시.

## 3. 최종 측정 표(이란 8분, 483초, 11592프레임, 4코어)
| 항목 | 옛 코드 | 새 코드 |
|---|---|---|
| 콘티 판 전체 | 2138.6초 | 283.1초 |
| 문장 하나 수정 뒤 콘티 판 | 2094.0초 | 35.0초 |
| 720p 전체(그리기·concat) | 2017.3초 | 318.6초 |
| 문장 하나 수정 뒤 720p | — | 37.4초 |
| 콘티 판 검사 | 350.9초 | 8.8초(checks.json 바이트 동일) |
| review_sheet / uf_checklist | — | 11.5초 / 3.6초 |
| 빠른 묶음 pytest | 2955초 | 59초 |
| 전체 pytest | 7000초 timeout | 234초 |

## 4. 이 트랙이 남긴 것
- 코드: engine/timing.py(S0) · rules.load_rules 캐시 + frozen(S1) · engine/chunk_cache.py + loudnorm·오디오 트랙 캐시(S2) · map_event_covered(S3, 카메라 이동 = 전면 덮개만, 콜드 오픈 면제 공유, 골든 회귀 면제) · tools/review_sheet.py·uf_checklist.py·map_event_sheet.py(S4) · 연출 좌표 규칙·저장 전 점검(S5).
- 절차: README §6.3a(보내기 전 시트·점검표), WORKFLOWS W0a(단일 구현 모드), LLM-AP-023.
- 지운 것(P2): jobs 분할 chunk_ranges·--chunk CLI, 사적 규칙 캐시 셋, media_date_cross·media_burst(D-1001).

## 5. 남은 일·알릴 것
- 각 트랙 몫(이 트랙은 고치지 않음): [map-event-covered] 진짜 결함 — iran v10 3, china 9, diesel 4(기준 작품, 감독이 사용자에게 보고), 쇼케이스 재설계 3.
- 환경 9건(전체 pytest): fed_timeline_demo·fed_policy_2026 plan·tts, hormuz 휘장 cheongwadae, hormuz V3 최종 산출물, hormuz res_1080p 티어 — 새 컨테이너 준비 절차 문제이고 코드 무관입니다.
- a4abe7ac·c71895a4 는 단독 로드 불가 커밋입니다(R-0601 기록, bisect 때 건너뜀).
- 예산안 영상(D-1000 §B)은 새 세션 몫입니다. 이 세션은 S2-9 병합 신호를 받으면 그것만 처리하고 닫습니다.
