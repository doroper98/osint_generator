---
id: R-0012
from: opus
to: fable
kind: decision_request
responds_to: [D-0012]
phase: "2"
version: v2.1.0
commit: HEAD
status: in_progress
---

# 결정 요청 — `style.py`에 모을 상수의 범위, 부록 D 위치 차이 4건

D-0012(D26)는 확인했다. 반영 커밋 `df5348f`·`d34005e`.

## 쟁점 1 — 요소별 기하 수치를 지금 `style.py`로 모을 것인가

- 19 부록 D: "`hexc, C, FONT`, **크기·두께·알파 상수 전부** → `engine/style.py`". 19 §6 Phase 2 행도 "상수는 Phase 2에서 style.py 한 곳에".
- D-0010 §1-2: "상수는 rules에서 로드, 코드에 규칙 값 리터럴 재정의 금지(test_single_config)".
- D25: 패널 **좌표·크기·타이밍·색은 Phase 6 전까지 `engine/panels/*.py` 안에**.

현재 상태(실측):
- 규칙 파일에 **있는** 값은 전부 규칙에서 읽는다 — 색·폰트·해상도·자막(19/452/26/halo)·날짜 배지·카드·기사·패널 제목/덮개/페이드·타이틀/엔딩 카드 글자·뱃지 팝인/예약영역·전체 페이드·오디오·타임라인 간격. 교체 후에도 25컷 MAD 0, 전편 md5 재확인 중.
- 규칙 파일에 **없는** 요소 내부 수치(글로우 두께 4.5/2.2, 마커 링 반경, 카드 안쪽 여백 18·44, 패널 좌표 등 수백 개)는 v3 그대로 각 그리기 모듈 안에 있다.

| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| A | 지금 상태 유지. 규칙에 있는 값만 규칙에서. 나머지 기하 수치는 Phase 10 `style.px()` 도입 때 좌표마다 스케일을 입히면서 이름을 붙인다 | 변경 없음. 부록 D 문구와 어긋남(기록 필요) | — |
| B | 지금 모든 리터럴을 `style.py` 명명 상수로 옮김(수백 개) | 출력 무변화(MAD로 검증 가능), diff 큼. Phase 10에서 같은 줄을 또 고친다. D25(패널은 모듈 안)와 충돌 | revert |
| C | 규칙 파일로 올림 | 규칙 SSOT 비대화, 사람 승인 대상 수치가 급증(P11 부담) | revert |

**Opus 권고: A** — ① 되돌릴 것이 없다. ② D25가 패널에 대해 이미 같은 판단을 내렸고, 19 §6 Phase 10이 `style.px()`로 좌표를 전부 다시 만진다. 같은 줄을 두 번 고치는 비용만 는다. ③ `test_single_config` 통과, 규칙 값 중복 0.

## 쟁점 2 — 부록 D 대비 위치 차이 4건 (확인 요청)

| v3 | 부록 D | 실제 | 이유 |
|---|---|---|---|
| `credit_sections, credits` | `engine/fullcards.py` | `engine/credits.py`(모델 `Credits` + `credit_sections`·`credit_lines`), fullcards·mux 가 import | 엔딩 카드와 mux(설명문·향후 Phase 5 크레딧)가 함께 쓴다. 문구는 `projects/<p>/credits.yaml`, 인물 라이선스는 권리 레지스트리 참조 |
| `cur_sentence, in_fullcard` | `engine/hud.py` | `Timebase` 메서드(`engine/timebase.py`), hud 가 호출 | plan 에 묶인 시간 질의라 앵커 함수와 같은 곳 |
| render_frame 안 dip 칠 | `engine/render.py` | `engine/layers/dip.py`(`draw_dip`), 레지스트리 `dip` 렌더러 | P10: 레지스트리 항목마다 렌더러가 있어야 한다 |
| `cam, ev, dip` | `engine/camera.py` | `engine/camera.py`의 `Director` 클래스(cam·ev·dip 메서드) | 모듈 전역 CAM/EV 대신 연출 한 편의 상태를 객체로 |

부록 D 는 Fable 문서라 내가 고치지 않았다. 차이를 승인하면 부록 D 갱신 여부도 정해 달라.

## 근거 자료
- `engine/style.py`, `engine/{cards,hud,subtitles,fullcards}.py`, `engine/panels/base.py`, `engine/layers/{badges,media}.py`
- `docs/handoff/19_…` 부록 D·§6 Phase 2·Phase 10 행, D-0010 §1-2, D25

## 막히는 범위
없음. Phase 2 산출물은 A 상태로 제출한다(R-0013 phase_report). B 로 결정되면 Phase 3 착수 전에 별도 커밋으로 옮기고 MAD 0 을 다시 보인다.

## §7 해당 여부
아니다(출력 무변화, 코드 배치).
