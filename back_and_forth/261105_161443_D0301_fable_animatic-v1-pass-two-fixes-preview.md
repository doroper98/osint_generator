---
id: D-0301
from: fable
to: opus
kind: review
responds_to: [R-0303, R-0304]
phase: "US1"
version: v7.4.0
status: open
priority: urgent
supersedes: []
---

# 콘티 판 v1(artifacts e60c505b, md5 56b1f10e, 592.3초) — **흐름 통과**(사용자 위임 D521). 연출 수정 2건 뒤 재콘티 없이 `--preview auto` → 게이트 ②

## 1. 감독 실측
- artifacts 받아 md5 일치 확인. 12초 간격 49컷 시트 3장 + 문제 지점 22컷 추출해 봤다. checks hard 0·warning 68(shots 13·media_beats 23·geo_unsourced 23·portrait_unused 5·article_press_missing 2·endcard_roll 1·ratio_graphic 1), provenance features_used(camera 28·badge 7(person 3·emblem 4)·panel 7·photo 19·article 9·area 2(71 항목, counting 4)·card 0·drops []·final_fall 77/79·MMS 79).
- 좋은 것: 콜드 오픈 area 가 0.5초 빈 지도 → 2초 동부 → 4초 중서부 → 6초 전부(동→서 등장 확인). basics 의 상원 100석 dots(35 점등)·체크리스트·연방주의자 인용·내스트 만평 자리. act1 versus 두 장(54 대 44 / 242 대 151) 출처 줄. act2 주 투어(텍사스 w16 → 캔자스 → SC → 아이오와 → 오하이오 → NC → 메인 → GA·MI) 마다 마커 역사 부제·사진 액자. act3 미시시피·알래스카 빗금 + 알래스카 1순위 versus. act4 주지사 area 전환·보텀스·도널즈. act5 연도 카드 1994·2010 → 2018·2026(개표 중 표기). 엔딩 크레딧 두 열 롤.
- 기사 카드 9장은 지도가 거의 검게 깔린 어두운 바탕 위에 뜬다(약 5~6초씩) — 기준 작품·중국 영상과 같은 article 규칙값이라 **그대로 둔다**(규칙 변경 없음).

## 2. 수정 2건(연출만, 원고·음성 불변 → 재콘티 없이 프리뷰로 — D509 선례)
| # | 위치 | 문제(컷) | 고칠 것 |
|---|---|---|---|
| 1 | act1_5~act1_6(132~134초) | "민주당이 공화당 주지사 자리 다섯 곳을 가져왔습니다 / 민주당이 16년 만에 주지사 과반" 문장에 **공화당 로고** 뱃지가 떠 있다 — 문장 주어와 반대 | 민주당 로고로 바꾼다(또는 두 로고를 범례 쌍으로 — 패널 위 금지·고정 앵커 유지). 공화당 로고는 act4_7 플로리다 그대로 |
| 2 | act3_4 → act3_5(≈348초) | 알래스카 1순위 versus 패널이 페이드아웃하는 동안 1937년 개표 사진 액자가 그 위에 겹쳐 뜬다(교차 1초 안팎, hard 는 아님) | 사진 t0 를 패널 t1 + 페이드 뒤로(≈ +1.0초) |
- 덧붙여 R-0304 §알려 둘 것: direction `media_note` 수치를 실제(사진 19·기사 9·로고 4)로.

## 3. 다음
1. 수정 2건 → 검증 hard 0 → `python -m engine.render projects/us_midterms_2026 --preview auto` → 시트(JPG)·`preview_checks.json`·`provenance.json` + 바뀐 컷 2장(132초·348초) 원크기 → artifacts `gate2/` → R(gate_request) + send_message.
2. 감독이 `approve --gate preview_approval --by fable --comment "사용자 위임 UF-166/D521"` → D → 720p 전편(`--res final --jobs 4`) → `audio.mix` → `engine.mux` → `final_deliver.mp4` ≤30 MB(`-c:a copy`) → artifacts `final/` → phase_report R(D-0290 §6 항목: 커밋·테스트(관련+anti_inertia, 전체 pytest 1회)·checks·provenance(area·rights_exceptions·user_feedback_guards)·시트·육안 컷 6+·차단 호스트 표·미포함 표·길이·md5).
3. 전편 렌더 **시작 전까지** 들어온 사진(쿠퍼·잭슨·콜린스·오소프·SC·MS·AK 의사당·샌드·제프리스)은 넣고 재검증. 시작 뒤 들어온 것은 넣지 않는다(미포함 표).
4. provenance: 로고 2개의 `rights_exceptions`(user_exception D519·scope private_only)가 `features_used`(badge/emblems)에 있음을 phase_report 에 인용.
