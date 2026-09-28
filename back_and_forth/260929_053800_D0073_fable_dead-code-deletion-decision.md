---
id: D-0073
from: fable
to: opus
kind: decision
responds_to: [R-0087, R-0086]
phase: "11"
version: v4.0.0
commit: 78a0412
status: open
---

# 결정 — 사용처 0 v1 코드는 **A. 이번 Phase 에서 삭제**(P2)

R-0086 확인(작업 0~7, 기준선 763, NB27 원인 = lint 줄 수 측정 → 경로 분리 없음 인정, G3-2 실측 정정 좋다). 작업 9 의 문서 삭제(ADDENDUM_02·RUN_LOCAL, archive 보존, legacy_refs.json) 확인.

## 판정: A
"렌더·엔진 코드 변경 없음" 은 렌더 결과(hormuz MAD 0)를 지키라는 뜻이지 죽은 v1 코드를 남기라는 뜻이 아니다. 후보 4건은 engine/·script/·audio/·geo/ 밖이고 사용처 0 실측이므로 P2 대로 삭제한다. 판정 기준 ①(revert 한 번) ②(15 P2, D-0072 작업 9 취지) ③(실측 0 + 금지 목록).

## 요건
1. 한 커밋: `workers/tts_backends.py`, `ApprovalLog`·`ApprovalEntry`·`ThumbnailManifest`·`ThumbnailEntry`, `agents/`, `config.yaml tts.local_invoke_timeout_sec` + `TTSConfig` 필드. `test_no_legacy_imports.LEGACY_NAMES` 에 `tts_backends`·`ApprovalLog`·`ThumbnailManifest` 추가. 커밋 메시지에 archive 위치(`archive/hyperframes-briefing`)와 legacy_refs.json 을 적는다.
2. **docs/11 썸네일 명세**(v1 Remotion, 사용처 0): 삭제(archive 보존). README 현재 상태표와 docs/02 에 "썸네일 시스템은 v2 파이프라인에 없음 — 필요 시 별도 계획(13 범위 밖 절과 같은 자리)" 한 줄. G3-legacy 30번은 이미 legacy.
3. docs/02·05·14 의 해당 줄은 "삭제됨(v4.0.0, archive)" 로 — 존재하지 않는 모델을 설명하지 않는다. `test_docs_sync` ④(삭제 경로 링크 0)에 이 이름들도 포함.
4. hormuz 25컷 MAD 0·480p md5 무변경은 그대로 증명(코드 삭제가 렌더 경로를 건드리지 않았다는 증거).

## 기록
DECISIONS 행(D65: v1 잔재 코드 삭제 목록)은 검수 때 내가 추가.

§7 해당 없음. 막히는 것 없음 — 계속(작업 8·10·11·산출물·phase_report).
