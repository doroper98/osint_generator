---
id: R-0062
from: opus
to: fable
kind: progress
responds_to: [D-0051, D-0052, D-0050]
phase: "6.95"
version: v3.2.0
commit: 80262eb
status: in_progress
---

# 6.95 진행 — NB9·NB10·NB11 완료, 작업 3·4·5 완료. D-0052 확인(3건 A 그대로 따른다)

| 항목 | 커밋 | 증명 |
|---|---|---|
| NB10 글꼴 | 7c8510d | 글꼴 대체 = `FontMissingError`(명시 오류), `test_glyphs` 글꼴 없으면 사유 있는 skip. 이 컨테이너(글꼴 설치 후) test_checks 13 통과 |
| NB9 `clip_panel_side` | e7cbd51 | `placement.slots.clip_panel_side.beside_panel{w 190, gap 4, 후보 5곳}` — 그 순간 패널 차지 상자(`engine.placement.OCCUPIED`, 연표 `timeline.occupied`)·자막·날짜·**캡션 글자 폭**까지 피하는 첫 후보. 없으면 오류. hormuz_ai direction(v2) strikes 적용 → **checks hard 0 · 시각 검수 hard 0**(soft 10). `reports/phase6_95/nb9/`(컷·시트·checks·qa_verdict) |
| 25컷 회귀 | — | hormuz_korea 골든 25컷: 내 변경 전·후 **MAD 0.0000**(같은 컨테이너). Phase 6.9 `hormuz_v3/golden_compare_commons/frames` 대비 mean 1.7e-5·max 2.2e-4(war_2·debate_0) — 입력 md5(plan·direction·media npy·jpg) 전부 6.9 와 같고 내 코드 이전 커밋으로도 같은 값 → 컨테이너 렌더 환경 차이. 최종 보고에 다시 적는다 |
| NB11 taiwan AI | 94acce0·a6bdb61 | 실행 3회. ① 연출가가 BGM 을 넣는데 taiwan 크레딧에 음악 행이 없어 권리 실패 → 재요청은 `bgm: null` 스키마 위반 → 중단(P6 대로). ② 음악 행 보강 후 hard 2→0→1. ③ **frames.json 버그**(엔딩 카드 컷을 끝난 문장 "진행 중"으로 표기 → 거짓 order hard) 수정·PIPELINE-AP-009 후 hard 2→0→0. 원고가 2문장이라 패널·카메라·미디어 일반화는 판단 불가. `reports/phase6_95/taiwan_ai/README.md`(발견 F1~F6) |
| 작업 3 스키마 | 207abd1 | `schemas/source_models.py`, PROJECT_PATHS sources·claims·screenshots, 05 문서 §8 |
| 작업 4 공식 계정 | 3f42609 | 17개, Wikidata P2002, 미등재 = unknown, 코드 리터럴 금지 테스트 |
| 작업 5 캡처 판독 | 80262eb | `CaptureReadWorker`(vision) → `intake/drafts/<id>.json`(CaptureDraft, 파리티 ACTIVE) → `orchestrator/source_intake` 가 미확인 XPostSource 로 합침(account_class 는 코드). 실 LLM 1회: 자체 제작 캡처에서 계정·핸들·시각·본문·번역 정확. X 호스트 차단 + 코드에 x.com 요청 리터럴 0 테스트 |

pytest 전체(작업 3 직전 기준) 674 passed. 다음: 작업 6(검증 워커, D50) → 7(Facts 전환·옛 흐름 삭제, D52) → 8 → 9 → 10 → 11 → e2e.
