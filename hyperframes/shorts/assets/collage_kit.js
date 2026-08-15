/**
 * collage_kit — 쇼츠 콜라주 L2 컴포넌트 (docs/17_COLLAGE_DESIGN_SHEET.md §2)
 *
 * 규약:
 *  - **결정론**: `Math.random()` / `Date.now()` 금지. 모든 흔들림은 시드+인덱스 파생.
 *  - **이원 이징** (§1.4): 물성 요소(컷아웃·소품·종이)=스텝/바운스,
 *    정보 요소(차트·라벨·자막)=Material decelerate. 섞지 않는다.
 *  - 컴포넌트는 DOM 을 만들고 **자기 등장 타임라인만** 돌려준다. 배치·시점은 씬이 정한다.
 *  - 토큰은 CSS 변수(`--paper-crumpled` 등)로만 읽는다 — 하드코딩 금지 (§0.3).
 */

(function (global) {
  "use strict";

  // ---------------------------------------------------------------- 결정론 유틸
  /** FNV-1a 32bit — Python 쪽 `schemas.models.fnv1a` 와 같은 알고리즘. */
  function fnv1a(str) {
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  /** 시드 파생 0..1 난수. 같은 (seed, key) 면 항상 같은 값. */
  function rnd(seed, key) {
    return (fnv1a(seed + ":" + key) % 100000) / 100000;
  }

  /** 시드 파생 범위값. */
  function rndRange(seed, key, lo, hi) {
    return lo + rnd(seed, key) * (hi - lo);
  }

  function tok(name, fallback) {
    const v = getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim();
    return v || fallback;
  }

  function num(name, fallback) {
    const v = parseFloat(tok(name, ""));
    return Number.isFinite(v) ? v : fallback;
  }

  function el(tag, cls, parent) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (parent) parent.appendChild(n);
    return n;
  }

  /**
   * HyperFrames `clip` 가시 구간 지정.
   *
   * **`data-duration` 은 "GSAP 로 등장해 있는 시간" 이 아니라 "이 DOM 이 존재해도
   * 되는 창" 이다.** 렌더러는 이 창 밖에서 요소를 숨긴다 — 씬 등장 시각에 맞춰
   * 좁게 잡으면 mp4 에서 통째로 사라진다 (실측 2026-08-15: 컷아웃·카드가 전부
   * 누락됐는데 Playwright 프리뷰는 clip 규약을 안 봐서 정상으로 보였다).
   *
   * 따라서 **기본은 컴포지션 전체 구간**이고, 실제 등장·퇴장은 GSAP opacity 가
   * 담당한다. 좁히는 건 자산을 늦게 로드시키고 싶을 때만.
   */
  function clipWindow(node, opt) {
    const total = (opt && opt.total) || window.__COMPOSITION_TOTAL__ || 0;
    node.dataset.start = (opt && opt.start) ?? 0;
    node.dataset.duration = (opt && opt.duration) ?? total;
    node.dataset.trackIndex = (opt && opt.track) ?? 1;
    return node;
  }

  // ---------------------------------------------------------------- 모션 상수
  const M = {
    get placeMs() { return num("--motion-place-ms", 220); },
    get placeFrom() { return num("--motion-place-from-scale", 1.06); },
    get stepFps() { return num("--motion-step-fps", 10); },
    get jitterDeg() { return num("--motion-jitter-deg", 0.3); },
    get drawOnMs() { return num("--motion-draw-on-ms", 400); },
    get staggerMs() { return num("--motion-stagger-ms", 120); },
    get pushFrom() { return num("--motion-push-in-from-scale", 1.0); },
    get pushTo() { return num("--motion-push-in-to-scale", 1.08); },
  };

  /** 물성 요소용 스텝 이징 — 스톱모션 질감 (§1.4). */
  function stepEase() {
    return "steps(" + Math.max(2, Math.round(M.stepFps * 0.25)) + ")";
  }

  /** 정보 요소용 Material decelerate (§1.4). 섞지 않는다. */
  const MATERIAL = "cubic-bezier(0,0,0.2,1)";

  // ================================================================ C 01 CutoutActor
  /**
   * 인물 컷아웃. 섀도는 빌드 타임에 이미 합성돼 있다(build_scene_assets.py).
   * 등장은 **하단에서**(bottom-in) place 이징, 이후 미세 지터 (§1.7).
   */
  function CutoutActor(parent, opt) {
    const wrap = el("div", "ca clip", parent);
    wrap.dataset.start = opt.start ?? 0;
    wrap.dataset.duration = opt.duration ?? 4;
    wrap.dataset.trackIndex = opt.track ?? 5;

    const img = el("img", "ca-img", wrap);
    img.src = opt.src;
    img.alt = "";

    wrap.style.left = opt.x + "px";
    wrap.style.bottom = opt.bottom + "px";
    wrap.style.width = opt.w + "px";

    const tilt = opt.tilt ?? 0;
    wrap.style.setProperty("--tilt", tilt + "deg");

    if (opt.tag) {
      const tag = el("div", "ca-tag", wrap);
      tag.textContent = opt.tag;
      if (opt.role) {
        const r = el("span", "ca-role", tag);
        r.textContent = opt.role;
      }
    }
    return wrap;
  }

  /**
   * CutoutActor 등장 타임라인. 단체는 stagger 120ms 순차 (§1.7).
   *
   * `hold` 는 지터를 몇 초간 돌릴지다. **`repeat: -1` 을 쓰면 안 된다** —
   * GSAP 타임라인 duration 이 무한(1e10초)이 되어 렌더러가 길이를 못 잡고
   * seek 도 어긋난다 (실측 2026-08-15).
   */
  function actorsIn(tl, nodes, at, seed, hold) {
    hold = hold || 6;
    nodes.forEach(function (n, i) {
      const t = at + (i * M.staggerMs) / 1000;
      tl.fromTo(
        n,
        { yPercent: 26, opacity: 0, scale: M.placeFrom },
        {
          yPercent: 0, opacity: 1, scale: 1,
          duration: M.placeMs / 1000,
          ease: stepEase(),
        },
        t
      );
      // 착지 후 미세 지터 — 시드 파생이라 매 렌더 동일 (§1.4).
      const j = M.jitterDeg;
      const cycle = 1.6 + rnd(seed, "jd" + i);
      tl.to(
        n,
        {
          rotation: "+=" + rndRange(seed, "jit" + i, -j, j).toFixed(3),
          duration: cycle,
          repeat: Math.max(1, Math.ceil(hold / cycle)),
          yoyo: true, ease: "sine.inOut",
        },
        t + M.placeMs / 1000
      );
    });
  }

  /**
   * 씬 퇴장 — 다음 씬이 시작할 때 이전 씬 요소를 물린다.
   * 이게 없으면 모든 씬이 화면에 쌓여 서로를 가린다 (실측 2026-08-15).
   */
  function sceneOut(tl, nodes, at) {
    const list = nodes.filter(Boolean);
    if (!list.length) return;
    tl.to(
      list,
      { opacity: 0, y: -18, duration: 0.34, ease: "power2.in", overwrite: "auto" },
      at
    );
  }

  // ================================================================ C 03 RansomHeadline
  /**
   * 오려붙인 헤드라인. **글자 단위**로 활자·기울기·배경을 바꾼다.
   * 시드는 문자열 해시 — 같은 문장이면 항상 같은 조합 (§1.3).
   */
  function RansomHeadline(parent, text, opt) {
    opt = opt || {};
    const seed = String(opt.seed ?? fnv1a(text));
    const wrap = el("div", "rh clip", parent);
    wrap.dataset.start = opt.start ?? 0;
    wrap.dataset.duration = opt.duration ?? 3;
    wrap.dataset.trackIndex = opt.track ?? 6;

    const FACES = ["rh-a", "rh-b", "rh-c", "rh-d"];
    const chars = [];
    Array.from(text).forEach(function (ch, i) {
      if (ch === " ") {
        el("span", "rh-sp", wrap);
        return;
      }
      const s = el("span", "rh-ch " + FACES[fnv1a(seed + ":f" + i) % FACES.length], wrap);
      s.textContent = ch;
      s.style.setProperty("--r", rndRange(seed, "r" + i, -4.5, 4.5).toFixed(2) + "deg");
      s.style.setProperty("--dy", rndRange(seed, "y" + i, -5, 5).toFixed(1) + "px");
      // 일부 글자만 강조 배경 (랜섬노트의 오린 종이 느낌)
      if (rnd(seed, "hl" + i) > 0.72) s.classList.add("rh-mark");
      chars.push(s);
    });
    return { root: wrap, chars: chars };
  }

  /** 글자 단위 stagger place (40ms) — §2 #3. */
  function ransomIn(tl, rh, at) {
    tl.fromTo(
      rh.chars,
      { opacity: 0, y: -22, scale: 1.14, rotation: 0 },
      {
        opacity: 1, y: 0, scale: 1,
        duration: 0.16, stagger: 0.04, ease: stepEase(),
      },
      at
    );
  }

  // ================================================================ C 04 StampLabel
  /** 검증 라벨 도장. 색·문구 변형 금지 (G4 / 07 §6). */
  const STAMPS = {
    confirm: { text: "<확인>", varName: "--stamp-confirm" },
    inferred: { text: "<추론>", varName: "--stamp-inferred" },
    unverified: { text: "<미검증>", varName: "--stamp-unverified" },
    refuted: { text: "<반박됨>", varName: "--stamp-refuted" },
  };

  function StampLabel(parent, kind, opt) {
    opt = opt || {};
    const spec = STAMPS[kind];
    if (!spec) throw new Error("unknown stamp: " + kind);
    const n = el("div", "stamp clip stamp-" + kind, parent);
    n.dataset.start = opt.start ?? 0;
    n.dataset.duration = opt.duration ?? 3;
    n.dataset.trackIndex = opt.track ?? 7;
    n.textContent = spec.text;
    n.style.color = tok(spec.varName, "#1C1A17");
    n.style.borderColor = tok(spec.varName, "#1C1A17");
    n.style.left = opt.x + "px";
    n.style.top = opt.y + "px";
    n.style.setProperty("--sr", (opt.rot ?? -5) + "deg");
    return n;
  }

  /** 도장 "쾅" — 1.3배에서 내리찍기 (§2 #4). */
  function stampIn(tl, node, at) {
    tl.fromTo(
      node,
      { opacity: 0, scale: 1.34 },
      { opacity: 1, scale: 1, duration: 0.14, ease: "power3.out" },
      at
    );
    tl.fromTo(
      node,
      { rotation: 0 },
      { rotation: parseFloat(node.style.getPropertyValue("--sr")) || -5,
        duration: 0.1, ease: "power2.out" },
      at
    );
  }

  // ================================================================ C 05 PaperPanel
  /** 종이 카드. place + 종이 숨쉬기. AI-대시보드 글로우 금지 (§2 #5). */
  function PaperPanel(parent, opt) {
    opt = opt || {};
    const n = el("div", "pp clip", parent);
    n.dataset.start = opt.start ?? 0;
    n.dataset.duration = opt.duration ?? 4;
    n.dataset.trackIndex = opt.track ?? 3;
    n.style.left = opt.x + "px";
    n.style.top = opt.y + "px";
    n.style.width = opt.w + "px";
    if (opt.h) n.style.height = opt.h + "px";
    n.style.setProperty("--pr", (opt.rot ?? 0) + "deg");
    if (opt.tone) n.style.background = tok("--" + opt.tone.replace(/_/g, "-"), "#F4EFE3");
    return n;
  }

  function panelIn(tl, node, at) {
    tl.fromTo(
      node,
      { opacity: 0, y: -30, scale: M.placeFrom },
      { opacity: 1, y: 0, scale: 1, duration: M.placeMs / 1000, ease: stepEase() },
      at
    );
  }

  // ================================================================ C 06 TapeStrip
  /** 테이프 조각. 씬당 3개 이하 (§2 #6). PaperPanel 등장에 종속. */
  function TapeStrip(parent, opt) {
    opt = opt || {};
    const n = el("div", "tape", parent);
    n.style.left = opt.x + "px";
    n.style.top = opt.y + "px";
    n.style.width = (opt.w ?? 150) + "px";
    n.style.setProperty("--tr", (opt.rot ?? -4) + "deg");
    return n;
  }

  // ================================================================ C 08 StringConnector
  /**
   * 붉은 실 관계선. draw-on (`getTotalLength` 패턴 — RENDER-AP v0.34.2 학습).
   * 관계 근거 없는 연결 금지 (G4) — 호출자가 번들 edge 를 근거로 전달해야 한다.
   */
  function StringConnector(svg, from, to, opt) {
    opt = opt || {};
    const seed = String(opt.seed ?? 0);
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    // 살짝 늘어진 실 — 중점을 아래로 당긴다
    const mx = (from.x + to.x) / 2;
    const my = (from.y + to.y) / 2 + rndRange(seed, "sag" + from.x + to.x, 18, 46);
    path.setAttribute("d", `M ${from.x} ${from.y} Q ${mx} ${my} ${to.x} ${to.y}`);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", opt.color || tok("--prop-string", "#B03A2E"));
    path.setAttribute("stroke-width", opt.width || 3);
    path.setAttribute("stroke-linecap", "round");
    svg.appendChild(path);
    // dasharray 를 inline 으로 명시 — getTotalLength 실패 시에도 안전
    const len = Math.hypot(to.x - from.x, to.y - from.y) * 1.5;
    path.style.strokeDasharray = len;
    path.style.strokeDashoffset = len;
    return path;
  }

  function drawOn(tl, nodes, at, stagger) {
    tl.to(
      nodes,
      {
        strokeDashoffset: 0,
        duration: M.drawOnMs / 1000,
        stagger: stagger ?? 0.09,
        ease: MATERIAL_GSAP,
      },
      at
    );
  }
  // GSAP 는 cubic-bezier 문자열을 직접 안 받으므로 CustomEase 대신 근사 사용.
  const MATERIAL_GSAP = "power2.out";

  // ================================================================ 자막 (대형)
  /**
   * 하단 대형 자막. 통문단이 아니라 **순차 표시** (C0).
   * 박스는 유지하고 텍스트만 swap — v0.34.2 학습.
   */
  function SubtitleBar(parent) {
    const bar = el("div", "sub-wrap", parent);
    const box = el("div", "sub-box", bar);
    return { root: bar, box: box };
  }

  /**
   * 자막 큐 — **큐마다 별도 DOM 을 만들어 opacity 로 교차**한다.
   *
   * `tl.call()` 로 textContent 를 갈아끼우면 안 된다: GSAP `seek()` 은 기본적으로
   * 콜백을 억제하므로(suppressEvents=true) 프레임 렌더러가 특정 시점으로 점프할 때
   * 자막이 첫 문장에 멈춘다 (실측 2026-08-15). 렌더러가 seek 을 쓰는지 우리가
   * 통제할 수 없으므로 **콜백에 의존하지 않는 구조**로 만든다.
   */
  function subtitleCues(tl, sub, cues) {
    if (!cues.length) return;
    const FADE = 0.18;
    cues.forEach(function (c, i) {
      const line = el("div", "sub-text", sub.box);
      line.textContent = c.text;
      line.style.opacity = "0";
      const next = cues[i + 1];
      tl.fromTo(line, { opacity: 0, y: 12 },
        { opacity: 1, y: 0, duration: FADE, ease: "power2.out", overwrite: "auto" },
        c.t);
      if (next) {
        tl.to(line, { opacity: 0, duration: FADE, ease: "power2.in", overwrite: "auto" },
          next.t - FADE);
      }
    });
  }

  // ================================================================ 카메라
  /** 증거판 위 슬로 푸시인 (§1.2). 씬 전체 컨테이너에 건다. */
  function pushIn(tl, node, at, dur) {
    tl.fromTo(
      node,
      { scale: M.pushFrom },
      { scale: M.pushTo, duration: dur, ease: "none" },
      at
    );
  }

  global.CollageKit = {
    fnv1a: fnv1a, rnd: rnd, rndRange: rndRange, tok: tok, num: num, el: el,
    M: M, stepEase: stepEase, MATERIAL: MATERIAL, clipWindow: clipWindow,
    CutoutActor: CutoutActor, actorsIn: actorsIn, sceneOut: sceneOut,
    RansomHeadline: RansomHeadline, ransomIn: ransomIn,
    StampLabel: StampLabel, stampIn: stampIn, STAMPS: STAMPS,
    PaperPanel: PaperPanel, panelIn: panelIn,
    TapeStrip: TapeStrip,
    StringConnector: StringConnector, drawOn: drawOn,
    SubtitleBar: SubtitleBar, subtitleCues: subtitleCues,
    pushIn: pushIn,
  };
})(window);
