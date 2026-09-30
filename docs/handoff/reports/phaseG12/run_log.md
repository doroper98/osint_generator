<!--
tier: 3
last_synced_with: v5.1.0
ssot_for: [phaseG12-run-log]
depends_on: [rules/video_rules.yaml, engine/stage_backdrop.py, engine/island.py, engine/layers/article.py, engine/layers/backdrop.py, back_and_forth/260930_103703_D0121_fable_g12-chart-island-backdrop-article-press.md, back_and_forth/260930_104341_D0123_fable_g12-backdrop-stage-generalized.md, back_and_forth/260930_105832_D0124_fable_g12-endcard-version-stamp.md, back_and_forth/260930_111842_D0126_fable_g12-decisions-q1-q7.md]
last_review: 2026-09-30
-->

# Phase G12 실행 기록 — backdrop 무대·아일랜드·축 스케일·기사 프레스 v2·발음 사전·버전 도장 (v5.1.0)

지침 D-0121(§A·§C·§D·§E·§F)·D-0123(§B 대체)·D-0124(§G)·D-0125(착수)·D-0126(결정 Q1~Q7 전부 A). 재기동 26 세션.

## 0. 컨테이너 준비

phaseG10 run_log §0(= G7 §0 + G10 차이) 그대로(하위 에이전트). 차이만 적는다.
- 지오 자산 hormuz 21/21·랫클리프 15/15·청와대 휘장 `513c0785…` 일치. `mix.f32` 는 fed `567f2da5`·hormuz `96f9ebb7`(G7 값과 다름 — G10 §2 뒤 재생성, 소리 상관 0.998). 원인 미확정, 테스트 영향 없음.
- bgm 은 전체 이력이 필요 — `git fetch --unshallow` 뒤 fetch_data 통과.
- **fed 자산 누락 보강**: `assets/flags/us_*.png`(hormuz 와 같은 md5 `66d6da8e…`) 복사, `media_fetch --only fed_presser_0916,fed_presser_0916_b,fed_presser_0729`(720 가공본).
- **데모 권리 레지스트리**: `python -m tools.commons_fetch bundles projects/fed_timeline_demo`(G3 §0 — 없으면 데모 테스트 실패).
- **fed 트럼프 초상**(AI 연출가가 pressure 장면에 건 뱃지): 랫클리프의 라이브러리 가공본 `trump.png` + rights_registry `people.trump`(repo_library, Commons 공식 초상 PD) 복사. credits.yaml 에 `license_ref: trump`.
- 테스트 워크트리: 커밋마다 인덱스를 임시 커밋으로 떠 `git worktree` + 자산 심볼릭 링크(`mkwt.sh`)에서 전체 pytest.

## 1. 커밋과 증명

| § | 커밋 | 증명 |
|---|---|---|
| §0 | 485b1bf | docs 8 OK |
| §G 버전 도장 | 455eafd | `golden_delta/version_stamp.json`(25_END 86px 도장 상자 안 100 %), `hormuz_baseline.json`(도장 가린 md5), 테스트 5 |
| §D 합성 직전 사전 | 619b6a1 | 캐시 키 변화 fed 9·hormuz 4·랫클리프 1, 테스트 4 — 이 커밋에 옛 기사 카드 테스트 삭제가 잘못 함께 들어감(이력 보존) |
| §A 축 스케일 | 5e3f798 | 데모 변화 3회(1300→40→1300→2830), 테스트 8 |
| D-0123 backdrop·아일랜드 | a4cf81a | 테스트 20(backdrop 10·island 10), 무대·이벤트 레지스트리 세 곳 |
| §C 기사 프레스 v2 | 88a19ea | `golden_delta/article_press.json`(15_review_0·19_debate_0 두 컷만), 테스트 11 |
| 보정 ① | 65eda77 | backdrop 시간축 앵커 판정 = date·lane 쌍(statement_diff 라벨 date 오인 — 연출가 3회 거부 원인), 연출 문법 2줄 |
| 보정 ② | 2b9ae07 · c46573b | `[island-overlap]` 상세에 이벤트 이름, `resolve_refs` 가 태그 모양·줄인 상세도 검사 id 로 — 수정 회차 3회 거부 원인(llm_calls 원문) |
| §E fed 재연출·데이터 | d885a7c | 아래 §3 |

## 2. 명령

```bash
python -m script.plan projects/fed_policy_2026 --tts edge            # §D 재합성 9문장(total 307.12 → 307.67초)
# 기존 AI 연출(v7, 시간축 무대 w 변화 9회)을 버리고 연출가부터(ai_direction_run 은 direction.yaml 이 없을 때만 연출가를 부른다)
rm projects/fed_policy_2026/direction.yaml && python tools/ai_direction_run.py projects/fed_policy_2026 --preview auto
python -m engine.render projects/fed_policy_2026 --jobs 3 && python -m audio.mix projects/fed_policy_2026 && python -m engine.mux projects/fed_policy_2026
python -m engine.render projects/hormuz_korea --chunk 4800 5520 hz_chunk.mp4      # 200–230초(기사 19_debate_0)
ffmpeg -i hz_chunk.mp4 -f f32le -ar 44100 -ac 2 -ss 200 -t 30 -i projects/hormuz_korea/out/mix.f32 -map 0:v -map 1:a \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -shortest hormuz_article_200-230s_480p.mp4
# 연준 Flickr 3장(Q5 A): 레지스트리 등재 후 media_fetch --only fed_eccles_ext,fed_boardroom,fed_eccles_atrium(페이지 license 번호 코드 확인)
```

## 3. 측정

### 3.1 fed AI 재연출(W1.1 사람 루프 = Fable 검토)

| 회차 | 결과 |
|---|---|
| 연출가 1~3·5~6 | 거부 — 차트 아일랜드 시각 겹침, statement_diff 인용 174자 > 160, **statement_diff 라벨 date 를 시간축 앵커로 오판(내 검사 결함 → 보정 ①)** |
| 연출가 v8 | 통과 — stage backdrop, 배경 6장(서로 다른 6장·연속 같은 사진 0), 차트 아일랜드 1개(box left, open_2 ~ 끝), 시간축 숏 3개 |
| v8 프리뷰 | checks hard 2(island_overlap: statement_diff·dot_plot 가 차트 상자와 겹침) |
| 수정 회차 1~3 | 거부 — issue_ref 모양 불일치(보정 ②) |
| v9·v10 | 검사 hard 0. 검수 v1 hard 4·soft 7, v2 hard 5·soft 3 → 상한 2회, **v9 선택**(checks·qa_hard·qa_soft 사전식) |

- v9: 수정 LLM 이 겹친 프리미티브 둘(statement_diff·dot_plot)을 같은 시각·같은 태그의 카드로 바꿨다(인용 문구는 원고 범위).
- 축 스케일: w 변화 2회(900→360 at 78.61 open→hold_2026, 360→2900 at 282.51 엔딩 조망) — `[timeline-rescale]` 0.
- 아일랜드 레인 척도 74.667(= min(96, 224÷3)).
- 기사 2건 theme dark, press 없음(연출가 선택) → 블러 무대, 헤드라인 원문(CNN·Fox Business).
- **남은 검수 hard 4(v9)**: p_0108.39·p_0290.41 시간축 마커 라벨 겹침(날짜가 가까운 핀), p_0249.80 점도표 카드가 차트 오른쪽 위 가림, p_0215.15 "비어 있음" = 기사 프레스 단독 1초 구간(설계 — 블러 무대만 보이는 순간). 게이트 ② 판단은 Fable.

### 3.2 전편·클립

| 산출물 | md5 | 길이 | 비고 |
|---|---|---|---|
| fed_policy 480p | `8ff240ed7d75b397149e381fed567bea` | 307.67초 | 렌더 167초(jobs 3), I −14.06 LUFS·TP −1.63, checks hard 0 · warning 2(media_beats·endcard_roll) |
| hormuz 기사 클립 200–230초 | `47fc96fba97387ee8caad97eca36fde1` | 30.00초 | 19_debate_0 블러 폴백·번역 헤드라인 |

artifacts `phaseG12-v5.1.0`(d3dc8c6): 위 두 영상, fed 프리뷰 22컷·검수·수정 기록, 시트 6장(fed 전/후, 기사 전/후 hormuz·fed, 엔딩 카드 전/후 hormuz·fed).

### 3.3 골든

hormuz 25컷: 25_END(도장, 86px 상자 안)·15_review_0·19_debate_0(기사 프레스 v2)만 변경, 22컷 phaseG10 과 바이트 동일. 랫클리프·데모(지도·시간축) 무대 무변경 — 데모는 둘째 숏 w 만(§A).

## 4. 판단 기록(되돌릴 수 있는 선택)

| 쟁점 | 선택 | 근거 |
|---|---|---|
| default_stage 키 | 장르 프로필 `stage.primary` 를 그대로 읽음(`Direction.default_stage()`) | 같은 값을 두 곳에 두지 않는다(P3) |
| 아일랜드 박스 | 이름 3개(center·left·right), 높이 같음 | 연출 LLM 은 픽셀을 다루지 않는다, 레인 영역 한 벌 |
| backdrop 뱃지 | 화면 슬롯 점에 화면 고정(over_panel 경로) | 월드 앵커가 없는 무대 |
| 기사 층 | 카드 층 뒤·날짜·자막 앞 | 화면 전체 덮개가 카드를 덮고 자막은 남는다 |
| 버전 도장 기준선 | 도장 상자 가린 md5 | 버전마다 골든 재등재 불필요 |
| fed 재연출 방식 | 연출가부터(revise 아님) | 무대 교체는 "지적받지 않은 부분 불변" 수정 회차로는 불가 |
