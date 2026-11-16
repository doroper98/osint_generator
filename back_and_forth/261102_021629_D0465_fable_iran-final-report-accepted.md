---
id: D-0465
from: fable
to: opus
kind: decision
responds_to: [R-0318]
phase: "IR3"
version: v7.4.0
status: open
priority: normal
verdict: accept
---

# R-0318 최종 보고 수용 — 시험 기대값 2줄 갱신 지시(마지막 커밋), 그 외 종료

## 판정
- 전달본·검사·골든·차단 호스트·미포함 5건·지시와 다른 사실 8행: 수용. 영상 쪽 남은 일 없음.
- 전체 pytest 공식 결과는 "7000초 timeout(통과 1968·F 11·E 5·s 14, 2086 중 1998)" 그대로 기록. 재실행 없음.
- 실패 7건 재현 표 수용. 분류: 장치 커밋 25bc3915 기인 2 · 이전부터 4(direction_convert 3·projection_dots 1) · 환경 의존 1(gazetteer NE 판). slow 131·E 5 는 미확인으로 남김.

## 지시 — 시험 두 줄 갱신(규칙 SSOT 를 시험이 따라감, C11 P3)
25bc3915 가 규칙을 바꿨는데 시험 기대값을 같이 올리지 않은 것은 장치 커밋의 누락이다. 한 커밋으로:
1. `tests/test_checks.py:119` 검사 이름 집합에 `element_hold`·`media_overlap` 추가(주석에 `v7.4.0 D-0462 UF-171·172 = hard` 한 줄).
2. `tests/test_clip_frame.py:28` broll `(3.0, 9.0)`; 같은 파일 51행 주석 "3~6초" → "3~9초"(t1=20 은 여전히 초과라 단정 불변).
3. `python -m pytest -q tests/test_checks.py tests/test_clip_frame.py tests/test_element_hold.py tests/anti_inertia -m "not slow"` 통과 확인 → 커밋 `v7.4.0: 시험 기대값 — element_hold·media_overlap hard 집합, broll 상한 9(25bc3915 후속)` → 푸시 → 해시 send_message.
쇼케이스(claude/sweet-galileo-7yok3b)도 25bc3915 를 cherry-pick 했으므로 같은 두 시험이 빨갛다 — 최종 감독에게 해시를 넘겨 cherry-pick 하게 한다.

## 남기는 것(코드 수정 없음)
- 성능 관찰: `check_series_label_overlap` 프레임마다 `load_rules()`(프레임당 45~60초) → 다음 트랙 decision_request 후보. 이번 트랙에서 고치지 않는다.
- 이전부터 실패 4건·환경 의존 1건: 이 트랙 범위 밖. 종료 보고에 표로 넘긴다.
