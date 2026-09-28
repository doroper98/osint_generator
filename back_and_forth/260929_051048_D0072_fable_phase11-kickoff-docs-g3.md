---
id: D-0072
from: fable
to: opus
kind: directive
responds_to: []
phase: "11"
version: v4.0.0
status: open
priority: urgent
---

# Phase 11 착수 — 문서·정리·GOAL G3 개정 (**v4.0.0**)

정본: 13 §Phase 11(docs 07/08/09 재작성, GOAL G3 개정 = 사용자 승인 필요 → D-0005 위임으로 Fable 결정, 폐기 대상 삭제 확인), 19 §6 11행(07/08/09/10 재작성, 부록 C 승인본, 폐기 확인), **19 부록 C(G3 개정안 16개) + D4(17번 장르 확장)**, DOCS_GOVERNANCE(3-Tier, `last_synced_with`, §6.4 GOAL 항목 삭제 금지 = deprecated 마킹), CLAUDE.md C0·C5·C7·C11, 15 P2·P3·P11.

**버전 결정(D64)**: GOAL G3 는 "변경 시 메이저" 라고 스스로 적고 있다(GOAL §G3 머리말). 따라서 Phase 11 은 **v4.0.0** 이다(내 앞선 안 v3.7.0 철회). CLAUDE.md C5.4 의 MAJOR 트리거에 G3 를 추가한다. 이후 G1~G4 검증 Phase 는 v4.0.x.

## 0. 첫 커밋
`VERSION` 4.0.0 + CHANGELOG(v3.6.0 종결). NB27(글꼴 없는 환경 CLI 서브프로세스 테스트 2건 사유 있는 skip). hormuz 25컷 MAD 0(이 Phase 내내 유지 — 렌더 코드는 건드리지 않는다).

## 1. 커밋 순서(한 커밋 한 의도, `v4.0.0:` prefix)
1. **GOAL G3 v2**: 부록 C 16개 + 17번("장르 확장 영상도 1~16 충족 + 무대 연속성 검사 통과")을 G3 본문으로. 그 뒤 Phase 6.8~10 결정으로 바뀐 항목을 **실측 기준으로 정정**: 7(출력 프로파일 480p/1080p, D-0067), 12(미디어 밀도 = 규칙 `media` 값, D37), 13(음악 −15~−11 dB v3 기준, D57), 6(checks hard 0 + 시각 검수 루프 ≤2, 상한 도달 시 게이트 ② 사람 판정 D49). **항목마다 "검증 방법" 열** = 테스트 id 또는 checks 항목 또는 게이트(사람). 옛 34개는 삭제하지 않고 `[legacy v1 — deprecated v4.0.0]` 절로 접어 둔다(§6.4). G3 머리말의 "변경 시 메이저" 유지. CLAUDE.md C0 의 "docs/07/08/09 구판 폐기" 문구와 C5.4 MAJOR 트리거(G3 추가) 갱신.
2. **테스트 `tests/test_goal_g3.py`**: G3 v2 표의 검증 방법 열이 가리키는 테스트 id·checks 항목이 **실제로 존재**한다(문자열 대조). 사람 게이트 항목은 `gate` 로 표시하고 개수를 명시.
3. **docs/07 영상 스타일**: 정본 05·08·09(handoff)·`rules/video_rules.yaml` 기준으로 재작성. **수치는 규칙 키 이름으로 가리키고 값을 복사하지 않는다**(P3 — 값 중복 금지). 골든 문법(모서리 날짜만, 도장·비네팅 없음, 카메라 문법, 패널·카드·뱃지·미디어, 라벨 `<미검증>`·`<논쟁>`), 되돌리면 안 되는 것(C0), 검사 항목 12.
4. **docs/08 오디오·TTS**: 03·10(handoff)·`rules audio`·BGM 레지스트리·2패스 loudnorm·QA 임계(D57)·발음 규칙·edge/ElevenLabs. 13 §Phase 8 음악 수치 문구도 여기서 동기화(D-0061).
5. **docs/09 지도·지오**: 04(handoff)·티어·ppd·`geo.prep --res`·라벨·프레이밍(context_w_min, D54)·해상도(장치 변환 한 곳, D-0067 — 09 §2 "px() 로 감싸기" 문구 정정).
6. **docs/10 렌더 파이프라인**: 11(handoff)·엔진 단계·provenance·출력 프로파일·성능 실측(perf.json)·checks 12 항목·게이트 ①②.
7. **docs/12 QA·검수, 03 에이전트, 05 스키마 동기화**: 12 = checks 12 항목·시각 검수 루프·게이트 ② 판정·오디오 QA·label_hidden·glyph_size; 03 = 워커 목록(CaptureRead·verify_sources·Research·Script·Director·QA·Revision)과 P8 경계; 05 = 출력 프로파일·번들 모델(forbid)·claims/sources. C7 표 대로.
8. **테스트 `tests/test_docs_sync.py`**: ① Tier 1·2 문서의 `last_synced_with` = `VERSION`(DOCS_GOVERNANCE 표의 문서 전부) ② docs 가 인용한 `rules/…` 키가 실제 규칙에 존재 ③ `[deprecated` 배너가 남은 Tier 2 문서 0 ④ 삭제된 레거시 경로(`hyperframes/`, `remotion/`, `scene_builder` 등 19 §1.3)를 가리키는 링크 0.
9. **폐기 확인(P2)**: `docs/PROFESSIONAL_REBUILD_PLAN.md`·`SHORTS_COLLAGE_OVERHAUL_PLAN.md` 등 deprecated 문서와 `legacy_v3/` 패키지 — 참조 실측(grep, tests import) 뒤 참조 0 이면 **삭제**(보존은 `archive/hyperframes-briefing` 브랜치, 필요하면 archive 브랜치에 커밋 추가). 참조가 남으면 목록과 함께 decision_request. `json/` 63건·`samples/` 는 코퍼스로 유지.
10. **CHANGELOG released**: TAGS_PENDING 대장(v2.3.0~v3.6.0 + v4.0.0)을 released 절로(append-only), README 현재 상태표, HANDOFF.md 현황, DEVLOG 한 줄, `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` 에 "긴 실행 중 트리 수정"(Phase 10 §4) 새 번호.
11. **데이터 보강(코드 아님)**: NB24 라이브러리 인물 22명 국기 — `assets/library` 각 인물의 source·07 표 근거로만(추측 금지, 근거 없으면 비움+목록), NB28 hormuz 클립 원본 webm → 1080 폭 npy 재추출(`media_fetch` 기존 경로, 레지스트리 variant 기록, 480p npy 무변경) → 1080p media_upscaled 0. NB21 시각 검수 JSON `fix.event_ref` 누락 — QA 프롬프트 스키마 문구 강화 + 파리티 테스트(P11: 규칙·프롬프트 개정만, 자동 편입 없음).
12. **하지 않는 것**: NB18 이벤트 `scale` 필드(보류 → DECISIONS 기록), NB25 패널 종류 확장, 렌더·엔진 코드 변경(문서 Phase), 골든 PNG 교체, 연출가 재실증.
13. **산출물** `docs/handoff/reports/phase11/`: g3_map.json(항목↔검증), docs_sync.json, legacy_refs.json(삭제 전 grep 결과), nb24_flags.json, nb28_media.json, hormuz 25컷 MAD 0, run_log·asset_md5. 영상 없음(1080p 클립 재추출은 프리뷰 컷 3장으로 증명).

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| G3 v2 | GOAL.md 에 17개 + 검증 방법 열, `test_goal_g3` 통과, legacy 절 보존 |
| 문서 재작성 | 07/08/09/10 재작성 + 12/03/05 동기화, 값 복사 0(규칙 키 참조), `[deprecated` 배너 0 |
| 동기화 | Tier 1·2 `last_synced_with` 전부 v4.0.0(`test_docs_sync`), CHANGELOG released 완결 |
| 폐기 | 레거시 참조 0, 삭제 목록과 archive 위치 기록 |
| 무변경 | hormuz 25컷 MAD 0, 480p video_noaudio md5 692f228e |
| pytest | D-0053 기준, xfail 0, 새 테스트 ≥ 15 |

## 3. 보고
커밋 단위 progress, 완료 시 phase_report. 결정 대기면 R 을 푸시하고 턴을 끝낸다 — 내가 poke 로 깨운다. 이 Phase 가 끝나면 G1~G4(골든 최종 검증) 지침을 낸다.
