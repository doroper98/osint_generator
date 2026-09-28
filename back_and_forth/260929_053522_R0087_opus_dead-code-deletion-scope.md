---
id: R-0087
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "11"
version: v4.0.0
commit: d28f06f
status: in_progress
---

# 결정 요청 — 사용처 0 인 v1 코드 삭제를 이 Phase 에 넣을까 (작업 9 범위)

## 쟁점
작업 9 는 "deprecated 문서와 `legacy_v3/`" 를 참조 실측 뒤 삭제하라고 했다. 실측 중 **코드** 쪽에서도 사용처 0 인 v1 잔재가 나왔다.
D-0072 는 "렌더·엔진 코드 변경 없음(문서 Phase)" 이라 코드 삭제를 혼자 넣지 않았다.

| 후보 | 실측(`reports/phase11/legacy_refs.json`) |
|---|---|
| `workers/tts_backends.py` (v1 세그먼트 TTS 백엔드) | import 0(코드·테스트). 참조 = `config.yaml tts.local_invoke_timeout_sec` 주석, docs/13(v1 로드맵), handoff 이력 |
| `schemas/models.py` `ApprovalLog`·`ApprovalEntry` | 사용처 0. 게이트 기록은 v3.0.0 부터 manifest `gate_decisions` |
| `schemas/models.py` `ThumbnailManifest`·`ThumbnailEntry` | 사용처 0. docs/11(썸네일 명세, v1 Remotion)만 가리킴 |
| `agents/__init__.py` (빈 패키지, v0.1.0) | 모듈 0. docs/02·14 가 옛 `agents/` 경로를 언급 |

렌더·엔진(engine/·script/·audio/·geo/) 코드는 하나도 없다. hormuz MAD 에 영향 없음.
`config.yaml tts.local_invoke_timeout_sec` 는 `TTSConfig` 모델 필드라 키를 빼면 config 모델도 같이 바뀐다.

## 선택지
- **A. 이번 Phase 에서 삭제**(한 커밋, P2). `tts_backends.py`·모델 4개·`agents/` 삭제, `config tts.local_invoke_timeout_sec` 와 `TTSConfig` 필드 삭제,
  `test_no_legacy_imports.LEGACY_NAMES` 에 `tts_backends` 추가(재생성 방지). 위험: 모르는 외부 스크립트가 쓰면 깨짐(저장소 안 0). 되돌리기: revert 한 번.
- **B. 목록만 남기고 G 단계 이후로**. 이번 Phase 는 문서만. 위험: 죽은 코드가 문서 동기화 대상에 계속 남음(docs/02·05·11 이 '존재하지만 안 쓰는 모델'을 설명해야 함).
- **C. 모델만 A, `tts_backends`·config 키는 B**. 스키마 파일 정리만 먼저.

## Opus 권고 — A
① revert 한 번으로 되돌린다. ② 15 P2("옛 경로는 삭제로 끝낸다")·D-0072 작업 9 의 취지. ③ 저장소 실측 사용처 0 + 금지 목록 추가로 재발 차단.
테스트 삭제는 없다(이 코드를 검사하는 테스트 0). 문서(docs/02·05·11·14)는 같은 커밋이나 문서 동기화 커밋에서 맞춘다.

## 막히는 범위
- 기다리는 것: 위 코드 삭제 커밋 하나, 그리고 docs/11(썸네일)·docs/02 의 해당 줄을 "삭제됨"으로 쓸지 "존재"로 쓸지.
- 계속하는 것: 나머지 Tier 1·2 문서 동기화, README·HANDOFF·DEVLOG·AP, test_docs_sync, 작업 11(NB24·NB28·NB21), 산출물.

## §7 해당 여부
해당 없음(사용자 고유 결정 아님).
