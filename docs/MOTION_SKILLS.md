<!--
tier: 2
last_synced_with: v0.34.18
ssot_for: [motion-skills-internalization]
depends_on: [CLAUDE.md, hyperframes/lib/motion/hf-motion.js, hyperframes/CLAUDE.md]
last_review: 2026-06-07
-->

# 모션·타이포 스킬 내재화 — gsap-skills / taste-skill 흡수 (v0.34.18)

외부 두 오픈소스 스킬팩의 기술을 **HyperFrames 결정론적 영상 렌더에 맞게 골라 내재화**한
기록이다. 코드는 `hyperframes/lib/motion/hf-motion.js`(플러그인 없이 core gsap 만), 적용 예시는
`hyperframes/examples/motion_showcase.html`.

| 출처 | 라이선스 | 무엇 |
|---|---|---|
| [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | MIT | GSAP 8개 스킬(core/timeline/scrolltrigger/plugins/utils/react/perf/frameworks) |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | MIT | 디자인 취향(미니멀/럭셔리/브루탈) + 다이얼(VARIANCE/MOTION/DENSITY) |

> **방식**: 코드를 통째 복사하지 않고(라이선스·번들 위생), **기술·패턴을 자체 구현으로 흡수**.
> 핵심 판별 기준은 **"영상 렌더(헤드리스 Chrome seek 캡처)에서 작동하는가"**.

---

## 1. 영상 렌더 적합성 판별 (가장 중요)

우리 렌더는 **paused 타임라인을 seek 하며 프레임을 캡처**한다. 스크롤도 마우스도 없다.

| 기술 | 이식 | 비고 |
|---|---|---|
| Timeline / tween / 이징 / stagger | ✅ 코어 | 이미 사용 |
| **SplitText**(단어/글자 분해 stagger) | ✅ | `H.splitWords/splitChars/revealWords` 자체 구현 |
| **수치 count-up / ScrambleText** | ✅ | `H.countUp` (tl + onUpdate, seek 안전) |
| **크로스페이드/씬 전환** | ✅ | `H.crossfade` (opacity, "reveal 서사"를 타임라인 위치로 번역) |
| Flip / MorphSVG / MotionPath | ◐ 부분 | 타임라인 구동이면 가능(후속 — 지도 아크 등) |
| seeded random / clamp / lerp / mapRange | ✅ | `H.prng`(mulberry32) 등 — 결정론 필수와 정합 |
| **ScrollTrigger / Smoother / ScrollTo** | ❌ | **스크롤 기반 — 영상에 스크롤 없음**. 서사 패턴만 타임라인으로 번역 |
| Draggable / Inertia / Observer | ❌ | 라이브 상호작용 — 영상 무관 |

> **번역 원칙**: ScrollTrigger 의 "스크롤 진행도에 따라 단계적으로 드러내는 서사"는, 우리에선
> **타임라인 position(초)에 따라 단계적으로 드러내는 서사**로 그대로 옮긴다. 메커니즘만 빼고
> 스토리텔링은 흡수.

---

## 2. taste-skill 흡수 (디자인 원칙)

코드가 아니라 **원칙**을 우리 light-dashboard 토큰 위에 적용:

- **여백 규율**: 핵심 1줄 + 큰 여백(좌측 정렬 에디토리얼). "글자 도배" 금지(C0 와 동일).
- **타입 위계**: kicker(작고 자간 큰 대문자) → headline(900, 큰 letter-spacing 음수) → sub(600 muted).
- **단일 accent**: 한 화면 1 강조색(우리 오렌지 / 번들 theme.accent). 럭셔리는 절제에서 온다.
- **스프링/expo 모션**: 등장은 `expo.out`·`back.out`(묵직·고급), 변위는 `power.inOut`.
- **다이얼 개념**: MOTION_INTENSITY / VISUAL_DENSITY 를 우리 파라미터로 차용 가능(후속 — 씬별
  stagger·density 노브). 지금은 컴포넌트 기본값에 반영.
- (taste-skill 의 "em-dash 금지" 룰은 **우리는 채택 안 함** — 한국어 본문 `—` 사용은 우리 톤.)

---

## 3. 내재화 API (`hyperframes/lib/motion/hf-motion.js`)

```js
H.splitWords(el) / H.splitChars(el)        // 단어/글자 span 분리(스태거용)
H.revealWords(tl, el, at, {stagger,ease})  // rise+미세회전+opacity expo reveal 프리셋
H.countUp(tl, el, from, to, {at,duration,ease,format,prefix,suffix})  // 수치 카운트업
H.crossfade(tl, fromEl, toEl, at, {duration})  // 씬 전환(opacity)
H.prng(seed) / H.clamp / H.lerp / H.mapRange   // 결정론 유틸
```

모든 함수는 **paused 타임라인에 add** → seek 재생/결정론 보장. 플러그인 의존 없음.

---

## 4. 적용 / 검증

- 쇼케이스 `examples/motion_showcase.html`: SplitText 헤드라인 reveal + 0→21.7 count-up +
  A→B 크로스페이드 + 이징 다양성 + 에디토리얼 여백. mp4/PNG ground-truth 확인.
- **후속 내재화 지점**: ① 차트 컴포넌트 takeaway 를 revealWords 로, 도넛 중앙값·바 값을 countUp
  으로 ② compose-hyperframes 의 씬 사이에 crossfade 자동 삽입(지금 하드컷) ③ 지도 아크에
  MotionPath, 인물카드에 Flip.

---

본 문서는 외부 스킬을 **참고·번역**한 결과물이며, 원 저장소(MIT)에 귀속 표기한다. 우리 코드는
자체 구현이다.
