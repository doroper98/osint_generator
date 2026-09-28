---
id: R-0006
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "1"
version: v2.0.1
commit: HEAD
status: blocked
---

# 결정 요청 — 영상 클립 2개의 원본(.webm) 다운로드가 Wikimedia 429로 막힘

## 1. 쟁점

`strikes`(U.S. Forces … Retaliatory Strikes Against Iran (1013909).webm)와 `niovi`(Oil tanker Niovi seized … .webm)
**원본 파일**을 받지 못한다. `legacy_v3/render3.py`는 시작할 때 두 클립의 npy를 읽으므로(`CLIP=…np.load`),
이 두 파일이 없으면 **프리뷰·골든 대조·전체 렌더가 전부 멈춘다.**

## 2. 실측 (2026-09-27 13:20~14:20 UTC)

| 대상 | 결과 |
|---|---|
| Commons API 메타데이터 8건 | **전부 수신**(항목별 캐시). 인물·휘장·사진 6장 수신, `prep people` 완료 — `rights_registry.json`이 참조본과 동일 |
| `upload.wikimedia.org/…/9/97/…(1013909).webm` 원본 | 429 연속(3회 실행 × 6회 재시도, 60~90초 대기). 응답: "Too many requests … **instead use thumbnail images in sizes listed on https://w.wiki/GHai**" |
| `upload.wikimedia.org/…/1/1b/Oil_tanker_Niovi….webm` 원본 | 같음 |
| 프록시 여부 | 세션 프록시가 아니라 Wikimedia envoy 제한(`x-envoy-ratelimited: true`, `retry-after: 29`). 공유 IP 한도로 보인다 |
| Wikimedia 트랜스코딩본(`/transcoded/…/*.480p.vp9.webm`, `720p.vp9`) | HEAD 요청 기준 **간헐적 200** (strikes 480p 200·720p 429, niovi 480p 429·720p 200) |

## 3. 선택지

| | 내용 | 결과·위험 | 되돌리기 |
|---|---|---|---|
| **A** | 원본만 고집. 10분 간격으로 원본 재시도를 계속하고 받을 때까지 Phase 1 렌더 대기 | 규칙 문면(D-0005 결정 1 조건 4 "대체 자료 금지")에 가장 충실. **언제 풀릴지 모른다** — Phase 1이 무기한 막힐 수 있다 | 해당 없음 |
| **B** | **같은 파일의 Wikimedia 공식 트랜스코딩본**(720p 또는 480p VP9)을 받는다. 같은 Commons 파일·같은 라이선스(Public domain)·같은 구간(strikes 1.5~6.5초, niovi 28.0~33.0초)을 480×270@24로 줄이므로 결과 npy 해상도는 동일. `media_registry`의 해당 항목과 `run_log.md`에 "원본 대신 Wikimedia 트랜스코딩본(720p VP9) 사용"을 기록 | 원본 재압축이라 480×270에서 픽셀 값이 조금 다를 수 있다(두 클립은 각 5초, 골든 25컷 중 클립이 보이는 컷은 소수). **다른 자료로 바꾸는 것은 아니다** — 같은 영상의 공식 파생본 | 원본을 받는 즉시 `media`만 다시 돌려 npy 교체 |
| **C** | A와 B 병행: B로 Phase 1 산출물을 먼저 만들고, 원본 재시도를 백그라운드로 계속해 받으면 교체·재렌더 | B의 위험 + 재렌더 비용(약 20분) | 같음 |

## 4. Opus 권고: **C**

- ① 되돌릴 수 있다: 원본을 받으면 npy만 바꿔 재렌더한다.
- ② 핸드오프 14 §10.4는 "Commons 429 대책 — 요청 간격·원본 URL·캐시 재사용"을 말한다. 원본 URL을 우선하라는 취지이지 파생본을 금지하지 않는다.
- D-0005 조건 4의 "대체 자료 금지"는 **다른 사진·영상으로 바꾸는 것**을 막는 조항으로 읽힌다. 트랜스코딩본은 같은 영상이다.
  다만 이 해석이 곧 결정이므로 네가 정해 달라.

## 5. 막히는 범위

- **막힘**: `fetch_data media`(npy), `golden_compare`, 컨택트 시트 3종, 전체 렌더, mix·mux, 산출물 세트, `phase_report`.
- **막히지 않음**: 원본 재시도(백그라운드 10분 간격으로 계속한다). 그 외 Phase 1 작업은 전부 이 뒤에 있다.

## 6. §7(사용자 고유 결정) 해당 여부

해당 없음(권리 원칙 완화가 아니다 — 같은 Public domain 파일). 네 판단에 맡긴다.
