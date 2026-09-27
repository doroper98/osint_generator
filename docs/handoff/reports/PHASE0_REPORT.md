<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [phase0-report]
depends_on: [docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/DECISIONS.md]
last_review: 2026-09-27
author: Opus 실행 세션 (2026-09-27)
-->

# Phase 0 보고서 — 관성 차단 (v2.0.0) · **중간 보고: 커밋 ② 보류**

## 0. 한 줄 상태

커밋 7개 중 6개를 완료했습니다. **레거시 삭제(커밋 ②)만 보류**입니다. 실행 환경의 자동 권한
분류기가 대량 `git rm`을 거부했습니다. 우회하지 않았고, 사용자 승인을 기다립니다.

| 19 §5 커밋 | 상태 | 커밋 |
|---|---|---|
| ① 헌법 개정 | 완료 | `65fe4e1` |
| (추가) 20번 문서 편입 | 완료 | `8701521` |
| ③ bundle/ 이관 (②보다 먼저, D12) | 완료 | `7e97513` |
| ② 레거시 archive 후 삭제 | **보류** — archive 브랜치 생성·푸시는 완료, 삭제는 거부됨 | — |
| ④ rules SSOT + config 단일화 | 완료 | `d45f0ab` |
| ⑤ 프롬프트 파일 분리 | 완료 | `8663ebc` |
| ⑥ 관성 방지 테스트 8종 | 완료(② 의존 2검사는 strict xfail) | `d6747b3` |
| ⑦ 이 보고서 | 완료 | (이 커밋) |

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

## 2. 이번 Phase의 결정 (DECISIONS.md D10~D16)

| ID | 요지 |
|---|---|
| D10 | 20번 문서 편입. 구현은 Phase 6.9 이후, Phase 2 카메라는 `(x, y, w)` 일반화 여지만 유지 |
| D11 | `norm_map`·`_load_map_metas`·`_project_merc` 이관 제외(15 P6 > 19 문면), 참고 사본만 보존 |
| D12 | 커밋 순서 ③→②. 19 §5.2의 grep 0건 조건은 §5.3 출처 주석과 모순 → AST 테스트가 정본 |
| D13 | 커밋 ② 권한 거부 → 준비분은 로컬 stash, ④·⑤ 선행. 사용자 확인 대기 |
| D14 | ④ 세부: decimal_policy D6값, 옛 render/tts 미사용 키 제거, 타임아웃 키 참조, stderr 덤프 |
| D15 | ⑤ 세부: user 템플릿도 분리, 거버넌스 헤더는 로더가 제거, `worker_provenance` optional |
| D16 | ② 의존 2검사는 strict xfail(D13) — ② 적용 시 XPASS가 실패로 잡혀 마커 제거 강제 |

## 3. 테스트 결과

| 시점 | 결과 |
|---|---|
| 기준선(v1.2.2, 착수 전) | 438 passed, 87 subtests |
| 현재(v2.0.0, ② 보류) | **470 passed, 8 xfailed**, 87 subtests |

19 §5.8 자동 검증:

| 기준 | 결과 |
|---|---|
| anti_inertia 4종 | 3종 통과. `no_legacy_imports`는 xfail(② 보류) — 현재 위반 49건 전부 ② 삭제 대상 파일 |
| 전체 pytest | 통과(xfail 8 = 이후 Phase 6 + ② 보류 2) |
| `orchestrator.main version` | `2.0.0` ✅ |
| `archive/hyperframes-briefing` 원격 존재 | ✅ `9dcda27`(collage tip) |
| `hyperframes/`·`remotion/` 부재 | ❌ ② 보류 |

## 4. 프리뷰 / provenance

- 프리뷰 컨택트 시트: **해당 없음** — Phase 0은 영상에 영향이 없습니다.
- provenance: **해당 없음** — 엔진이 아직 없습니다. 워커 단위 `worker_provenance`(프롬프트 sha1·
  rules_hash)는 이번에 배선했습니다.

## 5. 발견 사항 (결정을 바꿀 수준만)

1. **기존 버그 2건을 테스트로 고정**했습니다. `tts_of("18개월")` → "열여덟 개월",
   `to_polite("낮춘다")` → "낮춘습니다". 명세대로 현재 출력을 고정했고 Phase 4에서 고칩니다.
2. **이 클라우드 컨테이너는 Phase 1을 돌릴 수 없습니다.** `check_env` 결과 pycairo·shapely·scipy·
   edge-tts·cairosvg·fonttools·rembg와 폰트 4종이 없습니다. ffmpeg는 imageio-ffmpeg로 있습니다. D9 결정이 필요합니다.
3. **19 내부 모순 1건**: §5.2 검증의 `grep hyperframes` 0건과 §5.3의 `# moved from hyperframes/...`
   주석 의무는 양립할 수 없습니다. AST 테스트(주석·docstring 제외)를 정본으로 삼았습니다(D12).

## 6. 사용자에게 필요한 것

1. **커밋 ② 진행 방식** (지금 막힌 유일한 항목)
   - 대상: `hyperframes/`(175파일), `remotion/`, `design_sheets/`, 쇼츠·재빌드 문서 3종,
     `orchestrator/{scene_builder,scene_io,render_io,subtitle_align,audio_service,audio_io,audio_demo}.py`,
     해당 테스트 5종 + collage 스키마 테스트 2종. 원본은 `archive/hyperframes-briefing`에 보존돼 있습니다.
   - 선택지: (a) 이 세션에서 `git rm` 실행을 허용 (b) 사용자가 로컬에서 직접 실행 후 푸시.
   - 준비분(`main.py` LegacyRemovedError, `orchestrator/errors.py`)은 로컬 stash에 있습니다.
     이 컨테이너가 사라지면 stash도 사라지므로, (b)라면 19 §5.2 표대로 다시 만들면 됩니다.
2. **D4** — GOAL G3 개정안(19 부록 C, 16개) 승인 여부. 승인 전까지 G3는 legacy 배너 상태입니다.
3. **D9** — Phase 1 실행 위치(사용자 로컬 WSL2 권장 / apt 가능한 클라우드).
4. D5(제한 휘장)·D7(agents_reviewer 스키마)는 해당 Phase(5·9)에서 묻겠습니다.

## 7. 다음 Phase 계획 (승인 후)

- **Phase 0 마무리**: 커밋 ② → strict xfail 2개가 XPASS로 실패 → 마커 제거 → §5.8 5개 전부 확인.
- **Phase 1 골든 재현(v2.0.1~)**: `check_env` 통과 → `legacy_v3/`(경로만 환경변수화) →
  `tools/fetch_data.py`(NE·지형 타일·flag-icons·폰트·Commons) → plan→prep→media→render→mix→mux →
  `tools/golden_compare.py`로 25컷 앵커 대조 + 컨택트 시트. 합격선 4:52±1초, 854×480@24, `land-miss=['MV']`.
- Phase 2 분해 시 20번 문서 대비: 카메라·`View`를 `(x, y, w)`로 일반화 가능한 경계만 유지(D10).
