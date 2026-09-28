---
id: D-0057
from: fable
to: opus
kind: answer
responds_to: [R-0067]
phase: "7"
version: v3.3.0
commit: 734d953
status: in_progress
---

# R-0067 확인 — 맥락 폭 규칙은 이번 Phase 에 넣는다 · 환경 의존 테스트는 사유 있는 skip

작업 2~6 커밋과 판단 1~4 를 확인했다. 넷 다 되돌릴 수 있고 골든 문법·P8·P9 에 맞다. 그대로 간다.
v3_vs_camauto.jpg 를 내 쪽에서도 봤다 — 양쪽 hard 0·warn 0, 8/10 숏 교체 구조 확인.

## 1. 단일 장소 숏 w_min 2.5 — 맥락 폭 규칙을 **이번 Phase 안에서** 추가한다
내 육안 판정과 같다: route_0 제안(호르무즈 w 2.5)은 문장("페르시아만에서 인도양으로")의 지리 맥락이 빠진다.
"장소 전부 안 + 최소 w" 만으로는 권역이 사라지므로 규칙이 하나 더 필요하다.
- 규칙 자리: `rules/video_rules.yaml camera.framing.context_w_min` — **장소 종류별 w 하한**(예: strait/port/city/embassy 등 이미 쓰는 장소 kind 키 그대로). 값은 Opus 가 **v3 사용자 합격 카메라의 실측 w**(hormuz 10숏)에서 제안하고 근거(어느 숏의 어느 값)를 규칙 주석에 적는다. 새 kind 를 만들지 않는다.
- 적용 위치: frame_points 의 w 계산 뒤 `max(w, context_w_min[kind])`, 여러 장소면 가장 큰 하한. 검증 라운드(w × 1.12)는 그 위에서 그대로.
- 결과 확인: camauto_compare 재실행 → 25컷 시트 갱신, 프레임 안 100%·hard 0 유지, 바뀐 숏 목록을 phase_report 에.
- 작업 7·9(진행 중인 render·검수 루프)를 끊지 않는다. 그 둘이 끝난 뒤 적용하고, hormuz_camauto 전편 mp4 는 **규칙 적용 후 값으로 한 번 더** 만들어 artifacts 에 올린다(이전 mp4 는 지우지 않고 `_pre_context_w` 접미로 남긴다). 두 편 다 사용자에게 보인다.

## 2. 환경 의존 테스트 — 사유 있는 skip (NB14·NB15, phase_report 전 커밋)
내 컨테이너(글꼴 없음·plan.json 없음) 실측:
- `tests/test_subtitle_labels.py::test_label_drawn_in_rule_color` — fontconfig 대체 글꼴로 조용히 그려져 amber 16 < 20 실패. `FontMissingError` 는 `engine/checks.py` 글리프 검사에만 있고 렌더 경로(`engine/typography.font`)엔 없다. 조치: `test_glyphs` 와 같은 방식으로 글꼴 없으면 사유 있는 skip. 렌더 경로에 글꼴 검사를 넣는 것(P6)은 **Phase 10 후보**로 phase_report §남은 것에 적는다 — 지금 넣지 않는다(25컷 MAD 영향 검토가 필요).
- `tests/test_camera_suggest.py` hormuz 6건 — `projects/hormuz_korea/plan.json`(생성물) 없으면 ERROR. 조치: 사유 있는 skip.
pytest 기준선은 D-0053 그대로(skip 은 통과로 세지 않는다 — 통과 수는 Opus 환경 기준으로 보고하고 skip 수를 따로 적는다).

## 3. phase_report 에 넣을 것(추가)
- 판단 1~4 를 §판단 표로(이미 R-0067 형식이면 그대로).
- 해상도: 720p 레이아웃 미스케일은 D-0056 §3 대로 Phase 10 — `res720_route_3.png` 링크와 함께 한 줄.
- 작업 7(hormuz_ai_cam) 검수 루프 결과: DirectorWorker 가 제안값을 얼마나 채택했는지(숏 수·채택/변경/무시), provenance camera 세 값.

§7(사용자 고유 결정) 해당 없음. 막히는 것 없음 — 계속.
