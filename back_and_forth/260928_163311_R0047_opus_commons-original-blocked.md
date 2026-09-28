---
id: R-0047
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "6.8"
version: v3.0.0
commit: 0f26174
status: blocked
---

# Commons 원본 영상(webm) 다운로드가 이 컨테이너 IP 에서 막혔다 — hormuz e2e 선행 조건

## 쟁점
- strikes 원본(upload.wikimedia.org, webm)이 15:41~16:32 KST 동안 429 7회 → `media_fetch` 가 **FAIL strikes** 로 기록(재시도 상한 소진, NB4 대로 남은 항목·재실행 명령 출력 예정).
- 서버 문구: "Too many requests - please contact noc@wikimedia.org to discuss a less disruptive approach or **instead use thumbnail images in sizes listed on https://w.wiki/GHai**". 원본 파일 요청 자체를 IP 단위로 막은 것으로 보인다(사진 3건은 표준 폭 썸네일이라 받았다).
- niovi 도 원본 webm 이라 같은 429 가 시작됐다(16:32, 1/6).
- 영상 2건이 없으면 hormuz 는 load_project(권리·자산 점검)에서 멈춘다 → 새 다운로드 md5 7/7, `test_provenance_e2e` 실제 통과, e2e md5 대조 전부 막힌다. 작업 1~9 코드는 끝났다.

## 선택지
**A. 기다림 — 30분 간격 재실행을 몇 시간 이어간다(권고, 단 B 와 함께)**
- 07 §3.2·14 §10.4 준수. 언제 풀릴지 모른다(수 시간~하루).
- 되돌리기: 필요 없음.
**B. 받은 뒤 재현성 구멍 닫기 — 영상 원본 2건(PD, rights_clear)과 가공 npy 를 `artifacts/phase6.8-v3.0.0` 에 넣고, 이후 컨테이너는 artifacts 에서 복원 → md5 로 레지스트리 source_hash 대조(권고, A 와 함께)**
- 매 재기동마다 Commons 원본 요청을 반복하지 않는다(서버 부탁 "less disruptive approach" 에도 맞다). tts 복원(D-0042)과 같은 방식.
- 되돌리기: 복원 절차 한 줄.
**C. Commons 가 제공하는 트랜스코드(예: 480p webm)로 대체**
- 원본 md5 = source_hash 대조가 깨지고 가공 결과 npy 가 달라진다(바이트 동일 불가). 레지스트리 정본 변경 = 권리·가공 기록 개정. 권고하지 않는다.
**D. DVIDS 등 다른 출처** — D-0038 금지(다른 미러). 제외.

## Opus 권고
**A + B.** ① 둘 다 되돌리기 쉽다 ② 07 §3.2·14 §10.4·D-0038 그대로 ③ 실측(원본 요청 IP 차단) 기준.
A 동안 막히지 않는 일: 없음에 가깝다(작업 1~9 완료, 문서·run_log 는 정리됨). taiwan 으로 e2e 메커니즘은 검증했다(R-0046).

## 막히는 범위
- 막힘: D-0038 PENDING-md5, 작업 10(hormuz e2e·25컷·artifacts), phase_report.
- 계속: 재실행 감시, run_log 보강.

## §7 해당 여부
아니다.
