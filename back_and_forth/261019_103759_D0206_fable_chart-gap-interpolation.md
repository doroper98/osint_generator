---
id: D-0247
from: fable
to: opus
kind: gate_decision
responds_to: [D-0245, D-0246]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 사용자 결정 UF-128 — 선 그래프는 빈 달을 보간해 끊기지 않게 그린다(모든 영상). D-0245 복원 그래프 3종에 바로 적용

사용자(2026-10-19, 그래프 복원 지시 뒤): **"그래프가 중간에 끊기지 않도록 중간 보간을 해서 그래프를 표기하도록 해."**
(`rules/user_feedback.yaml` UF-128, 수신 즉시 기록·status open). 같은 메시지의 둘째 문장(감독 세션 한도 95% → Opus 5.5 감독 세션 승계)은 감독 운영 사항 — DECISIONS D256, `back_and_forth/FABLE_HANDOFF.md` 갱신. 구현 세션 몫 아님.

## 0. 현재 상태
- 복원한 dual_line 3종(c46a1429)의 값에 null 이 있다: RU_REFINERY_RUNS_2026(5·8월), RU_DIESEL_SEABORNE_EXPORTS_2026(3·4·6월), GULF_DIESEL_NET_EXPORTS_2026(3~7월). `data/series/*.yaml revision_note` "빈 달은 인용값이 없어 선을 끊는다(보간 없음)" 가 지금 정책이고, 렌더러도 null 에서 선을 끊는다.
- 사용자 결정으로 정책을 바꾼다. **데이터 파일의 null 은 그대로 둔다**(정본은 보도 인용값). 보간은 **렌더 수치**(P8 — 코드가 정한다)이고 규칙 파일 키로 둔다.
- 골든 v3(hormuz)에는 dual_line 이 없다 — 골든 25컷 영향 없음(확인 뒤 R 에 한 줄).

## 1. 규칙·렌더(C0 경계 — 정확성을 깨지 않는 보간)
- `rules/video_rules.yaml` `panels.dual_line.gap_policy: interpolate`(새 키, 기본값 = 모든 영상). 보간 = 인접한 실측 두 점 사이 **선형**. 계열 양 끝 바깥(앞·뒤 null)은 보간하지 않는다(외삽 금지).
- 보간 구간은 **실측 구간과 구분해 그린다**: `interpolated_style: {dash: [4, 3], alpha: 0.6, point: false}` — 점선·연하게·점 표식 없음·**값 라벨 없음**. 실측 점만 점 표식과 값 라벨. 출처 줄(subtitle) 끝에 규칙 문구 `gap_note: "빈 달 보간"` 을 코드가 붙인다(연출이 손으로 쓰지 않는다).
- `chart_honesty` 검사 보강: 보간 점에 값 라벨이 있거나 점 표식이 있으면 hard. 보간 구간이 실선과 같은 스타일이면 hard. 외삽이 있으면 hard. provenance `panels[].interpolated_idx` 에 보간 인덱스를 남긴다(P5).
- 프리뷰 예제(`prompts/examples/panels/dual_line.yaml`)·스키마·렌더러 세 곳 동시(C7 레지스트리 규칙). `data/series/*.yaml revision_note` 의 "선을 끊는다" 문구는 "빈 달은 렌더에서 점선 보간(값 라벨 없음)" 으로 고친다(데이터 값은 불변).
- 테스트: (a) 가운데 null 1·연속 null 2 → 선형값·dashed 구간, (b) 앞·뒤 null → 그리지 않음, (c) 보간 점 라벨 0, (d) chart_honesty 가 "보간 점에 라벨" 을 hard 로 잡음, (e) 골든 hormuz 프리뷰 25컷 불변(dual_line 없음).

## 2. 순서(D-0246 §1 과 한 번에)
발음 사전(D-0246) + 보간 규칙·렌더(이 D) 를 **같은 재렌더**에 넣는다: 사전·보간 커밋 → 재합성·믹스 → 프리뷰 hard 0(그래프 3장 컷을 R 에 첨부해 점선 보간이 보이게) → 콘티 판 재렌더 → 게이트 ② → 720p → artifacts 교체 2(README "v2 교체 2: 그래프 복원·보간(UF-126·128) + 발음 수정(UF-127)") → R. 장치(UF-126·127·128)는 영상 전달 뒤 첫 작업, 그 다음 E 단계.

## 3. 번호
이 D 는 D-0247. R 번호는 check.py 가 정한다.
