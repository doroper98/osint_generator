---
id: D-0189
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1-0b"
version: v5.21.1
status: open
priority: normal
supersedes: []
---

# 새 컨테이너 재현에서 나온 결함 2건 — media_fetch 의 B 항목 · gulf_pk_soldiers 원본 해시

감독 컨테이너를 새로 세우며 `python tools/fetch_data.py people media` 를 돌렸습니다(v5.21.1, 2b2dc72).
레지스트리 미디어 수집이 아래로 실패했습니다(strikes 는 위키미디어 429 = 환경, 제외).

## 1. `gulf_pact_2026_art_0005_press: 'source'` — 코드 결함
- `tools/media_fetch.py:100` 이 `prm["source"]` 를 읽는다. v5.21.0 B 항목(`press_of`)에는 `source` 가 없어 KeyError 로 멈춘다.
- 결과: **새 컨테이너에서 B 사진을 다시 받을 수 없다.** 재현성(G4 권리 기록·P5) 구멍이다.
- 고칠 것: B 항목의 재수집 경로를 명시한다. `photo_url`(기사 og:image) 로 받아 `source_hash` 와 대조하거나, 받을 수 없으면 "보도 인용 — 재수집 불가, 원본은 프로젝트 media/" 를 **오류 문구로 분명히** 낸다(KeyError 금지, P6). 테스트 1개.
- gulf 본영상(D-0187)을 막지 않는다. 본영상 뒤 PATCH.

## 2. `gulf_pk_soldiers`: 원본 md5 `77d34b0b…` ≠ 레지스트리 `source_hash 19b315d2…`
- DVIDS 원본이 바뀌었거나 등록 때 해시를 다른 파일(변형본)로 잰 것이다. 어느 쪽인지 Opus 컨테이너 원본과 대조해 답해 주십시오.
- 원본 변경이면: 화면에 쓰는 가공 파일이 무엇에서 왔는지 provenance 와 맞는지 확인하고 레지스트리 기록 방식(원본 URL·해시·받은 시각)을 한 줄로 보고. 본영상은 Opus 컨테이너 파일 그대로 진행해도 됩니다.

## 3. 기록
DECISIONS 행은 고친 뒤 판정 때 붙입니다.
