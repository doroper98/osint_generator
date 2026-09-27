<!--
tier: 2
last_synced_with: v0.43.4
ssot_for: [v2-map-overlays]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 06. 지도 오버레이와 데이터 레이어

참조 코드: `v3/render3.py` (marker, route, tanker, barrier, ships, boom, country), `v2/render2.py` (arc, plane, channel, shield, occupied), v1 `render.py`/`events.py`/`ds_proc.py` (arrow, dots, occupied, timelapse)

공통 헬퍼:
```python
window(t, t0, t1, fin, fout)  # smoothstep 페이드 인/아웃 알파
glow_line(ctx, pts, col, a, w, dash)   # 3중 스트로크: (w*4.5, 0.08), (w*2.2, 0.22), (w, 0.95), 둥근 캡/조인
```

---

## 1. 마커 (`draw_marker`)

| 요소 | 값 |
|---|---|
| 펄스 링 | 2개, 주기 2초(`lt*0.5`), 반경 4→24px(ease_out), 알파 0.5×(1−f), 선 1.3px |
| 색 | hl=True면 금색 `#e8b860`, 아니면 흰색 |
| 아이콘 | `dot`: 반경 3.3 흰색 + 검은 테 1px / `boom`: 10꼭짓점 별(반경 9/4, 6/3) 호박색 `#ffb347` |
| 아이콘 등장 | ease_out 0.3초 |
| 라벨 | IBM Plex Sans KR SemiBold 13px 흰색, 헤일로 3.2 |
| 서브라벨 | Medium 10.5px 금색, 라벨 아래 15px |
| 라벨 위치 | right (12, 4, 좌정렬) / left (−12, 4, 우정렬) / top (0, −14, 중앙) / bottom (0, 22, 중앙) |
| 라벨 등장 | 0.2초 지연 후 0.4초 페이드 |
| 화면 밖 | x<−80, x>W+80, y<−40, y>H+40이면 생략 |
| 예약 | 라벨 폭+20 영역을 RESERVED에 등록(도시 라벨 충돌 방지) |

서브라벨에 날짜·수치를 넣는다("3월 2일 IRGC 봉쇄 선언", "가장 좁은 곳 약 39km"). 도장은 쓰지 않는다(지적 11).

---

## 2. 경로와 유조선 (`draw_route`, `tanker`, `draw_tanker_loop`)

### 2.1 경로 곡선
```python
uv = [(lon, ym(lat)) for lon, lat in waypoints]
curve = catmull_rom(uv, n=12)          # 구간당 12샘플, 끝점 반복 패딩
prog = ease_io((t - t0)/grow)          # 점진 드로잉
sub = screen(curve)[:max(2, int(len*prog))]
glow_line(sub, col, a, 1.9, dash=[5,4] if dashed)
```
Catmull-Rom 식: `0.5*((2p1) + (−p0+p2)s + (2p0−5p1+4p2−p3)s² + (−p0+3p1−3p2+p3)s³)`.

### 2.2 v3 유조선 항로 웨이포인트 (호르무즈 → 울산)
```python
ROUTE = [(56.2,26.45),(57.8,24.9),(60.5,22.6),(65.0,18.2),(72.0,11.0),(79.5,5.4),(88.0,5.6),(95.2,5.9),(98.8,4.6),
         (101.5,2.6),(104.1,1.25),(106.5,3.8),(110.0,9.5),(115.0,15.5),(120.2,20.2),(122.4,23.8),(123.8,28.2),
         (126.2,32.2),(128.6,34.5),(129.35,35.45)]
```
오만만 → 아라비아해 → 스리랑카 남쪽 → 믈라카 해협 → 싱가포르 → 남중국해 → 바시 해협(대만 동쪽) → 동중국해 → 남해안. 청해부대 항로(`CHEONG`)는 부산→아덴만 역방향 + (60,12)(52.5,12.6)(47.2,12.3).

**원칙**: 항로는 실제 해상 통로를 따라야 한다. 육지를 가로지르면 즉시 신뢰를 잃는다. 웨이포인트를 해협 중앙에 찍고 프리뷰로 확인한다.

### 2.3 유조선 글리프
```python
translate(x,y); rotate(접선각); scale(sc)
빛번짐: 방사 그라데이션 반경 15, (1, 0.85, 0.5, 0.45a) → 투명
선체: (9,0)→(5,−3)→(−8,−3)→(−8,3)→(5,3) 흰색 채움 + 검은 0.6px 테
브리지: rect(−7,−2,3,4) 짙은 회청색
```
경로 선두에 붙어 이동한다(`ship=True`). 점선 경로(`dashed=True`)는 완성 시 끝에 화살촉(길이 9px).

### 2.4 순환 유조선 (`tanker_loop`)
엔딩 장면에서 항로 위 유조선 3척이 26초 주기로 순환(위상 0, 1/3, 2/3), 크기 0.85배. 경로는 `glow_only=True`, 즉시 표시.

---

## 3. 두 점 호와 비행기 (v2 `draw_arc`, `plane_glyph`)

```python
u0,v0 = p0; u1,v1 = p1; mid; d = 거리
normal = (−(v1−v0), u1−u0)/d  — 북쪽(+v)을 향하도록 부호 선택
ctrl = mid + normal * d * bulge      # flow 0.16, tension 0.10
curve = 2차 베지어 72샘플
tension(대립) = 붉은 점선 [5,4], flow(흐름) = 금색 실선
진행 중 plane=True면 선두에 비행기 글리프(접선 방향), 완료 후 화살촉
라벨은 label_t 비율 위치(번들 arcs의 label_t), 완료 0.4초 뒤 페이드
```
비행기 글리프 경로 좌표는 `render2.py` `plane_glyph()` 참조(날개·꼬리 포함 20점 다각형 + 금빛 방사 번짐).

---

## 4. 봉쇄선 (`draw_barrier`)
```python
k = ease_out((t - t0)/0.8)                 # 0.8초에 걸쳐 그어짐
glow_line([p0, p0+(p1−p0)k], 붉은색 #ff5566, a, 3.2)
k > 0.95 → '봉쇄' SemiBold 12.5 붉은색, 선 중점 왼쪽
```
v3 좌표: 이란 해안(56.28, 27.05) → 무산담 반도 끝(56.42, 26.28).

---

## 5. 선박 입자 (`draw_ships`) — 발 묶인 배 1,000척
```python
최초 1회: 걸프 bbox(48.3~56.2E, 24.2~29.9N)에서 균등 난수, 모든 국가 fine 링(shapely prepared)에 포함되면 기각 → 150개 (seed 4)
등장: 각 점 위상 ph∈[0,1)에 대해 t0 + ph*1.6초 이후 표시
그리기: 반경 1.7, 색 (1, 0.82, 0.5), 알파 0.85 × (0.6 + 0.4 sin(2t + 9ph))  — 반짝임
```
숫자는 상징적 밀도다. 실제 수(약 1,000척)는 카드에 텍스트로 명시한다.

---

## 6. 점령지 — DeepState (v1·v2, 우크라이나 관련 영상용)

### 6.1 수집
```
GET https://deepstatemap.live/api/history/public           → [{id(=유닉스시각), updatedAt, ...}] (2022-04 ~ 현재, 1,767건)
GET https://deepstatemap.live/api/history/{id}/geojson     → FeatureCollection
```
월별 스냅숏: 각 달 1일에 가장 가까운 id 선택 + 특정 사건일 추가 → 61개 다운로드(총 32MB).

### 6.2 분류와 병합 (`ds_proc.py`)
```python
keep if name.lower() contains any of ('occupied','окуп','ордло','ordlo','crimea','крим','tuzla','тузла')
peak 모드(2022-04-03)에서는 해방 지역('звільн','liberat','під питанням','невідомо','24.03')도 포함 → 2022년 3월 최대 점령 범위 근사
g = union(선택 폴리곤 + 크림) .buffer(0.004).buffer(−0.004)     # 틈 메우기
g = g ∩ 우크라이나(크림 포함) ; simplify(0.004)
```
DeepState에는 정치적 성격의 폴리곤(카렐리야, 동프로이센 등)도 있다 → **우크라이나 경계로 클리핑**하면 자동 제거된다.

### 6.3 면적 검증 (반드시 수행)
```python
sinusoidal(g): x = lon*cos(lat)*111.32, y = lat*110.57    # 등적 투영
pct = area(g)/area(우크라이나) * 100
```
- 2022-10 이후: 17.9% → 19.3% (외부 집계 약 19%와 일치) → 사용.
- **2022-05~09: 7~10% → 점령 레이어 누락(형식 변경) → 사용 금지**, 해당 시기는 수작업 개략 경계(peak, apr22)로 대체하고 화면에 "개략" 표기.
- 쿠르스크(2024.8): DeepState에 없음 → `타원(35.28E, 51.2N, rx 0.36°, ry 0.21°) ∩ 러시아` 로 근사, "개략".

### 6.4 그리기 (`draw_occupied`)
```python
path(EVEN_ODD)
fill  #d7263d × 0.26a
hatch: 7×7 타일, 대각선 1.3px, 알파 0.55 — clip 후 paint
stroke 4px (#ff4d5e, 0.3a) + 1.4px (0.95a)
```

### 6.5 전선(front line) 추출 (v1)
`occupied.boundary ∩ 우크라이나.buffer(−0.03°)` → 국경·해안을 제외한 순수 전선만 남는다. 밝은 붉은 글로우로 강조.

### 6.6 타임랩스 (v1 7장)
- 월별 스냅숏 49개를 17초 무음 구간에 균등 배치(프레임당 약 0.33초), 각 0.3초 교차 페이드.
- 하단 카운터: 날짜(Black 34px) + "러시아 통제 {pct}%"(붉은색) + 진행 막대.
- **개선안**: 반투명 폴리곤 두 장의 교차 페이드는 겹친 부분 알파가 순간적으로 낮아진다. cairo `push_group()` → 이전 스냅숏(알파 1−f)과 다음 스냅숏(알파 f)을 `OPERATOR_ADD`로 합성 → `pop_group_to_source()` → `paint_with_alpha(0.45)`. 같은 색이면 겹침 부분이 정확히 1이 되어 깜빡임이 없다.

---

## 7. 폭발·타격 링 (`draw_boom`)
확산 링 3개(0.12초 간격), 반경 6→56(ease_out 1.2초), 호박색, 알파 0.6×(1−lt/1.6). 실제 타격 지점이 확인된 곳에만(v3: 하르그섬). 확인 안 된 지점에 폭발 효과를 넣지 않는다.

---

## 8. v1·v2 추가 오버레이 (이식용 명세)

| 타입 | 명세 | 용도 |
|---|---|---|
| `arrow` (v1) | 웨이포인트 곡선을 따라 굵은 화살표가 `grow`초 동안 성장, `retract` 시각 이후 역으로 줄어듦, `stop=True`면 끝에 저지선 | 침공 축, 반격 축 |
| `dots` (v1) | 점 여러 개가 stagger 간격으로 팝인, 펄스 | 병력 집결 |
| `movers` (v1) | 경로 위 점들이 일정 속도로 흐름 | 곡물 회랑, 선박 흐름 |
| `particles` (v1) | 한 지점 주변 무작위 입자(시드) | 군중(마이단) |
| `channel` (v2) | 두 도시 사이 점선 + 양방향으로 흐르는 빛점 6개 | 정보기관 채널 |
| `shield` (v2) | 도시 중심 반경(km) 원, 회전 점선, 일시정지 아이콘 | 타격 중단 요청 구역 |
| `flash` (v1) | 전체 화면 흰 번쩍임(알파 0.28, 0.5초) | 전면 침공 순간 |
| `line` (v1) | 점선/실선 경로 + 진행 드로잉 + 라벨 | 도피 경로, 크림대교 |

---

## 9. 국가 강조와 레이어 순서
`04` §8 참조. 렌더 순서(v3 `LAYER`): `country → ships → route → tanker_loop → barrier → boom → marker → badge`. 마커·뱃지가 RESERVED를 채운 뒤 라벨 LOD가 그려진다.
