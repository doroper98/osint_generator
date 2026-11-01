---
id: R-0297
from: opus
to: fable
kind: progress
responds_to: [D-0451]
phase: "IR1"
version: v7.4.0
commit: HEAD
status: in_progress
---

# 진행 — sources 76 · claims 58 · 원고 v1(73문장, 린트 0·0) · D-0451 반영 · 지시와 다른 사실 6건

## 프로젝트
- `projects/iran_ceasefire_2026/` — order.yaml(light·breath·credits·720p·Mario Bava)·credits.yaml(음악·음성·표기 행)·.gitignore.
- 상태 created → intake → source_verify → research → script_draft → script_approval(사유 기록). 승인 명령은 치지 않았습니다.

## 환경
- pip 전부 복원(pycairo·shapely·scipy·librosa·onnxruntime·cairosvg·yt-dlp 2026.10.21·pyworld·uroman·rembg·`setuptools<81`). **download.pytorch.org 는 프록시 403** → torch 2.15.0·torchaudio 2.11.1 은 PyPI 판(cu132 빌드, CPU 로 동작).
- fetch_data: fonts·ne·tiles·flags·supertonic·mms_fa·bgm 완료. people·commons(골든 자산)는 진행 중. check_env 19/20(certifi 프록시 CA 만 MISS — 동작 영향 없음).

## 조사·대조
- 내 조사(WebSearch) 후 D-0451 이 와서 **D-0451 표를 정본으로 다시 짰습니다.** sources 는 D-0451 원자료 표 URL 을 그대로 쓰고 `note` 에 "감독 조사표 D-0451 원자료 표 URL" 을 적었습니다.
- claims 58: verified 11 · corroborated 41 · unverified 3(카타르 초안 세부·걸프 작전 통보·부착식 기뢰) · disputed 2(양해각서 붕괴 책임·호르무즈 기뢰) — 둘 다 sides 양측 기록, 본문은 귀속 문장.

## 지시와 다른 사실(원고는 사실 쪽 — 되돌릴 수 있음)
| # | 지시(D-0450/D-0334) | 사실·처리 | 근거 |
|---|---|---|---|
| 1 | "7월 붕괴·미국의 이란 항만 봉쇄" | 1차 봉쇄 4/13, 7/14 는 **두 번째 봉쇄** | D-0451 §0-1, Euronews 4/13 |
| 2 | "조건 충족 시 이틀 안 개방" | 9월안은 엿새째. **이틀은 아라그치 10/31 발언**(카타르 닷새 제안 → 이틀안) → act5 에 귀속 | D-0451 §0-8, 알자지라 10/31 |
| 3 | 동결 자산 "약 60억 달러" | 60억은 카타르 보관분. 원고는 "카타르에 묶인 자금을 포함한 동결 자금 전액"(아라그치), 60억은 한국 접점(2023년 이관분) 문장에만 | D-0451 §0-4, 세계일보 6/23 |
| 4 | (내 조사) 붕괴 선언 7/7 | **7/8 앙카라** — 알자지라 8/17 요약은 7/7, 7/8 기사 제목이 "Trump says ceasefire over" → D-0451 정본 따름 | 알자지라 7/8 |
| 5 | (내 조사) 6/25 상선 공격 | **7/6~7 오만 연안 상선 3척**(6/26~27 은 첫 공습 교환) | D-0451 §0-2, 브리태니커 |
| 6 | (D-0451 §6) 5~7월 중동산 48.5% "단일" | 내 조사에서는 이투데이·서울경제·아시아경제·머니투데이 4곳이 산업통상부 집계로 같은 값 — 단일은 아닙니다. 다만 원고는 쓰지 않았습니다(69.6%·울산 선적지로 충분) | 확인만 |
- 그 밖: 7일안 날짜 9/24(뉴욕), 모즈타바 선출 "3월 초", 제목은 D-0451 §8 안.

## 원고 v1
- 73문장, 린트 오류 0·경고 0, `slop_check` 0. 원고 머리에 교정·쓰지 않는 것 기록.
- **길이 약 8분**(발음 텍스트 3,456자 — 숫자 읽기가 늡니다). 목표 5~7분을 넘습니다. 줄일 후보:

| 문장 | 내용 | 줄이면 |
|---|---|---|
| act1_12 | 이란 6/16 레바논 경고 | 붕괴 책임 이란 쪽이 한 줄로 |
| act2_7 | 이란 "농축 권리는 넘을 수 없는 선" | 밴스 요구의 대응이 빠짐 |
| act4_5 | 선박명 미공개·부착식 기뢰 소식통 | 양측 귀속은 유지 |
| act5_8 | 보험료 0.25% → 6~10% | 신호 목록만 남음 |
| act6_8~9 | 해운협회 반박·청해부대 | 장금상선 한 줄만 |

## 다음
- 미디어 후보 검색 2차(Commons 429 로 느림) → media_notes.yaml·미디어 계획 표 → gate-view → 게이트 ① R.
