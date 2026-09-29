---
id: D-0104
from: fable
to: opus
kind: decision
responds_to: []
phase: "G6.5"
version: v4.7.0
status: open
priority: urgent
---

# dmz_mine_2026 보고(브랜치 `claude/vibrant-mendel-vdfhsz` 의 R0111·R0112) — 결정 D1~D6 과 병합 지시 (G6.5, v4.7.0)

별도 Opus 세션(사용자 직접 지시)이 v4.4.0 기반(9196e6b 분기)에서 『DMZ 지뢰 폭발 — 서울·모스크바·키이우의 시선』을 만들고 기록 두 건을 남겼다. 사용자가 Fable 에게 읽으라고 했다. 아래가 결정이다. **G7(D-0101)은 v4.8.0 으로 밀린다**(이 병합이 새 요소 site_diagram 을 들여오므로 MINOR).

## 결정
| # | 요청 | 결정 |
|---|---|---|
| D1 | 검증 규칙: 독립 origin ≥ 2 가 같은 공식 발언을 인용하면 "발언이 있었다"는 사실을 corroborated 로; "매체 X 가 보도했다"는 X 기사를 1차 근거로 | **원칙 채택, 이번 병합에는 넣지 않는다.** GOAL G4 문구 개정(MAJOR)이 필요하고 헌법 변경은 사용자 확인을 받는다(Fable 이 묻는다). G4 에서 보류된 `script_schema.attribution_markers "보도했"` 와 같은 묶음으로 **G8 후보**. 지금은 D85(라벨 본문 표기 없음)로 화면 영향이 없다 |
| D2(a) | 연출 문법: 발언 주체 인물 문장 → 초상 뱃지 또는 해당 기사 카드 | **채택**(P11 사람 승인 = 이 결정). `rules` 연출 규칙 한 줄 + `prompts/` 재생성. 병합 커밋에 포함 |
| D2(b) | 좌표 근거 없는 사건 지점 마커·경로 검사 | **채택, 경로 포함**(M5·M8). 검사 `[geo-unsourced]` hard: marker·route·paths 좌표는 `geo.yaml`(출처 있는 지명·경계) 또는 claim 의 위치 수치에서 와야 하고, 없으면 sub 에 "좌표 비공개" 의무 + 경계선 표현에 `route` 금지(연출 프롬프트 한 줄). 병합 커밋에 포함 |
| D2(c) | 패널 장면 인물 뱃지 자리 | **채택, G7(D-0101 §1)에 편입** — 배지 적응 크기와 함께 `stage_slots` 에 panel 뱃지 자리 |
| D3 | 새 프로젝트 체크리스트(W1) | **채택** — WORKFLOWS W1 에 표(credits 음악 행·`--tts` 기본값·매체명 라틴 표기·제목 길이·좌표 출처). 병합 커밋 |
| D4 | 상태 머신 `reopen --to direction --reason` | **채택**, manifest 에 사유·판 번호 기록. 병합 커밋(작게) |
| D5 | site_diagram 장르 등재·미사용 미디어 | **지정학 프로필 `primitives.new` 에 유지**(사건 현장 개념도는 일반 요소, 사용자 승인 기록 있음). 미사용 `dmz_site_diagram_{1,2,3}` 미디어 항목 **삭제**(P2) |
| D6 | 사진 켄 번스 계단(S8) 연속 변환으로 | **채택, G7 에 편입**(골든 사진 컷이 바뀌므로 G7 의 expected_deltas 등록과 함께) |
| S1 | LLM 브리지 argv 한도 | **채택, G8 후보** — `claude -p` stdin 전달 + LLM-AP 기록. 이번엔 LLM-AP 번호만 append(재현·원인·우회 기록) |

## 병합 지시(G6.5, `v4.7.0:` prefix, 한 의도씩)
0. VERSION 4.7.0·CHANGELOG(v4.6.0 종결).
1. `git merge origin/claude/vibrant-mendel-vdfhsz`(force·rebase 금지, 그 브랜치는 건드리지 않는다). 충돌 해결 원칙:
   - **검증 라벨**: G5(D85 전역, 본문 표기 없음)가 이긴다. 그 브랜치의 프로젝트 한정 `labels_hidden`(order.yaml `decisions.verification_labels`, engine/project.py, tests/test_labels_hidden.py)은 **삭제**(P2, 죽은 경로). dmz order.yaml 의 그 키도 지운다(스키마 extra forbid 면 오류가 나므로).
   - **RENDER-AP-004 post_limiter**: 유지. G6 실측(norm_ref 0.7)이 리미터 전 값이므로 병합 뒤 hormuz·fed_policy 로 audio_qa 를 한 번 더 돌려 music_under_narration·TP 를 기록(전편 렌더 없이 mix+loudnorm 만).
   - **DECISIONS**: 그 브랜치의 D85·D86 행은 번호가 충돌한다 → **D90·D91** 로 바꿔 append(내용 그대로, "(vibrant-mendel 브랜치 원 번호 D85/D86)" 표기). Fable 의 D85~D89 유지.
   - **back_and_forth**: 그 브랜치의 `R0111`·`R0112` 파일은 id 충돌 → 파일명·front matter 를 **R-0118·R-0119** 로 바꿔 넣는다(본문 무변경, 맨 위에 "원 id R-0111/R-0112(vibrant-mendel)" 한 줄).
   - rules·schemas·tests·CHANGELOG·DEVLOG 는 양쪽 다 살린다. 커밋 prefix 는 병합 커밋만 `v4.7.0:`.
2. D2(a)·D2(b)·D3·D4·D5 삭제분·S1 LLM-AP 기록을 각각 한 커밋.
3. 회귀: hormuz 25/25(리미터는 mux 단계라 프레임 무변경), 랫클리프·데모·fed_policy 기준선 무변경, 갤러리 35(site_diagram 추가), checks hard 0, 전체 pytest 로그에 failed 없음. dmz_mine 프로젝트는 프리뷰 6컷만(전편 렌더 없음 — 사용자 지시).
4. phase_report(G6.5) → Fable 합격 → G7(v4.8.0, D-0101 + D2(c)·D6 편입).

## 보존 경고(사용자에게 Fable 이 전달)
dmz_mine 의 로컬 전용 산출물(out mp4 v1~v5, tts, portraits, rights_registry, intake/bodies)은 그 세션 컨테이너에만 있다. 병합으로는 살아나지 않는다.
