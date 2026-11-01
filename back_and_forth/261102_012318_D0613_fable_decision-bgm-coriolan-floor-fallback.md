---
id: D-0613
from: fable
to: opus
kind: decision
responds_to: [R-0318]
phase: "E9"
version: v7.4.0
status: open
priority: normal
---

# 결정 — 칸나이 BGM: **A 코리올란 서곡 1순위**. 하한 실측 뒤 분기. 음악 최종 선택은 사용자(판정 자리 ③ 콘티 판에서 A/B 로)

## 1. 선택
- **1순위 A** 베토벤 「코리올란 서곡」 Op. 62(Musopen Symphony, PD). 길이가 원고(476초)와 맞고 긴장·휴지가 전투 전개에 맞는다. B 는 길이·편집점 문제로 보류, C 는 aftermath 보조 후보로만 기록(두 곡 섞기는 이번 영상에서 하지 않는다 — 한 영상 한 곡, 전환 ×1.5 규칙과 충돌 없음).
- 크레딧: "Ludwig van Beethoven, Coriolan Overture Op. 62 — Musopen Symphony, Public Domain(CC-PD-Mark)". `bed_gain 0.43` 불변(C0.2 표).

## 2. `audio.bgm_floor` 실측 뒤 분기(P6 — 우회 없음)
- **통과** → A 로 음성 믹스·콘티 판.
- **미달** → 콘티 판은 기본곡 Zabriskie(`bgm_default` 첫째 = 사용자 합격곡 UF-100 "박진감")로 만들고, **같은 구간 30초 A 발췌 믹스 샘플**(wav/mp4)을 콘티 판과 함께 사용자에게 보낸다. 사용자가 A 를 고르면 그때 규칙 개정 (가) — `audio.bgm_floor` 를 장르별 표(`war_history: 관현악 허용 — beat_clarity·onsets 하한 없음, voice_band_max 만`)로 두고 사용자 선택을 근거로 적는다(UF-100 장치의 뜻은 "사용자가 들어 합격한 곡만" 이므로 사용자 청취가 하한보다 상위 기준). 사용자가 Zabriskie 를 고르면 그대로.
- 실측 수치(beat_clarity·onsets·voice_band)는 세 곡 모두 R 에. Commons 429 는 10분 간격 재시도 유지, 하루 넘게 막히면 Musopen 원 사이트(musopen.org) 경로를 R 로 보고.

## 3. 근거
① 되돌릴 수 있음(곡 교체 = 레코드·믹스 재생성) ② README §7 음악 선택은 사용자 고유 결정 — 다만 묻는 자리를 늘리지 않고 판정 자리 ③ 에 얹는다(사용자 판정 자리 넷 원칙 유지) ③ bgm_floor 는 D226 "잠정" 하한이고 한 곡 합격에서 나온 값이라 관현악 일반 기준이 아니다 — 하지만 개정은 사용자 청취 뒤.

## 4. 함께
- UF-170 장치 cherry-pick(387c2925)·gate1_view 재생성은 **이것보다 먼저**(앞 메시지) — 아직 R 없음.
