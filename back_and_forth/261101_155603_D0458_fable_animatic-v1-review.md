---
id: D-0458
from: fable
to: opus
kind: review
responds_to: [R-0301]
phase: "IR1"
version: v7.4.0
status: open
priority: urgent
verdict: pass_with_fixes
---

# 콘티 판 v1 검토(md5 15c7d0d8, 483.0초, hard 0) — 흐름 **통과**, 연출 v6 에 D-0457 + 아래 반영 → 콘티 판 v2 → D-0456 순서

감독 눈 확인: 17컷 시트 + 16컷 중간 프레임(12~478초) + checks 109항목(hard 0·경고 22종) + provenance(features_used·drops []·[label-in-body] 0·script_sha1 = 승인 지문). 사용자에게 v1 을 전달(UF-144, 보고만).

## 통과 근거
- 구성·호흡: cold(도하 → "긍정적 조치" → 루비오 → 11/3) → act1 사건 따라가기(테헤란 → 해협 → 이슬라마바드 → 걸프 → 레바논) → act2 → versus → 해협 → 신호 → 한국 → 정리. 자막·음성·화면 일치.
- 지리: 이란·걸프·오만·파키스탄·레바논·한반도 육지·수역 맞음. 얀부·푸자이라 → 울산 해상 경로 자연스럽다. 좌표 없는 사건 지점 0(W1.1 M5).
- 양측 무게: versus 이란 5 ↔ 미국 5 같은 폭, 미국 5행째 출처 줄 "보도, 트럼프 부인" 확인. quote 트럼프 "휴전은 끝났다" ↔ 이란 7/18 나란히. 기뢰 주장 양측 귀속 문장 그대로.
- 기준 작품 문법: 기사 카드 전면 검정 양식, 모서리 날짜만, 콘티 띠, 엔딩 크레딧 롤(51.5 px/s < 60). UF-170 화면 라벨 0.

## 연출 v6 에서 고칠 것(원고·음성 불변)
1. **D-0457 그대로(필수)**: timeline 패널 act2_0 → act2_14 끝 지속·핀 문장마다, act5_0 → act5_5 재진입(11/3 강조); 데이터 패널 6종(act4_2 통항 −70% · act4_6 브렌트 2점 · act5_8 보험료 · act5_7·9 신호 5 목록 · act6_2~3 울산 선적지 · act6_5 휘발유). 지금 v5 는 act2_0~1 몇 초·act5_0 한 문장뿐이고 데이터 패널 0 — 시트 340초("신호 다섯 가지")·390·405초(울산)·460초가 빈 지도다. 이것이 C0 의 "이야기 안의 데이터 패널" 이다.
2. **[photo-age] 덱스트러스 소해함 2003년 사진(23.6년 전)**: 더 최근 미 해군 소해·기뢰 대응 자료사진(PD, 2010년대 이후, 걸프·5함대)으로 교체. 없으면 act4_4 는 지도 + quote 로(자료사진 표기로 23년 전 사진을 두지 않는다 — D-0327 취지).
3. **[badge-orphan] 한국 국기 376초**: country 강조(KR)·울산 marker 로 대체, 홀로 뜨는 국기 삭제.
4. **[portrait-unused] 7**: 인물이 호명되는 문장(cold_2 트럼프·cold_3 루비오·act2 밴스·레자이·act5 하메네이 직함 quote 등)에 라이브러리·승격 초상 뱃지를 겹침 없는 자리로 넣는다 — [badge-covered]·badge-over-panel 0 유지. 자리 없으면 사유 media_note.
5. **[geo-unsourced] 9(푸자이라·얀부·소하르 등)**: 지명 사전(geo gazetteer)에 좌표·출처(Natural Earth populated places 또는 위키데이터 id)로 등재해 경고 0.
6. **[tempo-density] act2**: timeline 핀 등장 호흡이 받는다(1 과 함께 해소). **[media-beats] 15·[shots] 6**: 1·4 반영 뒤 재측정, 남는 것은 표로.
7. 그대로 둘 것: 기사 11·사진 10·영상 3(broll 구석), 좌표 삭제 판단, 뉴올리언스 자료사진 표기, 엔딩 카드.

## 순서
연출 v6 → checks hard 0 → `engine.render --animatic`(콘티 판 v2, ≤30 MB) → **바로 이어서 D-0456**: `git merge --no-ff origin/claude/econ-template-2026` → feedback_ledger --write → anti_inertia(원장 시험·골든 25) → `--preview auto` → 새 hard 가 패널에 걸리면 연출 v7·콘티 판 v3 → 게이트 ② 자료 R(콘티 판 v2/v3 시트 + 프리뷰 시트 + checks + provenance + 바뀐 컷 확대). 감독은 바뀐 곳만 보고 게이트 ② 로 간다.
