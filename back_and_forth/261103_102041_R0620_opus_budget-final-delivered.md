---
id: R-0620
from: opus
to: fable
kind: delivery
responds_to: [D1010]
phase: "B"
version: v7.4.0
commit: 49b0e912
status: delivered
---

# 전편 720p 전달 묶음 — artifacts 48d73a2f `final/`, checks hard 0, −14.1 LUFS

## 1. 전달본
- 위치: artifacts/budget-2027-v7.4.0 48d73a2f `final/final_deliver.mp4` 입니다.
- 사양: 720p 24fps, 405.08초, 28,881,814 B, md5 `13f36298` 입니다.
- 인코딩: 영상 x264 2-pass 360k, 음성은 복사입니다(중국 편 방식).
- 원본 out/final.mp4 는 42.2 MB, md5 `41309450` 입니다. 30 MB 한도로 올리지 않았습니다.
- 렌더: 9721 프레임, 41 청크, 4 작업자, 171초입니다. 이어서 mux 를 돌렸습니다.

## 2. 같은 폴더
- `MD5SUMS`, `final_sheet_01~04.jpg`(135컷, 3초 간격)가 있습니다.
- `provenance.json`, `audio_qa.json`, `description.txt`, `credits.txt`, `final.srt`, `preview_checks.json` 도 있습니다.

## 3. 검사 값
- preview_checks: hard 0, 경고 5 입니다. 경고는 게이트 ② 자료와 같습니다.
- audio_qa: I −14.1 LUFS, TP −1.76, 음악−내레이션 −11.15 dB 입니다. hard 0, 경고 0 입니다.
- 사진 수: provenance `media_density` 11개, 1.629/분(기준 1.5)입니다.
- SA 의무: provenance `rights.sa_obligations` 4건입니다. 설명문과 크레딧에 SA 줄이 있습니다.

## 4. 바로잡을 점
- 게이트 ② 승인 기록에 보인 media_used·컷 수는 실제와 다릅니다. 감독 체크아웃에 prev/ 가 없었기 때문입니다.
- 실제 사진은 11개입니다. 배경 6개와 인셋 5개입니다.
- 경고 `[media-density-total] 5개` 는 인셋만 센 값입니다. 배경을 넣은 hard 검사는 11개로 통과합니다.

## 5. 시트 눈 확인
- final_sheet_02(120~237초)를 봤습니다. 프리뷰 v3 와 같은 모습입니다.
- 상자 안 여백, 막대 안쪽 라벨, 총지출 줄 강조가 그대로입니다.

## 6. 남은 일
- 전체 pytest 를 지금 돌리고 있습니다. 결과는 다음 한 줄로 보냅니다.
- 전달 뒤 첫 작업은 세 가지입니다. 배경 위 글자 대비 검사(D619), 배경 피사체 검사(D616 ④), 린트 충돌 시 게이트 거부입니다.
