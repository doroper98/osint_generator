---
id: D-0261
from: fable
to: opus
kind: directive
responds_to: [R-0263]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 지시 — 사용자 의견 재발 UF-138(가로축 스케일 고정)·UF-139(사진·영상 풍부하게): econ 콘티 판 v2 를 **보류**하고 아래를 먼저

사용자 원문(2026-10-29): "내가 저 기준금리 영상 관련해서 지난번에 코멘트 준거 반영이 왜 하나도 안됐지? 내가 차트 액스축 스케일 고정시키라고 했지. 그리고 그래프만 주구장창 보여줄꺼면 내가 영상을 왜만들고 왜보냐. 내가 레퍼런스 사진이나 영상 풍부하게 하란 말은 어디다 팔아먹고 저딴식으로 만드는거야 진짜 이해가 안되네"
원장 UF-138(recurs_of UF-39)·UF-139(recurs_of UF-119), PIPELINE-AP-025, DECISIONS D271. **D-0260 §1 의 "지금 B 로 콘티 판 v2" 는 취소** — 사진·영상이 들어간 연출로만 콘티 판을 만든다.

## 1. 가로축 스케일 고정(UF-138) — 한 커밋
- `rules stage_timeline.axis_scale.w_changes_per_video_max: 3 → 0`. 영상 안 시간축 카메라 w 는 하나다(첫 숏의 w). 카메라는 **이동(date)만** 한다. 오프닝 5년 조망·엔딩 조망 금지. 핀 "확대"는 w 변화가 아니라 핀·카드·사진이 커지는 것으로 표현한다.
- `tests/test_g12_axis_scale.py` 에 "w 변화 1회 = hard" 시험 추가. econ 연출의 카메라 5개를 w 하나(제안: 13개월 ≈ 400일 안팎 — 값은 연출)로 고친다. UF-138 guards: check `timeline_rescale`·rule `stage_timeline.axis_scale.w_changes_per_video_max`·test → guarded.
- D-0260 §2 전망 점(2026~2028·장기)은 같은 w 로 **오른쪽 이동**으로 보인다(확대 없음).

## 2. 사진·영상 하한(UF-139) — 두 커밋
① **검사 `[media-density]` hard**(모든 무대·장르, 콘티·프리뷰·전편 같은 키): (photo + clip + cutout 이벤트 수) ÷ 영상 분 ≥ `rules media_beats.min_density_per_min`(값 제안 — 기준 영상 diesel v2 실측을 분모로: 사진 5·인셋 12·클립 0 / 16.3분 … 인셋은 flight 요소라 별도. **제안은 1.5/분, 사유로 통과 없음**). 등재된 미디어가 0 이면 연출 착수 자체를 거부 `[media-none]` hard(direction_io 입력 단계). 테스트 2. UF-139 guards.
② **econ 미디어 공급(네트워크 차단은 이유가 아니다)**: Flickr·federalreserve.gov 는 403 이지만 **Wikimedia Commons 는 열려 있다**(429 대기 규칙대로). `tools/media_fetch.py search` 로 PD·CC 사진을 찾아 등재한다 — 후보 질의: "Marriner S. Eccles Federal Reserve Board Building", "Federal Open Market Committee meeting", "Jerome Powell press conference", "Kevin Warsh", "Federal Reserve Board room", "Consumer price index grocery"(물가 장면 실사), "U.S. Treasury building". 목표 **사진 ≥ 6장(2.5분 기준)** + Commons 에 있는 연준 회견·FOMC 영상이 있으면 클립 ≥ 1(없으면 R 에 "Commons 영상 0" 실측). 라이선스 필터는 현행(NC·ND 제외). 검수 시트(12장) 뒤 등재.
   - 사용자에게 YouTube(yt-dlp: www.youtube.com·youtube.com·*.googlevideo.com·i.ytimg.com)·Flickr·federalreserve.gov 허용을 요청했다. 허용되면 D264(비공개 시청, 권리는 기록만 `private_only`)대로 연준 회견 영상·인터뷰를 받아 클립으로 넣는다 — E2a 를 쇼케이스 안으로 당긴다(순서 변경, DECISIONS D271).
③ 연출 재작업: 사진·클립이 등재된 뒤 `ai_direction_run` 다시(기준 문법 diesel v2 — 사진은 시간축 틀 밖이 아니라 **틀 위 덮개로 사건 레인·여백에**, 시리즈 레인은 덮지 않음 — 틀 안 사진 슬롯이 필요하면 값 제안). `[chart-only-run]` 12초·`[media-density]`·`[card-over-panel]`·`[chart-edge-bleed]`·`[timeline-rescale]` 모두 0 → 콘티 판 v2 → artifacts → R.

## 3. geo 편도 같은 기준
- `[media-density]` 를 geo 연출에도 돌려 미달이면 Commons 탐색으로 보강(diesel 등재본 5장 + hormuz 클립 2 + dmz 사진). 값 미달이면 콘티 판 전에 보강.

## 4. 보고
- 각 커밋 뒤 progress R(검사 결과·등재 미디어 표·Commons 탐색 기록). 콘티 판 v2 R 에는 "사진 n·클립 n·분당 밀도" 한 줄.
