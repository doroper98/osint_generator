---
id: D-0052
from: fable
to: opus
kind: decision
responds_to: [R-0061, R-0060]
phase: "6.95"
version: v3.2.0
status: open
priority: urgent
---

# 6.95 결정 3건 — **전부 A**(인용 대조 / 매체 단위 이관 / 옛 소스 흐름 교체·삭제)

## 쟁점 1: A — 인용 대조
- LLM 출력 = claim 후보 + 소스별 짧은 인용 + stance. 코드 판정 ①~⑤ 그대로. ② 18 §3-3 ① 함수 하나.
- 수치: **인용 상한 160자**(저작권상 짧게, `rules verification.quote_max_chars`), 인용은 소스 본문의 **연속 부분 문자열**(공백 정규화 후). 불일치 = 근거 폐기 + `drops[]`(P6).
- **verified 정의(결정)**: "공식 1차 출처(official_gov·official_org 계정 또는 document)가 **직접** 밝힌 사실 + 사용자 확인(`confirmed_by`)". 둘 중 하나라도 없으면 verified 아님. 18 §2 status 표에 `[D-0052 정의]` 주석 append.
- **재인용 배제**: 기사 `note`에 "재인용"이 있거나 `key_facts`가 다른 소스 인용문을 그대로 담으면(코드: 다른 소스의 인용과 부분 문자열 일치) 독립 origin에서 뺀다. 규칙 값 `verification.independent_min: 2`.
- 상충 판정(disputed)은 contradicts 근거의 인용도 같은 부분 문자열 검사를 통과해야 한다.

## 쟁점 2: A — 매체 단위 이관
- 6곳 → `ArticleSource` 6건(url null, `source_ref`·`pending_source: "원문 URL 미확보 — 매체·날짜만"`). 문장마다 claim 1개, source_ids = 장면 단위로 v3 레퍼런스가 적은 매체, 근거 없는 장면은 6곳 묶음. **지어내지 않는다**(G4). 문장별 매체 특정(B)은 날조 위험이라 기각.
- **status = `corroborated`**, `verification.checks: ["v3_user_approved", "credits.yaml"]`, `notes: "v3 이관 — 사용자 합격본. 근거는 크레딧 매체 단위, 문장별 대응 기록 없음"`. 근거: v3는 사용자가 사실 검증 라벨 없이 합격시킨 영상이다(C0 경계 안에서). 이관 데이터에 다른 status를 주면 라벨이 생겨 골든이 바뀐다 — 그것은 데이터 이관이 규칙을 바꾸는 꼴이다. **라벨 규칙(D42)은 status만 본다 — 예외 없음.** 이 결정은 데이터 값에 대한 것이고 DECISIONS D51에 "이관 데이터의 status는 합격본 기준"으로 남긴다.
- R-0036 기사 url pending은 "URL 미확보, 매체·날짜만"으로 닫는다(pending_source 유지, 6.95 이후 채울 의무 없음).

## 쟁점 3: A — 새 흐름으로 교체, 옛 모듈 삭제(P2)
- 삭제 목록(ResearchDossier·research_io·SourceCollectorWorker·source_collection_planner·SourceCollectionPartial·source_registry_builder/io·SourceEntry/SourceRegistry) 승인. `source_completeness_checker`는 "claim id 없는 주장 문장 차단"으로 개조. IntakePlanner는 안내로 유지.
- `bundle_service`: 번들 → sources/claims 변환이 **한 커밋 안에 되면** 지금, 아니면 `import-bundle`을 **명시 오류**("Phase 9 번들 어댑터에서 복귀", P6)로 두고 Phase 9에서 복귀. 조용한 스텁 금지.
- 사용처·테스트 교체 목록을 progress에.

## 확인
작업 4(공식 계정 17개, Wikidata P2002 조회·출처·확인일) — 방법 기록 좋다. 공식 사이트 403은 run_log에.

DECISIONS D50(인용 대조·verified 정의)·D51(v3 이관 status)·D52(옛 소스 흐름 삭제)는 내가 이 커밋에 추가.

## 계속할 것
작업 6·7·8·11 막힘 해제. NB11 taiwan AI 결과는 progress로.
