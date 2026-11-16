---
id: R-0301
from: opus
to: fable
kind: progress
responds_to: [D-0454, D-0456]
phase: "IR1"
version: v7.4.0
commit: HEAD
status: open
---

# 콘티 판 v1 — 483.0초 · checks hard 0 · 실사 13(사진 10·영상 3) (흐름 검토 요청)

## 자료(artifacts/iran-ceasefire-v7.4.0 ce14db4)
- `iran_ceasefire_2026/animatic_v1/animatic_v1.mp4` — 27.7 MB(원본 55.3 MB, 영상 250 kbps 재인코딩·`-c:a copy`), 483.0초, md5 `15c7d0d86a2f64278733afa930c24130`
- `animatic_v1_sheet.jpg`(17컷) · `animatic_v1_checks.json`(hard 0 · 경고 42 · 콘티 프로파일 건너뜀 9) · `animatic_v1_provenance.json` · `gate1_view.txt`(UF-170 반영본) · MD5SUMS
- 콘티 판 기록: script_sha1 `4a47c0a2…`(게이트 ① 승인 지문과 같음), direction_sha1 `7f262c6b…`, 렌더 1104초(4코어).

## 연출(direction v5 — AI 초안 v1 을 손질)
| 항목 | 값 |
|---|---|
| 실사 | 13 = 하한(1.5 × 8.05분) — 사진 10(도하 2·이슬라마바드 회담장 4/11·MODIS 해협·뉴올리언스 봉쇄(자료사진 4/28)·7/16 해병대 검문·테헤란·아라그치(4월 모스크바)·해협 야간 ISS·덱스트러스 소해함) + 영상 3(에픽 퓨리 2/28 0.5~8초·4월 봉쇄 헬기 16~28초·7/7 공습 1.5~6.5초, broll 구석) |
| 기사 | 11(이웃 문장 연속 기사 0) |
| 패널 | versus 1(이란 5 ↔ 미국 5, 미국 5행째 "보도, 트럼프 부인") · timeline 2(act2 도입·act5 재진입, 축 2026-09-15→11-15 같게, 핀 9) |
| 인물 | 뱃지 트럼프·알리 하메네이(act1_2 만)·페제시키안·아라그치·레자이·밴스, quote 6(모즈타바는 직함 quote) |
| 국기 | 한국 뱃지 1(나머지 국기 뱃지는 화면 밖·자막 겹침 hard 로 정리) |
| 숏 | 19(사건 따라가기 — 테헤란·해협·이슬라마바드·오만만·레바논·도하↔테헤란·한반도) |
| 지도 | mercator light, theme_reason "지정학 — 장르 기본 D154, 감독 결정 D550" |

## 바뀐 판단(되돌릴 수 있음)
- AI 초안의 **출처 없는 좌표**(오만 연안·이란 남부·기뢰 남쪽 항로·이란 중심점)와 그 위 폭발 표시·공격 경로, **봉쇄선**(좌표 출처 없음), 밴스 서한 경로를 삭제(W1.1 M5).
- 뉴올리언스 사진(4/28 1차 봉쇄)은 6/18 해제 문장에서 [clip-date-mismatch] → 레지스트리 **자료사진** 표기로 등재.
- 레바논 경고 문장(act1_11)·해운협회 문장(act6_8)은 기사 연속(cutaway-churn) 때문에 기사 대신 지도.
- 유튜브 공식 클립: 봇 검사로 받기 실패 — 우회 안 함, 클립 0(D551).

## UF-170(D-0454)
- 콘티 판 provenance `user_feedback_guards` UF-170 → `forbidden: 0`([label-in-body] 포함). 화면 글자에 괄호 라벨 없음. gate-view 수정·시험·원장 guarded 는 387c2925.

## 다음
- 감독 콘티 판 판정 → 고칠 것 반영 → D-0456 순서: econ-template 병합 → anti_inertia·골든 25 → `--preview auto` → 게이트 ② 자료 R.
