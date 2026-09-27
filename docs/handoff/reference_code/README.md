# reference_code — 채팅 세션 원본 소스

세 버전의 동작 코드 원본이다. **경로는 채팅 샌드박스 기준**(`/home/claude/...`, `/home/claude/og` = osint_generator collage 체크아웃)이므로 이식 시 저장소 기준으로 바꾼다.

## v3_hormuz_korea (정본 — 사용자 합격)
| 파일 | 역할 | 실행 순서 |
|---|---|---|
| `plan3.py` | 원고(SCRIPT)·금지문구/발음 린트·edge-tts/ElevenLabs 합성·트림·타임라인 → `plan.json` | 1 |
| `prep3.py` | 폰트 설치, Natural Earth 지오메트리(재귀 평탄화), 지형 티어 W/G/K(커버리지 검사), 인물(라이브러리+위키미디어+rembg+흑백), 휘장, 국기 | 2 (`python prep3.py fonts geo base people flags`) |
| `render3.py` | 연출층(카메라·이벤트, 문장 앵커) + 렌더 엔진(프레임 루프, 레이어, 라벨 LOD, 뱃지, 패널, 카드, 날짜, 자막, 암전) | 3 (`--preview t1,t2` / `START END out.mp4`) |
| `mix3.py` | 내레이션 배치·더킹·BGM 강도 자동화·효과음 → `mix.f32` | 4 |
| `media3b_round2.md` | 2차 미디어(유조선 나포 영상, 이라크 파병 사진) 수집·가공 절차 기록 | 2.5 |
| `media3.py` | 사진·영상·컷아웃 수집(위키미디어 PD)과 가공(16:10 크롭·톤, rembg isnet, 영상 구간→npy) → `media_registry.json` | 2.5 |
| `plan.json` | 실제 타임라인 산출물(45문장, 292.44초) | — |
| `rights_registry.json` | 인물·휘장 권리 기록 | — |
먹싱: `11_RENDER_QA_PERFORMANCE.md` §2, `10_AUDIO.md` §5.

필요 데이터(prep3가 기대하는 위치, 샌드박스 기준):
- `/home/claude/data/ne_10m_admin_0_countries.geojson`, `ne_10m_admin_1_states_provinces.geojson` (Natural Earth)
- `/home/claude/v3/data/ne_10m_populated_places.geojson`
- `/home/claude/v3/data/t5|tg|tk/{x}_{y}.png` (terrarium z5/z7 타일)
- `/home/claude/v3/data/commons_v3.json` (위키미디어 후보 검색 결과 — 04/07 문서의 검색 코드로 생성)
- `/home/claude/v3/assets/flags_svg/*.svg` (flag-icons)
- `/home/claude/og/...` (저장소: 인물 라이브러리, photo_manifest, BGM)

## v2_bundle_ratcliffe (번들 어댑터 버전)
`plan.py`(번들→문장, 저장소 bundle_to_video 함수 import, 언급 탐지, ElevenLabs 경로), `prep.py`(세계 W 티어 + 동유럽 E 티어, 인물 수집), `render2.py`(관계도·도트·간트·선그래프·찬반·분기·체크리스트 패널, 호+비행기, 채널, 방패, DeepState 점령지), `mix2.py`, 권리 JSON.

## v1_ukraine_war (최초 버전)
`common.py`/`base.py`(흑해 벡터 베이스맵 200/100/50ppd), `geo.py`, `script_data.py`(원고), `tts.py`, `timeline.py`, `events.py`(연출 — 침공 화살표, 병력 점, 타임랩스 등), `render.py`(엔진 원형, 날짜 배지+타임라인 스크러버+장 카드 — v3에서 HUD는 날짜만 남김), `ds_proc.py`(DeepState 스냅숏 분류·면적 검증), `music.py`(D단조 절차 합성 음악).
