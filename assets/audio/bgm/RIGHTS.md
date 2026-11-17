# bgm/ 권리 기록 (C9)

> **v3.4.0 — 기계가 읽는 SSOT 는 `registry.yaml` 이다**(D-0060 작업 1). 이 문서는 사람용 설명으로 남긴다. 엔딩 카드·설명란 음악 문구, direction `sound.bgm` id, 권리 대조는 전부 레지스트리를 쓴다.

영상 배경음악. 외부 음원은 반드시 출처·라이선스를 기록한다.

| 파일 | 출처 | 라이선스 | 출처표시 의무 | 영상 적용 |
|---|---|---|---|---|
| The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3 | YouTube 오디오 보관함 | **CC BY 4.0** | **필수** | ✅ 사용중 |
| Take Off and Shoot a Zero - Chris Zabriskie.mp3 | YouTube 오디오 보관함 | CC BY 4.0 | 필수 | 미사용 |
| Drone in D - Kevin MacLeod.mp3 | YouTube 오디오 보관함 | CC BY 4.0 | 필수 | **사용 금지**(작가 Content ID 사전 등록 공지, v7.2.0 D-0222) |
| Mario Bava Sleeps In a Little Later Than He Expected To - Chris Zabriskie.mp3 | archive.org 미러(작가 Bandcamp 는 이 환경 403) | **CC BY 4.0**(작가 공식 https://chriszabriskie.com/use/ 2026-10-12 확인) | **필수** | ✅ 새 영상 기본(사용자 청취 합격 UF-100) |

## CC BY 4.0 출처 표시 의무
- 사용중인 곡(Zabriskie Patriarch)은 영상 하단 출처 라인 + **유튜브 설명란**에
  "Music: Chris Zabriskie (CC BY 4.0)" 또는 작가가 지정한 문구를 넣어야 함.
- 작가 표준 표기(작가 요청 형식, 앨범 포함 — v7.2.0 D-0222): `"The Life and Death of a Certain K. Zabriskie, Patriarch" by Chris Zabriskie / From the album Vendaface / Licensed under Creative Commons Attribution 4.0 / creativecommons.org/licenses/by/4.0/ / chriszabriskie.com`
- Mario Bava 표기: `"Mario Bava Sleeps In a Little Later Than He Expected To" by Chris Zabriskie / From the album Vendaface / Licensed under Creative Commons Attribution 4.0 / creativecommons.org/licenses/by/4.0/ / chriszabriskie.com`

## 저장소 보관 주의
- 음악 파일(31~51MB)은 .gitignore 대상이나 본 건은 전달 위해 임시 커밋됨.
- 운영 안정 후 git history 정리(BFG/filter-repo) 또는 LFS 전환 권장 — repo 비대화.

## v2.0.1 — 추적 해제 (DECISIONS D22, back_and_forth D-0005)
- 사용중 곡 mp3 는 git 추적에서 뺐다(작업 트리 파일은 유지). 이력 정리·LFS 는 하지 않는다.
- 복원: `python tools/fetch_data.py bgm` — git 객체 `bd37b58`에서 꺼내 sha1 대조.
- sha1 `c0ddb7b38ee7866c32d2510a84125cf611a54e93`, 길이 931.8초(ffprobe).

## v7.2.0 — Mario Bava 등록 (UF-100, D-0222)
- 사용자 청취 판정(2026-10-12): "1번만 합격. 약간 박진감이 느껴지는 부분에서 점수를 줬어."
- 파일: archive.org `chris-zabriskie-complete-discography` 미러(사용자가 들은 파일과 같은 바이트). sha1 `02ceb4e748b003fb7447ccd74b0ccf4fad64d3fb`, 길이 511.27초(ffprobe).
  같은 곡의 다른 미러(`vendafacebychriszabriskie` 320k, sha1 2434e205…)는 바이트가 달라 쓰지 않는다.
- 작가 배포처(Bandcamp)는 이 환경에서 403 — 받지 못한 사실과 사유를 여기 남긴다. 라이선스 근거는 작가 공식 페이지(모든 곡 CC BY 4.0, 크레딧 필수, 수익 영상 허용).
- 복원: `python tools/fetch_data.py bgm`(레지스트리 source_url → sha1 대조).
- 실측(audio.bgm_measure, 0~360초): 박 명확도 6.55 · 온셋 분당 473.5 · 300~3000 Hz 8.8 % — 등록 하한 rules audio.bgm_floor 통과.

## v7.4.0 — 사용자 제공 곡 "두 개의 악기"(UF-910, D922)
- 파일: `두 개의 악기 - _yk.mp3` — 사용자가 세션에 올린 파일(2026-11-17). 파일 태그: 제목 "두 개의 악기", 작가 `_yk`, `made with suno`(id 351e4e60-1737-479b-9a65-a4282e0c20d6), 연주곡. sha1 `c18ed525ab6f7a86d1930310344f7e373dda85be`, 길이 189.94초.
- 권리: Suno 생성물의 상업 이용 권리는 만든 시점의 요금제 약관에 따른다 — **사용자 확인 전이라 `available: false`**. 확인되면 레지스트리 license·available 을 고친다.
- 실측(audio.bgm_measure): 박 명확도 4.12 · 온셋 분당 263.8 · 300~3000 Hz 32.2 % — 등록 하한(rules audio.bgm_floor) 셋 다 미달. 내레이션 대역 비중이 커서 말소리와 겹칠 수 있다(음악 베드 음량·덕킹으로 확인 필요).
- 파일은 git 추적 대상이 아니다(.gitignore). 보관 방식(저장소 이력에 넣을지)은 사용자 결정 대기.
- **사용자 확인(2026-11-17, D923)**: 무료 요금제로 만든 곡 → **비상업 이용만**. 레지스트리 `noncommercial: true` — 연출 `sound.noncommercial_ok` 에 "이 영상은 수익화하지 않는다"는 사용자 결정 번호가 없으면 쓸 수 없다(연출 스키마·믹서 둘 다 오류). 수익화 영상에 쓰려면 유료 요금제에서 새로 만든 곡이 필요하다(무료 요금제에서 만든 곡은 나중에 유료로 바꿔도 조건이 따라오지 않는 것으로 안다 — 쓰기 전 Suno 약관 확인).
- 사용자 결정: 저장소에 보관(.gitignore 예외로 이 파일만 추적), 등록 하한 면제(`floor_waiver`), 이 곡만 음량을 낮춰 쓴다(`bed_gain_scale: 0.56` = sqrt(0.10 ÷ 0.322), 약 −5 dB).

