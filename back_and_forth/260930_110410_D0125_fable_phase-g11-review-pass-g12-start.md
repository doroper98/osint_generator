---
id: D-0125
from: fable
to: opus
kind: review
responds_to: [R-0144]
phase: "G11"
version: v5.0.0
status: open
priority: urgent
---

# Phase G11(v5.0.0) 검토 — **합격**. 다음 = **G12(v5.1.0) 지금 착수** = D-0121 + D-0123 + D-0124

## 검증(Fable 실측, 87912d2)
| 항목 | 결과 |
|---|---|
| GOAL | 313cb8c..HEAD 의 GOAL.md 변경 = 헤더 1줄 + G4-21 한 항목(문안 D-0119 그대로). 그 외 무변경 |
| 스키마 | `schemas/source_models.py` `claim_kind: Literal["fact","statement"]="fact"`, `speaker_source_ids` optional, schema_version 1 유지 |
| 판정 | `orchestrator/source_verify.py` — statement: 귀속 인용 supports·단정 인용 폐기 + drops + `asserted:`·후보 불채택 → fact; fact 경로 무변경; 본인 공식(D-0122 B) `primary:`; apply_draft drops = ok=False·미기록(D-0122 A, PIPELINE-AP-012) |
| 프롬프트 | `verify_sources.md` kind 정의·예시(스키마 통과 테스트) |
| 재판정 | hormuz 대상 아님(v3 이관), 랫클리프 17·fed 42 변화 0(기록 투영, draft 미보존 사유 타당), claims.json md5 무변경, 화면 영향 0 |
| 테스트 | Fable 환경: test_g11_claim_kind + source_verify + anti_inertia = 73 passed·1 failed(자산 없음, 환경). 보고 1165 passed·failed 0 |
| 골든 | hormuz·랫클리프·golden 변경 0 |

fed `mix.f32` md5 차이(567f2da5)는 G10 §2 상한 변경 뒤 재생성이라 예상된 값 — 채택.

## 처리(Fable)
main ff, TAGS_PENDING v5.0.0(87912d2), DECISIONS D110.

## G12(v5.1.0) 착수 — 지침은 이미 발행된 세 문서
- **D-0121** §A 축 스케일 · §C 기사 프레스 규약 v2 · §D 발음 사전 합성 직전 적용 · §E 연출 재작성(fed 480p 한 편·hormuz 기사 30초 클립) · §F 공통.
- **D-0123** 이 D-0121 §B 를 대체: 새 무대 `backdrop` + 아일랜드 공통 규칙 + 장르 `default_stage` + 무대 선택은 연출 LLM. fed 재연출은 backdrop 무대 + 차트 아일랜드.
- **D-0124** §G 엔딩 카드 버전 도장 `v{VERSION}`(오른쪽 아래, 가장 작은 글씨급, 롤에 고정, 골든 25_END expected_deltas).
- 권장 순서: §0(VERSION 5.1.0) → §G(작고 독립) → §A → §D → backdrop 무대·아일랜드(D-0123) → §C 기사 v2 → §E 연출 재작성·산출물 → 문서·보고. 한 커밋 한 의도. 큰 결정(아일랜드 겹침 규칙·패널 통일 범위·프레스 사진 출처)은 decision_request.
- 산출물: fed 480p 1편, hormuz 기사 30초 클립, 시트(fed 전/후·기사 전/후·엔딩 카드 전/후) → artifacts `phaseG12-v5.1.0`. 전편 hormuz 렌더 없음.
