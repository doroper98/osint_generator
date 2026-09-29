<!--
tier: 2
last_synced_with: v4.2.0
ssot_for: [rights-policy, source-policy]
depends_on: [05_DATA_SCHEMA_SPEC.md]
last_review: 2026-09-29
-->

# 06 — Source & Rights Policy

## 1. 모든 소스와 자산은 기록을 가진다 (v4.0.0)

- **사실 소스**(기사·X 게시물·문서)는 `intake/sources.json` 레코드와 id를 가진다. 원고 문장의 출처는 `intake/claims.json`의 claim id다(handoff 18, [05](05_DATA_SCHEMA_SPEC.md) §8).
  출처 없는 수치 문장은 린트 오류다.
- **화면 자산**(인물·휘장·국기·지도·지형·미디어·음악·글꼴·음성)은 프로젝트 `assets/rights_registry.json`과 저장소 레지스트리(`assets/media/media_registry.json`, `assets/audio/bgm/registry.yaml`)에 있어야 렌더된다.
  크레딧 표기 위치는 `rules/video_rules.yaml credits`(엔딩 카드 ∪ 설명문 = 전 자산).

## 2. rights_status 값

v2 레지스트리의 값은 `rights_clear`·`restricted`·`unverified` 세 가지다(`schemas/engine_models.py`, `schemas/media_models.py`).
`rights_clear`만 영상에 쓴다. 제한 휘장(위키미디어 `Restrictions`)은 쓰지 않고 국기로 대체한다(D5).
번들 이미지(`BundleImage`)는 계약 값 `cleared`·`needs_review`·`blocked` 중 `cleared`만 재료가 된다(IMAGE_BUNDLE_CONTRACT).
아래 v1 값 표는 v1 파이프라인의 소스 상태 이력이다.

| 값(v1) | 의미 | 사용 가능 여부 |
|---|---|---|
| `rights_clear` | 라이선스/CC/공공 도메인 등 명확 | ✅ |
| `rights_unknown` | 권리 정보 미상 | ❌(v2: `unverified` — 렌더 전 오류) |
| `review_required` | 사람 검토 필요 | ❌ 검토 전 사용 금지 |
| `manual_user_provided` | 사용자가 직접 업로드, 권리 책임 사용자 | ✅(레지스트리에 기록 후) |
| `download_failed` · `login_required` · `private_or_deleted` · `do_not_use` | 확보 실패·접근 불가·사용 금지 | ❌ |

## 3. X 게시물

- **스크래핑하지 않는다.** 사용자가 게시물 텍스트·화면 캡처를 전달한다(`add-source`, x.com 을 열지 않음).
- 캡처는 캡처 판독 워커가 초안을 만들고, 사용자가 계정·시각을 확인해야 검증 단계로 간다(handoff 18 §1·§7).
- 영상에는 캡처 이미지가 아니라 자체 조판한 게시물 카드로 나온다(로고 없음, handoff 18 §5). 공식 계정 판정은 `rules/official_accounts.yaml`.

## 4. 기사

- **원문 장문을 저장·표시하지 않는다.** 레코드에는 요지(`key_facts`)만, 본문은 비공개 보관(`intake/bodies/`).
- 인용은 짧게(`rules/video_rules.yaml verification.quote_max_chars`), 소스 본문의 연속 부분 문자열이어야 한다(D50).
- 원본 URL·매체·게시일·가져온 시각을 기록한다. 페이월·차단은 미해결로 남기고 추측으로 채우지 않는다.

## 5. 전쟁·재난 영상

- **사상자를 식별할 수 있는 장면은 쓰지 않는다**(GOAL G4-10 v2.0.0, `rules/video_rules.yaml media_beats.casualty_identifiable_forbidden`).
  미디어 레지스트리가 구간별로 검사하고 위반은 렌더 전 오류다(`tests/test_media_registry_phase65.py`).
- 자료사진·자료 영상 표기와 출처 줄은 필수다(`media_beats.file_photo_label_required`, `caption_credit_required`).
- (v1 이력) risk_flag 사용자 명시 승인 절차(`graphic_content`·`death_visible` 등)는 v2.0.0 에서 위 금지 규칙으로 대체됐다.

## 6. 미검증 정보

- 영상 안에서는 라벨로 분리한다. 문구는 `rules/video_rules.yaml script_schema.labels`(`<미검증>`·`<논쟁>`), 라벨은 claims status로 코드가 계산한다.
- 논쟁 사안은 양측을 같은 무게로 다룬다. 미검증 주장은 누가 말했는지 귀속한다(`attribution_markers`).
- **제목·썸네일에는 미검증 정보 사용 금지** (GOAL G4-7).

## 7. AI 이미지

GOAL G4-10(v1.0.0 개정·v2.0.0 추가)이 정본이다. 실존 인물·장소·사물은 **실자료 입력 가공만** 허용하고, 입력 없이 사실을 그리지 않는다.
생성 이미지로 사실 자료를 대체하지 않는다(`media_beats.ai_generated_forbidden`). 도구·원본·프롬프트를 기록하고, 사실 텍스트는 코드로 렌더한다.

## 8. 외부 지도 데이터

- 국경·라벨: Natural Earth(공공 도메인). 지형: terrarium 고도 타일(AWS Open Data `elevation-tiles-prod`). 표기는 프로젝트 `credits.yaml`·권리 레지스트리 `map` 절.
- Google Maps: 약관 검토 없이 상업 영상 자산으로 고정 사용하지 않는다(G4-11). 지금 쓰지 않는다.

상세 지도 명세는 [09_MAP_AND_GEO_SPEC.md](09_MAP_AND_GEO_SPEC.md).

## 8.5 TTS 음성 권리

- TTS 나레이션은 **본인 목소리 또는 합성/라이선스 보이스만** 사용한다. 타인의 목소리를
  무단 복제하는 것은 법적 문제가 될 수 있다.
- 백엔드는 `config.yaml tts`가 정한다(edge-tts·ElevenLabs, [08](08_AUDIO_AND_TTS_SPEC.md) §3). 외부 API로 원고가 나간다는 점을 전제로 한다.
  API 키·voice id는 `.env`로만 두고 커밋하지 않는다(C9). 음성 권리는 권리 레지스트리 `narration` 절에 기록한다.

## 9. 위반 시 조치

- 위반 발견 → 즉시 자산 격리.
- `RIGHTS-AP-N` 카탈로그에 항목 추가.
- 영향받은 영상 목록을 각 영상의 `provenance.json`·권리 레지스트리에서 역추적.
- 필요 시 비공개 전환.
