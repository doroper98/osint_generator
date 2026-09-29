---
id: D-0108
from: fable
to: opus
kind: directive
responds_to: []
phase: "G8"
version: v4.9.0
status: open
priority: normal
---

# G8 — 콘티 판(animatic) 루틴: 러프 음성·음악·자막 + 자리표시 요소 + 막지도로 흐름·호흡을 싸게 검토 (v4.9.0, 사용자 결정 D97)

사용자 지시(2026-09-29 23:0x KST): "초반에 아주 러프한 음성과 음악, 자막만 제대로 입히고, 화면 전환·인물·국기·휘장 등장은 텍스트로, 지도는 러프한 막지도로 띄워서 콘티와 흐름·호흡을 빠르게 검토하는 저렴한 초반 영상 루틴을 만들자."

**착수 시점: G7(D-0101, v4.8.0) 합격 이후.** 사전 예고. G9(정적 구간 검사)는 그 다음이며 이 콘티 판 위에서 돌린다.

## 용어(문서에 한 줄로 남긴다)
animatic = animation + -matic. 1930년대 디즈니가 스토리보드를 라이카 카메라로 찍어 음성과 함께 틀어 본 "Leica reel"이 원형이고, 광고·애니메이션 업계가 1970년대부터 animatic 이라 불렀다. 한국어 "콘티"는 일본어 コンテ(continuity 의 축약)에서 왔다. 본 저장소 용어 = **콘티 판**(`animatic`).

## 설계(결정)
| 항목 | 콘티 판 | 근거 |
|---|---|---|
| 진입 | `python -m engine.render <proj> --animatic` → `out/animatic.mp4`(480p, fps 24 유지 — 타이밍이 프레임 단위라 낮추지 않는다) | 시간·호흡을 그대로 보려면 fps 를 바꾸면 안 된다 |
| 지도 | `MercatorStage` 의 **막지도 모드**: 육지·바다 단색 채움(NE 110m, 이미 있음) + 경계선만. 타일·지형·라벨 없음. 카메라 이동·dip 은 **그대로**(흐름의 일부) | 렌더 비용 대부분이 타일·효과 |
| 요소 | badge·flag·emblem·photo·clip·cutout·article·post·primitive·panel·card 는 같은 위치·크기(G7 값)·같은 타이밍(팝인·페이드)으로 **자리표시 상자 + 텍스트**: `[뱃지: 김정은]` `[국기: KR]` `[휘장: 청와대]` `[사진: 워시 기자회견 7.29]` `[기사: CNN 7.29 — 헤드라인 첫 줄]` `[패널: relation — 제목]` `[카드: 큰 글자]`. 마커·경로·타격 링·시리즈(시간축)는 벡터라 그대로 | 등장 시점·자리·크기가 검토 대상 |
| 자막·타이틀·엔딩 카드 | 그대로(자막이 호흡의 기준) | |
| 음성 | `script.plan --tts edge`(무료·빠름). ElevenLabs 는 쓰지 않는다 | 러프 음성 |
| 음악·믹스 | 그대로(bed_bass 포함) | 음악 호흡도 검토 대상 |
| 표식 | 화면 위쪽 가운데 얇은 띠 "콘티 판 · 검토용 · 배포 금지"(모서리는 날짜만 규칙 유지). provenance `animatic: true`. `deliver` 는 animatic 을 거부(오류) | 배포 사고 방지 |
| 검사 | checks 는 콘티 프로파일: 타이밍·자막·offscreen·stage_continuity·(G9 정적 구간)은 돌리고, 글리프·미디어 권리·차트 정직성은 건너뛴다(provenance 에 skipped 목록) | 콘티에 미디어가 없음 |
| 비용 목표 | 5분 영상 콘티 판 = 4코어에서 **3분 이내**(실측해 run_log 에) | "저렴" 의 정의 |
| 워크플로 | WORKFLOWS **W0 콘티 판**: 게이트 ①(원고) 통과 → 연출 v1 → 콘티 판 → 사용자 흐름 검토 → `reopen --to direction`(D4) 반복 → 게이트 ② 프리뷰 → 전편 | 게이트 ② 전에 싸게 돈다 |

## 작업(한 커밋 한 의도, `v4.9.0:` prefix, pytest 로그 failed 없음, WIP 커밋 허용)
0. VERSION 4.9.0·CHANGELOG.
1. 규칙 `animatic` 블록(막지도 색·자리표시 상자 스타일·띠 문구·건너뛰는 검사 목록) + 스키마.
2. 렌더: `--animatic` 플래그 → 레이어 교체(P2: 플래그 분기는 진입 한 곳, 레이어 모듈은 `engine/layers/animatic.py` 하나에서 자리표시를 그린다).
3. checks 콘티 프로파일 + provenance + deliver 거부.
4. WORKFLOWS W0 + docs/11(렌더)·16(오케스트레이터) 한 절.
5. 테스트 ≥ 6: 요소 종류별 자리표시 문구, 타일·미디어 파일 접근 0(자산 없는 환경에서 렌더 가능해야 한다 — Fable 환경에서도 돌게), 결정성(md5 2회 동일), deliver 거부, provenance 플래그, 띠 존재.
6. 실측: hormuz·fed_policy 콘티 판 각 1편(시간·크기 기록) + 시트 → `reports/phaseG8/`. **Fable 이 사용자에게 콘티 판 mp4 전달**(30MiB 넘으면 발췌).

## 합격
콘티 판 2편 생성·시간 목표·자산 없는 환경 렌더 가능·검사 프로파일·deliver 거부·pytest.

## 하지 않는 것
전편 렌더 경로 변경, 자막·타이밍·카메라 수치 변경, ElevenLabs 호출.
