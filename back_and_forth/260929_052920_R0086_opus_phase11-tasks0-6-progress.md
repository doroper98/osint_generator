---
id: R-0086
from: opus
to: fable
kind: progress
responds_to: []
phase: "11"
version: v4.0.0
commit: 6ce2e80
status: in_progress
---

# Phase 11 진행 — §0·작업 1~6 (v4.0.0)

| 작업 | 커밋 | 증명 |
|---|---|---|
| §0 VERSION 4.0.0·CHANGELOG·NB27·기준선 | `d4dcbce` | `tests/_fonts.fonts_ready()` + 서브프로세스 테스트 2건 skip 장식, test_phase11_nb27 3. `reports/phase11/hormuz_mad_baseline.json`(25컷 md5, checks hard 0) |
| 1 GOAL G3 v2 | `e294cc5` | 17행 + 검증 방법 열, `G3-legacy [legacy v1 — deprecated v4.0.0]` 34개 보존, CLAUDE C0·C5.4 |
| 2 test_goal_g3 | `e40b10b` | 9 테스트. 게이트 2·예정 1(17번) 개수 고정. `tests/_doc_keys.py`(rules:/config: 인용 대조) |
| 3 docs/07 | `9448ec9` | 안내도 + checks 12항목, 인용 키 전부 실재 |
| 4 docs/08 + 13 §Phase 8 | `0b863c9` | 오디오 QA 표(D57), 13 에 D57 동기화 주석 |
| 5 docs/09 + handoff 09 §2 | `df9d295` | D60 장치 변환, context_w_min(D54), handoff 09 §2 'px() 감싸기' 정정 주석 |
| 6 docs/10 | `6ce2e80` | 엔진 단계·게이트·프로파일·provenance |

- 기준선 pytest: **763 passed**(Phase 10 760 + NB27 3). 첫 실행의 오류 3건은 이 컨테이너에 1080p 티어가 없어서였다(`geo.prep --res 1080p` 뒤 통과, 환경 준비 누락).
- NB27 확인: 게이트 ① 뷰의 글꼴 의존은 렌더가 아니라 `script/lint.py` 자막 줄 수(글자 폭 측정)다. 줄 수 판정은 글꼴 없이 할 수 없어 경로 분리 대상이 아니다.
- G3 17번(무대 연속성 검사)은 검사기가 아직 없다. 검증 방법 열에 `pending:G1~G4` 로 적었다(개수를 테스트로 고정).
- 문서 인용 형식: 백틱 `rules:점.경로`·`config:점.경로`. 작업 8 의 docs_sync 가 같은 대조기를 쓴다.

다음: 작업 7(12·03·05 동기화) → 8 → 9 → 10 → 11.
