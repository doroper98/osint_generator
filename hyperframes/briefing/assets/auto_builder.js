/* auto_builder — 번들 주도 제네릭 브리핑 컴포지션 빌더 (v0.36.0, 옵션 C 1차)
 *
 * window.BRIEFING_DATA(변환기 bundle_to_video.py 가 생성)를 읽어 씬을 조건부로
 * 조립한다. 데이터에 있는 씬만 만들어진다 — 지도가 없으면 지도 씬이 없다.
 *
 * DATA 스키마:
 *   meta:   { brand, sub, date, sourceLine1, sourceLine2 }
 *   themeVars: { "--accent": "#..", ... }   // 번들 테마 토큰 → CSS 변수 오버라이드
 *   colors: { phase:{past,crack,present,future}, gradStops:[[off,color]..],
 *             market:{up,down,vol,flat}, marketTag:{...} }
 *   total:  영상 총 길이(초) — root data-duration 에 주입
 *   scenes: [{ type:"title"|"ladder"|"versus"|"markets"|"closing",
 *              t0, t1, no, chip, head?{kicker,title}, data:{...} }]
 *   cues:   [{ t, text }]
 *
 * 계약: window.__timelines[<root data-composition-id>] 등록, 결정론.
 */
(function () {
  "use strict";
  const SK = window.SceneKit;
  const D = window.BRIEFING_DATA;
  const root = document.getElementById("root");

  // ── 총 길이/테마 주입 (hyperframes 가 attribute 를 읽기 전, 빌드 시점) ──
  root.setAttribute("data-duration", String(D.total));
  if (D.themeVars)
    for (const k in D.themeVars) document.documentElement.style.setProperty(k, D.themeVars[k]);

  // ── 크롬 텍스트 ──
  const put = (id, text) => {
    const n = document.getElementById(id);
    if (n && text) n.textContent = text;
  };
  put("brand-name", D.meta.brand);
  put("brand-sub", D.meta.sub);
  put("top-date", D.meta.date);
  put("source-line1", D.meta.sourceLine1);
  const src2 = document.getElementById("source-line2");
  if (src2) src2.innerHTML = D.meta.sourceLine2 || "";

  const stage = document.getElementById("stage");

  // ── 씬 골격 생성 ──
  function sceneShell(sc, idx) {
    const sec = document.createElement("section");
    sec.className = "scene";
    sec.id = "sc" + idx;
    if (sc.head) {
      const head = document.createElement("div");
      head.className = "scene-head";
      head.innerHTML =
        `<div class="kicker">${sc.head.kicker}</div>` +
        `<div class="scene-title">${sc.head.title}</div>`;
      sec.appendChild(head);
    }
    if (sc.no) {
      const no = document.createElement("div");
      no.className = "scene-no";
      no.textContent = sc.no;
      sec.appendChild(no);
    }
    stage.appendChild(sec);
    return sec;
  }

  // ── 마스터 타임라인 ──
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });
  const TOTAL = D.total;

  tl.fromTo("#prog", { scaleX: 0 }, { scaleX: 1, duration: TOTAL, ease: "none" }, 0);
  tl.fromTo("#stage", { scale: 1.0 }, { scale: 1.025, duration: TOTAL, ease: "none" }, 0);

  const sceneIn = (sel, t) =>
    tl.fromTo(sel, { autoAlpha: 0, y: 26, scale: 0.992 },
      { autoAlpha: 1, y: 0, scale: 1, duration: 0.85, ease: "power3.out" }, t);
  const sceneOut = (sel, t) =>
    tl.to(sel, { autoAlpha: 0, y: -18, duration: 0.6, ease: "power2.in" }, t);
  const chip = (t, label) =>
    tl.call(() => { document.getElementById("scene-label").textContent = label; }, [], t);
  const draw = (el, at, dur, ease) =>
    tl.to(el, { strokeDashoffset: 0, duration: dur, ease: ease || "power2.out" }, at);
  const headIn = (sec, t) => {
    const h = sec.querySelector(".scene-head");
    if (h) tl.from(h, { opacity: 0, y: 18, duration: 0.7 }, t + 0.1);
  };

  // ── 씬 타입별 빌더 + 연출 ──
  const BUILDERS = {
    title(sc, sec) {
      const d = sc.data;
      sec.innerHTML +=
        `<div class="watermark">${(d.watermark || "").replace(/\n/g, "<br/>")}</div>` +
        `<div style="position:absolute; top:300px; left:96px; right:96px;">` +
        `<div class="s1-kicker"></div><div class="s1-rule"></div>` +
        `<div class="headline"></div><div class="deck"></div></div>`;
      sec.querySelector(".s1-kicker").textContent = d.kicker;
      sec.querySelector(".deck").textContent = d.deck;
      const chs = SK.splitChars(sec.querySelector(".headline"), d.lines);
      const t0 = sc.t0;
      sceneIn(sec, t0);
      tl.from(sec.querySelector(".s1-kicker"), { opacity: 0, y: 16, duration: 0.7 }, t0 + 0.3);
      tl.fromTo(sec.querySelector(".s1-rule"), { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "power4.out" }, t0 + 0.6);
      tl.from(chs, { yPercent: 115, opacity: 0, duration: 0.9, stagger: 0.02, ease: "power4.out" }, t0 + 0.8);
      tl.from(sec.querySelector(".deck"), { opacity: 0, y: 20, duration: 0.9 }, t0 + 1.9);
      sceneOut(sec, sc.t1 - 0.5);
    },

    ladder(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const lad = SK.buildStepTimeline(svg, sc.data.steps, {
        x0: 250, x1: 1640, yBottom: 778, yTop: 360,
        colors: D.colors.phase,
        gradId: "ladgrad-auto",
        gradStops: D.colors.gradStops,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      draw(lad.riser, t0 + 0.5, 3.0, "power2.inOut");
      lad.items.forEach((it, i) => {
        const at = t0 + 0.8 + i * 0.42;
        tl.to(it.marker, { opacity: 1, duration: 0.4, ease: "power2.out" }, at);
        tl.fromTo(it.marker, { scale: 0.4, transformOrigin: "50% 50%" },
          { scale: 1, duration: 0.5, ease: "back.out(2)" }, at);
        if (it.leader) draw(it.leader, at + 0.12, 0.3, "power1.out");
        tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, at + 0.22);
      });
      const pi = sc.data.steps.findIndex((s) => s.phase === "present");
      if (pi >= 0)
        tl.fromTo(lad.items[pi].marker, { scale: 1 },
          { scale: 1.35, transformOrigin: "50% 50%", duration: 0.5, yoyo: true, repeat: 1, ease: "sine.inOut" },
          t0 + 4.6);
      sceneOut(sec, sc.t1 - 0.5);
    },

    axis(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const ax = SK.buildAxisTimeline(svg, sc.data.steps, {
        x0: 240, x1: 1660, y: 586, colors: D.colors.phase,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      draw(ax.riser, t0 + 0.4, 1.6, "power2.inOut");
      ax.items.forEach((it, i) => {
        const at = t0 + 0.7 + i * 0.4;
        tl.to(it.marker, { opacity: 1, duration: 0.4, ease: "power2.out" }, at);
        tl.fromTo(it.marker, { scale: 0.4, transformOrigin: "50% 50%" },
          { scale: 1, duration: 0.5, ease: "back.out(2)" }, at);
        if (it.leader) draw(it.leader, at + 0.12, 0.3, "power1.out");
        tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, at + 0.22);
      });
      const pi = sc.data.steps.findIndex((s) => s.phase === "present");
      if (pi >= 0)
        tl.fromTo(ax.items[pi].marker, { scale: 1 },
          { scale: 1.35, transformOrigin: "50% 50%", duration: 0.5, yoyo: true, repeat: 1, ease: "sine.inOut" },
          t0 + 4.4);
      sceneOut(sec, sc.t1 - 0.5);
    },

    bars(sc, sec) {
      const wrap = document.createElement("div");
      sec.appendChild(wrap);
      const panels = SK.buildBarPanels(wrap, sc.data.panels, { accent: D.themeVars["--accent"] });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      panels.forEach((pn, pi) => {
        tl.from(pn.card, { opacity: 0, y: 40, duration: 0.7, ease: "power3.out" }, t0 + 0.5 + pi * 0.3);
        pn.rows.forEach((row, ri) => {
          const at = t0 + 0.9 + pi * 0.3 + ri * 0.22;
          tl.fromTo(row.fill, { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "power3.out" }, at);
          SK.counter(tl, row.valEl, row.value,
            (v) => (Number.isInteger(row.value) ? Math.round(v).toLocaleString("ko-KR") : v.toFixed(1)) + row.unit,
            at, 0.9);
        });
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    candle(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const ch = SK.buildCandleChart(svg, sc.data.ohlc, {
        x0: 180, x1: 1640, y0: 320, y1: 820,
        up: D.themeVars["--sage"] || "#7d9b76",
        down: D.themeVars["--oxide"] || "#b25450",
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.to(ch.candles, { opacity: 1, duration: 0.25, stagger: 0.022, ease: "power1.out" }, t0 + 0.5);
      tl.fromTo(ch.candles, { y: 14 }, { y: 0, duration: 0.4, stagger: 0.022, ease: "power2.out" }, t0 + 0.5);
      tl.to(ch.lastLine, { opacity: 0.85, duration: 0.5 }, t0 + 2.4);
      tl.fromTo(ch.lastPlate.g, { opacity: 0 }, { opacity: 1, duration: 0.5 }, t0 + 2.5);
      sceneOut(sec, sc.t1 - 0.5);
    },

    signals(sc, sec) {
      const items = sc.data.items;
      const cw = 318;
      const gap = 26;
      const total = items.length * cw + (items.length - 1) * gap;
      const startX = (1920 - total) / 2;
      const cards = items.map((it, i) => {
        const card = document.createElement("div");
        card.className = "sigcard";
        card.style.left = (startX + i * (cw + gap)) + "px";
        card.innerHTML =
          `<span class="sg-when">${it.when}</span>` +
          `<div class="sg-name">${it.name}</div>` +
          `<div class="sg-desc">${it.desc}</div>` +
          (it.unverified ? `<div class="sg-tag">&lt;미검증&gt; 관측 대기</div>` : "");
        sec.appendChild(card);
        return card;
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      cards.forEach((c, i) => {
        tl.from(c, { opacity: 0, y: 44, duration: 0.65, ease: "power3.out" }, t0 + 0.5 + i * 0.18);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    versus(sc, sec) {
      const wrap = document.createElement("div");
      sec.appendChild(wrap);
      const cards = SK.buildProfileCards(wrap, sc.data.cards, {
        cardW: sc.data.cards.length <= 2 ? 560 : 390,
        gap: 64,
        gauge: sc.data.axis,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      cards.forEach((p, i) => {
        const at = t0 + 0.6 + i * 0.4;
        tl.from(p.card, { opacity: 0, y: 44, duration: 0.7, ease: "power3.out" }, at);
        draw(p.ring, at + 0.25, 1.0, "power2.inOut");
        tl.from(p.lineEl, { opacity: 0, y: 12, duration: 0.5 }, at + 0.45);
        tl.fromTo(p.dot, { x: 0.5 * (560 - 68), opacity: 0 },
          { x: p.dotX, opacity: 1, duration: 0.9, ease: "power3.inOut" }, at + 1.0);
        tl.from(p.stanceEl, { opacity: 0, duration: 0.45 }, at + 1.6);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    markets(sc, sec) {
      const wrap = document.createElement("div");
      sec.appendChild(wrap);
      const cards = SK.buildMarketCards(wrap, sc.data.markets, {
        colorByKind: D.colors.market,
        tagByKind: D.colors.marketTag,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      cards.forEach((m, i) => {
        const at = t0 + 0.6 + i * 0.35;
        tl.from(m.card, { opacity: 0, y: 40, duration: 0.7, ease: "power3.out" }, at);
        tl.to(m.area, { opacity: 1, duration: 0.8 }, at + 0.3);
        draw(m.line, at + 0.2, 1.3);
        tl.to(m.end, { opacity: 1, duration: 0.3 }, at + 1.3);
        SK.counter(tl, m.pctEl, m.data.pct,
          (v) => (v >= 0 ? "+" : "") + v.toFixed(1) + "%", at + 0.3, 1.2);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    closing(sc, sec) {
      const d = sc.data;
      sec.innerHTML +=
        `<div class="quote"></div><div class="closing"></div>` +
        `<div class="confbox"><div class="clabel">신뢰도</div>` +
        `<div class="cscore">0.00</div>` +
        `<div class="ctrack"><div class="cfill"></div></div>` +
        `<div class="cdesc"></div></div>`;
      const quoteChs = SK.splitChars(sec.querySelector(".quote"), d.quote);
      sec.querySelector(".closing").textContent = d.closing;
      sec.querySelector(".cdesc").textContent = d.confidence.desc;
      const fill = sec.querySelector(".cfill");
      fill.style.width = Math.round(d.confidence.score * 100) + "%";
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(quoteChs, { opacity: 0, y: 18, duration: 0.7, stagger: 0.012, ease: "power3.out" }, t0 + 0.4);
      tl.from(sec.querySelector(".closing"), { opacity: 0, y: 20, duration: 0.8 }, t0 + 1.6);
      tl.from(sec.querySelector(".confbox"), { opacity: 0, x: 30, duration: 0.7 }, t0 + 1.2);
      SK.counter(tl, sec.querySelector(".cscore"), d.confidence.score,
        (v) => v.toFixed(2), t0 + 1.6, 1.2, "power2.out");
      tl.fromTo(fill, { scaleX: 0 }, { scaleX: 1, duration: 1.2, ease: "power3.out" }, t0 + 1.6);
    },
  };

  // ── 씬 조립 ──
  const sections = [];
  D.scenes.forEach((sc, i) => {
    const sec = sceneShell(sc, i);
    sections.push(sec);
    gsap.set(sec, { autoAlpha: 0 });
    chip(sc.t0, sc.chip);
    BUILDERS[sc.type](sc, sec);
  });

  // pulse-ring (씬 빌드 후 존재 확정) — 시킹 안전 반복
  if (document.querySelector(".pulse-ring"))
    tl.to(".pulse-ring", { scale: 2.2, opacity: 0, duration: 1.5,
      repeat: Math.max(1, Math.floor(TOTAL / 1.5) - 2), ease: "sine.out",
      transformOrigin: "50% 50%" }, 0);

  // ── 자막 ──
  const cap = document.getElementById("cap");
  const subwrap = document.querySelector(".subwrap");
  gsap.set(subwrap, { autoAlpha: 0 });
  D.cues.forEach((c, i) => {
    if (i === 0) {
      tl.call(() => { cap.textContent = c.text; }, [], c.t - 0.1);
      tl.fromTo(subwrap, { autoAlpha: 0, x: -20 }, { autoAlpha: 1, x: 0, duration: 0.55, overwrite: "auto" }, c.t);
    } else {
      tl.to(subwrap, { autoAlpha: 0, x: -16, duration: 0.25, overwrite: "auto" }, c.t - 0.3);
      tl.call(() => { cap.textContent = c.text; }, [], c.t - 0.05);
      tl.fromTo(subwrap, { x: 16 }, { autoAlpha: 1, x: 0, duration: 0.3, overwrite: "auto" }, c.t);
    }
  });

  window.__timelines[root.dataset.compositionId] = tl;
})();
