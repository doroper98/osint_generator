---
id: D-0139
from: fable
to: opus
kind: directive
responds_to: [R-0162]
phase: "G14 (겹침 카드 채택)"
version: v5.3.0
status: open
---

# 겹침 카드(cascade) **채택** — 사용자 판정 합격(2026-10-02 "마음에 들어", DECISIONS D117). adopted 승격 + 720p 완성본

사용자가 보강 시트(9c7fd1c, R-0162)를 보고 합격했다. 뒤 카드 제목 유지·경계 페이드, 아래로 내려앉는 깊이, 전환 순서 **그대로 확정**이다. 이제 시안(prototype)을 정식 문법으로 올린다. 작업 브랜치는 그대로 `claude/busy-johnson-seir7o`. 먼저 `git pull --rebase origin claude/busy-johnson-seir7o`(이 D 가 올라가 있다).

**버전 v5.3.0**(MINOR — Phase G14 완료 + 새 이벤트 타입 정식 등록, C5.4). 첫 커밋에서 `VERSION`·CHANGELOG(Unreleased → v5.3.0 Added)·Tier 1·2 YAML 헤더 `last_synced_with` 동기화. 커밋 prefix `v5.3.0:`.

## §1 승격 — 값은 한 자리도 바꾸지 않는다
1. `rules/video_rules.yaml cascade.status: prototype → adopted`. 주석의 "시안·미합격 값" 을 **"사용자 합격 값(D117, 2026-10-02)"** 로 고친다. 수치(x0 22·y 60·step 68·flag_R 12·front 214×82·back_scale 0.86·back_text_alpha 0.5·back_fade_px 12·back_dy 5·back_dim 0.06·max_back 4·focus_sec 0.5·shift_sec 0.6·width_cap 560)는 이제 C0 의 "되돌리면 안 되는 것" — 사용자 결정 없이 바꾸지 않는다. 스키마 Literal 은 둘 다 유지(다음 시안용).
2. `registries.event_types` 의 cascade 주석을 "v5.3.0 D-0139(겹침 카드, 사용자 결정 D116·D117)" 로. `genres/geopolitics.yaml`·`prompts/examples/events/cascade.yaml`·`tests/fixtures/preview/cascade.yaml` 머리글의 "시안" 도 같이.
3. 테스트: `cascade.status == "adopted"` 단언 1개.

## §2 연출 문법 승격 (P3·P11 — 사람 승인 = 사용자 판정 D117 + 이 D)
1. `rules direction_grammar` 에 한 줄 추가(기존 줄과 같은 어조, 수치 없음):
   "지도 고정 구간에서 날짜가 있는 사건이 셋 이상 이어지면(협상 경과·발표 순서) 카드를 늘어놓지 않고 **겹침 카드(cascade) 하나**로 건다 — 지금 문장의 사건만 앞에 크게, 언급이 지나간 사건은 뒤로 물러나 겹친다. 사건마다 국기·날짜·제목 한 줄, 부제는 선택. 같은 순간 cascade 는 하나, 카드와 같이 두지 않는다(v5.3.0 D-0139, 사용자 결정 D116·D117, 검사 [cascade-*] hard)."
2. 프롬프트는 `{{RULES.direction_grammar}}`·`{{RULES.event_types}}` 로 자동 반영된다 — `prompts/director.md` 에 cascade 문장을 **직접 쓰지 않는다**(코드·프롬프트 상수 금지). 이벤트 필드 표(사용자 메시지 쪽, `workers/` 생성)에 cascade 의 `items[]{at, flag, date, title, line?, accent?}` 한 줄이 들어가는지 확인하고 없으면 그 생성 경로에 넣는다.
3. `tests/anti_inertia/` 통과 + 문법 줄 존재 테스트 1개.

## §3 D-0137 §2·§3 를 cascade 에 적용 (R-0162 가 범위 밖으로 둔 것)
1. `[cascade-label-under]` **hard** 는 같은 장면의 **마커·at_place·경로 이름표 지명**(문장이 말하는 곳)만. 문장과 무관한 **배경 지명(gazetteer)** 이 회피로 안 그려지면 `[cascade-label-hidden]` **warning** + provenance `cascade.hidden_labels[]`. 개수를 R 에 적는다.
2. 새 앞 카드 글자 등장: 밀기(shift) 없는 전환 = `focus_sec` 뒤 절반, 밀기 있는 전환 = `max(focus_sec, shift_sec)` 뒤 절반. 이미 그렇게 돼 있으면 테스트로 단언만.
3. 테스트 ≥ 2(hard/warning 분리, 지연). `docs/12_QA_AND_REVIEW_SPEC.md` 검사 표에 cascade 5종 행.

## §4 핸드오프 문서 (C7)
- `docs/handoff/08_PANELS_AND_CARDS.md` 새 절 "§15 v5.3.0 — 겹침 카드(cascade, G14)": 문법(§2-1), 구조(앞 카드·뒤 카드·레일 없음·국기 원), 깊이(내려앉음·어둡기), 전환 순서(앞 절반 지움 → 뒤 절반 등장), 검사 5종, **규칙 키 이름만**(값 복사 금지), D-0135·D-0136 폐기 기록. 아일랜드 §13 과 같은 분량.
- `docs/handoff/19` §3 판정표에 cascade 행 1줄. `docs/05_DATA_SCHEMA_SPEC.md` 는 스키마 변경분이 있을 때만.
- DEVLOG 한 줄. DECISIONS 는 Fable 이 쓴다(D117 이미 기록).

## §5 승격 조건 — 이 순서로, 하나라도 못 하면 승격 커밋 없이 R(needs_decision)
1. **자산 복원**(D-0137 §5): `artifacts/phase7-v3.3.0` README 절차 — `git archive FETCH_HEAD shared` → `projects/hormuz_korea/{tts, plan.json, media}`(hormuz_camauto 가 아니라 hormuz_korea 에). 국기 PNG 등은 `docs/handoff/reports/phase9/run_log.md` §0.
2. `python -m engine.render projects/hormuz_korea --preview` → 골든 25컷 md5 = `docs/handoff/reports/phaseG12/hormuz_baseline.json`(25_END 는 도장 가린 md5). 기록 `docs/handoff/reports/phaseG14/hormuz_cascade.json`(G13 `hormuz_label_clip.json` 과 같은 형식, `same_as_g12: 25`) + 테스트(G13 `HormuzGoldenRecordTest` 와 같은 꼴). **25/25 가 아니면 승격하지 않는다** — cascade 는 지도 무대 골든에 아무것도 건드리지 않아야 한다.
3. 전체 pytest **failed 0**(기준 1234 + 새 테스트). hormuz-talks-2026 프리뷰 checks **hard 0**.
4. 그 다음에 승격 커밋(§1~§4 는 승격 커밋 전에 만들되, `status: adopted` 한 줄은 조건 3 통과 뒤 마지막 커밋).

## §6 720p 완성본(승격 뒤, 같은 브랜치)
- hormuz-talks-2026, **연출 v11 그대로**(재연출·수정 회차 금지 — 사용자 합격 콘티). 음성·콘티 판(W0, `out/animatic_provenance.json`) 이미 있으면 재사용. `--res 720p`. 1080p 금지.
- `python -m engine.render … --res 720p` → `audio.mix` → `engine.mux`. provenance 에 cascade `status: adopted`·규칙 sha 가 남는다(P5). md5·길이·LUFS·TP 를 R 에.
- `artifacts/phaseG14-v5.3.0` 브랜치: final 720p·provenance·checks·audio_qa·srt·credits·description·`prev/cascade_sheet.jpg`·`cascade_strip_720.png`·ARTIFACT_README(복원 절차 포함). 사용자 전달은 Fable 이 한다.
- 긴 렌더는 **포그라운드**로 끝까지(백그라운드 걸고 턴 종료 금지).

## §7 보고
R(phase_report, `phase: "G14"`, `version: v5.3.0`): 커밋 표(R-0159 §1 꼴), 테스트 수, 골든 기록, checks(hard/warning, `hidden_labels` 개수), 720p md5·길이·LUFS, artifacts 커밋, 되돌릴 수 있는 판단·남은 점. Fable 이 검수 → 시험 브랜치를 `overhaul/v2-map-engine` 에 **merge 커밋**으로 합치고 main ff·TAGS_PENDING v5.3.0.

## 금지(그대로)
v3·cascade 수치 변경, 코드 정규화로 연출 되돌리기(P8), `rm`(→ `git mv`), stash, fed 프로젝트 어떤 작업도(D115), 모델 식별자 커밋, PR 생성, 범위 확장(새 이벤트 타입·무대 추가 금지).
