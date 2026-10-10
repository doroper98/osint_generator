---
id: R-0191
from: opus
to: fable
kind: phase_report
responds_to: [D-0153, D-0156]
phase: "Q0"
version: v5.13.0
commit: c68fa6c
status: done
---

# Phase Q0 완료 — 유료 TTS 차단·지도 테마 시제품·cascade 단절 재현 (v5.13.0)

상세는 `docs/handoff/reports/phaseQ0/run_log.md` 입니다. **지도 테마 결정(사용자)이 필요합니다.**

## 1. 변경 요약(커밋)

| 커밋 | 내용 |
|---|---|
| `ebfed99` | VERSION 5.13.0·헤더·CHANGELOG, 00_INDEX 23·19 §3 |
| `81ef603` | Q0-1 `elevenlabs.require_allowed()` 한 곳 — plan·`eleven_one`·`tts_align_probe` 가 요청·키·폴더 전에 호출, 테스트 6 |
| `3d86d6c` | Q0-2 `rules geo.themes`(dark = v3 값, light = 가이드 §13·§15), `geo.prep --theme`, `stage_config.mercator.theme`, 지도 색 토큰, 테스트 9, 시트 2 |
| `c68fa6c` | Q0-3 cascade 단절 재현 crop |
| run_log 커밋 | phaseQ0 run_log |

## 2. 합격 조건 대조(D-0153 §3)

| 조건 | 결과 |
|---|---|
| 테스트 통과 | 전체 **1430 passed · failed 0 · skip 0**(1415 + 15) |
| 시트 2장 | `hormuz_light_sheet.jpg`, `hormuz_dark_vs_light.jpg` |
| 골든 무변경(dark) | 25컷 md5 = phaseG17 기준선(`test_provenance_e2e`). 지형 티어 18장(k 1·1.5) 옛/새 코드 md5 동일 |
| 유료 호출 0 테스트 | 세 경로 `requests.post` 0회 |

## 3. 지도 테마 — 사용자 결정 요청

- 시트 2장은 생성해 저장소에 커밋했습니다(이 세션의 사용자 화면에도 띄웠습니다).
- 선택지: (a) light 를 기본으로(Q3 = dark 삭제·골든 재등재), (b) dark 유지(Q3 = light 경로 삭제 + 선 위계만 dark 에 적용).
- light 시제품에서 보인 Q3 과제 5가지는 run_log §2.4 에 있습니다. 핵심 둘:
  - 국경 글로우(청록)가 밝은 바탕에서 국경을 푸르게 만듭니다.
  - 해안선이 국경과 같은 짙은 선입니다(국가 폴리곤 고리 전체를 긋기 때문, 가이드 §14).

## 4. cascade 단절(Q0-3)

현 코드, 8항목 데모, t = 5.8초입니다. 아래끝 '발표' 140.52·'협의' 135.52 로 가이드 §6 값과 같습니다. `draw_frame` 에 걸린 세로 클립 때문에 하단선이 x 90 에서 끊깁니다. `cascade_asis_clip.png` 가 Q1 전/후 기준입니다.

## 5. 판단 기록(되돌릴 수 있는 선택)

1. 과장을 `[2.7, 1.7]`(설계 ppd < 64, 이상)로 뒀습니다. dark 의 두 값 구조, 가이드 §13 "2.7→1.7" 을 따랐습니다.
2. light 행정선은 실선(§15)입니다. dark 대시는 그대로입니다.
3. light 해안 광채는 세기 0 입니다.
4. `colors.sea_label` 을 테마 토큰으로 옮기고 옛 키를 지웠습니다(읽는 곳 하나, P2).
5. 테마 이름은 dark·light 두 필드로 고정했습니다. Q3 에서 하나를 지웁니다.

## 6. 자산(§20)

받음: 가이드, 목업 시트 3장(cascade V2·인물 국기·우크라이나 v4). mp4 원본은 저장소에 없습니다.
받지 못함: F-35 SVG·빌더(**Q5 착수 조건**), render harness 스크립트, 지도 데이터(OCHA·KOSTAT·OSM·NE 강 — 도로·강·ADM2 레이어 조건). 표는 run_log §4 입니다.

## 7. 다음

D-0154 §5 순서대로 **Q1(v5.14.0) cascade V2** 의 지시를 기다립니다. Q1 은 지도 테마 결정과 독립입니다.
