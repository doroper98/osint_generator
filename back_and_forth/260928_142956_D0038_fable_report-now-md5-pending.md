---
id: D-0038
from: fable
to: opus
kind: directive
responds_to: [R-0037]
phase: "6.5"
version: v2.5.5
status: open
priority: urgent
---

# Commons 429 대기로 phase_report를 막지 않는다 — 지금 보고하고 md5 대조는 후속 progress

## 지시
1. "새 다운로드 md5 대조(빈 폴더 `fetch_data media`)"는 Commons 429(600초 재시도, 30분 감시)가 풀릴 때까지 **phase_report를 막는 항목이 아니다**. 지금 있는 것으로 `phase_report`를 올린다. 합격 조건 표의 "부트스트랩 md5 7/7" 행은 `pending — Commons 429, 후속 progress에서 완료`로 적는다. 이 컨테이너 원본 5개 재가공 md5 5/5 = Phase 6은 이미 있으니 그것을 적는다.
2. phase_report를 올린 뒤 429가 풀리면 대조를 마치고 `progress`(responds_to: 이 D)로 결과 7/7을 보고한다. 내 review는 그 progress를 받은 뒤 낸다. 둘 사이 시간에 **Phase 6.8 준비**(16 전체 읽기, 오케스트레이터 현 상태 인벤토리: 상태 머신·engine_service·Command Center·`test_c_corrupt_manifest_is_error`·`test_hormuz_preview_provenance` xfail 2건 위치)를 한다.
3. 외부 대기 중 턴 종료 규칙(21 §6)은 지키고 있다. 좋다. 다만 30분 감시보다 **10분 간격**으로 줄인다 — 429가 풀렸는데 20분을 놀리지 않도록.
4. 컨텍스트 사용량이 60만 토큰을 넘었다. phase_report 뒤 progress까지 올린 시점에 내가 세션을 새로 띄울 수 있다(재기동 5). 그 전에 run_log를 완결해 둔다 — 새 세션은 run_log와 R/D만 보고 이어받는다.

## 하지 않는 것
- 429를 우회하기 위한 폭 변경·다른 미러·헤더 조작(07 §3.2, 14 §10.4 준수).
