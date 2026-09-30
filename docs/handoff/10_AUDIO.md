<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v2-audio-mix]
depends_on: [docs/handoff/00_INDEX.md, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-29
origin: claude.ai chat handoff bundle (2026-09-26 ~ 09-27), imported verbatim
-->

# 10. 오디오 — 내레이션 · 음악 · 효과음 · 믹스

참조 코드: `v3/mix3.py` (정본), `v2/mix2.py`, `v1/music.py` (절차 합성 음악)

---

## 1. 신호 흐름

```
내레이션 npy (문장별, 트림됨) ──► 피크 0.8 정규화 ──► t0에 배치 ─────────────┐
                                                                            ├─► 합산 × 전체 페이드 ─► 피크 0.97 리밋 ─► mix.f32
BGM(CC BY) ─► 저음 보강(§3.4, v4.6.0) ─► 정규화 ─► × 강도곡선 × (1 − 0.5·duck) × 0.47 ──────────────────┤
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

### 3.4 v4.6.0 저음 보강 (사용자 결정 D86, back_and_forth D-0097·D-0102)

사용자 지시: "배경음악에 베이스를 좀 더 풍부하게 넣어서 좀 웅장한 느낌이 드는 배경음악이 깔리도록 해."
곡을 따라가는 처리만 한다. 조성을 모르는 곡에 고정 근음 드론을 깔지 않고, 새 곡·절차 합성도 쓰지 않는다. 수치는 전부 `rules audio.bed_bass` 다.

```python
bg = 디코드 → 루프 → 자르기                         # 곡 교체면 곡마다(자기 시간축)
pre = max|bg|
y = low_shelf(bg, 110Hz, +5dB, q 0.7)              # RBJ 쿡북 biquad, lfilter
m = y 모노합; band = bandpass(m, 55–220Hz)
sq = 상승 영교차마다 부호 토글(2분주 사각파) → lowpass 110Hz   # 곡 저음의 한 옥타브 아래
sub = sq × 포락선(band 블록 RMS×√2, attack 0.03s·release 0.25s) × 0.35 × 스웰
스웰 = 장면 시작(첫 장면 제외)에서 1.35 → 2.5초 동안 선형으로 1
y += sub(양 채널)
bg = y / (pre^(1−k) × max|y|^k)                   # k = norm_ref 0.8(D-0102)
이후 bed_gain 0.47 × 강도 × (1 − 0.5·duck) 는 v3 그대로
```

**정규화 기준(norm_ref)이 핵심이다.** 처리 뒤 피크로 정규화하면(k = 1) 서브 층이 키운 피크만큼 베드 전체가 내려간다.
그러면 저역 절대 레벨은 그대로이고 중역만 약 5.7 dB 내려가 "묵직"이 아니라 "어두움"이 된다. 처리 전 피크 기준(k = 0)은 저역이 약 +5.5 dB 오르지만 음악 레벨이 −7.5 dB 가 되어 v3 합격 범위 [−15, −11] 를 벗어난다.
k 는 두 편(hormuz·fed_policy) 모두 기존 오디오 QA hard 를 통과하는 최소값으로 정했다(0.1 단위 실측, `reports/phaseG6/norm_ref_sweep.jsonl`·`tp_sweep.jsonl`).
음악 레벨이 범위 안에 0.3 dB 이상 여유를 두려면 0.7 이상, 최종 트루 피크(loudnorm 2패스 + AAC)가 −1.5 + 0.15 dBTP 안에 들려면 0.8 이상이다(0.7 은 hormuz −1.34). 그래서 0.8 — 저역 절대 +0.8 dB, 중역 −4.5 dB 다.
즉 bed_gain·음악 레벨 범위·트루 피크 여유를 지키는 한 이것이 저역을 올릴 수 있는 한계다. 더 웅장하게 하려면 음악 레벨 범위 자체를 사용자 청감으로 다시 정해야 한다.

> **구현 메모(v4.11.0, back_and_forth D-0118 §2 — 음악 상한 +2 dB, 사용자 위임 D103)**: 위 마지막 문장의 "범위 자체"를 옮겼다.
> `rules:audio.qa.music_under_narration_db` [−15, −11] → **[−13, −9]**(v3 값에서 2 dB 위). `norm_ref` 는 같은 절차(0.3 dB 여유 최소값, `tools/norm_ref_sweep.py`,
> `reports/phaseG10/norm_ref_sweep.jsonl`)로 **0.4**(0.3 = hormuz −9.26 여유 밖, 0.4 = hormuz −9.83·fed −10.57). 음악 +1.7 dB, 베드 저역 비율 상승폭은 그대로(5.35).
> 트루 피크는 post_limiter(−2.0 dBFS, RENDER-AP-004)가 맡는다. 다른 오디오 값(post_limiter·TP·bed_bass)은 무변경. 원복은 두 줄(범위·norm_ref 0.7).

**측정 정의(audio/qa.py, `out/bed_stats.json`)**: 베드(내레이션·효과음 제외) 모노의 30–120 Hz 대역 RMS − 200–2000 Hz 대역 RMS(dB, rfft 파워 합).
믹서가 처리 전·후 두 값을 남기고, 판정은 **상승폭**(후 − 전)이 `audio.qa.bed_bass_rise_db` [4, 8] 안인지다(hard).
절대 비율은 곡마다 달라 기록만 한다. zabriskie_patriarch 는 60–120 Hz 패드가 강해 처리 전부터 +11.8 dB 다(D-0097 의 절대 범위 [−6, 0] 은 도달 불가로 폐기, D-0102).
서브 층 잡음성 실측: 서브 에너지의 90% 가 원곡 대역 피크의 절반 주파수 ±2 Hz 에 모인다(평탄도 0.06, 110 Hz 위 누설 −26 dB). 화음 구간에서도 잡음으로 번지지 않았다.

무음악(`sound.bgm: null`) 경로는 처리·측정을 거치지 않는다(`bed_stats.json` 도 쓰지 않는다). 이득을 0 으로 두면(셸프 0 dB·서브 0) hormuz mix 가 v3 합격본 md5 `c1314fb9` 와 바이트 단위로 같다.
되돌리기: v4.6.0 G6 커밋 revert, 또는 `shelf.gain_db: 0`·`sub.gain: 0`.

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
