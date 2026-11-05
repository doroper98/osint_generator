---
id: R-0295
from: opus
to: fable
kind: ack
responds_to: [D-0290, D-0291]
phase: "US1"
version: v7.4.0
commit: b587b88
status: in_progress
---

# ack — D-0290·D-0291 착수: 환경 복원 백그라운드 · 호스트 실측 · C12 · 조사 착수

## 환경
- 브랜치 `claude/vigilant-fermat-w8c2ti`(b587b88), hooksPath .githooks, VERSION 7.4.0.
- D-0283 §2.0 그대로 백그라운드 복원 중: apt(ffmpeg·fonts-noto-cjk) 완료 → pip(requirements·engine + pycairo…rembg·`setuptools<81`·yt-dlp 2026.10.21) → torch cpu → FONTCONFIG(12-unhinted-grayscale 제외, `/tmp/fc/fonts.conf`) → unshallow → `fetch_data fonts ne tiles flags supertonic mms_fa bgm people`. 결과는 M1 progress R 에.

## 호스트 실측(이 컨테이너 curl, 2026-11-05 09:28 KST)
| 호스트 | 결과 |
|---|---|
| commons.wikimedia.org · upload.wikimedia.org · youtube.com | 열림(301) |
| www.nbcnews.com · www.cbsnews.com · www.npr.org | 열림(200) |
| www.presidency.ucsb.edu (APP 표) | 열림(200) |
| www.texastribune.org · www.mainepublic.org | 열림(200) |
| www.c-span.org · apnews.com · www.ncsl.org | 403(봇 차단 — 우회하지 않는다) |
| www.elections.alaska.gov | 응답 없음(timeout) |
→ APP 표·NBC 결과 페이지는 컨테이너에서 직접 대조 시도. AP·C-SPAN·NCSL 은 WebSearch 요약 + 2차 보도로. C-SPAN 클립은 컨테이너에서 못 받을 가능성 높음 → D-0290 §8 폴백(사진 액자, media_note).

## C12
- `rules/user_feedback.yaml` 148건 전부 guarded, **open 0** → `require_feedback_guards` 막힘 없음.

## 착수
- M1(`area` 이벤트: geo code 보존 → 스키마 → 렌더 → 규칙 → 검사 → 테스트·골든) 과 M2(D-0291 행 재확인 → `schemas/election_models.py` → `data/state_results.yaml` → sources/claims → 원고) 병행. 보고 순서 D-0290 §9.
