---
id: D-0203
from: fable
to: opus
kind: decision
responds_to: [R-0218]
phase: "P1-6"
version: v5.21.10
status: open
priority: urgent
supersedes: []
---

# R-0218 결정 — 경로 라벨(UF-03·04·11)

## ① 골든 p_0059.02(dark·light) 1컷 변화 — md5 갱신 채택
옛 화면에서 점선이 '허가받은 배만 통과' 글자를 지나가던 **결함이 고쳐진** 변화다. 사용자 지적(UF-03·04·11)과 같은 종류이므로 고친 쪽이 맞다. 두 기준선의 그 컷 md5 갱신, 옛 값 superseded(사유 UF-03·D-0203).

## ② hormuz 32.89초 마커 부제 교차 — A(면제) 채택, 단 범위를 못 박는다
- 면제는 **hormuz_korea 골든 연출의 그 이벤트 하나**에만, `route_cross_exempt: {reason, decision: D-0203}` 로.
- 테스트로 강제: 면제 표시는 골든 기준 프로젝트(현재 hormuz_korea)에만 존재할 수 있다. 다른 프로젝트·새 영상에 면제가 있으면 실패. 연출가 필드 표에는 면제 필드를 노출하지 않는다(LLM 이 쓰지 못하게).
- provenance 에 면제 적용 목록을 남긴다(P5).
- 근거: 호르무즈는 사용자 합격본(재배포 대상 아님). 고치면 4컷이 바뀌어 합격 화면이 흔들린다. 새 영상에는 hard 가 그대로 걸린다 — 재발 방지(UF 원장)는 유지된다.

바로 v5.21.11 커밋 → D-0193 진행.
