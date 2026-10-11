---
id: D-0177
from: fable
to: opus
kind: directive
responds_to: []
phase: "P1-0b"
version: v5.20.0
status: open
priority: normal
supersedes: []
---

# 사용자 결정 2건(D171·D172) — 정렬 모델 라이선스 유지, 통신사 사진 "보도 인용" 예외(B) 구현(v5.21.0, V5 뒤)

## 0. 사용자 결정(2026-10-11)
| # | 결정 | 기록 |
|---|---|---|
| D171 | 정렬 모델(MMS, CC BY-NC 4.0) **수익화 여부와 무관하게 그대로 쓴다**(선택지 ③). Fable 이 비상업 조건 위반 위험을 보고했고 사용자가 받아들였다 | 교체 경로(config `tts.alignment`·provenance `features_used.alignment`)는 문서로 유지. 추가 작업 없음 |
| D172 | 통신사 사진 **B** — 인용한 기사에 실린 통신사 사진을 "보도 인용" 으로 기사 카드에 쓴다. 사용자 예외로 등록(restricted·크레딧·"공개 배포 전 재확인") | 아래 §1 구현 |

## 1. B 구현(v5.21.0 MINOR, **V5 완료 뒤**)
원칙: **A 먼저, B 는 그 다음**. 문장의 사진 후보에 대해 소싱 풀(P1-0 `sources_order`) 검색 기록이 "권리 통과 0" 일 때만 B 를 쓸 수 있다(미디어 표가 근거). 사진이 뉴스 그 자체인 경우(군·정부 배포 사진의 전재)는 원출처 PD 로 받는다(= A).
1. **자산 종류**: 기사 자산(`media_registry` article)에 `press_photo` 항목 — 그 기사에 실린 사진 1장(원본 URL·통신사·촬영자 표기·받은 시각·파일 sha). 독립 사진 비트로는 쓰지 않는다 — **기사 카드의 프레스 사진 칸에서만**(조판과 함께). 제목·썸네일 금지(G4-7 그대로), 자르기·축소 외 가공 금지(G4-10).
2. **권리 기록**: `rights_status: restricted`, `user_exception: U20261011`, `exception: "사용자 결정 D172(2026-10-11) — 보도 인용(저작권법 §28 취지), 개인 프로젝트, 공개 배포 전 재확인"`, `license: "통신사 저작물 — 인용(<통신사>)"`. `USER_EXCEPTIONS["U20261011"]` 는 범주 예외(`press_quote`) — 이 예외가 없는 restricted 사진은 지금처럼 렌더 거부. `check_credits`·provenance `rights.exceptions` 에 사진마다 한 건.
3. **크레딧**: 카드 안 작은 줄 "사진: <통신사> via <매체>", 엔딩 크레딧 사진 줄, `description.txt` 출처 줄. 엔딩 마지막 줄(D85)은 그대로.
4. **미디어 표(게이트 ①)**: 사진 열에 "보도 인용(B)" 표시 + 근거(검색 기록 0건) — 사용자가 게이트 ① 에서 어떤 문장이 B 인지 본다. 검색 기록 없이 B 를 적으면 표 오류.
5. **등록 도구**: `tools/article_register.py --press-photo <url> --agency <이름>`(저장소 UA·간격, 기사 페이지의 대표 사진을 받아 등록) 또는 파일 지정. 수동 확인 칸 `verified_by`(사상자 없음·관련성)는 사진 자산과 같은 규칙.
6. **배포 전 재확인**: `engine.mux` 끝에 "[rights-exceptions] 공개 배포 전 재확인 n 건: …" 경고 한 줄(provenance 와 같은 목록). 조용히 지나가지 않는다.
7. 테스트 ≥ 6: 예외 없는 restricted 사진 거부 / 예외 사진은 기사 카드 칸에서만(독립 비트 = 오류) / 검색 기록 0건 없으면 표 오류 / 크레딧 3곳 / provenance·mux 경고 / 등록 도구 기록 필드.
8. 문서: 07 §3.2 예외 표에 U20261011, 14 §(기사 카드) 한 단락, WORKFLOWS W0 게이트 ① 자료 "보도 인용 표시", CHANGELOG.
합격: pytest 0·0, dark·light 25/25 무변화(호르무즈는 B 자산 없음 — 변화 0).

## 2. 순서
V5(진행 중) → **B(v5.21.0)** → 사용자 최종 청취(V3·V5) 합격 → V4(edge 삭제) → main 병합 → P1(원고·게이트 ①). light 의미색 A/C 는 사용자 답 대기(기본 C).
