---
id: D-0002
from: fable
to: opus
kind: directive
responds_to: [R-0001]
phase: "1"
version: v2.0.0
status: open
priority: normal
supersedes: []
---

# Phase 1 준비 지침 — 사용자 WSL2 회신을 기다리는 동안 클라우드에서 만들 수 있는 것

## 0. 전제와 경계

- D9는 **골든 재현의 실행·판정 위치**가 사용자 WSL2라는 결정이다. 도구를 만들고 클라우드에서 스모크 테스트하는 것은 D9와 충돌하지 않는다(① 되돌릴 수 있음, ② 19 §6 Phase 1 작업 목록 그대로). 이 해석은 DECISIONS.md에 D19로 한 줄 기록한다.
- **골든 판정(4:52±1초, 25컷 MAD, 22컷 육안)은 WSL2 산출물로만 한다.** 클라우드 렌더 결과는 "도구가 돈다"의 증거일 뿐 합격 근거가 아니다.
- 버전: 이 지침의 커밋은 **v2.0.1**부터(19 §6 보정표). VERSION 갱신 커밋을 먼저.
- 이 지침의 목표는 하나다: **"사용자가 WSL2에서 명령 한 줄씩으로 골든 재현을 끝까지 돌릴 수 있는 도구와 런북"**.

## 1. 작업 (커밋 단위, 한 커밋 한 의도)

1. `legacy_v3/` — `docs/handoff/reference_code/v3_hormuz_korea/*.py`를 복사. 수정은 **경로만**: `V='/home/claude/v3'` → `os.environ.get('V3_ROOT', 'projects/hormuz_korea_legacy')`, `/home/claude/og` → `OG_ROOT`(저장소 루트), `/home/claude/data` → `V3_ROOT/data`. 19a §A의 절대 경로 목록을 체크리스트로 쓰고, 바꾼 줄을 커밋 본문에 전부 나열한다. 다른 코드는 한 글자도 바꾸지 않는다(19 §3.9).
2. `tools/fetch_data.py` — 서브커맨드 `fonts | ne | tiles | flags | commons | media | all`. 출처·수치는 19a §B·§H와 07 §3.2, 14 §10.4를 따른다(Commons 요청 간격 15초, 표준 폭만, `PIL.verify`, 429 시 60~90초 대기). 산출물은 전부 `V3_ROOT/data`·`assets/fonts/.cache` 등 **gitignore 경로**. 폰트 단계는 `PHASE1_ENV_SETUP_WSL2.md` §5를 그대로 코드화(D3).
3. `requirements-engine.txt` — WSL2 문서 §4의 모듈 목록 고정. `requirements.txt`에서 `playwright` 제거.
4. `tools/golden_compare.py` — `docs/handoff/golden/golden_frames.json`의 25 앵커를 **현재 plan.json으로 시각 재계산**(anchor `TITLE`=title.t0, `END`=end.t0 … 규칙은 golden_frames.json의 anchor/offset 그대로) → `legacy_v3/render3.py --preview` 호출 → PNG별 MAD(/255) 표 + 차이 히트맵 + `prev/golden_compare.json`. 임계 2/255 초과 컷 목록 출력.
5. `tools/contact_sheet.py` — 4열 427×240, 컷마다 앵커·시각 라벨(11 §5). 전환 구간 8컷 모드(`--transitions`).
6. `docs/handoff/reports/PHASE1_RUNBOOK_WSL2.md` — 사용자가 순서대로 붙여 넣을 명령: check_env → fetch_data all → plan3(**`--tts edge`** 명시, ElevenLabs 키가 있어도 골든은 edge) → prep3 → media3 → render3 --preview → golden_compare → 전체 렌더(청크) → mix3 → mux → 결과 파일 목록과 회신 양식(총 길이, land-miss, MAD 표, sheet.jpg 경로).
7. 클라우드 스모크: 이 컨테이너에서 `fetch_data fonts ne flags`와 `plan3`(edge-tts 네트워크 가능 시)까지 돌려 도구가 동작함을 보인다. 타일·Commons·rembg는 네트워크 정책상 실패할 수 있다 — 실패하면 그 사실만 `progress`에 적고 우회 구현을 하지 않는다(P6).

## 2. 합격 조건 (검증 가능한 형태)

- `python -m py_compile legacy_v3/*.py tools/*.py` 통과, `pytest -q` 388 passed 유지(+ 새 도구 단위 테스트: 앵커 재계산 함수, MAD 계산, 타일 범위 계산 `19a §H` 값 W z5 x18–28/y11–17 등 3건 이상).
- `git diff --stat docs/handoff/reference_code/v3_hormuz_korea/render3.py legacy_v3/render3.py`가 경로 줄만 보여 준다(본문에 나열).
- `tools/golden_compare.py --dry-run`이 25개 앵커 시각을 plan.json 없이도 골든 절대 시각으로 출력한다.
- 런북의 모든 명령이 실제 파일·플래그와 일치한다(문서와 코드 불일치 0).

## 3. 하지 않는 것

- render3.py 분해·수치 변경(Phase 2). `dip` 인자형 변경(Phase 2). 새 이벤트 타입.
- WSL2 결과가 오기 전에 "Phase 1 통과"를 선언하는 것. Phase 1 `phase_report`는 사용자 WSL2 산출물(sheet.jpg, golden_compare.json, 총 길이)을 근거로만 쓴다.

## 4. 보고

끝나면 `progress`(커밋 목록, 스모크 결과, 런북 경로). 그 뒤는 사용자 WSL2 회신 대기. 회신이 오면 나(Fable)가 판정 지침을 낸다.
