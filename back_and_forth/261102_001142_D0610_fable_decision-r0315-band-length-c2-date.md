---
id: D-0610
from: fable
to: opus
kind: decision
responds_to: [R-0315, D-0609]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — R-0315 §4 넷. 스케치 v2 통과(사용자에게 보고로 전달). 원고는 D-0609 대로 v3 뒤 게이트 ①

## 0. 스케치 v2(b49c90d3) — 통과
SK-W6 0·SK-W5 0, 인천 C2 31프레임, relief·픽토그램·입체·타니트·주화 교체·인천 clip(DoD CC0) 실물 확인. 2026-11-01 15:1xZ 사용자에게 보고로 전달(판정 아님). NARA 111-ADC-8251 미사용 판단(권리 미확인) 옳다.

## ① band — **(가)+(다)**: 사료 간 범위를 허용하되 종류를 밝힌다
- `ForceFigure.band` 에 `kind: Literal[ancient_range, modern_estimate]` 를 더한다(필수). 지금 레코드는 `ancient_range`. 화면 띠 라벨·내레이션은 "사료마다 다르다 — 에우트로피우스 4만~폴리비오스 7만" 꼴로, **"현대 추정" 이라는 말을 쓰지 않는다**(코드가 kind 로 라벨 문구를 고른다 — `war_history.casualty.band_labels`). `band_required` 규칙은 유지하고 주석에 "modern_estimate 를 열람할 수 없으면 ancient_range 허용, provenance 에 기록" 을 적는다. 학술 출처가 열리면 modern_estimate 로 교체(되돌릴 수 있음).
- **로마군 병력 레코드 `rome_strength` 를 만든다**(폴리비오스 III.113 보병 약 8만·기병 6천 + 리비우스 XXII.36 "기록마다 다르다" 메모를 band ancient_range 로). cold_open_1 은 force: 를 인용한다. 사료 하나뿐인 값도 레코드로 두는 것이 원칙(수치 = 레코드).

## ② 길이 414초 — **사실을 줄이지 않는다. D-0609 의 정리(중복 제거·논쟁 쌍 묶기·접속사 제거)로 자연히 줄어드는 만큼만.** 목표는 6분 30초 이하이되, 넘으면 넘는 대로 게이트 ① 에 보낸다(사용자 "길이는 내용이 정한다" 선례). 지휘관 배치 문장은 지도 위 배치를 말해 주는 문장이라 빼지 않는다.

## ③ SK-C2 — **바꾼다.** 이름 없는 부대 블록끼리 맞닿은 것은 겹침 입력에서 뺀다(SK-W6 입력은 그대로). 진형이 붙어 있는 것은 사실이지 결함이 아니다. 규칙 키(`sketch.checks.c2_exclude_unnamed_units: true`)로 두고 provenance 에 제외 수를 남긴다.

## ④ 제목·뱃지의 "8월 2일" — **출처가 확인될 때만 쓴다.** 후보: 마크로비우스 『사투르날리아』 I.16.26(라틴어 원문 PD — archive.org Teubner 판)에 칸나이 날짜가 로마력으로 적혀 있다고 알려져 있다(감독 기억 — **확인 전까지 사실로 쓰지 않는다**). 구현이 archive.org 에서 라틴 원문을 확인하면 소스로 넣고, EraDate `calendar: roman` 으로 "기원전 216년 8월 2일(로마력)" 라벨 — 율리우스력 환산이 아님을 규칙 라벨에 명시. 확인 못 하면 원고·연출·스케치 뱃지 모두 **"기원전 216년"** 으로 통일(스케치 spec 날짜도 고친다 — 출처 없는 수치 금지).

## 2. 순서
D-0609 v3 작업 안에서 ①②④ 반영 → gate-view v3 → R(바뀐 문장 전/후·접속사·귀속 횟수 표) → 감독 검토 → 사용자 게이트 ①. ③ 은 스케치 규칙이라 별 커밋. 전체 pytest 는 R-0315 §5 대로 1회(끝날 때까지 rules·schemas 무변경 — ①③ 의 규칙 변경은 pytest 뒤에).
