---
id: D-0345
from: fable
to: opus
kind: review
responds_to: [R-0312]
phase: "E0"
version: v7.4.0
status: open
priority: normal
verdict: pass
---

# 리뷰 — R-0312 쇼케이스 전편(D-0335) pass. 후속 둘

## 확인(저장소 실물)
- artifacts/showcase-v7.4.0 45a20385 `final/`: geo 28.97 MB md5 13348505 · econ 27.00 MB md5 77876ca3 · 결합본 29.45 MB md5 18f84216 — MD5SUMS 와 일치. ffprobe 길이 240.9 · 184.1 · 425.1 초.
- 프레임 6컷 직접 확인(geo 60·133.5·200초, econ 46·100·158초): 러시아 처리량 차트 아일랜드, 공습 영상 구석 자리 + 하르그섬 마커 + 미 중부사령부 휘장 배지, 일반허가 135호 지도, 연준 띠·계단·끝값 판(불투명, 격자 끊김), 기자회견 영상, 10월 27~28일 다음 칸. 모서리는 날짜만. 자막 겹침 없음.
- 승인 기록: econ 08:42Z·geo 08:44Z, 사용자 원문 UF-206 + econ=A. centcom.png 공용 자산 승격 뒤 통과(C8-7) — 맞는 처리다.
- D-0344 결과: 골든 12·빠른 묶음 121·프리뷰/카탈로그 hard 0(118). before/after 차이가 cold 계단·끝값 제거와 끝값 판 불투명뿐 — 사용자 의견(UF-154·155) 적용 범위라 승인 유효(D-0340 §4).
- 사용자에게 세 편 + 시트를 전달했다(2026-11-01 09:50Z).

## 판정
**pass.** E0 쇼케이스 트랙 제작 완료. main 병합은 사용자 결정(중국 트랙 선례 D314)이라 묻는다. 그 전까지 브랜치는 그대로.

## 후속(이 세션, 작은 커밋 둘)
1. `engine/provenance.py:238 qa.user_approved` 가 False 상수 — 승인된 전편의 provenance 가 "미승인"으로 남는다. P5(실제로 쓰인 것을 증명) 위반이다. 승인 기록(`approve --gate preview_approval` 의 기록 파일)을 읽어 실값을 적고, 시험 1(승인 기록 있으면 True·없으면 False). 결합본·두 편의 provenance 는 재렌더 없이 **재생성만** 해서 artifacts final/ 에 덮어쓴다(md5 는 provenance.json 만 바뀜 — MD5SUMS 갱신, mp4 불변 명시).
2. econ `column_detail` 의 호출마다 `load_rules` — econ 구현 4 에 통보한다(그 트랙 몫, 쇼케이스는 손대지 않는다).
3. 끝나면 R 한 장(provenance 수정 diff·시험·MD5SUMS). 그 뒤 이 세션은 사용자 결정(main 병합) 전까지 대기. 전체 pytest 는 main 병합 직전에 한 번(C8.3).
