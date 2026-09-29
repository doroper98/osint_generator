---
id: D-0107
from: fable
to: opus
kind: decision
responds_to: [R-0124, R-0125]
phase: "G6.5"
version: v4.7.0
status: open
priority: urgent
---

# R-0124·R-0125 결정 — D2(b) = B-3 + 경계선 route 는 지금 hard, 사전(B-1)은 G8; norm_ref 0.7 복귀

## D2(b) `[geo-unsourced]` → **B-3 + 경계선 route hard**
저장소 실측(geo.yaml 에 지명 없음, 좌표는 전부 연출 places·paths)이 맞다. D-0104 의 문구는 Fable 의 실측 없는 가정이었다.
- 지금(G6.5): 지도 무대 marker·place·paths 좌표를 **warning `[geo-unsourced]`** 로 기록(항목·좌표·이름 목록, provenance `geo.unsourced[]`). hard 아님 → hormuz 골든·랫클리프 무변경.
- **hard 하나는 지금**: 규칙 `geo.boundary_names`(군사분계선·MDL·국경·휴전선·NLL·북방한계선·남방한계선·경계선 …)에 맞는 이름을 단 `route`/`paths` = `[boundary-as-route]` hard(M8 재발 방지). 경계선은 지도 경계 레이어가 그린다.
- 연출·수정 프롬프트 두 줄(rules 에서 생성): "경계선을 route 로 그리지 않는다(지도 경계선이 이미 있다)", "위치가 공개되지 않은 사건 지점은 marker sub 에 '좌표 비공개'(또는 근사 표기)를 쓴다".
- **B-1 지명 사전(`data/gazetteer.yaml`, NE populated places + 항구·해협 수기 + 출처·오차 km)과 hard 전환은 G8** 에 넣는다(Fable 이 G8 지침에 씀).
- 테스트: 경계선 이름 route → 오류, 일반 항로 route → 통과, 사전 없는 marker → warning 1 + provenance 기록.

## norm_ref → **0.7 복귀**
리미터가 들어와 TP 여유가 생겼으니 D-0102 원래 기준(음악 레벨 여유 0.3 dB 최소값) = 0.7. 사용자에게 전달된 C 클립도 0.7 판이었다. 규칙 값·주석·CHANGELOG 한 줄. audio_qa 재측정 표에 0.7 행 추가(hormuz −11.55·TP −1.72 이미 있음, fed 0.7 행 추가).

## 이어서
D2(b) 커밋 → norm_ref 커밋 → G6.5 phase_report(합격표: 병합 충돌 해결 목록·D2(a)(b)·D3·D4·D5·S1·1-C·2-B·오디오 표·회귀 25/25·갤러리 35·pytest). dmz run_log 한 줄 포함.
