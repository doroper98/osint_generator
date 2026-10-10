---
id: D-0159
from: fable
to: opus
kind: directive
responds_to: [R-0192]
phase: "Q2"
version: v5.15.0
status: open
priority: urgent
supersedes: [D-0153 §5 링 값]
---

# Q2 보강 — 사용자 지시(2026-10-10, DECISIONS D152): 링 두께 유지 · 이재명 정수리 잘림 수정 · 이재명 사진 교체(권리 제약 → 후보 시트)

## 1. 사용자 지시 3건
| # | 지시 | 적용 |
|---|---|---|
| 1 | **테두리 선 두께는 이전과 동일** | 가이드 §10 의 링 `2.4/.8` 을 **적용하지 않는다**. 현재 값 바깥 `3.2`·안쪽 `1.5`(`badges.py:236·239` 리터럴) 유지. Q2 의 리터럴 → 규칙 키 이관은 **같은 값**으로(`badge.ring_outer_w: 3.2`, `badge.ring_inner_w: 1.5`). 얼굴 분리 shadow alpha `.16` 은 가이드대로 |
| 2 | **이재명 얼굴 일부(정수리) 잘림 수정** | Fable 실측: 골든 01컷(solo R56) 에서 머리 윗부분이 원 위쪽에서 잘린다. 사진 폭 2.04R·alpha-top −.83R 적용 뒤에도 **정수리가 원 안에 여유를 두고 들어오는 것**을 규칙으로: `head_inside_max` 가 정수리(alpha>20 최상단) 기준으로 작동하는지 확인하고, 4명(이재명·하메네이·노무현·트럼프) × R56·R30 에서 정수리·턱·어깨 잘림 0 을 테스트(마스크 bbox 가 원 안). 잘림이 있으면 사진을 내리는 것이 아니라 **확대율을 줄이는 쪽**(머리 크기 우선 규칙 키) |
| 3 | **이재명 사진을 정부 대표 대통령 사진으로 교체** | 아래 §2 권리 판정 때문에 정부 공식 초상은 쓸 수 없다. **허용 후보 3장으로 뱃지 후보 시트**를 만들어 사용자가 고른다(P12) |

## 2. 권리 판정(Fable 조사, 2026-10-10)
| 후보 | 출처·라이선스 | 판정 |
|---|---|---|
| 청와대 president.go.kr 사진 갤러리 | 저작권정책: **공공누리 제4유형**(출처표시·비상업·변경 금지) | **불가** — 흑백·컷아웃 가공 = 변경, 영상은 상업 이용 가능성. C9 |
| Commons `File:Lee Jae-myung's Portrait (2025.6.4).jpg`(KOCIS Flickr "Republic of Korea") | CC BY-SA 2.0 + 정부 고지 "보도·공공 목적만, 변경·재판매 금지" | **불가** — 07 §3.2 BY-SA 불허(`license_allowed`) + 변경 금지 고지 |
| Commons `File:Official portrait Lee Jae-myung.jpg` | 제작자 "경기도 뉴스포털・Gemini", 제한 personality·ai | **불가** — AI 생성(G4-10) |
| **A** `File:Lee Jae Myung portrait.jpg` | 백악관 촬영(2025-10-29 경주), **Public domain(US Gov)**, 1280×1794, Commons 사용자가 크롭·리터치(처리 이력 기록 필요) | 허용 |
| **B** `File:Lee Jae-myung 20250823.jpg` | 일본 내각관방 내각홍보실, **CC BY 4.0** | 허용 |
| **C** `File:Lee Jae-myung and Bongbong Marcos in Manila (2026) 07 (cropped).jpg` | 필리핀 대통령 공보실, Public domain | 허용(단체 사진 크롭) |
판정은 `tools/commons_fetch.py search` 의 `allowed` 와 일치. 정부 공식 초상 사용은 **사용자 고유 결정 사항**(C9 예외)이지만, 변경 금지 조건 때문에 예외를 두어도 가공 파이프라인과 맞지 않는다 — 사용자에게 보고함.

## 3. Q2 추가 작업(D-0158 Q2 지시에 더함)
1. 후보 A·B·C 를 `tools/commons_fetch.py get`(960px) → `tools/portrait_fallback.py`(rembg·mono·정규화) → 뱃지 R56·R30 으로 렌더한 **후보 시트** `reports/phaseQ2/lee_candidates_sheet.png`(현재 사진 포함 4열, 480p 실크기 + 4배 crop). 사용자 선택 뒤 `python tools/asset_library.py promote`(C8.7) 로 `assets/library/people/lee_jae_myung_mono_v02.png` + 권리 기록(원본 URL·저자·날짜·sha256·라이선스·처리 이력: rembg 모델·blur·mono). 선택 전에는 현재 사진 유지.
2. 현재 이재명 사진(`projects/hormuz_korea/assets/portraits/lee_jae_myung.png`, v3 Commons + rembg)은 `library_manifest`·`rights_bundles` 에 기록이 없다 — 19a §408 의 `rights_registry.json` 형식을 찾아 run_log 에 출처·라이선스를 적고, 없으면 "출처 기록 누락(v3)" 로 RIGHTS-AP 1건 append.
3. 골든: 사진 교체 컷은 사용자 선택 뒤 `expected_deltas q2_portrait_flag_d148` 에 함께 등재(사유 "사용자 지시 사진 교체").

## 4. 순서
Q2 본작업(96 strip·2.04R·크롭 수정, 링 유지) → 후보 시트 → phase_report(시트 포함). 사용자 선택은 Fable 이 받아 D 로 전달.
