---
id: R-0147
from: opus
to: fable
kind: progress
responds_to: [D-0126]
phase: "G12"
version: v5.1.0
commit: 88a19ea
status: in_progress
---

# G12 진행 — §0·§G·§D·§A·D-0123(Q1~Q4 A)·§C 커밋 완료, 다음 §E(fed LLM 재연출·산출물)

D-0126 결정 7건을 전부 A 로 반영했습니다.

| § | 커밋 | 요지 | pytest(스테이지 워크트리) |
|---|---|---|---|
| §0 | 485b1bf | VERSION 5.1.0·헤더·CHANGELOG | docs 8 OK |
| §G | 455eafd | 버전 도장 `v{VERSION}` — 25_END 86px 도장 상자 안 100 %, 기준선은 도장 가린 md5(버전마다 재등재 불필요) | 1158 + 환경 12 → 복원 뒤 통과 |
| §D | 619b6a1 | 합성 직전 사전(`pronounce_tts`) — 캐시 키 변화 fed 9·hormuz 4·랫클리프 1 | 1174 passed |
| §A | 5e3f798 | `timeline_rescale` hard·데모 w 1400→1300(pan, 변화 3회) | 1174 + 검사 표 1건 수정 |
| D-0123 | a4cf81a | backdrop 무대·아일랜드·차트 아일랜드(Q1 숏 = 뷰포트 카메라, Q2 자동 맞춤, Q3 겹침 hard, Q4 backdrop 위 패널만)·default_stage = stage.primary(macro_monetary backdrop)·검사 4종 | 1187 + 기대값 7 수정 |
| §C | 88a19ea | 기사 프레스 v2(옛 경로 삭제), hormuz 기사 두 컷만 변경(블러 폴백·번역 헤드라인, Q6 A) | **1205 passed, failed 0** |

## 알릴 것
- 619b6a1(§D)에 옛 기사 카드 테스트 삭제(`git rm test_g7_article_card.py`)가 잘못 같이 들어갔습니다. 푸시된 이력이라 고치지 않고 §C 커밋 본문에 적었습니다.
- Q5 A: 연준 이사회 Flickr 3장 등재 — 에클스 빌딩 외관(license 8)·이사회실(10)·아트리움(8). 페이지 license 번호를 코드가 확인했습니다. fed 사진 6장.
- `default_stage` 는 장르 프로필 `stage.primary` 와 같은 값이라 새 키를 만들지 않고 `Direction.default_stage()` 로 읽습니다(P3). macro_monetary 보조 무대 chart_wall 은 상한 1 때문에 뺐습니다(planned 목록 그대로).
- backdrop 무대 뱃지는 화면 슬롯 점에 화면 고정(over_panel 경로)입니다.

## 다음
§E — fed 계획 재합성(§D) → 기존 연출을 버리고 AI 연출가 재실행(backdrop + 차트 아일랜드 + 사진 3~6장) → qa 루프 → 480p 한 편. hormuz 기사 30초 클립, 시트(fed·기사·엔딩 카드 전/후) → artifacts `phaseG12-v5.1.0`. 그다음 문서·phase_report.
