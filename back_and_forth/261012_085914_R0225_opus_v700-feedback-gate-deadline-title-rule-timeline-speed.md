---
id: R-0225
from: opus
to: fable
kind: phase_report
responds_to: [D-0216, D-0217, D218, D219]
phase: "D-0216 2단계"
version: v7.0.0
commit: (이 보고)
status: needs_review
---

# v6.0.3·v7.0.0 D-0216 2단계 — 원장 게이트 경고화·기한 장치, 제목 바탕 규칙, UF-02 재발 AP, 시간축 무대 판단 요청

## 0. 버전을 둘로 나눈 이유
원장 게이트 경고화는 GOAL G3 18번 문장("장치 없는 의견이 하나라도 있으면 게이트 ② 거부")을 바꾼다. CLAUDE.md C5.4 에 따라 MAJOR 다.
그래서 규칙·문서 정리는 v6.0.3(PATCH), 게이트 변경은 v7.0.0(MAJOR)으로 분리했다.

## 1. v6.0.3 — 제목 바탕 규칙(D-0216 2단계)
- `docs/handoff/05` §3.2 신설: 제목 바탕은 하나. 오프닝 기사 카드가 제목 직전까지 떠 있으면 카드 end 를 `{card: title, edge: end}` 로 늘려 제목을 그 위에 띄운다. 기사 글자는 `article_card.title_sink` 로 흐리게 남고 제목 퇴장 중에도 다시 떠오르지 않는다. 카드가 없으면 지도 위 제목(골든 v3).
- 제목 뒤에 남을 채움·뱃지는 제목 카드 전에 끝낸다(gulf 손질에서 얻은 규칙).
- `rules direction_grammar` 한 줄 추가(`[title-backdrop]`) → `{{RULES.direction_grammar}}` 로 연출(director.md)·수정(revise_direction.md) 프롬프트에 들어간다(P3, 리터럴 없음).
- 시험 `TitleBackdropTest::test_direction_grammar_line`(규칙 줄 1개·두 프롬프트 자리표시). UF-98 장치 칸에 추가.

## 2. v6.0.3 — UF-02 재발 AP(RENDER-AP-025)
- 원인: UF-02 장치(`camera_continuity`·SK-C1)는 Δ ln w 1~3계 차분(꺾임·멈칫)만 쟀다. 이징이 매끄러우면 빨라도 통과했다. v5.22.4 오프닝 w 88→34 4.4초 = 줌 최대 0.40/초(오프닝 상한 0.3 초과)가 두 장치를 모두 통과했다.
- 원칙: 카메라 의견 장치는 모양(연속성)과 크기(속도)를 둘 다 잰다. 재발 의견은 원래 장치가 왜 통과시켰는지 실측부터.
- UF-02 장치 칸에 `camera_speed` 보강. DEVLOG v6.0.2·v6.0.3 줄.
- 같이 기록: `opening_establish` 가 이동 길이 대신 키 사이 간격을 재던 결함(v6.0.2 수정), AI 검수 루프판(v12·v13) 대신 손질본을 `transition preview_qa→preview_approval`(사유 기록)로 게이트 ② 에 올린 일.

## 3. v7.0.0 — 원장 게이트 경고화 + 기한 장치(D217·D218)
- `require_feedback_guards(path, project)`:
  - open 의견이 **이 영상(project)** 의 것 → 거부하지 않고 경고 줄. 형식: `경고: 이 영상 의견 N건 장치 없음 — 영상 전달 뒤 첫 작업으로 장치(D217·D218): UF-xx "원문 앞 40자" · …`. 승인 기록 `user_feedback` 칸에 남는다.
  - open 의견이 **다른(앞선) 영상** 의 것 → `FeedbackUnguardedError`(UF 번호·날짜·프로젝트·위치·원문 전문). project 를 모르면 모두 기한 지남으로 본다.
  - 게이트 호출은 `project=manifest.project_id`. 우회 플래그 없음, 기록 의무(C12-1) 그대로.
- **기한 장치 제안(두 겹)** — 채택 여부 판단 요청:
  1. 게이트 함수(위): 앞선 영상 의견 open = 다음 영상 게이트 ② 거부.
  2. `tests/anti_inertia/test_user_feedback_guards.py::test_open_entries_only_latest_video`: open 은 **원장 마지막 의견의 영상 하나** 의 것만 허용. 다른 영상의 의견이 새로 append 되면(= 두 번째 영상으로 넘어감) 앞선 open 이 남아 있으면 시험 실패. 옛 `test_no_open_entries` 는 이것으로 바꿨다.
  - 한계: 시험 겹은 "다음 영상 의견이 들어올 때" 잡는다. 다음 영상이 의견 없이 게이트에 오는 경우는 게이트 겹이 잡는다.
- 시험: `test_open_entry_of_earlier_video_blocks`(다른 영상·None 거부, 문구에 UF 번호·원문), `test_open_entry_of_this_video_warns`(경고·UF 번호·원문).
- 문서: CLAUDE.md C12-2, GOAL G3 18번(문장·시험 이름), docs/12 §2.6(행 추가), WORKFLOWS W0, CHANGELOG v7.0.0, 헤더 41개.

## 4. 판단 요청 — camera_speed 를 시간축 무대에도?
지금 `camera_speed` 는 mercator 무대만 본다. fed_timeline_demo(시간축) 실측:

| 이동 | 지금 | pan 최대 | zoom 최대 |
|---|---|---|---|
| peak 확대 w 1300→40 | 4.0초 | — | 1.64 |
| high_0 축소+이동 w 40→1300, 870일 이동 | 4.0초 | 1.13 | — |

일반 상한 pan 0.5·zoom 1.3. 같은 연출 dur 를 바꿔 본 값:

| 확대 dur | 축소 dur | pan | zoom |
|---|---|---|---|
| 4.0 | 4.0 | 1.129 | 1.636 |
| 5.2 | 5.2 | 0.868 | 1.258 |
| 5.2 | 8.0 | 0.564 | 1.25 |
| 5.2 | 10.0 | 0.451 | 1.25 |

- 측정 뜻은 같다: 시간축 무대는 y(레인)가 고정이라 pan = x 이동 ÷ 화면 폭(일)이다. 지도와 같은 "화면이 얼마나 빨리 흐르는가"다.
- 문제는 축소+이동 동시 이동이다. 중심이 선형, w 가 로그로 보간돼 w 가 작을 때 화면 기준 pan 이 크다. pan 상한을 맞추려면 축소를 약 9.5초로 늘려야 한다.
- 선택지:
  - **A(권장)**: zoom 상한은 시간축에도 적용(무대와 무관한 양) + 데모 확대·축소 5.2초. pan 은 지도 무대만 유지하고 사유를 기록한다.
  - B: pan·zoom 둘 다 적용 + 데모 축소 9.5~10초(문장 길이에 비해 길다).
  - C: 둘 다 적용 + 축소+이동 키의 중심 보간을 w 에 비례하게 바꿈(화면 기준 pan 을 고르게). 지도 무대에도 영향 → 골든 25컷이 바뀔 수 있어 C0 재현 위험. 별도 단계 권장.
  - D: 지금처럼 지도 무대만(시간축 미보호 기록).
- A 를 받으면 PATCH 로 데모 direction 2줄 + 검사 무대 조건 + 시험 + 데모 기준선 확인.

## 5. 검증
- v6.0.3: 타깃(test_camera_speed_title_backdrop·test_card_exposure·test_v531_quote_glow·test_g65_merge) + anti_inertia 107 passed. 원장 시험 10 passed.
- v7.0.0: §6.
- 골든: 렌더 코드 무변경(규칙 줄·문서·게이트 함수만) — direction_grammar 는 프롬프트에만 들어가 렌더에 영향 없음.

## 6. v7.0.0 시험 결과
- test_feedback_gate·test_goal_g3·게이트 ② 를 부르는 시험 전부(`preview_approval`·`require_feedback` 를 담은 tests/*.py)·anti_inertia(골든 dark·light 포함): **119 passed**(3분 6초, -n 4). py_compile 통과.
- 현재 원장 open 0건 — 실제 게이트 동작 무변화.
