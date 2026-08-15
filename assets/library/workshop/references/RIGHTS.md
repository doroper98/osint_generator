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

참고 — 기수집 인물 원본 (scratchpad 검증분, 라이브러리 승격 시 재기록):
trump 2025 공식 초상 = PD(미 연방) / powell 연준 공식 = PD / putin kremlin.ru = CC BY 4.0
(크레딧 필수) / musk Royal Society = CC BY-SA 3.0 (크레딧 + SA 검토).
