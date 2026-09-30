<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-typography, v2-hud, v2-subtitles]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 09. 타이포그래피 · HUD · 자막 · 색

참조 코드: `v3/render3.py` (`FONT`, `font`, `text`, `tw`, `wrap`, `rrect`, `draw_date`, `draw_subtitle`, `draw_fullcards`, `build_vignette`, `C`), `v3/prep3.py` (`fonts()`)

---

## 1. 폰트 — agents_reviewer 르포 스택 (지적 7)

agents_reviewer 저장소 전체에서 `font-family` 사용 빈도를 집계한 결과:
| 빈도 | 선언 | 용도(르포) |
|---|---|---|
| 2,976 | `'Newsreader','Noto Serif KR',serif` | 제목(라틴 Newsreader + 한글 Noto Serif KR) |
| 2,309 | `'Noto Serif KR', serif` | 본문 세리프 |
| 1,008 | `'IBM Plex Mono',monospace` | 숫자·코드 |
| 793 | `'IBM Plex Sans KR',sans-serif` | UI·본문 산세리프 |
| 385+214 | `'GmarketSans'` | 디스플레이(굵은 제목·숫자) |
| 247 | `'Noto Sans KR', sans-serif` | 보조 |

영상 적용:
| 역할 | 폰트 | fontconfig 이름(cairo `select_font_face`) |
|---|---|---|
| 자막·라벨·카드 본문 | IBM Plex Sans KR Medium / SemiBold / Regular | `'IBM Plex Sans KR Medium'`, `'IBM Plex Sans KR SemiBold'`, `'IBM Plex Sans KR'` |
| 제목·인용·해역명 | Noto Serif KR (설치본: Noto Serif CJK KR) | `'Noto Serif CJK KR'` (+ BOLD weight) |
| 타이틀·큰 수치·연도 | GmarketSans Bold/Medium | `'GmarketSansBold'`, `'GmarketSansMedium'` |
| 날짜·숫자 | IBM Plex Mono SemiBold/Medium | `'IBM Plex Mono SemiBold'`, `'IBM Plex Mono Medium'` |

### 1.1 설치 (`prep3.py fonts()`)
```python
G = 'https://raw.githubusercontent.com/google/fonts/main/ofl'
IBMPlexSansKR-{Regular,Medium,SemiBold,Bold}.ttf  ← {G}/ibmplexsanskr/
IBMPlexMono-{Medium,SemiBold}.ttf                 ← {G}/ibmplexmono/
GmarketSans{Bold,Medium}.woff  ← https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/
   → fontTools: TTFont(BytesIO(woff)); f.flavor=None; f.save('~/.fonts/GmarketSans{w}.otf')
fc-cache -f ; fc-list : family 로 등록 확인
```
Claude Code는 폰트를 `assets/fonts/`에 두고 라이선스 파일을 함께 커밋한다(IBM Plex·Noto: OFL. GmarketSans: 지마켓 무료 폰트 — 배포 조건 확인 후 커밋 여부 결정).

### 1.2 글리프 함정 (실제 발생)
| 문제 | 증상 | 대책 |
|---|---|---|
| IBM Plex Mono + 한글 혼용 | 한글이 네모로 깨짐("자료사진", "기준") | `mixed_runs()`: 한글 런은 Sans로 자동 폴백, 폭 계산도 동일 규칙 |
| GmarketSans(woff→otf 변환본)의 공백 | 공백이 네모(□)로 렌더 ("호르무즈와□한국", "10억□배럴") | disp 폰트는 글자 단위로 그리고 공백은 `0.3×size` 전진만. `tw()`도 같은 규칙으로 폭 계산 |
| IBM Plex Mono에 한글 없음 | "2월"이 깨져 "20"처럼 보임 | Mono는 **숫자·점·콜론만**. 한글이 섞이면 Sans 사용 |
| cairo toy API 커닝 | 한글은 문제없음 | 라틴 제목이 필요하면 Newsreader 설치 후 사용 |

---

## 2. 크기 체계와 해상도 스케일

480p(854×480) 기준 값. **다른 해상도는 `k = H_OUT / 480`을 곱한다**(1080p: 2.25). 모든 픽셀 상수(글자 크기, 선 두께, 오프셋, 뱃지 R, 카드 폭 등)를 `style.px(n)`으로 감싸는 것이 Claude Code 과제. **[v4.0.0 정정 — D60(back_and_forth D-0067): 리터럴을 감싸지 않는다. `px()` 는 렌더 진입 장치 변환 한 곳(`translate(pad_x)·scale(k)`)이고, 래스터만 장치 해상도로 준비한다. 현재 명세는 `docs/09_MAP_AND_GEO_SPEC.md` §3·`docs/10_RENDERING_PIPELINE_SPEC.md` §4.]**

| 요소 | 크기(480p) | 화면 높이 대비 | 1080p 환산 |
|---|---|---|---|
| 자막 | 19px | 4.0% | 43px |
| 날짜 배지 | 15px Mono | 3.1% | 34px |
| 타이틀 | 46px Gmarket | 9.6% | 104px |
| 패널 제목 | 19px Serif Bold | 4.0% | 43px |
| 카드 큰 수치 | 30px Gmarket | 6.3% | 68px |
| 마커 라벨 | 13px | 2.7% | 29px |
| 국가명 | 12~13px | 2.6% | 28px |
| 도시(수도/일반) | 11.5 / 10.5px | 2.2~2.4% | 24~26px |
| 최소 글자 | 9.5px(도 이름, 출처) | 2.0% | 21px |

**판독성 규칙**: 화면 높이의 2% 미만 글자는 쓰지 않는다. 저장소 롱폼은 1080p 캔버스에 11~17px(1.0~1.6%)을 써서 휴대폰에서 판독 불가였다.

---

## 3. 텍스트 렌더 함수

```python
def text(ctx, s, x, y, size, name='sansm', col=(1,1,1), a=1.0, halo=3.0, anchor='l', spacing=0.0, halo_a=0.8):
    font(ctx, name, size)
    w = tw(ctx, s, size, name) + spacing*(len(s)-1)
    x -= w/2 (anchor 'c') 또는 w ('r')
    path: 자간 있으면 글자별 text_path (disp 폰트 공백은 건너뛰고 0.3*size 전진), 없으면 한 번에
    헤일로: stroke(rgba(0.02,0.03,0.05, halo_a*a), width=halo, LINE_JOIN_ROUND) → fill(col, a)
    return w
```
헤일로(외곽선)는 지도 위 가독성의 핵심이다. 자막 4.4 / 라벨 2.2~3.2 / 패널 안 글자는 0(어두운 바탕).

---

## 4. 자막 (`draw_subtitle`)

```python
활성 문장: t0 − 0.05 ≤ t ≤ t1 + 0.25
알파: min(smooth((t − t0 + 0.05)/0.18), smooth((t1 + 0.25 − t)/0.2))
크기 19, 폭 700px에서 어절 단위 줄바꿈(wrap) → 최대 2줄(원고 문장을 짧게 쓰는 것으로 보장)
기준선: 마지막 줄 y=452, 줄 간격 26 → base_y = 452 − (줄수−1)*26
정렬: 줄마다 중앙
강조: segments를 글자별 플래그로 펼침 → 줄 안에서 같은 플래그 구간(run)별로 그림
      일반 = Medium 흰색 / 강조 = SemiBold 금색(#e8b860), 헤일로 4.4 알파 0.9
```
자막은 영상에 입힌다(번인). SRT는 자동 번역용 별도 제공.

---

## 5. HUD — 날짜만 (지적 3)

**폐기**: "◆ OSINT BRIEFING" 브랜드, "01 / 12" 섹션 번호, 섹션 제목(좌상단), 타임라인 스크러버(v1), 장 번호.

**유지**: 우상단 날짜 배지 하나.
```python
현재 문장 = t0 − 0.3 ≤ t 인 마지막 문장; 전면 카드(타이틀/엔딩) 중에는 숨김
날짜 문자열: 'YYYY.MM.DD' → 'YYYY. MM. DD' (점 뒤 공백), 'YYYY'·'YYYY.MM' 허용
날짜가 바뀐 시각 t_ch부터 0.45초: 6px 위에서 내려오며 페이드 인
text(날짜, W−26, 40, 15, Mono SemiBold, 흰색 0.95, 헤일로 3, 우정렬)
금색 밑줄: y=48, 두께 1.4, 폭 = 글자폭 × 진행률 (오른쪽에서 왼쪽으로 그어짐)
```
날짜는 **문장의 사건 날짜**다(제작일이 아님). 과거 회상 장면은 과거 연도(2004 등), 통계 장면은 통계 기준 연도(2025).

---

## 6. 전면 카드

### 6.1 타이틀 카드 (콜드 오픈 뒤, 5.6초)
```python
배경: 세로 그라데이션 검정 (0: 0.86, 0.5: 0.70, 1: 0.92) × 페이드
제목: GmarketSans Bold 46, (W/2, 232), 1초 ease_out으로 10px 위로 올라오며 페이드(0.1초 지연)
금색 룰: y=254, 두께 1.6, 폭 220 × ease_io((lt−0.5)/0.9)
부제: Noto Serif Bold 18 (0.92,0.9,0.88) @ y=290, 0.8초 지연
날짜: IBM Plex Mono 12 금색 @ y=322, 1.1초 지연
카드 뒤에서 카메라 컷 + 카드 아래 암전(05 §3.1)
```

### 6.2 엔딩 카드 (11초) — 라운드 6 재디자인 (사용자 요청: "고급지고, 글씨를 작게")
```python
배경: rgba(0.018, 0.022, 0.032, 0.94) 단색 덮개(지도가 아주 희미하게 비침)
킥커: 'SOURCES  &  CREDITS'  IBM Plex Mono SemiBold 8.5, 자간 2.4, 금색 @ (64, 84)
제목: '자료 및 출처'  Noto Serif CJK KR Regular 17, 자간 1.0 @ (64, 110)
금색 룰: (64, 122) 폭 36 × 진행률, 두께 1.1
가로 헤어라인: y=140, x 64 ~ W−64, 흰색 0.08
2단: 왼쪽 x=64 (보도·자료, 인물 사진, 사진·영상) / 오른쪽 x=456 (휘장·국기·지도, 음악·음성), 시작 y=158
  섹션명: Sans SemiBold 8.5 금색 0.9, 자간 1.4, 아래 17px
  항목: Sans Regular 9.2 (0.86,0.87,0.9) / 라이선스 줄: Mono Medium 7.8 muted (항목 아래 12px, 없으면 15px 간격)
  섹션 간 12px
하단: 헤어라인 y=H−44 / 좌: '{날짜} 기준' Mono 7.8 / 우: '수치와 인용은 제작 시점의 공개 보도에 근거합니다' Sans 7.8
애니메이션: 킥커·제목 6px 위로 떠오르며 0.9초 / 섹션 0.18초 간격 / 항목 0.03초 간격 / 하단 1.6초 후
```
크레딧 데이터는 `credit_sections()`가 권리·미디어 레지스트리에서 만든다(`07` §7, `14` §6).
**판독성 예외**: 엔딩 카드는 정독용이 아닌 기록용이라 §2의 "최소 2%" 규칙의 예외(7.8~9.2px, 480p)를 사용자 요청으로 허용한다.

## 7. 색 토큰 (v3)

| 토큰 | 값 | 쓰임 |
|---|---|---|
| ru | `#ff5566` | 대립·봉쇄·거절·러시아/이란 측 |
| us | `#5aa9ff` | 미국 측, 호위 |
| gold | `#e8b860` | 강조·한국·핵심 마커·자막 강조 |
| teal | `#5cc8da` | 중립·통과·청해부대 항로 |
| green | `#8fd08a` | 합의·휴전 |
| muted | `#a9b0bd` | 보조 텍스트 |
| amber | `#ffb347` | 폭발·반대 입장·추정 태그 |
| 해역 라벨 | `#9cc8e6` | |
| 패널 덮개 | rgba(0.025,0.03,0.045,0.8) | |
| 카드 바탕 | rgba(0.05,0.06,0.09,0.86) | |
| 패널 카드 바탕 | rgba(0.07,0.08,0.12,0.92) | |

---

## 8. 비네팅 없음 (라운드 6) · 전체 페이드
- **비네팅(방사형 가장자리 어둡힘)과 상·하단 그라데이션을 쓰지 않는다**(사용자 지시 "비네팅 효과 없애").
- 가독성은 헤일로로 확보: 자막 5.0(알파 0.92), 날짜 3.0, 라벨 2.2~3.2.
- 전체 페이드: 시작 1.2초 인, 끝 1.6초 아웃(유지).
- v1~v3 초판의 `build_vignette()`는 레퍼런스 코드에 남아 있으나 호출하지 않는다.

---

## 9. v4.8.0 — 화면 글자 크기 전수 표 (G7, back_and_forth D-0101 §3·D-0113 A, 사용자 결정 D89)

사용자 지시: "전체적으로 요소들이 너무 작다". §2 표의 v3 값(자막 19 등)은 사용자 결정으로 바뀌었다. **수치 정본은 `rules/video_rules.yaml`** — 아래는 무엇이 바뀌었는지의 요약이다(값 복사 금지 원칙에 따라 키 이름으로 읽는다).

- 기준: 480p 설계에서 본문성 글자 ≥ 12, 메타(출처·라이선스·PHOTO·VIDEO·ARTICLE) ≥ 9.
- 1단계(20bc020): 렌더 코드의 글자 리터럴을 규칙 키로 옮김(값 무변경, 골든 25컷 바이트 동일). 2단계(D-0113 A): 값 적용.
- 바뀐 키(표 1): `layout_480p.subtitle.size`(19 → 21), `layout_480p.card`(line·tag·src·cap + line_gap·src_gap), `layout_480p.panel.subtitle_size`, `layout_480p.media_caption`(caption·credit·tag·cutout_credit + caption_dy·credit_dy·tag_h·tag_dy), `media_beats.caption_bar_px`.
- 바뀐 키(표 2): `layout_480p.marker.sub_size`·`sub_dy`, `layout_480p.route_label.route_size`, `placement.post_card`(name·handle·chip·body·orig·foot + body_line), `panels.relation.edge_label`, `panels.timeline`(date·label·month·band_label — **시간축 무대 stage_timeline 은 제외**, D-0092 B), `panels.charts`(dual_line x_label·value, fork body, dots note_caption, network label), `panels.precedent`(line·caption, 상자 172×212 고정이라 더 키우지 않음).
- 바꾸지 않은 것(표 3): 엔딩 카드·타이틀 카드·시간축 무대 글자·모서리 날짜(D-0101 제외), 지도 바탕 글자(`engine/layers/labels.py` LOD — 지도 질감), 이미 메타 기준 이상인 것(prov_tag·gantt·dual_line tick·versus 등), `primitives.site_diagram`(G8 콘티 판에서), `article_card`(G7 작업 2 에서 확정, 08 §12).
- 자막 21 의 결과: 2줄 문장 hormuz 3 → 15/45, fed_policy 1 → 7/48, 랫클리프 5 → 7/38, 데모 0/10. 3줄 0(wrap 700px, `script.lint` 와 같은 폭). 2줄은 모두 자막 구역(y ≥ 410) 안. `docs/handoff/reports/phaseG7/subtitle_lines.json`.
- 전/후: `docs/handoff/reports/phaseG7/scale_before_after.jpg`(hormuz 6·fed_policy 6컷), 골든 증명 `reports/phaseG7/golden_delta/`(expected_deltas `g7_scale_d0101`).
- 사용자가 480p 를 보고 "아직 작다"고 하면 2차 표(자막 22·카드 line 16)를 G8 뒤에 검토한다(D-0113).

## 10. v4.11.0 — 글자 크기 2차 표 (G10, back_and_forth D-0118 §3, 사용자 위임 D103)

§9 마지막 줄의 2차 표를 적용했다(G7 480p 판정 대신 사용자 위임). 수치 정본은 여전히 `rules/video_rules.yaml` 이다.

- 바뀐 키: `layout_480p.subtitle.size`(21 → 22), `layout_480p.card.line_size`(15 → 16). 그 밖 무변경(표 1·2 의 다른 값, 표 3 유지, card.line_gap 그대로).
- 자막 22 의 결과: 2줄 문장 hormuz 15 → 17/45, fed_policy 7 → 11/48, 랫클리프 7 → 10/38, 데모 0/10. 3줄 0. `docs/handoff/reports/phaseG10/subtitle_lines.json`.
- 카드 넘침 0: 가장 넓은 카드 fed_policy 436px(x ≥ 394), 카드 아래 끝 ≤ 204 — 자막 구역(410)과 멀다. 렌더 전 점검·checks hard 0(네 편).
- 골든: 23컷 변경(타이틀·엔딩 무변경), 변경 픽셀 요소 영역 안 100 %. expected_deltas `g10_scale_d0118`, 증명 `reports/phaseG10/golden_delta/`, 기준선 `reports/phaseG10/hormuz_baseline.json`·`regression_baselines.json`.

## v5.1.0 — 엔딩 카드 버전 도장 (G12, back_and_forth D-0124, 사용자 결정 D109)

- 엔딩 카드 오른쪽 아래 구석 `v{VERSION}`(`rules:layout_480p.end_card.version_stamp` — x_from_right 12·y_from_bottom 10·7.8 mono·alpha 0.55·halo 없음). 문자열은 렌더 시점 VERSION 파일(P3).
- 롤(scroll)에 실리지 않고 고정, 검정 홀드 구간에는 없다. 안내 줄(notice_unverified)과 겹치면 안내 줄을 우선하고 도장을 dy 만큼 위로. checks offscreen `[endcard-overflow]` 에 포함.
- **G4-14 와의 관계**: G4-14("화면 모서리에 날짜 외 요소 금지")는 본문 장면의 브랜드·섹션 표기를 막는 규칙이다. 엔딩 카드는 크레딧 텍스트 화면이라 대상이 아니며, 이 도장은 사용자 결정 D109 로 엔딩 카드에만 둔다(GOAL 본문 무변경).
- 골든 25_END: 도장 상자 안 86px 만 변경(expected_deltas `g12_version_stamp_d0124`). 기준선은 도장 상자를 가린 md5 — 버전 증분마다 재등재 불필요.
