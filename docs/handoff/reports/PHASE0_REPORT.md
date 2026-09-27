<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [phase0-report]
depends_on: [docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/DECISIONS.md]
last_review: 2026-09-27
author: Opus 실행 세션 (2026-09-27)
-->

# Phase 0 보고서 — 관성 차단 (v2.0.0) · **완료**

## 0. 한 줄 상태

19 §5 커밋 7개를 모두 마쳤습니다. §5.8 합격 기준 5개가 모두 충족됐습니다.
처음 보고(`dc8ba13`) 때 보류됐던 커밋 ②는 사용자 허용(2026-09-27)으로 실행했습니다.

| 19 §5 커밋 | 커밋 |
|---|---|
| ① 헌법 개정 | `65fe4e1` |
| (추가) 20번 문서 편입 | `8701521` |
| ③ bundle/ 이관 (②보다 먼저, D12) | `7e97513` |
| ④ rules SSOT + config 단일화 | `d45f0ab` |
| ⑤ 프롬프트 파일 분리 | `8663ebc` |
| ⑥ 관성 방지 테스트 8종 | `d6747b3` |
| ⑦ 중간 보고서 | `dc8ba13` |
| ② 준비분: LegacyRemovedError (사용자 지시로 삭제보다 먼저 푸시) | `6a5da48`* |
| ② 레거시 archive 후 삭제 | `bd37b58` |
| 버그 테스트 2건 → 올바른 기대값 + strict xfail (D18) | `e19d830` |
| ⑦ 최종 보고서 + WSL2 설치 절차 | (이 커밋) |

\* 이 커밋만 단독으로는 옛 CLI 테스트 15건이 실패합니다. 세 파일은 바로 다음 커밋 `bd37b58`에서 삭제됐습니다.

## 1. 변경 요약

- **헌법**: CLAUDE.md C0(영상 기준 → `docs/handoff`, 되돌리면 안 되는 목록), C0.1(byte-equal 비적용),
  C11(관성 방지 P1~P12). GOAL.md G0·G1(v2 산출물)·G3 legacy 배너·G4-13~20·G5·G7(영상 기준 정본).
  옛 항목은 삭제하지 않고 `[deprecated v2.0.0]` 마킹(DOCS_GOVERNANCE).
- **20번 문서**: 사용자가 세션 중 전달한 `20_GENRE_EXTENSION_FREE_PRODUCTION.md`를 원문 편입.
  구현(Phase G1~G4)은 20 §12대로 Phase 6.9 이후. Phase 0에서는 코드를 미리 만들지 않음(D10).
- **bundle/**: `bundle_to_video.py`의 순수 함수를 본문 무변경 이관(text 30항목, charts 22항목).
  `norm_map` 계열은 삭제 대상 SVG 메타에 묶여 조용한 드롭 통로가 되므로 제외(D11).
- **rules/video_rules.yaml**: 19 부록 A + D6 확정값 + 20 §7 상투어 후보 3개. `load_rules()`는
  extra=forbid, `rules_hash()`는 sha1.
- **config**: `engine:`(854×480 / 1920×1080 @24), `llm` 타임아웃 2종, `tts:` 재정의. 워커 타임아웃과
  ElevenLabs 모델 기본값을 config에서 읽음. 서브커맨드마다 stderr에 `effective_config` 1줄.
- **prompts/**: system 5종 + user 템플릿 4종 + 카테고리 가이드 YAML. 렌더 결과는 원문과 바이트 동일.
  예외는 `script.md`의 "영상 길이 4~6분 제한" 문단 삭제(G4-13). `TaskResult.worker_provenance` 추가.
- **tools/check_env.py**: Phase 1 첫 관문.

## 2. 이번 Phase의 결정 (DECISIONS.md D9·D10~D18)

| ID | 요지 |
|---|---|
| D10 | 20번 문서 편입. 구현은 Phase 6.9 이후, Phase 2 카메라는 `(x, y, w)` 일반화 여지만 유지 |
| D11 | `norm_map`·`_load_map_metas`·`_project_merc` 이관 제외(15 P6 > 19 문면), 참고 사본만 보존 |
| D12 | 커밋 순서 ③→②. 19 §5.2의 grep 0건 조건은 §5.3 출처 주석과 모순 → AST 테스트가 정본 |
| D13 | 커밋 ② 권한 거부 → 준비분은 로컬 stash, ④·⑤ 선행. 사용자 확인 대기 |
| D14 | ④ 세부: decimal_policy D6값, 옛 render/tts 미사용 키 제거, 타임아웃 키 참조, stderr 덤프 |
| D15 | ⑤ 세부: user 템플릿도 분리, 거버넌스 헤더는 로더가 제거, `worker_provenance` optional |
| D16 | ② 의존 2검사는 strict xfail(D13) — ② 적용 후 실제로 XPASS → 마커 제거 완료 |
| D17 | ② 세부: `test_collage_models`는 DesignSheet 테스트만 제거(유지 모델 검사 보존), BGM mp3는 추적 유지 |
| D18 | 버그 테스트 2건은 올바른 기대값 + strict xfail (사용자 지시) |
| D9 | Phase 1 실행 위치 = 사용자 로컬 WSL2 (사용자 결정) |

## 3. 테스트 결과

| 시점 | 결과 |
|---|---|
| 기준선(v1.2.2, 착수 전) | 438 passed, 87 subtests |
| 중간 보고(② 보류) | 470 passed, 8 xfailed |
| **최종(v2.0.0)** | **388 passed, 8 xfailed**, 70 subtests |

통과 수가 줄어든 것은 삭제한 옛 경로 테스트 6파일(약 80건) 때문입니다. 실패는 0건입니다.

xfail 8건은 모두 strict이며 이후 Phase 과제입니다. 19 부록 B는 "xfail 4"라 했지만 8건인 이유는 둘입니다.
`test_no_silent_fallback`을 (a)(b)(c) 세 개로 나눴습니다. 그리고 버그 테스트 2건(D18)이 추가됐습니다.

| xfail | 해제 Phase |
|---|---|
| no_silent_fallback (a) RegistryError · registry_complete | 2 |
| bundle_text 개월·경어체 버그 2건 · prompt_schema_parity | 4 (parity는 6.9까지) |
| no_silent_fallback (b) RightsError | 6.5 |
| no_silent_fallback (c) 손상 manifest · provenance_e2e | 6.8 |

19 §5.8 자동 검증:

| 기준 | 결과 |
|---|---|
| anti_inertia 4종(`no_legacy_imports`·`prompts_from_files`·`constitution`·`single_config`) | ✅ 전부 통과 |
| 전체 pytest | ✅ 388 passed, 실패 0 |
| `orchestrator.main version` | ✅ `2.0.0` |
| `archive/hyperframes-briefing` 원격 존재 | ✅ `9dcda27` (hyperframes 224·remotion 28 파일 보존 확인) |
| `hyperframes/`·`remotion/` 부재 | ✅ |

추가 검증: `python -m orchestrator.main build-scene demo` → `LegacyRemovedError` 메시지, exit 3.
`grep hyperframes` 결과는 0이 아닙니다. 남은 건 출처 주석·docstring·archive 브랜치 이름뿐입니다(D12, AST 테스트가 정본).

## 4. 프리뷰 / provenance

- 프리뷰 컨택트 시트: **해당 없음** — Phase 0은 영상에 영향이 없습니다.
- provenance: **해당 없음** — 엔진이 아직 없습니다. 워커 단위 `worker_provenance`(프롬프트 sha1·
  rules_hash)는 이번에 배선했습니다.

## 5. 발견 사항 (결정을 바꿀 수준만)

1. **기존 버그 2건**: `tts_of("18개월")` → "열여덟 개월", `to_polite("낮춘다")` → "낮춘습니다".
   올바른 기대값 테스트를 strict xfail로 두었습니다. Phase 4에서 고칩니다.
2. **19 내부 모순 1건**: §5.2의 `grep hyperframes` 0건 조건은 §5.3의 출처 주석 의무와 양립하지 않습니다.
   AST 테스트를 판정 기준으로 삼았습니다(D12).
3. **BGM mp3(37MB)가 git에 추적 중**입니다. RIGHTS.md에 "전달 위해 임시 커밋"으로 기록돼 있습니다.
   추적을 해제하면 pull할 때 사용자 로컬 파일이 지워지므로 그대로 두었습니다. history 정리·LFS 전환은 별도 결정 대상입니다(D17).

## 6. 사용자 결정 상태

| ID | 상태 |
|---|---|
| ② 실행 | ✅ 허용 → 완료 |
| D4 GOAL G3 개정안(19 부록 C) | 사용자 검토 중. 답변 전까지 G3는 legacy 배너 |
| D9 Phase 1 실행 위치 | ✅ 로컬 WSL2 |
| D5 제한 휘장 / D7 agents_reviewer 스키마 | Phase 5 / 9에서 질문 |

## 7. Phase 1 착수 전 준비 — WSL2 환경

절차는 `docs/handoff/reports/PHASE1_ENV_SETUP_WSL2.md`에 있습니다.

- 같은 절차를 Ubuntu 24.04 클라우드 컨테이너에서 실행했습니다. `check_env`가 11건 누락에서 **20 ok / 0 missing**이 됐습니다.
- 폰트 이름 8개도 fontconfig에서 의도한 굵기로 해석됐습니다(R1 확인).
- **사용자 WSL2에서 직접 돌린 결과는 아직 없습니다.** 같은 문서 8단계 출력을 받으면 Phase 1을 시작합니다.

## 8. 다음 Phase 계획 (승인 후)

- **Phase 1 골든 재현(v2.0.1~)**: `check_env` 통과 → `legacy_v3/`(경로만 환경변수화) →
  `tools/fetch_data.py`(NE·지형 타일·flag-icons·폰트·Commons) → plan→prep→media→render→mix→mux →
  `tools/golden_compare.py`로 25컷 앵커 대조 + 컨택트 시트. 합격선 4:52±1초, 854×480@24, `land-miss=['MV']`.
- Phase 1 통과 후 main 첫 머지(ff-only, M1).
- Phase 2 분해 시 20번 문서 대비: 카메라·`View`를 `(x, y, w)`로 일반화할 수 있는 경계만 유지(D10).
