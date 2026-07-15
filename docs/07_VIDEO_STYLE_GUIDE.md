<!--
tier: 2
last_synced_with: v0.45.0
ssot_for: [video-style-guide]
depends_on: [09_MAP_AND_GEO_SPEC.md, 10_RENDERING_PIPELINE_SPEC.md]
last_review: 2026-05-19
-->

# 07 — Video Style Guide

## 1. 내레이션

- 인사말 없음. 바로 본론.
- 존댓말, 공경체 아님, **브리핑체**.
- 낮고 진중한 톤.
- 짧은 문장 (한 문장 한 메시지).
- 확인 / 추론 / 미검증을 라벨로 분리.

## 2. 화면

- 지도 중심.
- 실제 영상 (X/TG) 삽입.
- 기사 실제 캡처 (헤더·제목·날짜·핵심 문장).
- Source Card (X/TG/기사) 사용.
- 빨간 형광펜, 펜 동그라미, 화살표 강조.
- 작은 한글 자막.
- 출처는 오른쪽 하단 소형 표기.
- 정지 이미지는 slow zoom/pan 적용.
- **AI 생성 이미지는 사용하지 않는다**.

## 3. 자막

- 어두운 배경 + 세련된 한글 폰트.
- 크기는 일반 유튜브 자막보다 작게.
- 너무 많은 텍스트 금지. 핵심 문장 중심.

권장 폰트 후보:
- Pretendard
- Noto Sans KR
- SUIT
- Spoqa Han Sans Neo
- IBM Plex Sans KR

### 3.1 채택 서체 — 르포(reportage) (v0.45.0, 구현 확정)

agents_reviewer 르포 테마와 동일 서체를 채택한다. 전부 로컬 번들(결정론/오프라인).

- **디스플레이** (헤드라인·타이틀·키커·칩·스테이트먼트·인용·네트워크 라벨):
  **GmarketSans** (Bold 700 / Medium 500). `.serif` 클래스가 GmarketSans 로 매핑됨.
- **본문·자막·데크·muted**: **Noto Sans KR** (400/500/700).
- 로드: `assets/reportage_fonts.css`. 폰트 파일: `assets/fonts/gmarketsans/`,
  `assets/fonts/notosanskr/`. 라이선스는 상업적 이용 가능 폰트만(C9).

## 4. 색상 시스템

### 4.0 르포 팔레트 8종 (v0.45.0)

`themes.js:SK_THEMES` 의 `reportage_*` 8종 — 전부 **다크 배경 + 크림 텍스트 +
채도 높은 액센트** (밝고 화려한 르포 톤). 번들 `report.theme.id` 로 자동 선택되며
기본 폴백은 `reportage_cyprus`.

| id | 배경 | 액센트 | 성격 |
|---|---|---|---|
| reportage_cyprus | teal #004741 | ochre #E3A93C | 밝은 다큐 기본 |
| reportage_noturno | near-black teal #001621 | vulcanico #FF4103 | 강렬·심야 |
| reportage_bridal | maroon #741A2F | peach #FFB38F | 따뜻함 |
| reportage_cosmos | deep blue #002F49 | crimson #E8503F | 정책·긴장 |
| reportage_laurel | forest #0D3A35 | mint #86C0A4 | 환경·장기 |
| reportage_princess | bright blue #015AA0 | coral #FF9457 | 금융·자본 |
| reportage_steel | plum-grey #282433 | amber #E2B25C | 협상·중립 |
| reportage_navy | indigo #0F0E49 | orchid #D9ABE8 | 권력·정치 |

의미색: `--accent`(브랜드/강조), `--sage`(상승·동맹), `--oxide`(하락·대립).



| 카테고리 | 주 색상 |
|---|---|
| 전쟁/군사 | 붉은색 |
| 지정학 (대치 구도) | 붉은색 + 청색 |
| 지정학 (3자 이상) | 빨강 + 파랑 + 녹색 + 노랑 |
| 경제/산업 | 노랑 / 주황 |
| 지진/재난 | 주황 / 적갈색 |
| 정보전/음모론 | 암청색 / 보라빛 적색 |

지도 국가 하이라이트 색상은 카테고리 주 색상을 따른다.

## 5. 모션

- 컷 전환: 0.2초 cross fade 기본.
- 정지 이미지: slow zoom 5–10초.
- 지도: zoom in/out, polyline 그리기 1–2초.

## 6. 라벨링 시스템

| 라벨 | 시각 |
|---|---|
| `<확인>` | 검정 배경 + 흰 글씨, 작게 |
| `<추론>` | 노랑 배경 + 검정 글씨, 작게 |
| `<미검증>` | 빨강 배경 + 흰 글씨, 작게 |
| `<반박됨>` | 회색 배경 + 빨강 글씨, 작게 |

자세한 라벨 정책은 [12_QA_AND_REVIEW_SPEC.md](12_QA_AND_REVIEW_SPEC.md).
