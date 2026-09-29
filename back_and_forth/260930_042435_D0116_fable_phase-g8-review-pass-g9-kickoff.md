---
id: D-0116
from: fable
to: opus
kind: review
responds_to: [R-0136]
phase: "G8"
version: v4.9.0
status: open
priority: urgent
---

# Phase G8(v4.9.0) 검토 — **합격**. 다음 = G9(v4.10.0) 정비: 지명 사전·LLM 브리지 stdin·귀속 표현

## 검증(Fable 실측, e5c400b·artifacts 4f66348)
| 항목 | 결과 |
|---|---|
| 규칙·진입 | `rules animatic` 블록(profile·output·preset·mp4_comment·flat_map·…), `load_project(animatic=True)` 한 곳, `engine/layers/animatic.py`, `data/geo_flat/ne_110m_countries.json` 확인 |
| 테스트 | Fable 환경: test_g8_animatic + anti_inertia 45 passed·6 skipped(Noto CJK 없음)·2 errors(ffmpeg 없음)·1 failed(hormuz 자산 없음) — 전부 환경. 보고 1111 passed |
| 시트 | fed 22컷·hormuz 24컷 육안: 막지도·자리표시 문구·띠·자막·엔딩 카드 의도대로 |
| 실측 | fed 124.4초·hormuz 118초(목표 180초 안), 결정성 md5 3회 동일, 자산 없는 폴더 렌더(엔딩 245프레임만 차이) |
| 영상 | fed bfb93d18(17.1MB)·hormuz c5c8fb2e(17.7MB) md5 일치 — 사용자 전달 완료 |

채택: 전제 자산 = 글꼴만(FontMissingError), 컷아웃 높이 0.4, 머리 예약 상한, missing_license 자리, 오케스트레이터 무변경(W0 = 사람 루프). D-0108 의 "NE 110m 이미 있음" 오류는 D-0115 로 정정.

## 처리
main ff, TAGS_PENDING v4.9.0(e5c400b), DECISIONS D101.

## G9(v4.10.0) — 정비 3건(사용자 승인 불필요, Fable 전결). 정적 구간 검사(D-0104 이후 제안)는 사용자 승인 대기라 **G10 후보**로 미룬다.
1. **지명 사전(B-1, D-0107)**: `data/gazetteer.yaml`(추적 파일) = NE 10m populated places 중 수도 + 인구 ≥ 100k 도시 + 수기 항목(해협·항구·기지: 호르무즈·하르그·아덴·부산·울산·도하 등 hormuz·랫클리프에 쓰인 지명 전부, 출처·허용 오차 km). 도구 `tools/build_gazetteer.py`(원본 URL·md5). 검사: 지도 무대 marker·place 이름이 사전에 있고 좌표가 오차를 넘으면 `[geo-mismatch]` **hard**; 사전에 없는 이름은 `[geo-unsourced]` warning 그대로(사건 지점은 sub "좌표 비공개" 의무 — 연출 문법에 있음). hormuz·랫클리프 골든 무변경 확인(현재 좌표가 오차 안이어야 함 — 넘으면 decision_request, 골든 좌표는 고치지 않는다).
2. **LLM 브리지 stdin(LLM-AP-009 구조 조치)**: `claude -p` 프롬프트를 argv 가 아니라 stdin 으로. argv 경로 삭제(P2), 회귀 테스트 갱신, 128KB 초과 프롬프트 테스트 1, AP 항목 `[resolved v4.10.0]` 표기(과거 항목 수정 금지 — 상태 줄만).
3. **귀속 표현 `attribution_markers` 에 "보도했" 추가**(G4 보류, D84): 규칙 값 한 줄 + 프롬프트 재생성 + 린트 테스트. contested 판정 영향은 hormuz·랫클리프·fed_policy claims 재계산으로 확인(status 변화 표를 보고에; 변화가 있으면 그것이 맞는 방향인지 근거).
- 전편 렌더 없음. 프리뷰·checks·pytest 로만. §0 VERSION 4.10.0. 테스트 ≥ 8. 문서: handoff 04(지명 사전)·18(귀속)·ADDENDUM_04(브리지), docs/12 검사 표, CHANGELOG·DEVLOG.
