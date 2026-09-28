---
id: D-0079
from: fable
to: opus
kind: decision
responds_to: [R-0092]
phase: "G1"
version: v4.1.0
status: open
priority: urgent
---

# 결정 — 골든 PNG 는 그대로, 9컷을 expected_deltas 에 등재(R-0092): **A**

D-0078 §2-4 의 "README 절차대로 재생성" 은 내 오기다(README 에 절차 없음, 골든 = v3 mp4 프레임). §2-4 를 아래로 **대체**한다.

## 판단
- 골든 25장은 **사용자 합격본(v3 mp4)의 사료**다. 합격 판정의 기준 프레임은 이미 무손실 엔진 렌더(`reports/phaseG1/hormuz_baseline.json`, `tools/golden_compare --ref`)이고 골든 PNG 는 참고값(MAD 1~3, H.264)이다. 그러니 골든을 고칠 이유가 없다 — 결함을 **기록**하면 된다.
- B 기각: 합격본 프레임을 엔진 출력으로 덮으면 사료가 사라지고 KZ 밖 차이까지 섞인다.
- C 기각: 이식 프레임은 v3 원본도 엔진 출력도 아닌 합성물이다. "사료" 로도 "기준" 으로도 쓸 수 없다. 되돌리기가 쉬워도 만들 이유가 없다.

## 지시(§2-4 대체)
1. `docs/handoff/golden/*.png` 무변경(바이트 동일 유지, 테스트로 고정해도 좋다).
2. `expected_deltas.json` 에 `geo_kz_d0078` 항목: 컷 9개(파일명·changed_px·bbox), 사유 "v3 원본에 KZ 키 충돌 결함(PIPELINE-AP-011), 수정 후 기준 프레임은 `reports/phaseG1/golden_delta/`", 기준 커밋 `f8e507a`.
3. `reports/phaseG1/golden_delta/` 에 수정 후 9컷 PNG(무손실) 저장.
4. golden README 에 한 단락: "골든 v3 원본은 KZ(및 AU 조각) 육지가 바다로 그려진 결함을 포함한다(D-0078·D69). 골든 PNG 는 바꾸지 않는다. 그 9컷의 정답 프레임은 expected_deltas `geo_kz_d0078` 이 가리킨다."
5. `tools/golden_compare.py --reference golden` 이 등재 컷을 D34·D36 선례대로 빼는지 확인(테스트 1).

## 그대로 진행
§2-3 전편 md5, §2-5 랫클리프 20컷(모스크바 컷은 이미 봤다 — 카자흐스탄 육지 확인), progress R, 이어서 작업 4~9. 작업 6 의 상대는 새 기준선(f8e507a).

## 지적 한 가지(합격 조건 아님)
작업 1~3 을 한 커밋(`4123cf0`)에 묶었다. C5.5(한 커밋 한 의도)다. 이후 작업 4·5·6… 은 커밋을 나눈다.

## DECISIONS 후보(Fable 기록)
D70: 골든 PNG 불변 + expected_deltas 등재 원칙 재확인(결함이 있어도 사료는 고치지 않고 기록).
