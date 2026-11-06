---
id: D-0634
from: fable
to: opus
kind: directive
responds_to: [R-0337, D-0633, UF-177, UF-178, UF-266, UF-267, UF-268, UF-269]
phase: "E9"
version: v7.4.0
status: open
priority: urgent
---

# 지시 — 칸나이 v1 전달 뒤: ① 전달 패키지(C13) ② 바다 타일 얼룩 장치·원인 ③ 반입·장치 정리. v2 렌더는 사용자 답 뒤

## 0. 전달 기록
- 칸나이 완성본 v1 을 01:50Z 에 사용자에게 보냈다. artifacts 691e9a7d final_v1/final_deliver.mp4, 28,885,844 B, md5 712cceb0, 분할 없음.
- 감독 눈 확인 점검표 190칸은 artifacts 060673ea final_v1/uf_checklist_filled.md 에 있다.
- 사용자에게 알린 결함은 둘이다. (가) 바다 타일 얼룩: 9~36초, 306~318초. (나) 표지 없는 지형: 1:50~1:54.

## 1. 전달 패키지 — CLAUDE.md C13(최우선, 사용자가 기다림)
1. 다른 트랙의 커밋 다섯을 이 순서로 cherry-pick 한다. 브랜치 merge 는 하지 않는다.
   - claude/vigilant-fermat-w8c2ti 의 df51d6e3 → 1912150b → 67ba071d → 59712982 → 3ef61740
   - 3ef61740 은 선택이다. 우리는 일반 모드라 영향이 없다.
2. 감독이 임시 worktree 로 미리 시험했다. df51d6e3 에서 충돌이 6곳 난다. 푸는 법은 아래와 같다.
   - `engine/fullcards.py`: 타이틀 카드 그리기를 `draw_title_card` 로 분리하되, 함수 안은 **이 브랜치의 현행 판**(title_subtitle(R)·badge_text·TITLE_CARD 값)을 그대로 옮긴다. 썸네일 = 이 영상의 타이틀 카드다(C13-2).
   - `rules/video_rules.yaml`·`schemas/rules_models.py`: 양쪽 블록을 모두 살린다. thumbnail·delivery_package 를 추가하고 기존 키는 그대로 둔다.
   - `rules/user_feedback.yaml`·`docs/handoff/USER_FEEDBACK_LEDGER.md`: 양쪽 항목을 모두 살린다. 원장은 `feedback_ledger.py --write` 로 다시 만든다.
   - `projects/us_midterms_2026/description.yaml`: 이 브랜치에 없는 파일이다. 삭제 쪽으로 둔다.
3. 시험: 타이틀 카드 픽셀이 cherry-pick 전후로 같아야 한다(칸나이 39초 프레임 비교). terrain3d 합성 골든을 확인한다. 호르무즈 골든 25컷은 불변이다. tests/test_thumbnail.py 와 anti_inertia 도 돌린다.
4. `rules thumbnail.theme_default_by_genre` 에 war_history 장르 키가 있는지 확인한다. 없으면 매핑만 넣는다(색 값은 바꾸지 않는다).
5. `projects/cannae_216bc/description.yaml` 을 정리한다. 지금 판(mux 용)에 감독 초안 `.scratch_wh/cannae_delivery_draft.yaml` 내용을 합친다. 아래 초안을 이 D 의 §5 에 그대로 옮겨 두었다.
   - 제목, 요약 2문단, 태그·해시태그는 감독 초안을 따른다.
   - chapters 에는 TITLE 을 남긴다.
   - "칸나이라는 이름" 같이 그 장면에 없는 말은 쓰지 않는다.
6. `tools/deliver_package.py` 와 `tools/thumbnail.py --theme war_history`(장르 기본이면 사유 불요)를 돌린다. 한도를 검사한다. 결과를 artifacts `final_v1/package/` 에 올린다. 기준은 us_midterms 썸네일과 war_history 샘플이다.
7. 원장 UF-177·178 에 전쟁사 적용 기록을 단다(감독이 확인 뒤).

## 2. 바다 타일 얼룩 — 장치 먼저, 원인, 수정(렌더는 사용자 답 뒤)
- 감독 실측: 12초 프레임(artifacts final_v1/defect_sea_tiles_12s.png)에서 아드리아해 바다 색이 사각 타일 단위로 진하거나 옅다. 306~318초 이탈리아 전경에도 있다.
- 콘티 판 v2(ed01e6d4) 23.3초에는 없었다. 프리뷰 v1 p_0014 에는 있었다. 감독이 놓쳤다(RENDER-AP-040).
- 장치(hard, 모든 테마·모든 렌더 경로): 바다 면에서 타일 경계를 따라 색이 계단처럼 뛰면 실패하는 검사를 만든다. 예: 바다 마스크 안에서 원천 타일 격자선 양옆 평균색 차가 상한을 넘으면 실패. 값은 규칙 키로 둔다. 프리뷰 v1 의 14초·31초와 final 12초·306초 프레임이 실패해야 한다. 콘티 판 v2 23.3초는 통과해야 한다.
- 원인을 R 에 적는다. 감독 추정은 D-0630 고해상도 티어(I·A·B·G·K)를 섞을 때 바다 쪽 원천(해저 음영 유무 또는 티어별 색)이 타일마다 다른 것이다.
- 수정한 뒤에는 위 프레임으로 전후 비교를 남긴다.

## 3. 반입·장치 정리(§1·§2 다음)
1. gate packet 을 반입한다: sweet-galileo 7cac0977 → 714c7252 cherry-pick, 시험. 원장 UF-266·267 guards 는 감독이 확인한 뒤 단다.
2. 1:50~1:54 표지 없는 지형(visual_void 109.9~114.0초): 연출로 고친다. 예: 2D 컷 뒤 강·칸나이 표지를 먼저 띄우거나, 컷 자리를 3D 들어감 0.5초 전으로 옮긴다. 지문이 바뀌면 seg00 을 다시 그린다. visual_void 의 길이 상한을 규칙 키로 두어 장치를 만든다.
3. UF-268·269 장치: 보낼 파일이 30MB 를 넘을 때만 조각을 만든다. 이하이면 만들지 않는다. 이를 시험으로 고정한다.
4. 원장 UF-260~264 guards 를 연결한다. 장치는 이미 있다(basemap_upscale·formation 3D 배율 시험·battle_sfx_missing·bgm_highlight 등). ref 를 원장에 달고 감독이 확인한다.
5. 남은 것: a4abe7ac 반입(tools/review_compat.py 삭제), basemap_upscale 전파 단독 커밋, terrain3d_prep.view_rows 한 프레임 어긋남 수정.

## 4. 순서
§1 → (사용자 v1 판정이 오면 그 의견도 v2 에 묶음) §2 장치·원인·수정 → §3 → v2 프리뷰 → 사용자 게이트 ②(감독 세션에서 기록, README §9) → 전편.

## 5. 감독 초안(description) — 그대로 합친다
- title: 칸나이, 기원전 216년 — 한니발의 초승달 진형과 양익 포위
- alt_titles: "8개 군단을 보낸 로마는 왜 포위됐나 · 칸나이 전투(기원전 216)" / "칸나이 전투 — 폴리비오스와 리비우스가 전한 포위전"
- summary 1문단: 기원전 216년 칸나이에서 로마군과 한니발의 카르타고군이 맞섰습니다. 폴리비오스가 적은 로마군은 동맹군을 포함해 보병 약 8만 명, 기병 6천여 명이었고, 카르타고군은 보병 약 4만 명, 기병 약 1만 명이었습니다. 한니발은 중앙의 히스파니아·켈트 보병을 적 쪽으로 볼록하게 내민 초승달 진형으로 로마 보병을 끌어들였고, 양 측면의 아프리카 보병과 하스드루발의 기병이 측면과 후방을 에워쌌습니다. 집정관 아이밀리우스 파울루스는 전사했고, 바로는 베누시아로 달아났습니다.
- summary 2문단: 폴리비오스와 리비우스는 로마군 전사자와 포로를 서로 다른 숫자로 전했고, 영상은 두 사료의 숫자를 나란히 적었습니다. 부대 위치와 크기는 폴리비오스 『역사』 III.113~116(Paton 영역 1922)을 바탕으로 한 개략이며 축척이 아닙니다. 당대 주화와 비석, 후대의 회화와 조각, 1856년 지리 사전과 1885년 판화로 이 전투가 어떻게 기억돼 왔는지도 함께 살폈습니다.
- tags: 칸나이 전투, 한니발, 제2차 포에니 전쟁, 로마 공화정, 카르타고, 폴리비오스, 리비우스, 초승달 진형, 포위전, 전쟁사, 고대사, Battle of Cannae, Hannibal, Second Punic War
- hashtags: #칸나이전투 #한니발 #전쟁사

## 6. 보충(02:05Z, 최종 감독 D367)
1. 바다 타일 얼룩의 원인 분석·검사·수정은 사용자 답과 상관없이 지금 한다. 결함 수정은 사용자 결정 사항이 아니다. §1 패키지와 병행한다. 타일 받기 같은 대기 작업은 §1 충돌을 푸는 동안 돌린다.
2. basemap_upscale 전파 단독 커밋(§3-5)은 **바다 이음 수정 + 그 검사와 같은 묶음**으로 만든다. 그 묶음이 오기 전에는 다른 트랙에 전파하지 않는다.
3. v2 재렌더·재전달만 사용자 답을 기다린다. 사용자가 "고쳐서 다시"라고 하면 바로 렌더할 수 있게 수정·검사·seg00 다시 그리기(필요하면)를 끝내 둔다. 1:50~1:54 빈 구간도 같은 v2 에 넣는다.
4. gate packet 은 origin/claude/sweet-galileo-7yok3b 의 7cac0977 → 714c7252 를 cherry-pick 한다(SKIP_VERSION_CHECK=1).
5. R-0337 의 장치 후보 둘(전편 provenance 에 프리뷰 checks 이어 받기 — 프레임 지문으로 묶음, mux 전제 점검)은 v2 묶음 뒤에 한다.
