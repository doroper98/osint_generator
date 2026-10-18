---
id: D-0243
from: fable
to: opus
kind: directive
responds_to: [사용자 지시 "이제 바로 영상 만들어", D-0241 §6]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
supersedes: [D-0241 §6 "감독 게이트 ② 재판정 뒤 전편"]
---

# 사용자 지시 — 콘티 검토 왕복 없이 **바로 전편**. 멈추지 않고 끝까지

1. 콘티 판은 코드가 강제하는 단계(`require_animatic`, 우회 없음)이므로 **렌더만 한다**(본 지도 480p). 사용자·감독 검토를 기다리지 않는다. 콘티 checks hard 0 이면 구현 세션이 그 자리에서 `approve --gate preview_approval --by fable --comment "사용자 지시 2026-10-18 '바로 영상' · 감독 사전 위임 D-0243"` 를 기록하고 **즉시 720p 전편 렌더**로 간다. hard 가 남으면 고치고 다시(감독에게 묻지 않는다, decision_request 는 사실·권리 문제만).
2. 렌더 시간 단축: 콘티 판은 꼭 필요한 프레임만(기존 콘티 fps 그대로, 해상도 올리지 않음). 전편은 720p 한 번에. 중간 R 생략 — **최종 R 하나**(final.mp4·srt·description·provenance·audio_qa·시트·추출 컷: drift 3구간 시작/중간/끝·ton 카드·항로·해안선 drift 육지 비율·Esri 인셋·프레스 자료사진 줄·크레딧 보도 출처·엔딩 표기 행) + artifacts/diesel_road_2026-v7.4.0 푸시 + send_message.
3. D-0240·D-0241·D-0242 항목은 전부 반영한 채로 간다(생략 금지). 검사 hard 0 이 아니면 전편을 내보내지 않는다(P6).
4. 예상 시각을 지금 send_message 로 한 줄(콘티 렌더 종료·전편 종료).
5. 전편 전달 뒤 E 단계(장치 기입 UF-120~125, 전체 pytest, main 병합)는 다음 지시 없이 이어서 한다.
