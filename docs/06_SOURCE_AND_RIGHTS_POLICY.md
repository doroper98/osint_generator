<!--
tier: 2
last_synced_with: v0.3.0
ssot_for: [rights-policy, source-policy]
depends_on: [05_DATA_SCHEMA_SPEC.md]
last_review: 2026-05-19
-->

# 06 — Source & Rights Policy

## 1. 모든 소스는 source_id를 가진다

- 어떤 자료도 `source_id` 없이 영상에 들어가지 않는다.
- `source_id` 발급 주체: **Source Registry Builder Agent**.
- 발급 후에는 `source_registry.json`이 SSOT.

## 2. rights_status 값

| 값 | 의미 | 사용 가능 여부 |
|---|---|---|
| `rights_clear` | 라이선스/CC/공공 도메인 등 명확 | ✅ |
| `rights_unknown` | 권리 정보 미상 | ⚠️ Review Gate 통과 시 |
| `review_required` | 사람 검토 필요 | ❌ 검토 전 사용 금지 |
| `manual_user_provided` | 사용자가 직접 업로드, 권리 책임 사용자 | ✅ |
| `download_failed` | 자동 다운로드 실패 | ❌ 사용 불가 |
| `login_required` | 로그인 필요 (계정 영역) | ❌ |
| `private_or_deleted` | 비공개/삭제됨 | ❌ |
| `do_not_use` | 사용 금지 | ❌ |

## 3. X / Telegram 영상

직접 영상 삽입을 우선으로 한다. 자동 다운로드 시:

1. `yt-dlp` 또는 공식 API로 시도.
2. 실패 시 `status=needs_user_upload`로 task 종료.
3. 성공 시 `rights_status=rights_unknown` 기본값. Source Registry Builder가 보강.
4. 영상 안에서는 항상 출처(계정명·게시일)를 오른쪽 하단 소형 표기.

## 4. 기사 캡처

- **전체 본문 장문 캡처 금지**.
- 헤더, 제목, 날짜, 핵심 문장(2–3줄) 중심.
- 캡처 도구: Playwright.
- 원본 URL과 캡처 시각을 항상 기록.
- 페이월·로그인 차단 시 `status=needs_user_confirmation`.

## 5. 그래픽 전쟁 영상

- 필요 시 사용. 기본 블러 적용하지 않음.
- 단, 다음 risk_flag 중 하나라도 있으면 Review Gate에서 사용자 명시 승인 필요.
  - `graphic_content`
  - `death_visible`
  - `injury_visible`
  - `explosion_visible`
  - `civilian_harm_possible`
  - `youtube_age_restriction_risk`
  - `monetization_risk`
- 승인 결과는 `approval_log.json`에 risk 항목 단위로 기록.

## 6. 미검증 정보

- 영상 내에 노출은 가능하나 반드시 `<미검증>` 또는 `<추론>` 또는 `<주장>` 라벨로 분리.
- **제목·썸네일에는 미검증 정보 사용 금지** (GOAL G4-7).

## 7. AI 생성 이미지

- 기본 영상 자산으로 **사용 금지**.
- 예외 사용 시 `risk_flag: ai_generated`를 의무 기록.

## 8. 외부 지도 데이터

- Google Maps Tiles: 약관 명시. 상업적 영상 자산 고정 사용은 금지될 수 있음.
- 기본 대안: OpenStreetMap (ODbL 라이선스, 저작자 표시 필요).
- 군사 주제는 지형/위성 지도. 경제/외교는 다크맵 허용.

상세 지도 정책은 [09_MAP_AND_GEO_SPEC.md](09_MAP_AND_GEO_SPEC.md).

## 9. 위반 시 조치

- 위반 발견 → 즉시 자산 격리.
- `RIGHTS-AP-N` 카탈로그에 항목 추가.
- 영향받은 영상 목록을 `approval_log.json`에서 역추적.
- 필요 시 비공개 전환.
