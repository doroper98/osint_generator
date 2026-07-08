<!--
tier: 2
last_synced_with: v0.42.0
ssot_for: [image-bundle-contract]
depends_on: [VIDEO_BUNDLE_CONTRACT.md, 05_DATA_SCHEMA_SPEC.md]
last_review: 2026-07-08
-->

# IMAGE_BUNDLE_CONTRACT — agents_reviewer ↔ osint_generator 사진 필드 계약

> 상태: **제안** (2026-07-08 초안). osint_generator 소비 구현 v0.42.0 완료(선행),
> agents_reviewer emit 구현 대기. 확정 시 본 헤더를 갱신한다.

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

1. **rights_status 는 판단 근거와 함께**: 보도자료·회사 공식 배포·정부 공공누리·
   CC 라이선스 등 재사용 근거가 확인된 것만 `cleared`. 불확실하면 `needs_review`
   (영상은 스킵하고 로그만 남긴다). 무단 전재 위험이 있으면 `blocked`.
2. **AI 생성 이미지 금지** (osint_generator G4-10). 실사 보도 사진·공식 배포
   이미지·문서 스캔만.
3. **url 은 원본 직링크**: HTML 페이지가 아니라 이미지 파일. 서명 만료 URL
   (S3 presigned 등) 지양 — 빌드 시점 다운로드가 실패한다.
4. **caption 은 사실 서술**: 과장·추정 금지. 미검증 장면이면 caption 에
   `<미검증>` 표기 (G4-7).
5. 인물 사진은 공인의 공적 활동 장면만. 초상권 우려 장면은 `blocked`.
6. 한 보고서당 이미지 총 2~6장 권장 (핵심 섹션 위주).

## 영상 쪽 소비 규칙 (osint_generator v0.42.0 구현)

- 빌드 시(`bundle_to_video.py`) `images[]` 를 다운로드해 로컬 자산화
  (`hyperframes/briefing/assets/photos/{report_id}/`). 다운로드 실패·타입 불일치
  는 해당 이미지 스킵 + 로그 (파이프라인은 계속).
- **rights gate**: `rights_status == "cleared"` 가 아니면 다운로드 자체를 하지
  않는다. 소비 결과는 `photos_manifest.json` 에 기록 (C9 권리 추적).
- `sections[].image_refs` 가 resolve 되는 섹션의 스테이트먼트 씬을 **photo 씬**
  으로 승격: 풀블리드 사진 + Ken Burns + 스크림 + key takeaway 오버레이 +
  우하단 `사진 · {credit}` 크레딧.
- `images` 부재 시: 기존 동작 그대로 (하위 호환).

## 이력

- 2026-07-08: 초안 작성 (osint_generator v0.42.0 소비 구현 선행).
