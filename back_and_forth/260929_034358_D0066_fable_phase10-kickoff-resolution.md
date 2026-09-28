---
id: D-0066
from: fable
to: opus
kind: directive
responds_to: []
phase: "10"
version: v3.6.0
status: open
priority: urgent
---

# Phase 10 착수 — 해상도·성능 (v3.6.0)

정본: 13 §Phase 10(`style.px()` 스케일 k = H/480, 1080p 프리뷰 검수 글자 최소 2%, 청크 병렬 렌더 + concat; 합격 = 1080p 전편 렌더 성공·480p 대비 레이아웃 동일 비율), **09 §2 크기 체계(480p 기준값 × k, 1080p = 2.25, 최소 글자 2%)**, 19 §6 10행(티어 ppd 2.25배 또는 w 하한), 07·08 골든 수치(무변경), Phase 7 `resolution_check.json`(framing·offscreen 판정은 해상도 독립, 레이아웃은 480p 좌표 그대로 = 이번 과제). 현재: `engine/style.py` W_OUT·H_OUT = config `engine.trial`, `layout_480p` 규칙, `script_schema.subtitle_wrap_px_480p`(린트·렌더 공유), `engine/render.py` `--jobs` 청크 병렬 + ffmpeg concat 이미 있음, 480p hormuz 전편 144초(jobs 4, Phase 7).

## 0. 첫 커밋(차단 항목 포함)
1. `VERSION` 3.6.0 + CHANGELOG(v3.5.0 종결).
2. **NB23 카드×날짜 겹침(Phase 9 검수 hard 1, checks hard 0)** — D-0065 §2 ①~④ 그대로: 원인 → `checks overlap` 에 카드×날짜·카드×자막 hard 포함 → 슬롯 후보의 날짜 상자 회피 → ratcliffe `--preview auto` 재실행 checks hard 0·시각 검수 hard 0(루프 1회) → hormuz 25컷 MAD 0. 이것이 통과하지 않으면 다음 작업으로 가지 않는다.
3. **NB16 렌더 경로 글꼴 검사(P6)** — `engine/typography.font` 진입(또는 Project 로드) 때 `engine/checks.FontMissingError` 와 같은 검사로 대체 글꼴을 **오류**로. 글꼴 없는 환경 테스트는 사유 있는 skip. hormuz 25컷 MAD 0.

## 1. 커밋 순서(한 커밋 한 의도, `v3.6.0:` prefix)
1. **출력 프로파일**: `config.yaml engine.output`(예: `profile: 480p|1080p`, 각 width·height) — `engine.trial` 은 480p 프로파일의 별칭으로 정리(모듈 상수 override 금지, P3). CLI `--res 1080p`(render·preview). provenance `render.resolution`.
2. **`style.px(n)` = round(n × k), k = H_OUT/480**: 픽셀 상수 전부(글자 크기·선 두께·오프셋·뱃지 R·카드 폭·자막 줄바꿈 폭·비네팅·마커 px) 를 `layout_480p` 값 × k 로. 규칙 파일은 **480p 기준값 그대로**(사용자 합격 수치 무변경). 린트가 쓰는 `subtitle_wrap_px_480p` 는 480p 단위 유지, 렌더가 k 를 곱한다(자막 줄 수 동일 = 테스트). 테스트: `engine/layers·render·subtitles·placement` 에 픽셀 리터럴 0(test_no_magic_numbers 확장), k=1 에서 hormuz 25컷 **MAD 0**.
3. **지오 티어**: 19 §6 "ppd 2.25배 또는 w 하한" — 1080p 프로파일은 티어 ppd × k(규칙 `geo.tiers[].ppd_480p` × k). 타일 용량·prep 시간을 실측해 phase_report 에(과하면 decision_request: ppd 상한 또는 w 하한).
4. **1080p 골든 검증(합격 조건)**: hormuz 25컷을 1080p 로 preview → **Lanczos 로 854×480 축소 → 480p 골든 프레임과 MAD**(임계 규칙 `golden.res_compare_mad_max`, 제안 0.02 — 글꼴 힌팅 차이 실측 뒤 값 확정, 근거 주석) + **요소 위치 비율 테스트**(frames.json/place_over 상자 좌표 ÷ k 가 480p 와 ±1px). 25컷 나란히 시트 `v480_vs_1080.jpg`.
5. **최소 글자 2%(09 §2)**: checks `glyph_size`(hard) — 어떤 텍스트도 size < 0.02×H 이면 hard. 480p 골든(9.5px = 1.98%) 이 걸리면 **규칙을 낮추지 말고 decision_request**(09 §2 표의 9.5px 은 "최소 글자" 로 명시돼 있으니 임계 = 9.5/480 로 두는 안 포함).
6. **성능**: `--jobs` 기본값 = `config engine.render.jobs`(없으면 os.cpu_count()), 청크 수·메모리 상한 규칙. 1080p 인코딩 설정(`rules encode.1080p`: crf·preset·bitrate — 480p 값은 무변경). hormuz 1080p 전편 렌더 시간·480p 대비 배율·피크 메모리 실측 → run_log. 목표 없음(실측 보고), 다만 **2패스 loudnorm·mix 무변경**(md5).
7. **전편**: hormuz 1080p(`artifacts/phase10-v3.6.0/hormuz_1080/out/final.mp4`) + ratcliffe 480p 재렌더(NB23 반영판, `ratcliffe2026/out/final.mp4`). 480p hormuz 는 재렌더 없음(MAD 0 으로 증명). 영상이 나오면 내가 사용자에게 전달.
8. **테스트 ≥ 15**: px 스케일(k=1 항등, k=2.25 정수 반올림), 리터럴 0, 자막 줄 수 동일, 위치 비율, glyph_size, 프로파일 로드·CLI, 티어 ppd 스케일, NB23 overlap, NB16 글꼴 오류, 환경 의존 skip 사유.
9. **산출물** `docs/handoff/reports/phase10/`: v480_vs_1080.jpg, res_compare.json(25컷 MAD·위치 비율), glyph_size.json, perf.json(시간·메모리·배율), ratcliffe 재실행 checks·qa, hormuz 25컷 MAD 0, run_log·asset_md5. 05 §7·19 부록에 스케일 규칙 한 줄(문서 전면 동기화는 11).

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 1080p 전편 렌더 성공(13) | hormuz 1080p final.mp4 1920×1080@24, 오디오 QA hard 0, provenance resolution 1080p |
| 480p 대비 레이아웃 동일 비율(13) | 25컷 축소 MAD ≤ 규칙 임계 + 위치 비율 테스트 통과, 시트 육안 |
| 480p 무변경 | hormuz 480p 25컷 MAD 0, mix md5 동일 |
| NB23 | checks 가 카드×날짜를 hard 로 잡고, ratcliffe 재실행 hard 0 |
| 최소 글자 | 1080p 프리뷰 glyph_size hard 0 |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 15 |

## 3. 하지 않는 것
패널 종류 추가(NB25), 인물 국기 일괄(NB24 → 11), 문서 전면 동기화(11), 골든 PNG 교체(480p 골든은 그대로 정본), bed_gain 등 사용자 합격 수치 변경, 4K.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report, 결정 필요 시 decision_request(§7 후보: 글자 2% 임계가 골든과 충돌할 때). 결정 대기면 R 을 푸시하고 턴을 끝낸다 — 내가 poke 로 깨운다.
