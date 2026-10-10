<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-badges, v2-asset-rights]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 07. 인물 · 국기 · 휘장 뱃지와 권리 관리

사용자 평가: 인물·국기 표기 **"100점 만점에 120점"**(v2). 단 기관 휘장 누락 지적(v3에서 해결).
참조 코드: `v3/render3.py` `badge_at()`, `flag_wave()`, `scaled()`, `surf_from_pil()` / `v3/prep3.py` `portraits_emblems()`, `commons_get()`, `mono()`, `normalize_portrait()`, `flags()` / `v2/prep.py`

---

## 1. 레퍼런스 시각 문법 (사용자 첨부 이미지 기준)

- 원형 플레이트. 인물은 흑백 고대비 컷아웃.
- 원 안(뒤)에 **국기가 펄럭인다**. 국기는 원 밖으로 약간 삐져나올 만큼 크다.
- **어깨 아래는 원 안에 갇히고, 머리는 원 위로 튀어나온다**(입체감의 핵심).
- 원 아래 검은 반투명 라벨 박스, 흰 굵은 이름.
- 기관은 원 안에 휘장 전체, 국가·기구는 원형 국기.

---

## 2. 뱃지 합성 명세 (`badge_at(ctx, x, y, e, t, a)`)

R = 반지름(480p 기준 17~36px. 지도 위 인물 30~34, 패널 주인공 36, 국기 17~24).

### 2.1 레이어 순서
```
0. pop-in 변환: translate(x,y); scale(k)   k = ease_back(lt/0.55), c=1.7 (살짝 튀었다 안착)
1. 그림자: 원(1.5, 3) 반경 R+7 알파 0.10, R+4 알파 0.18 (검정)
2. clip(원 R) → 바탕 #1b2a3a 채움
   2a. person: 펄럭이는 4:3 국기 — 폭 2.3R, 중심 (0.25R, −0.05R), 알파 0.92
   2b. flag:   1:1 국기 — 폭 2.1R, 중심 정렬
   2c. emblem: 흰 바탕(0.96) 위에 휘장 이미지 폭 1.96R
3. person이면 인물 컷아웃:
   폭 1.72R, 아래끝 = 원 아래 + 0.02R (y = R − ph + 0.02R)
   clip = 원(R) ∪ 사각형(−0.66R, −2.4R, 1.32R, 2.4R)   ← FILL_RULE_WINDING 합집합
   → 어깨는 원 경계에서 잘리고, 머리는 원 위로 나온다
4. 테두리: 짙은 선 3.2px (0.03,0.04,0.06) 위에 강조색 1.5px (알파 0.92)
5. 라벨(0.3초 뒤 0.35초 페이드):
   기본: 원 아래 +5px에 둥근 사각형(r3, 폭=글자폭+16, 높이 20, 검정 0.84) + 이름 SemiBold 12px 흰색
         역할(role)은 그 아래 +38px, Medium 10px 강조색
   side='right': 원 오른쪽 +10px에 이름 13px, 역할 10px (패널 세로 목록용)
6. RESERVED 등록: (x−R−10, y−2.2R, x+R+10, y+R+44)
```

### 2.2 펄럭이는 국기 (`flag_wave`)
```python
fs = 국기 4:3 이미지를 폭 wdt로 스케일(캐시)
n = 14 세로 띠
for i in range(n):
    dy = sin(2.6t + 0.5i) * wdt * 0.032               # 띠마다 위상차 → 물결
    clip(띠 i 사각형); 국기를 dy만큼 내려 그림(알파 a)
    음영: 검정 × 0.16 × (0.5 + 0.5 sin(2.6t + 0.5i + 1.2)) — 주름 명암
```
비용이 낮다(띠 14개 × 뱃지 수). v2는 주파수 3.0, 음영 0.18, 진폭 0.035였고 v3는 조금 차분하게 낮췄다.

### 2.3 강조색(accent) 규칙
| accent | 색 | 쓰임 |
|---|---|---|
| gold | `#e8b860` | 한국/주인공/핵심 인물 |
| us | `#5aa9ff` | 미국 측 |
| ru | `#ff5566` | 러시아·이란 측(대립 측) |
| teal | `#5cc8da` | 중립/제3국, 통과 허가국 |
| muted | `#a9b0bd` | 목록 속 일반 국가 |

색은 진영을 암시한다. 논쟁 사안에서 한쪽만 붉게 칠하는 식의 편향 연출은 피하고, 사실 관계(요구한 쪽/거절한 쪽)에만 쓴다.

### 2.4 이미지 캐시
```python
scaled(key, w): 폭을 3px 단위로 반올림해 (key, w) 캐시. PIL LANCZOS 리사이즈 → cairo ARGB32(프리멀티플라이드 BGRA)
surf_from_pil(im): rgb*=alpha/255 → (B,G,R,A) → ImageSurface.create_for_data(buf, ARGB32, w, h, w*4)   # buf 참조 유지 필수
```

---

## 3. 인물 자산 수집

### 3.1 우선순위
1. **저장소 인물 라이브러리** `assets/library/people/{pid}_mono_v01.png` (RGBA 컷아웃, codex imagegen 가공, 권리 기록 완비). v2·v3에서 트럼프, 푸틴, 젤렌스키, 하메네이 사용.
2. 라이브러리에 없으면 **위키미디어 공용**에서 라이선스 확인 후 수집 → rembg 배경 제거 → 흑백화 → (권장) 저장소 codex 공방으로 재가공해 라이브러리 등록.

### 3.2 위키미디어 API
```python
# 후보 검색
GET https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={query}&gsrnamespace=6&gsrlimit=7
    &prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=960&format=json
extmetadata: LicenseShortName, Artist(HTML), Restrictions, Credit
# User-Agent 헤더 필수: 'osint-video-trial/0.3 (research)'
```
- **허용 라이선스**: Public domain, CC0, CC BY(1.0~4.0), KOGL Type 1(공공누리 제1유형). CC BY-SA는 파생물 라이선스 검토 필요(저장소 RIGHTS.md 규칙과 동일).
- **Restrictions 태그**(`personality`, `insignia`, `trademarked`, `communist`)가 있으면 자동 차단 → 사람 판단. (예: 이재명 2021 사진은 KOGL+personality → 제외, 같은 인물의 Public domain 공식 초상 사용)
- **다운로드 폭은 표준 썸네일 폭(예: 960) 또는 원본**. 비표준 폭(700 등)은 썸네일 생성 요청이 되어 **HTTP 429**가 반복된다(v2에서 실제 발생 — 저장소 RIGHTS.md의 교훈과 동일). 실패 시 원본 URL로 폴백, 6회 재시도, 지수적 대기.
- 받은 바이트는 `PIL.Image.open(BytesIO).verify()`로 검증(429 HTML이 jpg로 저장되는 사고 방지).

### 3.3 이번 세션에서 쓴 인물 원본
| 인물 | 파일 | 라이선스 | 비고 |
|---|---|---|---|
| 존 랫클리프 | Official Portrait of CIA Director John Ratcliffe.webp | Public domain (CIA) | v2 |
| 세르게이 나리시킨 | Sergey Naryshkin (2016-07-14).jpg | CC BY 4.0 (kremlin.ru) | v2, 크레딧 필수 |
| 알렉산드르 보르트니코프 | Bortnikov 2019 crop.jpg | CC BY 4.0 | v2, 크레딧 필수 |
| 이재명 | Lee Jae Myung portrait.jpg | Public domain | v3 |
| 노무현 | Roh Moo-hyun presidential portrait.jpg | KOGL Type 1 | v3, 출처표시 |
| 트럼프·푸틴·젤렌스키·하메네이 | 저장소 라이브러리 가공본 | 원본 권리는 저장소 photo_manifest | v2·v3 |

### 3.4 배경 제거와 흑백화
```python
from rembg import new_session, remove
sess = new_session('u2net_human_seg')                 # 최초 실행 시 모델 다운로드(~170MB)
cut = remove(img_rgb, session=sess).convert('RGBA')
cut.putalpha(cut.getchannel('A').filter(GaussianBlur(0.8)))    # 가장자리 부드럽게

def mono(im):                                          # 라이브러리 질감에 가깝게
    g = autocontrast(grayscale(im), cutoff=1.2).filter(UnsharpMask(radius=2, percent=90, threshold=2))
    x = g/255;  x = 0.5 + tanh((x − 0.52)*2.6) / (2*tanh(1.3))    # S자 대비 곡선
    return RGBA(x, x, x, alpha)

def normalize_portrait(im, out_w=420):                 # 머리-어깨 구도 통일
    alpha > 40 인 bbox; 폭 w; 높이 = min(bbox높이, 1.22w); 위에서부터 크롭; 폭 420으로 리사이즈
```
**한계(사용자에게 고지함)**: 사진을 이 방식으로 흑백화하면 라이브러리의 codex 가공본보다 질감이 거칠다. 새 인물은 저장소 공방(`assets/library/workshop/`, `$imagegen`, `portrait_panel.md` 템플릿)으로 가공해 라이브러리에 등록하는 것이 정석이다. rembg 경로는 긴급 폴백.

---

## 4. 국기

- 소스: **flag-icons (MIT)** `https://raw.githubusercontent.com/lipis/flag-icons/main/flags/{1x1|4x3}/{iso2}.svg`
- 변환: `cairosvg.svg2png` — 1:1은 256×256, 4:3은 480×360.
- 1:1은 국기 뱃지, 4:3은 인물 뱃지 배경(펄럭임).
- 저장소 기존 국기 9종(cn il ir jp kp kr lb ru us)은 우크라이나·유럽 국가가 없어 부족 → flag-icons 전체를 캐시하는 방식으로 교체.
- v3에서 쓴 코드: kr us ir om ae sa jp cn in pk qa iq kw bh ye sg my id gb fr de au nl ca it eu.

---

## 5. 휘장(기관·기업)

### 5.1 원칙
- 기관은 **실제 휘장**으로 표기한다(지적 1: 백악관·CIA·NATO가 문자 원으로 나와 불만).
- 휘장은 저작권과 별개로 **법적 사용 제한**이 있을 수 있다. 위키미디어 `Restrictions`에 `insignia`, `trademarked`가 있으면 사람 판단 전까지 쓰지 않고 **해당 국가 국기로 대체**한 뒤 권리 레지스트리에 사유를 남긴다.

### 5.2 이번 세션 판단 사례
| 기관 | 파일 | 라이선스/제한 | 판단 |
|---|---|---|---|
| 미 해군 중부사령부(NAVCENT) | United States Naval Forces Central Command patch 2014.png | Public domain, 제한 없음 | **사용**(v3, 호위 작전) |
| 한국 해군 | Emblem of the Republic of Korea Navy.svg | South Korea-Gov, insignia·trademarked | 미사용 → 태극기 |
| 대한민국 국방부 | Emblem of the Ministry of National Defense (South Korea) | South Korea-Gov, insignia·trademarked | 미사용 |
| 청해부대 | 위키미디어에 휘장 없음(사진만, CC BY-SA 2.0) | SA 파생 문제 | 미사용 → 태극기 + 라벨 |
| 이란 혁명수비대(IRGC) | Seal of the Army of the Guardians… | Public domain, insignia | 미사용(정책상 보류) |
| CIA 문장, 대통령 문장 | — | 미국 법상 승인 암시 사용 제한 | 보도 목적 사용은 통상 문제없으나 저장소 정책상 사용자 결정 필요 |

Claude Code 과제: `assets/emblems/registry.json`에 기관별로 `{file, license, restrictions, decision(use|flag_fallback|user_decision), reason}`을 두고, 렌더러가 decision을 따르게 한다.

---

## 6. 엔티티 레지스트리 (권장 신설)

인물·기관·국가를 이름으로 찾아 뱃지를 자동 구성하기 위한 사전:
```yaml
lee_jae_myung:
  kind: person
  names: [이재명, 이재명 대통령]
  flag: kr
  portrait: assets/library/people/lee_jae_myung_mono_v01.png   # 공방 가공 후
  role_default: 대한민국 대통령
  accent: gold
navcent:
  kind: emblem
  names: [미 해군 중부사령부, 5함대]
  image: assets/emblems/navcent.png
  fallback_flag: us
```
원고의 문장에서 `names`를 찾으면 해당 문장 시각에 뱃지를 제안할 수 있다(번들 어댑터의 mention 탐지와 동일 원리, `12` §4).

---

## 7. 권리 레지스트리와 크레딧

### 7.1 형식 (`rights_registry.json`, v3)
```json
{"people": {"lee_jae_myung": {"src": "wikimedia_commons", "license": "Public domain", "artist": "...", "url": "https://commons.wikimedia.org/wiki/File:...", "title": "File:Lee Jae Myung portrait.jpg"},
            "trump": {"src": "repo_library", "license": "Public domain", "artist": "Shealeah Craighead", "url": "..."}},
 "emblems": {"navcent": {"license": "Public domain", "url": "...", "title": "File:United States Naval Forces Central Command patch 2014.png", "restrictions": ""}}}
```

### 7.2 엔딩 크레딧 자동 생성 (`credits()`)
- 인물: `{이름} 사진{(라이브러리 가공본)}: {license}{ · 저작자}` — PD는 저작자 생략.
- 휘장, 국기(flag-icons MIT), 지도(Natural Earth), 지형(AWS Terrain Tiles), 음악(Chris Zabriskie CC BY 4.0), 내레이션(AI 음성 합성), 자료 출처 목록.
- 유튜브 설명문에도 같은 내용(CC BY 곡은 설명란 표기 의무 — 저장소 BGM RIGHTS.md).


### 7.3 출처 표기 의무와 위치 (라운드 6 논의)
- 법적으로 필요한 것은 **특정 라이선스가 요구하는 출처 표시**다: CC BY(음악·사진), 공공누리 제1유형(출처표시). 퍼블릭 도메인(미국 정부 저작물, Natural Earth)은 의무 없음. flag-icons(MIT)는 영상 속 이미지에 통상 표기하지 않음. AWS 지형 타일은 구성 데이터별 조건 확인 필요.
- CC BY 4.0은 매체·맥락에 맞는 **합리적 방식**이면 충족(링크 제공 포함) → 유튜브 설명란만으로도 충족 가능. 유튜브 오디오 보관함의 CC BY 곡도 설명란 표기를 요구한다.
- 그럼에도 **사용자 결정으로 엔딩 카드를 유지**한다(고급·작은 글씨 디자인, `09` §6.2). 영상 내 캡션(사진·영상 출처 줄) + 엔딩 카드 + 설명란 3중 표기가 기본값.
- 저장소 BGM RIGHTS.md는 "영상 하단 출처 라인 + 설명란"을 요구 — 엔딩 카드 유지로 충족.
- 공공누리·지형 타일의 표기 위치 요건은 원문 재확인 권고(법률 자문 아님).

---

## 8. v4.8.0 — 인물 배지 적응 크기·머리 예약 실측·청와대 휘장 (G7, back_and_forth D-0101 §1·D-0104 D2(c)·D-0109·D-0111·D-0112)

사용자 지시(D89): "한 사람만 나오면 크게, 여러 사람이 더 등장하면 작아지는 효과".

- **크기는 코드가 정한다(P8).** 같은 풀(지도·시간축 무대 / 패널 위 뱃지)에서 표시 구간(팝인 완료 ~ 페이드 아웃 시작)인 인물 뱃지 수 n(t):
  n = 1 → `badge.R_person_solo` 56, n = 2 → `R_person_group[1]` 34, n ≥ 3 → `R_person_group[0]` 30. 바뀌면 `resize_sec` 0.6 동안 smooth 보간.
  새 뱃지는 자기 자신을 세어 처음부터 그 크기로 뜨고, 사라지는 뱃지는 끝까지 자기 자신을 센다(페이드 아웃 중 커지지 않음). 카메라 화면 안 여부는 세지 않는다(t 만의 함수).
- **인물 뱃지의 연출 `R:` 는 버린다**(D-0111 A) — provenance `badge.R_ignored[]` + warning `[badge-R-ignored]`. 국기·휘장 R 은 그대로 우선, 없으면 `badge.R_other` 30.
- 이름표 글자: solo 15/11, group 12/10, side:right 13/10 — R 에 따라 group ↔ solo 보간(`label_sizes`).
- **머리 예약 = 초상 실측**(D-0112 A): 불러올 때 초상 PNG 알파 윗줄로 `head_top`(R 단위) 계산, 상한 `reserve_top_factor` 2.2. 저장소 초상 35장 1.02~1.13R. `head_reserve: factor` 로 되돌린다. provenance `badge.head_top[]`(초상 md5).
- **화면 가장자리 보정**(`edge_nudge`): 앵커가 화면 안인데 그 순간 상자가 밖이면 그 px 만큼 안쪽으로 — 카드 회피(D-0033)보다 먼저, provenance `reserved.avoidance` strategy `edge`. 보정 뒤에도 밖이면 offscreen hard.
- **자리**: 시간축 `timeline_badge` [640, 186](solo 상자가 레인 영역·축 값 자리 밖). 패널 장면(패널이 떠 있는 순간 시작하는 map_* 뱃지)은 `stage_slots.panel → panel_badge` 화면 고정 점 [[96,300],[758,300]], 패널 층 위에 그린다(D2(c), dmz_mine M7).
- **청와대 휘장**(D-0109, 사용자 결정 D98): `assets/emblems/registry.json cheongwadae` — Commons 대통령 표장(Public domain, restrictions insignia 기록 유지), `user_exception: D98` + `exception_scope`(청와대·대통령실이 발언·행위 주체인 문장의 식별 표시 전용, 무가공, 크레딧). 예외는 `schemas/emblem_models.USER_EXCEPTIONS` 목록만 — 다른 제한 휘장은 §5 그대로 국기 대체. 연출 문법 한 줄(`rules direction_grammar`): 대통령 개인이 주체면 초상, 둘 다면 초상 우선.

- **v5.1.0 크레딧(G12)**: 배경 사진(`backdrop.img`)·프레스 사진(`article.press`)도 `media.<id>` 권리 참조로 요구된다(`engine.credits.required_refs`) — credits.yaml 에 그 항목이 없으면 렌더 전 RightsError.

## 9. v5.5.0 — 인물 정수리는 원 안에 (사용자 결정 2026-10-02, RENDER-AP-006)

§2.1 3단계의 "머리는 원 위로 나온다"(v3 합집합 clip)는 **폐기**한다. 사용자 시청 지적: 정수리가 원 테두리 밖으로 나온 모습이 어색하다.
`rules badge.head_popout: false` 이면 인물 컷아웃도 원(R) 하나로 clip 하고, 실측 정수리(`portrait_head_top`)가 원 꼭대기에서
`head_inside_max`·R 보다 깊이 내려오도록 컷아웃을 아래로 민다(어깨가 더 잘린다). 머리 예약(`head_factor`)은 1.0 — 원 밖으로 나오는 머리가 없다.
골든 재기준선 phaseG16(expected_deltas `g16_head_path`).

## 10. v5.15.0 — 인물 뱃지 V2·국기 물결 (back_and_forth D-0153 §5·D-0158, 사용자 결정 D148, 가이드 23 §10)

§9 의 "`head_inside_max` 만큼 아래로 민다" 배치를 바꾼다(정수리가 원 안인 원칙은 그대로). 수치는 전부 `rules layout_480p.badge.{portrait, flag_wave, ring}`.
- **초상**: 폭 `2.04R`(옛 1.72R). 원본 알파 > `alpha_thr`(20) 맨 윗줄(정수리)을 중심 위 `0.83R` 에 둔다 — 같은 인물 픽셀의 확대·배치이고 얼굴을 다시 만들지 않는다.
  배치용 문턱 20 은 정규화(`tools/portrait_fallback`, 알파 > 40 bbox)와 목적이 달라 따로 둔다. 얼굴 분리 그림자 = 초상 알파 모양을 0.8 설계 px 아래에 검정 0.16.
- **국기 물결**: 중심 `(0.16R, −0.05R)`, 폭 `2.3R`, 원 안 클립. 세로 띠 수 = 장치 폭 기반(`clamp(ceil(장치 폭 ÷ strip_px), 14, 96)` — 480p solo 96, group 은 장치 폭만큼).
  위상 `t·2.6 + (i/n)·7`, 진폭 `0.018·폭`(옛 14띠·0.032). 띠 경계 = 장치 픽셀 정수 열이라 겹침·빈 줄이 없다. 작업 표면은 국기·크기당 한 번 만들어 다시 쓴다.
- **링**(인물만): 바깥 어두운 `2.4`(원 바깥쪽), 안쪽 accent `0.8`(원 안쪽) 설계 px. 국기·휘장 뱃지 링(3.2/1.5)과 국장 뱃지는 그대로.
- 국기 모양·색 영역은 원본 그대로(flag-icons MIT 고지 유지). 골든 재기준선 phaseQ2(expected_deltas `q2_portrait_flag_d148`).
