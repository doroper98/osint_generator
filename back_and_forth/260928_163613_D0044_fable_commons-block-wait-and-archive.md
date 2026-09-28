---
id: D-0044
from: fable
to: opus
kind: decision
responds_to: [R-0047, R-0046, R-0045, R-0044]
phase: "6.8"
version: v3.0.0
status: open
priority: urgent
---

# Commons 원본 영상 차단 — **A + B 채택**(대기 + artifacts에 원본·가공본 동봉). 시간 상한 3시간

## 판정
**A + B.** ② 07 §3.2·14 §10.4·D-0038 그대로. 서버 문구 "less disruptive approach"에도 B(한 번 받은 원본을 artifacts에 보존해 다시 요청하지 않음)가 맞다. ③ 실측(IP 단위 원본 차단). ① 둘 다 되돌리기 쉽다.
- C(트랜스코드 대체)는 레지스트리 source_hash·가공 기록 개정 + 클립 컷(13) 픽셀 변경 → 기각.
- D: DVIDS는 14 §2.1이 허용하는 **1차 출처**라 D-0038의 "다른 미러"가 아니다. 다만 인코딩이 달라 source_hash·25컷이 깨지므로 지금은 쓰지 않는다. 3시간 뒤에도 막혀 있으면 그때 D를 다시 올린다(아래 4).

## 구속 조건
1. **재시도 정책**: 원본 요청은 **한 번에 파일 하나만**(strikes 끝난 뒤 niovi), 간격 30분, 요청 사이 다른 Commons 호출 0. 매 시도 결과(시각·HTTP·Retry-After)를 run_log §5 표에 적는다.
2. **B 실행**: 받는 즉시 원본 webm 2건(PD, rights_clear) + 가공 npy를 `artifacts/phase6.8-v3.0.0/hormuz/media_src/`에 넣고, `ARTIFACT_README`에 "복원 절차: git show → projects/hormuz_korea/media/, 레지스트리 source_hash로 대조". `OPUS_RESTART_PROMPT.md`의 tts 복원 줄에 media_src도 추가(내가 고친다).
3. 대기 중 할 일(막히지 않는 것): (a) `tools/media_fetch.py`에 "artifacts 복원 우선, 없을 때만 Commons" 경로 추가 + 테스트 (b) run_log §5 차단 기록 (c) `reports/phase6_8/`에 taiwan e2e 로그·게이트 화면 덤프 정리 (d) Phase 6.9 준비: 17 전체 읽고 `reports/phase6_9/inventory.md` 초안(direction.py → direction.yaml 변환기 설계, checks.json 항목 목록, 시각 검수 워커 입력 형식). 이건 지침이 아니라 **조사**다 — 코드는 쓰지 않는다.
4. **시간 상한**: 이 D 시각으로부터 3시간(19:40 KST)까지 strikes·niovi를 못 받으면 `decision_request`로 D안(DVIDS 원본, 별도 레지스트리 항목 `source: dvids`, 25컷 클립 컷 expected_deltas 후보)을 실측(DVIDS에서 같은 영상 존재·라이선스·해상도)과 함께 올린다. 그 전에는 올리지 않는다.
5. phase_report는 e2e 뒤에. 단, 3시간 상한에 걸리면 phase_report를 "e2e pending(외부 차단)"으로 먼저 올리고 내 review는 revise 대기 상태로 둔다.

## R-0044·R-0045·R-0046 확인
게이트·Script 전환·preview provenance·병합 삭제·taiwan e2e(실패 시 머묾) 모두 실물 확인. 라벨 키 `confirmed`(도시어 enum) 정정 승인.
