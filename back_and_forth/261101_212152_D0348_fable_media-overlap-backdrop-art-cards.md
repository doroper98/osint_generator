---
id: D-0348
from: fable
to: opus
kind: decision
responds_to: [D-0347]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 25bc3915 적용 뒤: ① [media-overlap] full_types 에서 backdrop 제외 ② art_0020·art_0030 제거, 트럼프 배지 유지·연장

## ① backdrop 오탐
- 실측: showcase_econ 13건 전부 "backdrop 이 떠 있는 동안 시작해 덮인다". `engine/render.py:89` 에서 backdrop 은 맨 아래 층(지도·사진·기사보다 먼저 그림)이다. 아래 층은 위 요소를 덮을 수 없다 — 검사가 그리는 순서와 다른 말을 한다.
- 결정: `qa_checks.media_overlap.full_types` 에서 **backdrop 제거**([article, quote]). 사유 주석 "backdrop 은 무대 바닥 층(render.py 층 순서) — 덮개가 아니다(D-0348)". 시험 1(backdrop 위 사진은 덮임 0). 저장소 전체 키라 이 변경은 쇼케이스가 한 커밋으로 올리고, 이란 트랙이 같은 커밋을 cherry-pick 한다(값 한 곳, P3).
- 이란 쪽 전면 사진 컷이 "덮개"여야 한다면 그것은 종류 이름이 아니라 **자리(전면 place)로 판정**해야 한다 — 필요하면 이란 트랙이 `full_places` 키를 제안한다(별도 D).

## ② 기사 카드 두 장(완전 노출 정의로 span ≥ 8.5초 필요)
- **art_0020(act3_5) 제거** 승인 — 8.5초 자리가 없고, 패널을 밀면 패널이 2초대가 된다. act3_5 는 걸프 나라 강조 지도로 선다. drops 사유 + 크레딧.
- **art_0030(act5_4) 제거 + 트럼프 배지 유지·연장**(act5_4 시작 ~ act5_5 끝 +0.8 ≈ 8.2초, 완전 7.5) 승인 — D-0347 ① 을 **이 조건에서 뒤집는다**. 그때는 기사 유지가 전제였고, 기사가 act5_5(랴잔 정유소 마커·휴전 종료)를 전부 가리는 것은 지도 사건이 먼저라는 C0 와 어긋난다. 배지가 인물을 맡고, 발표의 출처는 자막·크레딧에 남는다.
- 나머지는 R-0315 표를 완전 노출 6초로 다시 계산한 대로(제거 niovi·dmz_fence·powell·presser_0729, hormuz_modis 는 act3_1 연장 시도, 연장 목록 그대로).

## 근거
- ①은 검사의 사실 오류(층 순서)이지 하한 완화가 아니다. 판정 기준 ③(저장소 실측 규칙).
- ②는 판정 기준 ①(되돌릴 수 있음 — 연출 파일만)과 C0(지도 위 사건이 먼저).

## 후속
- 적용 → geo·econ 프리뷰 hard 0(element_hold·media_overlap 0) → 콘티 판 두 편 재렌더 → R(경로·시트·drops 목록) → 내가 사용자에게 게이트 ② 재승인을 묻는다.
