<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-map-engine]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 04. 지도 엔진

참조 코드: `v3_hormuz_korea/prep3.py` (티어·지오메트리), `render3.py` (`View`, `draw_borders`, `draw_labels`, `draw_country`), v1 `base.py`/`common.py` (벡터 베이스맵), v2 `prep.py`

---

## 1. 좌표계와 투영

### 1.1 메르카토르 "도 단위"
```python
def ym(lat):  return degrees(log(tan(pi/4 + radians(lat)/2)))      # 위도 → v
def lat_of(v): return degrees(2*atan(exp(radians(v))) - pi/2)          # 역변환
u = lon
```
u, v 모두 "도" 단위다. 해상도는 **ppd(경도 1도당 픽셀)** 하나로 정해진다. 이 방식의 장점:
- 지형 타일(Web Mercator)과 **선형 관계** → 타일 모자이크를 아핀 변환(EXTENT) 한 번으로 티어 격자에 옮길 수 있다.
- 카메라 보간이 (u, v, log w) 공간에서 자연스럽다.

### 1.2 화면 변환 (`View`)
```python
w  = 카메라 가로 폭(경도 도)          s  = W_OUT / w        # px per degree
h  = w * H_OUT / W_OUT              # 세로 폭(v 단위)
u0 = clamp(lon - w/2, umin, umax - w)
v1 = clamp(v + h/2, vmin + h, vmax)  # 화면 위쪽 경계
x  = (lon - u0) * s
y  = (v1 - ym(lat)) * s
```
- `umin/umax/vmin/vmax`는 **광역 티어 W의 경계**. 카메라가 경계를 넘지 않게 클램프하고, `w`도 티어 폭보다 크지 않게 줄인다.
- 링 배열은 전처리 때 (u, v)로 변환해 두고(`to_uv`), 프레임마다 `uvs(uv)`로 벡터화 변환.

### 1.3 필요한 해상도
- 480p: 필요 ppd = 854 / w. 예: w=6.4(한반도) → 133 ppd, w=14(걸프) → 61 ppd, w=90(광역) → 9.5 ppd.
- 1080p: 1920 / w (2.25배). 티어 ppd를 같은 비율로 올리거나 확대 한계를 w 기준으로 제한한다.

---

## 2. 데이터 소스

| 데이터 | URL/출처 | 쓰는 필드 |
|---|---|---|
| 국가 | `raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson` | `ISO_A2_EH`(없으면 `ADMIN`), `NAME_KO`, `LABEL_X`, `LABEL_Y`, `LABELRANK`, `MIN_LABEL` |
| 1급 행정구역 | `ne_10m_admin_1_states_provinces.geojson` | `iso_a2`, `name_ko`, `name`, `longitude`, `latitude`, `name_en` |
| 도시 | `ne_10m_populated_places.geojson` | `NAME_KO`, `SCALERANK`, `FEATURECLA`, `ADM0CAP`, `POP_MAX`, `ADM0_A3` |
| 강·호수(v1) | `ne_10m_rivers_lake_centerlines`, `ne_10m_rivers_europe`, `ne_10m_lakes(_europe)` | `name`, `scalerank` |
| 지형 | `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` (Mapzen/AWS Open Data) | RGB → 고도 |
| 점령지(v1) | DeepState API (`06` §6) | 폴리곤 |

모두 공개 데이터다. 크레딧: "지도: Natural Earth · 지형: AWS Terrain Tiles (Mapzen)".

---

## 3. 지오메트리 전처리 (`prep3.py`)

### 3.1 국가 로드
```python
bb = box(20, -20, 150, 60)                                  # v3 작업 영역
for f in admin0:
    g = shape(f['geometry']).buffer(0)                      # 자기교차 정리
    if not g.intersects(bb): continue
    key = ISO_A2_EH if ISO_A2_EH not in (None, '-99') else ADMIN
    G[key] = g.intersection(bb)
```

### 3.2 크림반도 재분류 (v1·v2 필수, 우크라이나 관련 영상 전체에 적용)
Natural Earth 기본 데이터는 크림반도를 러시아로 분류한다. 국제적으로 인정된 경계(유엔 총회 결의 68/262)에 맞춰:
```python
crimea = union(admin1 where name_en in ('Autonomous Republic of Crimea', 'Sevastopol'))
G['UA'] = union(G['UA'], crimea)
G['RU'] = G['RU'].difference(crimea.buffer(0.001))
```
엔딩 크레딧에 "크림반도는 국제적으로 인정된 우크라이나 영토로 표시" 명시.

### 3.3 재귀 평탄화 — 프랑스 버그의 원인과 수정 (지적 5)
> **주석(v4.1.0, back_and_forth D-0078)**: 또 다른 원인 — 같은 ISO 키 피처 덮어쓰기(FR = 프랑스 → 클리퍼턴, KZ = 카자흐스탄 → 바이코누르). 지금은 합집합 + 면적 커버리지 검사(PIPELINE-AP-011). 아래 과거 서술은 그대로 둔다.
**증상(v2)**: 프랑스가 바다(대륙붕) 색으로 칠해져 사라져 보임.
**원인**: `g.intersection(bb)`나 `simplify()` 결과가 `GeometryCollection` 안에 `MultiPolygon`을 담는 형태가 될 수 있다. v2의 `rings()`는 `getattr(g, 'geoms', [g])`로 **1단계만** 펼쳐 `Polygon`만 수집했기 때문에, 중첩된 `MultiPolygon`(프랑스 본토)이 통째로 빠졌다.
**수정(v3)**:
```python
def polys(g):
    if g is None or g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    if hasattr(g, 'geoms'):
        out = []
        for x in g.geoms: out += polys(x)     # 재귀
        return out
    return []                                 # LineString/Point 무시
```

### 3.4 커버리지 검사 (재발 방지)
티어 래스터화 직후, 국가마다 `representative_point()`가 티어 안에 있는데 육지 마스크 값이 128 미만이면 누락으로 보고:
```python
for k, g in G.items():
    rp = g.representative_point(); x, y = 티어 픽셀 좌표(rp)
    if 티어 안 and mask[y, x] < 128: miss.append(k)
print('land-miss=', miss)
```
v3 결과: W 티어 `['MV']`(몰디브, 24ppd에서 섬이 너무 작음 — 무해), G·K 티어 누락 없음. **Claude Code는 누락이 "작은 섬 국가"가 아니면 실패로 처리하는 테스트를 만든다.**

### 3.5 단순화와 링 추출
```python
coarse = rings(g, 0.03)     # 광역(w ≥ 22)
fine   = rings(g, 0.005)    # 확대(w < 22)
admin1 = rings(a, 0.006)
# rings(): polys(g.simplify(tol, preserve_topology=True))의 외곽+내부 링을 float32 (N,2)로
```

### 3.6 라벨용 데이터
- 국가: `meta[key] = {name, ko=NAME_KO, lx=LABEL_X, ly=LABEL_Y, rank=LABELRANK, minlab=MIN_LABEL}`
- 행정구역: `admin1[ISO2] = [{name=name_ko or name, lx=longitude, ly=latitude, rings}]` (v3 대상: KR, IR, OM, AE, SA, QA, KW, BH, IQ, KP, JP, YE)
- 도시: `places = [{ko=NAME_KO, lon, lat, rank=SCALERANK, cap=('capital' in FEATURECLA) or ADM0CAP==1, iso, pop=POP_MAX}]` — `NAME_KO`가 없는 도시는 제외(3,013개 수록).

---

## 4. 지형 베이스 래스터 (티어)

### 4.1 v3 티어 정의
```python
TIERS = {
  'W': dict(lon0=28.0,  lon1=140.0, lat0=-12.0, lat1=48.0, ppd=24, z=5),   # 광역: 중동~동아시아
  'G': dict(lon0=46.0,  lon1=62.0,  lat0=20.5,  lat1=32.5, ppd=96, z=7),   # 걸프·호르무즈
  'K': dict(lon0=122.5, lon1=131.8, lat0=32.3,  lat1=39.8, ppd=96, z=7),   # 한반도
}
levels = [ppd, ppd/2, ppd/4]   # LANCZOS로 두 번 절반 축소
```
v2: W(lon −90~67, lat 12~68, 32ppd, z5) + E(동유럽 lon 18~46, lat 38~58, 128ppd, z7).
v1: 흑해 권역(lon 18~46, lat 39.5~57.5) 벡터 렌더 피라미드 200/100/50 ppd(지형 래스터 없이 벡터 채움 + 해안 글로우 + 경위선).

### 4.2 타일 범위 계산
```python
n = 2**z
tx(lon) = floor((lon + 180) / 360 * n)
ty(lat) = floor((1 - ln(tan(lat) + sec(lat)) / π) / 2 * n)
# v3: W z5 x18–28, y11–17 (77장) / G z7 x80–86, y51–56 (42장) / K z7 x107–110, y48–51 (16장)
```
병렬 다운로드(`xargs -P 16 curl`). 100바이트 미만 파일은 무시.

### 4.3 모자이크와 재표본화
```python
elev = R*256 + G + B/256 - 32768                        # terrarium 디코딩(미터)
M = 타일을 (ty-y0)*256, (tx-x0)*256 위치에 배치한 float32 배열
S = 256 * 2**z
extent = ((lon0+180)/360*S - x0*256,  (1 - ym(lat1)/180)/2*S - y0*256,
          (lon1+180)/360*S - x0*256,  (1 - ym(lat0)/180)/2*S - y0*256)
E = Image.fromarray(M,'F').transform((W,H), Image.EXTENT, extent, Image.BICUBIC)
# W = (lon1-lon0)*ppd,  H = (ym(lat1)-ym(lat0))*ppd
```
Web Mercator 픽셀과 도 단위 v가 선형이라 EXTENT 한 번으로 정확하다.

### 4.4 육지 마스크
- 국가 링을 티어 픽셀로 변환해 `ImageDraw.polygon(fill=255)`(외곽·내부 링 모두 칠함 — 호수는 이 축척에서 육지로 둔다).
- 단순화 허용치: ppd<64면 0.02°, 아니면 0.003°.
- 가장자리 부드럽게: `GaussianBlur(0.6)` 후 /255.

### 4.5 힐셰이드
```python
lat_rows = 각 행 중심의 위도;  mpp = 111320*cos(lat)/ppd      # 픽셀당 미터
ex = 2.8 if ppd < 64 else 2.0                               # 수직 과장 (v2: 2.6/1.8)
gy, gx = np.gradient(max(E,0) * ex);  gx /= mpp; gy /= mpp
az, alt = radians(315), radians(42)
slope = arctan(hypot(gx, gy));  aspect = arctan2(-gx, gy)
hs = clip(sin(alt)*cos(slope) + cos(alt)*sin(slope)*cos(az - aspect), 0, 1)
```

### 4.6 색 (v3 정본 — 사용자 합격)
```python
# 육지: 고도 램프 × 음영
land_ramp = [(0,'#2b313a'), (400,'#30353c'), (1500,'#3b3a3a'), (4000,'#4b4640')]
lc = ramp(clip(E,0,4000)) * clip(0.58 + 0.95*(hs - sin(alt)), 0.5, 1.5)
# 바다: 수심 램프
sea_ramp = [(0,'#1c4a66'), (60,'#18415c'), (400,'#11304a'), (2000,'#0c2236'), (6000,'#081626')]
sc = ramp(clip(-E,0,6000))
# 해안 글로우(바다 쪽)
glow = GaussianBlur(mask, 3 if ppd<64 else 8) / 255
sc += rgb('#3a9cb8') * glow * 0.2
out = sc*(1-land) + lc*land
```
v2 팔레트(육지 `#1c2129` 계열)는 너무 어두워 로드 시 `×1.32+10`으로 보정했다. v3는 팔레트 자체를 밝혀 보정 없이 쓴다. **육지(회색 계열)와 대륙붕(청색 계열)은 색상 자체가 달라야 한다** — 프랑스 문제의 시각적 혼동이 재발하지 않는다.

### 4.7 저장
`base_{name}_{ppd}.png`, `base_{name}_{ppd/2}.png`, `base_{name}_{ppd/4}.png` + `tiers.pkl`에 `levels` 기록.

---

## 5. 티어 선택과 블렌딩 (`View.base`)

```python
need = W_OUT / w
im = tier('W', need)
for n in ('G', 'K'):
    if view가 티어 n 안에 완전히 들어감(여유 0.05도):
        a = smooth((need - 26) / 18)          # need 26ppd부터 섞기 시작, 44ppd에서 완전 전환
        if a > 0.01: im = Image.blend(im, tier(n, need), a)

def tier(n, need):
    lv = 가장 작은 level ≥ need*0.95, 없으면 최대 level
    x0 = (u0 - lon0)*lv;  y0 = (ym(lat1) - v1)*lv
    box = (max(0,x0), max(0,y0), min(x0 + w*lv, img.width), min(y0 + h*lv, img.height))   # ★ 클램프
    return img.resize((W_OUT, H_OUT), Image.BILINEAR, box=box)
```
- **박스 클램프 필수**: v2에서 부동소수 오차로 `box can't exceed original image size`(ValueError) 발생.
- 티어 경계를 걸치는 화면에서는 고해상도 티어를 쓰지 않는다(이음새 방지).
- 성능: 5000×2600 이미지에서 박스 리사이즈는 프레임당 수 ms.

---

## 6. 국경과 행정구역 (`draw_borders`)

```python
lod = 'fine' if w < 22 else 'coarse'
모든 국가 링 → path (bbox 컬링 + 화면상 1px 미만 링 생략)
stroke: rgba(0.82, 0.86, 0.92, 0.36 if w<40 else 0.26), width 0.75, LINE_JOIN_ROUND

# 행정구역(1급) — 확대 시 점진적으로
a = 0.3 * smooth((24 - w) / 10)             # w=24에서 0, w=14에서 0.3
dash [2.5, 2.5], width 0.55, rgba(0.8, 0.84, 0.9, a), 화면상 2px 미만 링 생략
```

---

## 7. 라벨 LOD (`draw_labels`) — 지적 9 해결의 핵심

패널이 떠 있으면 라벨 알파 = 1 − 패널 알파(패널이 완전히 덮으면 생략).

### 7.1 충돌 관리
- 프레임 시작 시 `RESERVED.clear()`.
- 마커·뱃지가 그려질 때 자기 영역(라벨 포함)을 `RESERVED`에 추가.
- 라벨은 `placed = RESERVED 복사본`에 대해 사각형 겹침 검사 → 겹치면 생략, 아니면 그리고 추가.
- 그리는 순서가 우선순위다: 해역 → 국가 → 도(道) → 도시.

### 7.2 해역 이름
```python
SEAS = [('페르시아만', 51.2, 27.6, 0, 34), ('오만만', 58.9, 24.4, 0, 30), ('아라비아해', 63.5, 15.5, 16, 140),
        ('인도양', 79, -3, 40, 140), ('벵골만', 88.5, 14.5, 40, 140), ('남중국해', 113.5, 14.5, 40, 140),
        ('동해', 130.9, 38.3, 2, 40), ('서해', 124.0, 36.0, 2, 40), ('홍해', 38.8, 20.0, 30, 140), ('아덴만', 48.5, 12.4, 16, 140)]
# (이름, lon, lat, 표시 최소 w, 최대 w)
style: Noto Serif CJK KR, 11px(w>30) / 12px, 자간 2.2, 색 #9cc8e6, 알파 0.62, 헤일로 없음
```
해역 목록은 주제마다 추가한다(흑해·아조우해 등은 v1 `STATIC_LABELS` 참조).

### 7.3 국가명
```python
thr = 2 if w>60 else 4 if w>30 else 6 if w>12 else 9     # LABELRANK 임계
w<12이고 국가가 KR이면 생략(한반도 확대 시 도·도시 우선)
화면 y 60~H-70 범위만 (날짜 배지·자막 영역 회피)
이름: KO 사전 우선(짧은 관용명: '북한', '대한민국', '사우디아라비아', '튀르키예' 등), 없으면 NAME_KO
style: IBM Plex Sans KR Medium 12(w>30)/13px, 자간 1.8, 알파 0.55, 헤일로 2.2
```
`KO` 사전은 `render3.py` 참조. NE의 NAME_KO는 공식 국호가 길어(예: 조선민주주의인민공화국) 화면용 관용명으로 덮어쓴다.

### 7.4 도(道) 이름
w < 8.5일 때 KR·KP의 admin1 이름을 9.5px, 알파 0.42로. 다른 나라로 확장 가능(해당 국가 확대 장면이 있을 때).

### 7.5 도시
```python
rk = 1 if w>60 else 2 if w>25 else 4 if w>12 else 6 if w>5 else 8     # SCALERANK 임계
후보 = 화면 x 12~W-12, y 58~H-72 안 & (rank ≤ rk  or  (수도 and rank ≤ rk+2))
정렬 = rank 오름차순, 인구 내림차순, 상위 40개 → 겹침 없는 것 최대 18개
점: 수도 r2.4 / 일반 r1.9, 흰색 0.9 + 검은 테 0.8px
라벨: 수도 IBM Plex Sans KR SemiBold 11.5 / 일반 Medium 10.5, 점 오른쪽 5px, 헤일로 2.6, 알파 0.82
```
이벤트 마커(예: '서울' 마커)가 RESERVED를 먼저 차지하므로 같은 도시 라벨이 중복되지 않는다.

---

## 8. 국가 강조 (`draw_country`)

```python
lod 동일; 해당 국가 링 path(EVEN_ODD)
fill: col × a (v3 이란 0.07 — 0.13은 화면이 붉게 뜸, 사용자 화면 기준 과함)
3중 글로우 테두리: (6px, 0.07), (2.6px, 0.2), (1.1px, 0.85)  × 페이드 알파
페이드 인 0.8초, 아웃 0.6초
```
강조 채움은 **낮은 알파**로. 큰 나라를 채우면 화면 전체가 물든다.

---

## 9. 새 권역을 추가하는 절차 (체크리스트)

1. 원고의 모든 장소를 나열하고, 장면별 카메라 폭 w를 정한다.
2. 최소 w로 필요한 ppd 계산(480p: 854/w, 1080p: 1920/w).
3. 광역 티어가 모든 카메라 프레임을 포함하는지 확인(클램프 때문에 가장자리 장소는 화면 끝에 붙는다 — v3 울산/부산 뱃지 잘림 사례).
4. 확대 장면마다 고해상도 티어(z7, 96ppd 내외)를 둔다. 티어 bbox는 카메라 화면 전체보다 넉넉히.
5. 타일 범위 계산 → 다운로드 → `build_tier` → `land-miss` 확인.
6. 행정구역 대상 국가 목록과 해역 이름 목록 갱신.
7. 프리뷰로 라벨 밀도 확인(너무 많으면 rk/thr 조정은 전역이 아니라 **장면별 오버라이드**로).

---

## 10. 함정 모음

| 함정 | 증상 | 대책 |
|---|---|---|
| GeometryCollection 1단계 평탄화 | 나라가 바다색(프랑스) | 재귀 `polys()` + 커버리지 검사 |
| NE 크림반도 분류 | 러시아 영토로 표시 | admin1로 재분류 |
| 리사이즈 박스 초과 | ValueError | 박스 클램프 |
| 광역 티어 경계 | 카메라가 원하는 곳에 못 감, 뱃지 잘림 | 카메라 중심 조정, 뱃지를 화면 안쪽 바다 쪽으로 |
| 고해상도 티어 걸침 | 이음새 | inside 검사 통과 시에만 블렌딩 |
| 육지가 너무 어두움 | 화면이 검게 뭉침 | v3 팔레트 |
| 국가 채움 과다 | 화면이 붉게 물듦 | 알파 0.07~0.2 |
| NE 국호가 김 | 라벨 폭주 | KO 관용명 사전 |
| sh의 중괄호 확장 미지원 | `mkdir -p a/{b,c}`가 `{b,c}` 폴더 생성 | 경로를 풀어 쓰거나 bash 사용 |
