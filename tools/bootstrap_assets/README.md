<!--
tier: 3
last_synced_with: v2.3.0
ssot_for: [bootstrap-assets]
depends_on: [tools/fetch_data.py, docs/handoff/DECISIONS.md]
last_review: 2026-09-28
-->

# tools/bootstrap_assets — 자산 부트스트랩 (임시, D32)

v3 참조 코드(`docs/handoff/reference_code/v3_hormuz_korea/`) **실행본**이다. v2.3.0 에서 옛 v3 실행본 폴더를 지울 때
영상 통로(render·plan·mix)는 삭제하고, 새 엔진에 아직 없는 **자산 생성 두 단계만** 여기로 옮겼다(back_and_forth D-0024).

| 파일 | 원래 이름 | 하는 일 |
|---|---|---|
| `prep_people_flags.py` | `prep3.py` | `people`: 인물 컷아웃(rembg)·휘장·`rights_registry.json` / `flags`: 국기 SVG→PNG |
| `media_first_pass.py` | `media3.py` | 미디어 1차(사진·영상·컷아웃, Commons) |

- **본문 무수정.** 경로 줄만 환경변수(`V3_ROOT`, 기본 `projects/hormuz_korea_legacy` / `OG_ROOT`, 기본 저장소 루트)로 바뀐 상태 그대로다.
  prep3 의 geo·base 단계는 파일에 남아 있지만 쓰지 않는다(지오는 `python -m geo.prep`).
- **호출은 `tools/fetch_data.py`만 한다**: `python tools/fetch_data.py people`, `python tools/fetch_data.py media`.
  새 엔진·워커(`engine/`·`script/`·`audio/`·`workers/`·`orchestrator/`)는 이 패키지를 import 하지 않는다
  (`tests/anti_inertia/test_no_legacy_imports.py`가 검사).
- **수명**: Phase 5(people·flags → 뱃지·엔티티·권리)와 Phase 6.5(media → 사진·영상·컷아웃)에서 정식 모듈로 대체되면 **삭제**한다
  (`docs/handoff/19` §6 표의 해당 행 "삭제" 열).
