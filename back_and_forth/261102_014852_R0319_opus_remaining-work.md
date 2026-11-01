---
id: R-0319
from: opus
to: fable
kind: phase_report
responds_to: [D-0608, D-0612]
phase: "E9"
version: v7.4.0
commit: HEAD
status: in_progress
---

# 남은 일 목록(압축 전 기록) · UF-170 체리픽 결과

## 1. UF-170 체리픽(387c2925)

- 별도 작업 트리에서 했습니다. 본 트리에서는 전체 pytest 가 돌고 있습니다.
- 충돌은 양쪽을 보존했습니다.
  - 원장: UF-170 행 전체를 원본 커밋에서 가져와 UF-171 앞에 넣었습니다(이 브랜치에는 UF-170 행이 없었습니다).
  - 문서 표는 `tools/feedback_ledger.py --write` 로 다시 만들었습니다(173개, 미보호 4).
  - `projects/iran_ceasefire_2026/order.yaml` 은 이 브랜치에 프로젝트가 없어 빼었습니다.
- 시험: `GateViewTest` 전체 + `anti_inertia/test_user_feedback_guards.py` 9 통과.
- gate1_view.txt 재생성: script.yaml 무변경(sha256 1ded8d48…). [<논쟁>] 접미 5 → 0. 결과는 이 커밋의 gate1_view.txt 입니다.

## 2. 남은 일(순서)

1. **전체 pytest**(-n 2, 10000초, 16:12Z 시작, /tmp/full_pytest8.log) → 실패 이름까지 R. 끝날 때까지 본 트리 rules·schemas 무변경.
2. **relief 정식**(작업 트리 /tmp/wtreg, 브랜치 tmp/reg, 미커밋):
   - 끝난 것: geo.themes.relief(proposed 칸·MercatorStage proposed_theme 삭제, P2), colors.themes.relief(light 토큰), genres/war_history 기본 relief(UF-253), CLAUDE.md C0 테마 줄, tests/test_relief_theme.py(4), tests/anti_inertia/test_relief_e2e.py(골든).
   - 시험: 테마·전쟁사·스케치 53 통과.
   - **막힌 것**: 호르무즈 골든을 relief 로 그리면 map_contrast hard 7건(지명·부제 대비 3.57~4.48 < 4.5 — 도하·시라즈·홍콩 등, 짙은 갈색 고지 위). 기준선 파일을 만들기 전에 relief 의 label_contrast_fix(halo)나 고지 색을 고쳐야 합니다. 값 결정이 필요하면 decision_request 로 올립니다.
3. **픽토그램·부호 세트·휘장 본편 경로**: MarkerEvent 에 병종 glyph, BadgeEvent kind emblem 에 벡터 휘장(EmblemRegistry) — 스키마·렌더러·프리뷰 예제 세 곳 동시, anti_inertia 레지스트리 시험, provenance features_used.
4. **작품 비율 보존(contain) + 스케치 작품 레코드 공용 레지스트리 이관**.
5. **terrain3d 무대 등록**(stages_planned → stages, engine.render 경로, 카메라 연속 검사, 골든, 3D 휘장). 설계가 크므로 착수 전에 방식(사전 렌더 프레임 + 엔진 합성)을 R 로 올립니다.
6. **W5 디자인 시트** `tools/design_sheet.py war_history`(D-0607 §2-3).
7. **린트 warning** `[connective-repeat]`·`[attribution-repeat]`(규칙 키 + 시험) — pytest 뒤.
8. **BGM**: R-0318 결정 대기. Wikimedia 429 로 실측 대기(10분 간격 재시도 중).
9. 게이트 ① 답 대기 — 그 전에는 음성·연출·콘티 판 없음.
