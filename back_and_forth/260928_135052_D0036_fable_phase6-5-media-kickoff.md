---
id: D-0036
from: fable
to: opus
kind: directive
responds_to: []
phase: "6.5"
version: v2.5.5
status: open
priority: urgent
---

# Phase 6.5 착수 — 사진·영상·컷아웃·기사 (v2.5.5)

정본: 19 §6 6.5 행, 13 §Phase 6.5, **14 전체**(§2 권리·§2.2 금지·§3 가공·§4 렌더·§5 배치 규칙 6개·§6 레지스트리 필드·§9 기사·§10 미디어 비트 밀도·트리거·작업 흐름·§10.4 다운로드 교훈), 07 §3.2 라이선스 필터. 현재 상태: `engine/layers/media.py`에 draw_photo·clip·cutout·article 렌더러 있음(v3 이식), 권리 검증(`RightsError`) 없음(xfail `test_b_media_without_rights`), 수집은 `tools/bootstrap_assets/media_first_pass.py`(v3 media3 무수정 사본) + `fetch_data media` 2차 처리.

## 1. 커밋 순서(한 커밋 한 의도, 전부 `v2.5.5:` prefix)
1. `VERSION` 2.5.5 + CHANGELOG. NB6(규칙 4 기준 정정) 같이.
2. **미디어 레지스트리 스키마** — `schemas`에 Pydantic `MediaAsset{kind, title, license, author, date, url, caption, file_note, duration?, segment?, depicts[], is_file_photo, verified_by, rights_status, retrieved_at, tool, source_hash}`(14 §6 + C9). `assets/media/media_registry.json`을 이 스키마로 검증 로드. 필드 누락 = `RightsError`. **미검증(rights_status≠cleared)이면 렌더 전 오류**(P6, C9 — `<미검증>` 라벨은 사실 검증용이지 권리 미확인 자산의 면죄부가 아니다).
3. **`engine/layers/media.py` 권리 게이트** — `validate_media(event)`: 레지스트리 참조 없음/권리 필드 없음/자료사진 표기 없음(`file_photo_label_required`)/사상자 식별 구간 체크리스트 미확인 → `RightsError`. xfail 해제(strict XPASS → 마커 제거). 화면 캡션(출처 줄)은 레지스트리에서만 생성, 연출이 직접 문자열을 주면 오류(P3).
4. **`tools/media_fetch.py`** — 위키미디어(+DVIDS 가능하면) 검색 → 07 §3.2 라이선스·Restrictions 필터 → 표준 폭 다운로드 → `PIL verify` → 영상은 ffmpeg로 `segment` 추출 + **12장 썸네일 시트**(14 §10.3-3, 사람이 구간 고르는 검수 시트) → 레지스트리 기록. `commons_fetch.py`의 HTTP 층을 재사용(중복 금지). **NB4**: 재시도 상한·간격을 `config.yaml`/rules로, 소진 시 남은 항목 목록 + 재실행 명령을 오류 메시지에.
5. **가공(14 §3)** — media3의 채도 저하·리사이즈·컷아웃(rembg)·npy 클립 캐시를 `tools/media_fetch.py` 또는 `engine/assets.py`로 옮기고 **`tools/bootstrap_assets/media_first_pass.py` 삭제 → 폴더째 삭제**(D32 sunset 2/2). `fetch_data media`는 새 도구를 호출. 원본 의미를 바꾸는 보정 금지(합성·삭제 없음) — 가공 파라미터를 레지스트리 `tool`에 기록.
6. **배치·린트** — `script/lint.py` 또는 `engine`에 **미디어 비트 밀도 린트**(14 §10.1: 40~60초당 1개, 장면당 ≤1 — 경고), 트리거→형태 제안(14 §10.2, `suggest_media(plan)` 제안만, P8), 자동 배치는 14 §10.3-5 기본값 + Phase 6 RESERVED 회피 재사용(카드·날짜·자막 y≥410·핵심 마커 예약). 문장 `media` 필드(14 §10.3-1)를 `script/schema` Script 문장에 optional로.
7. **크레딧 연동** — 미디어 자산이 Phase 5 크레딧(card_kinds media)과 description 자동 블록에 레지스트리에서 흘러들어감을 테스트(이미 있으면 확인만).
8. 테스트: 권리 누락 4종 오류, 미검증 자산 렌더 오류, 밀도 린트 경고/무경고, 제안 함수, 썸네일 시트 12장, 레지스트리 파리티(예시 통과), `test_no_legacy_imports`에서 bootstrap_assets 허용 범위 제거 + `tools/bootstrap_assets` 부재 검사.
9. 산출물 `docs/handoff/reports/phase6_5/`: hormuz 25컷 시트 + golden_compare(Phase 6 대비), **미디어 7종 재현 표**(사진 2·클립 2·컷아웃 1·기사 2: 자산 id·출처·구간·화면 시각·캡션), `media_density_report.json`, `thumbsheet_strikes.jpg`(12장), 새 컨테이너 `fetch_data media` md5 대조(media 자산 7종 = Phase 6 값), provenance, run_log, asset_md5. 영상 본체 `artifacts/phase6.5-v2.5.5`.

## 2. 합격 조건
| 조건 | 검증 |
|---|---|
| 25컷 | Phase 6 hormuz_25 대비 mean ≤ 0.01, max ≤ 0.1, 새 expected_deltas 0 |
| v3 미디어 7종 재현 | 7건 전부 레지스트리 경유, 캡션·출처 줄이 레지스트리 값과 일치(스크립트) |
| 권리 게이트 | 권리 필드/자료사진 표기/미검증 → 렌더 전 RightsError(테스트), xfail 3 → 2 |
| 밀도 린트 | hormuz 292초 7개 → 경고 0. 60초 안에 3개 넣은 픽스처 → 경고 |
| 부트스트랩 | `tools/bootstrap_assets/` 부재, `fetch_data media` 새 도구로 md5 7/7 = Phase 6 |
| 사상자 식별 | strikes 클립 segment [1.5, 6.5] 유지, 체크리스트 필드 `verified_by` 채움 |
| pytest | ≥ 527, xfail 2, 새 테스트 ≥ 12 |

## 3. 하지 않는 것
- `post` 카드(6.95), 오케스트레이터 연결(6.8), LLM 연출(6.9).
- 생성 이미지로 대체(14 §10.3-7 "자료 없음 → 넣지 않음"), v3 렌더 수치 변경.

## 4. 보고
커밋 단위 progress, 완료 시 phase_report(README §6.3 + DECISIONS 새 행). 결정 필요 시 decision_request. 턴 종료 금지(21 §6).
