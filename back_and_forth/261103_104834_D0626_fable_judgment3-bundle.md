---
id: D-0626
from: fable
to: opus
kind: directive
responds_to: [UF-256, UF-255, R-0327]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 지시 — 판정 ③ 묶음: 음악 = 코리올란(UF-256) + 진형 가운데(UF-255, D-0625) + 날짜(D-0622) + 지도 가림. rollback → 게이트 ① 재승인 → 콘티 판 v2

## 0. 사용자 답(판정 ③)
- UF-255(D-0625 진행 중): "그리고 군대의 진형(칸나이 전투 같은)은 중앙에 위치하게 해야 되는데 칸나이 전투 마지막 쯤에는 왼쪽 상단에 위치하더라고"
- UF-256: "coriolan" — 감독이 견본 둘과 수치를 설명하고 Zabriskie 를 권한 뒤의 선택이다. 코리올란 실측은 박자 선명도 3.69, 분당 시작 75.3, 목소리 음역 0.630 이다. D-0613 에서 "코리올란을 고르면 전쟁사 장르 하한을 개정한다"고 미리 알렸다. 이 선택을 **장르 하한 개정의 사람 승인**으로 본다(C11 P11).

## 1. 음악(UF-256)
1. **등록.** `assets/audio/bgm/registry.yaml` 에 코리올란을 올린다. 항목: 파일, sha1, duration, 출처 URL(archive.org MusopenCollectionAsFlac), 라이선스(Public Domain, CC-PD-Mark), attribution("Ludwig van Beethoven, Coriolan Overture Op. 62 — Musopen Symphony, Public Domain"), measured 세 값. 공용 자산 규칙(C8 7)대로 권리 기록과 함께 둔다.
2. **장르 하한.** `audio.bgm_floor` 공통 값은 그대로 둔다. 전쟁사 장르 몫만 따로 둔다(예: `audio.bgm_floor_by_genre.war_history`). 값은 코리올란 실측을 근거로 정하고 주석에 UF-256 을 적는다.
   - 장르 하한으로만 등록된 곡을 다른 장르 영상에 쓰면 오류다. 레지스트리에 장르를 적고 검사로 막는다.
   - 등록 오류(audio/registry.py)는 장르 하한을 읽게 고친다. 조용한 예외 처리는 넣지 않는다.
3. **내레이션 명료도 장치(가림 위험 보완).** 하한을 푸는 대신 실제 믹스에서 잰다.
   - 새 check(예: `narration_clarity`, hard, 모든 장르): 내레이션 구간마다 목소리 음역(rules voice_band_hz)에서 내레이션 대 베드 에너지 비(dB)가 규칙 하한 이상이어야 한다.
   - 하한 값: 사용자 합격 믹스(Zabriskie 콘티 판 v1, 기존 합격 영상)가 통과하는 값으로 정하고 근거를 R 에 적는다.
   - 코리올란 믹스가 실패하면 bed_gain 0.43 은 건드리지 않는다(C0.2 고정). 덕킹 깊이 등 다른 값을 바꿔야 하면 바꾸기 전에 `decision_request` 를 올린다.
4. **배치.** direction `sound.bgm` = 코리올란. order.yaml `decisions.bgm` = 사용자 결정(UF-256). 곡의 시작 지점·끝 페이드는 연출 몫이다(P8). 양익 포위(encirclement) 구간과 곡의 긴장 구간이 어떻게 맞물리는지 R 에 시각 표로 적는다.
5. 크레딧(credits.yaml)에서 Zabriskie 를 빼고 코리올란을 넣는다. 크레딧 검사 [credit-garbled] 를 다시 돌린다.

## 2. 함께 묶는 것
- **진형 가운데**(D-0625): 장치 formation_centered 먼저, 그다음 연출.
- **날짜**(D-0622 (가)): deployment_9 date = `-300~-201`. 날짜 표지 장치(v1 "2026. 11. 01" 실패, 같은 대상 날짜 맞춤 통과)를 넣는다. 시험 설명에 "같은 대상일 때만 날짜 맞춤" 한 줄을 넣는다.
- **지도 가림**(R-0327 §4): 276.9초 30초 창 66% → 0.5 이하. 사료 인용 둘은 남긴다.
- **원장 장치**: UF-255 guards = formation_centered + 시험. UF-256 guards = 장르 하한 규칙 키 + narration_clarity + 레지스트리 장르 검사. 둘 다 guarded 로 바꾼다(감독이 확인한다).

## 3. 순서(게이트 장치 우회 없음)
1. 위 장치·연출·음악 등록을 커밋한다. 원고 수정 전에 끝낼 수 있는 것은 먼저 한다.
2. `rollback`(사유: "D-0622 (가) 재현 고지 문장 날짜 = 비석 연대, 문장 글자 불변") → script.yaml 의 deployment_9 date 수정 → gate-view 재생성. R 에 바뀐 줄 전/후와 새 원고 지문을 적는다.
3. **여기서 멈춘다.** 감독이 사용자에게 게이트 ① 재승인을 받는다. 승인 전에는 콘티 판 v2 를 렌더하지 않는다.
4. 승인 뒤: 표준 음성은 글자가 같으므로 다시 만들지 않는다(plan 지문이 바뀌면 그 이유를 적는다) → `audio.mix`(코리올란) → 콘티 판 v2(표준 FONTCONFIG) → artifacts `war_history/cannae_216bc/animatic_v2/` → R(checks·provenance·narration_clarity 값·formation_centered 결과·대표 프레임).
- 감독은 v2 를 실물로 보고 사용자에게 보낸다. 그 뒤가 게이트 ②(판정 ④)다.

## 4. 보충(01:50Z, 최종 감독 조건 셋)
1. 전쟁사 장르 bgm 하한은 사용자 결정 UF-256 의 결과다. 규칙 주석에 원문("coriolan")과 UF 번호를 남긴다. 장르 키로만 갈린다는 것을 시험으로 고정한다. 다른 장르의 하한(`audio.bgm_floor`)이 그대로인지 시험이 확인한다. bed_gain 0.43 불변.
2. narration_clarity 를 모든 장르 hard 로 걸기 전에 실측표를 R 에 붙인다. 대상은 호르무즈 골든, 쇼케이스 geo·econ v3 콘티 판(artifacts/showcase-v7.4.0 5aade897 v3_animatic), 이란 final_v3b, 칸나이 v1·v2 다.
   - 골든은 반드시 통과해야 한다.
   - 사용자가 받아들인 영상이 하나라도 걸리면 임계를 정하기 전에 `decision_request` 를 올린다.
3. narration_clarity 는 검사 + 규칙 키 + 시험만 담은 **단독 커밋**으로 만들고 해시를 알린다. 다른 브랜치 전파는 최종 감독이 한다.
