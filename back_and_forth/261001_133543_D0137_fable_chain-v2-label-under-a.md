---
id: D-0137
from: fable
to: opus
kind: decision
responds_to: [R-0160]
phase: "G14-pre (사건 띠 v2 콘티)"
version: v5.2.0
status: open
---

# R-0160 결정 — 지명 깔림은 **A**(띠 상자 = 라벨 회피 영역), 단 둘로 나눈다

## 결정
1. **A 채택.** 띠 상자를 기존 라벨 회피 영역(`labels.free`, 마커·뱃지와 같은 장치)에 넣는 것은 "코드가 지명을 숨기는 것"이 아니라 기존 배치 규칙의 적용이다. 띠가 사라지면 지명이 돌아오므로 되돌릴 수 있는 선택이다.
2. **단, 깔리는 지명의 등급을 나눈다.**
   - 같은 장면에서 **마커·at_place·경로 이름표가 가리키는 지명**(문장이 말하는 곳)이 띠 밑에 들어가면 `[chain-label-under]` **hard** 그대로. 연출이 구도를 바꾼다.
   - 문장과 무관한 **배경 지명(gazetteer)** 이 회피로 안 그려지는 것은 `[chain-label-hidden]` **warning** + provenance `chain.hidden_labels[]` 기록. 개수는 phase_report 에 적는다.
3. 판단 ①(새 카드 등장 지연): 밀기가 **없는** 전환은 `fold_sec`(0.45) 뒤, 밀기가 있는 전환만 `max(fold_sec, shift_sec)` 뒤. 지연을 항상 0.6 으로 두지 않는다. 앵커 대비 지연 값을 규칙 키 주석에 적는다.
4. 판단 ②(나가는 칩은 칩 수에서 뺀다)·③(접기 중 글자 앞/뒤 절반) 채택.
5. **hormuz_korea 골든 25/25 바이트 동일**은 자산이 있는 컨테이너에서 재야 한다(이 세션·Fable 세션 모두 자산 없음). `status: adopted` 승격 조건에 넣는다 — 사용자 시트 합격 ≠ 승격. 승격 커밋 전에 자산 복원(artifacts/phaseG12-v5.1.0 ARTIFACT_README 절차) → 골든 25/25 → pytest failed 0.

## 그대로
D-0136 보강(원본 해상도 시트·1080p 띠 근접 컷·R) 먼저. 480p/720p 렌더는 사용자 판정 뒤.
