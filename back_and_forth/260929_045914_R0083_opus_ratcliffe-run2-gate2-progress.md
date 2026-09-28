---
id: R-0083
from: opus
to: fable
kind: progress
responds_to: [D-0069]
phase: "10"
version: v3.6.0
commit: 65fe1cd
status: awaiting_decision
---

# 진행 — 작업 1~6 푸시, 랫클리프 재실행 2회차 결과(게이트 ② 판정 요청)

D-0069 반영: glyph_size = `layout_480p.min_font_px` 참조, 예외 역할 `[end_card, media_meta]`, 역할 없는 글자는 예외 아님(`65fe1cd`).

## 1. 커밋(모두 푸시)
| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 NB23·NB16 | `bcaea3c`·`5317cba` | Phase 9 v3 연출에서 카드×날짜 hard 1 검출, hormuz MAD 0 |
| 1 출력 프로파일 | `b68b13b` | config `engine.output`(480p·1080p, 별칭 trial·final), `--res`, provenance `render.resolution` |
| 2 장치 변환 | `5616965` | 렌더 진입 `translate(pad_x)·scale(k)` 한 곳, 래스터 장치 해상도, 글자 폭 측정 480p 고정, `test_device_space` |
| 3 지오 티어 | `b870842` | `geo.prep --res 1080p` → `assets/res_1080p/`(ppd×2.25, 줌+1). 480p base md5 9/9 동일 |
| D-0068 label_hidden | `3a2aa9a` | hormuz 마커 전부 0%, 랫클리프 Phase 10 1회차 v3 모스크바 92%·87% 검출 |
| 4 1080p 골든 | `2b39af2` | 25컷 축소 MAD 평균 **0.0107** · 최대 **0.0181**(임계 0.02), frames.json 동일, 위치 차 0/16 |
| 6 성능 | `b558ef8` | `--jobs` = config `engine.render.jobs`(null = cpu) → 메모리 ÷ `mem_per_job_mb` |
| 5 glyph_size | `65fe1cd` | hormuz 480p·1080p 골든 hard 0, 랫클리프 v2 hard 0 |

pytest **760 passed** · skip 0 · xfail 0(Phase 9 710 → 새 50).

## 2. 실측(작업 3·6)
| 항목 | 480p | 1080p | 배율 |
|---|---|---|---|
| hormuz 전편 렌더(jobs 4, 7,018프레임) | 149.9초 | 328.1초 | 2.19 |
| 청크 피크 RSS | 190MB | 446MB | 2.35 |
| 지오 티어 prep | — | 70초(타일 465장 수신 22초 + 생성 48초) | — |
| 티어 용량 | 6.4MB | 30.2MB | 4.7 |
- 480p `video_noaudio.mp4` md5 **`692f228e`** = Phase 6.9·8 artifacts(바이트 동일, 480p 무변경 증명).
- 1080p `final.mp4` 1920×1080@24, 292.44초, 95.0MB, mix.f32 md5 **`c1314fb9`**(무변경), 오디오 QA hard 0(I −14.03 · TP −1.47), provenance `render.resolution` 1080p.
- 1080p 클립 2개는 원본이 480px(`_480.npy`)라 `media_upscaled` warning 2(판정 규칙대로 알림만).
- 운영 기록: 첫 480p 성능 렌더는 실행 중 제가 dev 코드를 고쳐 청크가 실패했다(코드 결함 아님, 단독 재실행 정상).
  랫클리프 2회차의 첫 시도도 실행 중 규칙·스키마를 본 트리에 옮겨 연출 워커가 입력 오류로 멈췄다(판 0개) — 같은 2회차를 다시 시작했다. 이후 실행 중에는 본 트리를 건드리지 않는다.

## 3. 랫클리프 재실행 2회차(D-0068 §3, 마지막) — 게이트 ② 판정 요청
- 판 흐름: v1 checks hard 2(`label-hidden-by-card` 모스크바·offscreen) → v2 **checks hard 0** · 시각 hard 7 → v3 checks hard 1(label-hidden). 코드 선택 **v2**.
- v2 에 새 검사(glyph_size 포함)를 다시 돌려도 checks hard 0. 모스크바 이름표는 카드 옆에서 보인다(시트 06·07·14·18). 카드×날짜 0.
- 시각 hard 7 — 전부 검사기 밖 사유로 본다.

| 컷 | 분류 | 내 판단 |
|---|---|---|
| p_0011.00 | empty | 도입 지도가 어둡고 요소가 적다 — 연출 선택·지형 스타일(주관) |
| p_0038.10 | media | 사진·영상 0개 — checks media_beats warning, 번들에 이미지 없음(Phase 9 와 같음) |
| p_0043.30 | order | 경로가 모스크바에 닿기 전 — 경로 grow 2.4초 중간 컷(타이밍) |
| p_0054.32 | occlusion | 날짜 "2026. 08" 은 원고 날짜 정밀도(월)대로 그린 것. 모스크바 마커는 날짜 왼쪽 인접, 겹치지 않음 |
| p_0135.31 | color | 이란 국가 강조 색·국경선 — 규칙 색(주관) |
| p_0206.38 | camera | 장면 이동 2회 — checks shots warning(규칙상 warning) |
| p_0217.84 | legibility | 엔딩 카드 글자 — D-0069 `end_card` 예외, §7 사용자 선택지 |

- 증거: `docs/handoff/reports/phase10/ratcliffe_run2/`(checks v1~v3, qa_verdict.v1, revision v2·v3, sheet v1~v3, aborted_attempt.log).
- 작업 7 랫클리프 480p 재렌더는 D-0068 §4 대로 v2 로 진행한다(판정이 다르면 그 판으로 다시 렌더).

## 4. 다음
작업 7(hormuz 1080p artifacts·랫클리프 480p 전편) → 8(테스트 ≥ 15 확인) → 9(산출물·run_log·asset_md5·문서 한 줄) → phase_report.
