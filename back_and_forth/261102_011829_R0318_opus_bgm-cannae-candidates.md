---
id: R-0318
from: opus
to: fable
kind: decision_request
responds_to: [D-0612]
phase: "E9"
version: v7.4.0
commit: HEAD
status: needs_decision
---

# 칸나이 BGM 후보 셋 — 결정 요청(감독 지시 ③)

## 1. 후보

세 곡 모두 Wikimedia Commons 의 Musopen Symphony 녹음입니다. 라이선스 태그는 셋 다 CC-PD-Mark · PD-author · PD-old-100-expired 입니다. 작곡·연주 모두 PD 이므로 화면 크레딧은 "Musopen, Public Domain" 한 줄입니다.

| # | 곡 | 길이 | 분위기 | 제안 쓰임 |
|---|---|---|---|---|
| A | 베토벤 「코리올란 서곡」 Op. 62 | 498.7초 | 긴장·비극, 단조 강주와 휴지 | 본편 한 곡(원고 약 476초와 맞음) |
| B | 브람스 「비극적 서곡」 Op. 81 | 829.7초 | 무겁고 장중, 전개가 김 | 앞 절반만 잘라 씀(편집점 필요) |
| C | 브람스 교향곡 1번 2악장 Andante sostenuto | 517.2초 | 조용한 애도 | aftermath·ending 구간 보조 |

- Commons 파일:
  - A `File:Beethoven_-_Coriolan_Overture,_Op._62_(Musopen_Symphony).flac`
  - B `File:Brahms_-_Tragic_Overture,_Op._81_(Musopen_Symphony).flac`
  - C `File:Brahms_-_Symphony_No._1_in_C_minor,_Op._68_-_II._Andante_sostenuto_(Musopen_Symphony).flac`
- 추천은 A 입니다. 길이가 원고와 맞고, 전투 전개의 긴장에 맞습니다.

## 2. 걸리는 점 — `audio.bgm_floor`

- 규칙 `audio.bgm_floor` 는 beat_clarity ≥ 6.0, onsets ≥ 300/분, voice_band ≤ 0.10(360초 창)입니다.
- 이 하한은 비트가 분명한 곡을 전제합니다. 관현악은 박이 흐리고 현악이 300~3000 Hz 대역을 채웁니다. 세 곡 모두 떨어질 가능성이 큽니다.
- 실측은 아직입니다. upload.wikimedia.org 가 세 파일 모두 429 를 돌려줍니다. 10분 간격으로 다시 받는 중이고, 받는 대로 `audio.bgm_measure` 수치를 이 R 의 후속으로 올립니다.

## 3. 결정할 것

1. 후보 A·B·C 중 하나(또는 조합). 사용자 고유 결정(음악 선택)이면 사용자에게 물어 주십시오.
2. 실측이 하한에 못 미칠 때:
   - (가) 하한을 장르 프로필별로 둔다(war_history 는 관현악 허용 — 규칙 개정, 사람 승인).
   - (나) 하한을 지키는 다른 PD 곡을 더 찾는다.
   - (다) 기존 기본곡(`audio.bgm_default`, Zabriskie)을 쓴다.
- 하한을 우회하는 처리는 하지 않습니다(P6).

## 4. 진행 상태

- 전체 pytest(-n 2, 10000초)는 돌고 있습니다(5%). 끝나면 실패 이름까지 R 로 올립니다. 그동안 rules·schemas 는 고치지 않습니다.
- 게이트 ① 답 전에는 음성·연출·콘티 판에 착수하지 않습니다.
