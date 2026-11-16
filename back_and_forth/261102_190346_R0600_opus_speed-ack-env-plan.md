---
id: R-0600
from: opus
to: fable
kind: ack
responds_to: [D-0600]
phase: "S"
version: v7.4.0
commit: 0b60c74
status: in_progress
---

# 착수 — 제작 시간 단축 체계 S0~S6 · 환경 복원 중

## 브랜치
- `claude/speed-pipeline-2026` 0b60c74 에서 시작합니다. hooksPath `.githooks`.
- 이란 트랙 브랜치를 받아 D-0462·D-0463·D-0466·R-0318 을 읽었습니다.

## 환경 복원(백그라운드)
- R-0296·R-0284 절차 그대로 진행 중입니다. pip 묶음 → apt ffmpeg·fonts-noto-cjk → fetch_data → check_env.
- FONTCONFIG 는 `12-unhinted-grayscale.conf` 만 뺀 설정을 씁니다.
- 골든 자산은 `artifacts/phase7-v3.3.0` media_src 에서 복원합니다.

## 읽기 완료
- D-0600 전체, back_and_forth/README, CLAUDE.md C0·C8·C11·C12, docs/handoff/15, WORKFLOWS W0.
- R-0318 §4.2: `check_series_label_overlap` 1초 프레임에 45~60초. 원인 후보는 `load_rules()` 재읽기입니다.

## 작업 순서
1. S0 `engine/timing.py` stage_timer, 감쌀 지점, provenance `timings`, 시험.
2. S1 load_rules 캐시(경로·mtime_ns·size 키) + 6299f295 cherry-pick + 전·후 검사 시간.
3. S2 고정 격자 조각 캐시(chunk_sec 10, 탐침 서명), 정확성 시험.
4. S3 `[map-event-covered]`·`[media-date-cross]`·밀집 hard + 여섯 프로젝트 건수 표.
5. S4 review_sheet·uf_checklist, README §6 절차, LLM-AP-023.
6. S5 WORKFLOWS 단일 구현 모드, 연출 좌표 규칙 확인.
7. S6 전·후 측정 표 → sweet-galileo merge → 검증 → 감독 승인 대기.

## 다음 R
- S0·S1 결과(전·후 검사 시간, checks.json 바이트 비교).
