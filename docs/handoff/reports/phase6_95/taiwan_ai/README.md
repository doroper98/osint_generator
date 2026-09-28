<!--
tier: 3
last_synced_with: v3.2.0
ssot_for: [report-phase6_95-taiwan_ai]
depends_on: [docs/handoff/17_AI_DIRECTOR_VISUAL_QA_PROMPTS.md, orchestrator/ai_direction.py, tools/ai_direction_run.py]
last_review: 2026-09-28
-->
# taiwan_ai — hormuz 밖 원고로 AI 연출 1회 실증 (D-0050 NB11, D-0051 §0-2)

합격 조건이 아니라 **일반화 판단 자료**다. 입력 = `projects/taiwan_strait` 의 원고·지오·라벨·크레딧 복사본(`projects/taiwan_ai`),
direction.yaml 없음. 예시는 hormuz 그대로(`prompts/examples/hormuz_direction.yaml`), 루프 상한 2(rules `qa_checks.visual_qa_loop_max`).
실행: `python -m script.plan projects/taiwan_ai --tts edge` → `python tools/ai_direction_run.py projects/taiwan_ai --preview auto`.

**한계부터**: taiwan_strait 원고는 "권역 준비 확인용 최소 원고"라 **2문장·22.6초**뿐이다. 장면·패널·미디어가 없어서 연출 문법의
일반화(패널 선택, 카메라 이동, 미디어 배치)는 이 실증으로 판단할 수 없다. 판단할 수 있는 것은 "hormuz 에 맞춘 프롬프트·루프가
다른 권역·다른 자산 구성에서 멈추지 않고 도는가"와 "어디서 걸리는가"다.

## 실행 세 번

| 실행 | 결과 | 판정(검수 hard/soft) | 폴더 |
|---|---|---|---|
| 1 | **연출가 실패** — 연출가가 `sound:`(BGM)를 넣었는데 크레딧에 음악 행이 없어 RightsError → 재요청 1회에서 `sound.bgm: null` 로 스키마 위반 → 중단(P6 대로) | — | `attempt1/` |
| 2 | 크레딧에 음악 행 추가(hormuz 와 같은 곡·같은 표기) 후 완주. 선택 v2 | v1 2/3 → v2 0/5 → v3 1/3 | `run2_before_frames_fix/` |
| 3 | frames.json 버그 수정(아래 F2) 후 완주. 선택 v2 | v1 2/4 → v2 0/3 → v3 0/4 | `run3/` |

실행 3 시트: `run3/sheet.v1.jpg`~`v3.jpg`. 결정적 검사 hard 는 전 회차 0. provenance `run3/provenance.json`
(`stages.ai_direction`·`visual_qa` true, `ai_direction.selected.version` 2).

## 발견 (일반화 판단 자료)

| # | 무엇 | 성격 | 처리 |
|---|---|---|---|
| F1 | 연출가는 BGM 을 기본으로 넣는다. 음악 크레딧이 없는 프로젝트에서는 연출이 권리 검사에 걸리고, 재요청은 `bgm: null` 로 스키마를 어긴다 | 프로젝트 준비물·프롬프트 계약 | 이번엔 크레딧에 음악 행을 넣어 진행. 후보: 연출가 입력에 "쓸 수 있는 음악 목록(없으면 sound 블록 금지)"을 주기 — Phase 8(오디오) 과제로 넘김 |
| F2 | `prev/frames.json` 이 문장이 끝난 뒤(엔딩 카드)에도 직전 문장을 "진행 중"으로 적어 검수가 **거짓 order hard 2건**을 냈다. 실행 2의 판정 진동(0 → 1)도 이것 | **코드 버그** | 수정 `94acce0`, PIPELINE-AP-009. 실행 3에서 진동 사라짐(v2·v3 hard 0) |
| F3 | 엔딩 카드 뒤로 지도 라벨·마커가 비친다(실행 3 v1 hard 2). 수정 LLM 이 마커 끝 앵커를 `{card: end}` 로 바꿔 해결 | 연출 | 루프가 스스로 고침(v2 hard 0) — 루프가 제 역할을 한 사례 |
| F4 | 수정 2회차가 "변경 없음 — 렌더러 몫" 3건만 내서 v3 = v2(바이트 동일). provenance `used_version` 이 3으로 적힌다(선택은 2) | 기록 모호 | 같은 바이트면 선택 판 번호를 쓰도록 고칠 후보(비차단) |
| F5 | 반복 soft: 도시 라벨·마커 부제 글자가 작고 대비 낮음, 엔딩 카드 아래쪽이 휑함, 미디어 0개 | 렌더러·자산 | 연출 필드 밖이라고 수정 LLM 이 정직하게 남김. 미디어는 확보된 mid 가 없어 지어내지 않음(권리 검사) — 올바른 거절 |
| F6 | `--preview auto` 가 22초 영상에서 컷 3장만 뽑았고 그중 2장이 엔딩 카드 | 샘플링 | 짧은 영상에서 본편 컷이 1장뿐이라 검수 근거가 얇다. Phase 7 후보(샘플 규칙) |

## 결론 (Opus 판단, 합격 판정 아님)
- 루프 자체는 다른 원고에서도 **멈추지 않고 돈다**(F1 은 프로젝트 준비물 누락이 원인이고 오류로 멈춘 것은 P6 대로).
- hormuz 에서 보였던 "2회차가 오히려 나빠지는" 진동의 한 원인은 검수 입력 버그(F2)였다. 수정 후 이 짧은 원고에서는 진동이 없다.
- 연출 문법 일반화(패널·카메라·미디어)는 이 원고로 판단 불가 — 장면이 여럿인 비(非)호르무즈 원고가 필요하다. 6.95 e2e 원고(소스 인테이크 결과)로 다시 시험하는 것을 제안한다.
