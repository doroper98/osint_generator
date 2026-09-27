<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-audio-mix]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 10. 오디오 — 내레이션 · 음악 · 효과음 · 믹스

참조 코드: `v3/mix3.py` (정본), `v2/mix2.py`, `v1/music.py` (절차 합성 음악)

---

## 1. 신호 흐름

```
내레이션 npy (문장별, 트림됨) ──► 피크 0.8 정규화 ──► t0에 배치 ─────────────┐
                                                                            ├─► 합산 × 전체 페이드 ─► 피크 0.97 리밋 ─► mix.f32
BGM(CC BY) ─► 정규화 ─► × 강도곡선 × (1 − 0.5·duck) × 0.47 ──────────────────┤
효과음(whoosh/boom/tick) ─► × (1 − 0.25·duck) ─────────────────────────────┘
                                                             ffmpeg: loudnorm I=-14 TP=-1.5 LRA=11 → AAC 192k
```
샘플레이트 44.1kHz, 스테레오 float32 raw(`mix.f32`), 길이 = plan.total + 0.5초.

---

## 2. 내레이션 배치와 더킹

```python
for 문장 x:
    a = np.load(x.npy); a = a / max|a| * 0.8
    vo[t0 : t0+len] += a
    duck[(t0 − 0.25) : (t1 + 0.3)] = 1          # 말 시작 0.25초 전부터 끝 0.3초 뒤까지
duck = convolve(duck, box(0.35초))               # 부드러운 램프
```

---

## 3. 배경음악 (베드)

### 3.1 소스
저장소 `hyperframes/briefing/assets/audio/bgm/The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3` (YouTube 오디오 보관함, **CC BY 4.0**, 931초). 출처 표기 의무: 영상 엔딩 + 유튜브 설명란("Music: … — Chris Zabriskie (CC BY 4.0)").
같은 폴더 RIGHTS.md에 미사용 CC BY 곡 2개(Take Off and Shoot a Zero, Drone in D)가 더 있다.

### 3.2 처리
```python
bg = ffmpeg 디코드(f32le, 2ch, 44.1k)
길이가 모자라면 4초 교차 페이드로 루프
bg /= max|bg|
강도 곡선(장면 시작 시각 키프레임, 선형 보간):
  v3: open 0.6 → route 0.62 → war 0.74 → ask 0.6 → timeline 0.66 → cost 0.7 → review 0.6 → past 0.55
      → debate 0.66 → decision 0.72 → now 0.66 → (끝 −7초) 0.62 → 끝 0
bed_gain = 강도 × (1 − 0.5·duck) × 0.47
```

### 3.3 볼륨 결정 이력 (지적 10)
| 버전 | 기본 이득 | 더킹 | 내레이션 중 실효 | 사용자 반응 |
|---|---|---|---|---|
| v2 | 0.33 | 60% 감쇠 | 0.13×강도 | "너무너무 작다" |
| v3 | 0.47 | 50% 감쇠 | 0.235×강도 | 합격 |

최종 먹싱에서 loudnorm이 전체를 −14 LUFS로 맞추므로, 여기서 조정하는 것은 **음악과 내레이션의 상대 비율**이다.

---

## 4. 효과음 합성식

```python
def whoosh(t_end, dur=1.2, v=1.0):             # 장면 전환 직전 상승음
    n = dur*SR; ti = 시간축; nz = 가우시안 잡음
    a = clip(ti/dur, 0, 1)**2.2                # 점점 커짐
    lp = lfilter([0.08], [1, −0.92], nz)       # 저역
    hp = nz − lfilter([0.3], [1, −0.7], nz)    # 고역
    y = (lp*(1−a)*0.6 + hp*a*0.25) * a * exp(−max(0, ti − dur + 0.08)/0.05)   # 끝에서 급감쇠
    배치: t_end − dur, 이득 0.2×v

def boom(t, v=1.0):                            # 저역 충격
    f = 34 + 44*exp(−ti/0.25)                  # 78Hz → 34Hz 하강 스윕
    y = sin(2π·cumsum(f)/SR)*exp(−ti/0.8)*0.55 + lfilter([0.02],[1,−0.98], 잡음)*exp(−ti/0.3)*0.6
    길이 2.6초, 이득 v

def tick(t, v=1.0):                            # 체크리스트 등
    y = sin(2π·1800·ti)*exp(−ti/0.015)*0.18    # 0.12초
```
v3 배치: 타이틀 카드(whoosh 1.4초 + boom 0.6), 각 장면 시작(whoosh 0.9초, 0.55), 하르그섬 타격(boom 0.5). v2: 모스크바 도착·루블린 미사일 boom, 체크리스트 tick 4회.

원칙: 효과음은 **실제 사건**(타격, 도착)과 **구조 전환**(장면 시작)에만. 장식용 효과음 남발 금지.

---

## 5. 마무리

```python
fade: 시작 1.2초 인, 끝 4초 아웃
L = (bg_L*bed_gain + fx*(1 − 0.25·duck) + vo) * fade;  R 동일
pk = max(|L|,|R|); if pk > 0.97: 전체 /= pk/0.97
np.stack([L,R],1).astype(float32).tofile('mix.f32')
```

먹싱:
```bash
ffmpeg -i video.mp4 -f f32le -ar 44100 -ac 2 -i mix.f32 -map 0:v -map 1:a -c:v copy \
       -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 44100 -c:a aac -b:a 192k -t {total} -movflags +faststart out.mp4
```
유튜브 기준 −14 LUFS, 트루피크 −1.5dBTP.

---

## 6. 절차 합성 음악 (v1 — 라이선스 곡이 없을 때의 폴백)

`v1/music.py` 요약:
- 조성 D단조, 코드 진행 `Dm Bb F C | Dm Bb Gm A`, 코드당 8초, 2.5초 교차 페이드.
- 패드: 코드 구성음 4개 × 배음 6개(진폭 1/n^1.7, 느린 LFO), 좌우 ±0.12% 디튠 → 코러스감. 강도가 높을수록 4배음 이상 강조.
- 서브 베이스: 근음 사인 + 2·3배음.
- 긴장 구간(강도 > 0.5): 8분음표(0.375초) 오스티나토, 강도 > 0.68이면 0.75초 간격 킥(48Hz+40Hz 스윕).
- 평온 구간(강도 < 0.5): 2옥타브 위 벨(2.76배 비조화 배음, 1.1초 감쇠).
- 리버브: 2.8초 지수 감쇠 잡음 IR, `scipy.signal.oaconvolve`(메모리 절약), wet 0.55.
- 장 카드: whoosh + boom, 전면 침공 순간 강한 boom.
평가: 기능적으로는 충분했지만 음악적 완성도는 라이선스 곡이 낫다. 기본값은 CC BY 곡 + 강도 자동화, 절차 합성은 폴백.

---

## 7. Claude Code 개선 과제
1. BGM 레지스트리(`assets/audio/bgm/registry.json`: 파일, 라이선스, 표기 문구, 분위기 태그, BPM, 길이).
2. 강도 곡선을 원고 장면에 `music_intensity` 필드로 지정 가능하게.
3. 곡 교체 시 장면 경계에 맞춘 교차 페이드.
4. ElevenLabs 전환 후 문장 간 음량 편차 확인(문장별 RMS 정규화 옵션).
5. 오디오 QA: 내레이션 구간 음악 레벨이 내레이션 대비 −14~−18dB 범위인지 측정.
