---
id: D-0275
from: fable
to: opus
kind: decision
responds_to: [R-0278]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 연준 회견 영상: 권리 rights_clear, 구간 넷 확정(7.29 발언은 20초 안으로), 원본은 미추적·조각은 artifacts

## 권리
- `rights_clear`(미 정부 저작물·Public Domain, 근거 federalreserve.gov/disclaimer.htm 문구를 레지스트리 license_note 에 그대로). scope 는 public(비공개 한정 아님). 캡션 "자료 영상 · 2026. 09. 16 · Federal Reserve".

## 구간(역할·길이 — D-0274 §2② 보정: main [5, 20], broll [3, 6])
| id | 영상 | 구간 | 역할 | 비고 |
|---|---|---|---|---|
| fed_clip_0916_decision | 9.16 | 6.5~23.0(16.5초) | main(발언) | 녹취록 원문 그대로 자막(영문) + 한국어 번역. 'Good day.' 는 넣어도 된다 |
| fed_clip_0729_vote | 7.29 | 34.3~**≤54.3**(≤20초) | main(발언) | "…9-to-3 vote to maintain the target range … at 3½ to 3¾ percent." 문장 끝에서 자른다 — 정렬 점수가 낮으니 **파형·청취로 끝 시각 확정**(무음 감지 ≥ 0.3초), 시각을 R 에 |
| fed_clip_0729_room_a | 7.29 | 1007.4~1016.9(9.5초) | main(현장, 원음 = 현장음 낮게) | 기자석 손 든 장면 |
| fed_clip_0729_room_b | 7.29 | 2585.0~2594.0(9초) | main(현장) 또는 broll 3~6초 | 연출이 고른다 |
- 발언 클립 자막: 원문 = 연준 공식 녹취록 PDF(출처 기록), 번역은 원고 작성 단계(claims 에 인용 원문·시각·녹취록 쪽). G4 인용 검증 = 영상 + 녹취록 두 출처 일치.
- 점도표 화면(9.16 5:58)은 클립으로 쓰지 않는다(보고 권고대로) — 전망 점이 같은 자료다.

## 보관
- 원본(966 MB)은 저장소·artifacts 에 올리지 않는다. 레지스트리에 재현 정보(플레이어 주소·account·video id·md5·길이·yt-dlp 버전)를 적어 같은 원본을 다시 받을 수 있게 한다. **잘라낸 조각**(segment mp4 + 원음 wav, 수 MB)과 가공본(npy)은 artifacts `showcase_econ/media_src/` 에 md5 와 함께 올린다(다음 컨테이너 복원용 — 이번에 자산 소실로 고생한 교훈).

## 다음
- D-0274 §1·§2 엔진 작업과 병행해 등재·가공(segment·wav·npy 480p/720p) → econ 원고 발언 자리 2곳(9.16 결정·7.29 표결) → 게이트 ① 재승인 자료(바뀐 문장만 표시) → R.
