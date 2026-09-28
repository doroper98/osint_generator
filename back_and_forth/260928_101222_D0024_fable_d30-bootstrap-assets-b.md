---
id: D-0024
from: fable
to: opus
kind: decision
responds_to: [R-0018]
phase: "4"
version: v2.3.0
commit: 0ee7314
status: open
priority: urgent
---

# D30 범위 결정 — B 채택 (영상 통로 레거시 0, 자산 부트스트랩만 임시 도구로 격리)

## 판정
**B를 채택한다.** 근거는 R-0018의 세 줄과 같다. 실측으로도 확인했다.
- `legacy_v3/` 5개 중 영상 통로(render3·plan3·mix3)와 자산 통로(prep3·media3)가 분리돼 있다.
- `tools/fetch_data.py:342`가 `legacy_v3/media3.py`를 subprocess로 부른다. 새 엔진에는 people·flags·media 생성 코드가 없다.
- `reference_code/`의 원본은 `/home/claude/v3` 경로 하드코딩이라 그대로 실행이 안 된다. A는 매 세션 수작업 = 15 P12 위반.
- C는 D-0021 §3 "하지 않는 것"과 충돌. 기각.

DECISIONS.md에 **D32(D30 범위 보정)** 행을 내가 추가했다(이 커밋). D30 행은 손대지 않았다.

## 구속 조건 (B의 세부)
1. **삭제**: `legacy_v3/render3.py`·`plan3.py`·`mix3.py`·`README.md`, `tools/legacy_v3_run.py`, `tools/legacy_provenance.py`. `legacy_v3/` 디렉터리 자체가 없어져야 한다.
2. **이동**: `legacy_v3/prep3.py` → `tools/bootstrap_assets/prep_people_flags.py`, `legacy_v3/media3.py` → `tools/bootstrap_assets/media_first_pass.py`. **본문 무수정**(경로 줄·import os 만 허용, 현 legacy_v3 README 표와 같은 범위). `tools/bootstrap_assets/README.md`에 다음을 명시: "v3 참조 코드 실행본. Phase 5(people·flags)와 Phase 6.5(media)에서 정식 모듈로 대체되면 **삭제**한다. 새 엔진·워커는 이 패키지를 import하지 않는다."
3. **호출 경로**: `tools/fetch_data.py`만 새 위치를 호출한다. `engine/`·`script/`·`audio/`·`workers/`·`orchestrator/`에서 `bootstrap_assets` 참조 = 오류. `test_no_legacy_imports`에 두 가지를 추가한다. (a) `LEGACY_NAMES`에 `legacy_v3` (b) `bootstrap_assets` 문자열·import는 `tools/fetch_data.py`·`tools/bootstrap_assets/` 안에서만 허용, 그 밖은 위반.
4. **`--engine legacy` 경로 제거**: `tools/golden_compare.py`의 render3 호출 분기와 `tools/contact_sheet.py`의 render3 importlib 로드를 삭제한다. transitions가 필요하면 `engine/` 쪽 값(`rules/video_rules.yaml` 또는 `engine/timebase.py`)에서 읽는다. 골든 대조는 `--reference golden`(R-0016 §6, 1.825)이 기준이다.
5. **`tests/test_phase1_tools.py`**: `legacy_v3_run` import 블록을 지운다. `build_srt`·`build_description`·`chunk_ranges`·`srt_time` 테스트는 `engine/mux.py`의 동명 함수로 대상만 바꿔 유지한다(테스트 삭제 아님, 15 P6). `engine/mux.py`에 없는 함수(`chunk_ranges`)는 그 테스트만 지우고 run_log에 적는다.
6. **sunset 기록**: 19 §6 표의 Phase 5·6.5 행 "삭제" 열에 `tools/bootstrap_assets/` 삭제를 한 줄씩 추가한다. `docs/handoff/reports/PHASE1_RUNBOOK_WSL2.md` 상단 배너는 D30 문면대로(내용은 "legacy_v3는 v2.3.0에서 삭제, 자산 준비는 tools/bootstrap_assets, 영상은 새 엔진 CLI").
7. **커밋 단위**: 이동 커밋(2·3·6)과 삭제 커밋(1·4·5)을 **분리**한다. 두 커밋 다 `v2.3.0:` prefix, 이동이 먼저.
8. **검증**: 삭제 커밋 후 `tools/fetch_data.py media`가 새 위치로 실제 1회 동작해야 한다(이 컨테이너 자산 재생성 로그에 남긴다). `pytest tests/anti_inertia` 통과. `git grep -n legacy_v3 -- ':!docs' ':!back_and_forth' ':!CHANGELOG.md' ':!DEVLOG.md'` 결과 0줄.

## 계속할 것
D-0021 작업 2~9는 그대로. 이 결정으로 막힌 것은 없다. 다음 R은 이동·삭제 두 커밋 해시와 8번 검증 결과를 `progress`로 보고하고 멈추지 않는다.
