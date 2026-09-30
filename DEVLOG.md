<!--
tier: 3
last_synced_with: v2.0.0
ssot_for: [development-log]
depends_on: [CHANGELOG.md]
last_review: 2026-06-06
-->

# DEVLOG

본 문서는 개발 과정의 의사결정·시행착오·구조적 학습을 시간 순서로 누적합니다.
**append-only**입니다. 과거 항목 수정 금지.

각 엔트리 포맷:

```
## YYYY-MM-DD vX.Y.Z — {짧은 제목}

- 무엇을: …
- 왜:    …
- 어떻게: …
- 결과:  …
- 연관:  AP-번호, 이슈, PR 번호 등
```

---

## 2026-09-28 v2.5.0 — Phase 6 완료: 관계·연표 데이터화, 카드 RESERVED, v2 차트 6종

- **무엇을**: 관계 패널 `relation`(v3 refusal 교체), 연표 자동 층, 카드 RESERVED(뱃지 회피·마커 라벨 흐림), v2 차트 dots·gantt·dual_line·fork·checklist·network 이식, 추정 태그·검증 라벨.
- **왜**: back_and_forth D-0032. 패널을 코드가 아니라 데이터로 만들고, 08 §3 정돈된 관계선 규칙과 08 §10 임시 조치(부산 뱃지)를 기능으로 해소한다.
- **어떻게**: 수치는 rules `panels.*`(test_no_magic_numbers). 데이터가 준 층·배치는 코드가 바꾸지 않는다(P8). 뱃지 이동 = 카드 존재도 층별 적분 — 카드 교대 때 24 px 점프를 없앴다. 추정 태그는 C0 모서리 규칙 때문에 제목 아래(D37).
- **결과**: 25컷 판정 23컷 MAD 0, 의도된 차이 3컷(09·15·16), 부산 겹침 4464→0 px², pytest 527 passed / 3 xfailed.
- **연관**: D36·D37, R0027~R0033, artifacts/phase6-v2.5.0.

## 2026-09-28 v2.4.0 — Phase 5 완료: 엔티티·휘장 레지스트리, 권리 대조 크레딧

- **무엇을**: `assets/entities.yaml`, `assets/emblems/registry.json`(제한 → 국기 대체 코드 확정), `commons_fetch`·`portrait_fallback`, 이름→뱃지 제안, 엔딩 크레딧 권리 대조(`RightsError`), prep_people_flags 삭제.
- **왜**: back_and_forth D-0029. 새 영상의 인물·휘장·국기를 코드 수정 없이 레지스트리로 붙이고, 권리 없는 자산이 영상에 들어가지 못하게 한다(C9, P6).
- **어떻게**: Restrictions 가 있으면 파일의 decision 을 손으로 `use` 로 바꿔도 로드가 실패한다. 크레딧은 렌더가 실제로 쓴 이미지 키와 레지스트리를 대조한다. 폰트는 설명문에만(D35).
- **결과**: 25컷 Phase 4 대비 mean 0.0033·max 0.047 PASS, 새 컨테이너 자산 md5 42/42 동일, pytest 489 passed / 3 xfailed. 세션이 두 번 끊겨 재기동 4에서 마무리(21 문서).
- **연관**: D35, M3, R0023~R0026, artifacts/phase5-v2.4.0.

## 2026-09-28 v2.3.0 — Phase 4 완료: 원고 린트·단어 정렬, 목소리를 바꿔도 연출 무수정 싱크

- **무엇을**: 원고 린트(오류/경고), ElevenLabs with-timestamps·edge WordBoundary 정렬 공통 형식, trim_offset, at_word 정렬 경로, TTS-AP-064~066, legacy_v3 삭제(자산 부트스트랩만 tools/bootstrap_assets 로 격리).
- **왜**: back_and_forth D-0021. 목소리 교체 시 연출 파일을 고치지 않고 전환이 발음에 붙어야 한다(03 §6.3).
- **어떻게**: edge 단어 경계를 실측해 보니 글자 비율 추정은 최대 0.97초 어긋났다 → edge 도 정렬을 저장(D34). 정렬 없는 캐시 = 재합성. 골든은 PNG 를 두고 의도된 차이 1컷만 등재.
- **결과**: InJoon→SunHi 전편, direction.py 동일, 전환−경계 ≤1 ms, Δ전환=Δ경계 7/7, 25컷 동일 구성. pytest 457 passed / 3 xfailed.
- **연관**: D30~D34, TTS-AP-064~066, LLM-AP-006, R0018~R0021, artifacts/phase4-v2.3.0.

## 2026-09-27 v2.2.0 — Phase 3 완료: 지오 일반화, 새 권역 한 줄 준비

- **무엇을**: prep3 지오·티어 코드를 권역 인자 `geo/` 패키지로. hormuz 자산 재생성, 대만해협 예시 권역.
- **왜**: back_and_forth D-0015. 새 영상마다 코드 수정 없이 `geo.yaml` 한 장으로 지도를 준비하려고.
- **어떻게**: 수치 v3 그대로, 타일은 티어 범위만 모자이크(누락 = 오류), land-miss 는 픽셀 면적 임계(D29)로 small/drop.
- **결과**: base 9장 md5 동일, 25컷 MAD 0, 전편 md5 동일. 대만해협 8초 준비. pytest 428 passed / 6 xfailed.
- **연관**: D29, R0015, D0017(M2), D0018(이름 체계).

## 2026-09-27 v2.1.0 — Phase 2 완료: render3·plan3·mix3 분해, 새 엔진 전편이 Phase 1 과 바이트 동일

- **무엇을**: `engine/`·`script/`·`audio/` 패키지와 `projects/hormuz_korea/`(원고·연출·라벨·크레딧·설명문)로 v3 를 분해. CLI 4종(script.plan·engine.render·audio.mix·engine.mux).
- **왜**: back_and_forth D-0010. 이후 Phase(레이아웃 데이터화·장르 확장)가 한 파일 997줄이 아니라 모듈·레지스트리·스키마 위에서 움직이게.
- **어떻게**: 수치·로직은 한 글자도 바꾸지 않고 모듈 전역을 RenderCtx 로 모음. 이벤트는 렌더 전 Pydantic·레지스트리·권리 점검. 패널 문구는 이벤트 필드(D25). post 는 planned 로(D26).
- **결과**: video_noaudio·final.mp4 md5 가 Phase 1 과 같음, mix 샘플 동일, 25컷 MAD 0. pytest 420 passed / 6 xfailed.
- **연관**: D23~D26, R-0010~R-0012, artifacts/phase2-v2.1.0.

## 2026-09-27 v2.0.0 — Phase 0 완료: 레거시 삭제·버그 테스트 전환·WSL2 절차

- **무엇을**: 사용자 허용으로 커밋 ② 실행(준비분 선커밋 → archive 원격 확인 → git rm). 버그 테스트 2건을 올바른
  기대값 + strict xfail로 전환(D18). WSL2 설치 절차 문서(D9).
- **결과**: pytest 388 passed / 8 xfailed, §5.8 5/5 충족. strict xfail 2건(② 의존)이 설계대로 XPASS → 마커 제거.
  클라우드 Ubuntu 24.04에서 설치 절차 검증: check_env 11 누락 → 20 ok.
- **연관**: DECISIONS D9·D17·D18, docs/handoff/reports/PHASE0_REPORT.md

## 2026-09-27 v2.0.0 — Phase 0 중간 보고: 커밋 ② 보류 (권한 거부)

- **무엇을**: Phase 0 커밋 ①③④⑤⑥ 완료, 보고서 `docs/handoff/reports/PHASE0_REPORT.md`. 커밋 ②(레거시 삭제)는
  실행 환경 권한 분류기가 대량 `git rm`을 거부해 보류. archive 브랜치는 생성·푸시 완료.
- **결과**: pytest 470 passed / 8 xfailed(기준선 438). §5.8 중 3/5 충족, 2개는 ② 대기. 사용자 결정 대기: ② 실행 방식, D4, D9.
- **연관**: DECISIONS D10~D16

## 2026-09-27 v2.0.0 — 워커 프롬프트 파일 분리, script 프롬프트의 고정 길이 제한 삭제

- **무엇을**: 워커 5종의 system prompt 상수 + user 템플릿 4종 + 카테고리 가이드를 `prompts/`로 옮김.
  `prompts/script.md`에서 "영상 길이는 4~6분(약 240~360초)으로 제한" 문단을 **삭제**(분당 320자 추정 문장은 유지).
- **왜**: `docs/handoff/15` P3 — 코드 상수 프롬프트는 문서 규칙을 바꿔도 옛 관점을 유지한다. 4~6분 제한은
  고정 구성의 뿌리(GOAL G4-13, 19 §1.4).
- **어떻게**: AST로 원문 상수를 추출해 파일에 그대로 쓰고, 로더 결과가 원문과 바이트 동일한지 확인한 뒤 상수를
  제거. 그 외 문안 개정은 Phase 6.9. user 템플릿은 19 명세 밖이지만 같은 P3 위반이라 함께 옮김(D15).
- **결과**: pytest 463 passed. 렌더된 프롬프트는 script 의 삭제 문단 외 원문과 동일.
- **연관**: docs/handoff/15 P3, 19 §5.5, DECISIONS D15

## 2026-09-27 v2.0.0 — Phase 0 착수: 헌법 개정(영상 기준 → docs/handoff, 관성 방지 C11)

- **무엇을**: CLAUDE.md C0/C0.1/C11, GOAL.md G0/G1/G3 배너/G4-13~20/G5/G7, HANDOFF 다음 할 일, README
  진입점, `tools/check_env.py` 신설.
- **왜**: `docs/handoff/15` P7 — 헌법에 옛 영상 기준이 남아 있으면 새 기능이 "규칙 위반"으로 되돌려진다.
  개편 첫 커밋은 헌법부터 바꾼다.
- **어떻게**: `docs/handoff/19` §5.1 명세 그대로. GOAL은 삭제 금지 규정(DOCS_GOVERNANCE)에 따라 옛 항목을
  `[deprecated v2.0.0]`으로 마킹만 했다. G3 개정안(19 부록 C)은 D4 사용자 승인 대기.
- **결과**: 기준선 pytest 438 passed(87 subtests). check_env: 이 클라우드 컨테이너는 pycairo·shapely·
  scipy·edge-tts·cairosvg·fonttools·rembg·폰트 4종 누락(exit 1) — Phase 1 전에 해결 필요(D9).
- **연관**: docs/handoff/15, docs/handoff/19 §5.1

## 2026-09-27 v1.2.2 — v2 전면 개편 착수: overhaul/v2-map-engine 분기 + 핸드오프 반영 + LLM 모델 고정

- **무엇을**: (1) 사용자 승인으로 `origin/collage`에서 `overhaul/v2-map-engine` 분기.
  (2) claude.ai 채팅 세션의 지도 중심 다큐 파이프라인 인계 문서 묶음을 `docs/handoff/`로 커밋.
  (3) Fable 분석 세션의 저장소 실측·불일치 판정·Phase 0 커밋 단위 명세(`19`), v3 코드
  인벤토리(`19a`), Opus 착수 프롬프트(`OPUS_KICKOFF_PROMPT.md`). (4) `claude -p --model` 고정.
- **왜**: 사용자 지시 — 분석·계획은 Fable, 개발은 Opus 5.5. 개편은 "주입 대신 교체"(handoff 15)
  원칙이며 첫 조건은 실행 세션이 추측할 여지를 없애는 것. 모델은 저장소에 고정된 적이 없었다.
- **어떻게**: collage ⊇ main 확인(35 commits, 역방향 0) → collage 분기. 골든 mp4와 PNG 25장
  픽셀 대조(MAD 0.00) → mp4 미커밋. TTS-AP 번호 충돌(058~063 기존) → 신규는 064~066. 소수점
  발음 정책 충돌(쩜 vs 점) → 사용자 결정 D6. `{model}` placeholder + `resolve_model()` +
  `LLMCallRecord.model`. 같은 내용을 main 기준 `claude/laughing-rubin-rujpp2`(v0.43.5)에도 남김.
- **결과**: 테스트 438건 통과(신규 7건 포함). Phase 0(v2.0.0) 착수는 D2·D8 답 후 Opus 세션.
  main 머지는 Phase 승인마다 fast-forward 권고(19 §4.1).
- **연관**: docs/handoff/15 P3·P5, docs/handoff/19 §3·§4·§5.

---

## 2026-08-15 v1.1.0 — Phase 2 완료: 인물 컷아웃 라이브러리 17인

- **무엇을**: 코어 인물 사진 수집 → codex `$imagegen` 가공 → 육안 검수 → 배경 제거 →
  라이브러리 등록까지 Phase 2 전 구간을 완주. 컷아웃 17장 + manifest.
- **어떻게**: 공방 도구 5종 신설. codex 는 **이미지 생성만** 맡고 수집·프롬프트·배치·검수·
  알파 추출·등록은 오케스트레이터가 수행.
- **결과**:
  - 사진 수집 19인(1인 보류) → 가공 17인 → 컷아웃 17장, 전경 비율 54~67% 균일.
  - manifest 는 `AssetLibraryManifest` 검증 통과. rights/tool/prompt_ref 전량 기록(G4-10).
- **막혔던 것 3건**:
  ① `codex exec` 배치 16/16 실패 — `-i` 가 가변 인자라 프롬프트를 삼킴. `--` 로 해결.
  ② 한글 프롬프트가 파이프에서 mojibake → codex 가 스스로 영어로 재작성. 템플릿을
     영어로 전환(모델 지시 정확도도 상승).
  ③ 배경 제거가 어두운 정장을 먹어 4인이 얼굴만 남음(전경 30%대). `background_mask`
     기본 tolerance 45 는 복잡한 사진 배경용 — 순백 배경 생성물엔 12 가 맞다.
- **육안 검수의 값어치 (자동 필터가 못 잡는 것)**:
  - `kim_jong_un` 후보가 **분장 배우 사진**이었다. 라이선스는 정상 통과 — 대조 없이는
    가짜 얼굴이 라이브러리에 등록됐을 것이다.
  - 해상도 하한을 올리자 개인 초상이 밀려나고 단체컷이 올라오는 **역효과** 발생.
  - **AI 오판 1건**: `bezos` 생성물을 딴사람으로 보고 반려했으나 사용자가 정상이라 정정.
    이미 `--force` 로 덮어써 원본 복구 불가(생성은 비결정론) → 재생성본 채택.
    교훈: 인물 동일성 판정은 **원본 대조 시트**로만 하고, 되돌릴 수 없는 덮어쓰기 전에
    사용자 확인을 받는다.
- **미결**: codex 투명배경 직접생성은 배경 제거 단계를 없애지만 **인쇄 질감이 약해진다**
  (실측 비교 `texture_compare.png`). 현재는 질감 우선으로 흰 배경 + 알파 추출 유지.
- **연관**: assets/library/workshop/*, docs/17 §1.7.0, 계획 §9 Phase 2, v1.0.13.

---

## 2026-08-15 v1.0.9 — 컷다운 슬롯 예산제 + 인물 자산 방식 B 확정

- **무엇을**: (1) 컷다운을 "중요도 순 N문장"에서 **씬 슬롯별 예산제**로 개정, (2) 인물
  라이브러리 자산 생성 방식을 **방식 B(인물만 굽고 섀도는 런타임)**로 확정하고 전용
  프롬프트 템플릿 신설.
- **왜**:
  (1) 사용자 지적 — "번들에 기승전결이 있는데 기·승까지만 담기고 내용이 잘리는 거 아니야?"
      정확한 지적이었다. 중요도 순으로 채우면 결말이 잘린다.
  (2) 스타일 앵커 시트가 섀도까지 구운 완성 패널이라, 그대로 19인을 뽑으면 액센트 색이
      파일에 굳어져 "영상마다 카테고리 액센트가 달라진다"는 설계가 깨진다.
- **어떻게**: 실번들의 서사 구조를 실측했더니 **기·전·결이 섹션 배열 바깥에 따로 있었다** —
  기=`report.video.intro_narration`, 전=`contradictions[].video`, 결=`outro_narration`.
  그래서 이 셋에 예산을 먼저 배정하면 섹션을 아무리 잘라도 이야기가 끝까지 간다.
  잘리는 건 승(EVIDENCE)뿐.
- **결과**:
  - 예산: HOOK 1 + CONTEXT 1~2 + EVIDENCE 잔여(~12) + TURN 3 + CLOSING 2 ≈ 19문장 ≈ 95초.
    v1.0.8 에서 발견한 "상위 2섹션 = 40~60초 미달" 문제도 함께 해소.
  - "선정은 중요도로, 배치는 번들 원래 순서로" 재정렬 규칙 추가 (안 하면 논지가 뒤엉킴).
  - 부수 발견: `contradictions[].video` 가 `label_a`/`label_b`/`line_a`/`line_b` 를 갖고
    있다 — **좌우 대립 구도 화면을 번들이 이미 설계해 넘겨준다.** TURN 씬 조판에 그대로 사용.
  - 인물 자산: 19인 × 5카테고리 = 95장 → **19장**으로 축소. `portrait_cutout.md` 신설,
    `portrait_panel.md` 는 검수 전용으로 강등(오용 경고 최상단 배치).
  - 남은 위험: 생성물 배경 제거 시 머리카락 경계 품질 미지수 — 첫 인물에서 실측 판정.
  - 431 중 429 통과 (잔여 2건은 기존 `.env` 환경 의존 실패, 본 변경과 무관).
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §5.3.0·§5.3.1,
  docs/17_COLLAGE_DESIGN_SHEET.md §1.7.0, workshop/prompts/portrait_cutout.md, v1.0.8.

---

## 2026-08-15 v1.0.8 — 파이프라인 트리거 확정 (URL 투입) + 실번들 검증

- **무엇을**: 번들 → 영상 파이프라인의 트리거를 "사용자의 번들 URL 투입"으로 확정하고
  (계획 §6.0.2 신설), 미뤄둔 "③ 자동 캐치 트리거"를 폐기. 사용자 제공 실번들 URL 로
  현행 파서를 실측 검증.
- **왜**: 사용자 확정 — "모든 json 을 영상으로 만들 건 아니고 영상으로 만들법한 녀석들만
  선택할 것." 선별이 사람의 판단이므로 자동 감지는 알람 소음만 만든다.
- **결과**:
  - 워처 CLI + push 알림 + 상시 데몬/실행 위치 결정이 통째로 소멸 (설계 부채 -1).
  - 대신 `import-bundle --url` 이 봇 슬라이스의 선결 작업으로 승격 — 현행
    `import_report_bundle(project_id, bundle_path: Path)` 는 로컬 파일만 받는다.
  - **Cloudflare Pages 가 기본 urllib UA 를 403 으로 차단** (실측). 브라우저 UA 필수.
  - 실번들 파싱 **통과**. 최상위 15키 전부 모델링, 섹션 11개 전부 video 블록 보유.
  - **§5.3 컷다운 수치가 안 맞는다 (미해결)**: "상위 2섹션" 규칙이면 10문장 → 40~60초로
    90~120초 타깃 미달. Phase 4 착수 전 상위 섹션 수 재확정 필요.
  - `bundle_service` docstring 의 `extra="forbid"` 는 오류였다 (실제 `extra="ignore"`) —
    미지 필드가 조용히 버려지므로 계약 확장 감지를 이 파서에 기대면 안 된다. 정정.
  - `contradictions` 2건이 각각 video 블록 보유 → TURN 씬 데이터 원천 후보 발견.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §6.0.2, HANDOFF 미뤄둔 목록 2번,
  orchestrator/bundle_service.py, v1.0.7.

---

## 2026-08-15 v1.0.7 — 참조 자료 정리 + 시트 샘플이 드러낸 축 보강

- **무엇을**: 사용자가 `workshop/references/` 에 배치한 자료 8종을 식별·명명·권리 기록하고,
  그 중 시트 샘플 3종이 드러낸 구조적 격차를 규약에 반영 (여백 축 / 플레이트 ID /
  display_name).
- **왜**: 사용자가 "내가 생각하는 바람직한 스타일 시트"로 샘플을 제시. 우리 시트와 비교하니
  실제 구멍이 나왔다.
- **어떻게**: 자료를 kind 3종(`style_anchor_` / `sheet_sample_` / `collage_sample_`)으로
  분류. 파일명이 196자 base64 라 Windows MAX_PATH 때문에 git 이 색인조차 못 하던 것을
  long-path API 로 개명.
- **결과**: 샘플에서 배운 것 3건 —
  ① `sheet_sample_editorial_vs_swiss` 의 Shared Rules 4축(Layout/Palette/Type/**Whitespace**)
     → 우리에게 여백 축이 없었다. `space_` 그룹 + `DesignSheet.spacing` 신설, 토큰 5종.
  ② `sheet_sample_meridian_linen` 의 플레이트 ID(`PL 01/24`, `P 01`, `S 05`)
     → 블록 단위 지시 수단. 프리뷰 게이트가 전체 승인/전체 리롤로 퇴화하지 않으려면 필수.
  ③ 같은 샘플의 `MERIDIAN · LINEN` 표기 → `display_name` 신설 (기계 키와 사람 이름 분리).
  콜라주 샘플 4종도 어휘로 매핑 — `collage_sample_paper_stopmotion_desk` = 놓기 모션의 원형,
  `collage_sample_string_connector` = §2 #8 StringConnector 의 시각 원형.
  테스트 25 → 33 통과.
- **주의**: `sheet_sample_*` / `collage_sample_*` 은 출처 미상 수집 이미지라 **내부 설계
  참조 전용**. 배운 것은 어휘로 추상화해 17 에 기록하고 픽셀은 재사용하지 않는다 (C9).
- **연관**: docs/17_COLLAGE_DESIGN_SHEET.md §0.2·§0.9·§0.10·§1.35,
  assets/library/workshop/references/RIGHTS.md, v1.0.6.

---

## 2026-08-15 v1.0.6 — 디자인 시트 명명 규약 정규화 (17 §0)

- **무엇을**: 시트 자체의 ID 문법과 시트에 들어가는 전 항목(토큰·컴포넌트·변형·씬·enum·
  자산 파일명)의 명명 규약을 17 §0 으로 신설하고, `DesignSheet` validator 로 집행.
  정식 시트 `design_sheets/shorts_collage_v1.json` + 회귀 25건 신설.
- **왜**: 사용자 지적 — "스타일 시트 자체의 명명법과 각 항목의 명명법을 정규화해야 나중에
  재활용할 수 있다." 실제로 규약 부재로 인한 드리프트가 이미 3건 누적돼 있었다.
- **어떻게**: 그룹 접두어 9종(`paper_`/`ink_`/`accent_`/`stamp_`/`mark_`/`prop_`/`bg_`/
  `type_`/`motion_`) + motion 단위 접미어 필수(단일 스칼라 보증) + CSS 변수 기계 매핑
  (`token_key` ↔ `--token-key`, 예외 없음) + `to_css_vars()` 로 주입.
- **결과**: 발견·해소한 드리프트 3건 —
  ① 모션 토큰 7개 중 4개(`push_in_scale`·`paper_breath`·`grain_loop`·`draw_on`)가 복수값·
     비수치라 `dict[str, float]` 직렬화에서 **유실**되던 것을 스칼라 12개로 분해.
  ② 코드에만 있던 `--paper-card`·`--hl-yellow` 를 정규 토큰으로 흡수.
  ③ 문서가 `string_red` 를 "붉은 실·형광펜" 겸용으로 기술했으나 실제 형광펜은 노란색 —
     `prop_string`/`mark_pen`/`mark_highlighter` 로 분리.
  스페시먼 개명 후 재렌더 결과는 개명 전과 동일(순수 리네임 확인). 420 중 418 통과 —
  잔여 2건은 본 변경과 무관한 기존 환경 의존 실패(`test_audio_flow` 가 사용자 `.env` 의
  실제 ElevenLabs 키·voice ID 를 읽어 "키 없음" 가정이 깨짐).
- **연관**: docs/17_COLLAGE_DESIGN_SHEET.md §0, schemas/models.py `DesignSheet`,
  tests/test_design_sheet_naming.py, v1.0.5.

---

## 2026-08-15 v1.0.5 — 세션 핸드오프 (로컬 PC 세션으로 전환)

- **무엇을**: HANDOFF.md 를 개편 세션(v0.43.5~v1.0.4) 전체 기준으로 갱신 — 확정 결정 8건
  요약, 구현물 목록, Phase 2 절차, 로컬 git pull 미실시 경고(사용자 확인)와 복구 절차,
  세션 확립 규칙.
- **왜**: 사용자가 클라우드 세션을 종료하고 로컬 PC(cmd, Windows) Claude 세션에서 계속
  진행하기로 함 — codex $imagegen 공방과 실음성 렌더가 모두 로컬 자원이므로 합리적 전환.
- **결과**: 다음 세션은 HANDOFF 🔥 블록 → 계획 §9·§10 순으로 읽으면 맥락 복원 완료.
  대기 중 사용자 입력: 인물 라인업 O/X, 스타일 앵커 배치, (후속) voice 오디션.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md, workshop/AGENTS.md, v1.0.4.

## 2026-08-15 v1.0.4 — codex $imagegen 스모크 테스트 통과 (사용자 검증)

- **무엇을**: §2.0.1 검증 완료 표기. 사용자가 Windows codex 에서 `/skills` 확인 →
  `$imagegen` 스모크 실행 → 에디토리얼 포스터 PNG 생성 성공 (기하 콜라주 + 하프톤 질감,
  품질 우수). 4인물 스타일 앵커 시트도 채팅으로 전달받음 (원본 파일은 사용자 머신 보유).
- **왜**: v1.0.3 의 알려진 이슈(스킬 미노출) 해당 여부 확인이 Phase 2 착수 전제였음.
- **결과**: 이미지 가공 체인 전 구간 검증 완료 — 남은 Phase 2 선행은 라인업 확정과
  스타일 앵커 파일 배치(codex 실행 머신 기준)뿐. 채팅 전달본은 재인코딩본이므로 정식
  앵커는 사용자 원본 파일을 references/ 에 두는 것으로 유지.
- **연관**: 계획 §2.0.1, workshop/AGENTS.md, v1.0.3.

## 2026-08-15 v1.0.3 — codex $imagegen 1순위 확정 + 자산 공방 스캐폴드

- **무엇을**: §2.0.1 개정(자동화 1순위 = codex CLI `$imagegen`, 구독 커버) + workshop
  스캐폴드(AGENTS.md·portrait_panel.md 템플릿·RIGHTS).
- **왜**: 사용자가 ChatGPT 확인 내용을 공유 — Codex CLI 에 GPT Image 2 스킬 내장
  (`codex -i` 첨부 + `$imagegen` 명시). v1.0.2 의 "codex 는 이미지 생성 무관" 판단은
  지식 컷오프 이후 기능으로 **정정**.
- **어떻게**: 사용자 4인물 시트의 실제 프롬프트를 표준 템플릿로 정식화(스타일 앵커 첨부
  + 가드 문구 + 섀도 3축 슬롯 + 이미지 내 텍스트 금지 + 4:5). AGENTS.md 로 공방 규칙을
  codex 가 자동 준수하게 함. 프롬프트 사본 저장 → manifest tool/prompt_ref 연결 (G4-10).
- **결과**: Phase 2 착수 준비 완료. 사용자 액션 — Windows codex `/skills` 확인 + 스모크,
  스타일 앵커 원본 PNG 를 references/ 에 배치, 인물 라인업 확정.
- **연관**: 계획 §2.0.1, GOAL G4-10, ADDENDUM_04, v1.0.2(정정 대상).

## 2026-08-14 v1.0.2 — 텔레그램→OpenAI 이미지 자동화 경로 설계

- **무엇을**: 계획 §2.0.1 — 스타일시트 생성 명령에서 이미지 생성까지 자동 연결되는 경로.
- **왜**: 사용자 질문 — "텔레그램으로 스타일시트 생성 시 chatgpt/codex 쪽으로 이미지 생성
  명령 전달이 가능한가."
- **어떻게**: 프로그램 호출 대상은 ChatGPT 앱이 아니라 OpenAI Images API 임을 명확화
  (`images.edit` 이 실사진 입력+스타일 앵커 동시 전달 지원 — G4-10 의 "실사 입력 가공"
  조건과 정합). 라이브러리 캐시 우선 → 미보유만 API → 프리뷰 low → 승인 후 고품질·고정.
  텔레그램 사진 첨부를 실사 입력 공급 경로로 활용(수집 실패 시 needs_user_upload 폴백과
  자연 결합). codex 는 이 경로와 무관(코딩 에이전트).
- **결과**: 문서 확정. AiImageWorker 는 Phase 2 도구로 구현 예정.
- **연관**: 계획 §2.0·§6.0.1·§3.0, G4-10 v1.0.0, C9.

## 2026-08-14 v1.0.1 — 기사·논문 타이포 스페시먼 (hyperframes/shorts 개시)

- **무엇을**: 갱지 위 기사·논문 카드 타이포 + 강조 마크(형광펜·밑줄·동그라미·화살표·날짜
  칩·검증 스탬프) 정적 스페시먼. Opus 위임, 4라운드 자체 검수 후 오케스트레이터 육안 검수
  통과. `hyperframes/shorts/` 첫 커밋.
- **왜**: 사용자 요청 — "기사나 논문 같은 것들의 타이포그라피와 강조 마크를 갱지 배경상에서
  보여주는 형태 테스트".
- **어떻게**: 최종 렌더러와 동일 기술(HTML+CSS + 저장소 실폰트) + Playwright 헤드리스
  스크린샷. 형광펜은 시각적 줄 단위 분할 + 줄별 상이한 swash·overrun(균일 사각 금지),
  손그림 마크는 필압 프로파일 채움 폴리곤. 사실성 — 기사 카드는 실번들 원문 그대로 +
  실존 매체 사칭 없는 자체 발행처 표기, 논문 카드는 JPE 게재본 초록 실발췌(생략 명시).
- **결과**: 결정론 렌더(SHA 동일) 확인. render_specimen.py 는 §6.0.1 스타일 프리뷰 시트의
  기술 기반이 됨. 한계 기록 — 컴포넌트化 시 폰트 로드 훅, 스탬프 배치 규칙.
- **연관**: 17 §2 #11 ArticleCollageCard·#4 StampLabel, 계획 §6.0.1, Phase 3 (v1.2.0).

## 2026-08-14 v1.0.0 — G4-10 전면 개정: AI 이미지 가공 허용 (MAJOR)

- **무엇을**: GOAL G4-10 개정 + CLAUDE C9 · 07 · 17 · 계획 §2 동기화 + 스키마
  tool/prompt_ref. ChatGPT 이미지 가공을 인물·텍스처 가공의 1순위 엔진으로 승격.
- **왜**: 사용자 결정 — "ChatGPT 쪽 이미지 가공 능력이 월등. 우리가 만든 우리 규칙에
  얽매이지 말자. G4-10 전면 개정을 해서라도 비주얼 우수한 방식 적용. ChatGPT 도 실사를
  갖고 가공하라고 시킨 것." 사용자 제작 4인물 시트 v2 가 품질 우위를 실증 (종이 질감·
  패턴 유기성·모노 중간조). 오케스트레이터는 얼굴 정확성·AI 라벨·일관성 리스크를 고지했고
  (v0.45.6 이전 권고), 사용자가 인지 후 개정을 지시 — 권고 기각 기록.
- **어떻게**: "실사 입력 → 가공" 골격은 유지한 채 엔진만 교체. 리스크 완화장치를 조항化 —
  무입력 사실 생성 금지 / 라이브러리 1회 고정(일관성·재현성 회복) / 도구·프롬프트 기록 /
  사실 텍스트 코드 렌더 / 검수 게이트 / 업로드 게이트에 플랫폼 AI 공개 정책 체크.
- **결과**: MAJOR 증분 v1.0.0 (C5.4 — G4 변경). 절차식 엔진(v0.45.x 산출)은 폴백으로 보존.
  Phase 2 (v1.1.0)는 ChatGPT 가공 기반 라이브러리 구축으로 재정의 — 표준 프롬프트 템플릿
  + 스타일 앵커가 첫 과제.
- **연관**: GOAL G4-10, CLAUDE C9, 계획 §2.0, 17 §1.7, v0.45.0(반려)~v0.45.7 흐름.

## 2026-08-14 v0.45.7 — OpenAI 진영 통합 지도

- **무엇을**: 계획 §2.1.6 — codex/ChatGPT 의 제작 체인 통합 지점 4개와 불변 경계 3개 명문화.
- **왜**: 사용자 — "OpenAI 진영을 써야 할 일이 분명히 있을 텐데 어떻게 통합하나."
- **어떻게**: 코드 확인 — base_llm_worker.py:206 `llm_backend` 인스턴스 override +
  models.py LLMCallRecord.backend Literal["claude","codex"] 기확인. 즉 브리지는 처음부터
  이중 백엔드 설계였고 통합은 설정·역할 배정 문제. 역할: V3 백엔드 A-B / 이종 모델 교차
  검증(모델 고유 오류 상쇄 — G4 에 실질 기여) / 비사실 소품 생성(보류) / 코드 작성.
- **결과**: 문서 확정. 구현은 각 Phase 에 귀속 (별도 작업 없음).
- **연관**: ADDENDUM_04, C10, 계획 §2.1.5·§6.0.1, LLM-AP 카탈로그.

## 2026-08-14 v0.45.6 — 스타일 프리뷰 게이트 + OpenAI 이미지 판단

- **무엇을**: 계획 §6.0.1(프리뷰 승인 후 렌더 흐름 + style_preview_review 게이트, Phase 5
  범위 편입) + §2.1.5(OpenAI 진영 이미지 생성 활용 판단).
- **왜**: 사용자 — ① "봇에서 바로 영상 만들지 말고 스타일시트 검수 먼저" (재렌더 비용 절감)
  ② "인물 가공·텍스처를 codex 에서 만들 수 있나 — OpenAI 가 이미지 생성 강점이라".
- **어떻게**: ① 은 기존 review_gates·art_direction 설계와 정합 — 승인된 JSON 이 렌더 입력
  이므로 검수·결과 일치가 구조적으로 보장. ② 는 지점 분리로 답 — 우리 가공은 생성이 아니라
  결정론 픽셀 연산이라 진영 무관(현행 유지), codex 는 코딩 에이전트일 뿐이며, OpenAI 이미지
  생성이 유효한 좁은 지점(비사실 소품)은 G4-10 예외 선행 필요로 보류.
- **결과**: 문서 확정. 봇 슬라이스는 로드맵 Phase 7 이후 (기존 결정 유지).
- **연관**: 계획 §6.0.1·§2.1.5·§2.2, config.yaml review_gates, ADDENDUM_04, C10.

## 2026-08-14 v0.45.5 — 섀도 3축 + 갱지 텍스처 구현 검증 통과

- **무엇을**: engraving_stylizer 확장 수용 — outline(정확 EDT 팽창)·hatch/dots(클리핑 패턴)·
  make_crumpled_paper(갱지). 테스트 29→38건, 4인물 데모 시트 육안 검수 통과.
- **왜**: 사용자 지시(감싸는 명확한 경계 그림자 + 패턴 채움 + 인물별 데모 + 갱지 배경).
- **어떻게**: Opus 위임. 팽창은 2-패스 분리 EDT(scipy 금지 제약 하에 반복 팽창의 마름모
  왜곡 회피). 갱지는 접힘선 부호거리 높이장 기울기 조명 — "유리 긁힘/천" 오독을 직선
  크리즈+wobble 로 교정한 시행착오 기록됨. 인물별 배경 플러드필 개별 튜닝(파월 열림 연산 9,
  푸틴은 깃발 접촉이라 크롭 프레이밍으로 해결).
- **결과**: 섀도 문법(2형태×3채움×N색)이 코드로 성립 — 자산은 인물당 mono 1장 그대로.
  검수 소견: 파월 outline 최상, 푸틴 hatch 는 오프셋 밴드가 좁아 판독 약함(밴드 확대 여지),
  mono 대비가 인물별로 상이(라이브러리 양산 시 인물별 톤 파라미터 기록 필요 — Phase 2 과제).
- **연관**: 17 §1.7.1·§1.2 paper_crumpled, v0.45.3~0.45.4.

## 2026-08-14 v0.45.4 — 하이브리드 표현 경제 + 갱지 배경

- **무엇을**: 계획 §1.2.5(3계층 표현 경제 + 전환 문법), 17 §1.2 `paper_crumpled` 토큰.
  섀도 데모를 4인물(트럼프/파월/푸틴/머스크, 라이선스 확인·수집 완료)로 재제작 지시.
- **왜**: 사용자 — "모든 걸 콜라주 기법으로 하면 비용이 많이 들 것" → 콜라주·실사·기존
  HyperFrames 표현의 하이브리드 제안. + 꾸겼다 편 갱지 배경, 인물별 섀도 데모 요청.
- **어떻게**: 비용 집중 원칙 — 풀 콜라주는 편당 2~3씬(HOOK·ACTORS·TURN), 실사·차트는
  기구현 경로 재사용, 등장 모션만 콜라주 물성으로 통일("놓이는 방식"이 세계관을 만든다).
  갱지는 절차 생성(결정론)이라 권리 self_made.
- **결과**: 문서 반영. 구현·데모는 Opus 진행 중 (후속 커밋).
- **연관**: 계획 §1.2.5·§3.0, 17 §1.2·§1.7.1, IMAGE_BUNDLE_CONTRACT.

## 2026-08-14 v0.45.3 — 수집 전략(하이브리드) + 섀도 문법 3축

- **무엇을**: 계획 §3.0(코어 사전 구축 + 온디맨드 승격 = 누적 캐시), 17 §1.7.1(섀도
  색·형태·채움 3축), 스키마 accent_hint/usage_count. 섀도 확장 구현(outline 팽창,
  hatch/dots 패턴 채움)은 Opus 위임 진행 중.
- **왜**: 사용자 질문 — 사전 라이브러리 vs 그때그때 수집 / 섀도 색 동적 / 감싸는 그림자 /
  패턴 채움 그림자 가능 여부.
- **어떻게**: 롱테일(무기·함정·랜드마크)은 사전 구축 낭비, 매편 전수집은 병목 → 등록 후
  사용 원칙으로 결정론 유지한 채 캐시 누적. 섀도는 전부 런타임 파라미터라 자산 증설 없이
  3축 조합(2형태×3채움×N색)이 나옴 — "같은 재료, 다른 연출" 변주 체계(§6.0)와 정합.
- **결과**: 문서·스키마 반영. 구현 검증은 후속 커밋.
- **연관**: 계획 §3.0·§6.0, 17 §1.7.1, schemas LibraryPerson/LibraryLogo.

## 2026-08-14 v0.45.2 — 스타일라이저 재작업 (스크리닝) 검증 통과

- **무엇을**: v0.45.1 방향대로 재작업된 `engraving_stylizer` 수용 — mono/mono_shadow/
  halftone/linescreen. 테스트 29건 OK, 결정론 SHA 동일, 샘플 4종 육안 검수 통과.
- **왜**: v0.45.0 반려의 구조적 교정 — "획 합성" 폐기, "사진 보존 + 인쇄 스크리닝" 채택.
- **어떻게**: 핵심 개선 3 — ① 디프린지(실루엣 밖 인페인트 후 언샤프 → 후광·테두리 제거)
  ② 백분위 하이라이트 클리핑(전경 14% 잉크 정확히 0 — "회색 안개" 해소) ③ 망점/선을
  규칙 격자로 (seed 는 위상만) → 노이즈가 아니라 인쇄 질감. 300px 축소 검수 시트로 확인.
- **결과**: mono_shadow 합성이 사용자 레퍼런스(NYT 콜라주 에딧)와 동급 구도 재현.
  잔여 흠: 머리카락 경계 흑점 소량(어두운 배경 구간 — 인물별 --bg-erode 튜닝 여지),
  halftone cell 5 에서 눈 디테일 소실 경향 (--cell 4.5 권장). 사용자 검수 대기.
- **연관**: v0.45.0(반려)·v0.45.1(규칙 개정), docs/17 §1.7 v2.

## 2026-08-14 v0.45.1 — 판화 반려 → 인물 표현 "모노톤+컬러 섀도" 통일

- **무엇을**: v0.45.0 판화 샘플 2종 사용자 검수 **전면 반려** ("진짜 최악. 완전히 가비지").
  사용자 재지시 — "그냥 배경 제거한 모노톤에 컬러 그림자" (본인 제시 NYT 콜라주 에딧 그대로).
  17 §1.7 v2 로 기본 표현 통일, 합성 판화 폐기, LibraryAssetVariant.style 에
  mono/halftone/linescreen 추가.
- **왜(실패 분석)**: ① 확률적 스티플은 규칙 격자가 아니라서 "인쇄"가 아니라 "노이즈"로
  읽힘 ② 합성 획은 얼굴 곡률을 실추종하지 못해 기계적 도배 ③ 목표 오설정 — 레퍼런스 인물의
  실체는 판화가 아니라 고대비 사진+인쇄 질감. 오케스트레이터 검수 기준("이목구비 식별")이
  낮았던 것도 원인 — 이후 인물 자산 검수 기준은 "프로 인쇄물로 보이는가"로 상향.
- **어떻게**: Opus 재작업 브리프 — 획 합성 폐기, mono(고대비 흑백)+compose_mono_shadow
  (실루엣 액센트 섀도 합성) 최우선, 스크리닝은 옵션. 문서·스키마 선반영(본 커밋), 코드는
  검증 후 별도 커밋.
- **결과**: 규칙 단순화로 라이브러리 생산 리스크 급감 (mono 는 알고리즘 실패 여지가 거의
  없음). 판화라는 원래 지향은 스크리닝 변주로만 잔존.
- **연관**: docs/17 §1.7 v2, docs/07 §2, 계획 §1.1·§3.2, v0.45.0 반려.

## 2026-08-14 v0.45.0 — Phase 1 완료: 판화 스타일라이저 PoC (Opus 5 위임)

- **무엇을**: `workers/engraving_stylizer.py` + 테스트 15건. 트럼프 2025 공식 초상(PD)으로
  stipple(58k점)/engraving(9.8k획) SVG+PNG 샘플 생성, 사용자 스타일 선택 대기.
- **왜**: 계획 §9 Phase 1 — 이후 전체 인물 생산의 기준이 될 스타일 확정용 실물.
- **어떻게**: 사용자 지시로 **Opus 5 서브에이전트에 구현 위임** (오케스트레이터=Fable 5 가
  계획·브리프·검증, Opus 가 코딩·자체 육안 개선 3라운드). 오케스트레이터 검증: py_compile /
  unittest 15건 / 샘플 육안 확인(이목구비 식별·계조 표현 합격) / C2 준수 확인. 알고리즘:
  언샤프 국소대비 + 계조 압축 + 가장자리 플러드필 배경 억제 → (stipple) 명도 가중 점 채택,
  (engraving) 물결 스캔라인 두께·진폭 변조 + flow warp + 암부 크로스해치. seed 결정론
  (동일 입력 = 바이트 동일 SVG). SVG/PNG 동일 지오메트리 이중 출력.
- **결과**: 테스트 전건 통과. 한계 기록 — 배경 제거 사진 의존(rembg/수동 마스크 후속),
  stipple 2.3MB(런타임 밀도 프리셋 필요), 윤곽 추종 해칭 미구현. requirements 에 numpy/Pillow.
- **연관**: SHORTS_COLLAGE_OVERHAUL_PLAN §3.2·§9 Phase 1, G4-10.

## 2026-08-14 v0.44.2 — 인물 샷 스케일 규칙 + ArticleCollageCard

- **무엇을**: 17 §1.7(클로즈업=판화 / 상반신·단체=모노톤+오프셋 섀도+하단 등장) + L2 #11
  ArticleCollageCard. 07 §2 동기화.
- **왜**: 사용자가 NYT 기사 콜라주 에딧 이미지를 제시하며 규칙 지정 — "얼굴 확대는 엔그레이빙,
  상반신·단체는 모노톤 + 한쪽 컬러 그림자 + 아래에서 등장".
- **어떻게**: 섀도는 컷아웃 실루엣 복제를 카테고리 액센트로 채워 6~10px 오프셋(런타임 처리 —
  자산은 흑백 cutout 1장, 스키마 불변). 레퍼런스의 기사 카드 문법(형광펜·날짜 칩·화살표·인물
  걸침)은 컴포넌트로 승격하되 기사 원문 변조 금지(G4) 명문화.
- **결과**: 문서 개정. Phase 3 씬킷 구현 대상에 편입.
- **연관**: docs/17 §1.7·§2, docs/07 §2, SHORTS_COLLAGE_OVERHAUL_PLAN §1.1.

## 2026-08-14 v0.44.1 — 변주 체계 신설 (기계적 시트 적용 금지)

- **무엇을**: 계획 §6.0 + 17 시트에 3층 변주 체계(V1 시드 / V2 콘텐츠 규칙+로테이션 /
  V3 ArtDirectorWorker) 명문화. 로드맵 Phase 5 삽입(총 Phase 0~7, ~v0.51).
- **왜**: 사용자 지시 — "톤은 유지하되 모든 영상이 똑같은 엘레먼트들이 나오는 영상은 누구도
  보지 않을 것. 디자인 시트가 탄탄하되 기계적으로 쓰는 건 옳지 않다."
- **어떻게**: 정체성(재료·라벨·위계·물성)과 연출(배경·구도·조합·조판)을 분리 — 전자는 시트가
  고정, 후자는 영상마다 변주. LLM(V3)은 계획 시점에만, 시트 어휘 enum 안에서만, 사실·라벨
  필드 접근 불가(스키마 배제) — 렌더 결정론·재현성(art_direction.json 이 재현 소스) 유지.
- **결과**: 문서 개정. 코드는 Phase 3~5 에서 구현. 동시에 Phase 1 판화 PoC 를 Opus 5
  서브에이전트에 위임해 병행 진행.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §6.0·§9, docs/17 §1.5~1.6, ADDENDUM_04.

## 2026-08-14 v0.44.0 — 쇼츠 콜라주 Phase 0 완료 (스펙·스키마 확정)

- **무엇을**: 07 v2 개정, 17_COLLAGE_DESIGN_SHEET 신설, 스키마 3묶음(Bundle video 블록 /
  AssetLibrary / DesignSheet) additive 추가, config 프로파일(render/tts), 테스트 5건.
- **왜**: 사용자 "이제 어떻게 실제 진행을 하면 되지?" — 결정 완료 항목(2분·톤·배포 3사·
  벤치마크)만으로 착수 가능한 Phase 0 을 즉시 개발.
- **어떻게**: video 블록은 계약(VIDEO_BUNDLE_CONTRACT)이 정의한 필드를 Pydantic 으로 정식
  모델링 — 라이브 변환기의 raw dict 우회(스키마 부채)를 쇼츠 변환기부터 해소할 토대.
  실번들(analysis_20260814_150031) 파싱 회귀로 검증(섹션 11개 video 전부 인식).
  기존 테스트 실패 2건은 fresh 컨테이너 의존성 누락(textual/fastapi)이었고 설치 후 전부
  통과 — 코드 회귀 아님.
- **결과**: Phase 0 산출물 완비, 사용자 문서 리뷰 대기. 다음: Phase 1 판화 스타일라이저
  PoC (트럼프 1인, stipple vs engraving 실물 비교).
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §9, docs/17, docs/07 v2, C7 동기화(05).

## 2026-08-14 v0.43.8 — 레퍼런스 영상 2건 프레임 분석 + 벤치마크·배포 대상 확정

- **무엇을**: 사용자 제시 유튜브 2건을 yt-dlp 스토리보드(sb0)로 받아 프레임 분석 (본편
  다운로드는 클라우드 봇 차단으로 불가, 스토리보드 모자이크로 대체). 계획서 §1.0 벤치마크
  신설 + §2.2 하이브리드 보류 옵션 + 멀티플랫폼 safe area.
- **왜**: 사용자 요구 — "이런 영상(`0XUixvTyQCA`) 이나 최소한 이 영상(`REGLr2rGvgs`
  0:35~1:16) 수준. 세로 기준, 유튜브·인스타·틱톡 배포."
- **어떻게**: 프레임 판독 결과 — 최소 기준 샘플은 종이 질감·흑백 판화 인물·선버스트·극장
  커튼 디오라마·검열바·스탬프·대형 자막 + 절제된 모션(푸시인·스포트라이트) = 계획 C안의
  결정론 스택으로 재현 가능한 문법. 상위 기준(Seedance)은 실사풍 캐릭터 액션·모프 전환이
  본질이라 생성형 전용. 튜토리얼의 제작 절차(콜라주 시트 → img2vid)가 C안과 동형임을 확인
  — 우리는 시트를 실사진 절차 가공으로, 모션을 HyperFrames 로 치환(G4-10 준수 유지).
- **결과**: "최소 기준 도달 가능, 상위 기준은 G4-10 개정 없이 불가" 판정. Phase 3 합격선을
  최소 기준 동급으로 상향. 하이브리드는 Phase 3 실물 검수 후 상정.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §1.0·§2.2·§5.1, GOAL.md G4-10.

## 2026-08-14 v0.43.7 — 음성 톤 확정 + 실번들 기반 실무 검토

- **무엇을**: 계획서 §7 개정 — 톤을 "정확한 인토네이션·딕션, 귀에 딱딱 꽂히는 전달"로 확정
  (사용자 지시). analysis_20260814_150031 번들(민주주의 vs 권위주의 AI 경쟁, 11섹션 37문장)을
  받아 실무 검토.
- **왜**: 사용자가 참고 번들 2 URL 을 주며 "가능한지 실무적으로 검토해봐" 요청.
- **어떻게**: 번들 파싱 — 전 섹션 video.narration(3문장씩)·narration_tts(숫자 한글화 완료)·
  emphasis 존재 확인 → 새 톤의 대본 측 전제(≤75자 단문 선언체) 이미 충족. 음성 체인 레버
  확인 — voice 교체는 `.env` 만, STABILITY/SIMILARITY/STYLE/SPEAKER_BOOST opt-in(v0.34.9) +
  문맥 스티칭(v0.38.3) + polish_tail 이 신톤 요구에 그대로 복무. 2분 컷다운 시뮬레이션:
  37문장 → 24문장(인트로2+섹션6~7+아웃트로2) ≈ 96~120s 성립.
- **결과**: "가능" 판정 + 권장 세팅 시작점 + 오디션 절차 문서화. 부수 발견: 이 번들 차트
  5종 중 3종(stakeholder_map/diverging_bar/donut)이 현행 변환기 미지원 스킵 — Phase 4 범위에
  편입. 코드 무변경.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §7·§9, docs/VIDEO_BUNDLE_CONTRACT.md.

## 2026-08-14 v0.43.6 — 쇼츠 길이 확정: 90~120초 (2분 상한)

- **무엇을**: SHORTS_COLLAGE_OVERHAUL_PLAN §5 개정 — 길이 45~60초안 → 90~120초, 문장 상한
  12→24, 씬 시간 예산 120초 기준 재배분, Bar 9항·결정 목록 #1 갱신.
- **왜**: 사용자 제안 "쇼츠 길이를 한 2분 정도로 하는 건 어때?" — 평가 결과 찬성. 60초안은
  컷다운이 가혹해(섹션 1개·12문장) 맥락·검증 라벨 구분·반전 구조가 빠듯했고, 2분이면 섹션
  2개 + 타임라인 + G4 라벨 여유가 생겨 채널 신뢰성 정체성에 부합. 유튜브 쇼츠 3분 규격 내.
- **어떻게**: 완주율 리스크는 HOOK 3초 법칙 + 씬당 3~6초 컷 + TURN 후반 이전 배치로 상쇄
  (L3 씬 템플릿 설계 요구로 명문화).
- **결과**: 문서 개정만, 코드 무변경.
- **연관**: docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md §5·§9.1·§10.

## 2026-08-14 v0.43.5 — 쇼츠 × VOX 콜라주 전면 개편 계획 수립

- **무엇을**: `docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md` 신설 — v0.44~v0.50 사이클(Phase 0~6)의
  SSOT. 07 스타일 가이드 v2 개정 방향, 디자인 시트 3계층(L1 토큰 / L2 컴포넌트 / L3 씬 템플릿)
  + 스페시먼 체계, 판화 스타일라이저(`workers/engraving_stylizer.py`) 신설, 인물·CI·국기 자산
  라이브러리(`assets/library/`) 스키마, `bundle_to_shorts.py` 컷다운 규칙, voice profile,
  BGM manifest 계획 포함.
- **왜**: 사용자 지시(2026-08-14) — 흐름 유지, 영상 풍·디자인·컨셉 대대적 변경(쇼츠 기준 +
  VOX 콜라주/컷아웃/포토 몽타주/랜섬노트 + 흑백 판화 인물 + voice key 교체 + BGM).
- **어떻게**: 저장소 전수 탐색(라이브 파이프라인 = bundle_to_video → HyperFrames, 1920×1080
  하드코딩 확인) 후 PROFESSIONAL_REBUILD_PLAN 전례 형식으로 작성. 핵심 결정 3: ① 힉스필드류
  생성형 미채택 — G4-10 유지, 판화 초상은 실사진 절차적 스타일라이즈(결정론 SVG) ② 제작 방식
  C안 = 사전 자산 라이브러리 + HyperFrames 결정론 합성 ③ briefing 개조 금지, `hyperframes/
  shorts/` 신규 컴포지션(W/H 토큰 파라미터화).
- **결과**: 계획 문서 1건 + 사용자 결정 필요 8건 목록화(§10). 코드 무변경.
- **연관**: docs/PROFESSIONAL_REBUILD_PLAN.md, docs/VIDEO_BUNDLE_CONTRACT.md, HANDOFF ③(인물
  카드 — 본 계획으로 흡수 예정).

## 2026-06-06 v0.34.2 — 라인/자막 안 보이던 사고 2 픽스 + 30초 확장 (영상미 C0)

- **무엇을**: v0.34.1 영상 사용자 검수 후 스크린샷 진단 — 차트 라인 0:10 시점에서도
  안 그려져있고, 자막 박스만 보이고 텍스트 비어있음. 두 근본 원인 픽스 + 30초로 확장.
- **왜**: 사용자 피드백 "여전히 차트 내 데이터와 자막이 보이지 않아. 한 30초 정도 되는
  영상으로 다시 수정후 만들어." v0.34.1 픽스가 사실상 무효였음을 스크린샷이 증명.
- **어떻게**:
  - **사고 1 진단 (라인 draw-on)**: HTML 의 `<path pathLength="1" stroke-dasharray="1"
    stroke-dashoffset="1">` 패턴이 GSAP 의 `tl.to({strokeDashoffset:0})` 트윈 시작점
    인식에서 실패. GSAP 가 SVG attribute 가 아닌 computed CSS style 을 읽으려 했고,
    `pathLength` SVG attribute 가 Chromium 의 dash 계산에 일관되게 반영되지 않은 것
    으로 추정. **픽스**: `path.getTotalLength()` 로 실 길이 측정 + `gsap.set(p,
    {strokeDasharray: len, strokeDashoffset: len})` 명시 시작 상태. 콜아웃 connector
    3개 동일 패턴. 표준 SVG line-drawing 패턴.
  - **사고 2 진단 (자막 텍스트)**: `.subtitle { background: #4a1e10; padding: 24px; }`
    에 `position: relative` 누락. cue `<span class="cue" id="cue1" style="position:
    absolute">` 들이 첫 positioned ancestor (root 또는 body) 기준으로 absolute 배치 →
    viewport 좌상단 어딘가에 박혀버림. 박스만 보이고 텍스트 안 보였던 이유. **픽스**:
    구조 자체 단순화 — 박스 하나 `<span id="subtitleText">` 만 두고 GSAP `.call()` 로
    시간 시점에 `textContent` swap + 짧은 opacity 페이드 (0.2-0.25s).
  - **데이터 점 마커 스타일 강화**: r=5 → r=6, fill 오렌지 → 흰 fill + stroke #e84a2d
    3px (line 위에서 가독성 향상, "데이터가 없는" 느낌 해소).
  - **콜아웃 명시 inline opacity**: 콜아웃 group 들에 `style="opacity:0"` inline 으로
    GSAP `tl.to({opacity:1, duration:0.001})` 시작점 안전. 이전엔 HTML attribute
    `opacity="0"` 였음.
  - **30초 확장**: composition duration 14 → 30, narration cue 4 → 8 (호르무즈 시나리오
    확장: 봉쇄 발생 → 원유 20% 차단 → 유가 50% 급등 → 1차 휴전 안정 → UAE 표적 공격
    재반등 → 협상 진행 → 지정학 리스크 요약), 콜아웃 2 → 3 (UAE 표적 공격 추가).
  - 라인 draw 시간 2 → 3s, Ken Burns scale 1.03 → 1.04 (30초 동안 좀 더 확대).
  - 렌더 30s × 30fps = 900 프레임, 2 워커, 228KB.
- **결과**: 30초 silent mp4 + SendUserFile 전달. 차트 라인 + 자막 텍스트 가시성
  확인 대기.
- **다음**: 사용자 v0.34.2 영상 검수 결과 → 음성 통합 (사용자 머신 ElevenLabs) /
  씬별 subtitleBgColor 토큰화 / v0.35.0 차트 family 포팅.
- **연관**: CHANGELOG v0.34.2, v0.34.0 (HyperFrames 채택), v0.34.1 (실패한 픽스), GOAL G0.

---

## 2026-06-06 v0.34.1 — HyperFrames 사용자 1차 피드백 4 픽스 (영상미 C0)

- **무엇을**: v0.34.0 의 HyperFrames 프로토 영상 본 사용자 평가 + 4 후속 요청 반영.
  데이터 점 마커 추가, 자막 다중 큐 swap, 자막 폰트 ExtraBold, 자막 배경 dark burnt
  orange. 14초 silent mp4 재렌더 + 사용자 전달.
- **왜**: 사용자 평가 "어 훨씬 나아졌는데, 그 차트에 데이터가 없었던 것 같아. 그리고
  자막을 이제 진짜 나레이션 스러운 자막과 음성을 입히는걸 해보자. 그리고 자막의 폰트는
  어떤걸로 할까? 그리고 자막의 배경은 화면에서 보여주는 차트나 지도, 정보에 맞는 짙은
  색을 자막 박스의 배경색으로 하는거야 어때". 4 항목 모두 즉시 적용 가능 (음성만 환경
  제약).
- **어떻게**:
  - **① 데이터 점 마커**: `<g id="points">` 에 line path 의 각 9 좌표에 `<circle r=5
    fill="#e84a2d" stroke="#fff" stroke-width=2 opacity="0">`. GSAP `tl.to(".pt",
    {opacity:1, stagger:0.18}, 0.8)` 으로 라인 draw-on (2초) 진행에 맞춰 차례로 등장.
    9 × 0.18 = 1.62초 → 라인 끝나는 시점과 거의 동기.
  - **② 음성**: 클라우드 SSL 인터셉트로 edge-tts(`speech.platform.bing.com`) +
    ElevenLabs (`api.elevenlabs.io` 403) 모두 차단. 자체 SSL bypass 시도(monkey-patch
    `aiohttp.TCPConnector`)했으나 edge-tts 모듈이 자체 세션 생성으로 우회 안 됨.
    → composition 에 `<audio class="clip" data-start=0 data-duration=14
    src="assets/audio/brent.mp3" preload="auto">` placeholder 만 사전 배선. 사용자
    머신에서 본인 ElevenLabs key 로 mp3 생성 시 자동 재생. HyperFrames + audio 통합은
    이미 1급 (`<audio data-*>` 표준 패턴).
  - **③ 자막 폰트**: `font-weight: 700` → `font-weight: 800` (Pretendard ExtraBold).
    Pretendard Variable woff2 가 100-900 wght axis 지원하므로 추가 파일 없이 weight
    변경만으로 적용. `letter-spacing: -0.3px` → `-0.4px` 조여서 broadcast 톤. 사용자
    질문 "자막 폰트 어떤걸로?" 답변: Pretendard 단일계 유지 권장 (한국 broadcast 표준
    Rix정고딕/MBC 새로움체 는 commercial license 불가, 무료 대안 Noto Sans KR Black /
    G마켓 산스 Bold 가능하나 본문/타이틀과 폰트 갈리면 통일성 깨짐).
  - **④ 자막 배경 동적**: `rgba(26,26,26,0.82)` (uniform near-black) →
    `#4a1e10` (dark burnt orange, 차트 accent `#e84a2d` 의 brightness 30% 톤).
    `box-shadow` 도 `rgba(74,30,16,0.35)` 톤 매칭. 본 PATCH 는 line chart 씬에 대해
    하드코딩, 향후 v0.35+ 에서 씬별 `subtitleBgColor` 토큰화 (`render_props.json` 또는
    composition data-attr). 매핑 가이드:
      * 오렌지 차트 → `#4a1e10` (dark burnt orange)
      * 지도 빨강 강조 → `#2a0a0a` (deep maroon)
      * 회색 dashboard → `#1a1a1a` (near-black, 기본)
      * 네이비 차트 → `#0a1a2e` (deep navy)
  - **자막 다중 큐**: 4 큐를 `position:absolute` 로 겹쳐 두고 opacity 만 swap. cue
    1=3.2s/cue2=3.5s/cue3=3.0s/cue4=3.5s = total 13.2s + 진입 0.8s = 14s.
  - composition duration 10s → 14s (자막 분량 확보).
- **결과**: 14초 silent mp4 90.9KB 렌더 + SendUserFile 전달. 영상미 추가 향상 검증 대기.
- **다음 (사용자 평가 후)**:
  - 음성 자동 합성 + HyperFrames 통합 (build-audio-demo 의 HyperFrames 적응판)
  - 씬별 subtitleBgColor 토큰화 (data-attr 또는 compose props)
  - v0.35.0: 차트 family 15종 React → HTML+SVG+GSAP 포팅
- **연관**: CHANGELOG v0.34.1, v0.34.0 (HyperFrames 채택), GOAL G0 영상미.

---

## 2026-06-06 v0.34.0 — HyperFrames 마이그레이션 시작 (Remotion 폐기 결정)

- **무엇을**: 모션그래픽 엔진을 Remotion → **HyperFrames** (HeyGen 오픈소스, Apache 2.0)
  로 전환 결정. 첫 프로토타입 1 씬 (브렌트 유가 line chart, 10초) 렌더 + SendUserFile
  전달 + 사용자 1 평가 ("훨씬 나아졌다") 수령.
- **왜**: v0.33.0/v0.33.1 의 Remotion+React+d3 시스템이 사용자 평가 "촌스러워" 를 두 라운드
  픽스 후에도 영상미의 천장에 도달 못 함. 사용자가 HyperFrames (HeyGen) 검토 요청 →
  deep research 5 트랙 결과 GSAP/Lottie 1급 지원, HTML 단순성, deterministic seek 가
  NYT/Vox-grade 편집 영상미와 정합. 사용자 선택: "1로 가자" (완전 전환).
- **어떻게**:
  - **환경 셋업**: `npm install hyperframes@0.6.76`. `apt install ffmpeg` 성공. 단
    `chromium-browser` apt 패키지는 snap 의존이라 puppeteer 가 실패 → 패키지 제거 후
    `PUPPETEER_EXECUTABLE_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome` 로
    playwright 번들 chromium 우회 → 렌더 성공.
  - **scaffold**: `npx hyperframes init demo` 가 `index.html + hyperframes.json +
    meta.json + package.json + CLAUDE.md + AGENTS.md` 생성. 기본 HTML 은 빈 root composition
    + GSAP 스크립트 inline + jsdelivr CDN 의존 (클라우드 차단이지만 렌더 시 puppeteer
    환경에선 통과한 듯, 25KB 빈 mp4 렌더 됨).
  - **폰트**: `cp remotion/public/fonts/PretendardVariable.woff2 hyperframes/demo/assets/
    fonts/`. HTML 의 `@font-face` 단순 선언 → Remotion 의 cancelRender 사고 0.
  - **프로토타입 씬**:
    - 좌상단 브랜드 (`#e84a2d` 사각형 + "OSINT 브리핑" 캡스)
    - 중앙 흰 카드 (`#ffffff` + 22px radius + soft shadow) + takeaway + SVG line chart
    - 데이터: 7 점 (`80→120→118→105→108→114→102`)
    - 이벤트 콜아웃 2개: 호르무즈 봉쇄 (피크), 1차 휴전 (2주 유효) — Subject 점 + Bezier
      Connector + 라벨 텍스트 (caps + 보조 텍스트)
    - 끝점 마커 + 시리즈명 "브렌트" + 값 "102 $"
    - 하단 다크 자막 바 `rgba(26,26,26,0.82)` + 흰 굵은 글씨
    - GSAP timeline (paused, `window.__timelines["brent"]` 등록):
      * 브랜드/출처/takeaway 페이드인 stagger 0-0.6s
      * 그리드 페이드인 0.4s
      * 라인 `strokeDashoffset` 1 → 0 draw-on 2.0s (power1.inOut)
      * 콜아웃 1 (1.2-2.0s): subject scale 0 → 1, connector dashoffset, 텍스트 fade-in stagger
      * 콜아웃 2 (2.4-3.2s): 동일 패턴
      * 끝점 마커 + 라벨 (2.7-3.3s)
      * Ken Burns 전체 `#stage` scale 1.0 → 1.03 (전 10초, ease none)
      * 자막 fade-in + slide-up 0.5s @ 0.6s
  - **렌더**: `PUPPETEER_EXECUTABLE_PATH=... npx hyperframes render` — 300 프레임 (10초 @
    30fps) × 2 워커, 100s 소요, mp4 109.5KB. headless Chrome 프레임 시킹 + ffmpeg 인코딩.
  - **SendUserFile** 로 전달 → 사용자 평가 "어 훨씬 나아졌는데". 방향 확정.
- **결과**: 1 씬 HyperFrames 프로토 성공. Remotion 의 `@remotion/fonts` cancelRender
  / chromium-headless-shell 다운로드 차단 / React 의존성 추상화 → 모두 회피. HTML+GSAP
  단순성이 영상미의 천장 더 높다는 가설 1 라운드 검증.
- **사용자 1차 평가 + 후속 4 요청 (v0.34.1 작업)**:
  1. "차트에 데이터가 없었던 것 같다" — line path 만 그리고 각 7 데이터 점 마커 누락 →
     각 점에 작은 원 추가.
  2. "자막을 진짜 나레이션 스러운 자막 + 음성을 입혀보자" — ElevenLabs TTS 통합 +
     단어 단위 자막 sync.
  3. "자막 폰트 어떤걸로?" — 권장 Pretendard ExtraBold (800) 단일계 유지. 한국 broadcast
     표준(Rix정고딕/MBC 새로움체) 은 commercial license. Noto Sans KR Black 대안 가능
     하나 통일성 위해 Pretendard 권장.
  4. "자막 배경을 차트/지도/정보에 맞는 짙은 색으로" — 씬별 `subtitleBgColor` 토큰 추가.
     오렌지 차트 → `#4a1e10` dark burnt orange. 지도 빨강 → `#2a0a0a` deep maroon.
     기본 → `#1a1a1a` near-black. dominant color derive 알고리즘 또는 명시 지정.
- **다음**:
  - v0.34.1: 위 4 요청 적용 + 재렌더.
  - v0.35.0: Remotion 차트 family 15종 → HyperFrames HTML+SVG+GSAP 포팅.
  - v0.36.0: orchestrator/render_io.py → HyperFrames 매니페스트 출력. build-audio-demo
    → HyperFrames 음성 동기. Remotion archive.
  - v0.37.0+: 호르무즈 풀 파이프라인 + 사용자 최종 검수.
- **연관**: CHANGELOG v0.34.0, v0.33.x (폐기 결정), GOAL G0 영상미 최우선. v0.33.x 의
  Remotion 코드는 v0.36 에서 정리 또는 archive 결정.

---

## 2026-06-06 v0.33.0 — Editorial Restraint Reset + 사용자 1차 픽스 (영상미 C0 갈아엎기)

- **무엇을**: 디자인 시스템 전면 갈아엎기 (Aurora Glass + 8색 + 다크 + 글로우 폐기) +
  사용자 첫 검수 후 4 픽스 (라벨 배지 화면 제거, ChartView title 중복 제거, 끝점 라벨
  잘림 픽스, Forecast 공백 잇기). 클라우드 mp4 2회 직접 렌더 + 사용자 SendUserFile 전달
  완료.
- **왜**: v0.32.2 후 사용자 평가 "전반적으로 차트라던지 폰트, 네온 글로우 같은 이펙트가
  너무 구려. 촌스러워" + "최고의 인포그래픽 엔진을 찾아. 그리고 적용해서 데모를 나한테
  만들어 올려" → 제가 결정+빌드+전달까지. Deep research 5 트랙 결과 + 사용자 9장
  dashboard 레퍼런스 + 3장 날리지식 화면 + 5 모션 패턴 텍스트 통합해 방향 확정.
- **어떻게**:
  - **Research synthesis**: NYT/Vox/FT 의 motion infographic 도구 = AE+Lottie 표준이나
    D3 가 NYT 엔진(천장이 가장 높음, 유지). Remotion + D3 = 결정론적 패턴(useCurrentFrame
    + interpolate + d3-shape 만, GSAP/Lottie 는 wall-clock 충돌). 편집 안티패턴: NN/g
    glassmorphism 가이드 위반(Aurora glass), Wilke 3D/gradient 금지, neon cyan/violet
    은 Reuters/FT/NYT 시스템 0건, direct labeling > legend (Amanda Cox annotation
    layer). 한국 broadcast 타이포: Fontrix Rix헤드/MBC 새로움체/KBS Yoon이 표준이나
    본 사용자 레퍼런스(dashboard infographic)는 Pretendard 적합. 한국 채널 실 사용:
    지식은 날리지(`UCQKZQFd7AfgHOYoui6OE9Ew`) 채널 ID 정정 + 슈카월드 Paint 3D 라이브.
  - **레퍼런스 9+3 + 5 패턴 통합**: dashboard 9장 = light bg + 오렌지 accent + Pretendard
    ExtraBold + 거대 숫자 hero + 둥근 카드 + 직접 라벨. 날리지식 3장 = 다크 지도 +
    엔티티 토큰 + 부드러운 연결선 + Ken Burns + 다크 broadcast 자막. → 둘 다 수용:
    dashboard 톤이 차트/데이터 씬, 날리지식 모션 패턴이 전 씬 공통.
  - **design.ts 재작성**: surface.page #f5f1ea, surface.card #ffffff, accent.primary
    #e84a2d, 시리즈 5색, weight 400-900, size 14→180, Material easing 단일계, stagger
    50-150ms. 8색 Okabe-Ito/aurora/cyan spotlight/샴페인 골드 quote 폐기.
  - **차트 일괄 rename** (sed): surface.s1/base → surface.cardAlt/page, accent.quote →
    accent.primary, accent.positive/negative → label.verified/unverified.
  - **Briefing.tsx**: AuroraGlassCard 의존 제거. 사각형+캡스 브랜드, 흰 카드 라벨 배지,
    SurfaceCard 중앙, Ken Burns 1.0→1.03 전 씬, 다크 translucent + 흰 굵은 자막.
  - **fonts.ts no-op**: @remotion/fonts 의 loadFont 가 fetch 실패 시 cancelRender →
    렌더 자체 실패. 클라우드는 remotion.media + jsdelivr/unpkg 모두 차단 → npm
    `pretendard` 패키지 설치 후 `node_modules/pretendard/dist/web/variable/woff2/`
    추출해 `public/fonts/` 배치만. fonts.ts 는 Phase 5 에서 안전 패턴(staticFile +
    FontFace + delayRender/continueRender)으로 재구현 예정.
  - **Chromium**: Remotion 기본 다운로드 URL 클라우드 allowlist 차단 → playwright 의
    `/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell` 감지해
    `--browser-executable=` 직접 지정.
  - **렌더 1차** (v0.33.0): 52초 1080p, 10.9MB, SendUserFile 전달.
  - **사용자 1차 평가** = 5 피드백: ① line 차트 왼쪽 라벨 가림 (ChartFrame title +
    Briefing takeaway 중복), ② `<확인>` `<추정>` 배지 제거, ③ stacked area 우측 끝점
    라벨 짤림, ④ forecast 공백 (agents_reviewer 동일 지적), ⑤ Codex 미적 검수 체계
    신설.
  - **v0.33.1 픽스 4건**: ChartView 의 `title={chart.title}` → `title={null}` (Briefing
    takeaway 가 같은 정보). Briefing 의 LabelBadge 렌더 제거 (데이터 보존). design.ts
    chart.padRight 100→180. ForecastChart 의 actual 마지막 점을 forecast mid + band
    시작에 prepend.
  - **렌더 2차** (v0.33.1): 52초 1080p, 9.3MB, SendUserFile 전달.
  - **5번 (Codex 미적 검수 체계)** 은 별도 v0.33.2 메타 PATCH 로 분리 — 본 PATCH 는
    코드 픽스만.
- **결과**: 사용자가 즉시 검수 가능. v0.29.0 의 Aurora glass/glow 100% 제거. 4 픽스
  적용된 두 번째 컷 까지 사용자 전달.
- **다음**: ① 사용자 v0.33.1 영상 평가, ② v0.33.2 = Codex 미적 검수 체계 (영상 키프레임
  추출 → 영상 LLM 검사 → 다음 PATCH 입력), ③ Phase 4 인물 카드 + 엔티티 연결선 draw,
  ④ Phase 3 다크 지도 GeoScene (날리지식 스타일).
- **연관**: C0/G0, CHANGELOG v0.33.0, docs/PROFESSIONAL_REBUILD_PLAN.md (Phase 메타
  결정). v0.29.0(폐기), v0.30~32(토대 유지, 표면 처리만 갈아엎음).

---

## 2026-06-05 v0.32.2 — build-audio-demo CLI (사용자 편의 PATCH)

- **무엇을**: `orchestrator/audio_demo.py:build_audio_demo(props_path, backend, voice,
  audio_subdir)` + `build-audio-demo` 서브커맨드. props 한 파일만 받아 각 scene
  narration 을 TTS 합성 → `demo_audio/` 에 wav/mp3 저장 → `audioPath` +
  `durationSec` + `startSec` 실 음성 길이로 갱신 → `<원본>_with_audio.json` 출력.
- **왜**: 사용자가 호르무즈 풀 렌더 시도 → `full_script.json` 없음 → `projects/
  seam-hormuz/` 가 git 에 없어 사용자 머신에 산출물 0 → bundle 부터 다시 빌드해야 하는
  큰 작업. 그 와중 "목소리도 입혀야지" 즉, **데모만이라도 음성이 입혀진 영상을 보고
  싶다**. 기존 `build-audio` 는 project state machine + full_script 가 전제라 데모엔
  과한 의존. → state 머신 거치지 않는 1회용 헬퍼 신설.
- **어떻게**:
  - 입력: `remotion/demo_props.json` (또는 같은 스키마의 임의 props). `scenes[].
    narration` 이 본 작업의 입력.
  - 백엔드 재사용: `workers/tts_backends.get_backend(backend)` 그대로. v0.32.1 의
    `.env` 자동 로딩 덕에 `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` 자동 적용.
  - **출력 위치**: props 가 있는 폴더 아래 `demo_audio/<sceneId>.<ext>`. Remotion 의
    `--public-dir=.` 로 props 디렉토리를 public 으로 두면 `staticFile()` 가 그대로
    잡음 (`render-debug` 의 패턴과 정합 — main.py:992 의 `--public-dir=project_dir`).
  - **시간 재누적**: 진입 모션 / wipe / stagger 들이 결국 `durationSec` 에 fit 하므로,
    실 음성 길이로 `durationSec` 갱신하고 다음 scene 의 `startSec` 도 재계산. 결과 영상
    길이가 원본보다 늘어나거나 줄 수 있음(자연스러움). Briefing.tsx 의 `calculateMetadata`
    가 총 길이를 다시 합산하므로 mp4 길이도 자동 맞춰짐.
  - **빈 narration 처리**: skip + audioPath 안 박음. 무음 scene 으로 남음. `durationSec`
    유지.
  - **오류 흡수**: 파일 없음 / 빈 scenes / JSON 깨짐 / TTS 실패 모두 별도 exit code.
  - 단위 테스트 4 케이스 (stub backend e2e + startSec 재누적 + 누락 / 빈 입력 에러).
- **결과**: 332 → 336 통과 (+4). build-audio 기존 동작 변화 없음(독립 경로).
- **다음 (사용자 측)**:
  ```
  python -m orchestrator.main build-audio-demo remotion\demo_props.json --backend elevenlabs
  cd remotion
  npx remotion render src/index.ts Briefing demo_out.mp4 ^
    --props=demo_props_with_audio.json --public-dir=.
  ```
- **연관**: v0.32.0(demo_props.json 도입), v0.32.1(.env 자동 로딩), HANDOFF 보류항목 4
  (Windows 실제 음성 풀 렌더 검증 — 호르무즈 풀 파이프라인은 별도이나 본 PATCH 가
  "데모만이라도 음성 검수" 의 작은 우회로). CHANGELOG v0.32.2.

---

## 2026-06-05 v0.32.1 — `.env` 자동 로딩 (사용자 편의 PATCH)

- **무엇을**: `orchestrator/main._load_env_file()` 진입점 도입. 저장소 root `.env` 가
  있으면 `python-dotenv` 로 로드. `override=False` 라 운영 환경의 export 우선.
  `requirements.txt` 에 `python-dotenv>=1.0` 추가, `.env.example` 갱신, 4 케이스 단위
  테스트.
- **왜**: 사용자가 호르무즈 풀 렌더 시도 중 "내 api키와 voice id 를 env 에 넣어서 쓰면
  안돼? 내가 매번 입력 해야 돼? 너무 불편한데?" 명시적 요청. setx(영구 환경변수) 와
  `.env` 두 옵션 제안 → 사용자 `.env` 선택. 비밀값을 한 곳에 모으고 추가 키(향후 whisper /
  다른 TTS) 가 늘어도 동일 패턴.
- **어떻게**:
  - 진입점 한 곳에서 호출(`main()` 첫 줄). 모든 서브커맨드 자동 적용.
  - **override=False**: 사용자 머신 OS 환경에 키가 export 되어 있으면 그쪽 우선 — 본
    저장소를 prod 머신으로 옮길 때도 안전. .env 는 dev 보조 채널.
  - `python-dotenv` 미설치 / `.env` 미존재 = 둘 다 silent no-op. CI 영향 0.
  - `requirements.txt` 주석은 ASCII-only (DEVLOG v0.15.2 의 한글 Windows cp949 사고
    재발 방지) — 한글 주석을 영문으로 작성.
  - `.env.example` 정리: ANTHROPIC/OPENAI 같은 미사용 placeholder 제거(우리는 구독 CLI
    호출이라 LLM API 키 불필요 — ADDENDUM_04), 실제 사용 중인 ELEVENLABS_* + OSINT_* 만
    명시적으로 박음. 사용자가 본 파일만 보면 환경변수 전모 파악.
  - 테스트: ① 키 로드, ② 기존 export override 안 함, ③ .env 없을 때 silent, ④ dotenv
    미설치 시 silent — `mock.patch.dict("sys.modules", {"dotenv": None})` 로 import
    실패 흉내.
- **결과**: 328 → 332 통과(+4 신규). 코드 변경 영향 0(미설치/.env미존재 시 동일 동작).
- **다음**: 사용자가 본인 머신 .env 채우고 `python -m orchestrator.main build-audio
  seam-hormuz --backend elevenlabs` 실행. 음성 산출되면 Remotion 풀 렌더로 새 차트(Phase
  1+2) + 음성 + 자막 + 지도가 함께 도는 호르무즈 영상 확인. 그 피드백 → Phase 3 진입.
- **연관**: C9(secret 미커밋), .gitignore 32-33(.env), ADDENDUM_04(LLM 구독 CLI 호출,
  LLM API 키 없음), CHANGELOG v0.32.1.

---

## 2026-06-05 v0.32.0 — Phase 2: Bar/Point family 정통 재구현 (영상미 C0)

- **무엇을**: Bar/Point family 9 종(bar / lollipop / range_bar / stacked_bar / waterfall /
  scatter / bubble / slope / candle) 을 디자인 시스템 토대로 재구현.
  - `charts/cat/BarChart.tsx`: `scaleBand` + mode 분기(bar/lollipop/range), 카테고리
    stagger 진입, 막대 grow + 직접 값 라벨, 음수 막대 다크오렌지.
  - `charts/cat/StackedBarChart.tsx`: 카테고리 sweep + 시리즈 60ms 내부 stagger, 마지막
    시리즈 상단 둥근 모서리, 우상단 범례.
  - `charts/cat/Waterfall.tsx`: 누적 막대 + connector 점선(이전 끝 → 본 시작), +/- 부호
    자동, total 막대 분리.
  - `charts/cat/PointChart.tsx`: scatter / bubble. bubble 반지름 = sqrt(size/smax)*50
    (면적 비례), 라벨 1D 충돌 회피 + leader line.
  - `charts/cat/SlopeChart.tsx`: 좌·우 양쪽 라벨 충돌 회피, 컬러 매칭, 도달 시 우 마커.
  - `charts/cat/CandleChart.tsx`: 양봉 accent.positive / 음봉 accent.negative, wick + box
    grow, x tick 자동 thinning.
- **왜**: XY 다음으로 OSINT 빈도 높은 family — bar/scatter/lollipop 은 카테고리 비교의
  주력, waterfall 은 경제·트레이드 흐름 분석, candle 은 시장·환율, slope 은 비교 시점
  변화. Phase 1 의 토대(util.ts/ChartFrame/Axis 등)를 그대로 재사용해 빠르게 영상미 끌어
  올림 — 21 종 중 15/21(71%) 가 design.ts 토큰 100% 적용.
- **어떻게**:
  - **scaleBand**: 카테고리 막대는 d3 `scaleBand({padding: 0.34})` — bandwidth() 가
    자동 산출되므로 막대 폭 결정론.
  - **음수 처리**: bar 의 음수 막대는 baseY(=0) 아래로 grow. 라벨도 막대 아래 배치.
  - **양봉/음봉 컬러**: `accent.positive`(녹) / `accent.negative`(적). open ≥ close 는
    양봉 — 다크 환경에서 양봉=녹 컨벤션(미국식). 한국 증시 컨벤션(적이 양) 은 향후 옵션.
  - **bubble 면적 비례**: 시각 인지는 면적 ∝ 데이터값 — radius = sqrt(value/max) * maxR.
    선형 비례하면 큰 값 시각적 과대 표현.
  - **Connector 점선 (waterfall)**: 이전 막대 끝 점 → 본 막대 시작 점. total 막대 앞엔
    연결 없음(누적 리셋).
  - **slope 좌·우 라벨 양쪽 충돌 회피**: `layoutEndpointLabels` 두 번(좌, 우). 같은
    `data.label` 이 좌·우 양쪽에 컬러 동기화.
  - **candle x tick thinning**: 라벨 너무 많으면 `Math.floor(n/6)` 간격으로 sparse.
  - **legacy 청소**: BarChart / StackedBar / Waterfall / PointChart / Candle / Slope /
    ChoroplethBars 제거(~200 LOC). Donut/Gantt/Heatmap/Network/Sankey 만 임시 유지.
  - **choropleth**: 임시로 BarChartV2 에 country_code/value 매핑. Phase 3 에서 world-atlas
    + ISO 매핑 + sequential color 스케일로 본격 재구현.
- **결과**: tsc clean(MapView 사전 경고만), Python 328/328. ChartView dispatcher 단순화
  (legacy 코드 ~50% 감축).
- **다음**: Phase 3 — Specialty (v0.33.0). Donut(외부 라벨 + %), Gantt(time-wipe stagger
  + 마일스톤 별), Heatmap(셀 행→열 stagger), Network(d3-force 헤드리스 사전 시뮬레이션 +
  degree 큰 노드부터 등장), Sankey(d3-sankey 실 사용), Choropleth(world-atlas + ISO +
  sequential color).
- **연관**: C0/G0, CHANGELOG v0.32.0, docs/PROFESSIONAL_REBUILD_PLAN.md §3 Phase 2,
  MVP Professional Bar 1/7/8/9/11 진행. v0.31.0(Phase 1) 의 util.ts 재사용.

---

## 2026-06-05 v0.31.0 — Phase 1: XY family 정통 재구현 (영상미 C0)

- **무엇을**: XY 6 종(line / area / stacked_area / small_multiples / dual_line / forecast)
  을 디자인 시스템(v0.30.0) 토대 + d3-scale + d3-shape + 자체 1D 라벨 충돌 회피 + Subject+
  Note+Connector + ReferenceRegion 으로 재구현.
  - `charts/util.ts`: time-aware x 스케일(ISO 면 scaleTime, 아니면 scalePoint), nice ticks
    y 스케일, Material easing(t→y, Newton 2-step), draw progress hook + 시리즈 stagger
    hook, 1D 라벨 충돌 회피(양방향 패스 + 경계 클램프), 시리즈 그룹화.
  - `charts/xy/XYChart.tsx`: line/area/stacked_area/small_multiples 통합. d3-shape `line()`
    + `area()` + `curveMonotoneX`. clipPath 로 x-wipe 진입(Material decelerate). 끝점 마커
    + leader line + 시리즈명 + 값(직접 라벨, 75% progress 후 등장). `event` 필드 있으면
    `Callout` 자동 노출. `referenceRegions` 옵션으로 위기 구간 음영.
  - `charts/xy/DualLineChart.tsx`: 좌/우 독립 y 스케일, 우 시리즈 점선, 색 매칭 헤더.
  - `charts/xy/ForecastChart.tsx`: 실측(실선) + 전망(점선 mid + band area) + 전망 구간
    ReferenceRegion + "실측"/"전망" 끝점 라벨.
- **왜**: Phase 0 토대만 박으면 디자인 토큰이 실 차트에 흐르지 않으므로, XY 6 종을 첫 family
  로 본체 진입. XY 는 OSINT 시계열의 빈도·중요도 1 등(line·area 가 전체 차트의 ~60%).
  d3-shape 의 `area()` / `line()` 은 우리가 직접 path 문자열을 만들던 v0.27.0 보다 곡률
  보간(`curveMonotoneX`) 등 정밀도가 훨씬 높고, `scaleTime` 은 ISO 입력에 대해 시간 위계
  를 자동(연/월/일 자동 포맷)으로 줘서 사용자가 데이터를 그대로 던져도 영상미 보존.
- **어떻게**:
  - **결정론**: labella(UMD, 비결정 정렬 의존) 회피하고 자체 1D 충돌 회피 구현 — 양방향
    패스(아래로 + 위로) + 경계 클램프. 입력 동일하면 출력 동일.
  - **Material easing 의 결정론적 t→y**: Remotion `interpolate` 는 함수형 easing 을 받으므로
    cubic Bezier `(0,0)→(cp0,cp1)→(cp2,cp3)→(1,1)` 의 t→y 를 Newton 2-step 으로 (정확도
    < 0.005). CSS keyframe / `cubic-bezier()` 안 씀 — 프레임 정확.
  - **Wipe 진입**: line/area 의 stroke-dasharray 트릭 대신 `clipPath` rect 의 width 를
    progress 로. area fill 도 동일 클립으로 잘려서 영상의 "데이터 그려지는 느낌" 일관성.
  - **끝점 라벨 시점**: progress 0–75% 는 wipe, 75–95% 는 라벨 페이드인. 라벨이 wipe 보다
    먼저 나오면 시각적 혼란.
  - **이벤트 콜아웃**: `event` 필드(legacy 호환) 있으면 `Callout`(Subject + Note + Bezier
    Connector) 자동 노출. note 위치는 데이터 포인트가 영역 우측 30% 안에 있으면 왼쪽 위,
    아니면 오른쪽 위.
  - **legacy 코드 청소**: `LineLike` / `ForecastChart` / `DualLine` 제거(~110 LOC).
    Bar/Point/Specialty 등 나머지 14 종은 본 PATCH 에선 손 안 댐(Phase 2/3).
- **결과**: tsc `--noEmit` 통과(MapView 의 JSON resolve 경고는 사전 존재). Python 328/328
  통과. ChartView 디스패치만 변경, 외부 인터페이스(ChartData) 동일.
- **다음**: Phase 2 — Bar/Point family (v0.32.0). bar / lollipop / range_bar /
  stacked_bar / waterfall / scatter / bubble / slope / candle 를 동일 토대로 재작성.
  Waterfall connector 선, bubble quadrant label, lollipop stem grow + head pop, label
  collision 자체 구현 재사용.
- **연관**: C0/G0, CHANGELOG v0.31.0, docs/PROFESSIONAL_REBUILD_PLAN.md §3 Phase 1,
  MVP Professional Bar 8/9/10/11/12 진행. v0.30.0 (토대) 의 첫 본체 적용.

---

## 2026-06-05 v0.30.0 — Phase 0: 프로페셔널 재빌드 디자인 시스템 토대 (영상미 C0)

- **무엇을**: 차팅·자막·타이포의 전면 재빌드 사이클(v0.30.0 → v0.36.0) 출발.
  `docs/PROFESSIONAL_REBUILD_PLAN.md`(SSOT) + `remotion/src/design.ts`(토큰) +
  공용 컴포넌트 4 종(`ChartFrame` / `Axis` / `Callout` / `ReferenceRegion`) +
  npm 의존성(`d3-scale d3-shape d3-time-format d3-array d3-scale-chromatic labella`).
- **왜**: 사용자 평가 — "전반적으로 차팅의 기술이나 시각화 기술이 너무 구려.
  총체적으로 다시 재빌드, 리팩토링을 전면적으로 해야 할거 같아. 프로페셔널한 수준으로
  그 레벨을 높일 수 있는 계획을 세워." 비주얼 기준은 날리지식 (YouTube `FaOqn3-YdkI`,
  `ucl9RED4Ye4` — YTN 세계는 날리지가 아님). 사용자 ack: "응 진행해."
- **어떻게**: 차트 본체 코드는 **한 줄도 안 건드린다**(Phase 1 부터 진입).
  Phase A 외부 리서치 5 트랙 통합 → 자기 평가(평균 갭 -5.9) → MVP Professional Bar
  20 합격 기준 → Phase 0–5+E 실행 계획. 디자인 토큰 SSOT 박음:
  - **Color**: Material Dark 베이스 `#121214`(`#000` 의 OLED 잔상·과대비 회피) +
    Okabe-Ito 색맹 안전 시리즈 7 색 + 의미 라벨 4 색(확인/추론/주장/미검증) +
    Aurora 4 색(보더 그라디언트).
  - **Typography**: Pretendard Variable(45–920 wght axis) 폰트 스택 + 1.618 황금비
    size scale(14→18→28→46→76→124) + **한글 `word-break: keep-all` + `overflow-wrap:
    anywhere`** 모든 텍스트에. Netflix Korean 자막 표준(16자/2줄/17CPS/5–7sec).
  - **Motion**: Material easing(decelerate `[0,0,0.2,1]` / standard / accelerate),
    duration 150/300/400/600/900ms, `stagger(n)` 헬퍼(`clamp(min(80, 600/N), 20, 120)`).
  - **Spacing**: 8-grid + safe area + chart 영역 + radius + stroke 토큰.
  - 헬퍼: `msToFrames(ms, fps)`, `seriesColor(i)`, `labelColor(key)`.
  공용 컴포넌트:
  - `ChartFrame`: kicker / title / subtitle / source 슬롯. 빈 슬롯 공간 차지 안 함.
  - `Axis`: SVG group x/y 축 + grid + tick + 라벨. d3-axis 의존 회피(결정론).
  - `Callout`: D3-annotation Subject + Note + Connector. 진입 트랙(subject 300ms →
    connector 300ms → note 200ms), Bezier curved connector, foreignObject 로 한글
    줄바꿈 안전.
  - `ReferenceRegion`: 위기 구간 / 이벤트 회색 알파 fill + 점선 경계 + 라벨.
- **결과**: 새 컴포넌트 tsc `--noEmit` 통과(기존 MapView 의 JSON resolve 경고는
  사전 존재). Python 회귀 328/328 통과. 차트 본체 동작 변경 없음(의도).
- **다음**: Phase 1 — XY family 정통 재구현(v0.31.0). line/area/dual_line/forecast/
  stacked_area 를 d3-scale + d3-shape + ChartFrame + Axis + Callout + Direct
  labeling + labella 충돌 회피로 다시.
- **연관**: C0/G0, CHANGELOG v0.30.0, docs/PROFESSIONAL_REBUILD_PLAN.md (본 사이클
  SSOT). HANDOFF 보류항목 3 (차트 영상미) 의 본격 진입.

---

## 2026-05-25 v0.29.0 — Visual Skin 1차: Aurora Glass Card (영상미 표면 처리)

- **무엇을**: AuroraGlassCard 공용 컴포넌트 + 브랜드/배지/자막 바에 적용.
- **왜**: ChatGPT 피드백 — 영상미는 차트 선보다 패널·카드·콜아웃·자막·배지의 표면 처리에서
  크게 나온다. C0(영상미)의 구체적 HOW. 핵심은 절제(본체 차분, 강조만 럭셔리).
- **어떻게**: 다크 글래스 fill + 오로라 그라데이션 보더(conic) + frame 구동 회전(엣지
  하이라이트, 프레임 정확) + soft bloom. CSS 키프레임 대신 frame 으로 각도 구동(결정론).
  차트/지도 본체엔 적용 안 함(축·격자 glow 금지). 화면당 글로우 카드 3개 수준으로 제한.
- **결과**: 호르무즈 line 차트 scene 프레임으로 확인 — 브랜드/배지/자막이 글래스 카드, 차트는
  깔끔. "다크 럭셔리 OSINT 브리핑" 미감. python 변경 없음(328 통과 유지).
- **다음(스테이징)**: 차트 내 이벤트 콜아웃 카드, title glow, surface 프리셋/토큰, scene
  surfaceEffect, 프롬프트 규칙, 스타일 가이드 문서. 거친 부분 반복 다듬기.
- **연관**: C0/G0, CHANGELOG v0.29.0.

## 2026-05-25 v0.28.0 — forced-alignment 스캐폴드 (자막 음성 정밀 싱크)

- **무엇을**: subtitle_align 모듈(교체형 백엔드 + 비례 폴백) + render_io 배선 + 테스트.
- **왜**: 사용자 요청. 자막 타이밍을 글자수 비례 추정에서 음성 실측으로 정밀화(영상미 C0).
- **어떻게**: OSINT_ALIGN_BACKEND=whisper 면 단어 타임스탬프로 큐 [start,dur] 교체. 미설정/
  무음/실패는 None → 비례 폴백(파이프라인 안 깨짐). 정밀 정렬은 모델+실제음성 필요라 사용자
  머신 전용 — 클라우드(stub 무음)는 기본 no-op.
- **결과**: 328 통과(신규 5). 클라우드 동작 변화 없음(폴백), 사용자 머신서 whisper 붙이면 정밀.
- **연관**: C0, CHANGELOG v0.28.0. (HANDOFF 보류항목 1 = forced-alignment 진행 시작.)

## 2026-05-25 v0.27.0 — 전 차트 family 영상용 렌더러 + 라벨 다듬기

- **무엇을**: ChartView 를 21종 전 타입 family 렌더러로 확장 + render_io SUPPORTED 전 타입 +
  버블 inset/gantt 라벨 anchor 등 클립 다듬기.
- **왜**: 사용자 "모든 차트 family 와 다듬기를 한번에 다 해"(영상미 C0). line 만으론 부족.
- **어떻게**: 공용 헬퍼(scale/draw-on/팔레트/edgeAnchor·clampX)로 family 별 렌더러. XY 묶음,
  bar 묶음, point(scatter/bubble), candle/donut/gantt/slope/heatmap/network/sankey/choropleth.
  미지원(미래 신규) 타입은 텍스트 폴백.
- **결과**: 323 통과. 실물 호르무즈로 network(원형 관계도)/gantt(11개월 타임라인)/bubble(시나리오)/
  line(브렌트) 프레임 렌더 확인 — 전부 안 깨지고 인식 가능. 거친 부분은 의도적 잔존(반복 다듬기).
- **다음**: 클립/겹침 미세조정 반복. network/sankey/choropleth 고도화.
- **연관**: C0/G0, CHANGELOG v0.27.0, docs/05 §3.4e.

## 2026-05-25 v0.26.0 — 영상용 차트 family 렌더러 (line, 영상미 C0 첫 구현)

- **무엇을**: RenderChart 모델 + render_io chart attach + Remotion ChartView(line family) +
  Briefing 통합 + 테스트.
- **왜**: 영상미 최우선(C0) 결정에 따라 차트를 정적 SVG 가 아니라 데이터로 우리가 cinematic
  재렌더. line 이 실물 분포상 압도적(호르무즈 9개 중 5개)이라 line family 부터.
- **어떻게**: claim_refs 에 지원 차트 id 가 있으면 그 scene 에 chartData attach(지도와 동형).
  ChartView line: 데이터 스케일 → 좌→우 draw-on(stroke-dashoffset) + event 마커/라벨 + 축.
  미지원 타입은 attach 안 함(텍스트 폴백). 중앙 비주얼 우선순위 map>chart>text.
- **결과**: 323 통과(신규 2). 실물 호르무즈 브렌트 유가 라인차트 프레임 렌더 확인 — $80→$120
  봉쇄 피크→$105→$114 event 콜아웃, <추론> 배지, 발화형 자막.
- **알려진 다듬기**: 끝점 event 라벨 SVG 경계 클립 / 라벨 겹침 → 후속.
- **다음**: bar/bubble/waterfall/gantt family → 복잡 타입(network 등).
- **연관**: C0/G0(영상미), CHANGELOG v0.26.0, docs/05 §3.4e.

## 2026-05-25 v0.25.0 — 최우선 가치 "영상미(Cinematic Quality First)" 최상위 규칙으로 확정

- **무엇을**: CLAUDE.md C0 + GOAL.md G0 신설("영상미 최우선"). 차트 전략 방침 전환(전-타입
  SVG passthrough 폐기 → 우리가 데이터로 cinematic 재렌더). HANDOFF/docs 정합.
- **왜**: 사용자가 영상 구성·구도를 충분히 이해한 뒤 "영상미를 제1 미덕으로 놓자"고 결정.
  이전의 "안 쫓기 위해 전-타입 SVG" 방침은 전반 구도를 모른 채 내린 거라 폐기. 마침
  agents_reviewer 가 "계약은 A안(consumer 가 데이터로 재렌더)이지 전-타입 SVG 아니다"라고
  잡아준 것과 **수렴** — 우리가 영상미 위해 데이터로 직접 그리는 게 곧 A안.
- **어떻게**: 영상미 = 정적 이식이 아니라 데이터·취지·맥락 이해 후 영상용 생성(애니·음성싱크·
  맥락강조). 선택지 갈리면 정적·편의보다 영상미. 단 사실정확성·G4·C9 위에서(정확성 깬 화려함
  금지). 차트는 family 렌더러로 우리가 cinematic 렌더, 외부 SVG 는 복잡 타입 폴백.
- **결과**: 321 통과(원칙 문서 변경, 코드 무변경). MINOR(G1/G2/G4 미변경이라 MAJOR 아님 —
  G0 는 additive). 다음: family 차트 렌더러 구현이 영상미 후속 작업.
- **연관**: CLAUDE C0, GOAL G0, HANDOFF, docs/05 §3.4e, CHANGELOG v0.25.0.

---

## 2026-05-25 v0.24.0 — 관대한 수신자(tolerant reader): 진화하는 보고서 수용 + v5.5.2 timeline

- **무엇을**: bundle 수신 모델 `extra="forbid"` → `extra="ignore"`(공용 `_BundleModel` 베이스).
  미지 top-level 필드 로깅. `timeline` 모델 추가. 테스트 갱신.
- **왜**: 사용자가 v5.5.2 실물 번들을 줬는데 우리 모델이 거부. 원인 — v5.5.2 가 새 top-level
  `timeline` 필드를 추가했고 `extra="forbid"` 가 번들 전체를 reject. 사용자가 "보고서 양식은
  계속 진화하니 flexibility 가 필요하다" 고 정확히 지적. 게다가 forbid 는 계약 §1("additive=
  schema_version 무증분")과 모순 — 추가 필드에 consumer 가 깨지면 안 됨.
- **어떻게**: tolerant reader 패턴 — 받을 땐 관대(모르는 필드 무시), 쓸 땐 엄격(선언 필드는
  타입·enum·필수·참조무결성 유지). 미지 필드는 로더가 warning 로 surface(인지). 차트
  `data: Any`(기존 유연)에 이어 구조 전체가 진화에 견딤. timeline 은 흡수(보관, 영상 소비 추후).
- **결과**: 321 통과. v5.5.2 실물 번들 검증 통과(timeline 수용) → 어댑터가 12 claims
  (confirmed 4/inferred 6/disputed 2) 합성. extra-rejected 테스트는 tolerant 테스트로 교체.
- **연관**: 계약 v1 §1(consumer=tolerant reader 로 갱신 권고), CHANGELOG v0.24.0, docs/05 §3.4g.

---

## 2026-05-25 v0.23.1 — 보류 작업 추적 (HANDOFF 상단 박음)

- **무엇을**: HANDOFF.md 상단에 "⏳ 다음 할 일(사용자 보류)" 블록 추가.
- **왜**: 사용자가 "3(Windows 실음성 검증) 먼저, 1(forced-alignment)·2(자동 캐치)는 나중"으로
  순서를 미루며 "까먹어도 알려달라"고 함. 세션 메모리는 컨테이너 재생성 시 초기화되므로,
  말 약속이 아니라 저장소 문서(다음 세션이 가장 먼저 읽는 HANDOFF)에 박아 durable 화.
- **결과**: forced-alignment / ③ 자동 캐치 / 차트 SVG 대기 / Windows 검증을 추적. 처리 시
  DEVLOG 반영 후 블록에서 제거.
- **연관**: CHANGELOG v0.23.1.

---

## 2026-05-25 v0.23.0 — ② 지도 비주얼 (Phase B): bundle map 을 d3-geo 로 재렌더

- **무엇을**: RenderMap 모델 + bundle 사본 영속화 + render_io 의 map attach + Remotion
  MapView(d3-geo) + Briefing 통합 + 테스트.
- **왜**: 영상이 텍스트 슬라이드뿐이라 지도/차트가 없었음(사용자 목표 = 직관적 비주얼).
  geo 번들엔 실제 지도(테헤란/이스파한/호르무즈 + 공격축)가 있어 먼저 지도부터.
- **어떻게**: 핵심 발견 — 차트/지도를 v0.20.0 에서 claim 으로 합성한 덕에 ScriptWorker 가
  claim_refs 로 참조(seg_03→map-1) → 비주얼↔scene 배치가 보존됨. import-bundle 이 받은
  bundle 을 04_research/report_bundle.json 으로 영속화 → render_io 가 map id 를 참조하는
  scene 에 RenderMap attach(from_id→fromId 변환). MapView 는 geoMercator.fitExtent(마커 전체
  표시) + world-atlas(npm 번들, 런타임 fetch 없음 — remotion.media 차단 우회) 베이스맵 +
  마커(라벨·highlight) + arc(곡선·강조색). mapData 있으면 caption 은 제목으로 축소.
- **결과**: 319 통과(신규 2). **실물 geo seg_03 프레임 렌더 확인** — 중동 지형 + 마커 5
  (이스파한/호르무즈 강조) + 텔아비브→이스파한 공격축 arc(강조색) + 제목 + <추론> 배지 +
  하단 자막. 레퍼런스(날리지식) 지도 스타일과 일치.
- **다음**: 차트는 agents_reviewer prerendered_svg(v5.5.0 null) 도착 후 SVG passthrough.
  forced-alignment 백엔드 → ③ 자동 캐치.
- **연관**: CHANGELOG v0.23.0, docs/05 §3.4e.

---

## 2026-05-25 v0.22.1 — ScriptWorker LLM 타임아웃 상향 (600→1200초)

- **무엇을**: ScriptWorker.invoke_timeout_sec ClassVar=1200 override.
- **왜**: fin 실물 번들 build-script 가 `claude CLI timeout after 600s` 로 실패. 5분 대본
  1-shot 생성은 claude think 시간이 길어 600초를 넘기는 경우가 있음(실측: geo 526초 성공,
  fin 600초 초과). 로직 오류 아님 — 순수 latency.
- **어떻게**: 긴 생성 전용으로 ScriptWorker 만 1200초로(다른 worker 기본 600초 유지). 전역
  상향 대신 surgical override.
- **결과**: fin build-script 재실행(1200초)으로 ① 출처 프레임 확인 예정.
- **연관**: CHANGELOG v0.22.1.

---

## 2026-05-25 v0.22.0 — ① 화면 상단 출처 텍스트 배선 (bundle sources → source_registry → scene)

- **무엇을**: import-bundle 이 bundle 출처를 source_registry 로 영속화 + render_io 가
  scene→claim→evidence→출처로 해소해 RenderSceneProps.source 채움 + 테스트.
- **왜**: 영상 문법의 상단 출처 슬롯이 비어 있었음(레퍼런스엔 출처 표기가 핵심). bundle 에
  출처 데이터가 있으니 연결.
- **어떻게**: `bundle_to_source_registry` 가 top-level sources + 차트/지도 provenance.sources
  를 SourceEntry 로 수집(dedup, top-level 우선). render_io 가 dossier claim 의 evidence
  source_id 를 registry 표기명(publisher/provider/도메인)으로 해소, scene 의 claim_refs 로
  모음(최대 3, 해소 불가 시 "" — 과잉 귀속 방지). 기존 source_registry 인프라 재사용.
- **결과**: 317 통과(신규 3). fin 번들 import → source_registry 에 mkt-1=YAHOO(차트 데이터)
  + src-1/2=bloomberg/federalreserve(top-level) 정확 수집 확인. 시각 프레임(YAHOO 출처 줄)은
  fin build-script(실 claude) 후 확인 예정.
- **한계(정직)**: v5.5.0 은 claim-출처 연결이 sparse(차트 데이터 출처 위주). fin(시장데이터)은
  출처 표기되지만 geo(서술 위주)는 대부분 빈 출처 — 과잉 귀속보다 빈 표기가 정직. 보고서-레벨
  출처를 크레딧 scene 으로 노출하는 건 별도 과제.
- **연관**: CHANGELOG v0.22.0, docs/05 §3.4e, docs/03 Bundle Importer.

---

## 2026-05-25 v0.21.0 — 순차 자막 (통문단 → 줄 단위 큐)

- **무엇을**: `SubtitleCue` 모델 + `RenderSceneProps.subtitleCues` + render_io
  `split_subtitle_cues` + Briefing 의 프레임 기반 큐 표시 + 테스트.
- **왜**: 자막이 나레이션 전체를 한 화면에 통째로 띄워 "자막답지 않다"는 지적(사용자). 실제
  자막은 줄 단위로 순차 전환된다.
- **어떻게**: narration 을 종결부호로 문장 분할 → 긴 문장은 42자 줄 길이로 공백 경계 재분할
  → scene 길이를 글자수 비례로 배분(TTS 가 문장별 타임스탬프를 안 주므로 표준 근사).
  Remotion 이 현재 프레임 시각(`frame/fps`, Sequence 가 0 기준 rebase)에 해당하는 큐만 띄움
  (짧은 페이드인). 큐 없으면 narration 폴백.
- **결과**: 314 통과(신규 3). **실물 geo 번들로 검증**: 같은 scene_02 를 frame 707/1126 에
  렌더하니 자막이 cue0("이 위기의 출발점은…추정됩니다.") → cue2("그 공격으로 사망했다는
  주장이 있습니다.") 로 줄 단위 전환됨을 프레임으로 확인. 중앙 takeaway/라벨 배지는 유지.
- **한계**: 글자수 비례라 실제 발화와 미세 오차. 정밀 싱크는 forced-alignment(whisper 등)가
  별도 과제. source 텍스트 화면 배선·차트 비주얼(Phase B)도 다음.
- **연관**: CHANGELOG v0.21.0, docs/05 §3.4e.

---

## 2026-05-25 v0.20.1 — LLM-AP-005: bundle 경로 대본 생성 실패 수정 (입력 캡 + 추출기 견고화)

- **무엇을**: bundle 어댑터 summary 섹션당 발췌 캡 + base_llm_worker JSON 추출기 견고화 +
  LLM-AP-005 기록 + 테스트.
- **왜**: v0.20.0 의 geo 실물 번들 풀 seam 에서 build-script 가 parse_failed. 진단: claude 가
  빈 응답이 아니라, 거대 summary(4,833자 prose 통째)를 5분 대본으로 압축하다 출력이 비대해져
  스스로 ```json 펜스 2개로 쪼개고(불완전) 서두 설명을 붙였다(526초). 손예시(작은 입력)는
  같은 5분 대본을 한 블록으로 성공했던 것과 대조 — 차이는 입력 크기.
- **어떻게**: (1) 어댑터가 섹션 prose 를 문장 경계 발췌(320자/섹션)해 개요만 전달 → 출력
  비대화·분할 예방(geo 4,833→2,462자). (2) 추출기가 서두 prose + 중간 ```json 블록 / 첫 균형
  {...}(문자열 내 중괄호 고려)를 회수. 단 두 분리 JSON 객체는 병합 불가 → 입력 캡이 1차 방어.
- **결과**: 단위 검증 — 추출기(서두+펜스/균형객체) + geo summary 2,462자 확인. 309→311 통과.
  **geo 실 run(실제 claude) 재검증은 본 커밋 직후 진행**(단일 완전 JSON 생성 확인 목표).
- **연관**: LLM-AP-005, 계약 v1 §6, CHANGELOG v0.20.1.

---

## 2026-05-25 v0.20.0 — 실물 v5.5.0 emit 연동 (§11 갭 수정 + 라벨 척추 provenance 합성)

- **무엇을**: agents_reviewer 실제 번들 2건(fin=엔캐리/VKOSPI, geo=이스라엘·이란)으로
  수신 모델 §11 대조 + 어댑터 강화. `BundleMapArc.highlight` 추가, 빈 claims 합성 로직.
- **왜**: v5.5.0 real emit 은 `claims=[]`(라이브 2-call 이 산문+차트만 생성, claim 그래프
  없음). 라벨 척추가 chart/map provenance + contradictions 를 타야 한다(agents_reviewer 가
  못박은 전제). 손예시(claims 있음)와 실물(claims 없음)의 간극을 실물로 메움.
- **어떻게**: §11 실물 대조에서 갭 1건 발견 — geo map arc 가 `highlight` 를 emit 하는데
  `BundleMapArc` 에 없어 extra=forbid 거부 → 필드 추가(additive). 어댑터는 claims 비면
  charts→claim(provenance.verification→status), map→claim, contradictions→disputed 합성 +
  섹션 prose 를 summary 로(ScriptWorker 가 발화형 변환). claims 차 있으면 직매핑(v5.6+).
- **결과**: 309 통과(신규 4). 두 실물 번들 검증 통과(arc 수정 후). 어댑터 산출:
  fin 5 claims(<확인> 1/<추론> 1/<반박됨> 3) + summary 4239자, geo 6 claims(<추론> 3/
  <반박됨> 3) + summary 4833자. **라벨 척추가 chart/map provenance 를 탐을 실물로 확인.**
  build-script→render 풀 seam(실제 claude)은 본 커밋 직후 검증.
- **다음**: source 텍스트 per-scene 배선(bundle sources→화면 출처), 정식 인용 마킹.
- **연관**: 계약 v1(agents_reviewer repo), CHANGELOG v0.20.0, docs/05 §3.4g.

---

## 2026-05-25 v0.19.0 — 영상 문법 재설계 (key takeaway 중앙 + 전체 나레이션 자막 바 + 인용 강조)

- **무엇을**: Remotion Briefing 레이아웃 재설계 + RenderSceneProps `source`/`isQuote` 필드 +
  render_io 인용 휴리스틱 + 테스트. "글자 도배"에서 "화면엔 핵심(key takeaway)만, 음성+하단
  자막 바" 형태로(레퍼런스 브리핑 스타일).
- **왜**: 사용자 원래 목표 — 직관적 화면 + 음성 + 세련된 작은 자막. ①②③ 결정 반영:
  ① key takeaway = on_screen_caption(caption) 중앙(pull_quote 는 추후 강조 인용 레이어),
  ② 자막 = 전체 narration(하단 바), ③ 캡션 바 스타일 + 인용은 강조색·인용부호로 명확히.
- **어떻게**: caption→중앙 대형 텍스트, narration→하단 반투명 자막 바, 좌상단 브랜드 /
  상단 출처(source) / 우상단 검증 라벨 배지. isQuote 면 강조색(골드) + 인용부호(`" "`/`「 」`)
  + 좌측 보더. isQuote 는 caption 의 인용부호 휴리스틱(정식 마킹은 ScriptWorker/bundle
  pull_quote 도입 시 교체). source 텍스트 배선은 bundle 어댑터 강화와 함께(다음).
- **결과**: 305 테스트 통과(신규 1). **still 프레임 실물 검증**: 정상 scene(브랜드/출처/
  `<추론>` 배지/중앙 takeaway/자막 바) + 인용 scene(골드 강조 + 인용부호) 둘 다 레퍼런스
  문법과 일치 확인(remotion npm install + headless-shell 렌더).
- **다음**: source 텍스트 per-scene 배선 + 정식 인용 마킹(ScriptSegment/bundle pull_quote).
  Phase B 차트/지도 SVG 가 중앙 슬롯에 합류하면 caption 은 제목/라벨로 축소.
- **연관**: CHANGELOG v0.19.0, docs/05 §3.4e.

---

## 2026-05-25 v0.18.1 — 외부 계약 v1 draft 보정 동기화 (map.id + map_ref resolve)

- **무엇을**: `BundleMap.id` 필드 + `section.map_ref → map.id` resolve 검증 추가. 테스트 2종.
- **왜**: v0.18.0 seam 에서 보고한 구조적 갭 — 번들 `map` 은 단일 객체인데 id 가 없어
  `section.map_ref="m-1"` 이 resolve 안 됐다. agents_reviewer 가 "단일 map + id"(예: "map-1")로
  계약 정본을 보정(A안 list[Map]·B안 bool 둘 다 회피 — 다중 지도 speculative generality 회피 +
  §8 균일 ref 모델 보존)했고, 우리 수신 mirror 를 동기화.
- **어떻게**: map.id 추가, validator 에 map_ref→map.id resolve(null 허용) 강제. 계약
  schema_version 무증분(draft 보정, 양측 합의). PATCH.
- **결과**: 304 테스트 통과(신규 2: map_ref resolve / dangling 거부). 보정된 예시 번들
  resolve 확인.
- **연관**: 계약 v1(agents_reviewer repo, commit 37416d4), CHANGELOG v0.18.1, docs/05 §3.4g.

---

## 2026-05-25 v0.18.0 — 외부 연동: agents_reviewer report_bundle 수신 (계약 v1, 텍스트 슬라이드 seam)

- **무엇을**: `ReportBundle` 수신 모델 + `bundle_io`(어댑터) + `bundle_service` +
  `import-bundle` CLI + 테스트 14. agents_reviewer 의 `report_bundle.json` 을 우리
  `research_dossier` 로 변환·흡수하는 새 intake 경로(`build-research-dossier`(LLM) 드롭인 대체).
- **왜**: agents_reviewer(텔레그램 보고서/분석 producer)와의 연동. "흡수(코드 복사)는
  파편화" 라 **버전 박힌 데이터 계약**으로 분석/차트데이터를 받기로 양측 합의(인터페이스 계약
  v1, 정본은 agents_reviewer repo `docs/CONTRACTS/report_bundle_v1.md`). 이번은 차트 없이
  컨테이너·매핑을 싸게 검증하는 ② seam 단계(비싼 producer PR/Q5 provenance 배선 앞에 둠).
- **어떻게**: 계약 §1~9 를 수신 모델로 미러. ① `extra="forbid"` fail-closed,
  ② `model_validator` 로 id unique + chart_refs/claim_refs resolve 강제(§8),
  ③ 차트 `data` 모양은 agents_reviewer `schemas.py` 가 SSOT 라 `Any` 통과(§9, 이중 SSOT 회피),
  ④ 라벨은 `verification`(=ResearchClaimStatus) 단일 축에서 파생 + 그대로 신뢰(재검증 floor
  없음, 사용자 결정), `model_forecast→inferred`(사용자 선택). 어댑터는 순수 변환(영속화는
  research_io). import-bundle 은 research_service 동형(precondition·전이 게이트).
- **결과**: 302 테스트 통과(신규 14). **실물 seam 관통**(예시 번들로): import-bundle →
  research_dossier(claims/라벨/근거/open_questions 정확) → build-script(실제 claude,
  6챕터/12세그/316초, TTS-lint 깨끗 — "HBM4"→"에이치비엠 사세대", "71,800원"→"칠만 천팔백 원")
  → build-scene(12) → build-audio stub(264.6초) → render_props(12 scene). **라벨 척추 무손실**:
  bundle claim C-2 `inferred` → 대본·scene·render 까지 `<추론>` 전파, C-1 `confirmed` → 무라벨.
- **seam 갭(producer PR 에 보고)**: `map_ref="m-1"` 이 단일 `map` 객체(id 필드 없음)로 resolve
  안 됨 → map 을 list+id 로 하거나 map_ref 의미 재정의 필요(현재 validator 는 map_ref 미강제).
  optional 빈값은 `""`/`null`/키생략 모두 우리 모델이 수용(producer 유연).
- **다음**: agents_reviewer producer PR(v5.5.0, Q5 provenance 실배선) → 실제 emit 으로
  필드 충실도 재검증. 우리 측 Phase 2(차트 컴포넌트 A안 + 복잡 3종 prerendered_svg B안).
- **연관**: 인터페이스 계약 v1(agents_reviewer repo), CHANGELOG v0.18.0, docs/05 §3.4g, docs/03.

---

## 2026-05-24 v0.17.0 — 대본 규칙: 4~6분 길이 + 후속 안내 마무리

- **무엇을**: script_worker 프롬프트에 (1) 영상 길이 4~6분(240~360초) 제한, (2) 마지막
  세그먼트는 항상 '지속 확인·후속 전달' 마무리(매번 표현 변주) 규칙 추가.
- **왜**: 사용자가 브리핑 포맷을 4~6분으로 고정하고, 끝맺음을 "계속 follow-up 하겠다"는
  뉘앙스로 통일하길 원함. 실제 샘플 길이(5.2분)가 이미 범위 안이라 자연스러운 제약.
- **어떻게**: 생성 단계(프롬프트) 규칙. label=null·claim_refs 빈 마무리 세그먼트 허용(도시어
  밖 멘트). 사용자 현재 audio 를 무효화하지 않으려 샘플 재생성은 보류(다음 build-script 부터 반영).
- **결과**: 288 통과(프롬프트 문자열 변경, 테스트 영향 없음). 사용자 만족 표명 → 세션 마무리
  커밋 후 main 에 fast-forward 머지.
- **연관**: CHANGELOG v0.17.0.

---

## 2026-05-24 v0.16.0 — TTS 발음 안전 (생성 차단 + 자동 린터)

- **무엇을**: tts_lint 린터(순수) + lint-script CLI + build-script 자동 검사 +
  script_worker 프롬프트 TTS 규칙 확장 + TTS_ANTIPATTERNS 부록 A + 샘플 재생성.
- **왜**: 실제 ElevenLabs 합성을 들어보니 narration 의 약어(USGS/CWA/OSINT)를 영어식으로
  읽어 AI 티. 카탈로그는 있었지만 파이프라인에 안 물려 있었음. 사용자가 50+ 실무 표기-해석
  오류 리스트를 주며 "재발 안 하게 확실히"를 요구.
- **어떻게**: 2겹 방어 — (1) 생성: script 프롬프트가 발화형 한국어 강제(약어→명칭/음차,
  날짜·시각·범위·단위·버전·URL·기호 풀어쓰기, 영문은 caption 에만). (2) 검출:
  lint_narration 이 12 카테고리 정규식으로 위험 표기 탐지, build-script 자동 경고 +
  lint-script --strict CI 게이트. 한글이 유니코드 \w 라 \b 대신 숫자 룩어라운드(버그 수정).
- **결과**: 288 통과(린트 12). 샘플 대본을 규칙으로 재생성하니 narration 로마자 0건(lint
  깨끗), 약어는 caption 에만. 운율·감정·믹싱 등 비표기 항목은 사람 검수 영역으로 명시.
- **연관**: docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md 부록 A, CHANGELOG v0.16.0.

---

## 2026-05-24 v0.15.7 — build-audio 세그먼트 진행 로그

- **무엇을**: build_audio 가 세그먼트별 `[i/n] 합성/완료` 를 출력.
- **왜**: mp3 전환으로 ElevenLabs 가 실제로 동작하기 시작하니, 16건 순차 합성 동안 출력이
  없어 사용자가 "멈췄나?" 혼동. (즉시 에러 → 무응답 전환 자체가 성공 신호였음.)
- **어떻게**: 루프에 print(flush=True) 진행 표시.
- **결과**: 276 통과. 다음 실행부터 진행률 보임.
- **연관**: CHANGELOG v0.15.7.

---

## 2026-05-24 v0.15.6 — ElevenLabs 무료 플랜용 mp3 기본 출력

- **무엇을**: ElevenLabs 기본 출력 포맷을 pcm_16000 → mp3_44100_128. file_ext 백엔드별
  결정 + mp3 CBR 길이 추정.
- **왜**: 권한(text_to_speech)·목소리(본인 생성) 다 통과 후에도 500 service_unavailable
  반복(같은 request_id). 원인은 pcm_* 출력이 무료 플랜에서 막힘 — 무료는 mp3 만.
- **어떻게**: _output_format(ELEVENLABS_OUTPUT_FORMAT, 기본 mp3) + file_ext 프로퍼티
  (mp3→.mp3 / pcm→.wav). mp3 는 _mp3_duration_sec(CBR bitrate, ID3 skip). audio_service 가
  engine.file_ext 로 파일명 결정. Remotion <Audio> 는 mp3/wav 둘 다 재생.
- **결과**: 276 통과. 무료 키 + 본인 목소리로 동작 기대. 정밀 길이/유료는 pcm 옵션.
  실물(무료 키)이 또 실서비스 제약을 잡음 — 이번 세션 ElevenLabs 무료 연쇄 6종
  (voices_read→text_to_speech→library voice 402→voice id 형식→pcm 500).
- **연관**: CHANGELOG v0.15.6.

---

## 2026-05-24 v0.15.5 — ElevenLabs 기본 voice 폴백 (voices_read 권한 불요)

- **무엇을**: voice 미지정 시 /v1/voices 자동조회 대신 기본 premade voice 로 폴백.
- **왜**: 사용자 키가 text_to_speech 권한만 있어 GET /v1/voices(=voices_read 필요)에서
  401 missing_permissions. 목록 조회는 사실 불필요했음.
- **어떻게**: _resolve_voice = voice > ELEVENLABS_VOICE_ID > default_voice_id
  (21m00Tcm4TlvDq8ikWAM, Rachel). /v1/voices 호출 제거. 본인 목소리/클론은
  ELEVENLABS_VOICE_ID 로 지정.
- **결과**: 276 통과. text_to_speech 권한만으로 동작. 실물 키가 또 실제 동작을 잡음
  (cp949 → set 공백 → npx.cmd → voices_read, 4연속 환경/실서비스 이슈).
- **연관**: CHANGELOG v0.15.5.

---

## 2026-05-24 v0.15.4 — Windows npx 실행 버그 수정 (RENDER-AP-002)

- **무엇을**: render-debug 의 npx 호출을 shutil.which 로 해석 + 배치면 cmd /c 경유.
- **왜**: 사용자 Windows 에서 render-debug 가 "npx/node 못 찾음" 으로 실패. Node v24
  설치돼 있고 셸 `npx --version` 도 됐지만, Python subprocess 가 `npx.cmd`(배치)를
  PATHEXT 없이 못 찾아 FileNotFoundError. 또 실물 실행이 Windows 전용 버그를 잡음.
- **어떻게**: shutil.which("npx") → Windows 면 npx.cmd 절대경로. .cmd/.bat 이고 nt 면
  ["cmd","/c",npx,*args], 아니면 [npx,*args]. POSIX 무영향(스크립트 직접 실행).
- **결과**: 275 통과(렌더 경로는 Linux 단위테스트 비대상이라 로직 분기만 검증). 사용자는
  git pull 후 render-debug 재시도.
- **연관**: RENDER-AP-002, CHANGELOG v0.15.4.

---

## 2026-05-24 v0.15.3 — TTS env 값 공백 strip (Windows set 트레일링 스페이스)

- **무엇을**: tts_backends 의 ElevenLabs/Voicebox 환경변수 값을 .strip().
- **왜**: 사용자가 `set ELEVENLABS_API_KEY=sk_...930 ` (뒤 공백 포함)로 설정 → httpx
  "Illegal header value" 로 거부. Windows `set VAR=값 ` 이 뒤 공백을 값에 포함시킴.
- **어떻게**: api_key/voice/base_url/model_id, voicebox url/profile/lang 모두 .strip().
  뒤 공백 키 회귀 테스트 추가.
- **결과**: 275 통과. 또 실물 실행이 환경 의존 버그를 잡음(cp949 → 헤더 공백). 사용자는
  키 재설정(뒤 공백 없이) 또는 git pull 후 그대로 진행 가능.
- **연관**: CHANGELOG v0.15.3.

---

## 2026-05-24 v0.15.2 — requirements.txt cp949 디코드 버그 수정 (Windows)

- **무엇을**: requirements.txt 를 ASCII-only 로 정리(한글 주석→영문, en-dash→hyphen) +
  상단에 재발 방지 주석.
- **왜**: 사용자가 한국어 Windows 에서 `pip install -r requirements.txt` →
  `UnicodeDecodeError: 'cp949' ... 0xe2`. pip 가 requirements 를 로케일 코덱(cp949)으로
  읽는데 파일에 UTF-8 문자(한글/en-dash)가 있어 실패. 리눅스 CI 엔 안 터지던 환경 의존
  버그 — 또 "실물 실행"이 잡아냄.
- **어떻게**: 주석 영문화 + en-dash 제거. 패키지 핀 동일. 워크어라운드 `set PYTHONUTF8=1`.
  .py 소스는 Python 이 UTF-8 로 읽어 영향 없음.
- **결과**: ASCII 검증 통과. git pull 후 그냥 pip install 가능.
- **연관**: CHANGELOG v0.15.2.

---

## 2026-05-24 v0.15.1 — 로컬 테스트 샘플 + 가이드

- **무엇을**: samples/hualien2024/ (research/script/scene JSON) + docs/RUN_LOCAL.md.
- **왜**: "대본+음성 입히는 테스트 해보고 싶어" 요구. 근데 hualien2024 는 클라우드 세션
  안에만 있고(gitignore) 사용자 PC엔 없음 → 동일 산출물을 커밋해 마찰 제거.
- **어떻게**: 실제 claude run 으로 만든 4개 JSON 을 samples/ 로 복사 커밋. 사용자는
  projects/ 로 복사 후 ELEVENLABS_API_KEY 만 넣고 build-audio --backend elevenlabs +
  render-debug → research/script 재생성 없이 음성+영상 확인. wav/mp4 는 gitignore.
- **결과**: 사용자가 2~3줄로 대본+음성 영상 테스트 가능. 키는 사용자 환경변수(세션에
  넣지 않음). 다른 주제는 full 파이프라인(claude 필요).
- **연관**: docs/RUN_LOCAL.md, CHANGELOG v0.15.1.

---

## 2026-05-24 v0.15.0 — ElevenLabs "키만 있으면 동작" 보강 + 통합 검증

- **무엇을**: 사용자가 "설치 X + 기본 목소리" 로 ElevenLabs 선택. 백엔드를 voice ID 없이
  키만으로 동작하게 보강 + mock 서버 통합 테스트.
- **왜**: Voicebox 자가호스팅/로컬설치는 "기본 목소리" 목적엔 과함 → 관리형 클라우드 TTS.
  ElevenLabs 백엔드는 이미 있었으나 voice 지정을 요구해 마찰이 있었음.
- **어떻게**: voice 미지정 시 GET /v1/voices 로 첫 목소리 자동선택. BASE_URL/MODEL_ID
  환경변수화(테스트·프록시·모델 선택). _MockElevenLabsServer 로 GET voices + POST tts
  전 경로 실 소켓 검증 (xi-api-key 헤더, output_format=pcm_16000, pcm→wav 길이).
- **결과**: 274 테스트. 실제 합성은 사용자 키 필요(외부 API라 세션에 키 넣지 않음) →
  사용자 로컬/머신에서 검증. 우리 쪽은 "키만 넣으면 작동" 상태.
- **연관**: docs 추후(테스트 가이드 v0.15.1), CHANGELOG v0.15.0.

---

## 2026-05-24 v0.14.1 — Voicebox 백엔드 파이프라인 통합 검증 (mock 서버)

- **무엇을**: "우리 파이프라인 상에서 작동되게 할 수 있어?" 요구. 실제 Voicebox 합성은
  이 환경에서 불가(HF 차단+미설치)하지만, 우리 통합 경로를 Voicebox-모양 mock HTTP
  서버(`_MockVoiceboxServer`, 스레드 ThreadingHTTPServer)로 실 소켓 검증.
- **왜**: stub(엔진 미접촉)만으로는 HTTP 어댑터의 실제 동작(httpx POST, content-type 분기,
  바이트/JSON 응답 처리, wav 길이측정, 요청 계약)을 못 본다. 신경망만 Voicebox 몫이고
  나머지 배선은 여기서 증명 가능.
- **어떻게**: mock 이 `POST /generate {text,profile_id,language}` 를 받아 무음 wav 를
  audio/wav 또는 JSON+base64 로 반환. build-audio --backend voicebox 가 양쪽을 처리해
  audio_manifest+wav 를 만들고, 요청 본문이 문서 계약과 일치함을 assert.
- **결과**: 272 테스트 통과(voicebox 통합 3종 추가). 우리 쪽은 "Voicebox 가 뜨면 바로
  작동" 상태. 사용자 측 차단요인은 Voicebox 앱 미실행(localhost:17493 연결거부) — 앱
  설치·실행 후 /docs 로 응답 포맷 확정 시 어댑터 미세조정만 남음.
- **연관**: CHANGELOG v0.14.1, tests/test_audio_flow.py.

---

## 2026-05-24 v0.14.0 — Voicebox TTS 백엔드 흡수 (HTTP, MIT)

- **무엇을**: 사용자가 지정한 github.com/jamiepine/voicebox 를 `voicebox` TTS 백엔드로
  흡수. Voicebox 의 로컬 FastAPI(`127.0.0.1:17493`) `POST /generate` 를 HTTP 호출.
- **왜**: "TTS 엔진 자체를 흡수" 요구. Voicebox 는 라이브러리가 아니라 풀스택 앱(Tauri+
  FastAPI+Rust, MIT)이라 벤더링 대신 **로컬 API 호출**이 정답 — 무거운 모델/GPU/가중치는
  Voicebox 측, 우리 repo·CI 는 가벼운 HTTP 어댑터만.
- **어떻게**: WebFetch 로 레포 확인 — MIT, 7엔진(Qwen3-TTS/Chatterbox/Kokoro/LuxTTS 등),
  zero-shot 클로닝, API `POST /generate {text, profile_id, language}`. profile_id 는
  앱에서 본인 목소리로 1회 생성. 응답 포맷(bytes/JSON)이 버전마다 달라 방어적 처리 +
  wav 길이측정/추정 폴백. ElevenLabs 어댑터와 동형(대상이 localhost).
- **사양 확인(사용자 요청)**: 엔진 선택형 — LuxTTS(~1GB VRAM, CPU 150x)/Kokoro(82M) 저사양,
  Qwen3(0.6B/1.7B)/TADA(1B/3B) GPU 권장. CPU "works everywhere, just slower". 우리는 배치
  합성이라 저사양도 실용. GPU 부담은 Voicebox 쪽이라 우리 프로젝트는 무거워지지 않음.
- **결과**: 269 테스트 통과(stub/factory/guard). **합성 실검증은 사용자 로컬**에서만 가능 —
  이 환경은 HF 가중치 allowlist 차단(`Host not in allowlist`) + Voicebox 미설치. github/
  pypi 는 도달 가능 확인. /generate 응답 포맷은 사용자 머신 /docs 로 확정 후 조정 가능.
- **연관**: docs/03 TTS 행, docs/06 §8.5(권리), CHANGELOG v0.14.0.

---

## 2026-05-24 v0.13.0 — 수직 슬라이스 V4b: 영상-음성 싱크

- **무엇을**: render_props 가 scene+script+audio 의 결합점이 되어, audio_manifest 가
  있으면 scene 타이밍을 실측 음성 길이로 재계산하고 각 scene 에 wav 경로(audioPath)를
  단다. Remotion Briefing 이 `<Audio>`+`staticFile` 로 오디오 트랙 삽입, 렌더 시
  `--public-dir`=project_dir.
- **왜**: V4a 가 음성 파일까지만 만들었음 → 영상에 실제로 싱크. stub 길이(471)가 LLM
  scene est(439)와 달랐던 것을 실측 길이로 정정.
- **어떻게**: build_render_props 에 audio_manifest 옵션 추가, 있으면 duration=음성 길이,
  start_sec 재누적, audioPath 부착. 없으면 무음 폴백(하위호환, 기존 테스트 유지).
  Remotion 은 public-dir 로 project_dir 를 정적 서빙해 08_audio/narration/*.wav 참조.
- **결과**: 267 테스트 통과. hualien2024 재렌더 14136 프레임(471초, 오디오 기반) +
  오디오 트랙 muxing(28.9MB) 성공. staticFile/public-dir 정상 작동 확인. 소리는 stub라
  무음 — 실제 음성은 사용자 로컬의 OSINT_TTS_CMD(local) 또는 ELEVENLABS_API_KEY(elevenlabs)
  로 build-audio 후 render-debug. 수직 슬라이스(주제→음성 싱크 영상) 메커니즘 완성.
- **연관**: docs/05 §3.4e(audioPath), docs/13 V4, CHANGELOG v0.13.0.

---

## 2026-05-23 v0.12.0 — 수직 슬라이스 V4: TTS 흡수 (교체 가능 백엔드)

- **무엇을**: TTS 백엔드 추상화(`workers/tts_backends.py`) + AudioManifest 모델 +
  audio_io/audio_service + `build-audio` CLI. full_script → 나레이션 wav + manifest.
- **왜**: 사용자가 공유한 외부 워크플로(VoiceBox 로컬 음성복제 + HyperFrames)에서 음성
  부분만 흡수 결정. 영상의 무음 한계를 메움. "ElevenLabs 로도 교체 가능하게"라는 요구를
  백엔드 추상화로 충족 (BaseLLMWorker 의 llm_backend 패턴 차용).
- **어떻게**: local(기본·OSINT_TTS_CMD·프라이버시) / elevenlabs(ELEVENLABS_API_KEY·외부·
  opt-in) / stub(무음·테스트) 3종. 길이는 wav 측정(권위 소스). HyperFrames 는 보류
  (Remotion 이미 보유). 이 환경엔 보장된 로컬 엔진/키가 없어 stub 로만 실검증.
- **결과**: 265 테스트 통과. hualien2024 stub 실행 → 16 wav + manifest(471초). stub 길이
  (471초)가 LLM scene est(439초)와 달라, **실제 TTS 길이로 타이밍 재계산이 필요함을 확인**
  (V4b 과제). 권리(본인 목소리만, elevenlabs opt-in)는 docs/06 §8.5 에 기록.
- **다음(V4b)**: audio_manifest 의 실측 길이로 scene/render_props 타이밍 재계산 + Remotion
  에 나레이션 오디오 트랙 삽입 → 음성 들어간 영상.
- **연관**: docs/05 §3.4f, docs/06 §8.5, docs/03 TTS 행, CHANGELOG v0.12.0.

---

## 2026-05-23 v0.11.1 — 렌더 환경 대응 (RENDER-AP-001) + 첫 실물 영상 완주

- **무엇을**: V3 코드를 실제로 렌더해보니 Remotion 의 chromium headless-shell 자동
  다운로드가 네트워크 allowlist 에 막힘(403). 머신의 chrome-headless-shell 자동탐지 +
  `--browser-executable` 부착으로 우회. RENDER-AP-001 기록.
- **왜**: 또 한 번 "실물 실행"이 stub/단위테스트가 못 보는 환경 의존성을 드러냄 — 이번엔
  렌더 인프라. V3 의 진짜 산출물(영상)을 뽑으려면 필수.
- **어떻게**: full chrome 는 old-headless 미지원으로 launch 실패 → headless_shell 만 채택.
  Playwright(`/opt/pw-browsers/...`)/puppeteer/ms-playwright 캐시를 자동탐지, 우선순위는
  플래그 > OSINT_HEADLESS_SHELL > 자동탐지. 못 찾으면 정상 다운로드로 폴백.
- **결과**: hualien2024 draft_debug.mp4 — 13170 프레임(7분19초), 27MB 렌더 성공.
  **topic 한 줄 → research → script → scene → 영상까지 파이프라인 첫 완주.** 미검증/추론/
  주장 라벨이 슬라이드 색 배지로 표시됨을 실물로 확인. (무음/캡션 슬라이드 버전.)
- **연관**: RENDER-AP-001, CHANGELOG v0.11.1, docs/13 수직 슬라이스.

---

## 2026-05-23 v0.11.0 — 수직 슬라이스 V3: Remotion 최소 렌더

- **무엇을**: `remotion/` 프로젝트(텍스트 슬라이드 `Briefing` 컴포지션) + RenderProps 모델
  + render_io(scene_manifest+full_script→render_props.json) + `render-debug` CLI.
- **왜**: 수직 슬라이스 마지막 단계 — topic 부터 영상까지 처음으로 관통. 사용자가 실물을
  눈으로 보고 톤·구조·라벨 표시를 검증하기 위함.
- **어떻게**: 이 환경에 node22/npm + chromium 네이티브 라이브러리(libnss3 등 5종) 존재 확인
  후 진행. render_props 는 scene_manifest(타이밍/라벨) + full_script(나레이션)를 join 한
  평면 구조(TS camelCase). 라벨은 슬라이드 우상단 색 배지. render-debug 는 state 전이 없는
  미리보기(현재 scene_manifest 로 언제든 재생성). node_modules/mp4 는 gitignore.
- **결과**: 256 테스트 통과. hualien2024 render_props 16 scene 생성 확인 (라벨 전파 유지).
  실제 Remotion 렌더는 본 커밋 후 실행 검증. 정식 RemotionJob/render_worker·TTS·Phase 7
  에셋은 슬라이스 관통 후 보강 예정.
- **연관**: docs/05 §3.4e, docs/13 수직 슬라이스, CHANGELOG v0.11.0.

---

## 2026-05-23 v0.10.0 — 수직 슬라이스 V2: 최소 Scene

- **무엇을**: scene_builder(순수) + scene_io + `build-scene` CLI. full_script →
  scene_manifest.json (세그먼트 1:1 매핑, 누적 타이밍).
- **왜**: 수직 슬라이스 V2. 텍스트 슬라이드 영상 목표라 scene 계획에 LLM 불필요 →
  결정론적 변환이 더 빠르고 확정적. Phase 5 source_registry_builder 의 순수 함수 패턴 채택.
- **어떻게**: SceneEntry 골격(기존 모델) 재사용. inference_label_required=segment.label
  유무로 미검증 배지 신호, source_link_required=claim_refs 유무. state 는
  script_writing→script_review→scene_planning (script_review Gate 흡수).
- **결과**: 252 테스트 통과. hualien2024 실행 → 16 scene, 누적 7.32분, 확인 사실
  scene 무라벨 / 미검증·추론·주장 scene LABEL 정확. 빌더가 타이밍 권위(LLM 자체 보고
  total 466초 오차를 실제 합 439초로 정정). 다음: V3 Remotion 최소 렌더.
- **연관**: docs/03 Scene Planner 행, docs/13 수직 슬라이스, CHANGELOG v0.10.0.

---

## 2026-05-23 v0.9.0 — Phase 6 Script (수직 슬라이스 V1)

- **무엇을**: ScriptWorker + FullScript 모델 + script_io/script_service + `build-script`
  CLI. research_dossier → full_script.json. blueprint 단계 흡수.
- **왜**: 수직 슬라이스 V1. 실물 영상까지 최단경로의 첫 콘텐츠 단계. 6A 와 같은 패턴.
- **어떻게**: 6A 패턴 답습 (모델→worker(.replace())→io→thin service→CLI→전이). state 는
  research_in_progress→blueprint_review→script_writing 으로 blueprint_review 를 통과만.
  segment.label 에 claim status 라벨을 박아 미검증 정보 추적(GOAL G4).
- **결과**: stub 247 테스트 통과 + **실제 claude run** 으로 hualien2024 대본 생성. 라벨
  전파 무손실(로이터 단독→<주장>, X→<미검증>, 추론→<추론>, 시드→<미검증>, 공식2기관→
  무라벨), 미검증 헤지 서술, 466초≈7.8분(목표 8분) 분량 정확. 인용 충실도는 6A 와 같은
  천장(소스 본문 부재) 상속.
- **연관**: docs/05 §3.4d, docs/03 Script Agent 행, docs/13 6D, CHANGELOG v0.9.0.

---

## 2026-05-23 v0.8.1 — LLM 브리지 response 모드 격리 (LLM-AP-004) + 개발 방향 전환

- **무엇을**: 6A 를 처음으로 **실제 `claude`** 로 돌려 검증. 그 과정에서 response 모드
  호출이 에이전트로 변질되는 사고를 발견·수정. `--tools ""`/`--no-session-persistence`
  + 중립 cwd 로 격리. LLM-AP-004 기록.
- **왜**: 사용자가 "stub 테스트만 하고 실물을 안 쓰는 게 맞냐"는 의문 제기 → 개발 방향을
  **수직 슬라이스(실물 영상까지 최단경로) + 실제 LLM run 으로 기능 리뷰 + codex 외부
  리뷰 일시 중단**으로 전환. 그 첫 실 run 에서 인프라 버그가 바로 드러남 — stub 초록불
  뒤에 숨어 있던 문제.
- **어떻게**: `claude -p ... --output-format json` 이 cwd 의 CLAUDE.md/훅/도구를 물어
  22턴/6분/$0.74 동안 commit 시도하고 JSON 을 안 줌. 도구 비활성 + repo 밖 cwd 로 1턴/
  1.3초/$0.005/정확 JSON 으로 정상화. 에러 처리(raw 보존·parse_failed·전이 차단)는
  설계대로 작동해 상태 오염은 없었음.
- **결과**: 6A 실 run 으로 hualien2024(2024 대만 화롄 M7.4) research_dossier 정상 생성.
  검증 로직(공식 2기관→confirmed, 단일언론→claim, 미검증 X→unverified+risk_flag 전파,
  시드→unverified+1차검증 요구)이 의도대로 동작 확인. 단 소스 본문이 registry 에 없어
  evidence quote 가 일부 재구성됨 — 6A 품질 천장이 Phase 5 본문 적재량에 묶임을 확인.
- **연관**: LLM-AP-004, ADDENDUM_04 §4.1/§5.1, CHANGELOG v0.8.1.

---

## 2026-05-23 v0.8.0 — Phase 6A Research 구현

- **무엇을**: `ResearchWorker`(BaseLLMWorker) + `ResearchDossier` 모델 + `research_io`
  + `research_service` + `build-research-dossier` CLI + 단위테스트. source_registry +
  manifest.initial_links → 주장-근거 페어 dossier. state `source_completeness_review →
  research_in_progress`.
- **왜**: Phase 6A. Research 단계는 영상 서사의 사실 토대를 만든다. 사용자가 사전 제공한
  분석 리포트(initial_links)는 자체 생성 2차 분석이라 사실 앵커가 아니므로, 시드로만
  다루고 1차 출처 별도 검증을 강제할 구조가 필요했다.
- **어떻게**: Phase 5 패턴 답습 — 모델(schemas) → worker(.replace() 프롬프트, 질문 금지)
  → io 경계(atomic write/load) → thin CLI(precondition→worker→영속화 검증 게이트→전이).
  claim `status`(ResearchClaimStatus)가 SSOT 이고 영상 라벨(`<미검증>` 등)은
  `CLAIM_STATUS_LABELS` 로 파생(이중출처 방지). `Evidence` 는 source_id(1차)/seed_id(파생)
  둘 다 인용 가능, registry 존재 cross-check 는 6B Evidence Guard 로 미룸(additive 유지).
- **결과**: 242 테스트 통과(6 신규). py_compile + import smoke OK. VERSION 0.7.3 → 0.8.0.
  MINOR push 후 codex 외부 리뷰(C10.1) 대상 — 결과는 다음 PATCH v0.8.1 로 흡수.
- **연관**: docs/13 6A, docs/05 §3.4c, docs/03 Research Agent 행, docs/12 §3.

---

## 2026-05-23 v0.7.3 — Phase 6 세부 분해 (서브스텝) 문서화

- **무엇을**: Phase 6 를 6A(Research) / 6B(Evidence Guard) / 6C(Blueprint) /
  6D(Script) / 6E(Scene) 서브스텝으로 분해해 docs/13 에 표로 추가. 산출물(신규 모델)·
  워커·입력·state/Review Gate·증분 단위 명시.
- **왜**: "Phase 6 = ResearchWorker 하나?" 라는 사용자 질문에서 출발 — Phase 6 는
  Research→Script→Scene 전 구간이고 워커가 5개(Research/Evidence Guard/Blueprint/
  Script/ScenePlanner)다. 새 세션이 한 번에 다 만들지 않고 서브스텝 단위로 진행하도록
  분해도를 SSOT(로드맵)에 박았다.
- **어떻게**: 각 서브스텝에 Phase 5 패턴(모델 → 순수 worker/agent → io 경계 → thin
  CLI → Review Gate) 을 반복. Gate 3(blueprint)/4(script)/5(scene)는 docs/12 와 정합.
  6A 의 입력에 manifest.initial_links(사용자 분석 리포트)를 1차 자료 추출 시드로 명시.
- **결과**: 문서 PATCH (코드 변경 없음, 236 테스트 유지). 다음: 6A 착수(ResearchDossier
  모델 + ResearchWorker + research_io + CLI).
- **연관**: docs/13. C10.1 mandatory 트리거 아님(docs PATCH).

## 2026-05-23 v0.7.2 — 목표 길이 범위 3~20분으로 통일

- **무엇을**: target_duration_min 지원 범위를 3~20분으로. 모델 제약(ge=3/le=20), 웹 폼
  min/max + clamp, 로드맵 Phase 6 완료 기준("15–20분" → "3–20분") 동기화.
- **왜**: 사용자 요청 — 샘플/실제 길이를 짧은 브리핑(3분)부터 폭넓게 조정 가능하게.
  기존엔 longform 가정(15–20)이라 짧은 영상이 스펙상 애매했고, 웹 폼은 반대로 1~180
  으로 과하게 열려 있어 범위가 일관되지 않았다.
- **어떻게**: 단일 범위(3~20)를 모델 제약·UI·문서 세 곳에 일치. 웹은 보정(clamp)으로
  UX 친화, CLI/직접 모델 생성은 범위 밖이면 ValidationError 로 거부(경계 enforce).
  v0.6.1 의 reliability ge/le 추가와 동일한 패턴 — additive 제약, schema_version 1 유지.
- **결과**: 신규 2 테스트(CLI 거부, 웹 clamp), 전체 234 → 236 통과.
- **연관**: PATCH (비구조적 범위 조정) — C10.1 mandatory codex 트리거 아님. docs 05/13
  동기화(C7).

## 2026-05-23 v0.7.1 — 외부 코드 리뷰 1차 반영 (v0.7.0 웹 진입 robustness)

- **무엇을**: codex 외부 리뷰(v0.7.0 대상) High 2 / Medium 3 / Low 2 를 전부 흡수.
  false positive 없음.
- **흡수 내역**:
  - **High1 (race window)**: intake_service 최종 전이가 `resume_project` 재호출 대신
    in-memory manifest 사용. planner worker 가 manifest 를 건드리지 않으므로 디스크
    상태와 동일 — 재로딩 사이 동시 변경 race 를 제거.
  - **High2 (web 예외 누락)**: create_project 가 `ValueError`(전이 실패)를 409
    "retry" 로, 기타 예외를 500 + `logger.exception` 으로 구조화 처리. 라우트의
    JSON 에러 계약 일관성 확보.
  - **Med1 (Content-Length)**: 잘못된 헤더를 무시(pass)하지 않고 400. (submit 라우트의
    동일 패턴은 prior-reviewed 라 본 PATCH scope 밖으로 유지.)
  - **Med2 (링크 trust boundary)**: `_normalize_initial_links` 를 new_project 입력
    경계에 신설 — 제어문자/공백 제거, http(s) allowlist, 2048자·50개 cap. 사용자
    링크가 planner 프롬프트에 verbatim 삽입되므로 prompt-injection/구조 훼손 차단.
    web/CLI 두 경로가 new_project 한 곳을 통과하므로 단일 출처.
  - **Med3 (backend fallback)**: 잘못된 backend 를 조용히 claude 로 fallback 하지 않고
    400 (클라이언트 버그 가시화). 폼은 select 라 정상 경로 영향 없음.
  - **Low1 (type:ignore)**: `llm_backend` 를 `ClassVar` → 일반 속성으로 (base + 3
    worker). 인스턴스 override 가 타입상 합법이 되어 `# type: ignore[misc]` 제거.
    런타임 동일(ClassVar 는 타입 힌트일 뿐), 값 검증은 입력 경계·CLI_INVOCATION 키.
  - **Low2 (projects_root)**: run_intake_planner 의 미사용 파라미터 제거, cfg 와 단일
    출처로.
- **결과**: 신규 2 테스트, 전체 232 → 234 통과. py_compile 통과.
- **연관**: C10.3 — 본 PATCH 는 "외부 리뷰 결과 반영" 카테고리로 codex 재리뷰 **면제**
  (무한 루프 방지). v0.7.0 (본 PATCH 가 반영하는 트리거).

## 2026-05-23 v0.7.0 — 웹 주제 입력 진입 화면 + 초기 링크 주입

- **무엇을**: CLI 전용이던 "주제 입력 → intake_plan 생성" 흐름을 웹으로. `GET /new`
  폼 + `POST /new` (new_project + planner + `/intake/{pid}` 리다이렉트). 프로젝트
  생성 시 사용자 사전 제공 링크(`initial_links`)를 받아 planner 프롬프트에 반영.
- **왜**: "주제는 intake 화면 어디서 주입되나?" 질문에서 출발 — 기존엔 주제 입력
  경로가 CLI(`new-project`) 전용이고 웹 intake 페이지는 이미 만들어진 plan 을 렌더만
  했다. 사용자가 자체 생성 OSINT 분석 리포트 링크를 보유 → 이를 생성 시점에 넣어
  계획에 반영하고 싶다는 요구(AskUserQuestion: "주제+초기 링크 동시 입력").
- **어떻게**:
  - planner 오케스트레이션(전이+worker+idempotency)을 `orchestrator/intake_service.py:
    run_intake_planner` 로 추출, CLI `_cmd_plan_intake` 는 thin wrapper 로 위임 →
    CLI/Web 가 전이 순서를 공유 (drift 방지). 기존 35 intake 테스트로 동작 보존 확인.
  - `ProjectManifest.initial_links` additive 필드 (schema_version 1 유지). planner
    프롬프트에 "사용자 사전 제공 자료(manual_user_provided 후보)" 섹션 — 단 사용자
    제공이라도 사실 검증은 별도 필요함을 명시(환각 방지).
  - 웹 폼은 기존 intake 페이지와 동일하게 외부 템플릿 엔진 없이 인라인, html.escape,
    project_id 정규식 검증, content-length 상한, 중복 409 / 검증 400 / planner 500.
  - **링크 자체의 소스 평가**: 사용자 확인 결과 자체 생성 리포트 → manual_user_provided
    (사용 가능). 단 2차/파생 분석이므로 reliability 중간, 1차 자료 추출·교차검증을
    Phase 6 ResearchWorker 가 수행하는 것이 바람직(본 PATCH 범위 밖, 설계 메모).
- **결과**: 신규 10 테스트, 전체 222 → 232 통과. py_compile 통과.
- **연관**: Phase 3(Dynamic Intake Page)의 진입부 확장. docs/04, docs/05 동기화(C7).
  MINOR → push 직후 codex 외부 리뷰 **필수**(C10.1). 결과 흡수는 다음 PATCH(v0.7.1).

## 2026-05-23 v0.6.1 — 외부 코드 리뷰 1차 반영 (Phase 5 산출물 robustness)

- **무엇을**: codex 외부 리뷰(v0.5.5/v0.6.0 대상)의 Critical/Medium/Nit 중 합의된
  항목 흡수. (1) `build-source-registry` 의 registry 영속화 디스크 `OSError`
  누락 수정, (2) checker severity 카운터 `str()` 정규화, (3) 미정의 권리 상태용
  `RIGHTS_STATUS_UNKNOWN_VALUE` issue_type 신설, (4) reliability_score /
  reliability_threshold `ge=0.0, le=1.0` 제약.
- **왜**: (1) report persist 는 `OSError` 를 잡는데 registry persist 는 안 잡아
  비대칭이었다 — codex 는 report 쪽만 지적했으나 실제 더 정확한 갭은 registry
  쪽. 영속화 어디서 깨지든 controlled exit + 전이 금지여야 한다. (2) `i.severity
  == Enum.value` 는 `use_enum_values=True` config 에 결합 — config 변경 시 조용히
  깨진다. (3) known `review_required` 와 unknown value 혼동 방지(진단 선명화).
  (4) score/threshold 는 도메인상 0~1 (worker 문서 명시) — 외부 주입 방어.
- **어떻게**: codex 가 제안한 광범위 `except Exception` 은 CLAUDE.md "일어날 수
  없는 시나리오 방어 금지" 에 어긋나 `OSError` 범위로 한정. 제약 추가 전 전체
  test 의 reliability_score 값(0.1~0.9)이 범위 내임을 확인 — breaking 없음.
- **보류 (사용자 합의, false positive / scope 밖)**:
  - **High (빈 partials strict 모드)**: AskUserQuestion → "현재 유지". `partials/`
    부재 시 `NO_USABLE_SOURCES` blocker 리포트가 이미 '자료 0개' 를 명확히 신호하고
    Review Gate 2 에서 사용자가 보완/진행 판단. 추가 플래그는 YAGNI(C8.4).
  - **Medium 2 (state `hasattr` fallback)**: 신규 코드 아님 — `plan-intake`
    (main.py:256)·`submit-intake`(:370) 와 동일한 기존 컨벤션. load-boundary
    리팩토링은 본 PATCH scope 밖.
  - **Low (temp 파일 race)**: `project_manager._write_manifest` 정책을 의도적
    미러링. 선형 state machine 상 동일 프로젝트 동시 쓰기 미발생.
  - **Low (filename casefold)**: 대소문자만 다른 파일명 + task_id 동률의 exotic
    케이스. cross-platform 재현성 요구가 명시되기 전까지 보류.
- **결과**: 테스트 222/222 통과 (회귀 없음). py_compile 통과.
- **연관**: C10.1 — 본 PATCH 는 "외부 리뷰 결과 반영" 카테고리로 codex 재리뷰
  **면제**(무한 루프 방지, C10.3). C7 동기화 (05_DATA_SCHEMA_SPEC).

## 2026-05-23 v0.6.0 — Phase 5 완료 (SourceCompletenessReport + checker)

- **무엇을**: `SourceCompletenessReport` 모델 + `source_completeness_checker`
  (순수 함수) + CLI 와이어링. `build-source-registry` 가 registry + completeness
  report 2 산출물을 만들고 Review Gate 2 (`source_completeness_review`) 로 전이.
- **왜**: roadmap §42 의 Phase 5 완료 기준 = `source_registry.json` +
  `source_completeness_report.json` 2 산출물 ("소스별 권리·신뢰도·위험도 기록,
  부족 자료 식별"). registry 만으로는 "부족 자료 식별" 이 빠졌다.
- **어떻게**: checker 도 builder 처럼 순수 함수 (디스크 I/O 없음, 영속화는 io
  모듈). 판정 기준은 docs/06 §2 의 권리 표에 근거 — 사용 가능 (rights_clear /
  manual_user_provided) 집계, 그 외는 warning/info. **severity 정책은
  AskUserQuestion 으로 사용자 확정**: (1) reliability 임계 기본 0.5 (strict `<`,
  기본값 0.5 자체는 통과), (2) **사용 가능 자료 0개일 때만 blocker** — 권리
  미확보/위험은 warning 으로 두고 Review Gate 2 에서 사용자가 '보완 또는 진행'
  판단. overall_status ∈ {ready, needs_attention, insufficient}.
- **결과**: 테스트 204 → 222 (checker 18 + io 1 + CLI 강화). 전부 통과.
  Phase 5 완료 marker (MINOR). C3 준수 (optional 모델 추가, schema_version 1 유지).
- **연관**: Phase 5 완료. C7 동기화 (05_DATA_SCHEMA_SPEC, 13_ROADMAP).
  C10.1 — MINOR + Phase 완료 → push 직후 codex 외부 리뷰 **필수** (트리거).

## 2026-05-23 v0.5.5 — Phase 5 셋째 PATCH (source_registry.json 영속화 wiring)

- **무엇을**: `source_registry_builder` (순수 함수) 의 I/O 경계
  `orchestrator/source_registry_io.py` 신설 + `build-source-registry` CLI
  서브커맨드. `02_sources/partials/*.json` → builder → `source_registry.json`.
- **왜**: v0.5.3/v0.5.4 의 builder 는 디스크 I/O 가 없어 (의도된 순수성) 그
  자체로는 partials 를 registry 로 만들 수 없었다. partials 가 효용을 발생시키는
  지점 = registry 영속화. Phase 5 e2e (intake → planner → worker → partials →
  registry) 의 디스크 측 한 단을 닫음.
- **어떻게**: builder 의 순수성 유지 — 로딩·쓰기는 io 모듈에만. `load_partials`
  는 `Path.glob` 의 OS 의존적 순서를 그대로 넘기지 않고 parsed `task_id` asc 로
  정렬 (builder docstring 의 caller-ordering 계약 충족). 영속화는 atomic
  (tmp → fsync → rename), `project_manager._write_manifest` 와 동일 정책. CLI 는
  precondition (`source_collecting`) 검증 후 thin orchestration 호출. 상태 전이는
  completeness report 와 함께 처리할 Phase 5 완료 단계로 미룸.
- **결과**: 테스트 184 → 204 (io 15 + CLI 5). 전부 통과.
- **연관**: Phase 5, docs/13_IMPLEMENTATION_ROADMAP.md:42. 다음 단계 =
  SourceCompletenessReport 모델 + checker (Phase 5 완료, MINOR → C10 codex 리뷰).

## 2026-05-23 v0.5.4 — 외부 코드 리뷰 5차 반영 (SourceRegistryBuilder fail-fast 강화)

- **무엇을**: v0.5.3 (SourceRegistryBuilder) 의 codex 1차 외부 리뷰 결과
  Critical 0 / High 2 / Medium 3 / Low 2 / Nit 1 을 한 PATCH 로 흡수.
- **왜**: fail-fast 빌더의 두 가지 식별자 무결성 갭 — (1) input_item_id=None
  이 충돌 검사를 우회하여 idempotency 가드를 약화시키는 분기, (2) 식별자
  비교가 byte-exact 만이라 ` s1` / `s1 ` / NFD 같은 의심 변이가 정상으로
  통과되는 분기 — 가 production path 의 무결성 사고를 은폐할 수 있다는
  codex 의 지적이 정합. fail-fast 의 기조와 일치하는 방향으로 갭을 메운다.
- **어떻게**:
  - `strict_input_item_id: bool = True` 키워드 추가 (default strict, raise
    on None). 도메인 재사용을 위해 lenient 모드는 보존 — 현실 production
    경로는 strict 만 사용.
  - `_validate_identifier` 헬퍼 — case-sensitive contract 를 docstring 에
    명문화하고, NFC 정규화 결과와 다르거나 strip 결과와 다른 식별자는
    raise. 정규화 후 매칭이 아니라 의심 변이 자체를 reject (`ABC` ↔ `abc`
    같은 정상 case 차이를 충돌로 오인하지 않으면서 ingest 단의 직렬화 사고
    는 차단).
  - 모든 raise 메시지에 `action: ...` 형식 operator next-step hint 추가.
    LLM-AP-003 참조는 유지하되, alert fatigue 방지 차원에서 "어디를
    inspect 하고 어디를 수정할지" 의 첫 단계를 명시.
  - 테스트: 19 → 36 케이스. `InputItemIdNoneStrictModeTests` (4),
    `IdentifierNormalizationContractTests` (10),
    `CollisionAlwaysRaisesSentinelTests` (3) 신설. 미래 dedupe 모드 도입
    시 sentinel 이 깨지고 docstring 머지 정책과 같이 갱신해야 함을 마킹.
- **결과**:
  - `python -m unittest discover -s tests` : 184/184 (운영 148 + builder
    36). v0.5.3 의 167 에서 +17.
  - `python -m py_compile orchestrator/source_registry_builder.py
    tests/test_source_registry_builder.py` 통과.
  - CLAUDE.md C10.3 에 따라 본 PATCH 자체는 codex 재리뷰 면제 (외부 리뷰
    흡수 PATCH).
  - False positive 흡수 안 함 항목 없음 — 1차 리뷰의 모든 지적을 정합으로
    판단.
- **연관**: LLM-AP-003 (echo identifier production breach 신호 — builder
  의 source_id 충돌 invariant 의 근거). v0.5.3 (대상). v0.5.2 (v0.5.0
  SourceCollectorWorker 의 1차 리뷰 흡수 — 같은 시리즈의 직전 흡수 PATCH).

---

## 2026-05-19 v0.1.0 — Phase 0 + Phase 1 착수

- **무엇을**: 빈 저장소를 받아 v2 확정서의 Phase 0(초기화)과 Phase 1(Command Center MVP)을 한 번에 셋업.
- **왜**: 영상 한 편을 빨리 만드는 것이 아니라 **재현 가능한 시스템**을 만드는 프로젝트이므로, 초기에 거버넌스·스키마·Antipattern 카탈로그 골격이 반드시 함께 있어야 후속 Phase에서 무너지지 않는다.
- **어떻게**:
  - `doroper98/agents_reviewer`의 3-Tier 거버넌스 컨벤션을 채택.
  - Tier 1 4종 + Tier 3 3종 + Tier 2 19종 동시 생성.
  - Pydantic v2를 도메인 데이터 SSOT로 고정 (`schemas/models.py`).
  - Textual + Rich로 단일 TUI Command Center를 구성, Worker는 `asyncio.create_subprocess_exec`로 띄우고 stdout을 Log Router가 각 Slot 패널로 라우팅.
  - 사용자가 직접 제공한 TTS 안티패턴 50+ 항목을 `TTS-AP-N` 포맷으로 초회 기록.
- **결과**:
  - `run_pipeline.bat`로 Command Center 진입, 4개 dummy worker가 subprocess로 동시 실행되고 각 Slot 패널에 로그가 흐르는 것을 확인.
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - Phase 1 smoke test 중 PIPELINE-AP-006 발견 즉시 수정: worker slot finalize 시 terminal 상태를 잔존시키면 `depends_on` 후속 task 가 영원히 queued 로 남는 문제. fix → `_finalize_slot`에서 즉시 idle 환원. 카탈로그 append.
- **연관**: PIPELINE-AP-006

## 2026-05-19 v0.1.1 — 호스팅 / 인증 / default branch 통합

- **무엇을**: branches.html 의 즐겨찾기 URL 을 위해 Vercel 호스팅 경로 확정, GitHub PAT 입력 UI 추가, default branch 가 `main` 으로 통합된 것을 로컬에도 반영.
- **왜**: 저장소가 **Private** 이라 GitHub Pages 무료 플랜이 막혀 있고, `htmlpreview.github.io` 도 raw 접근이 안 됨 → Vercel 만이 무료로 Private 저장소 정적 호스팅을 지원. 그리고 같은 이유로 페이지 안에서 GitHub API 를 호출하려면 사용자 토큰이 필요함.
- **어떻게**:
  - `vercel.json` 추가: `outputDirectory: docs`, `/` → `/branches.html` rewrite, cleanUrls.
  - `branches.html`: token 입력 다이얼로그 + `localStorage` 저장 + `Authorization: Bearer` 헤더 부착. raw.githubusercontent.com 대신 contents API 사용.
  - GitHub UI 가 `claude/osint-video-system-IaGd0 → main` rename 안내 → 로컬도 `git branch -m`, `git fetch`, `git branch -u`, `git remote set-head` 으로 정리.
  - VERSION 0.1.0 → 0.1.1, 30개 마크다운/HTML 의 `last_synced_with` 일괄 갱신.
- **결과**:
  - vercel.json 1개 커밋만으로 Vercel 가져오기 후 즉시 배포 가능.
  - branches.html 이 Private 저장소에서도 정상 동작.
- **연관**: 없음 (호스팅·운영 영역 PATCH)

## 2026-05-19 v0.1.2 — Vercel 루트 404 수정

- **무엇을**: Vercel 첫 배포 후 루트 URL (`/`) 이 `404: NOT_FOUND` 를 띄우던 문제 수정. `docs/index.html` 정적 파일 추가, `vercel.json` 의 `rewrites` 룰 제거.
- **왜**: `outputDirectory: "docs"` + `rewrites: [{ source: "/", destination: "/branches.html" }]` 조합이 Vercel 의 정적 호스팅 모드에서 안정적으로 매칭되지 않음. 실측 시 deployment URL 루트가 404. `/branches.html` 직접 접근은 정상.
- **어떻게**:
  - `docs/index.html` 신설: meta-refresh + `window.location.replace('/branches.html')` 양쪽으로 즉시 리다이렉트.
  - `vercel.json` 의 `rewrites` 블록 삭제. cleanUrls / 캐시 헤더는 유지.
  - VERSION 0.1.1 → 0.1.2, 30 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 푸시 후 Vercel 자동 재배포 → 루트 URL 이 `branches.html` 로 정상 진입.
  - 안정 도메인 (`osint-generator.vercel.app`) 도 동일하게 동작.
- **연관**: 없음 (호스팅 hotfix)

## 2026-05-19 v0.1.3 — branches.html 진짜 git graph 화 + 세션 인계 문서

- **무엇을**: `docs/branches.html` 의 flat list 렌더링을 `@gitgraph/js` 기반 SVG 그래프로 교체. `HANDOFF.md` (Tier 1) 신설.
- **왜**:
  - 사용자가 GitExtensions/Sourcetree 스타일의 "진짜 가지" 시각화를 원함. 현재는 모든 브랜치가 같은 SHA 를 가리켜서 가지 효과가 안 보이지만, Phase 2 부터 브랜치가 갈라지면 즉시 예쁜 그래프가 나오도록 프레임워크를 미리 깔아둠.
  - 세션이 멈췄을 때 다음 AI 가 빠르게 컨텍스트를 잡기 위한 인계 문서가 필요했음. `CLAUDE.md` 는 규칙, `GOAL.md` 는 목표, `DEVLOG.md` 는 과거 — "지금 어디까지 와 있고 다음에 뭘 하면 되는지" 를 한 페이지에 압축한 문서가 부재.
- **어떻게**:
  - `branches.html`: `@gitgraph/js` CDN 추가, `buildCommitGraph()` 가 모든 브랜치 commit 을 `Promise.all` 로 병렬 fetch → SHA 로 dedup → `commit.parents` 필드 보존 → 시간순 정렬 → `gitgraph.import(commits)` 호출. 다크 테마 / 폰트 커스텀 (Metro template extend).
  - 사이드 패널: 등록되지 않은 브랜치는 한글 경고 카드로 자동 노출. PR 배지 통합.
  - `HANDOFF.md` (Tier 1) 신설: 다음 세션의 0–6 절. 작업 시작 체크리스트, Phase 2 DoD, 자주 까먹는 규칙 reminder.
  - VERSION 0.1.2 → 0.1.3, 31 개 마크다운 (HANDOFF.md 포함) `last_synced_with` 일괄 갱신.
- **결과**:
  - 사용자 시각 확인 시 v0.1.3 헤더 + 단일 라인 그래프 (브랜치 두 개가 동일 SHA 라서 line 1 개가 정상) + 사이드 패널의 main 카드 노출.
  - Phase 2 시작 후 첫 분기점부터 자동으로 갈라지는 그래프가 그려질 것 (검증 예정).
- **연관**: 없음 (UX 개선 + 문서 추가)

## 2026-05-19 v0.1.4 — 분기 그래프 검증 + 한글 commit 라벨 + main 라벨 우선순위

- **무엇을**:
  1. `test/graph-demo` 임시 브랜치를 `d0c8771` 에서 분기시켜 그래프 분기 시각화를 사용자 측에서 검증.
  2. 영어로 작성된 과거 커밋의 첫 줄을 한글로 보여주는 `COMMIT_DESCRIPTIONS` SHA 맵을 `branches.html` 에 추가.
  3. 같은 SHA 에 여러 브랜치가 있을 때 라벨 우선순위 (`BRANCH_PRIORITY`) 도입. `main` 이 항상 먼저.
- **왜**:
  - **검증**: gitgraph.js 통합 후 실제 분기가 나타나는지 사용자 측에서 시각 확인이 필요했음. → 사용자 스크린샷에서 `d0c8771` → 두 갈래로 정확히 분기되는 그림 확인.
  - **한글 라벨**: 사용자가 버전 중심으로 소통하기로 했지만 commit 첫 줄은 영어로 작성되어 있어 페이지에서 가독성 떨어짐. 과거 commit 을 rebase 로 고치는 것은 destructive 이므로 디스플레이 레벨에서 override.
  - **main 우선**: `c359bd8` 처럼 두 브랜치가 동일 SHA 를 가리킬 때 `claude/resume-session-YLOYE` 가 알파벳 순으로 먼저 와서 main 라벨이 가려지는 시각 버그.
- **어떻게**:
  - `git checkout -b test/graph-demo d0c8771` → `docs/_GRAPH_DEMO.md` 추가 → `v0.1.2: graph divergence demo` commit → `git push -u origin test/graph-demo` → `git checkout main`.
  - `branches.html` 의 `<script>` 상단에 `COMMIT_DESCRIPTIONS` (SHA prefix 7자 → 한글 텍스트) 와 `BRANCH_PRIORITY` (정규식 배열) + `branchPriority()` + `sortBranchRefs()` 추가.
  - `renderGraph()` 의 `commits.map` 에서 한글 override + ref 정렬 적용. `onClick` 핸들러도 `sortBranchRefs` 사용.
  - VERSION 0.1.3 → 0.1.4, 31 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 사용자 스크린샷 확인: `bb530d2 → 083a764 → d0c8771` 까지 단일 라인, `d0c8771` 에서 보라색 곡선이 분기되어 `c359bd8 (main)` 과 `0159299 (test/graph-demo)` 로 갈라짐. ✓
  - 한글 override / main 라벨 우선순위는 사용자 다음 새로고침에서 검증 예정.
- **연관**: 없음 (검증 + UX 개선)

## 2026-05-19 v0.1.5 — test/graph-demo 정리

- **무엇을**: 검증용 임시 브랜치 `test/graph-demo` 삭제, 관련 dead code 제거.
- **왜**: v0.1.3 그래프 분기 시각화 검증이 v0.1.4 사용자 스크린샷으로 완료됨. 임시 브랜치 / 더미 commit / 더미 파일을 더 이상 유지할 이유가 없음. 카탈로그를 깨끗이 유지하는 것이 다음 세션의 인지 부담을 줄임.
- **어떻게**:
  - 컨테이너 측 `git push origin --delete test/graph-demo` 가 HTTP 403 (Claude Code 인프라가 main / claude/* 외의 브랜치 삭제 차단) → 사용자가 GitHub 웹 UI 에서 직접 삭제.
  - `git fetch --prune origin` 으로 로컬 원격 추적 ref 정리.
  - `branches.html`: `BRANCH_DESCRIPTIONS["test/graph-demo"]` 제거, `COMMIT_DESCRIPTIONS["0159299"]` 제거.
  - VERSION 0.1.4 → 0.1.5, 31 개 마크다운 `last_synced_with` 일괄 갱신.
- **결과**:
  - 원격 브랜치 목록: `main`, `claude/resume-session-YLOYE` 두 개로 복귀.
  - `branches.html` 새로고침 시 단일 라인 그래프 (v0.1.3 시점과 동일 모양) + 현재 commit 5 개 (v0.1.0~v0.1.5).
- **연관**: 없음 (정리 PATCH)

## 2026-05-19 v0.2.0 — Phase 2: Project Manager / State Machine

- **무엇을**: 프로젝트의 라이프사이클을 관리하는 Project Manager 와 State Machine 을 정식 구현. `new-project / resume / transition` CLI 명령이 동작하고, `project_manifest.json` 이 디스크에 영속화되며, 모든 상태 전이는 검증을 거치고 `state_history` 에 append-only 로 기록된다.
- **왜**: Phase 1 까지는 더미 워커가 task_queue.json 만으로 돌아갔으나, Phase 3+ 의 Worker 들이 자기 산출물을 어디로 떨어뜨릴지·언제 다음 단계로 전진할지 결정하려면 "프로젝트가 지금 어떤 상태인가" 가 단일 출처로 박혀 있어야 한다. 임의 점프를 막아야 `created → render_final` 같은 사고를 차단할 수 있다.
- **어떻게**:
  - `schemas/models.py` 에 `StateTransition` 모델과 `ProjectManifest.state_history` (default `[]`) 추가. schema_version 은 1 유지 — 신규 optional 필드는 호환 방향 (C3).
  - `orchestrator/state_machine.py` 신설: docs/02 §4 의 24개 상태를 `LINEAR_SEQUENCE` 에 박고, `allowed_next_states` 가 (다음 선형 상태 + `archived`) 집합을 반환. `archived` 는 어디서든 종료 허용하지만 archived 에서 추가 전이 불가. `validate_transition` 이 실패 시 한글 메시지로 ValueError. Pydantic `use_enum_values=True` 때문에 manifest 로드 시 enum 이 str 로 들어오는 점을 `_coerce` 헬퍼로 흡수.
  - `orchestrator/project_manager.py` 신설: `MANIFEST_FILENAME` 상수, `_SLUG_RE` 로 project_id 검증, `new_project / resume_project / transition_state` 공개 API. 모든 디스크 쓰기는 `_write_manifest` 한 군데로 단일화 — `updated_at` 자동 갱신.
  - `orchestrator/main.py` 의 `new-project` placeholder 를 실 구현으로 교체. `resume`, `transition` 서브커맨드 신설. category / state 는 enum choices 로 argparse 가 자동 검증.
  - `orchestrator/command_center.py` 가 raw json 파싱 대신 `project_manager.load_manifest` 를 호출하도록 정리. manifest 가 손상되면 created 로 fallback (TUI 진입 자체는 막지 않음).
  - 스모크 테스트 (demo2): 정상 new-project, 중복 new-project (FileExistsError), 잘못된 project_id (ValueError), resume 정상, resume 미존재 (FileNotFoundError, 디렉토리도 안 만듦), 정상 전이 2회, 불법 점프 (created→render_debug 거부), 동일 상태 전이 거부, archived 종료, archived 에서 추가 전이 거부 — 모두 의도대로 동작. state_history 3개 엔트리 직렬화 확인.
  - 작업 중 `resume_project` 가 `_ensure_project_layout` 을 먼저 호출해서 미존재 프로젝트에도 빈 폴더가 생기는 버그 발견 → manifest 검증을 먼저 수행하도록 순서 교체.
  - VERSION 0.1.5 → 0.2.0 (MINOR · Phase 완료), 31 개 마크다운/HTML `last_synced_with` 일괄 갱신.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - HANDOFF DoD 6 항목 모두 충족: new-project 시 manifest 가 `state: "created"` 로 생성, resume 으로 마지막 상태에서 이어짐, 불법 전이는 ValueError + 한글 메시지, py_compile 통과, last_synced_with 갱신, CHANGELOG/DEVLOG 엔트리 추가.
  - Phase 3 (Dynamic Intake Page) 가 `intake_planning → intake_pending_user → source_collecting` 흐름을 그대로 호출하면 됨.
- **연관**: 없음 (새 Antipattern 없음. 잘못된 전이 시도는 schema_machine 이 ValueError 로 차단함 — 카탈로그에 등록할 만한 미발견 결함이 아니라 사전 차단된 케이스이므로 SCHEMA-AP 등록 보류)

## 2026-05-19 v0.2.1 — Subscription LLM Bridge 패턴 정립 (문서 PATCH)

- **무엇을**: 본 시스템이 LLM API 키 (`ANTHROPIC_API_KEY` 등) 와 공식 SDK (`anthropic`, `openai` 등) 를 사용하지 않고, 사용자가 이미 구독 중인 `claude` / `codex` CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정을 정식 문서화. 코드 변경 없음.
- **왜**:
  - 사용자가 강하게 어필하고 싶다고 명시. 비용 예측성 / rate-limit 여유 / 최신 모델 우선 반영 / 결제 중인 자원 활용도 극대화 / API 키 관리 부담 제거.
  - "Agent 가 LLM API 직접 호출" 전제로 docs/03 이 작성되어 있었던 것을 정정해야 Phase 3 이후 코드가 잘못된 방향으로 가지 않음.
  - 한 번 의사결정 + 본 세션 안에서 짧은 시행착오: 처음에 "프롬프트 출력 → 사용자 복붙" 패턴으로 해석했으나 사용자가 즉시 정정 — "에이전트가 CLI 에서 JSON 응답을 만들어 낼 수 있다, 왜 복붙해야 하나" — 정확한 의도는 **구독 인증된 CLI subprocess** 였음. 이 정정을 DEVLOG 에도 남겨 둠.
- **어떻게**:
  - `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설 (9개 절): 위상·핵심원칙(Hard NO/YES)·rationale·BaseLLMWorker 설계 (`llm_backend`, `llm_mode`)·CLI 인터페이스 가정·추적성 (`llm_calls/{call_id}.json`)·에러 모드·향후 확장·관련 안티패턴.
  - `docs/03_AGENT_ARCHITECTURE.md` 의 §4 베이스워커 안내문에 "LLM 호출 Worker 는 BaseLLMWorker 상속 필수" 박스 추가, §4.5 신설 (BaseLLMWorker 계약 요약 + 호출 모드 표 + 백엔드 선택 가이드).
  - `CLAUDE.md` C6 안티패턴 카테고리 목록에 `LLM-AP-N` 추가.
  - `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설, `docs/ANTIPATTERNS/README.md` 인덱스 행 추가.
  - 거버넌스 결정: GOAL.md G4 본문은 건드리지 않음. C5.4 에 따르면 G4 변경은 MAJOR 사유인데 본 변경은 PATCH 로 흡수하기 위함. ADDENDUM_04 자체에 "G4 와 동등한 강제력으로 운용" 을 명시해 어필 강도는 유지하고, v1.0.0 시점에 G4 #13 으로 정식 흡수 예정.
  - VERSION 0.2.0 → 0.2.1, 31 개 마크다운/HTML `last_synced_with` 일괄 갱신.
- **결과**:
  - 코드 변경 없음 → py_compile 영향 없음.
  - Phase 3 시작 시 `BaseLLMWorker` 구현 + IntakePlannerWorker 가 본 패턴을 그대로 채택. ADDENDUM_04 §4 의 시그니처를 코드로 옮기면 됨.
  - 다음 세션은 v0.2.2 (BaseLLMWorker 코드 도입) 또는 v0.3.0 (Phase 3 + BaseLLMWorker 동시) 중 사용자가 선택.
- **연관**: 없음 (안티패턴 카테고리 신설 1건. LLM-AP 항목은 Phase 3 첫 실 호출부터 누적 예정.)

## 2026-05-20 v0.2.2 — BaseLLMWorker 코드 도입 + LLM-AP-001 발견

- **무엇을**: ADDENDUM_04 §4 의 BaseLLMWorker 인터페이스 명세를 코드로 옮김. `workers/base_llm_worker.py` 신설, `schemas/models.py` 에 `LLMCallRecord` 추가, `workers/dummy_llm_worker.py` 로 4 케이스 smoke test. 실 `claude` CLI 호출 케이스에서 응답 wrapper 발견 → LLM-AP-001 등록 (구조적 조치는 v0.2.3 patch).
- **왜**:
  - v0.2.1 에서 패턴은 문서화했지만 코드가 없으면 Phase 3 의 IntakePlannerWorker 가 base 클래스를 직접 짜야 함. 작은 단위 (C8.2) 원칙에 따라 인프라 먼저 박고 Phase 3 진입.
  - 사용자가 "옵션 A (v0.2.2 — BaseLLMWorker 코드 도입)" 명시적으로 선택.
- **어떻게**:
  - `LLMCallRecord` Pydantic 모델: `call_id`, `task_id`, `worker`, `backend`, `mode`, `system_prompt_hash`, `user_prompt_path`, `raw_response_path`, `parsed_status`, `started_at/completed_at`, `exit_code`, `retry_index`, `error_message`. schema_version 1 유지 (신규 optional 모델 추가는 호환).
  - `BaseLLMWorker(BaseWorker)`: 클래스 변수 (`llm_backend`, `llm_mode`, `system_prompt`, `response_model`, `invoke_timeout_sec=600`), 추상 (`build_user_prompt`, `output_path`), `run` 오버라이드로 전체 흐름 흡수. `_invoke_llm` 가 `CLI_INVOCATION` 매핑 (`(backend, mode) → list[str]`) 으로 subprocess 호출하고 `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 변환. `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회.
  - 모든 호출은 3 파일로 영속화: `{call_id}.prompt.txt` (system+user 합쳐서 sha256 해시 함께), `{call_id}.raw.txt` (subprocess stdout 그대로), `{call_id}.json` (LLMCallRecord). `TaskResult.outputs` 에 LLMCallRecord 경로 포함 → task ↔ LLM 호출 양방향 추적.
  - `DummyLLMWorker` + `DummyLLMResponse` 로 demo3 프로젝트에 task_queue 만들고 4 케이스 smoke test: (1) 정상 stub → completed/parsed_status=ok, (2) `"not a json"` → failed/validation_failed, (3) `{"unknown_field":42}` → failed/validation_failed (extra_forbidden), (4) `OSINT_LLM_STUB` 없이 실 `/opt/node22/bin/claude` 호출 → JSON 응답은 받았으나 wrapper 때문에 validation_failed.
  - 4번째 케이스에서 wrapper 구조 확인: `{"type":"result","subtype":"success","result":"<actual_text>","session_id":...,"duration_ms":...,"usage":{...},"uuid":"..."}` — 도메인 응답은 `result` 필드의 string. 이 발견을 LLM-AP-001 로 정식 등록. 구조적 조치는 v0.2.3 patch 에서 `BaseLLMWorker._invoke_llm` 내부에 backend 별 wrapper unwrap 단계 추가 예정.
  - VERSION 0.2.1 → 0.2.2 (MINOR — C5.4 "새 Worker 추가" 트리거). 31 개 마크다운 `last_synced_with` 일괄 갱신.
  - ADDENDUM_04 §4 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 로 구체화.
- **결과**:
  - py_compile 통과. Pydantic 검증 + 추적성 파일 영속화 모두 의도대로 동작.
  - Phase 3 의 `IntakePlannerWorker` 는 `BaseLLMWorker` 를 그대로 상속하면 됨 — `system_prompt`, `response_model=IntakePlan`, `build_user_prompt(args, task)`, `output_path` 만 구현.
  - 다음 patch (v0.2.3) 는 LLM-AP-001 fix: wrapper unwrap 로직 + 회귀 테스트 fixture.
- **연관**: LLM-AP-001 (active, v0.2.3 대기)

---

## 2026-05-20 v0.2.3 — LLM-AP-001 구조적 조치 (wrapper unwrap)

- **무엇을**: v0.2.2 에서 발견한 LLM-AP-001 (claude CLI 응답 wrapper 로 인한 Pydantic `extra_forbidden` reject) 을 구조적으로 해결. `BaseLLMWorker` 가 backend 별 wrapper 를 벗긴 뒤 검증하도록 변경. 회귀 테스트 `tests/test_base_llm_worker.py` 신설.
- **왜**:
  - 실 `claude` CLI 호출이 stub 없이 정상 동작하려면 wrapper unwrap 이 필수. Phase 3 의 IntakePlannerWorker 가 stub 없이 돌아가야 의미가 있음.
  - 회귀 테스트가 없으면 같은 종류의 버그 (코덱스, 향후 CLI 갱신) 가 재발해도 알아채지 못함. C6.4 "구조적 조치" 요구.
- **어떻게**:
  - `workers/base_llm_worker.py` 에 모듈 레벨 헬퍼 3 종: `_unwrap_claude_response` (wrapper `{type:result, subtype:success}` 에서 `result` 필드 추출, `is_error=True` 면 `LLMSubprocessError`), `_unwrap_codex_response` (v0.2.3 시점 미검증 → pass-through), `_extract_json_block` (markdown code fence 제거).
  - `BaseLLMWorker._unwrap_response(raw)` 가 `self.llm_backend` 로 dispatch. `run()` 의 `model_validate_json` 직전에 호출. `LLMSubprocessError` 도 잡아서 `parsed_status="subprocess_error"` 로 기록.
  - `raw.txt` 는 unwrap 전 원본 그대로 보존 → 디버깅 추적성 유지.
  - `tests/__init__.py` + `tests/test_base_llm_worker.py` 신설. 13 케이스: extract_json_block 5 + claude unwrap 7 + codex pass-through 1. 모두 `python -m unittest tests.test_base_llm_worker` 로 통과.
  - LLM_ANTIPATTERNS.md 의 LLM-AP-001 status `active` → `resolved`, regression_test pending → 실제 파일 경로로 갱신. 본문 (증상/원인) 은 수정하지 않음 (C6 append-only 준수, 상태 라이프사이클만 진행).
  - VERSION 0.2.2 → 0.2.3 (PATCH — C5.4 "버그 수정" 트리거).
- **결과**:
  - py_compile 통과, import smoke 통과, 13 단위 테스트 통과.
  - 다음 단계: Phase 3 IntakePlannerWorker 착수 가능. 실 `claude` CLI 호출 시에도 도메인 JSON 검증이 정상 동작할 것으로 기대 (실 호출 검증은 Phase 3 smoke test 에서).
  - codex CLI wrapper 검증은 별도 작업 (LLM-AP-002 후보) 으로 분리.
- **연관**: LLM-AP-001 (resolved), ADDENDUM_04 §5

---

## 2026-05-20 v0.2.4 — codex JSONL stream 처리 + LLM-AP-002 발견 즉시 해결

- **무엇을**: v0.2.3 시점에 미검증 pass-through 였던 codex CLI 의 wrapper 를 사용자 머신 (codex-cli 0.130.0, Windows cmd) 한 줄 호출 캡쳐로 검증. 단일 JSON wrapper 가 아니라 JSONL 이벤트 스트림 패턴이라는 사실을 발견 → LLM-AP-002 등록 + 즉시 fix.
- **왜**:
  - v0.2.3 시점의 codex pass-through 는 "실 호출 시 검증 실패" 라는 알려진 risk 였음. Phase 3 진입 전에 해소되어야 IntakePlannerWorker 가 codex backend 도 안전히 쓸 수 있음.
  - 사용자가 codex CLI 보유 확인 → 즉석 검증 가능해짐.
- **어떻게**:
  - 검증 절차: `codex exec --json --skip-git-repo-check "<프롬프트>"` 를 사용자 머신에서 던져 stdout 캡쳐. 4 줄 JSONL: `thread.started` / `turn.started` / `item.completed`(agent_message) / `turn.completed`. 도메인 응답은 `item.completed` 의 `item.type=="agent_message"` 의 `text` 필드.
  - `_unwrap_codex_response` 실 구현: 모든 줄을 순회하며 codex 이벤트 (`thread.*`, `turn.*`, `item.completed`) 가 한 번이라도 보이면 codex stream 으로 인정. 마지막 agent_message 의 text 를 채택. markdown code fence 가 끼면 `_extract_json_block` 으로 한 번 더 벗김. codex stream 인데 agent_message 가 하나도 없으면 `LLMSubprocessError`. codex stream 패턴이 전혀 안 보이면 pass-through (단일 JSON / stub mode 보호).
  - 의도적 호환성: tool_call / reasoning 등 미지 item type 은 무시. codex 가 새 이벤트 타입을 추가해도 깨지지 않음. 그 대신 fixture 기반 회귀 테스트가 포맷 변경을 빠르게 감지.
  - `CLI_INVOCATION` codex 매핑 보강: `--skip-git-repo-check` (project_dir 이 git repo 아닐 수 있음), `--color never` (ANSI 코드 안전장치). agent 모드는 `--cd {project_dir}` 유지.
  - `tests/test_base_llm_worker.py::TestUnwrapCodexResponse` 8 케이스 추가 (실 캡쳐 / fence / 다중 message / unknown item / no message / 단일 JSON / non-JSONL / 빈 입력). 단위 테스트 13 → 20.
  - LLM_ANTIPATTERNS.md 에 LLM-AP-002 신규 등록 (status=resolved). LLM-AP-001 본문은 수정하지 않고 별개 항목으로 분리 (claude / codex 가 다른 패턴이라는 사실 자체가 카탈로그 가치).
  - VERSION 0.2.3 → 0.2.4 (PATCH — C5.4 "버그 수정/비기능 개선").
- **결과**:
  - py_compile 통과, import smoke 통과, 20/20 단위 테스트 통과.
  - codex backend 가 실제 호출 가능 상태로 진입. Phase 3 의 IntakePlannerWorker 가 claude/codex 양쪽 모두 안전히 사용 가능.
  - Windows cmd 환경에서 subprocess 매핑이 잘 도는지는 Phase 3 첫 실 호출에서 추가 검증 (인용부호 / shell=False 동작 확인).
- **연관**: LLM-AP-002 (resolved), LLM-AP-001 (자매 항목 — claude wrapper), ADDENDUM_04 §5

---

## 2026-05-20 v0.2.5 — 외부 코드 리뷰 1차 반영 (BaseLLMWorker 견고성 강화 + LLM-AP-003)

- **무엇을**: 사용자가 codex CLI 로 v0.2.2~v0.2.4 변경에 대해 코드 리뷰를 돌린 결과 (Critical 0 / High 6 / Medium 3 / Low+Nit 모두 OK) 의 High/Medium 항목을 한 PATCH 로 일괄 반영. 신규 LLM-AP-003 (agent 모드 prompt injection) 등록 + opt-in 가드 도입.
- **왜**:
  - 외부 리뷰는 BaseWorker 가 Phase 3 의 첫 도메인 worker (IntakePlannerWorker) 의 베이스로 들어가기 전 마지막 견고화 기회. 추적성·상태 분류·output 컨테인먼트는 한 번 합의된 뒤 깨면 회귀 비용이 크므로 지금 정리.
  - Critical 이 없었다는 사실 자체가 핵심 로직 (wrapper unwrap, subprocess 호출, Pydantic 검증) 의 방향성이 맞다는 확인. 다만 6 개 High 모두 정당해서 방어할 항목 없음.
- **어떻게**:
  - **(H1+H2)** `LLMSubprocessError` 에 `stdout`/`stderr`/`exit_code` 첨부. `_invoke_llm` 의 비0 종료 / `TimeoutExpired` / `FileNotFoundError` 모두 부분 출력과 exit_code 를 보존하도록 변경. `run()` 의 except 가 `e.stdout` 을 `raw_text` 로 복원해 `raw.txt` 영속화에 사용.
  - **(H3)** `model_validate_json(raw)` 한 줄을 `json.loads(raw)` → `model_validate(parsed_obj)` 2 단계로 분리. `JSONDecodeError` → `parsed_status="parse_failed"`, `ValidationError` → `validation_failed`. 4 `parsed_status` 가 의미적으로 구분됨.
  - **(H4)** `run()` 의 LLM 호출 + 검증 + output 저장을 `try` 안에, LLMCallRecord 영속화를 `finally` 안에 배치. 어떤 예외 경로에서도 record/prompt/raw 3 파일이 항상 남음. output write 실패 시 `parsed_status` 는 `ok` 유지 (LLM 응답은 정상이었음) 하되 `error_message` 에 명시하고 task 는 FAILED.
  - **(H5)** `_validate_output_path(args, task, outp)` 헬퍼 추가. project_dir 밖이면 `ValueError`. `task.output_refs` 가 비어있지 않으면 outp 의 상대경로가 그중 하나와 일치해야 함 (Windows `\` 와 POSIX `/` 차이 흡수). CLAUDE.md C4 "writes only own output_refs" 의 코드 단 가드.
  - **(H6 / LLM-AP-003)** `BaseLLMWorker.allow_agent_mode: ClassVar[bool] = False` 도입. `run()` 시작 직후 `llm_mode=="agent" and not allow_agent_mode` 면 즉시 `TaskResult(FAILED)` 반환 — LLM 호출 자체가 일어나지 않으므로 `llm_calls/` 디렉토리도 생성되지 않음. agent 모드 사용 worker 는 명시적으로 `allow_agent_mode = True` 선언 필요. LLM-AP-003 본문에 옵션 (1)~(3) 단계별 보강 (외부 자료 격리, CLI sandbox 옵션) 을 향후 Phase 3+ 후속으로 기록.
  - **(M1)** `_unwrap_claude_response` 의 subtype 검증 엄격화. `type=="result"` 면 `subtype=="success"` 강제, 아니면 `LLMSubprocessError`. 이전엔 `subtype != "success"` 도 pass-through 였어서 `validation_failed` 로 흡수돼 원인 추적 어려웠음.
  - **(M2)** `LLMCallRecord.exit_code: int = 0` → `Optional[int] = None`. 이전엔 CLI 호출 실패 (FileNotFoundError) 케이스도 `exit_code=0` 으로 남아 "정상 실행 후 실패" 와 구분 안 됐음. None = "미실행 또는 timeout" sentinel.
  - **(M3)** `tests/test_base_llm_worker_run.py` 신설. monkeypatch + stub mode 로 `_invoke_llm` 을 가짜 함수로 교체하거나 `OSINT_LLM_STUB` 으로 fake stdout 주입. 4 `parsed_status` 모두 도달성 + agent gate + output 컨테인먼트 (project_dir 밖 / output_refs 불일치) 총 8 케이스.
  - 단위 테스트 총 20 → 30. 모두 통과.
  - VERSION 0.2.4 → 0.2.5 (PATCH — C5.4 "버그 수정/비기능 개선"). schema_version 은 1 유지 (`exit_code` Optional 화는 호환 변경).
- **결과**:
  - py_compile 통과, import smoke 통과, 30/30 단위 테스트 통과.
  - BaseLLMWorker 의 추적성·상태 분류·output 컨테인먼트가 외부 리뷰가 요구한 수준에 도달. Phase 3 의 IntakePlannerWorker 가 안전하게 상속 가능.
  - 다음 후보: (a) Phase 3 IntakePlannerWorker 착수, (b) agent 모드 본격 sandbox (CLI `--sandbox` 매핑 + scratch dir) — LLM-AP-003 의 후속 단계.
- **연관**: LLM-AP-003 (resolved-partial), LLM-AP-001/002 (자매 항목), 외부 codex 리뷰 결과, ADDENDUM_04 §5/§7, CLAUDE.md C2/C4.

---

## 2026-05-20 v0.2.6 — codex review 절차 정형화 + 다음 세션 인계 정리

- **무엇을**: 외부 LLM (codex) 코드 리뷰를 일회성 실험에서 정식 거버넌스 절차로 격상. `CLAUDE.md C10` 신설, `docs/REVIEW_PROMPT.md` 운영 매뉴얼 신설, `HANDOFF.md` 를 v0.2.6 기준 + Phase 3 진입 준비로 전면 갱신. 코드/스키마/테스트 변경 없음.
- **왜**:
  - v0.2.5 의 외부 리뷰가 6 개 High 를 발견 — 자기 검증의 사각지대가 분명히 존재. 일회성으로 두면 재발. **MINOR/MAJOR/Phase 완료 직전 의무화** 로 강제력 부여.
  - 사용자가 매번 "어떤 프롬프트로 시켜야 하지?" / "어떻게 호출하지?" 를 묻지 않도록 운영 매뉴얼 분리. 변경 범위만 채워 재사용 가능한 영문 프롬프트 템플릿.
  - 다음 세션이 어떤 컨텍스트에서 시작할지 분명히 — Phase 3 의 IntakePlannerWorker 가 정식 다음 항목, BaseLLMWorker 인프라는 이미 외부 리뷰까지 거친 견고한 상태.
- **어떻게**:
  - **CLAUDE.md C10 신설** — 4 절 구조: C10.1 실행 의무 시점 표 (MINOR/MAJOR 필수, Phase 완료 필수, 새 Worker 권장, 단순 fix 면제), C10.2 절차 5 단계 요약, C10.3 자기 검증 면제 (본 절차 자체와 외부 리뷰 결과 흡수 PATCH 는 무한 루프 방지로 면제), C10.4 산출물 처리 (`review-prompt.txt`/`review-out.jsonl` 커밋 금지).
  - **`docs/REVIEW_PROMPT.md` 신설** (tier 2, ssot_for=codex-review-procedure) — 6 절 구조:
    1. 언제 실행하나 (표)
    2. 표준 영문 프롬프트 (재사용 템플릿 + 작성 가이드)
    3. 실행 명령어 (Windows cmd / macOS-Linux / .git/info/exclude)
    4. 결과 해석 (Critical/High/Medium/Low/Nit 처치표 + commit 컨벤션 + false positive 처리)
    5. 절차의 한계 (codex 가 ADDENDUM/AP 카탈로그 모름)
    6. 관련 문서
    프롬프트는 영문 고정 — codex 의 reasoning 일관성 + Windows 한글 코드페이지 이슈 회피.
  - **HANDOFF.md 전면 갱신**:
    - `last_synced_with: v1.1.0 → v0.2.6`, `depends_on` 에 `docs/REVIEW_PROMPT.md` 추가.
    - "1. 지금 어디까지 와 있나" 표에 v0.2.3 / v0.2.4 / v0.2.5 / v0.2.6 4 행 추가.
    - 알려진 antipattern 카탈로그 갱신 (LLM-AP-001/002/003 상태 명시).
    - "2. 다음 작업" 절을 v0.2.3/Phase 3 양자택일 → **Phase 3 (v0.3.0) IntakePlannerWorker 단독** 으로 교체. 도메인 모델 4 종, Worker 명세, 웹 페이지, CLI 확장, DoD 7 항목, 알려진 risk 4 종, Phase 4 예고 포함. 대안 절 (LLM-AP-003 후속 보안 강화 먼저) 도 명시.
    - "3. 작업 시작 전 체크리스트" 에 codex review 단계 + 30 단위 테스트 통과 확인 (`python -m unittest tests.test_base_llm_worker tests.test_base_llm_worker_run`) 추가.
    - "자주 까먹는 규칙" 에 6 개 항목 추가 — agent 모드 opt-in, codex review 의무, parsed_status 4 상태 의미, exit_code Optional 의미, output_path 컨테인먼트.
  - VERSION 0.2.5 → 0.2.6 (PATCH — C5.4 "문서 보강"). 코드 변경 없으므로 schema_version 영향 없음.
  - C10.3 self-exemption 의해 본 PATCH 자체에는 codex review 미실시.
- **결과**:
  - 다음 세션이 HANDOFF.md 의 §3 체크리스트만 따라가면 즉시 Phase 3 진입 가능.
  - codex review 가 일회성 실험에서 정식 거버넌스 절차로 격상. 같은 종류의 사각지대 (자기 검증 한계) 재발 위험 ↓.
  - 사용자가 매 리뷰 시점마다 절차 / 명령어 / 프롬프트 / 결과 처리를 새로 생각할 필요 없음.
- **연관**: CLAUDE.md C10, docs/REVIEW_PROMPT.md, HANDOFF.md.

---

## 2026-05-20 v0.2.7 — 평행 브랜치 흡수: SCHEMA-AP + TUI 라이브 reload + atomic write

- **무엇을**: 같은 출발점 (`v0.1.5` main) 에서 두 Claude Code 세션이 평행으로 Phase 2 를 구현한 것을 발견. 본 브랜치 (`n9ird` 계열) 가 정본이고, 평행 브랜치 `claude/start-after-handoff-Ij1TX` 의 차별점 3 가지만 본 PATCH 로 흡수.
- **왜**: 평행 브랜치는 양적·질적으로 본 브랜치가 훨씬 깊었지만 (BaseLLMWorker 등 +2,500 줄), Ij1TX 에 있는 다음 3 가지는 본 브랜치에 부재했고 모두 채택 가치가 있었다:
  1. **SCHEMA-AP 안티패턴 카탈로그**: 상태 머신을 우회한 임의 점프 / self-loop 라는 클래스의 안티패턴을 카탈로그화. Phase 3+ 에서 새로운 schema 위반이 발견됐을 때 들어갈 자리.
  2. **TUI 라이브 manifest reload**: 외부 프로세스가 `transition` 으로 state 를 바꿔도 본 브랜치의 TUI 는 stale state 를 보여줬다. 사용자는 "지금 어디까지 왔는가"라는 기본 질문에 답할 수 없게 된다. Phase 3+ 의 IntakePlannerWorker 가 `created → intake_planning → intake_pending_user` 로 전이시킬 때 즉시 시각화 필요.
  3. **Atomic write**: 본 브랜치의 `_write_manifest` 는 `path.write_text` 직접 호출 — 외부 reader (위 2번 reload) 가 half-written 상태를 잠깐도 볼 수 있는 race. TUI reload 를 도입하는 순간 이 race 가 실제로 발현될 수 있어 함께 차단.
- **어떻게**:
  - `orchestrator/project_manager.py:_write_manifest`: tmp 파일에 쓴 뒤 `Path.replace` 로 교체. POSIX rename / Windows `os.replace` 모두 atomic. tmp 파일 잔존 가능성 없음 (`replace` 가 unlink 까지 보장).
  - `orchestrator/tui_app.py`:
    - imports: `JSONDecodeError`, `pydantic.ValidationError`, `orchestrator.project_manager.load_manifest`, `schemas.models.ProjectState`.
    - `_tick_loop` 에 `_reload_manifest_state()` 호출 1 줄 추가.
    - 새 메서드 `_reload_manifest_state`: 매 tick 마다 `load_manifest` 호출, 실패 모드 3 분류 (`FileNotFoundError` → `unknown` / `JSONDecodeError|ValidationError` → `invalid` / 정상 → 변경 시 log). 동일 상태 진입 시에만 1 회 stderr 로그 (noise 억제). 모든 예외 swallow → tick loop 유지.
  - `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` 신설 + `SCHEMA-AP-001 — ProjectState 임의 점프 / self-loop 전이`. mitigation 칸은 본 브랜치의 API 이름 (`LINEAR_SEQUENCE`, `allowed_next_states`, `transition_state`) 에 맞춰 작성. atomic write 도 4중 방어의 한 축으로 명시.
  - `docs/ANTIPATTERNS/README.md` SCHEMA-AP 줄 갱신.
  - VERSION 0.2.6 → 0.2.7, 모든 Tier 1·2·3 마크다운 `last_synced_with` 일괄 갱신.
  - smoke test 5 케이스: ① new_project 성공 ② tmp 파일 잔존 없음 (atomic) ③ transition + history append ④ 손상된 manifest 로드 시 `ValidationError` ⑤ non-JSON manifest 로드 시 `JSONDecodeError` — TUI reload 가 의존하는 모든 경로 검증.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py` 통과.
  - 5 케이스 smoke test 모두 의도대로.
  - 외부 `transition` 호출 → manifest 디스크 갱신 → 다음 tick (≤ `tui_refresh_interval_sec`, 기본 0.5s) 에 TUI 가 `state changed: A → B` log + Dashboard 라이브 반영.
  - 평행 브랜치 `claude/start-after-handoff-Ij1TX` 의 가치 있는 부분 모두 본 브랜치에 흡수됨. 그 브랜치는 외부 codex review 통과 후 폐기 예정.
- **연관**: SCHEMA-AP-001 (신설). 평행 브랜치 발견 자체는 거버넌스 문제 (PR 없이 두 세션이 동시 작동) 라 별도 카탈로그 항목으로 등록은 보류 — 본 PATCH 자체가 그 사고의 복구.

## 2026-05-20 v0.2.8 — Codex 2차 리뷰 H2 반영: atomic write durability + tmp cleanup

- **무엇을**: `claude/phase-2-finalize` (v0.2.7) 에 대한 Codex Cloud 3-way 통합 리뷰 결과 (High 2 / Medium 3 / Low 4) 중 코드 측 High 1 건 (H2 — atomic write durability + tmp leftover) 을 머지 전 PATCH 로 흡수.
- **왜**: v0.2.7 의 `_write_manifest` 는 `tmp.write_text(...) + tmp.replace(path)` 로 **visibility** (rename atomicity) 만 보장했으나, durability (전원장애·강제종료 시 마지막 write 유실 방지) 는 별개. 또한 write 와 replace 사이에서 예외가 발생하면 tmp 파일이 leftover 로 남는 문제. TUI 라이브 reload 가 동시에 manifest 를 읽는 본 PATCH 시점부터는 이 두 갭이 실제 운영 리스크로 격상됨. Codex H2 의 지적이 정확함.
- **어떻게**:
  - `orchestrator/project_manager.py:_write_manifest` 전면 재작성:
    - `path.write_text` 를 `open() / write() / flush() / os.fsync(fileno())` 4단으로 분해. fsync 가 OS 버퍼 → 디스크 매체까지 강제. `f.flush()` 만으로는 OS 버퍼만 비우고 디스크 도달은 미보장이므로 둘 다 필요.
    - rename 후 부모 디렉토리도 `os.fsync(dir_fd)`. POSIX `rename(2)` 의 원자성과 디렉토리 entry 의 durability 는 별개라서 dir fsync 가 필요 (널리 알려진 함정). `O_DIRECTORY` 가 없는 Windows 환경은 `OSError` 로 떨어지므로 best-effort skip.
    - write/replace 단계 전체를 `try/except` 로 감싸 leftover tmp 를 `unlink` (cleanup 실패는 swallow, 원본 예외만 전파). `replace` 성공 후엔 tmp 가 이미 path 로 옮겨졌으므로 잔존 불가.
    - docstring 을 "atomic visibility" vs "durability" 로 분리. 향후 reader 가 "이 함수가 무엇을 보장하고 무엇을 안 하는지" 한눈에 알 수 있게.
  - `os` 모듈 import 추가 (`fsync`, `O_DIRECTORY`, `open` 헬퍼).
  - smoke test 에 `Path.replace` mock 으로 의도적 실패를 흉내내 cleanup 동작 검증 1 케이스 추가. 정상 happy path / corrupt manifest ValidationError / non-JSON JSONDecodeError 와 함께 5 케이스 모두 통과.
  - n9ird 의 기존 30 단위 테스트 회귀 전부 통과.
- **결과**:
  - `python -m py_compile` 통과.
  - 5 smoke + 30 unit = 35 케이스 모두 의도대로.
  - 머지 차단 사유 (H2) 해제. H1 (Ij1TX 원본 커밋 부재로 흡수 완전성 입증 불가) 은 코드 이슈가 아닌 절차 이슈로 분리:
    Codex Cloud 가 본 저장소 clone 시 모든 브랜치를 fetch 하지 않을 수 있음 → 다음 리뷰 시 사용자가 명시적으로 `claude/start-after-handoff-Ij1TX` 와 `claude/phase-2-implementation-n9ird` 를 비교 대상으로 지정. 본 저장소에서는 두 브랜치 모두 origin 에 존재.
- **연관**: Codex H2. M/L 5건은 v0.2.9 또는 Phase 3 진입 전 일괄 처리 후보로 분리.

## 2026-05-20 v0.2.9 — Codex 3차 리뷰 결과 흡수 (dir fsync 신호화 + 타입 힌트 + 주석 정합)

- **무엇을**: `claude/phase-2-finalize` HEAD 78f11bb (v0.2.8) 에 대한 Codex Cloud 단일 브랜치 리뷰 결과 (Critical 0 / High 1 / Medium 1 / Low 1) 를 v0.2.9 PATCH 로 흡수. 머지 차단 사유 해제.
- **왜**: 3차 리뷰의 H1 ("dir fsync 실패가 완전히 묵살되어 docstring 의 durability 보장과 어긋남") 이 머지 차단 사유였음. v0.2.8 에서 `try/except OSError: pass` 가 너무 적극적인 swallow 였다. POSIX 환경에서 권한·FS 특성·일시 오류로 dir fsync 가 실패하면 rename durability 가 약화되는데, 호출자에게도 로그에도 신호가 없으면 사후 추적 불가능. 운영자 기대치 (docstring 의 durability 보장) 와 runtime 현실의 정합이 필요.
- **어떻게**:
  - `orchestrator/project_manager.py`:
    - 모듈 레벨 `logger = logging.getLogger(__name__)` 도입. 본 저장소 첫 표준 logging 진입점.
    - dir fsync `except OSError as e:` 에서 platform (`os.name`) · errno · 메시지를 포함한 `logger.warning(...)`. 실패는 여전히 흡수 (rename 은 이미 visible) 하되 신호화. 호출 측이 logging 설정 없으면 root logger 가 stderr 로 송출.
    - `_SLUG_RE` 주석을 "하이픈만" 뉘앙스 → "하이픈·언더스코어 허용, 첫 글자는 영숫자" 로 실제 정규식 의도와 일치하게 정합화 (3차 리뷰 L 항목).
  - `orchestrator/main.py`:
    - `_print_manifest_summary(manifest)  # type: ignore[no-untyped-def]` → `_print_manifest_summary(manifest: ProjectManifest) -> None`. type ignore 제거. CLAUDE.md C2 "모든 함수 시그니처 타입 힌트 필수" 정합.
    - `from schemas.models import ... ProjectManifest` 추가.
  - smoke test 추가: `unittest.mock.patch('orchestrator.project_manager.os.fsync', ...)` 로 두 번째 fsync 호출 (dir fsync) 만 `OSError(13, ...)` 던지게 mock. warning 로그에 `errno=13` / `platform=posix` / 한국어 메시지 포함을 직접 검증.
  - 5 케이스 smoke (happy / dir fsync 실패 시 warning log / cleanup 회귀 / corrupt JSON / non-JSON) + 30 기존 단위 테스트 회귀 모두 통과.
  - VERSION 0.2.8 → 0.2.9, 갱신된 4 파일 (`CHANGELOG.md`, `DEVLOG.md`, `HANDOFF.md`, `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md`) 의 `last_synced_with` 만 v0.2.9 로 (n9ird 컨벤션: 수정한 파일만 갱신).
- **결과**:
  - `python -m py_compile` 통과.
  - 35 케이스 (5 smoke + 30 unit) 모두 의도대로.
  - Codex 머지 차단 사유 (H) 해제. M·L 도 같이 처리. main 머지 직전 단계.
  - 본 PATCH 자체에 대해 머지 전 한 차례 더 codex 리뷰를 돌리는 것이 안전 (코드 변경 있음, C10.3 self-exemption 미적용).
- **연관**: Codex 3차 리뷰 H1/M1/L1. 미반영 4 항목은 CHANGELOG v0.2.9 의 "Codex 3차 리뷰 미반영 항목" 절에 사유와 함께 기록.

## 2026-05-21 v0.3.0 — Phase 3: Dynamic Intake Page + IntakePlannerWorker

- **무엇을**: Phase 3 의 핵심 산출물 3 종 (도메인 LLM Worker + 웹 폼 + CLI) 을 단일 MINOR
  로 묶어 도입. HANDOFF §2.2 의 DoD 8 항목을 모두 충족.
- **왜**: BaseLLMWorker 인프라가 외부 리뷰 3 차까지 (v0.2.9) 견고해졌고, codex review 절차도
  정형화 (v0.2.6) 됐다. 다음 자연스러운 단계는 **첫 도메인 LLM Worker** 인 IntakePlannerWorker.
  이 Worker 가 도입되면 (a) Phase 0 의 IntakePlan Pydantic 모델이 처음으로 실 데이터로 채워지고,
  (b) BaseLLMWorker 의 4 parsed_status / output_path 가드 / agent 모드 opt-in 이 도메인 흐름에서
  실제로 검증되며, (c) 사용자가 처음으로 웹 UI 로 파이프라인과 상호작용하게 된다 (지금까지는
  CLI / TUI 만).
- **어떻게**:
  - `workers/intake_planner_worker.py` 신설. BaseLLMWorker 상속. `system_prompt` 가 IntakePlan
    스키마 + IntakeMode 9 enum 값 + 출력 규칙을 LLM 에 강제. `CATEGORY_GUIDANCE` (모듈 레벨 dict)
    가 GOAL.md G2 의 5 카테고리별 baseline 항목 카탈로그. `build_user_prompt` 가 manifest 의
    title/category/duration/topic_summary 를 `.replace()` 로만 치환 (`.format()` 은 JSON `{}` 와
    충돌 — CLAUDE.md C2). `output_path` 는 `01_intake/intake_plan.json` 으로 고정.
    `load_manifest` 의존을 의도적으로 회피하고 `BaseWorker.project_dir(args)` 가 책임지는 경로 기반
    파일 read 로 가서 단위 테스트의 `args.projects_root=<tmp>` 가 정상 동작.
  - `web/intake_page_app.py` 신설. FastAPI + 인라인 HTML (Jinja 미도입). `_render_intake_html`
    이 manifest + plan 을 카드 폼으로 직렬화, 모든 사용자/manifest 유래 문자열에 `html.escape`.
    `_form_to_decisions` 가 form-urlencoded 입력을 `UserDecision[]` 로 검증된 변환 — 알 수 없는
    enum 값은 `default_mode` 폴백, 누락 mode 도 폴백. `submit` 핸들러는 `transition_state` 를 통해서만
    상태를 변경 (직접 manifest 쓰지 않음). 401·404 등은 `HTTPException` 으로 일관 응답.
  - `orchestrator/main.py` 에 `plan-intake` / `submit-intake` 서브커맨드 추가. `_cmd_plan_intake`
    가 합성 `TaskQueueItem` (output_refs=["01_intake/intake_plan.json"]) 으로 worker.run() 직접
    호출 + state 두 단계 전이. `_cmd_submit_intake` 가 입력 JSON 의 project_id 일치 검증 + 영속화 +
    `source_collecting` 전이. Phase 4 의 자동 task_queue.json 도입 전 단계라 의도적으로 task_queue
    파일 영속화는 하지 않음.
  - 의존성: `requirements.txt` + `pyproject.toml` 에 fastapi/uvicorn/python-multipart 추가.
  - 테스트: `tests/test_intake_planner_worker.py` (13 케이스) + `tests/test_intake_flow.py` (6
    케이스). 후자는 `orchestrator.config.REPO_ROOT` 와 `workers.base_worker.REPO_ROOT` 양쪽을
    임시 디렉토리로 monkeypatch 해 실제 `projects/` 를 건드리지 않으면서 CLI end-to-end (new-project
    → plan-intake → submit-intake) + FastAPI `TestClient` POST 흐름까지 검증. stub mode 로 실 LLM
    호출은 회피.
  - 문서: `docs/03_AGENT_ARCHITECTURE.md` Agent 카탈로그의 Dynamic Intake Planner 행을 실제 구현
    파일 (`workers/intake_planner_worker.py (BaseLLMWorker)`) 로 갱신 + Worker 카탈로그에 한 행
    추가. 본 저장소 정책에 따라 LLM 호출 worker 의 parallelizable 은 ❌ (slot 1개 점유 가정).
  - VERSION 0.2.9 → 0.3.0, 36 개 마크다운/HTML `last_synced_with` 일괄 갱신 (sed).
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 모두 통과.
  - 단위 테스트 49 케이스 (30 회귀 + 13 IntakePlanner + 6 인테이크 flow) 모두 통과.
  - DoD 8 항목 (HANDOFF §2.2) 충족 확인:
    - [x] plan-intake → intake_plan.json + intake_pending_user 상태 (test_intake_flow.TestPlanIntakeCLI 검증)
    - [x] 웹 제출 → source_intake.json + source_collecting (test_intake_flow.TestWebSubmit 검증)
    - [x] 모든 도메인 데이터 Pydantic 검증 통과 (IntakePlan / SourceIntake / UserDecision 통합 케이스)
    - [x] LLM 호출은 BaseLLMWorker 경유, llm_calls/{call_id}.{json,prompt.txt,raw.txt} 영속화
    - [x] codex backend 도 stub mode 케이스 추가 (test_codex_backend_passthrough). 실 호출은 Windows
          에서 사용자 검증 필요 — 본 컨테이너는 codex CLI 미설치.
    - [x] py_compile + 단위 테스트 49 케이스 통과 (35+ 초과)
    - [x] CHANGELOG.md `[v0.3.0]` + DEVLOG.md 본 엔트리
    - [ ] **C10.1 codex review** — 본 컨테이너에 codex CLI 부재. 사용자 머신에서 `docs/REVIEW_PROMPT.md`
          §3 절차로 실행 예정. 결과는 v0.3.1 PATCH 로 흡수 또는 false-positive 합의.
- **알려진 위험과 향후**:
  - Phase 4 (`task_queue.json` 자동 생성 + 일반 worker subprocess 흐름) 가 도입되면 IntakePlannerWorker
    도 합성 task 대신 실제 queue 의 task 로 호출되도록 plan-intake CLI 를 단순화.
  - LLM-AP-003 후속 (codex --sandbox, scratch dir, `<untrusted_source>` envelope) 은 Phase 4 의
    `source_collector_worker` 도입 전에 처리 — IntakePlanner 는 agent 모드 미사용이라 본 Phase 미해당.
  - SCHEMA-AP-001 회귀 테스트는 v0.2.9 에서 v0.3.x 후보로 분리되어 있었음 — 본 PATCH 에서도 다루지
    않음. intake flow 의 정상 전이 (6 케이스) 가 부분 cover 하지만 임의 점프 명시 회귀는 별도.
- **연관**: HANDOFF §2 Phase 3 DoD, GOAL.md G3 #7/#8/#10, docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md.

## 2026-05-21 v0.3.1 — Codex 4차 리뷰 흡수: web 보안 + state 견고성 + 테스트 보강

- **무엇을**: v0.3.0 (89f56f9) 에 대한 Codex 단일 브랜치 리뷰 결과 (Critical 1 / High 3 /
  Medium 4 / Low 1 / Nit 1, 총 11 항목) 를 단일 PATCH 로 흡수. False positive 없음.
- **왜**: Phase 3 는 본 저장소 첫 web-facing endpoint + 첫 도메인 LLM Worker 도입이라 보안
  표면이 처음으로 확장. C1 (path traversal), H1 (절대경로 누출), H2 (form DoS) 는 모두 web 표면
  의 신뢰 경계 미설정에서 비롯. H3/M1/M2 는 state machine 과 추적성의 일관성 문제로, 다음 Phase
  들의 task_queue 자동화가 들어오기 전에 베이스라인을 견고하게.
- **어떻게**:
  - **C1** — `orchestrator/project_manager.py` 에 공개 가드 `validate_project_id(pid)` 분리.
    `new_project` 내부 검증을 추출해 web/CLI/통합 코드가 공유. `_SLUG_RE` 와 동일 정책. 위반 시
    `ValueError`. `web/intake_page_app.py` 에 `_validated_pid` 헬퍼가 두 endpoint 진입점에서 강제,
    실패 시 400 + generic detail. CLI `plan-intake`/`submit-intake` 도 동일 호출.
  - **H1** — `web/intake_page_app.py` 의 두 핸들러 `except FileNotFoundError` 블록에서 절대경로가
    포함된 원본 메시지를 generic `"intake plan not found for the requested project"` 로 교체.
    원본 detail 은 `logger.warning("intake … 404 — pid=%s detail=%s", ...)` 로 서버 측 로그만.
  - **H2** — submit 핸들러가 `request.headers.get("content-length")` 검사를 `await request.form()`
    전에 수행. 한도는 모듈 변수 `MAX_FORM_BYTES = 256 * 1024`. 초과 시 413 즉시 거부. 변조된
    헤더는 swallow 하고 starlette 내부 한도가 fallback.
  - **H3** — `orchestrator/main.py:_cmd_plan_intake` 에 `--force` 옵션 + idempotent skip 로직
    추가. `intake_planning` 상태에서 `01_intake/intake_plan.json` 이 존재하고 `IntakePlan` 검증을
    통과하면 worker 호출을 건너뛰고 `intake_pending_user` 로 전이만 진행. 손상된 plan 은
    재실행 (이전 부분 산출물 복구). 출력에 `skipped=True/False` 명시.
  - **M1** — `_cmd_submit_intake` 의 흐름을 (1) state precondition (current_state == intake_pending_user)
    조기 검증 → (2) tmp 파일에 write → (3) `transition_state` 시도 → (4) 성공 시 `tmp.replace(out_path)`,
    실패 시 tmp `unlink` cleanup. Web 의 `submit_intake` 도 비슷한 흐름 (write 자체를 transition
    뒤로 이동) 으로 재배열. 잘못된 상태에서 파일 덮어쓰기 차단.
  - **M2** — `_cmd_plan_intake` 가 `worker.run()` 직후 `worker.write_result(worker_args, result)`
    를 명시 호출. `projects/{pid}/03_tasks/task_results/intake-plan-{pid}_result.json` 생성. Phase 4
    의 정식 task_queue 흐름 전까지 C4 추적성 stopgap.
  - **M3** — `tests/test_intake_planner_worker.py` 에 `TestRunParseFailed` (자연어 stub →
    JSONDecodeError) + `TestRunSubprocessError` (`_invoke_llm` monkeypatch, exit_code 7 record
    영속화 검증). IntakePlanner 가 BaseLLMWorker 의 4 parsed_status 분기 전부에 도달함을 명시.
  - **M4** — `tests/test_intake_flow.py::TestWebSecurityAndNegativePaths` 7 케이스 신설.
    traversal PID GET/POST, 대문자 PID, 없는 PID 의 generic 404 (절대경로 미노출 grep),
    MAX_FORM_BYTES 잠시 낮춰 413, M1 race (state precondition + 기존 파일 bytes 보존), M2
    task_result.json 존재, H3 idempotent skip (LLM stub unset 상태에서도 worker 미호출
    + llm_calls/ 미생성).
  - **L1** — `_render_item_card` HTML 에 google_drive_links / uploaded_files / ai_delegate_remaining
    입력 필드 추가. parser 가 처리하는 모든 UserDecision 필드를 UI 에 노출 (contract drift 해소).
  - **N1** — `TestRunValidationFailed` 의 코멘트가 실제 실패 원인 (extra="forbid" 위반) 과
    어긋났던 부분 정정.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 49 → **60 케이스** (BaseLLMWorker 22 + run 통합 8 + IntakePlanner 15 + 인테이크
    flow 15). 모두 통과.
  - 머지 차단 사유 (Codex Critical/High 4건) 모두 해제. Medium/Low/Nit 도 같이 흡수.
  - last_synced_with 는 v0.2.9 의 n9ird 컨벤션 (수정한 마크다운만) 따름 — CHANGELOG.md /
    DEVLOG.md / HANDOFF.md 만 v0.3.1 로. PATCH 의 코드 4 파일 + 테스트 2 파일은 YAML 헤더 없음.
- **알려진 한계와 향후**:
  - H2 의 starlette 내부 form 크기 한도는 ASGI 서버 (uvicorn) 설정에 의존. 운영 배포 시
    `uvicorn --limit-max-requests N` / nginx 등의 reverse proxy 단에서 추가 강제 권장.
  - M1 의 web 흐름은 CLI 와 달리 tmp-rename 대신 transition-우선 순서를 채택. write 실패
    (디스크 full 등) 시 state 만 진행되는 좁은 race 존재. Phase 4 에서 web 도 tmp-rename
    패턴 통일 검토.
  - H3 의 `--force` 는 의도적 우회로 두되, Phase 4 의 task_queue 흐름이 도입되면 task
    재실행은 큐 레벨에서 결정 (worker 단의 `--force` 는 사라질 가능성).
- **연관**: Codex 4차 리뷰 11 항목 전부. C10.3 self-exemption 적용.

## 2026-05-22 v0.3.2 — SCHEMA-AP-001 회귀 테스트 명시 (누적 부채 청산)

- **무엇을**: `orchestrator.state_machine.validate_transition` 의 다섯 가지 보호 조건
  (정상 선형 / 임의 점프 거부 / self-loop 거부 / ARCHIVED 어디서든 도달 / ARCHIVED
  종착성) 을 단위 테스트로 회귀화. `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` 의
  `regression_test: pending` 을 실제 파일 경로 + 카테고리 매핑으로 갱신. 코드 동작
  변경 없음.
- **왜**: SCHEMA-AP-001 은 v0.2.7 에 카탈로그 등록되었지만 회귀 테스트가 5 케이스
  pending 으로 남아 있어 v0.2.9 부터 누적 부채. Phase 4 (task_queue + 첫 agent 모드
  Worker) 가 state 머신 위에 새 전이 사용처를 얹기 전에 가드의 정확성을 명시적으로
  고정해 두는 것이 안전. v0.3.x PATCH 후보 (HANDOFF §2.4) 의 첫 항목.
- **어떻게**:
  - `tests/test_state_machine.py` 신설. 5 카테고리 × 평균 2 메소드 = 10 테스트 메소드.
    각 카테고리를 별도 `TestCase` 클래스로 분리해 실패 시 어느 보호 조건이 깨졌는지
    즉시 식별 가능. `LINEAR_SEQUENCE` 의 모든 인접 페어를 `subTest` 로 순회해 정의가
    바뀌면 즉시 신호.
  - `_coerce` 가 str → enum 변환을 한다는 사실도 한 케이스로 명시
    (manifest 의 `use_enum_values=True` 와 정합).
  - 메시지 contract 도 회귀화: "잘못된 상태 전이" / "동일 상태" / "허용된 다음 상태"
    힌트가 메시지에 포함되는지 검증. CLI / web 의 사용자-facing 에러 메시지가 조용히
    바뀌는 것을 차단.
  - `SCHEMA_ANTIPATTERNS.md` 의 `regression_test` 필드를 `pending` 에서 실제 위치로
    갱신. README 가 명시한 `status` / 위치 정보의 운영 라이프사이클 갱신 (내용 자체
    수정 아님, append-only 정책 준수).
  - 테스트 디렉토리 구조는 카탈로그 표기 `tests/orchestrator/test_state_machine.py`
    대신 기존 평면 구조 `tests/test_state_machine.py` 채택 (CLAUDE.md 원칙 1
    "단순함을 우선"). 카탈로그도 평면 경로로 정정.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 60 → **70 케이스**. 모두 통과.
  - 카탈로그의 `pending` 부채 1건 청산. v0.4.0 의 Phase 4 가 state 머신 위에 안심하고
    얹을 수 있는 기반 마련.
- **알려진 한계와 향후**:
  - `LINEAR_SEQUENCE` 자체의 진화 (예: 새 상태 삽입) 는 본 회귀가 자동으로 따라간다
    (인접 페어 순회). 그러나 ARCHIVED 의 특수 의미가 바뀌면 ④/⑤ 케이스 직접 수정 필요.
  - 메시지 contract 검증은 영어 → 한국어 / 표현 변경 시 함께 갱신해야 한다. 너무
    엄격하면 i18n 비용, 너무 느슨하면 회귀 가치 떨어짐. 현재는 핵심 키워드만 매치
    (substring) 로 균형.
- **연관**: SCHEMA-AP-001, HANDOFF §2.4 첫 항목.

## 2026-05-22 v0.3.3 — `<untrusted_source>` envelope 헬퍼 도입 (LLM-AP-003 후속 사전 작업)

- **무엇을**: `workers/prompt_safety.py:wrap_untrusted` 순수 함수 신설. 외부 자료를
  `<untrusted_source>...</untrusted_source>` envelope 으로 안전하게 wrap 하는
  헬퍼와 회귀 테스트 (13 메소드). 코드 동작 변경 없음 — 호출하는 worker 는 아직 없음
  (Phase 4 의 `source_collector_worker` 가 사용 예정).
- **왜**: LLM-AP-003 의 본격 mitigation 은 (a) opt-in 가드 (v0.2.5 완료), (b)
  envelope 격리, (c) sandbox 매핑 + scratch dir 의 세 요소. (c) 는 Phase 4 와 함께
  가야 의미가 있지만 (b) 는 순수 함수 + 회귀 테스트만 들어가는 작은 작업이라 미리
  분리. Phase 4 PATCH 가 커지는 것을 막고, envelope 의 정확한 시맨틱이 단위 테스트
  로 못박힌 상태에서 worker 가 호출할 수 있게.
- **어떻게**:
  - 위치는 `workers/prompt_safety.py` 신규 모듈로 결정 (BaseLLMWorker staticmethod
    대신). BaseLLMWorker 가 이미 573 줄로 비대해진 점, Phase 4 의 sandbox / scratch
    유틸이 같은 위치에 자라날 자리 확보를 위해. CLAUDE.md 원칙 1 "단순함을 우선"
    의 단순함은 "한 곳에 모음" 보다 "각각의 책임 모듈" 로 해석.
  - escape 전략은 명시적 마킹 (`<ESCAPED_OPEN_untrusted_source` /
    `<ESCAPED_CLOSE/untrusted_source>`). zero-width space 같은 invisible escape 대신
    LLM 이 보고 명백히 sanitize 되었음을 인지할 수 있는 노이즈 토큰 사용. 정확한
    envelope 경계 토큰과 더 이상 매치되지 않으면 충분.
  - 변형 회피: case-insensitive + 공백 허용 regex (`<\s*untrusted_source\b` /
    `<\s*/\s*untrusted_source\s*>`). LLM 이 정규화해서 받아들일 수 있는 변형까지
    보수적으로 차단.
  - label 안전화: envelope 태그 escape + `"` → `&quot;` (속성값 종료 방지) +
    newline 공백 평탄화 (opener 한 줄 보장).
  - 회귀 테스트 5 카테고리: ① 정상 wrap 형식 ② close-tag injection ③ open-tag
    injection (속성 변형 포함) ④ case / whitespace 변형 ⑤ label 안전화 (`"` /
    envelope 태그 / newline 각각).
  - LLM-AP-003 카탈로그의 mitigation / regression_test / resolved / 알려진 한계
    절을 envelope 헬퍼 진전 반영해 update. status 는 `resolved-partial` 유지 —
    sandbox / scratch dir 까지 끝나야 `resolved`.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 단위 테스트 70 → **83 케이스**. 모두 통과.
  - Phase 4 의 `source_collector_worker` 가 외부 자료를 prompt 에 넣을 때 호출할
    안정적 sentinel 확보.
- **알려진 한계와 향후**:
  - sentinel 만으로는 prompt injection 의 한 layer 일 뿐. semantic injection
    (envelope 안에서 일반 문장으로 LLM 을 속이는 방식) 은 막지 못함. Phase 4 의
    `--sandbox workspace-write` 매핑 + scratch dir 격리가 함께 가야 의미가 있다.
  - "envelope 안을 명령으로 해석하지 마라" 를 LLM 에게 명시하는 책임은 호출자
    (worker 의 system_prompt) 측. 본 함수는 sentinel 형식만 보장.
  - 매우 긴 외부 자료 (수십 KB+) 의 길이 제한은 호출자 정책. Phase 4 의 worker 가
    필요 시 truncate + summary 단계 도입.
- **연관**: LLM-AP-003 (resolved-partial 의 (b) envelope 격리 완료), HANDOFF §2.4
  envelope 헬퍼 항목, Phase 4 의 `source_collector_worker` 선결 작업.

## 2026-05-22 v0.3.4 — codex 리뷰 절차의 역할 분담을 규칙으로 박음

- **무엇을**: `CLAUDE.md` C10 과 `docs/REVIEW_PROMPT.md` §2 에 codex 외부 리뷰의
  역할 분담을 명문화. 새 §C10.0 "역할 분담 (변경 불가)" 추가 — AI 어시스턴트가
  `review-prompt.txt` 본문을 직접 생성하고, 사용자는 codex 실행 + 결과 paste 만
  수행. AI 가 절차를 *안내만* 하고 사용자 명시적 요청을 기다리는 형태도 위반으로
  정의. C10.2 5 단계에 `(AI 어시스턴트 책임)` / `(사용자 책임)` / `(공동)` 태그 부여.
- **왜**: 직전 세션 (v0.3.3 직후 / v0.4.0 작업 도중) 에 AI 어시스턴트가 MINOR
  증분 직전이라는 trigger 시점을 인식했음에도, codex 리뷰를 "사용자가 자기
  머신에서 직접 수행하는 단계" 로만 안내하고 능동적으로 시작하지 않는 사고가
  발생. 사용자가 직접 "왜 의무인데 패스하느냐 / 프롬프트는 AI 가 생성해서
  나에게 줘라" 라고 교정 지시. 같은 ambiguity 가 재발하지 않도록 규칙 자체를
  닫음. (v0.2.6 의 절차 정형화 PATCH 가 *언제 실행하나* / *어떻게 실행하나* 까지는
  박았지만 *누가 채우나* 는 암묵적이었음.)
- **어떻게**:
  - C10 머리에 새 §C10.0 표로 AI 어시스턴트 / 사용자 책임을 분리 명시. 표
    아래에 "AI 어시스턴트는 본 절차를 임의로 생략하지 못한다" 를 굵게 명문화.
    "trigger 시점에 절차를 안내만 하고 사용자의 명시적 요청을 기다리는 것" 도
    위반으로 정의.
  - C10.2 의 5 단계 각각에 책임자 태그 부여. step 1 은 "AI 가 세 절을 모두
    직접 채워서 완성된 `review-prompt.txt` 를 SendUserFile 또는 코드블록으로
    전달" 로 강화. 사용자에게 "이 칸을 채우세요" 는 명시적 금지.
  - `docs/REVIEW_PROMPT.md` §2 의 템플릿 안내 직후에 인용 블록으로 같은 규칙을
    재진술 (작업자가 CLAUDE.md 까지 안 봐도 매뉴얼만 보고 알 수 있도록).
  - 본 PATCH 는 `CLAUDE.md` C10.3 "본 절차 자체를 도입/수정하는 PATCH 는
    codex review 면제" 에 의해 외부 리뷰 면제. 자기 검증 회피 방지.
  - 버전 / 동기화: VERSION 0.3.3 → 0.3.4, CLAUDE.md / REVIEW_PROMPT.md /
    CHANGELOG / DEVLOG 헤더 last_synced_with 갱신.
- **결과**:
  - 다음 trigger 시점부터 AI 어시스턴트는 "리뷰 절차를 안내" 가 아니라
    **"완성된 review-prompt.txt 본문을 전달"** 을 의무로 수행. 사용자의 명시적
    요청 없이도 능동적으로 시작해야 함이 규칙으로 박힘.
  - 본 PATCH 직후 v0.4.0 (LLM-AP-003 sandbox + scratch dir mitigation) 작업에서
    본 규칙을 최초로 자기 자신에게 적용 — 코드 완성 후 review-prompt.txt 본문
    생성 → 사용자 paste → 흡수 → v0.4.0 커밋.
- **알려진 한계와 향후**:
  - "trigger 인식" 자체를 자동화하는 git hook / CI 검증기는 아직 없음. AI 가
    self-discipline 으로 수행. 향후 commit-msg hook 에 "MINOR/MAJOR 커밋이면
    직전 N 커밋 안에 'codex' 라는 단어가 포함된 commit body 가 있는지" 같은
    weak signal 검증을 추가 검토.
  - false positive 합의 / DEVLOG 근거 명시 의무는 C10.2 step 5 에 그대로.
- **연관**: CLAUDE.md C10, docs/REVIEW_PROMPT.md, v0.2.6 (절차 정형화의
  연속), v0.4.0 (본 규칙의 첫 적용 대상).

## 2026-05-22 v0.4.0 — LLM-AP-003 sandbox + scratch dir 본격 mitigation + SourceCollectionPartial

- **무엇을**: codex agent CLI 매핑에 `--sandbox workspace-write` 추가, `--cd` 를
  `{project_dir}` → `{scratch_dir}` (`projects/{pid}/scratch/{task_id}/`) 로 변경.
  `BaseLLMWorker._scratch_dir_for_task` 헬퍼 신설. `_invoke_llm` 의 placeholder
  치환 시 `llm_mode == "agent"` 인 경우만 scratch dir 경로로 치환. 동시에 Phase 5
  의 `source_collector_worker` 출력 모델 `SourceCollectionPartial` (VersionedModel,
  schema_version=1 유지) 선행 정의.
- **왜**: LLM-AP-003 의 mitigation 세 layer 중 마지막 한 칸. (a) opt-in 가드
  (v0.2.5 완료) (b) envelope 격리 (v0.3.3 완료) (c) OS 레벨 sandbox + 파일시스템
  격리 — 본 PATCH 의 본론. agent 모드의 LLM 이 prompt injection 으로 sandbox
  바깥 / scratch 바깥에 write 하지 못하도록 두 겹의 boundary 를 둔다.
  Phase 5 worker 가 들어와야 실 효과 실증되지만, CLI 매핑과 헬퍼는 worker 보다
  먼저 박혀 있어야 worker 가 일관된 sandbox 가정 위에서 동작할 수 있음.
  `SourceCollectionPartial` 도 같은 맥락 — Phase 5 PATCH 가 worker + 모델을
  동시에 도입하지 않아도 되도록 모델만 선행 (작은 단위 커밋 C8.2).
- **어떻게**:
  - `CLI_INVOCATION` 의 `("codex", "agent")` 엔트리만 수정 (claude 와 codex
    response 는 동일). `--sandbox workspace-write` 의 의미는 codex `--cd` 디렉토리
    내부에서만 write 허용 — codex 자체의 OS 레벨 boundary.
  - `--cd` 인자를 `{scratch_dir}` 로 옮긴 이유: sandbox 가 active 여도 codex 의
    "현재 작업 디렉토리" 가 project_dir 이면 사용자가 무심코 거기에 write 가능한
    파일들 (다른 worker 산출물 / git 추적 코드) 이 sandbox 안에 포함된다. scratch
    dir 로 격리하면 sandbox + cwd 두 boundary 가 일치해 가장 좁아진다.
  - `_scratch_dir_for_task` 의 위치는 `BaseLLMWorker` 로. BaseWorker 에 두는 안도
    검토했지만, scratch dir 은 LLM agent 모드 의 sandbox 와 짝을 이루는 개념이라
    역할이 맞는 쪽에 둠. 비-LLM worker 가 scratch 공간이 필요해지면 그 때
    BaseWorker 로 lift.
  - placeholder 치환 분기: `llm_mode == "agent"` 일 때만 헬퍼 호출 (= mkdir 발생).
    response 모드는 빈 문자열 substitution → 만약 template 이 실수로 `{scratch_dir}`
    를 갖고 있어도 argv 가 빈 문자열로 변형되어 codex 측에서 명시적으로 실패
    (silent corruption 보다 낫다). 단 향후 response template 이 `{scratch_dir}`
    를 의도적으로 참조하지 않도록 코드 리뷰 / 회귀로 관리.
  - LLM-AP-003 카탈로그의 mitigation / regression_test / resolved / status /
    알려진 한계 절을 v0.4.0 진전 반영. status 는 `resolved-partial` 유지하되
    partial 의 의미가 "sandbox/scratch 매핑까지 마련, 실 호출 worker 는 Phase 5"
    로 이동.
- **결과**:
  - `python -m py_compile orchestrator/*.py workers/*.py schemas/*.py web/*.py` 통과.
  - 기존 단위 테스트 83 케이스 회귀 없이 통과.
  - codex agent CLI 가 자기 task 의 scratch 디렉토리 밖으로 write 못 하는 두 겹
    boundary 확보 — sandbox + cwd.
  - Phase 5 의 `source_collector_worker` 가 일관된 가정 위에서 도입 가능.
- **알려진 한계와 향후**:
  - 실 호출 worker (`source_collector_worker`) 가 아직 없음. sandbox 의 실제
    효과 — symlink escape, mount bind escape, codex 버전별 차이 — 는 worker
    도입 후 e2e smoke test 에서 검증.
  - scratch dir 은 task_id 단위 mkdir 만. 같은 task_id 재실행 시 잔존물 보임.
    현재 workers 가 멱등 실행 가정 없으므로 수용 가능. 필요 시 Phase 5 에서
    `shutil.rmtree → mkdir` 로 ephemeral.
  - codex `--sandbox workspace-write` 의 정확한 escape 경계는 codex 버전마다
    달라질 수 있어 `docs/ADDENDUM_04` §5 에 정기 갱신 필요.
  - 사용자 머신의 codex CLI 가 `--sandbox` 미지원이면 agent 모드 호출이 unknown
    flag 로 실패. 호출자가 분기 가능 (LLMSubprocessError exit_code != 0).
- **연관**: LLM-AP-003 (mitigation layer (c) 완료, status 는 여전히 resolved-partial
  — 호출 worker 도입까지), v0.3.3 (envelope 헬퍼), Phase 5 의
  `source_collector_worker` (본 PATCH 의 가정을 활용할 첫 worker).
- **codex 리뷰**: 본 PATCH 직후 v0.3.4 의 새 C10.0/C10.2 규칙에 따라 AI 가
  생성한 review-prompt.txt 로 codex 외부 리뷰 실행. 결과 흡수는 v0.4.1 PATCH
  ("외부 코드 리뷰 N차 반영") 로.

## 2026-05-22 v0.4.1 — codex 1차 외부 리뷰 흡수: sandbox 가드 승격 + 회귀 잠금

- **무엇을**: v0.4.0 의 codex 외부 리뷰 (Critical 2 / High 3 / Medium 3 / Low 1 /
  Nit 1) 단일 PATCH 흡수. v0.4.0 의 "의도된 가정" 들을 명시적 가드로 승격하고
  17 회귀 테스트로 잠금.
- **왜**: v0.4.0 는 codex `--sandbox workspace-write` + `--cd {scratch_dir}` 의
  "방향" 은 옳았지만 (i) task_id 가 path traversal 페이로드면 scratch 경계가
  깨지고, (ii) scratch 경로상 누군가 미리 깔아둔 symlink 가 있으면 codex 의
  sandbox resolve 가 우회될 수 있고, (iii) response 모드 template 에 누군가
  `{scratch_dir}` 를 끼우면 빈 문자열로 silent corruption 되며, (iv) 새
  placeholder 가 도입돼도 자동으로 알 방법이 없었다. 보안 mitigation 의 "intent"
  를 "verified guarantees" 로 끌어올리려면 가드 + 회귀 잠금이 필수.
- **어떻게**:
  - **C1 (task_id traversal)**: module-level helper `_is_safe_path_segment` 도입.
    `/`, `\\`, `..`, `.`, leading `.`, len > 128 거부 + `Path(s).name == s` 추가
    확인. `_scratch_dir_for_task` 진입 즉시 호출, 실패 시 `LLMSubprocessError`.
  - **C2 (symlink escape)**: module-level helper `_assert_no_symlinks_in_path`
    도입. scratch dir 부터 `project_dir` 까지 위로 올라가며 symlink 검사. 발견
    시 raise. codex 가 자기 안에서 만든 symlink 를 따라가는 행동은 codex 의
    책임이지만, scratch 경계 자체가 symlink 인 시나리오는 우리 쪽에서 차단.
  - **H1 (placeholder footgun)**: `_invoke_llm` 의 argv 빌드 로직을
    `_build_invocation_cmd` 로 추출 (subprocess 호출 없는 순수 함수 → 테스트
    가능). 그 안에서 치환 후 `cmd` argv 의 각 seg 에 `\{[A-Za-z_][A-Za-z0-9_]*\}`
    패턴이 잔존하면 `LLMSubprocessError`. `seg == full_prompt` 인 자리는 검사
    제외 (사용자 prompt 본문의 JSON `{}` 와 충돌 회피).
  - **H2 (mode/template drift)**: 같은 메서드에서 `template_uses_scratch =
    any("{scratch_dir}" in seg for seg in template)` 로 검사. (a) True 이면서
    `llm_mode != "agent"` 면 raise (silent empty-string 차단). (b) True 일
    때만 `_scratch_dir_for_task` 호출 (mode-driven → template-driven, 의도 drift
    제거).
  - **H3 (테스트 부재)**: `tests/test_base_llm_worker_sandbox.py` 신설. 17
    메소드, 4 클래스 (`TestPathSegmentSafety`, `TestScratchDirHelper`,
    `TestAssertNoSymlinks`, `TestInvocationCmdShape`, `TestPlaceholderFailFast`).
    POSIX 한정 symlink 테스트는 `sys.platform == "win32"` 일 때 skip.
  - **M1 (scratch lifecycle)**: `BaseLLMWorker.clean_scratch_on_start: ClassVar
    [bool] = True` 신설. `_scratch_dir_for_task` 가 mkdir 전에 `shutil.rmtree`
    수행. 기본값 True 로 ephemeral 보장 — 멱등 worker 가 잔존물 활용해야 하면
    클래스 변수로 `False` 명시 (현재 그런 worker 0 개).
  - **M2 (Phase 4 → 5)**: `SourceCollectionPartial` docstring 정정.
  - **M3 (notes 범용)**: `notes` → `collector_notes` rename. 모델이 v0.4.0
    신규로 영속 인스턴스 없어 호환성 부담 없음.
  - **L1 (input_item_id 도메인 불변식)**: schema 는 Optional 유지 (C3
    additive-first), 강제는 Phase 5 worker 단으로 미룸. LLM-AP-003 known-limits
    에 명시.
  - **N1 (단정 톤)**: LLM-AP-003 v0.4.0 mitigation 본문의 "scratch 밖으로도
    write 못 함" → "의도된 가정 하에서 — codex 가 `--sandbox workspace-write` 를
    honor 하고, scratch 경로상 symlink 가 없으며, task_id 가 단일 path 세그먼트
    인 경우 — agent 는 (a) 사용자 자료 / (b) 다른 worker 산출물 / (c) git 추적
    코드 모두 건드릴 수 없다." 로 톤다운. known-limits 의 symlink/mount 불확실성
    과 균형.
- **결과**:
  - `python -m unittest discover tests` 100 케이스 통과 (기존 83 + 신규 17, 회귀 없음).
  - codex 1차 리뷰의 모든 Critical/High/Medium/Low/Nit 흡수.
  - argv shape 회귀가 잠겨 향후 CLI 매핑 변경 시 sandbox/scratch 플래그가
    실수로 누락되면 즉시 테스트 실패.
- **False positive**: 첫 번째 리뷰 round (commit 9b200a8 이전 working tree 기준,
  사용자 머신의 v0.3.4 코드를 본 결과) 의 모든 Critical 항목은 "구현 안 됨" 으로
  정확했지만 두 번째 round (commit 9b200a8 기준) 로 superseded — 모두 흡수 대상
  외. 두 번째 round 만 흡수.
- **codex 재리뷰 면제**: 본 PATCH 는 CLAUDE.md C10.3 ("외부 리뷰 결과 반영
  PATCH 는 면제 — 무한 루프 방지") 에 해당.
- **연관**: LLM-AP-003 (mitigation 의 v0.4.0 가정 → v0.4.1 가드 승격),
  v0.4.0 (본 PATCH 가 흡수하는 변경), Phase 5 의 `source_collector_worker`
  (본 가드들을 활용할 첫 worker).

## 2026-05-22 v0.4.2 — 실 codex sandbox 검증 → known-limits 갱신

- **무엇을**: 사용자 머신 (Windows 11 + ChatGPT Plus + codex-cli 0.130.0) 에서
  v0.4.0-v0.4.1 mitigation 의 실 효과를 호출 단위로 검증. 결과를 ADDENDUM_04
  §5.2.1 (신설) 과 LLM-AP-003 known-limits (재구성) 에 반영. 코드 변경 없음.
- **왜**: 단위 테스트는 "우리 가드가 의도대로 호출되는가" 만 보장하고, 실
  codex 가 `--sandbox workspace-write` 를 어떻게 honor 하는지 / Windows 의
  junction 을 처리하는지 등은 호출해 봐야 알 수 있다. v0.4.0 의 LLM-AP-003
  본문이 "intent" 만 적었고 v0.4.1 이 "intent → guarded intent" 로 끌어올렸으면,
  v0.4.2 는 "guarded intent → verified guarantees" 로 한 단계 더.
- **어떻게**:
  - Stage 1 (실 codex 호출, 4 회):
    - 1a `workdir 안 write` → ✅ inside.txt 정상 생성.
    - 1b `Desktop write` → ✅ codex 가 명시적 거부 ("workspace-write,
      writable paths are limited to …, Desktop is outside").
    - 1b-multi `C:\tmp\sibling / %TEMP% / .codex/memories` 각각 시도:
      - `C:\tmp\sibling_outside.txt` → 🚫 차단 (UnauthorizedAccessException).
        codex header 의 `/tmp` 라벨은 Windows literal `C:\tmp` 가 **아니라**
        `%TEMP%` 의 OS-relative 라벨.
      - `%TEMP%\temp_outside.txt` → ⚠️ 자동 허용.
      - `~/.codex/memories\memory_test.txt` → ⚠️ 자동 허용.
    - 1c `junction escape` → ✅ codex 가 OS-level resolve 한 뒤 차단
      (`PermissionDenied`).
  - Stage 2 (Python 가드 단독, 컨테이너):
    - `_is_safe_path_segment` 11 케이스 모두 기대값.
    - `_scratch_dir_for_task` 멱등 / clean_scratch True ephemeral / False opt-out 정상.
    - `_build_invocation_cmd` argv: codex agent 에 `--sandbox workspace-write
      --cd <scratch>` 포함, claude response 에 sandbox 부재 + scratch 미생성.
    - `_assert_no_symlinks_in_path` POSIX symlink 검출.
    - placeholder fail-fast + response + `{scratch_dir}` raise + 본문 brace 허용
      모두 동작.
  - 결과를 ADDENDUM_04 §5.2.1 (신설) 에 검증 표 + 우리가 닫을 수 없는 영역의
    의미 (side channel) + codex CLI 의 한계 + 버전 종속성으로 정리. 동일 핵심을
    LLM-AP-003 known-limits 에 요약. 두 문서는 ADDENDUM_04 가 source 의 위상.
- **결과**:
  - `%TEMP%` 와 `~/.codex/memories` 두 곳이 codex CLI 의 디폴트로 우리가 닫을
    수 없는 side channel 임을 명시. prompt 측 / 운영 절차로 보강.
  - v0.4.1 의 `_assert_no_symlinks_in_path` preflight 가 codex 0.130.0 의
    OS-level junction 차단과 중복하지만 defense-in-depth 로 유지 결정 (다른
    codex 버전 / Linux/macOS / 다른 backend 대비).
  - codex CLI 의 `--help` 에서 `workspace-write` 영역을 좁히는 옵션 부재 확인.
    `-c sandbox_permissions=[...]` 는 확장 방향 (예: disk-full-read-access),
    `--dangerously-bypass-approvals-and-sandbox` 는 우회. 따라서 본 두 side
    channel 은 codex CLI 의 디폴트 가정.
- **codex 재리뷰 면제**: 본 PATCH 는 외부 검증 결과를 반영하는 문서/메타 변경
  으로 CLAUDE.md C10.3 의 정신 ("외부 리뷰 결과 반영 PATCH 는 codex 재리뷰
  면제") 과 동일. 코드 변경이 0 이라 정적/동적 회귀의 새 표면이 없다.
- **연관**: LLM-AP-003 (mitigation 의 "verified guarantees" 절 신설),
  v0.4.0/v0.4.1 (본 PATCH 가 검증한 변경), ADDENDUM_04 §5.2.1 (신설), Phase 5
  의 `source_collector_worker` (sandbox 가정을 활용할 첫 worker).

## 2026-05-22 v0.5.0 — Phase 5 첫 PATCH: SourceCollectorWorker 도입 (codex agent 모드)

- **무엇을**: v0.4.0–v0.4.2 의 LLM-AP-003 mitigation (codex `--sandbox workspace-write`
  + per-task scratch dir + path 가드 + side-channel known-limits) 위에서 실 호출하는
  첫 agent 모드 worker 를 도입. `workers/source_collector_worker.py` (BaseLLMWorker
  상속, `allow_agent_mode=True`, `response_model=SourceCollectionPartial`),
  `orchestrator/source_collection_planner.py` (SourceIntake → TaskQueueItem 순수
  빌더), `tests/test_source_collector_worker.py` (29 케이스). 신규만, 기존 동작
  변경 없음. VERSION 0.4.2 → 0.5.0.
- **왜**: Phase 5 의 목적은 `SourceIntake.user_decisions` 중 AI 위임 항목 (`ai_delegate`
  / `mixed(ai_delegate_remaining=True)`) 을 자동 자료 수집 task 로 변환하고 실행하는
  것. v0.4.x 까지는 sandbox 가드와 envelope 헬퍼만 마련했고 실제 호출자가 없었다.
  본 PATCH 는 그 첫 호출자다. 단일 PATCH 의 부담을 줄이기 위해 task_queue 영속화 /
  CLI / SourceRegistryBuilder / 실 codex e2e 는 후속 PATCH 로 분리.
- **어떻게**:
  - **worker**: codex agent mode + opt-in 가드 통과. system prompt 가 ADDENDUM_04
    §5.2.1 의 verified side channels (`%TEMP%`, `~/.codex/memories`) 접근 금지를
    명시. `build_user_prompt` 는 source_intake.json 의 매칭 UserDecision 의
    외부 자료 4 종 (user_note + provided_links + google_drive_links +
    uploaded_files) 을 `wrap_untrusted` 로 단일 envelope 격리. mode 화이트리스트
    {ai_delegate, mixed} 외 항목은 ValueError 로 거부 (worker 책임 밖).
    input_item_id 누락 / unknown item_id / 파일 부재 모두 명시적 raise.
    output_path = `02_sources/partials/{task_id}.json`.
  - **planner**: 순수 함수 모듈. `task_id = src_collect__{item_id}` (단일 path
    세그먼트, `_is_safe_path_segment` 통과 보장). `existing_task_ids` set 인자로
    재제출 idempotency. mixed-with-ai_delegate_remaining=False 와 direct_provide /
    skip / link_provide / file_upload / reference_only / must_use 는 모두 제외.
  - **테스트**: 7 클러스터. (1) system_prompt 가 SourceCollectionPartial /
    SourceEntry 필드 + 8 개 RightsStatus enum 값 + sandbox 경계 + envelope
    guidance 를 모두 포함하고 `.format()` 시 raise. (2) build_user_prompt 의
    happy path / envelope tag-injection 격리 / 6 가지 에러 분기. (3) output_path
    위치 고정. (4) run() 의 4 가지 parsed_status 분기 (stub backend). (5) agent
    opt-in 가드 통과. (6) `_build_invocation_cmd` argv 가 `--sandbox
    workspace-write` + `--cd {scratch_dir}` 를 포함하고 scratch dir 이 실제
    생성됨 + task_id 가 `_is_safe_path_segment` 통과. (7) 빌더의 mode 필터링 /
    task shape / existing_task_ids idempotency / empty intake / needs_collection
    helper.
- **결과**:
  - `python -m py_compile workers/source_collector_worker.py
    orchestrator/source_collection_planner.py
    tests/test_source_collector_worker.py` 통과.
  - `python -m unittest discover -s tests` = **129/129 통과** (기존 100 + 신규 29).
  - 본 commit 은 push 직후 codex 클라우드 외부 리뷰 대상. CLAUDE.md C10.1 의
    "MINOR 증분 직전 필수" 는 v0.4.0 → v0.4.1 의 패턴 (push → 외부 리뷰 → 흡수
    PATCH) 으로 해석. 결과 흡수는 v0.5.1 (PATCH).
- **연관**: LLM-AP-003 (resolved-partial → 본 worker 가 첫 실 호출자), SCHEMA
  (SourceCollectionPartial 의 input_item_id Optional 인 채 worker 단 강제 — 본
  PATCH 가 worker 단 ValueError 로 강제), `wrap_untrusted` (v0.3.3 부터 호출
  대기 → 본 PATCH 에서 첫 사용), `_scratch_dir_for_task` + `_is_safe_path_segment`
  + sandbox argv (v0.4.0–v0.4.1) — 본 PATCH 가 그 가드 위에서 동작.

## 2026-05-22 v0.5.1 — C10 외부 코드 리뷰 절차 갱신: push-then-review + 전달 형태 의무화

- **무엇을**: CLAUDE.md C10.0 / C10.1 / C10.2 와 docs/REVIEW_PROMPT.md §3 갱신.
  (1) MINOR/MAJOR 의 codex 리뷰 트리거 시점을 "commit + push 직후" 로 명문화하고,
  (2) codex 클라우드 (권장) / 로컬 codex CLI (폴백) 두 패턴을 docs/REVIEW_PROMPT.md
  §3.0 으로 분기 정리하고, (3) AI 어시스턴트가 review-prompt 본문을 SendUserFile
  단독으로 전달하는 것을 위반으로 명시 (inline 코드블록 동시 전달 의무화).
  VERSION 0.5.0 → 0.5.1.
- **왜**: v0.5.0 세션에서 실 사용 중 두 가지 사고가 드러났다.
  (1) AI 가 review-prompt.txt 를 SendUserFile 만으로 전달했고 사용자가 다운로드된
  파일을 어디서 열어야 할지 못 찾았다 — 사용자 답답함 폭발 + 세션 시간 손실.
  (2) "MINOR 증분 직전 codex 리뷰" 라는 표현이 codex 클라우드 (commit 된 브랜치를
  fetch 하는 방식) 와 본질적으로 충돌했다. codex 클라우드는 push 된 SHA 만 보므로
  "commit 전 리뷰" 는 불가능하다. v0.4.0 → v0.4.1 사례도 사실은 "commit + push
  후 리뷰 → 다음 PATCH 흡수" 패턴이었는데 규칙이 그 점을 명확히 안 박았다.
- **어떻게**:
  - C10.0 표의 AI 어시스턴트 책임을 (a)-(d) 4 항목으로 확장. push 의무 (b) 와
    SendUserFile + inline 코드블록 동시 전달 (c) 명시. 위반 사례로 "SendUserFile
    단독" 도 명문화 ("위반 사례 v0.5.0 세션 참고").
  - C10.0 표의 사용자 책임에 codex 클라우드 (권장) / 로컬 codex CLI (폴백) 선택
    명시. AI 가 사용자 머신 OS / CLI 설치 상태를 모르므로 둘 다 지원.
  - C10.1 트리거 표의 "MINOR / MAJOR 증분 직전" 행을 "MINOR / MAJOR commit +
    push 직후" 로 갱신. 비고에 v0.4.0 → v0.4.1, v0.5.0 → v0.5.1 패턴 박음.
    "본 C10 절차 자체를 도입/수정하는 PATCH" 행 신설 (C10.3 정합).
  - C10.2 절차를 5 → 6 단계로 재구성. 1번이 "commit + push", 2번이 "review-prompt
    전달 (SendUserFile + inline)", 3번이 "codex 클라우드 / 로컬 CLI 분기".
  - docs/REVIEW_PROMPT.md §3 위에 §3.0 codex 클라우드 절 신설. 두 패턴의 비교
    표 (codex 가 코드를 읽는 위치 / 전제) + 클라우드 패턴의 장단점 명시. 기존
    Windows cmd / Linux 절은 "로컬 codex CLI (폴백)" 으로 재라벨.
  - 두 문서의 YAML 헤더 last_synced_with v0.3.4 → v0.5.1.
- **결과**:
  - 본 PATCH 는 문서 변경만. 코드 / 스키마 / 테스트 영향 없음.
  - CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (본 절차 자체의 수정 PATCH).
  - 다음 MINOR/MAJOR commit (v0.5.2+ 또는 v0.6.0+) 부터 본 절차 적용.
- **연관**: v0.4.0 → v0.4.1 (본 패턴의 첫 사례, 당시는 규칙에 박혀있지 않음),
  v0.5.0 (본 PATCH 의 트리거 — push 직후 review-prompt 전달 실패 사고).

## 2026-05-22 v0.5.2 — codex 1차 리뷰 흡수 (SourceCollectorWorker) + C10 전달 형태 강제

- **무엇을**: v0.5.0 의 codex 외부 1차 리뷰 결과 (Critical 2 / High 3 / Medium 3 /
  Low 2) 를 흡수하고, 본 절차 자체의 사용자 워크플로우 적합성을 v0.5.1 에 이어
  한 번 더 박음 (CLAUDE.md C10.5 신설). worker / planner / tests 의 4 갈래
  robustness 갭을 메움. VERSION 0.5.1 → 0.5.2.
- **왜**: v0.5.0 PATCH 의 4 갈래 갭과 v0.5.0/v0.5.1 운용 사고를 한 번에 정리.
  (1) `task_id_for` 가 sanitization 없이 prefix 만 붙여 contract drift 가능
  했음 → planner 단 fail-fast. (2) LLM 응답의 echo 식별자 (project_id /
  task_id / input_item_id) 검증 부재 → cross-task contamination 위험.
  (3) `_find_decision` 의 duplicate first-match-wins silent 동작 → 명시적
  ValueError. (4) `build_user_prompt` 의 raise 가 run() 안에서 catch 안 되어
  task_result.json 추적성 손실 가능 → preflight 흐름으로 catch. 추가로
  v0.5.1 에서 잠시 박았던 "SendUserFile + inline 동시 노출" 규칙은 사용자가
  중복 거추장스럽다 거부 → C10.5 의 크기 분기표로 교체. v0.5.0 의 codex 클라우드
  fetch 실패 (HTTP 403) 사고를 반영해 "신규 파일 inline 박는다" 를 디폴트로 승격.
- **어떻게**:
  - **Critical 1**: `source_collection_planner.task_id_for` 가 item_id 자체에
    `/`, `\\`, `..` 토큰 검사 + candidate 의 `_is_safe_path_segment` 검증. 양쪽
    위반 모두 ValueError. (단순 prefix concatenation 만 하던 v0.5.0 → planner
    단 fail-fast.)
  - **Critical 2**: `SourceCollectorWorker.run` override. `BaseLLMWorker.run`
    호출 후, output 을 다시 읽어 partial.project_id / task_id / input_item_id
    가 task 와 일치하는지 검증. 불일치 시 status=FAILED + errors 에
    `identity_mismatch:<field>` 추가. base 코드는 안 건드림.
  - **High 1**: `_find_decision` 을 0/1/many 분기로 재작성. matches 가 2+ 이면
    ValueError.
  - **High 2**: `_preflight_validate` 헬퍼 신설. `build_user_prompt` 가 호출하던
    검증을 분리해 `run()` override 가 LLM 호출 전에 직접 호출 → ValueError /
    FileNotFoundError 잡아 TaskResult(FAILED) 변환. LLM 호출 비용 절감 + 추적성
    보장.
  - **High 3**: tests 의 `_argv_get_option(cmd, name)` 헬퍼 신설. `--name value`
    와 `--name=value` 두 형태 모두 인식. 기존 index-based 검증 교체.
  - **Medium**: unused `import json` 제거. `mode == mixed and not
    ai_delegate_remaining` 도 `_preflight_validate` 에서 reject. SourceEntry
    전체 16 필드 prompt 정합 회귀. 80 KB user_note boundary 회귀.
  - **Low**: planner 의 `Optional[set[str]]` → `set[str] | None`. system_prompt
    의 `%TEMP% (Unix /tmp)` → "OS 임시 디렉토리 (Windows `%TEMP%`, Unix `/tmp`)".
  - **규칙 강화**: CLAUDE.md C10.0 의 AI 책임에 (d) 신설 — "codex 환경이 GitHub
    fetch 못 할 가능성을 디폴트로 가정하고 신규/변경 파일 본문을 review-prompt
    안에 inline (`### FILE: <path>` 헤더 구분) 으로 함께 박는다". v0.5.0 세션의
    HTTP 403 / outbound 차단 사고 반영. C10.5 신설 — 본문 크기 (≤ 30 KB inline
    단독 / > 30 KB SendUserFile 단독) 분기표 + 4 가지 금지 형태 (동시 노출 /
    SendUserFile-단독-with-작은-본문 / 코드블록 분할 / 머신 경로 placeholder
    노출) 를 v0.5.0/v0.5.1 운용 사고 사례와 함께 명문화. C10.2 절차 본문도
    inline 박는 의무 반복 명시.
- **결과**:
  - py_compile 통과 (수정된 3 파일).
  - 전체 unittest = **148/148 통과** (직전 129 + 신규 19).
  - 본 PATCH 는 CLAUDE.md C10.3 에 따라 codex 재리뷰 면제 (외부 리뷰 결과 흡수
    PATCH + 본 절차 자체의 수정 PATCH 의 합집합 면제).
- **연관**: v0.5.0 (본 흡수의 대상), v0.5.1 (전달 형태 규칙의 첫 시도 — "inline +
  SendUserFile 동시 노출" 은 본 PATCH 에서 폐기), LLM-AP-003 (codex agent 모드
  worker 의 첫 호출자가 본 PATCH 로 production-ready 한 상태로 진입), codex 1차
  리뷰 결과 (Critical 2 / High 3 / Medium 3 / Low 2 / Nit 5 — Nit 5 개는 모두
  OK 평가라 흡수 불필요).

---

## 2026-05-23 v0.5.3 — Phase 5 둘째 PATCH: SourceRegistryBuilder 도입

- **무엇을**: `02_sources/partials/*.json` 의 `SourceCollectionPartial[]` 을
  합쳐 정식 `SourceRegistry` 를 생성하는 순수 함수 빌더 모듈 도입
  (`orchestrator/source_registry_builder.py`) + 단위 테스트 19 케이스
  (`tests/test_source_registry_builder.py`).
- **왜**: 직전 PATCH (v0.5.0 / v0.5.2) 에서 명시적으로 deferred 한 §3 표 1 번
  항목. partial 들이 "효용을 발생시키는 지점" — 빌더가 없으면 partials/*.json
  은 단순 산출물 더미. Phase 5 의 e2e 흐름 (intake → planner → worker →
  partials → registry) 의 마지막 한 단을 닫음. 가장 작고 위험 적은 항목부터
  진입 (순수 함수 + Pydantic 합성, 디스크 I/O / 네트워크 / LLM 호출 없음).
- **어떻게**:
  - **fail-fast 정책**: 사용자 확정. 조용히 dedup / merge 하지 않고 raise.
    근거: LLM-AP-003 (echo identifier) 의 production 사용자인
    SourceCollectorWorker 가 발급한 source_id 가 task 단위로 고유해야 하므로,
    충돌 자체가 worker / planner 단의 버그 신호이거나 buggy upstream 의 사고.
    조용히 dedupe 하면 무결성 사고가 은폐된다.
  - **다섯 가지 invariant**:
    1. cross-partial source_id 충돌 → raise
    2. cross-partial input_item_id 충돌 → raise (한 input_item_id 는 한
       partial, planner / task_queue idempotency 검증)
    3. intra-partial source_id 중복 → raise (Pydantic 가 list uniqueness 강제
       안 함, builder 진입 전 검증)
    4. schema_version 불일치 → raise
    5. project_id 불일치 → raise
  - **빈 partial 처리**: `collected_sources` 가 빈 partial 은 통계
    (`empty_partial_count`) 에만 +1, `sources` 에는 기여 없음. "collector 가
    실행됐으나 후보 없음" 을 구분 가능하게.
  - **머지 정책은 docstring 으로만 명문화** (raise 정책상 dead path, 향후
    dedupe 모드 도입 시 재사용 대비):
    - rights: `do_not_use > review_required > rights_unknown > rights_clear`
    - verification: `disputed > unverified > cross_checked > official`
      (의심 우선 — official 이 가장 낮은 우선순위 = 분쟁 시 보수적 강등)
    - reliability_score: min(a, b)
    - risk_flags / usage_plan: 순서 보존 합집합
  - **`partial_counter`** 보조 함수: 호출자 (후속 v0.5.4 CLI / orchestrator)
    가 로그·검증에 사용. partial_count / empty_partial_count / source_count.
  - **테스트 19 케이스**: happy path 8 (빈 입력, 단일 partial, 다수 partial
    순서 보존, 빈 partial 통계 반영, input_item_id=None 허용,
    schema_version 일치, 필드 통과) + 충돌 / 무결성 5 (cross source_id /
    cross input_item_id / intra source_id / project_id / schema_version) +
    counter 3 + 충돌 검출 순서 1 + 보조 케이스 2.
  - VERSION 0.5.2 → 0.5.3. `__version__` 은 SSOT (VERSION) 에서 자동 갱신.
  - CHANGELOG / DEVLOG `last_synced_with: v1.1.0`.
- **결과**:
  - py_compile 통과.
  - 전체 unittest = **167/167 통과** (직전 148 + 신규 19).
  - 본 PATCH 는 CLAUDE.md C10.1 의 "새 도메인 컴포넌트 도입 PATCH" 카테고리
    (권장, 의무 아님). 실 codex e2e 와 후속 v0.5.4 (task_queue.json 영속화
    CLI — MINOR 트리거) 전 한 번 더 정합성 검토 권장.
- **연관**: v0.5.0 (본 PATCH 가 닫는 partial 산출 흐름의 시작), v0.5.2 (planner
  단 fail-fast 패턴 — 본 PATCH 의 builder 단 fail-fast 와 일관), LLM-AP-003
  (echo identifier 무결성 — cross/intra source_id 충돌 검증의 근거), §3 후속
  PATCH 표 2 번 (task_queue.json 영속화 + CLI, v0.5.4 MINOR) — 본 PATCH 이
  후 진입.

---

## 2026-06-08 v0.34.13 — OSINT 시네마틱 브리핑 컴포지션 신규 (영상미 C0, 과거 미감 비상속)

- **무엇을**: `hyperframes/briefing/` 신규 컴포지션. agents_reviewer report_bundle
  (`midnight_indigo` 테마) 데이터를 100% 적용한 60초 6씬 GSAP 영상 HTML. 기존
  `hyperframes/demo`(베이지/캔들) 미감을 1도 상속하지 않고 전면 재설계.
- **왜**: 사용자 요청 — 영상미를 완전·전면 재설계하고, 차트/도식을 정적 이미지가
  아니라 원본 데이터에서 영상용으로 재렌더(C0). gsap-skills/taste-skill 류의 프로
  애니메이션·고급 미감 지향.
- **어떻게**: 단일 마스터 타임라인(`window.__timelines["briefing"]`, demo 패턴) +
  6씬(타이틀/에스컬레이션 사다리/5행위자 네트워크/3좌표 지도+미사일 아크/시장
  스파크라인/클로징). 모든 씬을 BUNDLE 임베드 데이터에서 JS로 결정론적 빌드.
  SplitText/MotionPath 플러그인 없이 코어 GSAP 3.15 + 직접 글자분할·이차베지어
  비행으로 구현. 권리/정확성(C9): 시나리오(가상) 라벨 + `<미검증>` 원칙 명시.
- **결과**: Playwright(chromium 1194)로 6씬 12프레임 시킹 렌더 검수 — pageerror 0,
  자막·차트·아크·카운터 정상. 영상미 확인.
- **연관**: C0(영상미 최우선), C9(권리/미검증 라벨), 기준 bundle
  analysis_20260608_065042. 검증 함정: Playwright `evaluate(()=>tl.time(t))` 가
  GSAP 타임라인 객체를 반환→직렬화 무한 대기. 블록바디로 undefined 반환해 해소.

---

## 2026-06-11 v0.35.0 — SceneKit 엔진 리팩토링 (브리핑 HTML 엔진 전면 개선, 영상미 C0)

- **무엇을**: ZE 브랜치(claude/keen-fermi-ZEY1R, v0.34.13)의 `hyperframes/briefing/`
  을 머지한 뒤, 일회성 하드코딩 레이아웃을 `assets/scene_kit.js` (SceneKit 엔진)
  기반 데이터 주도 빌드로 전면 리팩토링. VERSION 0.34.13 → 0.35.0 (MINOR — 새
  엔진 레이어 도입).
- **왜**: 사용자 보고 — "html 엔진이 너무 취약하고 구려. 글씨나 마킹이 서로 막
  겹치고 줄 위로 글씨가 있고 어디에 내놓을 수가 없어." 실측(Playwright 시킹
  스크린샷)으로 확인된 결함: S2 사다리 상단 3개 스텝 라벨 상호 겹침 + 날짜/라벨이
  연결선 위에 얹힘 + 씬번호 "02" 와 충돌, S3 범례·씬번호 겹침 + 노드 원 밖 글자
  넘침, S4 인접 마커 라벨 완전 겹침 + 점선 아크가 글자 관통 + 보조 아크 라벨
  미렌더(데이터에만 존재), S6 인용문 단어 중간 줄바꿈("명/분").
- **어떻게**:
  - **SceneKit 엔진** (`hyperframes/briefing/assets/scene_kit.js`): ① 안전영역
    밴드(LAYOUT: 헤더 150~268 / 스테이지 268~866 / 자막 866~) + 씬번호 장식
    영역을 장애물로 선등록한 `stageField()`. ② 결정론적 텍스트 폭 추정
    (`estTextWidth` — 폰트 로드 타이밍 무관 → 시킹 렌더 안전, canvas 측정 대신
    코드포인트 가중치). ③ `LabelField` 충돌 회피 배치기 — 선분/베지어 샘플링
    장애물 + 4방 후보 슬롯 + 수직 밀어내기 탐색, 배치 후 자기 자신도 장애물로
    등록해 라벨 간 겹침 원천 차단. ④ `plateLabel` 반투명 플레이트 + 자동 줄바꿈
    멀티라인 라벨. ⑤ `leader` 마커↔플레이트 리더선. ⑥ `prepDraw` —
    getTotalLength 실측 draw-on (하드코딩 dasharray 4000/3000/2000 제거).
    ⑦ `splitChars` 단어 span 래핑 (keep-all 보존). ⑧ 씬 빌더 4종:
    buildStepTimeline / buildNetwork(라벨 폭 기반 노드 반지름 + 링크 가장자리
    트리밍) / buildGeoScene(마커+아크+아크라벨 통합 충돌장) / buildMarketCards.
  - **index.html**: 모든 씬을 BUNDLE 데이터 → SceneKit 빌더로 구성. 미사일 도착
    임팩트 링, 자막 하단 스크림, 마켓 카드 kind 태그(상승/변동/보합) 추가.
    엔진 계약 유지 (window.__timelines["briefing"], 결정론, 로컬 GSAP).
  - agents_reviewer 차트 보강은 참고만 — 영상 맥락(타임라인 시킹·결정론·
    브로드캐스트 안전영역)에 맞춘 독자 설계 (사용자 지시).
- **결과**: Playwright(chromium 1194) 시킹 11프레임 + 자동 감사(플레이트 쌍별
  겹침 / 스테이지 밴드 위반) — pageerror 0, 겹침 0, 위반 0. 씬별 스크린샷 검수
  (전/후 비교) 통과.
- **연관**: C0(영상미 최우선), v0.34.13(리팩토링 대상), NEXT_SESSION_PROMPT 옵션
  B/C 의 토대(차트 컴포넌트화·번들 자동 변환이 본 엔진 프리미티브 위에 올라감).
  검증 함정: Edit 도구가 NBSP(글자 span 공백) 매칭 실패 — 라인 단위 python 치환
  으로 우회.

---

## 2026-06-11 v0.35.0 후속 — codex 외부 리뷰 생략 (사용자 결정)

- v0.35.0 (MINOR) 의 C10 외부 코드 리뷰는 **사용자 명시 지시로 생략**
  (C10.0 사용자 책임 (c) "절차 자체에 대한 결정"). review-prompt.txt 는
  전달 완료된 상태였음. 코드 변경 없음.

---

## 2026-06-11 v0.35.1 — 키 플레이어 씬 신규 (SceneKit 엔진 첫 확장 검증)

- **무엇을**: SceneKit 에 씬 빌더 ⑤ `buildProfileCards` 추가 + 브리핑에 S4
  "키 플레이어" 씬 삽입 (60초 6씬 → 72초 7씬). VERSION 0.35.0 → 0.35.1.
- **왜**: 사용자 요청 "씬을 한번 만들어봐" — v0.35.0 엔진이 새 씬 타입을 실제로
  받아내는지 검증 + NEXT_SESSION_PROMPT 옵션 D (인물 카드) 첫 단 착수.
- **어떻게**: 카드 = 모노그램(이니셜) + 컬러 링 draw-on (prepDraw 재사용) +
  핵심 행동 라인 + 입장 게이지 (자제↔확전 스펙트럼 트랙 위 행위자 dot 슬라이드,
  "분석 추정" 태그 명시 — C0 경계: 추정과 사실 구분). C9: 인물 사진/AI 이미지
  대신 모노그램이 권리 안전 기본값. 지도/마켓/클로징 씬·cue +12s 시프트
  (브리핑 narration mp3 미생성이라 sync 부채 없음). 씬 번호 05/06/07 재번호.
- **결과**: Playwright 시킹 15프레임 + 플레이트 겹침/밴드 감사 — pageerror 0,
  겹침 0, 위반 0. 4카드 스태거 진입 + 링 draw + 게이지 dot 슬라이드 정상.
- **연관**: v0.35.0 (엔진), NEXT_SESSION_PROMPT 옵션 D, C9 (권리), C10 은
  사용자 지시로 생략 유지 (PATCH 카테고리 — 권장 항목).

---

## 2026-06-11 v0.35.2 — ink & brass 에디토리얼 테마 (AI-dashboard 미감 폐기)

- **무엇을**: 브리핑 컴포지션 비주얼 테마 전면 교체 + SceneKit 색 토큰화.
  VERSION 0.35.1 → 0.35.2.
- **왜**: 사용자 피드백 — "컬러감과 테마를 더 고급지게. AI vibe가 너무 많이
  느껴져서 정성이 들어갔다는 느낌이 들지 않는다." 기존 midnight_indigo 는
  네이비 + 파란 글로우 + 블롭 + 그리드 + 글래스 카드라는 전형적 AI 대시보드
  문법이었음.
- **어떻게**: ① 팔레트 — 잉크 차콜(#121214) + 브라스(#c4a265) 단일 액센트 +
  옥사이드(#b25450)/세이지(#7d9b76)/슬레이트(#8d99ae)/시에나(#b07a4a) 뮤트
  데이터 컬러. 글로우/박스섀도 액센트 전부 제거, 헤어라인 룰 추가.
  ② 타이포 — Noto Serif KR 가변(구글 폰트 124 유니코드 서브셋, 6.3MB 로컬
  내장 + 로컬 url 재작성 CSS) 을 헤드라인/씬 타이틀/인용/씬번호/모노그램에.
  데이터 라벨은 Pretendard 산세리프 유지 (가독). ③ SceneKit 의 SVG 하드코딩
  색을 CSS 변수(--sk-ink/--sk-node-fill/--sk-grid/--sk-region/--sk-text/
  --sk-muted/--sk-dim/--sk-hairline, 폴백 포함) 로 분리 — 엔진 테마 독립.
  플레이트 rx 10→4 (샤프 에디토리얼).
- **결과**: Playwright 시킹 15프레임 + 겹침/밴드 감사 클린. 7씬 전부
  스크린샷 검수 — 세리프 디스플레이 + 브라스 액센트 정상 렌더.
- **연관**: C0 (영상미), v0.33.0 의 "Aurora glass 촌스러움" 피드백과 같은
  계열의 사용자 미감 결정. 폰트 서브셋 내장은 결정론 렌더 (오프라인) 전제.

---

## 2026-06-11 v0.35.3 — 실측 지도 중심 재구성 + 국기/인물 노드 (날리지식 패턴 ③⑤)

- **무엇을**: S3(행위자 네트워크)·S5(지오 씬)를 실제 중동 지도 중심으로 재구성,
  노드를 원형 국기 배지로 교체. VERSION 0.35.2 → 0.35.3.
- **왜**: 사용자 요청 + 레퍼런스 이미지(날리지식 채널 스타일 — 실측 지도 풀블리드
  + 원형 국기 배지 + 인물 사진 카드 + 이름 플레이트). "actor network 와
  geospatial chain 은 지도가 중심적으로 나와야" + "노드는 국기나 인물 사진".
- **어떻게**: ① world-atlas 50m → 메르카토르 사전 계산 생성기
  (`build_mideast_map.mjs`, 재현 가능) → 52KB 정적 JS. 런타임 라이브러리 0
  (HyperFrames 결정론 계약). ② buildBasemap — 잉크 톤 지형 + 당사국(이란/레바논/
  이스라엘) 하이라이트 + 상단 페이드 마스크. ③ buildNetwork 재작성 — anchor 가
  있으면 노드 원을 앵커 주위 충돌 회피 배치(LabelField), 앵커 점 + 점선 리더,
  원형 클립 국기 이미지(slice) + 잉크 톤 오버레이, 이름 플레이트 분리. 미국은
  지도 밖(동지중해 상공) 고정 노드. ④ 국기: flagcdn·위키미디어가 outbound
  allowlist 차단 → npm `flag-icons`(MIT) 로 우회 확보. 인물 사진(트럼프 공식
  초상, PD)은 차단으로 보류 — RIGHTS.md 에 교체 절차 명시 (C9). ⑤ 레이어 사고:
  scene-head 가 svg 보다 DOM 앞이라 베이스맵 육지가 타이틀 글자를 덮음 — 처음엔
  폰트 서브셋 누락으로 오판(document.fonts.check 전수 통과로 반증), scene-head
  z-index 상향 + 베이스맵 상단 마스크로 이중 방어.
- **결과**: 플레이트 겹침/밴드 감사 클린, pageerror 0. S3/S4/S5 스크린샷 검수
  통과. 베이루트·남레바논·예루살렘 앵커 밀집(35px 간격)도 노드 충돌 회피로 분산.
- **연관**: C0(영상미), C9(권리 — RIGHTS.md), 옵션 D/E, v0.35.0 엔진(LabelField
  재사용이 본 작업의 토대).

---

## 2026-06-11 v0.35.4 — 직각 연결선 + 흐름 펄스 + 국기 풀블리드

- **무엇을**: 네트워크 연결선을 라운드 코너 직각 라우팅(`orthoPath`)으로 교체,
  링크 위를 순환하는 흐름 펄스 추가, 국기 이미지를 노드/카드 도형에 꽉 채움.
  VERSION 0.35.3 → 0.35.4.
- **왜**: 사용자 요청 3건 — "연결선은 각진 부분에 라운드가 있는 직각 선으로
  (단정하게)", "선 위에서 하이라이팅 색이 이동하는 애니메이션 (영향 방향)",
  "국기/사진은 도형 안에 꽉 채워".
- **어떻게**: ① orthoPath — 주축(|dx| vs |dy|) 기준 H-V-H/V-H-V 엘보, 코너는
  Q 베지어 라운드(반경 16), 양 끝은 노드 반지름 stub. 짧은 구간은 직선 폴백.
  ② 흐름 펄스 — 링크와 같은 d 의 오버레이 path 에 dasharray "seg L",
  dashoffset L+seg → 0 tween (ease none, repeat 2) = 경로 1회 완주 × 3.
  마스터 타임라인 내 tween 이라 시킹/오프라인 렌더 안전. 타입별 밝은 색
  (LINK_FLOW). ③ 클립 r-1 + 오버레이 제거, pcard img 82px.
- **사고 기록**: 편집 스크립트 앞에 `pkill -f "hyperframes render"` 를 붙였다가
  pkill 이 자기 자신의 셸 command line 까지 매칭해 편집 전에 셸이 죽음(exit
  144). 편집 0건 적용 상태를 grep 으로 확인 후 pkill 없이 재실행. pkill -f
  는 self-match 위험 — 패턴에 자기 명령 문자열이 포함되지 않게 할 것.
- **결과**: 겹침/밴드 감사 클린, pageerror 0. 클로즈업 연속 프레임(25.6/26.4/
  27.2s)으로 펄스 세그먼트 이동 확인.
- **연관**: v0.35.3(지도 노드), C0. 사용자 레퍼런스(날리지식)의 단정한 연출 계열.

---

## 2026-06-11 v0.35.5 — 하이브리드 링크 라우팅 (근거리 직각 / 원거리 아치)

- **무엇을**: buildNetwork 링크 라우팅을 거리 기반 하이브리드로 — 근거리는
  orthoPath(라운드 직각), 장거리는 위쪽 아치(Q 베지어, bend = clamp(dist×0.16,
  56, 150)). 링크별 `curve` 오버라이드. 미국발 3개 링크 곡선 강제.
  VERSION 0.35.4 → 0.35.5.
- **왜**: 사용자 — "멀리서 지원하거나 영향을 주고받는 건 곡선으로 해도 돼.
  적절하게 판단해서 로직에 반영". 직각의 단정함(v0.35.4)과 원거리 투사의
  거리감을 의미 단위로 구분.
- **어떻게**: 거리 임계값(opts.curveDist, 기본 430px) 자동 판별 + lk.curve
  명시 오버라이드. 아치는 normal 방향을 항상 위로 정규화(투사 느낌), 양 끝은
  control point 방향으로 노드 반지름 stub. 흐름 펄스 오버레이는 동일 d 를
  공유하므로 변경 없음.
- **결과**: 감사 클린. 미국→이란/이스라엘/레바논 = 아치, 이란→이스라엘/
  헤즈볼라 = 거리 자동 아치, 헤즈볼라↔이스라엘/레바논 = 직각. 의미 가독 확인.
- **연관**: v0.35.4(직각 라우팅), C0.

---

## 2026-06-11 v0.35.6 — 링크 회피 라우팅 (국기·플레이트 간섭 제거)

- **무엇을**: 네트워크 링크가 다른 노드 원(국기)·이름 플레이트를 비켜 가도록
  후보 경로 탐색 추가. VERSION 0.35.5 → 0.35.6.
- **왜**: 사용자 보고 — 선이 국기 뒤로 지나가거나 가려짐. 링크가 노드 뒤
  레이어라 시각적으로 잘려 보였음.
- **어떻게**: buildNetwork 내부 순서 재배열 (노드→플레이트→링크). 링크별 후보:
  곡선 = bend {base,+45,+90,+140} × 방향 {위,아래}, 직각 = 엘보 frac
  {0.5,0.35,0.65,0.25,0.75} + 곡선 폴백. 각 후보를 22px 샘플링 →
  스테이지 밴드 검사 + 노드 히트(패딩 14)/플레이트 히트(패딩 6) 계수.
  노드·플레이트 클린 후보 우선, 없으면 노드 클린 후보. orthoPath 에 frac
  파라미터 추가. 흐름 펄스는 선택된 d 공유라 변경 없음.
- **결과**: 클로즈업 검수 — 미국→이란 아치가 레바논 플레이트 위로 상승 회피,
  이란→헤즈볼라가 국기 사이 통과, 간섭 0. 감사 클린.
- **연관**: v0.35.4/0.35.5 (라우팅 계열), LabelField 철학(충돌 회피)의 링크 확장.

---

## 2026-06-11 v0.36.0 — 번들→영상 자동 변환 1차 (옵션 C, 실 JSON 검증)

- **무엇을**: 사용자가 제공한 실제 agents_reviewer 번들
  (analysis_20260611_130642_9f7fbb749d, 반도체 분석, graphite_slate)로
  번들→컴포지션 변환기 1차 구현 + e2e 검증. VERSION 0.35.6 → 0.36.0 (MINOR).
- **왜**: 사용자 — "샘플 영상이 마음에 드는데, 정말 json 이 제공되었을 때
  그대로 작동되는지 보기 위함". 손으로 만든 데모가 아니라 데이터 주도
  파이프라인의 증명.
- **어떻게**: ① bundle_to_video.py (stdlib only, LLM 없음 — 결정론):
  headline greedy wrap(+마지막 줄 em) / timeline 13→7 샘플링(crack·present·
  future 우선, past 균등) / contradictions → versus 카드(조사 '은/는' 분리로
  진영·주장 추출, resolution 의 다수·소수 키워드로 stance) / line+strip 차트
  → 마켓 카드(첫값 대비 % 시리즈, pct·spread 로 kind 분류) / pull_quote
  숫자+단위 regex em / 출처 publisher 상위 3 + 외 N. ② auto_builder.js:
  BRIEFING_DATA 의 scenes[] 를 조건부 조립, data-duration 동적 주입,
  번들 테마 토큰 → CSS 변수. CSS 는 index.html <style> 블록 재사용.
  ③ 씬 부재 처리 검증: 본 번들은 map=None·행위자 없음 → 지도/네트워크 씬이
  생성되지 않음 (엔진의 올바른 동작).
- **결과**: scenes=[title, ladder, versus, markets, closing], 53초, cue 12개.
  플레이트 겹침/밴드 감사 클린, pageerror 0. 5씬 스크린샷 검수 — 헤드라인
  줄바꿈/강조, 타임라인 7분기점, 강세론(다수설) vs 보수론(소수설) 게이지,
  SK하이닉스 +119.1% 마켓 카드, 150조원 자동 강조 인용 + 신뢰도 0.38 모두
  번들 값 그대로.
- **C10**: MINOR 트리거이나 사용자의 세션 명시 지시("코드리뷰는 생략해")로
  생략. 차기 세션에서 필요 시 일괄 리뷰 권장.
- **남은 것 (옵션 C 2차+)**: cue 문장 품질(LLM 보강), candle/bar/slope 차트
  전용 씬, map 있는 번들에서 지오/네트워크 씬 자동 활성, narration 연동.
- **연관**: v0.35.x 전체(엔진·씬·테마가 본 변환의 토대), 옵션 C/G4(미검증
  라벨 — 출처 라인에 명시).

---

## 2026-06-11 v0.36.1 — 씬 라이브러리 확장 + 렌더러 빈 화면 사고 픽스 (RENDER-AP 후보)

- **무엇을**: 수평 축 타임라인/캔들/바 패널/시그널 씬 4종 추가, 타임라인 유형
  자동 선택, auto_builder 인라인화. 반도체 번들 자동 영상 5씬→9씬.
  VERSION 0.36.0 → 0.36.1.
- **왜**: 사용자 피드백 3건 — ① "너무 단조롭다, 화면 수가 적다" (번들 차트
  10개 중 7개를 미사용했음), ② "시계열마다 계단 모양이면 별로 — 유형 필요",
  ③ v0.36.0 렌더 mp4 가 빈 화면(408KB/63kbps).
- **어떻게**: ① buildAxisTimeline(수평 축) + timeline_kind 휴리스틱(crack+
  present 공존 = 에스컬레이션 서사 → 계단, 그 외 → 수평 축. 본 번들은 축).
  ② buildCandleChart/buildBarPanels + auto 씬 bars(단일+같은 단위 듀얼 자동
  묶음)/candle/signals. ③ **빈 화면 근본 원인**: hyperframes 렌더 세션이
  body 끝 외부 <script src> 를 실행하지 않음 — 정적 마크업만 보이고 JS 산출
  전부 부재. 로컬 Chromium 141 + 렌더러의 chrome-headless-shell 131 양쪽에서
  수동 검증 시 정상이라 페이지 문제 아님을 확정 후, 작동하는 index.html
  패턴(인라인 스크립트)과의 구조 차이로 격리. 변환기가 빌더를 인라인 주입.
- **사고 기록**: 듀얼 바 패널 cue 의 패널 혼합 비율(만원 단위 vs 만원 단위지만
  스케일 상이) 19.0배 — 시각 검수에서 포착, 패널별 비율로 교정. 자동 cue 는
  단위/스케일 경계를 넘는 집계 금지 원칙.
- **결과**: 9씬 89초, cue 19, 감사 클린. 캔들/바/시그널/수평축 스크린샷 검수.
- **연관**: v0.36.0(변환기 1차), C0, G4(<미검증> 태그 — 시그널 카드).

---

## 2026-06-11 v0.37.0 — 타임라인 5유형 + 테마 5종 + 슬로프/도넛/인용 (MINOR)

- **무엇을**: ① 타임라인 시각화 5유형(ladder/axis/serpentine/vertical/metro)
  + 데이터 성격 기반 자동 선택 휴리스틱 + CLI 오버라이드. ② 테마 시스템 —
  CSS 전면 토큰화(--plate-fill/--scrim-rgb/--cap-color 등 14토큰 신설) +
  themes.js 프리셋 5종(라이트 paper_oxblood 포함) + 번들 theme.id 자동 매칭 +
  의미색 런타임 파생. ③ 슬로프 씬(실데이터 ch-10)/도넛 빌더(하니스 검증)/
  인용 인터스티셜. VERSION 0.36.1 → 0.37.0 (MINOR — 씬·테마 라이브러리).
- **왜**: 사용자 — "타임라인 유형 5개, 컬러 테마 5개로 늘려라. 미개발 유형도
  개발해 둬라." + 직전 피드백(매번 계단이면 단조).
- **어떻게**: 자동 선택 — crack+present 공존=ladder(에스컬레이션), n≥11=
  serpentine, 평균 라벨 26자↑=vertical, 미래 비중 40%↑=metro, 그 외 axis.
  테마 — auto_builder 가 SK_THEMES[themeId].vars 적용 후 getComputedStyle 로
  accent/oxide/sage/slate/faint 를 읽어 phase/market/gradient 파생 (테마-의미색
  단일 출처). 라이트 테마는 scrim/cap/vignette/grain 토큰까지 오버라이드.
- **검증**: 본 번들로 5유형 × 5테마 매트릭스 스크린샷 (모두 감사 클린,
  pageerror 0). 도넛은 번들에 데이터가 없어 임시 하니스로 렌더 검증.
  디폴트 실행 = graphite_slate(번들 theme.id 매칭) + serpentine(13분기점) —
  11씬 106초 cue 22.
- **C10**: MINOR 트리거이나 사용자 세션 지시로 생략 유지.
- **연관**: v0.36.x(변환기), C0. 잔여: stacked/waterfall/scatter/heatmap/
  gantt 차트 씬, LLM cue 작문(옵션 C 2차), 도넛 실데이터 검증.

---

## 2026-06-12 v0.37.1 — 잔여 차트 유형 5종 (stacked/waterfall/scatter/heatmap/gantt)

- **무엇을**: SceneKit 차트 빌더 5종 + auto_builder 씬 타입 + 변환기 정규화기
  + `--preview-charts` 갤러리 픽스처. VERSION 0.37.0 → 0.37.1.
- **왜**: 사용자 — "잔여 차트유형을 먼저 만들자. 비주얼하게 잘". 옵션 B 의
  잔여분(스택/워터폴/스캐터/히트맵/간트). 현재 번들에는 해당 타입 실데이터가
  없어 합성 데이터 갤러리로 비주얼 검증, 변환기 매핑은 미리 연결 (해당 타입
  번들 도착 시 자동 씬 생성).
- **어떻게**: ① 빌더는 전부 테마 토큰 파생 색 + 기존 프리미티브 재사용
  (plateLabel/LabelField/prepDraw — 스캐터 포인트 라벨이 충돌 회피의 수혜).
  ② 정규화기는 스키마 미확정을 전제로 관용 파싱 (segments|parts|series,
  kind|type, dict|list 히트맵, 날짜 검증 후 간트) — 형식이 안 맞으면 씬 생략
  (조용한 실패 대신 콘솔 로그 없음·데이터 없음 = 씬 없음 원칙). ③ 애니메이션:
  스택 세그먼트 순차 성장(svgOrigin 기반 scaleX), 워터폴 컬럼 부유 상승 +
  커넥터 페이드, 스캐터 대각선 draw-on + 백아웃 팝, 히트맵 (행+열) 대각
  웨이브, 간트 막대 성장 + 오늘 라인.
- **결과**: 갤러리 5씬 45초 — 감사 클린, pageerror 0, 5씬 스크린샷 검수 통과.
- **연관**: v0.36.x(자동 변환), 옵션 B 완료에 근접 (남은 것: forecast 밴드,
  network 차트 — 번들 스키마 확정 시).

---

## 2026-06-12 v0.37.2 — 영상 필드 계약 초안 (agents_reviewer 전달)

- **무엇을**: docs/VIDEO_BUNDLE_CONTRACT.md 신설 + 사용자에게 agents_reviewer
  세션 전달용 프롬프트 작성. VERSION 0.37.1 → 0.37.2 (문서 PATCH).
- **왜**: cue LLM 대본화의 방식으로 사용자가 옵션 ③ 확정 — "보고서를 쓴
  LLM 이 영상 대본도 같이 쓴다". 부수 효과로 서술 전용 섹션(현 번들 s5/s6
  류)의 영상 누락도 해소됨 (highlights → 스테이트먼트 씬).
- **계약 요지**: sections[].video {narration ≤58자/문장, highlights ≤40자,
  emphasis 는 정확한 부분 문자열, narration_tts 선택} + report.video
  {intro/outro_narration}. 전부 optional (schema_version 1 유지). 사실 근거
  강제 — 영상 쪽 검증기가 수치·날짜·고유명사를 번들과 대조, 위반 문장은
  템플릿 폴백.
- **다음**: agents_reviewer 합의/샘플 번들 도착 → 영상 쪽 소비 구현
  (스테이트먼트 씬 + 검증기 + cue 교체) → 본 문서 "확정" 갱신.
- **연관**: 옵션 C 2차, G4 (사실 근거/미검증 라벨), v0.36.x 변환기.

---

## 2026-06-12 v0.38.0 — 계약 video 필드 소비 (스테이트먼트 씬 + 내레이션 + 검증기)

- **무엇을**: VIDEO_BUNDLE_CONTRACT 의 영상 쪽 의무 구현. SpaceX/구글 번들
  (analysis_20260606_114653, forest_sage)로 e2e 검증 — 12씬 118초.
  VERSION 0.37.2 → 0.38.0 (MINOR, C10 은 사용자 세션 지시로 생략 유지).
- **왜**: agents_reviewer 가 계약을 구현해 전 섹션 video(narration 4문장 +
  highlights 2 + emphasis + narration_tts 발음 분리)를 실어 보냄. 사용자 —
  "데이터 없는 씬 작업 반영, 내레이션 보완했다. 읽고 영상 만들어봐".
- **어떻게**: ① section_videos() — 수치 토큰 ⊂ 번들 직렬화 말뭉치 검증,
  위반 문장 폐기(이번 번들 0건). ② 씬에 _sid 연결 → 섹션 시간창 수집 →
  narration 균등 배치, 해당 창의 템플릿 cue 제거. intro/outro 는 타이틀/클로징
  창. ③ statement 씬 — 미소비 서술 섹션의 highlights 를 62px 세리프 순차
  등장(emphasis 액센트, 헤어라인 룰 분리). versus/signals 소비 섹션은 제외.
  ④ versus 진영명 "(A)인가, (B)인가" 패턴 추출 — "임대업" vs "궤도로 가는
  다리". ⑤ 간트 눈금 월/분기/연 자동(30.44일 환산 monthsSpan, ≤14/≤42/초과)
  + 기간 라벨 연도. 스캐터 눈금 범위≤8 → 소수 1자리.
- **검증**: 감사 클린, pageerror 0. 스테이트먼트/간트/스캐터/versus 스크린샷
  검수. 계약 narration 32문장 채택 로그 확인.
- **남은 것**: sankey 차트 (이번 번들 ch-8, 미지원 스킵 — 차기 차트 유형),
  cue.tts → build_narration 연동.
- **연관**: VIDEO_BUNDLE_CONTRACT(확정으로 갱신), G4, v0.36~37 변환기 계열.

---

## 2026-06-12 v0.38.1 — 내레이션 시계 (음성에 맞춘 화면 전환)

- **무엇을**: build_auto_narration.py + 변환기 --narration/--cuesync. 씬
  길이가 "해당 씬 내레이션 실측 길이 + 호흡(lead 1.1/pause 0.5/tail 1.3)"으로
  재계산되고, 자막은 문장이 말해지는 시각에 정확히 뜸. VERSION 0.38.0 → 0.38.1.
- **왜**: 사용자 — "나레이션이 들어가면 나레이션 소리에 맞춰 화면 전환이
  이뤄져?" 기존 고정 시계(문장 수 기반)는 음성과 무관했음.
- **사고/교훈 (RENDER 계열)**: 1차 구현은 목표 cue 시각을 먼저 정하고 무음으로
  갭을 채움 → mp3 프레임(26ms) 반올림이 60개 조각에 누적되어 **+2.86초
  드리프트** (요청 203.53 vs 실측 206.39). v0.34.8 의 교훈 그대로 — **실측이
  시계의 원천**이어야 함. 조각(무음/문장)별 probe 길이를 누적한 커서를 cue
  시각으로 삼는 방식으로 재작성 → 계산 207.02 = 실측 207.02 (드리프트 0).
- **환경 메모**: 본 클라우드 환경은 api.elevenlabs.io 가 egress allowlist 에
  없고 ELEVENLABS_API_KEY 도 없음 → --estimate 로 메커니즘만 e2e 검증.
  실합성은 ① 환경 설정에 host+key 추가 후 본 세션에서, 또는 ② 사용자 머신
  --narration=synth 한 줄.
- **연관**: v0.34.5~12 (demo 음성 파이프라인 — synth_one/write_silence/
  concat_mp3s 재사용), VIDEO_BUNDLE_CONTRACT (narration_tts 소비).

---

## 2026-06-12 v0.38.2 — 1차 음성 영상 검수 반영 (렌더링 측 B 패키지)

- **무엇을**: 검수 9건 중 렌더링 책임분 — 템플릿 cue 재작성+tts 자동 표기,
  날짜 발음(유월/시월), 고유어 수사, 조사 선택, 숨소리 후처리, 자막 75자+폰트
  축소, timeline.video 소비, 미니 캘린더. VERSION 0.38.1 → 0.38.2.
  대본 측 A 패키지는 사용자가 agents_reviewer 에 전달 (계약 개정).
- **사고 재발 방지 메모**: tts_of 1차 구현이 날짜를 "육 월 오 일"로 끊어 읽게
  만듦 — v0.34.12 에서 자동 변환 default OFF 한 바로 그 사고 유형. 월 이름
  사전(_MONTH_KR, 유월·시월 불규칙) + "N월 D일" 패턴 선처리로 해소. 템플릿
  처럼 형식을 아는 텍스트는 패턴 선처리가 정답이고, 임의 텍스트 자동 변환은
  여전히 위험(기존 결정 유지).
- **검증**: 감사 클린. cue tts 샘플 확인 — "일곱 개", "유월 오일에는",
  "구 점 이 억 딸러", "스페이스엑스". 캘린더 스크린샷 (월 전환 연출).
  숨소리 컷은 실합성에서만 검증 가능 — 사용자 재합성 시 확인 항목.
- **연관**: TTS-AP-054~057 계열, v0.34.8/12 교훈 재적용, VIDEO_BUNDLE_CONTRACT
  개정(75자/timeline.video — A 패키지).

---

## 2026-06-12 v0.38.3 — 억양 문맥 전달 (TTS-AP 계열)

- **무엇을**: synth_one 에 previous_text/next_text 추가, auto 내레이션이 앞뒤
  cue 를 전달. VERSION 0.38.2 → 0.38.3.
- **왜**: 사용자 — "평서문인데 끝을 올린다, 어떤 설정치를 조정해야 하나".
  진단: ElevenLabs 에 억양 직접 파라미터는 없음. ① stability↑/style↓ 가
  간접 레버, ② 더 큰 원인은 우리의 문장 낱개 합성 — 모델이 담화 위치를
  모른 채 억양 추측. API 의 request-stitching(previous/next_text)이 정답.
- **검증**: 코드 경로만 (실합성은 사용자 재합성 시 확인 — 2차 검수 항목).

---

## 2026-06-12 v0.38.4 — 계약 문서 개정판 동기화

- **무엇을**: VIDEO_BUNDLE_CONTRACT.md 를 1차 검수 합의 내용(75자, timeline.video,
  발음 강화)으로 갱신. VERSION 0.38.3 → 0.38.4 (문서 PATCH).
- **왜**: agents_reviewer 가 A 패키지 반영 완료 통지. 코드(v0.38.2~3)는 이미
  개정 스키마를 소비하는데 계약 문서가 구판(58자)이라 문서-코드 불일치 상태였음.
- **상태**: 양측 배포 완료 — 개정 번들 도착 시 즉시 맞물림. 2차 검수 항목:
  평서문 억양/숨소리/날짜 발음/캘린더 연출.

---

## 2026-06-13 v0.39.0 — 지도·관계망 자동 소비 (옵션 E 완성)

- **무엇을**: 번들 map → geo 씬, network 차트 → geonet 씬. 다권역 베이스맵
  생성기(투영 메타 분리로 파이썬-JS 이중 투영 일치). VERSION 0.38.4 → 0.39.0
  (MINOR, C10 은 사용자 세션 지시로 생략 유지).
- **왜**: 개정 계약 첫 번들이 동북아 지정학 보고서 — map·network 를 처음
  실어 옴. 이란 브리핑에서 수동 제작했던 두 씬의 자동화 완결.
- **설계 결정**: 투영 SSOT 는 생성기(d3) — JS 용 path 와 별개로 meta.json
  (k, translate, bbox) 을 내려 변환기가 동일 공식으로 마커를 투영. 권역
  선택은 데이터(마커 bbox) 기반 자동, 미지원 권역은 씬 생략 (조용한 강행
  대신 로그). 네트워크 레이아웃은 최다 연결 중심 + 원형 — 노드 원이 스테이지
  밴드를 침범하던 초기 반경(280)을 234 로 보정 (cy±(r+nodeR) ⊂ 밴드).
- **검증**: 12씬 125초, 계약 narration 26문장(템플릿 11건 대체), 감사 클린.
  동북아 지도(4도시+방북 아크+분석 추정 태그)·국기 관계망(북한 중심 6개국)·
  서펜타인(11분기점) 스크린샷 검수.
- **연관**: 옵션 E, VIDEO_BUNDLE_CONTRACT(map/network 는 기존 번들 필드 —
  계약 외 필드의 첫 소비), v0.35.x 엔진 재사용 (라우팅·회피·펄스 무수정).

---

## 2026-06-13 v0.39.1 — 2차 음성 검수 반영 (렌더링 측 B)

- **무엇을**: 동북아 영상 2차 검수의 렌더링 책임분 — tts_of 강화(ISO날짜·
  고유어수사·em대시·가운뎃점·화살괄호), josa, 논설체→경어체, sentences 분할
  버그, 스테이트먼트 씬 재디자인. VERSION 0.39.0 → 0.39.1.
- **사고 기록 (TTS-AP 계열)**: ① sentences() 가 `(?<=[.!?다])\s+` 로 바 "다 "
  ("침묵보다 더")를 문장 경계로 오인 → 절단 cue. 구두점 필수로 수정.
  ② to_polite 이중 적용 ("전환이다"→"입니다"→"입니습니다") — 카드 line 이
  이미 변환된 걸 cue 가 재변환. cue 는 변환된 값 직접 사용. ③ geo josa 의
  인라인 정규식 `(.*)` 가 전체 매칭 → 빈 문자열 → 조사 오류. norm_map 에서
  이미 괄호 제거하므로 note 직접 사용.
- **검증**: 감사 클린, cue 전수 확인 — 경어체·완결문장·고유어수사·날짜 한글
  전부 정상. 스테이트먼트 카드형 스크린샷 검수.
- **남은 것 (A 패키지)**: highlight 가 heading 을 메아리("묵인이냐 침묵이냐"),
  contradictions 논설체 원문(영상은 경어체 변환으로 임시 대응 — contradictions.
  video 신설이 근본), "장보고-엔" 번들 표기, 가운뎃점 "담화·김정은" 띄어쓰기.

---

## 2026-06-13 v0.40.0 — 자체 생성 BGM + 더킹 믹스

- **무엇을**: 외부 음원 없이 ffmpeg lavfi 로 앰비언트 베드 합성 + 사이드체인
  더킹. make_bgm.py + --bgm 플래그. VERSION 0.39.1 → 0.40.0 (MINOR).
- **왜**: 사용자 요청 — 라이브러리 음원 제시했으나 본 환경이 Pixabay/FreePD
  등 음악 CDN 을 차단(403). 사용자가 "생성" 선택. C9 권리 측면에서도 자체
  생성이 유튜브 Content-ID 안전.
- **설계**: Cm 화성(긴장/비장) + lowpass 540Hz(내레이션 1~4kHz 대역 비움) +
  사이드체인compress(threshold 0.03/ratio 8/release 400ms)로 말할 때 -21dB
  하강. 정적 드론 방지용 보이스별 독립 트레몰로(0.1~0.17Hz — ffmpeg tremolo
  최저 0.1Hz 제약 반영).
- **사고 메모**: tremolo f 최저 0.1Hz — 더 느린 LFO(0.05) 시 exit 222
  (out of range). 0.1+ 로 보정.
- **검증**: 베드 mean -43.9dB, 믹스 mean -21.5/max -4.1dB(무클리핑).
  실 내레이션(206s)에 믹스해 렌더 진행. 톤·음량 사용자 검수 대기.
- **남은 것**: 베드 화성/음량 파라미터 조정(사용자 피드백), 보고서 톤별
  BGM 변형(긴장↔중립) 가능성.

---

## 2026-06-13 v0.40.1 — BGM 무음 사고 픽스 (이중 감쇠)

- **무엇을**: duck_mix 의 고정 dB 곱(-21dB)을 loudnorm 정규화로 교체.
  VERSION 0.40.0 → 0.40.1.
- **사고**: 베드 생성 레벨이 -44dB(사인 mix + lowpass 손실)인데 더킹에서
  bed_db=-21 을 곱(×0.089) → -65dB 무음. "목표 음량을 곱으로 적용" 하려면
  소스가 0dBFS 라는 가정이 필요한데 베드는 이미 한참 아래였음. loudnorm
  (I=-23 LUFS)으로 절대 음량 타깃 → 생성 레벨 무관 일정 가청.
- **교훈**: 음량 타깃은 "곱(상대)"이 아니라 "정규화(절대 LUFS)"로. 소스 레벨이
  가변일 때 상대 dB 곱은 예측 불가.
- **검증**: 정적 구간 mean -32dB(가청), 전체 mean -20.8/max -4.2(무클리핑).
  재렌더 진행.

---

## 2026-06-13 v0.40.2 — BGM 외부 음원 모드 (합성 폐기, 라이선스 음원 기본)

- **무엇을**: --bgm 을 경로 인자로 확장. 외부 음악을 루프/트림/페이드 후
  더킹. VERSION 0.40.1 → 0.40.2.
- **왜**: 사용자 — 합성 사인 베드는 "기계음, 높낮이 없음". ffmpeg 사인 합성의
  근본 한계(음색·멜로디·진행 부재) 인정. YouTube 오디오 보관함 등 라이선스
  음원이 정답. 사용자가 "Between The Spaces" 선택.
- **흐름**: 음악 사이트가 본 환경 차단 → 사용자가 음원 다운로드 →
  assets/audio/bgm/ 에 넣고 push → 클라우드에서 더킹 믹스 + 재렌더 (내레이션
  불변이라 재합성 불필요). 음악 파일은 .gitignore(C9), RIGHTS.md 추적.
- **교훈**: 코드로 만들 수 있는 것과 없는 것의 경계 — 음악은 합성 대상이
  아니라 소싱 대상. 시도는 가치 있었으나(권리·결정론) 품질이 영역 밖.

---

## 2026-06-13 v0.40.3 — 외부 BGM 적용 (Zabriskie, CC BY)

- **무엇을**: 사용자 선택곡으로 조용한 더킹 믹스 + 출처 표시. VERSION 0.40.2
  → 0.40.3.
- **음량 결정**: "조용히 엠비언트처럼만" → bed_lufs=-30 (내레이션 -21 대비
  -9dB). 곡이 성긴 피아노라 도입부는 거의 무음(페이드인+공백) — 의도된 은은함.
- **권리(C9/G4)**: CC BY 4.0 은 출처표시 의무 — 영상 하단 + 유튜브 설명란 둘
  다 필요. RIGHTS.md 에 작가 표준 표기 명시.
- **repo 위생**: 음악 파일은 .gitignore 대상인데 전달 위해 -f 로 커밋됨(100MB).
  미사용 2곡 untrack + 삭제. history 정리/LFS 는 운영 안정 후 과제로 기록.
- **사고**: 사용자의 첫 git add 가 공백 파일명 + glob 미스로 실패 반복 →
  결국 이전 스테이징분이 3곡 전부 커밋됨. 권리·용량상 1곡만 유지가 맞아 정리.

---

## 2026-06-13 v0.40.4 — 자막↔출처 겹침 + "물러설 한계선" 안전망

- **무엇을**: 출처 라인 하단 이동(겹침 해소), 번들 narration 비문 자동 보정.
  VERSION 0.40.3 → 0.40.4.
- **"왜 자꾸 살아나나"**: 해당 어구는 번들 sections[].video.narration 원문
  (agents_reviewer A측). 우리는 대본을 충실히 소비하므로 매번 등장. A 에 1차
  전달했으나 본 번들 미반영 → B 측 fix_phrasing 안전망 추가. 음성은 이미 합성된
  것이라 자막만 즉시 교정, 음성 일치는 다음 재합성.
- **검증**: Playwright bbox — 자막 하단 979 < 출처 상단 1015 (겹침 없음).
  자막 텍스트 "물러설 수 없는 한계선" 확인.

---

## 2026-06-13 v0.40.5 — 3차 검수(톤끕/AUKUS) + BGM·크레딧 파이프라인 일원화

- **무엇을**: 톤급→톤끕, 오커스→AUKUS(표기)/오커스(음성), 전 cue tts 사전
  최종패스. --bgm 경로 전달 + --music-credit. VERSION 0.40.4 → 0.40.5.
- **핵심**: 계약 narration_tts 가 사전을 안 거쳐 톤급/AUKUS 미보정이었음 →
  전 cue tts 에 apply_pronunciation 최종패스(멱등). 음성 반영은 재합성 필요.
- **사고**: --narration=estimate 검증 실행이 진짜 synth cuesync(206s)를 추정
  값(230s)으로 덮음 → git checkout 복구. 검증은 estimate 가 cuesync 를
  덮어쓰지 않는 임시 경로로 했어야. (추후: estimate 출력 분리 고려.)
- **다음**: 사용자 재합성(--narration=synth --bgm=<곡> --music-credit) 1회 →
  음성까지 전 검수 반영 → 렌더.

---

## 2026-07-12 v0.43.4 — 실합성 검수 2차: 숫자 연음·소수점·절단·티커·BGM (TTS-AP-058~063)

- 무엇을: SK하이닉스 뉴욕 상장 브리핑 첫 유성 렌더를 사용자가 듣고 지적한 6건을
  구조적으로 잠금. (1) 숫자 음절 공백 제거(연음), (2) 소수점 "쩜" 무공백, (3) 절단
  "…" 음성 유입 차단(자막↔음성 분리), (4) 슬래시날짜·중복날짜·영문티커 정리,
  (5) 경어체 규칙 순서 버그, (6) BGM 누락(재합성에 --bgm 상시).
- 왜: ElevenLabs 는 공백에서 국어 연음을 끊는다 — "백 육 십 팔"[배규씹팔] vs
  "백육십팔"[뱅뉵씹팔]. 소수점 " 점 " 공백은 반박자 쉼. clip() 의 "…" 를 음성이
  삼켜 말이 중간에 끊김. 신호명 "7/13 SKHY …" 는 슬래시·중복날짜·티커를 그대로 낭독.
- 어떻게:
  - `tts_pronounce.num_to_sino_kr`: 한 숫자 내부 음절 `"".join` (공백 제거). 단위어
    경계 공백만 유지. 회귀 테스트 단언 붙임으로 갱신.
  - `bundle_to_video.tts_of`: `_decimal_tts`(168.49→백육십팔쩜사구),
    `_slash_date_tts`(7/13→칠월 십삼일, 분기 제외), "…"/접속꼬리 제거. 계약
    narration_tts 경로도 `apply_pronunciation` 단독 → `tts_of` 승격(멱등).
  - `build_signals`: `_strip_lead_date` + `name_spoken`(첫 절). versus/signals cue 는
    자막=절단, 음성=완결 문장(`tcue(tts=...)`).
  - `_POLITE_TAIL`: 일반 폴백을 리스트 끝으로 (본다→봅니다 복구) + 하다→합니다.
  - `pronounce.json`: SKHY/SKHYV/SKUU/SKDD/ETF/ADR/HBM/TSMC 매핑.
- 결과: 단위 테스트 355/355 통과. 재합성(--bgm Zabriskie) → 재렌더로 음성 반영.
- 연관: TTS-AP-058, 059, 060, 061, 062, 063. C0(영상미)·C6(안티패턴)·C9(BGM 권리).

## 2026-09-28 v3.0.0 — Phase 6.8 오케스트레이터 통합

- 무엇을: 상태 머신 16 §2 교체(manifest v2), engine_service 어댑터, 승인 게이트 2개, ScriptWorker→Script(라벨은 코드), preview provenance, tts_lint·tts_pronounce 병합 삭제, Command Center e2e(hormuz CREATED→DONE, final.mp4 = CLI 직접 바이트 동일).
- 왜:    D-0040(16 전체). xfail 2 → 0.
- 교훈:  Commons 원본(webm) 요청이 환경 egress 단위로 429 차단 — 한 번 받은 원본은 artifacts 에 보존하고(D-0044 B) 1차 출처 대체 경로를 레지스트리에 둔다(D43, source_variants). tts 캐시도 artifacts 에 보존해야 새 컨테이너에서 바이트 동일 대조가 된다(D-0042).

## 2026-09-28 v3.1.0 — Phase 6.9 선언형 연출·결정적 검사·AI 연출 루프

- 무엇을: direction.py → direction.yaml(코드 실행 0), 배치 슬롯, checks.json 10항목(hard → preview 실패), 연출가·시각 검수·연출 수정 워커와 루프(최선 판 선택·게이트 ② 판 목록), provenance ai_direction. hormuz_ai 원고만으로 AI 연출 실증 2회.
- 왜:    D-0047(17 전체)·D-0048·D-0049.
- 교훈:  LLM 단계를 실제로 돌려야 계약 버그가 보인다 — 스텁 테스트 전부 통과 상태에서 실측 버그 5건(PIPELINE-AP-007·008, LLM-AP-007, RENDER-AP-003, latest() 번호). 검사용 상자를 렌더 예약 영역과 공유하면 골든이 바뀐다 — 렌더 공용 함수 변경 뒤엔 golden_compare.

## 2026-09-29 v4.0.0 — Phase 11 문서·정리·GOAL G3 개정

- 무엇을: GOAL G3 v2(17개 + 검증 방법 열, 옛 34개 legacy 절), docs/07·08·09·10 재작성(규칙 키 안내도), 12·03·05 와 나머지 Tier 2 동기화, 폐기 문서·v1 잔재 코드 삭제(ADDENDUM_02·RUN_LOCAL·docs/11·tts_backends·ApprovalLog·ThumbnailManifest·agents/), test_goal_g3·test_docs_sync, PIPELINE-AP-010.
- 왜:    D-0072·D-0073(D4·D64).
- 교훈:  문서가 수치를 복사하면 규칙이 바뀔 때 조용히 틀린다 — 문서는 `rules:키` 로만 가리키고 테스트가 키 존재를 대조한다. 긴 실행 중 트리 수정 금지(PIPELINE-AP-010).

## 2026-09-29 v4.1.0 — 국가 지오메트리 키 충돌 수정(카자흐스탄 소실, D-0078)

- **무엇을**: `load_countries` 같은 ISO 키 피처 합집합, 면적 커버리지 검사(`rules geo.land_fill_min_ratio`), 지오 자산·골든 25장 재생성.
- **왜**: 사용자 보고 — 랫클리프 모스크바 컷에서 카자흐스탄이 바다로 그려짐. hormuz 골든에도 같은 결함(KZ·AU 조각).
- **결과**: KZ 329 deg²(hormuz)·면적 비율 1.0, 옛 덮어쓰기 재현에서 KZ 0.012·AU 0.0 → drops. PIPELINE-AP-011.

## 2026-09-29 v4.1.0 — Phase G1 무대 추상화

- **무엇을**: `engine/stage.py`(Stage 프로토콜·MercatorStage·StageSet), `View(stage, cam)` 월드 좌표, direction `stage`·`shots[].stage`, 결정적 검사 `stage_continuity`(13항목), 무대 격리 AST 테스트.
- **왜**: handoff 20 §2.3·§12 — 지도가 아닌 무대(G3 시간축 등)를 같은 카메라 문법으로 쓰기 위한 추상화. 합격 = v3 골든 픽셀 동일.
- **결과**: 옛 자산으로 25컷 25/25·전편 692f228e·1080p 25/25·랫클리프 20/20·camera_suggest 동일, 렌더 +0.5%. pytest 838 passed(새 46). 도중 D-0078 국가 키 충돌 수정(PIPELINE-AP-011).


## 2026-09-29 v4.2.0 — Phase G2 장르 프로필과 새 요소 파이프라인

- **무엇을**: `genres/*.yaml`(GenreProfile, geopolitics approved·macro_monetary proposed), direction `genre`·결정적 검사 `genre_elements`(14항목), 프리미티브 계약 `engine/primitives`·첫 요소 `statement_diff`, 요소 갤러리(등록 요소 32 전부 실제 렌더), prompts/examples 채움.
- **왜**: handoff 20 §3·§4·§12 G2 — 장르 층 선언과 "등록 요소마다 스키마·렌더러·예제·테스트", 미등록 요소 = 오류.
- **결과**: hormuz 25/25(phaseG1 기준선)·랫클리프 20/20(G1 코드 대비), checks hard 0, pytest 881 passed(새 43). 작업 3 에서 `DEFAULT_STAGE` 삭제 때 다른 패키지(bundle/) 참조·심각도 표 테스트를 놓쳐 후속 커밋 2개 — 이후 커밋 전 전체 pytest.


## 2026-09-29 v4.3.0 — Phase G3 시간축 무대·데이터 레코드·차트 정직성 검사

- **무엇을**: `TimelineStage`(x = 일수·압축, y = 레인, 세로 척도 고정), 데이터 레코드 `SeriesRecord`(FEDFUNDS·CPIAUCSL), `series` 이벤트, 정직성 검사 4(18항목), 원고 `series:<id>` 수치 대조, 실증 `fed_timeline_demo`.
- **왜**: handoff 20 §2.3·§5·§6·§12 G3 — 공개 시리즈 2개로 시간축 프리뷰, 정직성 위반 주입 시 실패.
- **결과**: 실증 12컷 시트·78초 mp4, checks hard 0. hormuz 25/25·랫클리프 20/20·갤러리 33. pytest 956 passed(새 75). 결정 D-0085~D-0088(R-0100·0101·0102·0104).
- **운영**: 2c0fba8 을 `pytest | tail && git commit` 사슬로 올려 실패 2건이 푸시됐다(tail 의 종료 코드 0) → 4088f2f 로 고침. 이후 로그에 failed 가 있으면 멈추는 조건으로만 커밋.


## 2026-09-29 v4.4.0 — Phase G4 첫 비지정학 영상

- **무엇을**: 장르 프롬프트 층(주문 `order.yaml` → `prompts/genre_*.md` + `rules genre_prompt`), 목표 범위 band·`color_by: change`, scatter 레코드·`dot_plot`, `statement_diff` 단어 비교·원문 대조, 시간축 자리 슬롯, 실증 `fed_policy_2026`(연준 2026-09-16 인상, 48문장 307초, 480p·1080p).
- **왜**: handoff 20 §3·§4·§5.2·§7·§9·§11·§12 G4 — 주문 템플릿으로 첫 비지정학 영상, 두 게이트·루브릭 7항목.
- **결과**: 게이트 ① 대행, 게이트 ② 1차 반려(D-0093, 루브릭 3) → 시간축 자리·한 루프 → 루브릭 3 통과, 선택 판 v7 checks hard 0. 실증에서 결함 7(글리프 검사가 그린 글꼴 기준이 아니었음, 뱃지 시간축 앵커, 성명 문구 지어내기 가능, 사진·카드 고정 자리 충돌 등)을 찾아 고쳤다. hormuz 25/25·랫클리프 20/20·데모 12/12(D-0092 새 기준선)·갤러리 34. pytest 1016 passed(새 60). 사용자 판정(영상·새 요소·프로필 status)은 남아 있다.

## 2026-09-29 v4.5.0 — G5 검증 라벨 본문 제거·엔딩 카드 한 줄

- **무엇을**: 자막 첫 줄 라벨 접두·패널 태그 줄 검증 라벨 상자·post 카드 하단 라벨을 그리지 않는다. 엔딩 카드 맨 마지막 줄에 `rules end_card.notice_unverified`(가장 작은 글씨, 라벨 문장 수 n, n = 0 이면 없음). 죽은 키 3개 삭제, 검사 `[label-in-body]`, 검수 프롬프트 문장 교체.
- **왜**: 사용자 결정 D85(CLAUDE.md C9 개정) — "미검증 같은 글씨를 본문에 넣지 말고 언급도 하지 말라. 넣으려면 맨 마지막에 아주 작게 한 줄로 끝내라." back_and_forth D-0096.
- **결과**: 기록(claims·script_labels·provenance labels·원고 라벨 대조) 무변경. hormuz 25/25·데모 12/12 무변경, 랫클리프 11/20·fed_policy 5/22 컷 변경이 모두 자막 띠·엔딩 카드 안내 줄 안(`reports/phaseG5/label_off_diff_*.json`). 갤러리 33/34 무변경(`panel_gantt` 태그 줄만).

## 2026-09-29 v4.6.0 — G6 배경음악 저음 보강·웅장한 베드

- **무엇을**: 베드에 곡을 따라가는 저음 처리(로우 셸프·서브 옥타브 층·장면 시작 스웰, `rules audio.bed_bass`)를 정규화 전에 넣었다. 베드 저역 비율(30–120 Hz − 200–2000 Hz) 상승폭을 QA hard(`audio.qa.bed_bass_rise_db [4, 8]`)로, 처리 전·후 값을 `out/bed_stats.json`·provenance 에 남긴다. fed_policy 에 음악(bgm)과 금리 인상 문장 boom 을 넣었다.
- **왜**: 사용자 결정 D86 — "배경음악에 베이스를 좀 더 풍부하게 넣어서 좀 웅장한 느낌이 드는 배경음악이 깔리도록 해." back_and_forth D-0097, 결정 D-0102.
- **어떻게**: 처음 설계(처리 뒤 피크 정규화)는 서브 층이 키운 피크만큼 베드 전체를 낮춰, 저역 절대는 그대로이고 중역만 5.7 dB 내려갔다("묵직"이 아니라 "어두움"). 처리 전 피크 기준은 음악 레벨이 v3 합격 범위를 벗어났다. 그래서 정규화 기준을 `norm_ref` 로 규칙화하고, 음악 레벨 [−15, −11] 안에 0.3 dB 여유를 두는 최소값 0.7 을 0.1 단위 실측으로 정했다(저역 +1.4 dB·중역 −3.9 dB). 곡은 처리 전부터 저역 비율 +11.8 dB 라 D-0097 의 절대 범위 [−6, 0] 은 폐기하고 상승폭 판정으로 바꿨다.
- **결과**: 두 편 상승폭 +5.3 dB, 음악 레벨 범위 안, 내레이션 변화 0(리미터 전 피크 0.93 이하). 서브 층 잡음성 없음(에너지 90% 가 원곡 피크 절반 주파수). 이득 0 이면 hormuz mix 가 v3 합격본 md5 c1314fb9 와 같다. A/B 클립 6개·스펙트럼 `reports/phaseG6/` — 청감 판정은 사용자.
- **연관**: D86, D-0097·D-0102, handoff 10 §3.4. 운영: 옛 코드 worktree 로 무음악 mix 를 대조하려던 명령은 권한 분류기가 막았고 우회하지 않았다(단위 테스트로 갈음, D-0102).
- **정정(같은 날)**: 위 항목의 norm_ref 0.7 은 음악 레벨 조건만 본 값이다. hormuz 480p mux 에서 최종 트루 피크 −1.34 dBTP 가 한도(−1.5 + 코덱 여유 0.15)를 0.01 dB 넘었다. 오디오 경로만 재현한 실측(`reports/phaseG6/tp_sweep.jsonl`: 처리 끔 −1.47, 0.7 −1.34, 0.8 −1.40, 0.9 −1.40, 1.0 −1.47)으로 기존 QA hard 를 모두 통과하는 최소값 0.8 을 채택했다(저역 절대 +0.8 dB·중역 −4.5 dB). 코덱 여유(v3 값)는 바꾸지 않았다.
- **마무리(D-0103)**: 사용자 지시 "렌더 그만해도 돼"로 전편 재렌더(fed_policy 480p·1080p, hormuz 480p)를 중단하고 산출물을 버렸다. 최종 판정은 A/B 클립 6개·스펙트럼·오디오 경로 QA(`reports/phaseG6/audio_qa_final.json`, 두 편 hard 0)로 갈음한다.

- 2026-09-29 dmz_mine_2026: 사용자 요청 영상 『DMZ 지뢰 폭발 — 서울·모스크바·키이우의 시선』 480p 409.9초 완성(checks hard 0, 검수 hard 1 잔여를 사용자가 알고 승인). 검증 라벨 화면 표시 프로젝트 한정 끔(D85). 검증 워커 프롬프트가 argv 한도(128KB)를 넘는 문제는 본문 정리로 우회 — 구조 수정은 미착수(LLM-AP 후보).
- 2026-09-29 dmz_mine_2026 v2: 사용자 피드백(정적 화면·AI 음성·'군사분계선' 발음) — ElevenLabs 재합성(439.7초, tts '군사 분계선'), 인물 초상 4명 등재(Commons 자유 라이선스)·한국 기사 카드 8장, AI 연출이 쓰지 않은 초상 뱃지·기사 카드를 사용자 연출 지시로 direction 에 반영(checks hard 0). mux 트루 피크 초과 → RENDER-AP-004(rules audio.post_limiter_dbfs −2.0).
- 2026-09-29 dmz_mine_2026 v5: 사용자 피드백 — 임의 좌표 route 삭제(M8), 현장 개념도를 새 프리미티브 site_diagram(벡터·폭발 ①② 단어 앵커 애니메이션)으로, 1080p 최종. 사진 켄 번스 계단식 결함 발견(S8, 미수정). back_and_forth R-0112.
- 2026-09-29 dmz_mine_2026 v5 전편 1080p: final.mp4 md5 fad4f90f6dafcd1aec00c77c54c75c33, 439.74초, 104.8MB, −14.39 LUFS·−1.61 dBTP. 전달 = 재인코딩 없는 1080p 6조각(out/share_1080p_final/).
- 2026-09-29 엔딩 카드 롤·검정 유지(원 D87·R-0113 → v4.7.0 병합 D95·R-0122, 롤은 결정 대기) — dmz_mine_2026 크레딧 잘림·끝 전환 지도 노출 사용자 지적. pytest 1024 passed.
- 2026-09-29 v4.7.0 LLM-AP-009 기록 — LLM 브리지 argv 프롬프트 128KB 한도(dmz_mine verify-sources, 원 R-0111 S1). 구조 조치(stdin 전달)는 G8 후보(D-0104).

## 2026-09-30 v4.8.0 — G7 요소 크기(인물 배지 적응·기사 카드 조판·글자 크기 표·켄 번스 연속 변환·청와대 휘장)

- **무엇을**: 인물 뱃지가 보이는 인물 수에 따라 커지고 작아진다(solo 56 / group 30~34). 기사 카드는 w 440·헤드라인 18 로 조판하고 가운데 자리를 둔다. 화면 글자 크기를 전수 표로 점검해 본문 ≥ 12·메타 ≥ 9, 자막 21 로 올렸다. 사진 켄 번스 계단을 연속 변환으로 고쳤고, 청와대 휘장을 사용자 예외로 등재했다.
- **왜**: 사용자 결정 D89 — "한 사람만 나오면 크게, 여러 사람이면 작게. 기사는 조판해서 크게. 전체적으로 요소들이 너무 작다." back_and_forth D-0101, 결정 D-0111·D-0112·D-0113, D-0104 D2(c)·D6, D-0109(D98).
- **어떻게**: 크기 값은 전부 규칙 파일로(리터럴 0). 글자 크기는 먼저 리터럴만 규칙으로 옮겨 골든 바이트 동일을 확인하고(1단계), Fable 결정 뒤 값만 바꿨다(2단계). 골든 변경은 v4.7.0 엔진 렌더(= G1 기준선 25/25)를 기준으로 요소 상자 합집합 안 비율을 쟀다.
- **결과**: hormuz 골든 24/25 변경, 요소 영역 안 99.24%(밖 4컷 = 캡션 바·경로 라벨·마커 부제 확대와 지도 도시 라벨 자리바꿈). 랫클리프 20/20·fed_policy 21/22·데모 10/12 변경, 모두 checks hard 0. 갤러리 36. 운영: 재기동 20 이 R-0131 뒤 회수돼 재기동 21 이 D-0113 부터 이었다. 새 컨테이너 준비에 청와대 휘장 받기(`tools.commons_fetch emblems … --only cheongwadae`)가 필요하다.
- **연관**: D89·D98, D-0101·D-0104·D-0109·D-0111~D-0113.

## 2026-09-30 v4.9.0 — G8 콘티 판(animatic) 루틴

- **무엇을**: `engine.render --animatic` → `out/animatic.mp4`(480p·fps 24). 막지도(`FlatMercatorStage`)·자리표시 상자(`engine/layers/animatic.py`)·표식 띠·검사 프로파일·deliver 거부.
- **왜**: 사용자 결정 D97 — 흐름·호흡을 게이트 ② 전에 싸게 검토(back_and_forth D-0108).
- **어떻게**: 플래그 분기는 `load_project(animatic=True)` 한 곳, `render_frame` 은 `LayerSet` 만 본다. 자리 계산은 전편 기하 함수 재사용. 막지도 자료는 저장소 추적 NE 110m(R-0135, D-0108 "이미 있음" 이 실측과 달라 결정 요청).
- **결과**: fed_policy 307초 → 124초, hormuz 292초 → 118초(4코어, 목표 180초). hormuz md5 3회 동일. 자산 없는 폴더에서도 렌더(엔딩 카드만 다름). pytest 1110 passed.
- **연관**: D-0108·D-0114·R-0135, reports/phaseG8/run_log.md, artifacts/phaseG8-v4.9.0.


## 2026-09-30 v4.10.0 — G9 정비: 지명 사전·LLM 브리지 stdin·귀속 표현

- **무엇을**: ① `data/gazetteer.yaml`(NE 10m 3119 + 수기 9) + `tools/build_gazetteer.py` + checks `[geo-mismatch]` hard(`geo.gazetteer`). ② `claude -p`·`codex exec` 프롬프트를 argv 대신 stdin 으로, `{prompt}` 자리 삭제(LLM-AP-009 `[resolved v4.10.0]`). ③ `attribution_markers` 에 "보도했" + 프롬프트 `{{RULES.attribution_markers}}`.
- **왜**: back_and_forth D-0116(B-1·D-0104 S1·D84 보류분).
- **결과**: 골든 hormuz 8·랫클리프 6 place 전부 사전 오차 안(좌표 무변경), 전 프로젝트 mismatch 0. 140KB 프롬프트 실 subprocess 통과(argv 대조군 OSError). 린트 경고 fed 8 → 0, claims 판정 변화 없음(근거 본문에 "보도했" 없음).
- **연관**: D-0116, LLM-AP-009, handoff 04 §11·18 §8, ADDENDUM_04 §5.1.

## 2026-09-30 v4.11.0 — G10: 정적 구간 검사·음악 상한 +2 dB·글자 크기 2차 표

- **무엇을**: ① `rules pacing.static_window` + `engine/pacing.py` + checks `[static-window]` warning + 느린 푸시인(creep, w × 0.96) + 연출 프롬프트 변화 사다리. ② `music_under_narration_db` [-13, -9], norm_ref 0.7 → 0.4(`tools/norm_ref_sweep.py`). ③ 자막 22·카드 line 16.
- **왜**: back_and_forth D-0118(사용자 "이것들 진행해봐", 세부 값 Fable 위임 D103).
- **결과**: 골든 정적 창 0(creep 0, 프레임 무변경). 음악 hormuz −11.55 → −9.83·fed −12.31 → −10.57, TP −1.58·−1.65(한도 안). 2줄 자막 hormuz 17/45, 3줄 0, 카드 넘침 0, 골든 23컷 요소 영역 안 100 %. pytest 1149.
- **연관**: D-0118, handoff 05 §7·09 §10·10 §3, docs/12, reports/phaseG10, artifacts/phaseG10-v4.11.0.


## 2026-09-30 v5.0.0 — G11: GOAL G4-21 — 귀속 인용은 교차 확인이 아니다, claim_kind fact/statement

- **무엇을**: GOAL G4-21 추가. claims `claim_kind`(fact 기본·statement), `speaker_source_ids`. judge 가 statement 는 귀속 인용·본인 공식 원문을 supports 로, 단정 인용은 폐기(drops). verify_sources 프롬프트 kind 정의. 재판정 도구 `tools/g11_rejudge.py`.
- **왜**: back_and_forth D-0119(사용자 결정 D103), D-0122(drops A·1차 원문 B).
- **결과**: 랫클리프·fed status 변화 0, hormuz 대상 아님, 화면 영향 0. apply_draft 가 drops 있는 판정에서 파일을 쓴 뒤 예외로 죽던 결함 수정(ok=False·미기록). pytest 1165.
- **연관**: D-0119·D-0122, PIPELINE-AP-012, handoff 18 §9, docs/05·12, reports/phaseG11.

## 2026-09-30 v5.1.0 — G12: backdrop 무대·아일랜드·축 스케일·기사 프레스 v2·발음 사전·버전 도장

- **무엇을**: 엔딩 카드 버전 도장(§G), 발음 사전 합성 직전 적용(§D), 시간축 축 스케일 검사 `timeline_rescale`(§A), 사진 배경 무대 `backdrop`·이벤트 `backdrop`·`island`·차트 아일랜드·아일랜드 공통 규칙(D-0123), 기사 프레스 규약 v2(§C, 옛 카드 삭제), fed_policy AI 재연출(backdrop + 차트 아일랜드 + 연준 Flickr 6장) 480p·hormuz 기사 30초 클립.
- **왜**: 사용자 시청 피드백(D105 — fed 가로축 스케일·발음), 사용자 결정 D106~D109, back_and_forth D-0121·D-0123·D-0124·D-0126.
- **어떻게**: 규칙 SSOT(`stage_timeline.axis_scale`·`stage_backdrop`·`island`·`article_card` v2·`end_card.version_stamp`), 레지스트리 세 곳(P10), 코드는 연출을 고치지 않고 검사만(P8). 첫 AI 재연출에서 내 검사 결함 2건(statement_diff 라벨 date 오판, 수정 워커 issue_ref 해석)을 찾아 보정.
- **결과**: 골든 hormuz 3컷만 변경(25_END·기사 두 컷, expected_deltas 2건), fed v9 checks hard 0·검수 hard 4(마커 라벨 겹침 등 — 게이트 ② Fable). pytest 1205(§C 스테이지) · 최종 1206(§E, 기대값 2 갱신).
- **연관**: TTS-AP-067·068(상태 줄), reports/phaseG12, artifacts/phaseG12-v5.1.0.
- 2026-09-30 v5.1.0 PIPELINE-AP-013(검사가 라벨 date 를 시간축 앵커로 오판 → 연출가 3회 거부, 65eda77)·LLM-AP-010(수정 LLM issue_ref 표기 불일치 → 지적 이벤트 미해결, 2b9ae07·c46573b) 기록. G12 후속 D-0127 §6. 검수 예외: article press_lead 구간 empty 판정 제외(rules qa_checks.empty_exempt, D-0127 §5).
- 2026-09-30 v5.2.0 LLM-AP-011(연출가가 statement_diff date ISO·인용 174자 > 160 → 재실행 3회 거부) 기록, 필드 표에 스키마 description(형식·상한). G13 D-0129 §D.
