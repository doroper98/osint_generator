# bgm/ 권리 기록 (C9)

> **v3.4.0 — 기계가 읽는 SSOT 는 `registry.yaml` 이다**(D-0060 작업 1). 이 문서는 사람용 설명으로 남긴다. 엔딩 카드·설명란 음악 문구, direction `sound.bgm` id, 권리 대조는 전부 레지스트리를 쓴다.

영상 배경음악. 외부 음원은 반드시 출처·라이선스를 기록한다.

| 파일 | 출처 | 라이선스 | 출처표시 의무 | 영상 적용 |
|---|---|---|---|---|
| The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3 | YouTube 오디오 보관함 | **CC BY 4.0** | **필수** | ✅ 사용중 |
| Take Off and Shoot a Zero - Chris Zabriskie.mp3 | YouTube 오디오 보관함 | CC BY 4.0 | 필수 | 미사용 |
| Drone in D - Kevin MacLeod.mp3 | YouTube 오디오 보관함 | CC BY 4.0 | 필수 | 미사용 |

## CC BY 4.0 출처 표시 의무
- 사용중인 곡(Zabriskie Patriarch)은 영상 하단 출처 라인 + **유튜브 설명란**에
  "Music: Chris Zabriskie (CC BY 4.0)" 또는 작가가 지정한 문구를 넣어야 함.
- 작가 표준 표기: "The Life and Death of a Certain K. Zabriskie, Patriarch by
  Chris Zabriskie — Licensed under CC BY 4.0 — https://chriszabriskie.com"

## 저장소 보관 주의
- 음악 파일(31~51MB)은 .gitignore 대상이나 본 건은 전달 위해 임시 커밋됨.
- 운영 안정 후 git history 정리(BFG/filter-repo) 또는 LFS 전환 권장 — repo 비대화.

## v2.0.1 — 추적 해제 (DECISIONS D22, back_and_forth D-0005)
- 사용중 곡 mp3 는 git 추적에서 뺐다(작업 트리 파일은 유지). 이력 정리·LFS 는 하지 않는다.
- 복원: `python tools/fetch_data.py bgm` — git 객체 `bd37b58`에서 꺼내 sha1 대조.
- sha1 `c0ddb7b38ee7866c32d2510a84125cf611a54e93`, 길이 931.8초(ffprobe).
