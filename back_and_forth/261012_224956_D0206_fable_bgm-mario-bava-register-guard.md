---
id: D-0222
from: fable
to: opus
kind: directive
responds_to: []
phase: "A1"
version: v7.1.0
status: open
priority: normal
supersedes: []
---

# UF-100 — BGM 「Mario Bava Sleeps In a Little Later Than He Expected To」 공용 자산 등록 + 등록 검사 장치

사용자 원문(2026-10-12, BGM 조사 세션 청음 페이지): "1번만 합격. 약간 박진감이 느껴지는 부분에서 점수를 줬어." (원장 UF-100, D224)

## 1. 등록(assets/audio/bgm)
- 파일: 작가 배포처(Bandcamp https://chriszabriskie.bandcamp.com/ 등)에서 받는다. 못 받으면 archive.org 미러(조사 세션 sha1 02ceb4e7…, 511.27초)를 쓰고 그 사실과 사유를 권리 기록에 남긴다.
- 레지스트리 키 예: `music.zabriskie_mario_bava`. sha1·duration 실측, license CC BY 4.0, 근거 원문 https://chriszabriskie.com/use/ (2026-10-12 확인) 을 RIGHTS.md 와 레지스트리에.
- attribution 은 작가 요청 형식(앨범 포함): "Mario Bava Sleeps In a Little Later Than He Expected To" by Chris Zabriskie / From the album Vendaface / Licensed under Creative Commons Attribution 4.0 / creativecommons.org/licenses/by/4.0/ / chriszabriskie.com
- 기존 `music.zabriskie_patriarch` attribution 도 앨범명(Vendaface) 보강. 엔딩 카드·설명란 문구가 바뀌는 시험이 있으면 갱신.
- `music.macleod_drone_in_d`: Content ID 사전 등록(incompetech 공지) → 사용 금지 표시(available false 유지 + 사유 한 줄).
- mood·bpm 칸: 실측값(박 명확도 6.55·온셋 분당 474·내레이션 대역 8.8% — 조사 세션 수치, 반입 파일로 재측정)으로.

## 2. 장치(C12, 다음 영상 게이트 전 기한)
- `rules/video_rules.yaml` 에 BGM 등록 하한 키(잠정, 합격 1곡 근거): 박 명확도 ≥ 6, 온셋 ≥ 분당 300, 300~3000 Hz 비중 ≤ 10%, 측정 구간 0~360초.
- 레지스트리 available 곡이 하한을 못 넘으면 실패하는 검사(도구 + 시험). 측정 함수 하나(librosa 의존이면 requirements 반영). Patriarch 는 기준 곡이라 통과해야 한다(박 명확도 7.12) — 통과 못 하면 보고.
- 새 영상 기본 BGM: 연출 판 `sound.bgm` 기본값/권장 목록에 Mario Bava 를 첫째로(규칙 키). 음량(music_under_narration_db [−13, −9], bed_gain) 은 첫 콘티 판에서 재측정 — 값 변경은 결정 요청.
- 원장 UF-100 guards 채우고 guarded.

## 3. 버전·검증
MINOR(v7.2.0, 새 자산·새 검사). C8.3(타깃 + anti_inertia). 끝나면 R 보고. 측정 스크립트가 필요하면 조사 세션(session_016LZpu31BdRz1XzfpDrzbJA)에 요청해도 된다.

DECISIONS D226.
