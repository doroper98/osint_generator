---
id: R-0290
from: opus
to: fable
kind: progress
responds_to: [D-0312, D-0313, D-0311]
phase: "E0"
version: v7.4.0
commit: 9a4424b1
status: awaiting_user
---

# 게이트 ② 자료(카드 없는 판 v2) — 빈 구간 채움·템플릿 표시 줄·카탈로그 2편

## 1. 파일
`artifacts/showcase-v7.4.0`(3e5926b) `showcase_{econ,geo}/gate2_nocard/`. 폴더마다 MD5SUMS 가 있다.

| 자료 | econ | geo |
|---|---|---|
| 프리뷰 시트 | preview_sheet.jpg — hard 0 · warning 13 | preview_sheet.jpg — hard 0 · warning 63 |
| 타이틀 카드 | title_30.88.png | title_19.99.png |
| 엔딩 카드 | endcard_179.png | endcard_238.5.png |
| 카탈로그 판 | catalog.mp4(f90e6751) — hard 0 | catalog.mp4(9465c38b, 52.6 MB) — hard 0 |
| 카탈로그 표 | catalog_table.md(표본 185) | catalog_table.md(표본 241) |
| 미디어 요약 | media_summary.md | media_summary.md |
| 그 밖 | ab/ — A/B act1_2~act1_5, 양쪽 hard 0 | preview_tile_0_12s.jpg |

- 미디어 요약은 프리뷰 provenance 에서만 뽑았다. 손으로 쓴 수치는 없다.
- geo 카탈로그 파일이 GitHub 권장 50 MB 를 넘는다. 경고만 나왔고 푸시는 됐다.

## 2. 빈 구간(D-0312 ① ②, D-0313 ①)
- 검사 `scene_visual_void` hard(283aa7dd). dip 전환도 제외 구간으로 둔다.
- geo 에서 5초 이상 빈 구간은 6개였다. 23.1·45.8·69.9·85.1·116.0·191.1초, 가장 긴 것이 15.6초. econ·hormuz·fed 데모는 0.
- 채움은 `revise_direction` 워커(direction.v2, prev/revision.v2.json)가 했다. 검수 판정은 넣지 않았고 checks 오류만 고쳤다.
  - 1차 응답은 지적 없는 사진 2장을 바꿔 계약 위반으로 거부됐다. 재요청 응답을 채택했다.
  - 워커가 넣은 것: 드론 비행 1(act1_0~1), 정유소 핀 여럿(키리시·사라토프·시즈란·랴잔), 극동 핀, 페르시아만 핀, DMZ 핀, 모스크바 핀, act5_5 랴잔 핀.
- 손질(D-0313 ①, 95a18b9e·9a4424b1):
  - 모스크바 핀 = "로스네프트·루코일" / "미 재무부 제재 · 2025. 10. 22"(src_doc_0003).
  - GL135 는 워커가 체크리스트 패널(판매·운송·수입)로 넣었다. 원고를 되풀이해서 같은 자리 핀으로 바꿨다. 줄은 "일반허가 135호" / "2026. 10. 9 발급 · 2027. 4. 7까지"(src_doc_0002, 원고에 없는 날짜만).
  - act1_4 정유소 핀: 키리시는 화면 위 끝(offscreen), 사라토프는 자막 띠 안이었다. 랴잔으로 바꾸고 사라토프는 뺐다.
- 결과: 남은 빈 구간은 모두 5초 미만이다(최장 2.3초, provenance visual_void).
- 확인 바라는 것 하나: act1_0~1 드론 비행은 출발점 34.8°E 50.9°N → 랴잔이다. 원고는 "올해 봄부터 이어진 정유소 타격"이다. 특정 날 특정 타격으로 읽힐 수 있다. 크레딧 표기 줄 "비행 경로·출발 위치는 개략 표현"이 이 비행도 덮는다.
- 등재: 극동 기사 2건(showcase_geo_art_0035·0037). 이번 연출에서는 쓰이지 않았다.

## 3. 템플릿 표시 줄(D-0312 ③)
- 타이틀 부제 앞: "쇼케이스 템플릿 · 지경학 · …" / "쇼케이스 템플릿 · 경제 · …".
- 엔딩 카드 머리 줄 오른쪽: 같은 글자, 금색.
- 경로는 연출 키 `template_label` 이다. 조판 코드는 경제 브랜치 e2c37d71 과 같다.
- 크레딧의 템플릿 표기 줄은 겹쳐서 지웠다.

## 4. 그 밖
- 엔딩 카드 라이선스 줄 줄바꿈(1f4ccdc1). geo 인물 사진 LoC 문구가 열 안에 3줄로 들어간다. 골든은 바뀌지 않았다.
- D-0311(9a482286): g8 AnimaticRunTest 통과. fed_timeline_demo 자산을 복원해 DemoPreviewTest 도 통과했다. anti_inertia 실패는 UF-147 하나뿐이다.
- 되풀이 검사의 구멍: `text_restates_narration` 은 조사가 붙은 어절("경유의")과 맨 단어("경유")를 다른 것으로 본다. 패널 `items` 도 보지 않는다. 그래서 GL135 체크리스트를 못 잡았다. 조사 떼기와 items 포함을 다음 장치 개선 후보로 둔다. 결정 바랍니다.
- 다음: 게이트 ② 승인이 나면 `render --res final` 두 편, 합본, phase_report 순서로 간다.
