<!--
tier: 3
last_synced_with: v3.3.0
ssot_for: [phase7-run-log]
depends_on: [engine/framing.py, engine/shots.py, engine/camera_suggest.py, engine/checks.py, tools/camauto_copy.py, tools/camauto_compare.py]
last_review: 2026-09-28
-->

# Phase 7 실행 기록 — 카메라 자동화 보조 (v3.3.0)

같은 Opus 클라우드 컨테이너(Phase 6.95 이어서). 시각은 KST. 지침 D-0056, 확인 D-0057.

## 1. 작업 순서와 증명

| 작업 | 커밋 | 증명 |
|---|---|---|
| 0 NB12·F6 | `04b5b09` | `tests/test_subtitle_labels.py` 3 — 라벨 픽셀·무라벨 불변·auto 본편 컷 수 |
| 2 frame_points | `71635a2` | `tests/test_framing.py` 8 — 장소 전부 안·예약 회피·최소 w·스케일 독립·클램프 |
| 3·4 전환·숏 검사기 | `b45ec97`·`9955032` | `tests/test_shots.py` 7 — 임계 2.5·6, 숏 규칙 3종, checks 가 같은 함수 호출 |
| 5 제안 엔진 | `ac8e343` | v3 골든 current_fits 10/10, 규칙 리터럴 0(test_no_magic_numbers 에 3모듈 추가) |
| 5 연결 | `b0801d1` | 연출가 `{camera_suggest}`·게이트 ② 표·provenance camera·엔진 단계, 제안 경로 offscreen 0 |
| 6 camauto | `a4f65e6` | `camauto_compare.json`, `v3_vs_camauto.jpg` |
| 5 보정 | `61a0eea` | 엔딩 풀백 숏 제안 제외 |
| 9 증거 | `d3581a9` | camauto provenance suggested 8·used 8, hormuz 25컷 MAD 0 |
| 7 AI 재실증 | `03bff2a` | `qa_compare.md`, `hormuz_ai_cam/` |
| D-0057 §2 | `9e0dcbc` → `9e0dc87` | 환경 의존 테스트 사유 있는 skip(NB14·NB15) |

## 2. 명령

```bash
python -m engine.camera_suggest projects/hormuz_korea          # prev/camera_suggest.json (자동 적용 없음)
python tools/camauto_copy.py projects/hormuz_korea projects/hormuz_camauto
python -m engine.render projects/hormuz_camauto --preview golden
python tools/ai_vs_golden_sheet.py projects/hormuz_korea/prev projects/hormuz_camauto docs/handoff/reports/phase7/v3_vs_camauto.jpg v3 camauto
python tools/camauto_compare.py projects/hormuz_korea projects/hormuz_camauto docs/handoff/reports/phase7/camauto_compare.json
python -m engine.render projects/hormuz_camauto --jobs 4   # 144초
python -m audio.mix projects/hormuz_camauto                 # 36초
python -m engine.mux projects/hormuz_camauto                # 27초 → final.mp4 292.441초
python tools/ai_direction_run.py projects/hormuz_ai_cam --preview golden   # 743초, 연출가 재요청 1(배치 슬롯)·검수 재요청 1(스키마)
```

## 3. 측정

| 항목 | 값 |
|---|---|
| hormuz 25컷 회귀 | MAD 0(평균·최대), checks hard 0·warn 0, provenance camera suggested 8·used 0 |
| camauto 25컷 | 프레임 안 100%(v3 100%), checks hard 0·warn 0, 숏 규칙 경고 0, MAD 평균 0.031 |
| camauto 카드 RESERVED | 부산 뱃지 push(v3 135px·camauto 140px), 이재명 hide 2프레임 — 같은 구조 |
| 해상도 | 854×480·1280×720 golden preview checks 동일(hard 0), frame_points 결과 동일(화면비 0.08% 차 이내). 렌더러 레이아웃은 480p 좌표 그대로(`res720_route_3.png`) → Phase 10 |
| hormuz_ai_cam | 선택 판 checks 0·검수 hard 1·soft 6(6.9: 0·1·7), 제안 채택 0/8(근접 2), provenance camera given_to_director true·used 0 |
| pytest | 636 passed · skip 0 · xfail 0 (Opus 환경, 글꼴·plan.json 있음). Phase 7 새 테스트 34 |
