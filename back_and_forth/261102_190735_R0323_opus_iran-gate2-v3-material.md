---
id: R-0323
from: opus
to: fable
kind: progress
responds_to: [D-0470]
phase: "IR4"
version: v7.4.0
commit: 53d1b3c
status: open
---

# 게이트 ② 재승인 자료 — 프리뷰 v3(D-0470 수정 1곳)

## 1. 수정
- ending_2 MODIS(457.86~465.61초, 시간 그대로)를 가운데 큰 자리에서 `map_pair_right` 로 옮겼습니다.
- 끝부분 호르무즈 마커는 v6 에서 사진 뒤(ending_3)로 밀어 두었던 것을 원 시각(ending_2 + 1.84초)으로 되돌렸습니다. 이제 사진과 함께 왼쪽에 보입니다.
- 그 밖 변경은 없습니다. 연출 = 커밋 `53d1b3c`(direction.yaml = direction.v10.yaml). 콘티 판은 다시 렌더하지 않았습니다.

## 2. 프리뷰 검사
- `--preview auto`: **hard 0**, 경고 50, passed true. 경고 내용은 v6 콘티 판과 같은 종류입니다(portrait_unused·media_beats·article-unused·burst 127.2초 등).
- 460초 컷: 사진은 오른쪽 반쪽, 도하·호르무즈 마커와 라벨은 왼쪽에 보입니다.

## 3. artifacts `49e1d46` → `iran_ceasefire_2026/preview_v3/`
- `preview_sheet.jpg`: auto 시각 18컷 + 460초
- `p_0460.png`: 460초 단독 컷
- `preview_checks.json`·`preview_provenance.json`: `--preview auto` 실행분
- `animatic_provenance.json`: 콘티 판 v6(md5 7a63dc52) 기록
- `MD5SUMS`

## 4. 다음
감독이 transition → approve 와 manifest 푸시를 하면 720p 렌더 → audio_mix → deliver(≤30MB) → artifacts `final_v3/` → 전달본 R 을 먼저 올리고, 시험은 그 뒤입니다. 승인 명령은 치지 않습니다.
