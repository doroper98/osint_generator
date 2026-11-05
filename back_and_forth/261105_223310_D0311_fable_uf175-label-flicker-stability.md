---
id: D-0311
from: fable
to: opus
kind: directive
responds_to: []
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 사용자 의견 UF-175 / D533 — 지도 지명 라벨 깜빡임 제거(숏 단위 라벨 일정·이력 LOD·[label-flicker] hard). D-0310 과 합쳐 **전편 1회** 재렌더

## 0. 사용자 원문(2026-11-05 22:35 KST)
> "지도가 확대 되거나 축소 될때 도시 이름이 나왔다 사라지거나 없던게 나온다거나 깜빡깜빡 거리는거 있는데 그런것도 없애라고 했잖아. 왜 기억을 못하니. 두가지 사항을 반영해서 다시 완성본 보완을 해"
- 원인(실측 `engine/layers/labels.py`): 프레임마다 `free()` 충돌 판정·폭 LOD(`by_w`)로 라벨 집합을 새로 정한다 → 카메라 이동 중 라벨이 나타났다 사라지고, 새 라벨이 끼어들어 기존 라벨을 밀어낸다. 경로 이름표에는 D209 `label_jump` 가 있지만 지명 라벨에는 안정 장치가 없다.
- **렌더는 D-0310(접속사)과 이 지시를 둘 다 넣은 뒤 한 번만** 돌린다. 순서: D-0310 원고·규칙(짧다) → 이 지시 엔진 → 검증 → 전편.

## 1. 엔진 — 숏 단위 라벨 일정(전 영상 공통, 모드·플래그 아님 — P2)
1. **사전 계산** `engine/labels_plan.py`(새 모듈): 숏(카메라 키 사이 이동·정지 구간, `mode: cut` 에서 끊음)마다 카메라 경로를 프레임 간격(또는 4프레임)으로 훑어 라벨 일정 `{label_id: [(t_in, t_out), …]}` 을 만든다.
   - 숏 시작 뷰에서 지금 로직(LOD·free)으로 **초기 집합**을 정한다.
   - 이동 중 **기존 라벨은 유지**. 새 라벨은 ① 기존 라벨과 안 겹치고 ② 숏 끝 뷰까지 화면 안·LOD 안에 남을 때만 추가(그때 한 번 페이드인). 끼어들어 기존 라벨을 밀어내는 일 없음.
   - 퇴장은 앵커가 화면 밖으로 나가거나 숏이 끝날 때만 — 나가기 `fade_sec` 전부터 페이드아웃(경로로 예측).
   - 폭 LOD 이력: 라벨이 들어온 폭 w0 기준 `w ≤ w0 × lod_hysteresis` 동안 유지(축소 중 LOD 경계에서 깜빡임 금지), 확대 중 새 등급 라벨은 ②로만.
   - 대상: 도시·주(admin-1)·나라·바다 라벨 전부. 수도 상시 표기(capital_always)는 그대로.
2. **렌더** `draw_labels`: 프레임마다 다시 정하지 않고 일정을 읽어 그린다(알파 = 페이드 곡선, 자리 = 앵커 투영 — 자리는 카메라에 따라 움직이되 '있고 없음'은 일정대로). 병렬 구간 렌더(`--jobs`)에서도 같은 일정(결정적, 렌더 전 1회 계산·`out/labels_plan.json` 저장).
3. 규칙 `labels.stability: {fade_sec: 0.5, min_hold_sec: 2.0, lod_hysteresis: 1.25, sample_every_frames: 4}` — 코드 리터럴 0(test_no_magic_numbers).
4. **검사 `[label-flicker]` hard**(engine/checks.py, 그려진 상자 기준 — P12): 프리뷰·콘티·전편의 `drawn` 라벨 상자를 프레임 열로 모아, 한 숏 안에서 같은 라벨이 사라졌다 다시 나타나거나(재등장) 보인 구간이 `min_hold_sec` 미만(숏 끝 절단 제외)이면 실패. 경고 `[label-churn]`: 한 숏에서 라벨 등장·퇴장 합이 `labels.stability.max_events_per_shot`(예 8) 초과.
5. provenance `features_used.label_plan: {shots, labels, events}`.
6. 테스트 `tests/test_label_stability.py`: 가짜 지도(stage.adm·plc 몇 개)에서 줌인 경로 → 일정에 재등장 0·최소 유지 충족, 옛 방식(프레임별)으로 만든 열은 `[label-flicker]` 가 잡는다(장치 증명). anti_inertia 통과.

## 2. 골든(hormuz dark·light 25컷)
- 지명 라벨 '있고 없음' 이 바뀌면 골든 화소가 바뀐다. **재기준은 감독 결정** — 구현은 ① 25컷 중 달라진 컷 수 ② 한 컷의 전후 비교(라벨 차이만인지) ③ 다른 요소 차이 0 을 R 로 올린다. 라벨 차이만이면 감독이 D-0053 방식으로 기준선 교체를 결정한다(기준선 파일은 `_pre_uf175` 로 보존). 라벨 외 차이가 있으면 멈춘다.

## 3. 절차
1. D-0310(원고 18문장·규칙·재합성) → 이 지시(엔진·규칙·검사·테스트) → direction 재검증 hard 0(`[label-flicker]` 포함) → 골든 R(§2) → 감독 D → `--preview auto` 1회(라벨 안정 확인용 — 이번엔 돌린다, 카메라 이동 구간 컷 6장: 콜드 오픈 줌인·텍사스 진입·메인 진입·알래스카 왕복·본토 복귀·주지사 전환) → 720p 전편 → mix → mux → final_deliver(교체본 2) → artifacts final/ → phase_report R + send_message.
2. 그다음 D-0309 §2(장치·전체 pytest·README). UF-174·175 장치는 이 지시의 린트·검사가 그것이다(원장 guards 연결).
