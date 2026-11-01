---
id: R-0273
from: opus
to: fable
kind: report
responds_to: [D-0270]
phase: "E0"
version: v7.4.0
commit: d96b5ae
status: done
---

# 보고 — showcase_econ 콘티 판 v2(A1) 완료 · artifacts 교체(c0e4a3f)

## 끝값 라벨 ↔ 축 눈금 라벨 (감독 지시)
- 885e41d: 끝값 라벨이 눈금 라벨과 겹치면 세로로 비킨다(기존 세로 분산). 비킬 자리가 없으면 그 눈금 라벨만 생략(눈금선은 남김). [series-label-overlap] 에 두 상자 교차를 hard 로 넣음 + 시험.
- d96b5ae: 위 수정 뒤 축이 사라진 회귀를 고침. 축을 늦게 나오는 전망 점(projection)이 맡아, 그 전까지 눈금이 없었다. 지금은 전망 점이 아닌 마지막 series 가 축을 그린다.
- 확인: 프리뷰 hard 0. 52초 컷 눈금 3~5% 보임. 94초 컷 "3.63%" 가 위로 비켜 "3.5%" 와 떨어짐.

## 콘티 판 v2
- `artifacts/showcase-v7.4.0` c0e4a3f: `showcase_econ/animatic.mp4` md5 c41a21e5. 154.25초, checks hard 0.
- v1 은 `animatic_v1.mp4`(b7ec4692)로 보존. v2_candidate 삭제. MD5SUMS·README 갱신. 12컷 시트 `animatic_v2_sheet.jpg`.
- 수치: 레인 둘(금리·기록), 금리 범위 3.0~5.0%(눈금 0.5), visible_ratio 0.688. 값 영역 64.8px, 0.25%p ≈ 8.1px.
- 실사 12(배경 5 + 사진 7) / 2.57분 = 분당 4.67(하한 1.5). 클립 0 — Commons 429, YouTube 403(우회 안 함), Brightcove 도메인 허용 대기. 전편 전 목표 그대로.
- warning: [article-unused] 3건(cold_0·act3_3·ending_0 후보 기사 미사용). 결정 아님 — 콘티 흐름 검토 뒤 media_notes 사유 또는 추가.

## 눈에 띈 것 (범위 밖 · 손대지 않음)
- 금리 선이 레인 오른쪽 끝까지 이어지는 컷(30·45·52·60초)에서 선이 눈금 라벨 "3.5%" 를 가로지른다. 읽히지만 깔끔하지 않다. 눈금 라벨 뒤 바탕 띠 또는 선 끝 여백 중 고를 일 — 필요하면 지시 바람.

## 환경
- 컨테이너에서 hormuz_korea 자산(국기·초상·사진·클립, 720p 지형 티어)이 사라져 있었다. 티어는 `geo.prep` 로 다시 만들었다. 나머지 탓에 anti_inertia 2건(test_provenance_e2e hormuz·test_q3_light_e2e) 실패 — 코드 무관, 골든 25/25 작업에서 자산 복구.

## 다음
- 사용자 흐름 검토 대기(econ v2·geo v1). 그동안 골든 25/25 자산 복구 → A/B 비교 구간.
