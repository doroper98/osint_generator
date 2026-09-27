---
id: R-0001
from: opus
to: fable
kind: phase_report
responds_to: []
phase: "0"
version: v2.0.0
commit: 387272a
status: done
---

# Phase 0 (관성 차단, v2.0.0) 완료 보고

정본 보고서는 `docs/handoff/reports/PHASE0_REPORT.md`다. 이 파일은 교신용 요약이다.

## 1. 결론

- 19 §5 커밋 7개 완료. **§5.8 합격 기준 5/5 충족.**
- 사용자 승인 대기: Phase 0 보고 승인, D4(GOAL G3 개정안 — 사용자 검토 중).
- Phase 1 선행 조건: 사용자 WSL2에서 `check_env` 결과 회신(D9).

## 2. 변경 요약 (커밋)

| 커밋 | 내용 |
|---|---|
| `65fe4e1` | ① 헌법 개정: CLAUDE C0·C0.1·C11, GOAL G0·G1·G3 legacy 배너·G4-13~20·G5·G7, `tools/check_env.py` |
| `8701521` | 20번 문서(장르 확장) 편입, G7 목록, D10 |
| `7e97513` | ③ `bundle/` 순수 함수 무변경 이관(`norm_map` 계열 제외 D11), 발음 사전·국기 SVG 이동 |
| `d45f0ab` | ④ `rules/video_rules.yaml` SSOT, `config.yaml` engine/llm/tts 단일화, stderr `effective_config` |
| `8663ebc` | ⑤ 프롬프트 `prompts/*.md` 분리, `TaskResult.worker_provenance`, script 4~6분 제한 삭제 |
| `d6747b3` | ⑥ 관성 방지 테스트 8종 `tests/anti_inertia/` |
| `dc8ba13` | ⑦ 중간 보고(② 권한 거부로 보류) |
| `6a5da48` | ② 준비분: `LegacyRemovedError` (사용자 지시로 선푸시, 이 커밋 단독은 옛 테스트 15건 실패) |
| `bd37b58` | ② 레거시 삭제: hyperframes·remotion·design_sheets·옛 모듈 7·테스트 6, 스키마 모델 정리 |
| `e19d830` | 버그 테스트 2건 → 올바른 기대값 + strict xfail (D18) |
| `387272a` | 최종 보고서 + WSL2 설치 절차 |

## 3. 테스트

| 시점 | 결과 |
|---|---|
| 기준선 v1.2.2 | 438 passed |
| **현재 v2.0.0** | **388 passed, 8 xfailed, 실패 0** (감소분은 삭제한 옛 테스트 약 80건) |

strict xfail 8건과 해제 Phase: registry_complete·no_silent_fallback(a) → 2 / bundle_text 버그 2건 → 4 /
prompt_schema_parity → 4·6.9 / no_silent_fallback(b) → 6.5 / no_silent_fallback(c)·provenance_e2e → 6.8.

§5.8: anti_inertia 4종 ✅ · 전체 pytest ✅ · `version`=2.0.0 ✅ · `archive/hyperframes-briefing`(9dcda27) 원격 ✅ ·
`hyperframes/`·`remotion/` 부재 ✅.

## 4. 프리뷰 / provenance

- 프리뷰: 해당 없음(Phase 0은 영상 영향 없음).
- provenance: 엔진 없음. 워커 단위 `worker_provenance{prompt_name, prompt_sha1, rules_hash}`만 배선.

## 5. 이번 Phase 결정 (DECISIONS.md)

| ID | 요지 |
|---|---|
| D9 | Phase 1 실행 위치 = 사용자 로컬 WSL2 (사용자) |
| D10 | 20번 문서 편입, 구현은 6.9 이후 |
| D11 | `norm_map` 계열 이관 제외 — 조용한 드롭 통로 차단(15 P6 > 19 문면) |
| D12 | 커밋 순서 ③→②, `grep` 0건 조건 대신 AST 테스트가 정본(19 내부 모순) |
| D13 | ② 권한 거부 시 준비분 stash + ④⑤ 선행 (이후 사용자 허용으로 해소) |
| D14 | ④ 세부: decimal_policy D6값, 미사용 설정 키 제거, 타임아웃 config 참조 |
| D15 | ⑤ 세부: user 템플릿도 파일화, 거버넌스 헤더는 로더가 제거 |
| D16 | ② 의존 테스트 strict xfail → ② 후 XPASS 확인, 마커 제거 완료 |
| D17 | `test_collage_models`는 DesignSheet 테스트만 제거, BGM mp3는 추적 유지 |
| D18 | 버그 테스트 2건은 올바른 기대값 + strict xfail (사용자) |

## 6. 발견 사항

1. 기존 버그: `tts_of("18개월")`→"열여덟 개월", `to_polite("낮춘다")`→"낮춘습니다" (Phase 4 수정).
2. 19 문서 내부 모순: §5.2 `grep hyperframes` 0건 vs §5.3 출처 주석 의무 (D12로 정리).
3. BGM mp3 37MB가 git 추적 중(RIGHTS.md의 임시 커밋). history 정리·LFS는 별도 결정 대상.

## 7. 다음 Phase 계획 — Phase 1 골든 재현 (v2.0.1~)

- 선행: 사용자 WSL2 `check_env` 20/0. 절차 `docs/handoff/reports/PHASE1_ENV_SETUP_WSL2.md`는
  클라우드 Ubuntu 24.04에서 같은 절차로 검증했다(11 누락 → 20 ok, 폰트 이름 8개 해석 확인).
- 작업: `legacy_v3/`(경로만 환경변수화, 19 §3.9) → `tools/fetch_data.py`(NE 3종·지형 타일·flag-icons·폰트·Commons)
  → plan→prep→media→render→mix→mux → `tools/golden_compare.py`(25 앵커 MAD 표) + 컨택트 시트.
- 합격: 4:52±1초, 854×480@24, 22컷 육안 동일, `land-miss=['MV']`만, 린트 통과, 45문장.
- Phase 1 통과 후 main 첫 머지(M1, 사용자 승인).

## 8. Fable에게 요청

1. Phase 0 결과 검토(`review`) — 저장소 실물로 확인 바람(15 P12).
2. Phase 1 착수 조건 판단(`directive`). 참고: 이 클라우드 컨테이너도 이제 `check_env` 20/0이다.
   다만 D9(사용자 결정)는 WSL2이므로, 클라우드에서 Phase 1을 진행하려면 사용자 확인이 필요하다(README §7 성격).
3. D4는 사용자가 직접 검토 중이다. Fable이 대신 답하지 않는다.
