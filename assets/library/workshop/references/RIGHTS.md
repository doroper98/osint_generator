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

## 인물 원본 사진 — 자동 생성 표

<!-- BEGIN photo_manifest 자동 생성 — 직접 수정 금지 -->

**26인** — 정본은 `photo_manifest.json` 이며 본 표는 그 렌더 결과다.
갱신: `python collect_portraits.py --sync-rights`

| 파일 | 인물 | 출처 | 라이선스 | 저작자 | 비고 |
|---|---|---|---|---|---|
| `photo_altman.jpg` | 샘 올트먼 | https://commons.wikimedia.org/wiki/File:Sam_Altman_CropEdit_James_Tamim.jpg | CC BY 2.0 | TechCrunch | 자동 수집 |
| `photo_audrey_tang.jpg` | 오드리 탕 | https://commons.wikimedia.org/wiki/File:Audrey_tang_089_(25378300354)_(cropped).jpg | CC0 | Audrey Tang | 자동 수집 |
| `photo_bezos.jpg` | 제프 베이조스 | https://commons.wikimedia.org/wiki/File:Jeff_Bezos%27_iconic_laugh_crop.jpg | CC BY 2.0 | Jeff_Bezos'_iconic_laugh.jpg: Steve Jurvetson derivative work: King of Hearts | 자동 수집 |
| `photo_chey_tae_won.jpg` | 최태원 | https://commons.wikimedia.org/wiki/File:Korea_Portuguese_Business_Forum_01_(cropped).jpg | CC BY-SA 2.0 | Republic of Korea | 자동 수집 |
| `photo_curtis_yarvin.jpg` | 커티스 야빈 | https://commons.wikimedia.org/wiki/File:Curtis_Yarvin_(3x4_cropped).jpg | CC0 | Davidmerfield | 자동 수집 |
| `photo_dario_amodei.jpg` | 다리오 아모데이 | https://commons.wikimedia.org/wiki/File:Dario_Amodei_in_2023.jpg | CC BY 2.0 | UK Prime Minister | 자동 수집 |
| `photo_daron_acemoglu.jpg` | 대런 애쓰모글루 | 사용자 제공 (출처 미확인 — 웹 수집) | 출처 미확인 · 공인의 보도·논평 목적 인용 | 미상 | 사용자 제공 — 사용자 판단으로 진행 (2026-08-15). 출처가 확인되는 자유 라이선스 사진으로 교체 권장. |
| `photo_helene_landemore.jpg` | Hélène Landemore | 사용자 제공 (출처 미확인 — 웹 수집) | 출처 미확인 · 공인의 보도·논평 목적 인용 | 미상 | 사용자 제공 — 사용자 판단으로 진행 (2026-08-15). 458x449 저해상도. 출처 확인되는 고해상도 사진으로 교체 권장. |
| `photo_jensen_huang.jpg` | 젠슨 황 | https://commons.wikimedia.org/wiki/File:Jensen_Huang_(cropped)_(2024).jpg | CC BY 4.0 | Photographer: Peter Dasilva | 자동 수집 |
| `photo_khamenei.jpg` | 알리 하메네이 | https://commons.wikimedia.org/wiki/File:Ali_Khamenei_Nowruz_message_official_portrait_1397_02_(cropped).jpg | CC BY 4.0 | khamenei.ir | 자동 수집 |
| `photo_lagarde.jpg` | 크리스틴 라가르드 | https://commons.wikimedia.org/wiki/File:Lagarde,_Christine_(official_portrait_2011).jpg | Public domain | Français : Fonds monétaire international (identité du photographe non mentionnée) | 자동 수집 |
| `photo_lee_jae_yong.jpg` | 이재용 | https://commons.wikimedia.org/wiki/File:Lee_Jae-yong_in_2016.jpg | CC BY 3.0 | KBS | 자동 수집 |
| `photo_macron.jpg` | 에마뉘엘 마크롱 | https://commons.wikimedia.org/wiki/File:Emmanuel_Macron_par_Claude_Truong-Ngoc_avril_2015.jpg | CC BY-SA 3.0 | Photo Claude TRUONG-NGOC | 자동 수집 |
| `photo_michael_sandel.jpg` | 마이클 샌델 | 사용자 제공 (출처 미확인 — 웹 수집) | 출처 미확인 · 공인의 보도·논평 목적 인용 | 미상 | 사용자 제공 — 사용자 판단으로 진행 (2026-08-15). 453x485 저해상도. 출처 확인되는 고해상도 사진으로 교체 권장. |
| `photo_musk.jpg` | 일론 머스크 | https://commons.wikimedia.org/wiki/File:Elon_Musk_Royal_Society_(crop2).jpg | CC BY-SA 3.0 | Debbie Rowe | 자동 수집 |
| `photo_netanyahu.jpg` | 베냐민 네타냐후 | https://commons.wikimedia.org/wiki/File:Benjamin_Netanyahu,_February_2023.jpg | CC BY-SA 3.0 | Avi Ohayon | 자동 수집 |
| `photo_peter_thiel.jpg` | 피터 틸 | https://commons.wikimedia.org/wiki/File:Peter_Thiel_by_Gage_Skidmore.jpg | CC BY-SA 3.0 | Gage Skidmore | 자동 수집 |
| `photo_powell.jpg` | 제롬 파월 | https://commons.wikimedia.org/wiki/File:Jerome_H._Powell,_Federal_Reserve_Chair_(cropped).jpg | Public domain | Federalreserve | 자동 수집 |
| `photo_putin.jpg` | 블라디미르 푸틴 | https://commons.wikimedia.org/wiki/File:Vladimir_Putin_portrait_(2024-02-23).png | CC BY 4.0 | This file comes from the website of the President of the Russian Federation and is licensed under the Creative Commons Attribution 4.0 License. In short: you are free to distribute and modify the file as long as you attribute www.kremlin.ru. Note: Works published on site before April 8, 2015 are also licensed under Creative Commons Attribution 3.0 License. The permission letter from the Press Secretary for the President of the Russian Federation is available here. | 자동 수집 |
| `photo_rhee_chang_yong.jpg` | 이창용 | https://commons.wikimedia.org/wiki/File:%EC%9D%B4%EC%B0%BD%EC%9A%A9%EA%B5%90%EC%88%98.jpg | CC BY-SA 4.0 | Sock7458 | 자동 수집 |
| `photo_tim_cook.jpg` | 팀 쿡 | https://commons.wikimedia.org/wiki/File:Visit_of_Tim_Cook_to_the_European_Commission_-_P061904-946789.jpg | CC BY 4.0 | European Commission - Photographer: Christophe Licoppe | 자동 수집 |
| `photo_trump.jpg` | 도널드 트럼프 | https://commons.wikimedia.org/wiki/File:Donald_Trump_official_portrait.jpg | Public domain | Shealeah Craighead | 자동 수집 |
| `photo_warsh.jpg` | 케빈 워시 | https://commons.wikimedia.org/wiki/File:Official_portrait_of_Kevin_M._Warsh_(cropped).jpg | Public domain | Federalreserve | 자동 수집 |
| `photo_xi_jinping.jpg` | 시진핑 | https://commons.wikimedia.org/wiki/File:Xi_Jinping_in_July_2024.jpg | CC BY 4.0 | Press Service of the President of the Republic of Azerbaijan | 자동 수집 |
| `photo_zelensky.jpg` | 볼로디미르 젤렌스키 | https://commons.wikimedia.org/wiki/File:Volodymyr_Zelensky_Official_portrait.jpg | CC BY 4.0 | http://www.president.gov.ua/ | 자동 수집 |
| `photo_zuckerberg.jpg` | 마크 저커버그 | https://commons.wikimedia.org/wiki/File:Mark_Zuckerberg_F8_2018_Keynote_(cropped).jpg | CC BY 2.0 | Anthony Quintano from Honolulu, HI, United States | 자동 수집 |

<!-- END photo_manifest 자동 생성 -->
