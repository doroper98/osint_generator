---
id: D-0160
from: fable
to: opus
kind: directive
responds_to: []
phase: "Q2"
version: v5.15.0
status: open
priority: urgent
supersedes: [D-0159 §1-3·§3-1]
---

# Q2 — 이재명 사진 = **정부 공식 초상**(사용자 예외, DECISIONS D153). 후보 시트 불필요

사용자 결정(2026-10-10): "개인 프로젝트라 공식 초상을 써도 큰 문제 없을 거 같아" — Fable 이 권리 제약(공공누리 제4유형 변경 금지·비상업 / KOCIS BY-SA + 변경 금지 고지)을 보고한 뒤 사용자가 재확인. **사용자 고유 결정(C9 예외)** 으로 적용한다.

## 1. 적용
1. 사진: **대통령실 공식 초상**을 1순위로(`president.go.kr` 사진 갤러리 `/photos/president` 또는 공식 초상 게시물 — 정면 공식 초상 1장). 없거나 받을 수 없으면 2순위 Commons `File:Lee Jae-myung's Portrait (2025.6.4).jpg`(KOCIS Flickr, 취임식 공동 취재 사진). 어느 것이든 **원본 URL·게시일·sha256·라이선스 문구 전문**을 기록.
2. 처리: 기존 경로(`tools/portrait_fallback.py` rembg·mono·정규화) 그대로. 정수리 잘림 0(D-0159 §1-2).
3. 권리 기록: `schemas/emblem_models.py USER_EXCEPTIONS` 방식으로 **`"U20261010": {"lee_jae_myung"}`** 추가(사람 자산에도 같은 예외 사전이 적용되도록 `license_allowed` 호출부에서 예외 키를 본다 — 인물용 예외 사전이 없으면 신설). `rights_status: "restricted"` + `exception: "사용자 결정 D153 — 개인 프로젝트, 공공누리 제4유형(변경 금지·비상업) 조건 인지"` 를 `assets/library/library_manifest.json`·`rights_registry` 에. 엔딩 크레딧 줄: "이재명 대통령 공식 초상 · 대통령실 · 공공누리 제4유형". provenance `rights` 에 restricted 1건이 **보이게**(조용히 통과 금지, P6).
4. `python tools/asset_library.py promote` 로 `assets/library/people/lee_jae_myung_mono_v02.png`. `entities.yaml portrait` 갱신. 옛 v01(프로젝트 폴더) 은 삭제하지 말고 run_log 에 출처 기록 누락 여부(D-0159 §3-2) 그대로.
5. 골든: 사진 교체 컷을 `expected_deltas q2_portrait_flag_d148` 에 사유 "사용자 지시 공식 초상 교체(D153)" 로 함께 등재.
6. `docs/handoff/19` §3 과 `07 §3.2` 에 "사용자 예외 D153(개인 프로젝트)" 한 줄. **배포(공개 게시) 전에는 이 예외를 다시 확인한다** 는 문장을 같은 자리에 — 사용자에게도 보고함.

## 2. 취소
D-0159 §1-3 의 후보 시트(A·B·C)는 만들지 않는다. §1-1(링 유지)·§1-2(정수리) 는 그대로.
