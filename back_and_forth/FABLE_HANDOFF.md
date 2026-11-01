# 감독(Fable 역할) 세션 인수인계 — 2026-10-11 (v5.21.0)

## 0-4. 2026-10-31 23:40Z — 감독 승계(사용자 지시 "새로운 감독 세션을 띄워서 인수인계시켜")

이 블록이 새 감독 세션의 **출발점**이다. 옛 감독 = `session_017Yuw8kbxf9Vxri6LoH5Je4`(Fable 5.1, sweet-galileo). **새 감독(최종) = `session_017Yuw8jLMWscY9bdVXTvddr`(Fable 5.1, 2026-11-01 00:10Z 생성 — 사용자가 네트워크 허용 목록(en.wikipedia.org·www.aljazeera.com·www.cbsnews.com·apnews.com·commons.wikimedia.org·upload.wikimedia.org·fred.stlouisfed.org·doroper98.github.io·analysis-reports.pages.dev)을 추가한 뒤 띄움). 중간 승계 세션 `session_017Yuw8iKFWUG9yMqoGHN39V`(23:53Z)는 대체·보관, 그 점검 트리거 trig_011g2r2iF93joBssYXSawwdo 는 껐다.** 옛 감독 점검 트리거 `trig_011XELpyTdKrmNeGj35Y9DEk` 는 23:53Z 에 껐다. 구현 세션 3·2 에는 새 id 를 통보했다. 읽는 순서: 이 블록 → 0-3·0-2·0-1 → `back_and_forth/README.md` → `CLAUDE.md` → `docs/handoff/15` → DECISIONS D299~D312 → D-0318~D-0333.

### 세션 목록(이 감독이 잡고 있던 것)
| 역할 | 세션 id | 브랜치 | 상태(23:40Z) |
|---|---|---|---|
| 쇼케이스 구현 3(Opus 5.5) | `session_017Yuw8mZjzL9rxkApRyBCoR` | `claude/sweet-galileo-7yok3b` | **게이트 ② 사용자 답 대기**. 패키지 v5 = artifacts/showcase-v7.4.0 47427cc(프리뷰·카탈로그 hard 0, 골든 12, 검사 109). D-0325~D-0333 전부 적용·커밋(마지막 a10c1323 R-0295). 사용자 승인 + econ A/B(감독 추천 A)가 오면 D(from: user) 로 final 렌더 신호 → geo final·catalog → econ → 결합본. |
| 경제 템플릿 구현 2(Opus 5.5) | `session_017Yuw8kbeoYpfyG3k9TfnLQ` | `claude/econ-template-2026` (artifacts/econ-template-2026) | **요소 넷 사용자 승인 대기**(가이던스 인셋·slope·덤벨·diverging, 사용자에게 보냄). 바닥 조판 정본 승인됨(D-0330, 손실 막대 A = UF-204). T3 준비분 WIP 커밋 6ccea7d. 승인 오면 D(from: user) → T3 한 커밋(세 곳 등록, princess 기본값·ink_light 대안 키 삭제, surface stage·noturno 경제 기본) → T4 → T5 삼성·인텔 영상. 컨텍스트 70만/100만 — 인계 임박 시 OPUS_RESTART_PROMPT 방식. |
| 중국 트랙 감독(Fable 5.1) | `session_017Yuw8hTb2zPgG7PvjAbjyu` | `claude/china-export-controls-2026` | **완료**(사용자 95점, UF-158·D-0324). 손대지 않는다. main 병합은 사용자 지시 대기. |
| 옛 쇼케이스 구현 1·2, 옛 경제 구현 1 | `session_017Yuw8k4hDAiSpVRGtFv4Lu`·`session_017Yuw8mVchPLgYxtnfEwjjh`·`session_017Yuw8hgL1EgKn1qUsDZQz2` | — | 종료(한도·컨텍스트). 깨우지 않는다. |

### 사용자 결정 대기(그대로 묻지 말고, 답이 오면 바로 실행)
- **2026-11-01 00:30Z 사용자 답(UF-206) "1~4까지 승인"** → 1·2 = D-0335(세션 3 렌더)·D-0336(세션 2 T3) 발송, 3 = CLAUDE.md C0 표제 정정 커밋, 4 = 중국 브랜치 main merge --no-ff. 5 = D-0337 전쟁사 트랙 착수(위임 감독 세션은 §0-6). 추가 지시 '이란 협상 분석 영상 별도 트랙' 은 D-0334 와 범위 중복 → 사용자 확인 중.
1. 쇼케이스 게이트 ② 승인 + showcase_econ A/B(감독 추천 A = 사진 배경 + 아일랜드). → 세션 3 에 D(from: user) 로 렌더 시작.
2. 경제 템플릿 요소 넷 승인. → 세션 2 에 D(from: user) 로 T3.
3. CLAUDE.md C0 표제 정정("다시 들여오면 안 되는 것") — 헌법 개정이라 사용자 결정(LLM-AP-021).
4. 중국 브랜치 main 병합 여부.
5. 전쟁사(E9, 우선 1)·미술사(E10) 트랙 — 쇼케이스 게이트 ② 뒤 착수, 계획 D-0307, 첫 사례 칸나에 가정. 전용 구현 세션을 `claude/war-history-2026` 에 띄운다.

### 번호·규칙(충돌 방지)
- D 다음 번호 **D-0334**(sweet-galileo), DECISIONS 다음 행 **D313**, UF 다음 **UF-205**(이 트랙 UF-200~ 사용 중; 중국 트랙 UF-160~162 별도). R 은 구현 세션이 올린다(세션 3 R-0295 까지, 세션 2 R-0306 까지).
- 커밋 첫 줄 `v7.4.0: …`, 트레일러 Co-Authored-By: Claude Fable 5.1 + Claude-Session(새 세션 URL). PR 금지(C8-5), main push 금지, 모델 식별자 저장소 기록 금지, 표준 음성 재질문 금지(C0.2), 게이트 장치 우회 금지, 조용한 드롭 금지(P6).
- 사용자 의견은 받은 즉시 `rules/user_feedback.yaml` 에 원문 그대로 UF 로(C12). 보고문은 `python tools/slop_check.py <file>` 통과 뒤 보낸다(UF-145·UF-202 금지어 — "~축에 겹칩니다" 류 화면 조작 해설 포함).
- 레퍼런스는 느낌만, 요소 이식 지시 금지(LLM-AP-022). 렌더 전 구상 1프레임으로 판정. 샘플은 나오는 대로 바로 사용자에게(UF-144).
- 점검: 옛 감독의 send_later 트리거 `trig_011XELpyTdKrmNeGj35Y9DEk` 는 승계 시 옛 감독이 끈다. 새 감독은 자기 점검(60~120분, 사용자 결정 대기 중엔 2~4시간)을 건다.
  - **승계 완료(2026-10-31 23:57Z)**: 새 감독이 §0-4 ·README·CLAUDE.md·15·DECISIONS D299~D312·D-0318~D-0333 을 읽고, 세션 3·2 에 새 id 통보, 자기 점검 `trig_011g2r2iF93joBssYXSawwdo`(3시간 간격, 02:58Z 첫 발화)를 걸었다. 세션 2 컨텍스트 71만/100만 — 인계 임박.
  - **승계 완료(최종, 2026-11-01 00:15Z)**: 최종 감독 `session_017Yuw8jLMWscY9bdVXTvddr` 가 §0-4·0-3·0-2·0-1·README §6·CLAUDE.md·15·DECISIONS D299~D312·R-0295·D-0321 을 읽고, 네 브랜치 fetch(sweet-galileo 5f2f5b8c·econ 6ccea7d·artifacts 47427cc·98c020b4), 세션 3·2 에 최종 id 통보(중간 세션 id 무효 명시), 자기 점검 `trig_015VQmUZd2C9VoKfnANtunEr`(03:15Z, 3시간 간격)를 걸었다. 중간 세션 트리거 `trig_011g2r2iF93joBssYXSawwdo` 는 꺼져 있음 확인. **네트워크 실측**: 허용 목록 추가 뒤에도 이 컨테이너는 commons.wikimedia.org·upload.wikimedia.org 만 200, en.wikipedia.org·www.aljazeera.com·doroper98.github.io·analysis-reports.pages.dev·fred.stlouisfed.org·www.cbsnews.com·apnews.com 은 CONNECT 403(정책 거부). 사용자에게 보고.
- 네트워크: 이 컨테이너는 doroper98.github.io·analysis-reports.pages.dev·en.wikipedia.org·www.aljazeera.com 이 막혔다(정책은 세션 시작 시 굳음). 사용자가 허용 목록에 넣은 뒤 새 세션부터 열린다. agents_reviewer 는 public 저장소라 `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/doroper98/agents_reviewer` 로 받아 로컬에서 본다(reports/*.html + src/templates/static/charts.js·charts.css·d3 를 같은 폴더에 두고 Playwright 로 스크롤 뒤 캡처).
- 최근 산출: 유튜브 문안 `docs/handoff/reports/china_youtube_meta_2026-10-31.md`, 르포 참고 캡처 `docs/handoff/reports/reportage_ref_2026-10-31/`.

### 새 감독이 처음 할 일(순서)
(1) 이 블록·README·CLAUDE.md·15·DECISIONS D299~ 읽기 (2) `git fetch` 로 sweet-galileo·econ-template-2026·artifacts 두 브랜치 확인 (3) 세션 3·세션 2 에 send_message("감독 승계, 이후 R·결정 요청은 이 세션으로") (4) 자기 점검 send_later 걸기 (5) 사용자에게 한 줄 보고(대기 중인 결정 1·2 를 다시 묻지 말고 목록만).

## 0-5. 2026-11-01 — 병행 트랙: 『미국·이란 휴전안 — 정리와 가능성 타진』(사용자 결정 D-0334, UF-205)
- 위임 감독(Fable 5.1) `session_017Yuw8hAgYiuiC4hYCHXB27`(2026-11-01 00:13Z, 옛 감독이 D-0334 요지로 기동). D-0282 방식 — 게이트 ①·② 위임, 질문 없이 완성본(final_deliver.mp4 ≤30MB + srt·description·credits·provenance·유튜브 문안)을 사용자에게 직접 전달. 브랜치 `claude/iran-ceasefire-2026`(sweet-galileo 41e00a99 에서 분기), artifacts `artifacts/iran-ceasefire-v7.4.0`. 번호 D-0450~(넘으면 D-0800~)·DECISIONS D550~·UF-170~199. 종료 보고는 최종 감독 `session_017Yuw8jLMWscY9bdVXTvddr` 로.
- **착수(2026-11-01 00:23Z)**: 기동 지시 D-0450(커밋 377561e5, DECISIONS D550·D551). 구현 세션 `session_017Yuw8kfoLTzsBrmCXnBDdk`(Opus 5.5, env_01SnvGMv3UmrvejEraZxEACo, B형 기동 문안 = D-0450 요지). 감독 자기 점검 send_later `trig_01NE5PKkJqpiU49FxtpTHP2q`(01:11Z 첫 발화, 이후 45~60분). 감독 컨테이너 네트워크: commons·upload.wikimedia 만 열림, en.wikipedia·aljazeera·cbsnews·apnews·fred 는 403 — 출처 대조는 WebSearch(크롤러 차단: apnews·bbc·reuters·mk·yna·chosun 은 allowed_domains 에 못 넣음). 조사표 D-0451 작성 중.
- **전달 완료(2026-11-01 10:56Z)**: artifacts/iran-ceasefire-v7.4.0 424fb28 `iran_ceasefire_2026/final/final_deliver.mp4`(720p·483.03초·28.9 MB·md5 fd89a455) + srt·description·credits·시트·유튜브 문안(docs/handoff/reports/iran_youtube_meta_2026-11-01.md) 사용자 전달. 경로: D-0451 조사표 → 원고 v1.2 66문장(게이트 ① D554) → 콘티 판 v1·v2·v4(D-0458·D-0459) → econ-template 병합 71a36ebb(D-0456, 원장 167 미보호 0) → 게이트 ② D-0460/D560(골든 25 환경 의존 미판정 → phase7 보존본 복원 지시) → 전편. 사용자 의견 UF-170(검증 라벨 화면·검토 자료 금지) guarded(387c2925). 취소된 결정: D-0455/D556(최종 감독 이의 D-0341 → D-0456/D557). 남은 것: 최종 R(전체 pytest·골든 3건) → 최종 감독 종료 보고, main 병합은 최종 감독 몫.
- **탈락·재작업(2026-11-01 11:10Z, UF-171·172)**: 사용자 판정 "뱃지·사진·기사 조판이 뜨자마자 사라짐 — 탈락" + "봉쇄 해제 장면 사진이 기사 카드에 묻힘". 원장 UF-171·172(open → 장치 커밋에서 guarded), D-0462(b1c212d7)·D563. 감독 실측 6초 미만 15건(direction v8×plan). 최종 감독 요청(11:24Z): 장치(규칙 키 종류별 최소 유지 시간 = 첫 아라그치 뱃지 실측 초 이상, hard [element-hold]·[media-overlap], 시험, 원장 guarded)를 **연출·프로젝트 파일 없는 커밋 하나**로 올려 해시 통보(쇼케이스 cherry-pick) — 구현 세션에 지시함. 그 뒤 reopen --to direction → 연출 v9 → 콘티 판 v5 → 감독 판정 → 프리뷰 → 게이트 ② 재승인(감독 컨테이너: pycairo 설치됨, transition preview_qa→preview_approval 뒤 approve) → 720p final_v2 → 사용자 재전달(유튜브 문안 챕터 재대조) → 최종 R → 최종 감독 종료 보고.
- **콘티 판 v5 통과(2026-11-01 13:20Z)**: 장치 커밋 25bc3915(D564) → 연출 v9 → artifacts 9a51972 animatic_v5/(md5 f2796da0, 483.0초, hard 0, element_hold·media_overlap 0, 요소 29건 완전 노출 ≥6.00초, 짧은 요소 5 제거). D-0463(85985e36)·D566, 사용자에게 v5 보고(mp4·시트·hold 표). 쇼케이스 full_types 정정(D-0348, D565)은 해시 오면 구현 세션 cherry-pick. 다음: 구현 세션 `--preview auto` → 게이트 ② 자료 R → 감독 컨테이너 transition→approve → 720p final_v2 → 재전달 → 최종 R → 종료 보고.
- **승계 명세(이 감독이 끊기면)**: 새 감독은 이 블록 → D-0450~D-0462 → DECISIONS D550~D563 → 원장 UF-170~172 순으로 읽고, 구현 세션 `session_017Yuw8kfoLTzsBrmCXnBDdk` 에 새 id 통보, 점검 send_later(45~60분) 재설정, 최종 감독 `session_017Yuw8jLMWscY9bdVXTvddr` 에 승계 통보. 사용자에게는 샘플·완성본 전달 때만 말한다. 게이트 ② 재승인은 감독 컨테이너에서 실행(approve 는 구현 세션 권한 판정기가 self-approval 로 거부함). 유튜브 문안 docs/handoff/reports/iran_youtube_meta_2026-11-01.md 는 재전달본 챕터·크레딧으로 다시 대조.

## 0-2. 2026-10-30 — 병행 트랙: 『중국의 기술 수출통제 확대(2026.10)』(사용자 결정 D-0282)
- **완성 확정(2026-10-31, 사용자 판정 95점 — UF-158·D-0324·D302)**. main 병합은 별도 지시 대기.
- **종결(2026-10-30 15:52Z)**: 완성본 전달 — artifacts/china-export-controls-v7.4.0 95148beb `china_tech_export_controls_2026/final/final_deliver.mp4`(720p·397.08초·md5 02ccbde3·hard 0). 원고 56문장, 게이트 ①·② 위임 승인, 콘티 판 v2 사용자 "아주 만족" + UF-160~162 반영. 교정 사실: 드론 공고 10/19 제49호(감독 메모의 10/14 는 오류), 공고 5건(10/16~10/26). 후속 후보: mercator 주 무대 + 시간축 아일랜드(D504 C안). 브랜치 claude/china-export-controls-2026 — main 병합은 사용자 결정.
- 사용자 지시로 **별도 감독(Fable) 세션**이 이 영상을 묻지 않고 완성본까지 만든다. 브랜치 `claude/china-export-controls-2026`. 감독 세션 `session_017Yuw8hTb2zPgG7PvjAbjyu`(Fable 5.1, env_01SnvGMv3UmrvejEraZxEACo, 2026-10-30 06:31Z 생성, 기동 프롬프트 = 부모 감독이 D-0282 §1~§4 요지로 작성). 쇼케이스 트랙(0-1)과 독립 — 이 세션(sweet-galileo)은 쇼케이스·E7 만.
- **D 번호 분리(충돌 방지)**: 중국 트랙 감독은 D-0285~D-0299(넘으면 D-0400~), 쇼케이스 트랙(이 세션)은 **D-0300~**(2026-10-30 D-0300 부터). 두 브랜치를 합칠 때 번호가 겹치지 않는다.
- **DECISIONS.md 행 번호도 분리**(2026-10-30): 부모 감독(이 세션) 순번 D28x~ · 경제 템플릿 트랙 D400~ · 중국 트랙 D500~. 합칠 때 행은 날짜순으로 끼워 넣는다.
- **원장 UF 번호 분리**(2026-10-30, 중국 트랙 감독 통보): 쇼케이스·경제 트랙(이 세션) UF-146~159 · 중국 트랙 UF-160~(사용자가 중국 콘티 판에 준 의견 3건 = UF-160~162). 이 세션이 159 를 넘기면 UF-200~ 으로 건너뛴다.

## 0-3. 2026-10-30 — 경제 템플릿 트랙(E3·E4·E5·E7, D-0301)
- **상태(2026-10-31 12:00Z)**: 쇼케이스 = 게이트 ② 패키지 v5 준비 완료(artifacts/showcase-v7.4.0 47427cc, 프리뷰·카탈로그 hard 0, 골든 12 통과, 검사 109; D-0325~D-0333 적용 — 전환 ×1.5·연준 band 일별·사진 교체·배지 덮임·라벨/캡션 검사). final 렌더는 **사용자 게이트 ② 승인 + econ A/B**(감독 추천 A)가 와야 시작, 세션 3 대기. 경제 템플릿 = 바닥 조판 정본 승인(D-0330, 손실 A UF-204), 요소 넷(가이던스·slope·덤벨·diverging) **사용자 승인 대기**, T3 준비분 WIP 커밋 claude/econ-template-2026 6ccea7d, 세션 2 대기. 중국 트랙 완성 확정(95점). 유튜브 문안 docs/handoff/reports/china_youtube_meta_2026-10-31.md.
- 사용자 지시로 착수. 감독 = 이 세션(별도 Fable 없음). 전용 구현 세션 `session_017Yuw8hgL1EgKn1qUsDZQz2`(Opus 5.5, 2026-10-30 08:50Z, B 형 기동 프롬프트 = D-0301 §1~§2 요지).
- **구현 세션 2(인계, 2026-10-30 18:39Z)**: `session_017Yuw8kbeoYpfyG3k9TfnLQ`(Opus 5.5). 세션 1 은 컨텍스트 한계로 d8044300(R-0297, bullet 스케치)에서 인계 — 작업 트리 깨끗, 미등록 패치는 artifacts/econ-template-2026 `t2_bullet/econ_sketch_v4.patch`. 남은 순서: 안 A(시세 2025-07~) → 덤벨 → diverging → slope → 가이던스 → (사용자 요소 승인 뒤) T3 → T5. 브랜치 `claude/econ-template-2026`. 정본 D-0251 §2·D-0278·D-0301. 쇼케이스 세션 3 은 E7 에서 손을 뗐다.

## 0-1. 2026-10-28 갱신 — E0 쇼케이스 트랙(감독 세션 `session_017Yuw8kbxf9Vxri6LoH5Je4`, Fable 5.1)
- **현재 트랙**: E0 쇼케이스 데모 2편 + 카탈로그 층(back_and_forth D-0251 §1·§5·§6·§7). 브랜치 `claude/sweet-galileo-7yok3b`(main 8d93103 위), 버전 v7.4.0.
- **구현 세션**: `session_017Yuw8k4hDAiSpVRGtFv4Lu`(Opus 5.5, env_01SnvGMv3UmrvejEraZxEACo, 2026-10-28 04:06Z 생성). 옛 구현 세션 `session_012yN5MN9eH1tBnNrQ1D8sBG` 은 diesel v2 종결·disconnected.
- **구현 세션 2(재기동, 2026-10-29 12:39Z)**: `session_017Yuw8mVchPLgYxtnfEwjjh`(Opus 5.5, 같은 env). 구현 세션 1 은 2026-10-28 09:39Z 계정 5시간 한도로 failed·disconnected(마지막 커밋 51cc7fa — 틀·UF-137 guarded까지). 남은 것: econ 콘티 판 v2 → geo 콘티 판 → 골든 25/25 → A/B → 게이트 ② → final·catalog·결합본.
- **구현 세션 3(재기동, 2026-10-30 03:33Z)**: `session_017Yuw8mZjzL9rxkApRyBCoR`(Opus 5.5, 같은 env). 세션 2 는 2026-10-30 01:18Z 계정 5시간 한도로 failed(마지막 커밋 7b6b997 — D-0274 §1·§2 완료, 연준 클립 넷 등재). 남은 것: preview_v9 확인 → 렌더 작업 수(클립 npy) → econ 원고 발언 자리 2곳 → 게이트 ① 재승인 → 연출 → 콘티 판 v3 → geo 콘티 판 v2(strikes 액자) → 게이트 ② → final·catalog·결합본.
- **사용자 결정 이 기간**: D264(비공개 시청·권리는 기록만) · D265(보완 방향·쇼케이스) · D266~D268(연준 탈락·호르무즈 미흡·diesel 기준 작품, C0 개정). 원장 UF-132~136.
- **사용자에게 갈 것(순서)**: ① showcase_geo 원고(gate-view) ② showcase_econ 원고 ③ 콘티 판 2편 ④ 게이트 ② 프리뷰 시트 + A/B 시트(D108 보정) + 카탈로그 요소 표 ⑤ final·catalog·결합본. 사용자 2026-10-28 원문 "영상은 어딨어" — 착수 지시를 기다리다 늦었다. 다음부터 계획 승인 = 착수.

## 0. 2026-10-19 갱신 — 승계 규칙(사용자 결정 D256)과 현재 상태
- **승계 규칙**: 감독 세션의 컨텍스트 사용량이 95% 에 이르거나 사용 한도가 차단되면, 감독은 `create_session(model: claude-opus-5-5, title "감독(fable) 승계 — diesel_road_2026 v2", prompt: 이 문서 §0 를 읽고 이어받으라)` 로 **별도 감독 세션**을 연다. 역할 이름은 그대로 `fable`. 구현 세션(아래)은 바꾸지 않는다. 새 감독은 이 문서 → `back_and_forth/README.md` → `CLAUDE.md` → `docs/handoff/15` → DECISIONS D238~ 순으로 읽는다.
- **현재 트랙**: diesel_road_2026 v2(브랜치 `claude/diesel-road-v2`, 버전 v7.4.0). 구현 세션 = cloud session `session_012yN5MN9eH1tBnNrQ1D8sBG`(Opus). 아티팩트 `artifacts/diesel_road_2026-v7.4.0`(교체본 2 대기). main 병합 보류 중(D-0245 §1).
- **열린 D**: D-0245(그래프 3종 복원, [series-unused]·[panel-dropped] hard), D-0246(발음 '유가' 경음화 — 발음 사전 "경유 가", tensification_traps 규칙 키, 린트 hard, TTS-AP-083), D-0247(dual_line 빈 달 점선 보간, 모든 영상). 구현 순서: 사전+보간 → 재합성·믹스 → 프리뷰 hard 0 → 콘티 판 재렌더(의무) → 게이트 ②(D-0243 위임) → 720p → artifacts 교체 2 → R → 장치(UF-126·127·128 guarded) → E 단계(빠른 묶음+영향 느린 노드, 골든 화소 비교, DEVLOG·CHANGELOG, `merge --no-ff`, PR 없음) → 최종 R.
- **사용자에게 할 일**: 교체본 2 가 오면 final.mp4(part00+part01 결합, MD5SUMS 대조)·그래프 3컷·두 문장 wav 를 한 줄로 전달. 병합이 끝나면 커밋·테스트 수 한 줄 보고.
- **예약 점검**: 감독 세션에 send_later 로 45~60분 간격 점검이 걸려 있다. 승계 시 새 세션에서 같은 점검을 다시 건다(옛 세션 트리거는 update_trigger enabled=false).
- **2026-10-19 02:45Z 승계 시점 상태(사용자 지시 "fable 한도 94%")**: 구현 세션은 8ab77fe2(짧은 사전 키 낱말 경계 + act2_35·act3_15 재합성, 두 문장만 변경 확인)까지 push, 테스트 작성 중. 남은 것: 믹스 → 프리뷰 hard 0 → 콘티 판 재렌더(~40분) → 게이트 ②(D-0243 위임) → 720p(~70분) → QA → artifacts 교체 3 → R(wav·MMS 간격 표·그래프 3컷). **artifacts 2e1fba69(md5 6d24abca, 그래프 복원만)는 사용자에게 보내지 않는다**(발음·보간·카드 겹침 미반영). 열린 D: D-0245·D-0246(+D258 보충)·D-0247·D-0248. 원장 UF-126~129 open(장치는 영상 전달 뒤). 옛 감독 세션(`session_016v5HgxdsPNKcUYQ94ZkAoo`)의 점검 트리거 `trig_01AookPVpgqVkk2F5AqWvu5W`(03:43Z)는 새 감독이 자기 점검을 건 뒤 옛 감독이 끈다. **구현 세션은 R 을 `send_message` 로 옛 감독 세션 id 에 보내고 있다 — 새 감독은 첫 메시지로 구현 세션에 새 session_id 를 알리고, 이후 R 은 새 id 로 받도록 한다.**
- **승계 세션(2026-10-19 02:49Z 생성)**: `session_01CLMApgWisjaB6TYfe7EUdx`(Opus 5.5, 사용자 요청 '높음' 노력). 구현 세션에는 옛 감독이 이미 새 id 를 알렸다(보고는 새 id 로).
- **새 감독이 처음 할 일(순서)**: (1) 이 문서·README·CLAUDE.md·DECISIONS D238~D258 읽기 (2) `git fetch`·브랜치 확인 (3) 구현 세션에 send_message("감독 승계, 이후 보고는 이 세션으로") (4) send_later 로 45~60분 점검 예약(점검 문구는 옛 트리거와 같은 틀: fetch → 진척 → 교체 3 이 artifacts 에 있으면 결합·md5·그래프 3컷·두 문장 프레임·wav 확인 후 사용자에게 한 줄 전달 → 장치·E 단계·merge --no-ff 확인) (5) 옛 감독 세션에 send_message("승계 완료, 트리거 꺼도 됨") (6) 사용자에게 한 줄 보고.
- **원장**: UF-126·127·128 status open — 장치가 달리면 guarded 로(구현 세션이 올림). `python tools/feedback_ledger.py --write`.

새 감독 세션은 이 문서를 먼저 읽고, 그 다음 `back_and_forth/README.md`·`CLAUDE.md`·`docs/handoff/15`·`docs/handoff/DECISIONS.md`(D169~D181)를 읽는다.
사용자 사정(세션 한도)으로 감독 역할이 이 세션으로 옮겨졌다. **역할 이름은 그대로 "fable"** 이다(`check.py --me fable`, 문서 `from: fable`).

## 1. 역할
- 구현 세션(Opus, cloud session `session_0157T2pwd4LG8dkkcvZACoWJ`)이 코드를 만든다. 감독은 **코드를 직접 고치지 않는다.** D 문서(지시·판정)를 쓰고, R 보고를 **자기 컨테이너에서 실측**해 판정하고, DECISIONS 에 한 줄 붙이고, 커밋·푸시하고, Opus 에 `send_message`(claude-code-remote MCP, session_id 위 값)로 알리고, 사용자에게 한국어(~습니다 체, 짧은 문장, 핵심 요약 1~3줄)로 보고한다.
- 사용자 고유 결정(README §7: 주제·청취 합격·게이트 승인·권리 예외·색 선택)은 감독도 내리지 않는다 — 사용자에게 묻는다.
- 문서 파일명: `python back_and_forth/check.py --me fable --next-name <slug>`; 본문 `id:` 는 파일 번호와 같게. 커밋 첫 줄 `vX.Y.Z: …` 는 `VERSION` 과 같아야 한다(hook). 리베이스는 `SKIP_VERSION_CHECK=1`. 푸시는 `git push -u origin claude/bold-mccarthy-ttmagk`(실패 시 fetch → rebase → 재시도, **force push 금지**). PR 만들지 않는다. main 병합은 트랙 끝에 감독만.
- 커밋 트레일러는 세션 안내(system reminder)의 것을 쓴다. 저장소 산출물에 모델 이름을 적지 않는다.

## 2. 검증 환경(감독 컨테이너)
- 렌더·pytest 는 반드시 `FONTCONFIG_FILE=<scratch>/restore/fontconfig/fonts.conf` — 없으면 만든다: 시스템 `/etc/fonts/fonts.conf` 를 복사해 `conf.d` 에서 `12-unhinted-grayscale.conf` 를 제외한 설정(이전 감독 컨테이너는 scratch 에 두었다; 골든 md5 가 안 맞으면 이것부터 의심).
- **C8.3(D187)**: 변경마다 타깃 + `tests/anti_inertia`(골든 e2e) — 전체는 하루 1회·병합 직전, 구현 세션이 같은 커밋에서 전체를 통과했으면 감독은 타깃·골든만 확인하고 수치는 인용. 빠른 묶음 `python -m pytest -q -m "not slow"`.
- 전체 pytest `python -m pytest -q -rs` ≈ 35~43분. 환경 고정 비합격 9 = 1080p 티어 errors 3·클립 skip 1·fed 자산 failures 4 + `HormuzV3Test.test_final_mix_within_audio_qa_range`(미추적 산출물). 코드 비합격 0 이면 합격. 수집 수는 Opus 보고와 같아야 한다(최근 1548).
- 골든: 프로젝트를 scratch 에 복사(`prev`·`out` 제외)한 뒤 `python -m engine.render <copy> --preview golden` → `docs/handoff/reports/phaseV3/hormuz_baseline.json`(dark) · `phaseQ3/hormuz_light_baseline.json`(light; direction.yaml `stage_config.mercator.theme: light` + `geo.prep <copy> --theme light`) 과 md5(`md5_masked` 는 stamp_box 가리고) 대조 → 25/25. 참고 스크립트 논리: `tests/anti_inertia/test_provenance_e2e.py` `_masked_md5`.
- e2e 테스트는 전체 pytest 와 동시에 돌리지 않는다(`projects/hormuz_korea/prev/` 공유). 컨테이너 간 **오디오 md5 는 일치하지 않는 것이 정상**(D-0180 §2-1) — 영상 골든만 대조.

## 3. 현재 상태(2026-10-12 KST, v6.0.0 — 구현 opus 갱신, D-0213 §3-2)
| 트랙 | 상태 |
|---|---|
| V3·V5 표준 음성 | 종결 — Supertonic 3 M3 ×0.95 + 끝 억양 시안 C + MMS 정렬 = 표준(CLAUDE.md C0.2, D185·D189) |
| v5.21.0 보도 인용 B ~ v5.21.8 | 합격 |
| P1 gulf_pact_2026 | 사용자 의견 UF-01~12 반영·예멘 채움 제거(D207) → `artifacts/gulf_pact_2026-v5.22.4` 사용자 전달(D208). 재렌더 없음(v5.22.5~8 은 다음 렌더부터) |
| 사용자 의견 원장(C12) | UF-01~96 전부 guarded(open 0), 게이트 ② `require_feedback_guards`, provenance `user_feedback_guards`(프리뷰·콘티·전편) |
| 경로 이름표 | 전경 층 회피·수명 고정·전 구간 비충돌(D209·D210), `label_jump` hard, 렌더·검사 장애물 통일(RENDER-AP-024) |
| D-0201 | xdist `-n 4`(v5.22.9)·국경 numpy(v5.22.10) 합격 D212 |
| V4 edge 삭제 | v5.23.0 합격 D-0213. fed_timeline_demo 표준 음성 재생성(면제 1건 D-0213) |
| GOAL G3 개정 | **v6.0.0**(MAJOR): 18번 사용자 의견 원장 + 사용자 보호 hard 검사 연결, 4번 표준 음성 문구·시험 이름(별칭 삭제) |

## 4. 다음 할 일(순서)
1. 병합 직전 전체 pytest 1회(C8.3) — R 보고 머리말 `full_pytest:`.
2. 감독 main fast-forward(README §6.5). main 이 이 브랜치의 조상이 아니면 멈추고 보고(force 금지).
3. 그 뒤: 사용자 시청 의견이 최우선. 보류 — Q4a/Q4b/Q5/Q6/G(요청 시), 검증 LLM "출처 많으면 건너뜀"(Opus 결정 요청으로), creaky 꼬리 패치(사용자 지적 때만, D-0184 §2-①), gulf 원장 후보 메모 ①41.58초 뱃지 밑 카드 ③58초 이란 채움(사용자 지적 때만).

## 5. 사용자 결정 기록(이 기간)
D169 믹스 OK·시안 C / D171 정렬 모델 CC BY-NC 유지 / D172 통신사 사진 B / D173 light A / D174 순서(P1-1 을 V5 뒤) / D180 게이트 ① "대본 오케이". ElevenLabs 금지(D127), edge 삭제는 V4.

## 6. 사용자 소통
- **레퍼런스는 느낌만**(UF-202, LLM-AP-022): 사용자가 '참고' 로 준 디자인은 인상(여백·절제·강조 1색·직접 라벨)만 가져온다. 머리·캡션·푸터 같은 구성 요소 이식 지시는 쓰지 않는다. 렌더 전 구상 1프레임으로 판정을 받는다.
- 한국어, 공손·명료, 한 문장 60자 이내, 문단 3~4문장, 말미 "기억해야 할 핵심 요약" 1~3줄.
- 사용자가 결정할 것만 묻는다. 파일은 SendUserFile(scratch 경로 가능). 영상은 30 MB 이하로 재인코딩(`-c:a copy` 로 음성은 원본 유지).
- **보고문을 보내기 전에 금지 문구 패턴으로 자기 점검**(UF-145, 사용자 원문 2026-10-30 "니가 작성하는 문구에 이런내용이 없도록 강하게 쪼여"): `rules banned_phrases.patterns`(수렴 은유·승부 은유·"남는다/올라온다" 마무리·청구서 의인화 등)를 사용자에게 가는 모든 글·원고·화면 문자열에 적용한다. 도구 `tools/slop_check.py`(D-0281) 가 생기기 전에는 python 한 줄로 돌린다.
- **샘플·시트·콘티 판은 만들어지는 즉시 사용자에게 보낸다**(UF-144, 사용자 원문 2026-10-30 "만들어진 샘플들은 바로바로 보여줘"): 구현 R 이 artifacts 를 가리키면 그 자리에서 받아 SendUserFile — 다른 산출물과 묶어 기다리지 않는다.
