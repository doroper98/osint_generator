# references/ 권리 기록 (C9 / G4-10)

공방 입력 자료의 출처·라이선스. **여기 기록 없는 사진으로 가공 금지.**

## 명명 규약

`references/` 는 라이브러리 배포 자산이 아니라 **참조 자료**라 17 §0.8 (자산 파일명) 이 아니라
아래 규약을 따른다. lowercase snake, `{kind}_{slug}[_v{N}].{ext}`:

| `kind` | 뜻 | 용도 |
|---|---|---|
| `style_anchor` | **가공 스타일 앵커** | codex 프롬프트에 첨부되는 실제 기준본. 사용자 검수 통과본만 |
| `sheet_sample` | 디자인 시트 샘플 | "바람직한 시트"의 구조 참조 — 가공에 첨부하지 않는다 |
| `collage_sample` | 콜라주 미학 샘플 | 표현·모션 어휘 참조 — 가공에 첨부하지 않는다 |

**`style_anchor` 만 프롬프트에 첨부한다.** 나머지는 설계 참조용이며, 가공 입력으로 넣으면
스타일이 섞여 앵커가 무의미해진다.

## 자산

| 파일 | 대상 | 출처 | 라이선스 | 크레딧 의무 |
|---|---|---|---|---|
| `style_anchor_portrait_v1.png` | **스타일 앵커** — 4인물 시트 (황젠슨 `outline`+`dots` / 워시 `outline`+`solid` / 시진핑 `offset`+`hatch` / 최태원 `offset`+`solid`) | 사용자 ChatGPT 가공물 (2026-08-15 배치) | 내부 스타일 참조 전용 (배포 자산 아님) | — |
| `sheet_sample_editorial_vs_swiss.jpg` | 시트 샘플 — Editorial vs Swiss 비교. **Shared Rules 축**(Layout/Palette/Type/Whitespace)으로 두 컨셉을 나란히 정의 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `sheet_sample_meridian_linen.jpg` | 시트 샘플 — MERIDIAN·LINEN 스페시먼. **플레이트 ID**(`PL 01/24`, `P 01`, `S 05`) + 토큰 카운트 + 팔레트 hex 병기 + 타입 스택 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `sheet_sample_editorial_brand_board.jpg` | 시트 샘플 — 브랜드 보드. **재질 견본**(recycled paper / linen / unglazed ceramic)을 색과 동급으로 취급 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `collage_sample_grid_paper_cutout.jpg` | 콜라주 샘플 — 모눈종이 배경 + 컷아웃 + 손글씨 + **컬러 오프셋 실루엣**(스케이터) | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `collage_sample_paper_stopmotion_desk.jpg` | 콜라주 샘플 — 종이 컷아웃 스톱모션. **손이 컷아웃을 놓는 장면** = 17 §1.4 놓기(place) 모션의 원형 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `collage_sample_ransom_wake_up.jpg` | 콜라주 샘플 — 랜섬노트 최대 강도. 모노 하프톤 인물 + **단일 액센트**(녹색) + 찢은 활자 + 메시 그레인 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |
| `collage_sample_string_connector.jpg` | 콜라주 샘플 — **흰 연결선 + 노드 원형** = 17 §2 #8 `StringConnector` 의 시각 원형. 신문지 질감 인물, 도트/하프톤 원 | 사용자 수집 (2026-08-15) | 내부 설계 참조 전용 | 외부 배포 금지 |

> `sheet_sample_*` / `collage_sample_*` 은 출처가 특정되지 않은 사용자 수집 이미지다.
> **내부 설계 참조로만 쓰고, 영상·문서·외부 산출물에 싣지 않는다.** 이들에서 배운 것은
> 어휘·구조로 추상화해 17 문서에 기록하며, 픽셀을 재사용하지 않는다.

## 인물 원본 사진 (`photo_{person_id}.jpg`)

**기계 기록은 `photo_manifest.json` 이 정본**이다 (출처 URL·저작자·라이선스·Commons 파일명).
수집기는 `collect_portraits.py`, 육안 검수 시트는 `make_contact_sheet.py` 로 재생성한다.

- 허용 라이선스: PD / CC0 / CC BY (1.0~4.0) / CC BY-SA (1.0~4.0) / **KOGL Type 1**
  (공공누리 제1유형 — 출처표시 조건의 상업적 이용·변형 허용, CC BY 동등).
- **`restrictions` 태그가 있으면 자동 차단**한다 (`personality` 초상권 / `communist` /
  `trademarked` / `insignia`). 저작권과 별개의 법익이라 사람 판단으로만 통과시킨다.
- CC BY / CC BY-SA 자산은 **영상 CLOSING 크레딧에 저작자 표기 의무**. SA 항목은 파생물
  라이선스 검토 필요 (musk, macron, netanyahu, chey_tae_won, rhee_chang_yong, kim_jong_un).

### 수집 상태 (2026-08-15)

| | 수 | 비고 |
|---|---|---|
| 수집 완료 | **19인** | 전원 육안 검수 통과 (인물 동일성·구도 확인) |
| 보류 | 1인 (`kim_jong_un`) | 아래 참조 |

**`kim_jong_un` 보류 사유** — Commons 검색 1순위가 **2018 싱가포르 회담 당시의 분장
배우(임퍼서네이터) 사진**이었다 (라이선스는 정상 통과). 실제 인물로 pin 한
`File:Kim Jong-un April 2019 (cropped).jpg` 는 CC BY 4.0·1028×1429 로 조건은 맞으나
`restrictions='personality|communist'` 라 자동 차단됐다. **사용자 판단 필요.**

> **교훈 (검수 절차에 고정)**: 라이선스·해상도 필터는 *"그 사람이 맞는가"* 를 못 잡는다.
> 오히려 해상도 하한을 올리자 개인 초상이 밀려나고 단체·행사 컷이 올라오는 회귀가 났다
> (`rhee_chang_yong` 회의실 전경, `zuckerberg` 풍자 삽화). **컨택트 시트 육안 검수는
> 생략 가능한 단계가 아니다.**

### 사용자 제공 사진 등록 (`--adopt`)

Commons 에 쓸 만한 자유 라이선스 사진이 없거나(`lee_jae_yong`) `restrictions` 로 자동
차단된 인물(`kim_jong_un`)은 사용자가 직접 사진을 주고 등록한다.

```bash
python assets/library/workshop/collect_portraits.py \
  --adopt kim_jong_un \
  --file "C:/경로/사진.jpg" \
  --source "https://... (출처 URL 또는 '직접 촬영')" \
  --license "CC BY 4.0 | PD | 보도 인용 등" \
  --artist "촬영자/기관" \
  --note "초상권 판단 근거 (공인의 보도·논평 목적 사용 등)"
```

`--file` · `--source` · `--license` 셋은 **필수**다. 권리 기록 없는 사진은 등록되지
않는다 (C9). 등록 후 `make_contact_sheet.py` 로 육안 재검수한다.

**좋은 입력 사진의 조건** (가공 품질을 좌우한다):

| 항목 | 기준 | 이유 |
|---|---|---|
| 얼굴 크기 | 최소 변 600px 이상, 1000px+ 권장 | 고대비 모노톤 변환 시 얼굴이 뭉개지지 않게 |
| 각도 | 정면~약간 측면, 상반신 | 17 §1.7 컷아웃 규격 |
| 조명 | 얼굴에 고르게 | 반쪽이 검게 뭉치면 S-커브 대비에서 이목구비가 사라진다 |
| 배경 | 단순할수록 좋음 | 배경 제거(방식 B) 품질이 올라간다 |
| 시기 | 최근 | 현재 모습과 일치해야 인물 식별이 된다 |

### 저해상도 수용분 (pin 으로 명시 채택)

| 인물 | 크기 | 사유 |
|---|---|---|
| `lee_jae_yong` | 342×493 | Commons 에 자유 라이선스 개인 초상이 이것뿐 (나머지는 촛불집회·행사 단체컷) |
| `rhee_chang_yong` | 510×800 | KOGL 대안은 전부 회의실 전경이라 얼굴 식별 불가 |

가공 결과가 뭉개지면 사용자 제공 사진으로 교체한다.
