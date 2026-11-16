---
id: R-0322
from: opus
to: fable
kind: progress
responds_to: [D-0469]
phase: "IR4"
version: v7.4.0
commit: a2dfe93
status: open
---

# 콘티 판 v6 — D-0469 2안, 매체 13, hard 0

- artifacts `61bc634` → `iran_ceasefire_2026/animatic_v6/`
  - `animatic.mp4` 52.3 MB, md5 `7a63dc52afae79f23d9307cc60fe28ab`, 483.03초
  - `animatic_checks.json`: **hard 0**, 경고 48, passed true
  - `animatic_provenance.json`: drops 0. UF-170 forbidden 0, UF-171 element_hold 0, UF-172 media_overlap 0
  - `sheet1_cold.jpg`(0~29초 1초 간격)·`sheet2_media.jpg`(덮는 요소별 1컷·패널 장면 전부·컷어웨이 앞뒤)·MD5SUMS
- 연출 = 커밋 `a2dfe93`(direction.yaml = direction.v10.yaml).

## 1. 1안이 막힌 사실
- R-0321 의 "backdrop 은 밀도에 안 센다"는 제 오기입니다. docstring 만 보고 `MEDIA_DENSITY_TYPES` 를 확인하지 않았습니다. 감독 정정이 맞습니다.
- 다만 mercator 주 무대에서 backdrop 이벤트는 `engine/project.py:505` 가 막습니다("backdrop 이벤트는 backdrop 무대에서만 — 주 무대 'mercator'"). 엔진 수정이 필요해 2안으로 갔습니다.
- 1안용으로 받은 두 사진(셀레스철 시 9700459 — 1차 후보 9700416 은 미 해군 함정이 피사체라 버림, 기뢰 제거 구축함 9609002)은 레지스트리에만 등재했습니다(`0d86749`). 영상에는 쓰지 않았습니다.

## 2. 2안 적용
- act2_4(9/30) 컷어웨이: 파테메 모하제라니 이란 정부 대변인(Mehr, 2026-01-27, CC BY 4.0). 조사표 02 "9/29~30 govt spokeswoman" 과 같은 인물입니다. map_pair_left 에 두어 카타르 경유 경로·도하·테헤란 라벨을 비킵니다.
  - 2막 시간축은 A(act2_0~3) → 대변인 → A2(act2_5~6) → 해병대 → 레자이 → B(act2_9~12) 로 나뉩니다. 같은 record 이고, 앞 핀은 재진입 때 함께 보입니다.
  - Commons API 가 429 로 40분 넘게 막혔습니다. 그래서 1280px 썸네일을 upload.wikimedia.org 에서 직접 받고, 권리 메타는 앞선 검색 API 결과(CC BY 4.0, Fatemeh Mirahmadi, 제한 없음)를 썼습니다. 이 경위를 레지스트리 verified_by 에 적었습니다.
- 중부사령관(act5_3) 유지, act5_3→act5_4 틈 0초 수용. MODIS ending_2 유지.
- [media-burst-window] 127.2초부터 40초 3개(ISS·대변인·해병대)는 D-0469 §2 수용분입니다.

## 3. 매체 13(시각)
| 매체 | 형태 | 장면 | t0~t1 |
|---|---|---|---|
| 에픽 퓨리 | clip | act1 | 34.80~42.15 |
| 4월 봉쇄 | clip | act1 | 58.59~65.94 |
| 7월 공습 | clip | act1 | 79.90~87.25 |
| ISS 야간 해협 | photo | act2(panel_gap) | 127.20~134.80 |
| 정부 대변인 | photo | act2(컷어웨이) | 141.60~149.20 |
| 해병대 검문 | photo | act2(컷어웨이) | 162.61~170.20 |
| 레자이 | photo | act2(컷어웨이) | 171.36~178.96 |
| 아라그치 모스크바 | photo | act3 | 210.40~218.00 |
| 뉴올리언스함 | photo | act3_5 | 243.85~251.45 |
| 알바스라 유조선 | photo | act5(컷어웨이) | 312.80~320.40 |
| 중부사령관 | photo | act5_3 | 325.71~333.30 |
| 이슬라마바드 | photo | act5_8 | 356.27~363.87 |
| MODIS 해협 | photo | ending_2 | 457.86~465.61 |

모든 사진·영상의 완전 노출은 6.09~6.24초입니다(element_hold 0).

## 4. 시트 자가 대조
- cold: 0~4.6초에 지도와 경로 성장, 도하 마커는 인용 전에 보입니다. 인용 4.75~11.92초, 기사 12.02초~, 타이틀 24~28초입니다. 진입 줌은 기사 카드 뒤입니다.
- 패널: 핀·양측 조건 항목·차트 선을 덮는 사진이 없습니다. 패널 위 사진은 131초 ISS 하나이고, 상자 밑은 빈 축입니다.
- 컷어웨이 앞뒤(140.3·141.2·149.3·150.4·161.5·162.4·179.8·180.8·312.0·312.6초): 패널이 나가고 지도 반쪽에 사진, 다시 패널이 들어옵니다. 지도 라벨(도하·테헤란·호르무즈)은 사진 밖입니다.

## 5. 경고 중 눈여겨볼 것
- portrait_unused 13: 이전 판과 같습니다(뱃지 자리가 패널 위·모즈타바 초상 없음).
- media_beats 18·tempo_density 1·article_press_missing 1: 이전 판에도 있던 경고입니다.

## 6. 다음
감독 확인·사용자 보고 → 프리뷰 → 게이트 ② 재승인(감독) → 720p final_v3. 승인 명령은 치지 않습니다.
