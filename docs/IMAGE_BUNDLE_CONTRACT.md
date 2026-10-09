<!--
tier: 2
last_synced_with: v5.7.0
ssot_for: [image-bundle-contract]
depends_on: [VIDEO_BUNDLE_CONTRACT.md, 05_DATA_SCHEMA_SPEC.md]
last_review: 2026-09-29
-->

# IMAGE_BUNDLE_CONTRACT — agents_reviewer ↔ osint_generator 사진 필드 계약

> 상태: **확정** (2026-07-08). osint_generator 소비 구현 v0.42.0~2,
> agents_reviewer emit 구현 v8.3.5 (§3.1-a 개정 포함). 계약 정본은 agents_reviewer
> repo `docs/CONTRACTS/IMAGE_BUNDLE_CONTRACT.md` 이며 본 문서는 소비자측 사본
> (정합 유지 의무).

## 목적

- 영상 중간중간 **보도 사진·현장 이미지**를 삽입해 이해도를 높인다 (다큐 문법).
- 사진의 선별·문단 매칭·권리 판단은 **보고서를 작성하는 agents_reviewer LLM**이
  가장 잘 알므로, 사진은 번들에 실려 오는 것이 원칙이다 (영상 쪽 자동 스크래핑 금지).
- 영상 파이프라인은 LLM 무호출 결정론 유지. **권리 미기록 사진은 최종 영상에
  삽입하지 않는다** (osint_generator G4-8 / C9).

## 스키마 (전부 additive — schema_version 1 유지)

### top-level `images[]` (신설)

```json
"images": [
  {
    "image_id": "img-1",
    "url": "https://.../photo.jpg",
    "caption": "울산 AI 데이터센터 예정 부지",
    "credit": "SKT 제공",
    "rights_status": "cleared",
    "license": "보도자료",
    "source_id": "src-1",
    "focus": "center"
  }
]
```

| 키 | 타입 | 필수 | 규칙 |
|---|---|---|---|
| image_id | string | ✅ | 번들 내 유일. `img-N` 권장 |
| url | string | ✅ | 원본 이미지 직링크 (jpg/png/webp). 페이지 URL 금지 |
| caption | string | ✅ | ≤ 60자. 화면 하단 캡션 겸 대체텍스트 |
| credit | string | ✅ | 출처 표기 (예: "연합뉴스", "SKT 제공"). 영상 우하단 크레딧 |
| rights_status | enum | ✅ | `cleared` \| `needs_review` \| `blocked`. **cleared 만 영상 삽입** |
| license | string | | 근거 (보도자료 / 공식 배포 / CC BY 4.0 / 정부 공공누리 등) |
| source_id | string | | `sources[]` 역추적 연결 (권장) |
| focus | enum | | Ken Burns 시작 초점: `center`(기본) \| `top` \| `bottom` \| `left` \| `right` |

### `sections[].image_refs` (기존 필드 활용 — 신설 아님)

- 그 섹션 구간에 보여줄 `image_id` 목록. 섹션당 0~2개 권장.
- 영상은 섹션당 **첫 번째 cleared 이미지 1장**만 쓴다 (남용 방지).
- `image_refs` 의 모든 id 는 `images[].image_id` 로 resolve 되어야 한다
  (미해결 참조는 수신 검증에서 거부 — fail-closed).

## 작성 규칙 (producer 의무)

1. **rights_status 판단 기준 — §3.1-a 개정 (2026-07-08, v8.3.5)**: 본 시스템은
   *봇 본인 사용 목적*(자체 브리핑 영상)이므로 저작권을 **출처표기(credit)로
   갈음**하는 기존 운영 방침을 따른다. cleared 의 근거:
   - 정부 공식 배포·보도자료 와이어 도메인 → `cleared` (license="공식 배포")
   - credit(출처표기)이 채워진 사진 → `cleared` (license="출처표기")
   - credit 도 근거 도메인도 없는 사진 → `needs_review`
   즉 cleared 의 의미는 "검증된 재사용 라이선스"가 아니라 **"출처표기로 갈음한
   자체 사용"**이다. 무단 전재 위험·초상권 우려는 `blocked`.
   **[§3.1-a 따름 조건]** 이 갈음이 성립하려면 (a) 영상 화면에 credit 이 반드시
   노출되어야 하고 (b) 용도가 자체 브리핑 영상에 한정된다 — 제3자 재배포·상업
   판매 용도로 전환 시 본 전제가 깨지므로 계약 재검토가 선행되어야 한다.
2. **AI 생성 이미지 금지** (osint_generator G4-10). 실사 보도 사진·공식 배포
   이미지·문서 스캔만.
3. **url 은 원본 직링크**: HTML 페이지가 아니라 이미지 파일. 서명 만료 URL
   (S3 presigned 등) 지양 — 빌드 시점 다운로드가 실패한다.
4. **caption 은 사실 서술**: 과장·추정 금지. 미검증 장면이면 caption 에
   `<미검증>` 표기 (G4-7).
5. 인물 사진은 공인의 공적 활동 장면만. 초상권 우려 장면은 `blocked`.
6. 한 보고서당 이미지 총 2~6장 권장 (핵심 섹션 위주).

## 영상 쪽 소비 규칙 (osint_generator v3.5.0 번들 어댑터 — v4.0.0 동기화)

- 번들 이미지는 **연출 재료**다. `bundle/to_direction.py`가 `images[]`를 `intake/bundle_materials.json`의 미디어 재료(`MediaMat`)로 옮긴다. 다운로드·화면 삽입은 하지 않는다.
- **rights gate**: `rights_status == "cleared"`만 `usable: true`다(G4-8·C9). 그 밖은 재료 목록에만 남고 쓰이지 않는다.
- 영상에 넣으려면 미디어 레지스트리(`assets/media/media_registry.json`)에 권리·검증·출처 줄과 함께 등록돼야 한다. 등록 안 된 미디어는 렌더 전 오류다(`engine/media_registry.py`).
- **credit 화면 노출 필수**(§3.1-a 전제): 사진 캡션 바의 출처 줄은 빠지면 오류다(`rules/video_rules.yaml media_beats.caption_credit_required`). 연출상 생략 불가.
- 사실 장면의 AI 생성 금지·사상자 식별 장면 금지는 `media_beats`의 금지 항목이 코드로 검사한다.
- (v0.42 이력) 옛 소비 경로(`bundle_to_video.py` → 로컬 photos 폴더, photo 씬 승격)는 v2.0.0 에서 삭제됐다. 보존본 `archive/hyperframes-briefing`.

## 이력

- 2026-07-08: 초안 작성 (osint_generator v0.42.0 소비 구현 선행).
- 2026-07-08: **확정** — agents_reviewer v8.3.5 emit 구현 + §3.1-a 개정(출처표기
  갈음). osint v0.42.2 에서 사본 동기화 + credit gate 추가.
