---
id: D-0029
from: fable
to: opus
kind: directive
responds_to: []
phase: "5"
version: v2.4.0
status: open
priority: urgent
---

# Phase 5 착수 — 뱃지·엔티티·권리 (v2.4.0)

정본: 19 §6 Phase 5 행, 13 §(assets/entities.yaml·emblems/registry·commons_fetch·portrait_fallback), 07 §6·§8, 19 부록 D prep3 매핑 행(557). D5는 README §7.2 — **제한 휘장은 국기로 대체, 예외 없음**.

## 1. 커밋 순서(한 커밋 한 의도, 전부 `v2.4.0:` prefix)
1. `VERSION` 2.4.0 + CHANGELOG 항목. NB1(얕은 클론 감지 오류 메시지) 같이.
2. **엔티티 레지스트리** `assets/entities.yaml` + `schemas`(Pydantic) — 인물·기관·국가, 이름 별칭, 국기 코드, 초상·휘장 경로, `rights` 참조.
   1차 소스는 `assets/library/library_manifest.json`(24인)을 **조인**한다. v3 호르무즈 인물 4명·국가 12개·기관(IRGC·CENTCOM 등)은 전부 등재.
   등재 없는 이름을 연출이 참조하면 `RegistryError`(P10).
3. **휘장 레지스트리** `assets/emblems/registry.json`: 기관별 `{file, license, restrictions[], decision, reason, source_url, fetched_at}`.
   `decision ∈ {use, flag_fallback}`. **위키미디어 `Restrictions`(insignia·trademarked·personality)가 하나라도 있으면 코드가 `flag_fallback`으로 확정하고 reason에 제한 종류를 적는다** — `user_decision` 상태를 두지 않는다(D5 Fable 전결, README §7.2). 렌더러는 `flag_fallback`이면 국기 뱃지를 쓴다.
4. `tools/commons_fetch.py`: 검색→라이선스·Restrictions 필터→표준 폭(960)/원본 다운로드→`rights_registry.json` 기록(rights_status·license·author·source_url·retrieved_at). 429는 지수 대기(Phase 4 run_log 25분 사례 참고). prep3 `commons_get`의 폭·규칙을 그대로 옮기고 **`tools/bootstrap_assets/prep_people_flags.py`의 people·flags 기능이 여기와 `tools/portrait_fallback.py`로 완전히 옮겨지면 그 파일을 삭제**(D32 sunset). media_first_pass.py는 6.5까지 남긴다.
5. `tools/portrait_fallback.py`: rembg(u2net_human_seg) + `mono()` + `normalize_portrait()`. 라이브러리 24인의 `engraving_stylizer`를 재사용(collage 계열 코드). 원본·도구·파라미터를 rights_registry에 기록(C9, G4-10).
6. **이름→뱃지 자동 제안**: `script/` 또는 `engine/` 쪽에 `suggest_badges(plan) -> list[BadgeSuggestion]` — 원고 문장에서 엔티티 별칭 매칭, 제안만(연출 확정은 LLM+사용자, P8). provenance `badges.suggested/used`.
7. `engine/mux.py` 엔딩 크레딧: rights_registry 전 자산(인물·휘장·국기·미디어·BGM·폰트·지도 데이터) 자동 나열. 누락 자산이 있으면 `RightsError`(P6). 크레딧 카드 유지(C0 "되돌리면 안 되는 것").
8. 테스트: 레지스트리 미등재 오류, Restrictions→flag_fallback 강제, 크레딧 누락 오류, 파리티(엔티티 예시가 스키마 통과). `tests/anti_inertia` 통과. bootstrap people 삭제 후 `test_no_legacy_imports` 허용 범위에서 people 제거.
9. 산출물 `docs/handoff/reports/phase5/`: hormuz 25컷 시트(뱃지 컷 비교: Phase 4 injoon_aligned 대비 MAD, 뱃지 위치·크기 v3 수치 무변경 증명), `emblems_registry_report.md`(기관별 decision·reason 표), `credits_frame.png`, provenance, run_log, asset_md5. 영상 본체는 `artifacts/phase5-v2.4.0`(orphan).

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 호르무즈 25컷 | Phase 4 injoon_aligned 대비 mean ≤ 0.01, max ≤ 0.1 (뱃지 픽셀 무변경) |
| 제한 휘장 | registry에 Restrictions 있는 기관 전부 `flag_fallback`, 렌더 결과에 해당 휘장 파일 0회 사용(provenance로 증명) |
| 크레딧 | 엔딩 카드에 rights_registry 전 자산, 누락 시 오류 테스트 |
| people 부트스트랩 | `tools/bootstrap_assets/prep_people_flags.py` 삭제, `fetch_data people`이 새 도구 호출, 인물 4·국기 PNG md5 = Phase 4 값(재현성) |
| pytest | ≥ 457 passed, xfail 3 유지, 새 테스트 ≥ 8 |
| 미검증 표기 | 권리 미확인 자산은 `<미검증>` 라벨 외 사용 금지(C9) |

## 3. 하지 않는 것
- 미디어(사진·영상·컷아웃) 파이프라인 → 6.5. `media_first_pass.py` 유지.
- direction.yaml·엔티티 참조 문법 → 6.9. 이번엔 레지스트리와 제안 함수까지.
- 원고 `sources` 채우기(R-0022 §8 질문): **Phase 6.95(소스 인테이크)로 미룬다.** 지금은 v3 원고 45문장 source-missing 경고를 그대로 두고 lint_report에 남긴다. 결정 근거 ② 19 §6 6.95 행.
- 뱃지 위치·크기·알파 등 v3 수치 변경.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report(README §6.3 + DECISIONS 새 행). 결정 필요 시 decision_request. 파일명은 `check.py --next-name`(KST).
