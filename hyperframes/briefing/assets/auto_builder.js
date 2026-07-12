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
  // 테마: 프리셋(themes.js) 우선, 그 위에 개별 변수 오버라이드
  if (window.SK_THEMES && D.themeId && window.SK_THEMES[D.themeId])
    for (const k in window.SK_THEMES[D.themeId].vars)
      document.documentElement.style.setProperty(k, window.SK_THEMES[D.themeId].vars[k]);
  if (D.themeVars)
    for (const k in D.themeVars) document.documentElement.style.setProperty(k, D.themeVars[k]);

  // 의미색 — 적용된 테마 변수에서 파생 (D.colors 로 강제 오버라이드 가능)
  const cssv = getComputedStyle(document.documentElement);
  const cv = (n, fb) => (cssv.getPropertyValue(n) || "").trim() || fb;
  const ACCENT = cv("--accent", "#c4a265");
  const OXIDE = cv("--oxide", "#b25450");
  const SAGE = cv("--sage", "#7d9b76");
  const SLATE = cv("--slate", "#8d99ae");
  const FAINT = cv("--faint", "#6e6a60");
  const COLORS = D.colors || {
    phase: { past: FAINT, crack: ACCENT, present: OXIDE, future: SLATE },
    gradStops: [["0", FAINT], ["0.62", OXIDE], ["1", SLATE]],
    market: { up: SAGE, down: OXIDE, vol: ACCENT, flat: SLATE },
    marketTag: { up: "상승", down: "하락", vol: "변동", flat: "보합" },
  };

  // ── 크롬 텍스트 ──
  const put = (id, text) => {
    const n = document.getElementById(id);
    if (n && text) n.textContent = text;
  };
  // 상단 브랜드 문구(OSINT BRIEFING / 리서치 브리핑)는 의미 없어 제거 (v0.45.2).
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

  // 타임라인 보조 캘린더 — 전 스텝이 완전한 날짜(YYYY.MM.DD)일 때만
  function attachCalendar(svg, sc, field) {
    const full = sc.data.steps.every((s) => /^\d{4}\.\d{2}\.\d{2}$/.test(s.date));
    if (!full) return null;
    const CAL = { x: 1404, y: 352, w: 348 };
    field.addRect(CAL.x - 12, CAL.y - 12, CAL.w + 24, 440);
    return { cal: SK.buildMiniCalendar(svg, sc.data.steps, { ...CAL, colors: COLORS.phase }), CAL };
  }
  function animateCalendar(cal, t0, stepGap) {
    if (!cal) return;
    tl.fromTo(cal.frame, { opacity: 0 }, { opacity: 1, duration: 0.5 }, t0 + 0.35);
    cal.months.forEach((m, mi) => {
      const at = t0 + 0.7 + m.firstIdx * stepGap - 0.05;
      if (mi === 0) {
        tl.fromTo(m.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, Math.max(t0 + 0.5, at));
      } else {
        tl.to(cal.months[mi - 1].g, { opacity: 0, duration: 0.3 }, at);
        tl.fromTo(m.g, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.45 }, at + 0.08);
      }
    });
  }

  // 타임라인 변형 공용 연출
  function pulsePresent(built, steps, at) {
    const pi = steps.findIndex((s) => s.phase === "present");
    if (pi >= 0)
      tl.fromTo(built.items[pi].marker, { scale: 1 },
        { scale: 1.35, transformOrigin: "50% 50%", duration: 0.5, yoyo: true, repeat: 1, ease: "sine.inOut" }, at);
  }
  function animateTimeline(built, sc, riserDur) {
    const t0 = sc.t0;
    sceneIn("#" + sc._secId, t0);
    headIn(document.getElementById(sc._secId), t0);
    if (built.riser) draw(built.riser, t0 + 0.4, riserDur, "power2.inOut");
    built.items.forEach((it, i) => {
      const at = t0 + 0.7 + i * 0.36;
      tl.to(it.marker, { opacity: 1, duration: 0.4, ease: "power2.out" }, at);
      tl.fromTo(it.marker, { scale: 0.4, transformOrigin: "50% 50%" },
        { scale: 1, duration: 0.5, ease: "back.out(2)" }, at);
      if (it.leader) draw(it.leader, at + 0.12, 0.3, "power1.out");
      tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, at + 0.22);
    });
    pulsePresent(built, sc.data.steps, t0 + 4.4);
    sceneOut("#" + sc._secId, sc.t1 - 0.5);
  }

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
      const field = SK.stageField();
      const calx = attachCalendar(svg, sc, field);
      const lad = SK.buildStepTimeline(svg, sc.data.steps, {
        x0: 250, x1: calx ? 1300 : 1640, yBottom: 778, yTop: 360,
        colors: COLORS.phase,
        gradId: "ladgrad-auto",
        gradStops: COLORS.gradStops,
        field,
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
      if (calx) animateCalendar(calx.cal, t0, 0.42);
      sceneOut(sec, sc.t1 - 0.5);
    },

    axis(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const field = SK.stageField();
      const calx = attachCalendar(svg, sc, field);
      const ax = SK.buildAxisTimeline(svg, sc.data.steps, {
        x0: 240, x1: calx ? 1310 : 1660, y: 586, colors: COLORS.phase, field,
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
      if (calx) animateCalendar(calx.cal, t0, 0.4);
      sceneOut(sec, sc.t1 - 0.5);
    },

    serpentine(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const sp = SK.buildSerpentineTimeline(svg, sc.data.steps, { colors: COLORS.phase });
      animateTimeline(sp, sc, 2.4);
    },

    vertical(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const vt = SK.buildVerticalTimeline(svg, sc.data.steps, { colors: COLORS.phase });
      animateTimeline(vt, sc, 2.0);
      vt.items.forEach((it, i) => {
        tl.to(it.dateEl, { opacity: 1, duration: 0.4 }, sc.t0 + 0.7 + i * 0.4);
      });
    },

    metro(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const mt = SK.buildMetroTimeline(svg, sc.data.steps, { colors: COLORS.phase });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      mt.segs.forEach((sg, i) => draw(sg, t0 + 0.5 + i * 0.28, 0.5, "power1.inOut"));
      mt.items.forEach((it, i) => {
        const at = t0 + 0.6 + i * 0.32;
        tl.to(it.marker, { opacity: 1, duration: 0.4, ease: "power2.out" }, at);
        tl.fromTo(it.marker, { scale: 0.4, transformOrigin: "50% 50%" },
          { scale: 1, duration: 0.5, ease: "back.out(2)" }, at);
        if (it.leader) draw(it.leader, at + 0.12, 0.3, "power1.out");
        tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, at + 0.22);
      });
      pulsePresent(mt, sc.data.steps, t0 + 4.4);
      sceneOut(sec, sc.t1 - 0.5);
    },

    slope(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const sl = SK.buildSlopeChart(svg, sc.data, { accent: ACCENT });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      sl.items.forEach((it, i) => {
        const at = t0 + 0.6 + i * 0.3;
        tl.fromTo(it.plates[0].g, { opacity: 0 }, { opacity: 1, duration: 0.4 }, at);
        tl.to(it.dots[0], { opacity: 1, duration: 0.25 }, at + 0.1);
        tl.to(it.line, { opacity: it.hi ? 1 : 0.7, duration: 0.2 }, at + 0.2);
        draw(it.line, at + 0.25, 0.8, "power2.inOut");
        tl.to(it.dots[1], { opacity: 1, duration: 0.25 }, at + 1.0);
        tl.fromTo(it.plates[1].g, { opacity: 0 }, { opacity: 1, duration: 0.4 }, at + 1.05);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    donut(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const dn = SK.buildDonut(svg, sc.data.items, {
        colors: [ACCENT, SLATE, SAGE, OXIDE, FAINT],
        centerLabel: sc.data.centerLabel,
        centerValue: sc.data.centerValue,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      dn.segs.forEach((sg, i) => {
        const at = t0 + 0.5 + i * 0.3;
        tl.to(sg.path, { opacity: 0.95, duration: 0.2 }, at);
        draw(sg.path, at, 0.9, "power2.inOut");
        if (sg.leader) draw(sg.leader, at + 0.7, 0.3, "power1.out");
        tl.fromTo(sg.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.4 }, at + 0.8);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    stacked(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const st = SK.buildStackedBars(svg, sc.data, {
        palette: [ACCENT, SLATE, SAGE, cv("--sienna", "#b07a4a"), OXIDE],
      });
      const lg = document.createElement("div");
      lg.className = "legend-row";
      st.segNames.forEach((n) => {
        const item = document.createElement("div");
        item.className = "item";
        const sw = document.createElement("div");
        sw.className = "swatch";
        sw.style.borderTopColor = st.colorOf(n);
        sw.style.borderTopStyle = "solid";
        item.appendChild(sw);
        const sp = document.createElement("span");
        sp.textContent = n;
        item.appendChild(sp);
        lg.appendChild(item);
      });
      sec.appendChild(lg);
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(lg, { opacity: 0, x: 20, duration: 0.5 }, t0 + 0.5);
      st.rows.forEach((row, ri) => {
        const at = t0 + 0.6 + ri * 0.55;
        row.segRects.forEach((seg, si) => {
          tl.to(seg, { opacity: 1, duration: 0.15 }, at + si * 0.32);
          tl.fromTo(seg, { scaleX: 0, svgOrigin: seg.dataset.ox + " 540" },
            { scaleX: 1, duration: 0.6, ease: "power2.out" }, at + si * 0.32);
        });
        tl.to(row.totalEl, { opacity: 1, duration: 0.4 }, at + row.segRects.length * 0.32 + 0.25);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    waterfall(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const wf = SK.buildWaterfall(svg, sc.data, { up: SAGE, down: OXIDE, accent: ACCENT });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      wf.cols.forEach((c, i) => {
        const at = t0 + 0.6 + i * 0.5;
        tl.to(c.g, { opacity: 1, duration: 0.4 }, at);
        tl.from(c.g, { y: 28, duration: 0.55, ease: "power3.out" }, at);
        if (c.conn) tl.to(c.conn, { opacity: 0.85, duration: 0.3 }, at + 0.42);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    sankey(sc, sec) {
      // 흐름 배분 — 소스 등장 → 깊이별 리본이 왼→오로 차오르고, 닿는 순간 행선지 점등
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const palette = [ACCENT, SLATE, SAGE, cv("--sienna", "#b07a4a"), OXIDE];
      const sk = SK.buildSankey(svg, sc.data, { accent: ACCENT, oxide: OXIDE, palette });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      if (sc.data.inferred) {
        const lg = document.createElement("div");
        lg.className = "legend-row";
        const tag = document.createElement("div");
        tag.className = "item";
        tag.style.color = OXIDE;
        tag.textContent = "흐름도 · 분석 추정";
        lg.appendChild(tag);
        sec.appendChild(lg);
        tl.from(lg, { opacity: 0, x: 20, duration: 0.5 }, t0 + 0.5);
      }
      // 깊이 0 노드 먼저
      sk.nodes.filter((nd) => nd.d === 0).forEach((nd) => {
        tl.to(nd.g, { opacity: 1, duration: 0.5 }, t0 + 0.55);
        tl.from(nd.g, { y: 16, duration: 0.55, ease: "power3.out" }, t0 + 0.55);
      });
      // 리본 — 소스 깊이별 스테이지, 스테이지 내 위→아래 스태거
      const STAGE = 2.0;
      const perStage = {};
      const arrival = {}; // 타깃 노드별 최초 도착 시각
      sk.links.forEach((lk) => {
        const k = (perStage[lk.sd] = (perStage[lk.sd] ?? -1) + 1);
        const at = t0 + 1.05 + lk.sd * STAGE + k * 0.26;
        tl.to(lk.path, { opacity: 0.42, duration: 0.25 }, at);
        draw(lk.path, at, 1.05, "power2.inOut");
        // 흐름 입자 — 리본을 따라 한 번 비행
        const head = SK.svgEl("circle", { r: 6, fill: "#f2e9d8", opacity: 0,
          filter: "drop-shadow(0 0 8px rgba(0,0,0,0.4))" }, svg);
        const fl = { p: 0 };
        tl.to(head, { opacity: 0.95, duration: 0.1 }, at + 0.08);
        tl.to(fl, { p: 1, duration: 1.0, ease: "power2.inOut",
          onUpdate: () => {
            const pt = lk.path.getPointAtLength(fl.p * lk.len);
            head.setAttribute("cx", pt.x);
            head.setAttribute("cy", pt.y);
          } }, at + 0.05);
        tl.to(head, { opacity: 0, duration: 0.25 }, at + 1.0);
        const arr = at + 0.95;
        if (!(lk.targetId in arrival) || arr < arrival[lk.targetId]) arrival[lk.targetId] = arr;
      });
      // 행선지 점등 — 첫 리본이 닿는 순간
      sk.nodes.filter((nd) => nd.d > 0).forEach((nd) => {
        const at = arrival[nd.id] ?? t0 + 1.9;
        tl.to(nd.g, { opacity: 1, duration: 0.45 }, at);
        tl.fromTo(nd.g, { scale: 0.94, transformOrigin: "0% 50%" },
          { scale: 1, duration: 0.5, ease: "back.out(1.8)" }, at);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    scatter(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const sct = SK.buildScatter(svg, sc.data, {
        accent: ACCENT, hiColor: OXIDE, diagonal: !!sc.data.diagonal,
      });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(sec.querySelector(".sct-axis"), { opacity: 0, duration: 0.6 }, t0 + 0.3);
      if (sct.diag) {
        tl.to(sct.diag, { opacity: 0.7, duration: 0.2 }, t0 + 0.7);
        draw(sct.diag, t0 + 0.75, 1.0, "power2.inOut");
      }
      sct.items.forEach((it, i) => {
        const at = t0 + 1.1 + i * 0.2;
        tl.to(it.g, { opacity: 1, duration: 0.3 }, at);
        tl.fromTo(it.g, { scale: 0.2, transformOrigin: "50% 50%" },
          { scale: 1, duration: 0.55, ease: "back.out(2.4)" }, at);
        if (it.plate) tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.35 }, at + 0.18);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    heatmap(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const hasNeg = sc.data.values.some((row) => row.some((v) => v < 0));
      const hm = SK.buildHeatmap(svg, sc.data, { pos: hasNeg ? SAGE : ACCENT, neg: OXIDE });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      // 대각 웨이브 리빌
      hm.cells.forEach((cell) => {
        tl.to(cell.g, { opacity: 1, duration: 0.45, ease: "power1.out" },
          t0 + 0.55 + (cell.ri + cell.ci) * 0.09);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    gantt(sc, sec) {
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const gn = SK.buildGantt(svg, sc.data, { colors: COLORS.phase, accent: ACCENT });
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      gn.bars.forEach((bar, i) => {
        const at = t0 + 0.6 + i * 0.4;
        tl.to(bar.lab, { opacity: 1, duration: 0.4 }, at);
        tl.to(bar.g, { opacity: 1, duration: 0.2 }, at + 0.1);
        tl.fromTo(bar.g, { scaleX: 0, svgOrigin: bar.g.dataset.ox + " 540" },
          { scaleX: 1, duration: 0.7, ease: "power2.out" }, at + 0.1);
        tl.to(bar.dt, { opacity: 1, duration: 0.35 }, at + 0.7);
      });
      if (gn.todayG) tl.to(gn.todayG, { opacity: 1, duration: 0.5 }, t0 + 0.5);
      sceneOut(sec, sc.t1 - 0.5);
    },

    statement(sc, sec) {
      // 서술 섹션 — 섹션 제목을 큰 편집형 히어로 스테이트먼트로 (v0.45.1).
      // 번호형 불릿 카드(구 video.highlights)는 AI 슬롭이라 폐기. 내레이션은 자막이 전달.
      const wrap = document.createElement("div");
      wrap.className = "stmt stmt-hero";
      const qm = document.createElement("div");
      qm.className = "stmt-qmark";
      qm.textContent = "\u201C";
      wrap.appendChild(qm);
      sec.appendChild(wrap);
      const rows = sc.data.lines.map((segs) => {
        const row = document.createElement("div");
        row.className = "stmt-hero-line";
        segs.forEach(([txt, em]) => {
          const sp = document.createElement(em ? "em" : "span");
          sp.textContent = txt;
          row.appendChild(sp);
        });
        wrap.appendChild(row);
        return row;
      });
      const t0 = sc.t0;
      const span = (sc.t1 - sc.t0 - 3.0) / Math.max(1, rows.length);
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(qm, { opacity: 0, scale: 0.6, transformOrigin: "left top", duration: 0.9 }, t0 + 0.3);
      rows.forEach((row, i) => {
        const at = t0 + 0.8 + i * span;
        tl.from(row, { opacity: 0, y: 34, duration: 0.9, ease: "power3.out" }, at);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    geo(sc, sec) {
      // 사건의 좌표 — 권역 베이스맵 + 마커/아크 (계약 map 필드)
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const bm = window.SK_MAPS && window.SK_MAPS[sc.data.region];
      const KINDC = { flow: ACCENT, subject: OXIDE, ally: SAGE, rival: SLATE };
      const M = {};
      sc.data.markers.forEach((m) => (M[m.id] = m));
      const arcs = sc.data.arcs.map((a) => {
        const A = M[a.from];
        const B = M[a.to];
        const dist = Math.hypot(B.x - A.x, B.y - A.y);
        return { ...a, bend: Math.min(170, Math.max(54, dist * 0.22)),
                 color: KINDC[a.kind] || ACCENT,
                 dash: a.kind === "flow" ? "" : "7 8",
                 glow: a.kind === "flow" ? "rgba(0,0,0,0)" : undefined,
                 cls: a.kind === "flow" ? "main-arc" : "sec-arc" };
      });
      const built = SK.buildGeoScene(svg,
        { regions: bm ? bm.labels : [], markers: sc.data.markers, arcs },
        { basemap: bm, hiColor: OXIDE });
      // 범례 + 분석 추정 태그
      const lg = document.createElement("div");
      lg.className = "legend-row";
      (sc.data.legend || []).forEach((item) => {
        const el = document.createElement("div");
        el.className = "item";
        const sw = document.createElement("div");
        sw.className = "swatch";
        sw.style.borderTopColor = KINDC[item.kind] || FAINT;
        sw.style.borderTopStyle = "solid";
        el.appendChild(sw);
        const sp = document.createElement("span");
        sp.textContent = item.label;
        el.appendChild(sp);
        lg.appendChild(el);
      });
      if (sc.data.inferred) {
        const tag = document.createElement("div");
        tag.className = "item";
        tag.style.color = OXIDE;
        tag.textContent = "관계도 · 분석 추정";
        lg.appendChild(tag);
      }
      sec.appendChild(lg);
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      if (built.basemap) tl.from(built.basemap, { opacity: 0, duration: 1.0, ease: "power2.out" }, t0 + 0.15);
      tl.from(lg, { opacity: 0, x: 20, duration: 0.5 }, t0 + 0.6);
      built.markerItems.forEach((it, i) => {
        const at = t0 + 0.7 + i * 0.3;
        tl.to(it.g, { opacity: 1, duration: 0.5, ease: "power2.out" }, at);
        if (it.leader) draw(it.leader, at + 0.1, 0.25, "power1.out");
        tl.fromTo(it.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.4 }, at + 0.18);
      });
      built.arcs.forEach((ac, i) => {
        const at = t0 + 2.4 + i * 0.8;
        tl.to(ac.path, { opacity: ac.kind === "flow" ? 1 : 0.75, duration: 0.2 }, at);
        tl.to(ac.path, { strokeDashoffset: 0, duration: 1.2, ease: "power1.inOut",
          onComplete: () => { if (ac.path.dataset.dash) ac.path.setAttribute("stroke-dasharray", ac.path.dataset.dash); } }, at);
        if (ac.kind === "flow") {
          // 흐름 헤드 — 아크를 따라 한 번 비행
          const head = SK.svgEl("circle", { r: 7, fill: "#f2e9d8", opacity: 0,
            filter: "drop-shadow(0 0 8px rgba(0,0,0,0.4))" }, svg);
          const fl = { p: 0 };
          tl.to(head, { opacity: 1, duration: 0.1 }, at + 0.05);
          tl.to(fl, { p: 1, duration: 1.25, ease: "power1.inOut",
            onUpdate: () => {
              const pt = SK.quadAt(ac.a, ac.c, ac.b, fl.p);
              head.setAttribute("cx", pt.x);
              head.setAttribute("cy", pt.y);
            } }, at + 0.05);
          tl.to(head, { opacity: 0, scale: 2, transformOrigin: "50% 50%", duration: 0.35 }, at + 1.3);
        }
      });
      built.arcLabels.forEach((al, i) => {
        tl.fromTo(al.plate.g, { opacity: 0 }, { opacity: 1, duration: 0.5 }, t0 + 3.4 + i * 0.8);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    globe(sc, sec) {
      // 르포 지구본 — d3 정사영(orthographic) + 자전 + 대권 호 흐름 + 마커 펄스 +
      // 당사국 역할 색조 (reportage_globe_mockup 대응). 결정론: 애니메이션은 GSAP
      // 타임라인 시간(elapsed)의 순수 함수 — d3.timer(벽시계) 미사용, 프레임 seek 안전.
      const d3 = window.d3, topojson = window.topojson, world = window.WORLD_110M;
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const S = d3.select(svg);
      const land = topojson.feature(world, world.objects.countries);
      const borders = topojson.mesh(world, world.objects.countries, (a, b) => a !== b);

      const CX = 1250, CY = 566, R = 452;
      const cardC = cv("--surface", "#1d1d21"), bgC = cv("--bg0", "#121214");
      const lineC = cv("--hairline", "rgba(236,233,226,0.16)");
      const softC = cv("--hairline-soft", "rgba(236,233,226,0.08)");
      const mutedC = cv("--muted", "#a39e92"), textC = cv("--text", "#ece9e2");
      // 육지색 — 배경(bg0)과 글씨(text) 사이를 살짝 블렌드해 다크·라이트 모두 대비 확보.
      const hx = (c) => { const m = /#?([0-9a-f]{6})/i.exec(c || ""); if (!m) return [18, 18, 20]; const n = parseInt(m[1], 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; };
      const blend = (a, b, t) => { const A = hx(a), B = hx(b); return "#" + [0, 1, 2].map((i) => Math.round(A[i] * (1 - t) + B[i] * t).toString(16).padStart(2, "0")).join(""); };
      const landC = blend(bgC, textC, 0.14);

      const mk = sc.data.markers || [];
      const arcs = sc.data.arcs || [];
      const byId = {}; mk.forEach((m) => (byId[m.id] = m));
      let clon = 0, clat = 0;
      if (mk.length) {
        clon = mk.reduce((s, m) => s + m.lng, 0) / mk.length;
        clat = mk.reduce((s, m) => s + m.lat, 0) / mk.length;
      }
      const baseLat = Math.max(-52, Math.min(52, clat));
      const proj = d3.geoOrthographic().scale(R).translate([CX, CY]).clipAngle(90).rotate([-clon, -baseLat]);
      const path = d3.geoPath(proj);
      const arcColor = (a) => (a.kind === "tension" || a.kind === "rival" || a.kind === "conflict" ? OXIDE : ACCENT);

      // 역할 색조 — 하이라이트 마커가 위치한 국가 = 당사국 (init 1회 계산)
      const roleName = {};
      mk.forEach((m) => {
        if (!m.hi) return;
        const f = land.features.find((ft) => d3.geoContains(ft, [m.lng, m.lat]));
        if (f) roleName[f.properties.name] = ACCENT;
      });

      const sphere = S.append("path").datum({ type: "Sphere" }).attr("fill", cardC).attr("stroke", lineC).attr("stroke-width", 1.2);
      const grat = S.append("path").datum(d3.geoGraticule10()).attr("fill", "none").attr("stroke", softC).attr("stroke-width", 0.6);
      const landP = S.append("path").datum(land).attr("fill", landC).attr("stroke", lineC).attr("stroke-width", 0.5);
      const roleG = S.append("g");
      const bord = S.append("path").datum(borders).attr("fill", "none").attr("stroke", lineC).attr("stroke-width", 0.6);
      const arcG = S.append("g");
      const markG = S.append("g");
      const labelG = S.append("g");

      function renderGlobe(elapsed) {
        const drift = 16 * Math.sin(elapsed * 0.16); // ±16° 완만한 자전 (마커 시야 유지)
        proj.rotate([-clon + drift, -baseLat]);
        sphere.attr("d", path); grat.attr("d", path); landP.attr("d", path); bord.attr("d", path);
        roleG.selectAll("path").data(land.features).join("path").attr("d", path)
          .attr("fill", (d) => roleName[d.properties.name] || "none")
          .attr("fill-opacity", (d) => (roleName[d.properties.name] ? 0.45 : 0)).attr("stroke", "none");
        const rot = proj.rotate(); const center = [-rot[0], -rot[1]];
        arcG.selectAll("path").data(arcs).join("path")
          .attr("d", (a) => { const A = byId[a.from], B = byId[a.to]; return A && B ? path({ type: "LineString", coordinates: [[A.lng, A.lat], [B.lng, B.lat]] }) : null; })
          .attr("fill", "none").attr("stroke", arcColor).attr("stroke-width", 2.4)
          .attr("stroke-linecap", "round").attr("stroke-dasharray", "3 9")
          .attr("stroke-dashoffset", -elapsed * 26).attr("opacity", 0.95);
        const pr = 8 + 5 * Math.abs(Math.sin(elapsed * 1.7));
        markG.selectAll("g.mk").data(mk).join((en) => {
          const g = en.append("g").attr("class", "mk");
          g.append("circle").attr("class", "ring"); g.append("circle").attr("class", "dot"); return g;
        }).each(function (m) {
          const vis = d3.geoDistance([m.lng, m.lat], center) < Math.PI / 2;
          const p = proj([m.lng, m.lat]); const g = d3.select(this);
          if (!vis || !p) { g.attr("opacity", 0); return; }
          g.attr("opacity", 1);
          g.select(".ring").attr("cx", p[0]).attr("cy", p[1]).attr("r", m.hi ? pr : 5)
            .attr("fill", "none").attr("stroke", m.hi ? ACCENT : mutedC).attr("stroke-width", 1.8).attr("opacity", m.hi ? 0.9 : 0.55);
          g.select(".dot").attr("cx", p[0]).attr("cy", p[1]).attr("r", m.hi ? 4.5 : 2.8)
            .attr("fill", m.hi ? ACCENT : mutedC).attr("stroke", "none");
        });
        const labeled = mk.filter((m) => m.hi && m.name).slice(0, 4);
        labelG.selectAll("text").data(labeled).join("text").each(function (m) {
          const vis = d3.geoDistance([m.lng, m.lat], center) < Math.PI / 2;
          const p = proj([m.lng, m.lat]); const t = d3.select(this);
          if (!vis || !p) { t.attr("opacity", 0); return; }
          const rightSide = p[0] > 1540;  // 오른쪽 가장자리 마커는 라벨을 왼쪽으로 (화면 밖 방지)
          t.attr("opacity", 1).attr("x", rightSide ? p[0] - 16 : p[0] + 16).attr("y", p[1] + 7)
            .attr("text-anchor", rightSide ? "end" : "start").text(m.name)
            .attr("fill", textC).attr("font-size", 27).attr("font-weight", 700)
            .attr("font-family", "'GmarketSans', 'Noto Sans KR', sans-serif")
            .attr("paint-order", "stroke").attr("stroke", bgC).attr("stroke-width", 5).attr("stroke-linejoin", "round");
        });
      }

      const lg = document.createElement("div");
      lg.className = "legend-row";
      (sc.data.legend || []).forEach((item) => {
        const el = document.createElement("div"); el.className = "item";
        const sw = document.createElement("div"); sw.className = "swatch";
        sw.style.borderTopColor = (item.kind === "tension" || item.kind === "rival") ? OXIDE : ACCENT;
        sw.style.borderTopStyle = "solid"; el.appendChild(sw);
        const sp = document.createElement("span"); sp.textContent = item.label; el.appendChild(sp); lg.appendChild(el);
      });
      if (sc.data.inferred) {
        const tag = document.createElement("div"); tag.className = "item";
        tag.style.color = OXIDE; tag.textContent = "지도 · 분석 추정"; lg.appendChild(tag);
      }
      sec.appendChild(lg);

      renderGlobe(0);
      const t0 = sc.t0, dur = sc.t1 - sc.t0;
      sceneIn(sec, t0); headIn(sec, t0);
      tl.from(svg, { opacity: 0, duration: 1.0, ease: "power2.out" }, t0 + 0.1);
      tl.from(lg, { opacity: 0, x: 20, duration: 0.5 }, t0 + 0.6);
      // 결정론 자전/흐름/펄스 — elapsed 를 타임라인 시간으로 구동 (seek 안전)
      const st = { e: 0 };
      tl.to(st, { e: dur, duration: dur, ease: "none", onUpdate: () => renderGlobe(st.e) }, t0);
      sceneOut(sec, sc.t1 - 0.5);
    },

    geonet(sc, sec) {
      // 관계망 (network 차트) — 중심+원형 배치, 국기 노드, 하이브리드 라우팅/흐름 펄스 재사용
      const svg = SK.svgEl("svg", { viewBox: "0 0 1920 1080", style: "position:absolute; inset:0;" });
      sec.appendChild(svg);
      const LC = { 대립: OXIDE, 동맹: SAGE, 협상: ACCENT, 영향: FAINT };
      const LD = { 대립: "2 12", 협상: "9 11", 영향: "1 10" };
      const palette = [ACCENT, SLATE, SAGE, cv("--sienna", "#b07a4a"), OXIDE, FAINT, "#9aa3b2", "#cdc9bf"];
      const net = SK.buildNetwork(svg, sc.data.nodes, sc.data.links, {
        linkColors: LC, dashByType: LD,
        nodeColor: (nd) => (nd.kind === "center" ? ACCENT : palette[(sc.data.nodes.indexOf(nd)) % palette.length]),
        nodeR: 60,
      });
      const lg = document.createElement("div");
      lg.className = "legend-row";
      [...new Set(sc.data.links.map((l) => l.type))].forEach((k2) => {
        const el = document.createElement("div");
        el.className = "item";
        const sw = document.createElement("div");
        sw.className = "swatch";
        sw.style.borderTopColor = LC[k2] || FAINT;
        sw.style.borderTopStyle = LD[k2] ? "dashed" : "solid";
        el.appendChild(sw);
        const sp = document.createElement("span");
        sp.textContent = k2;
        el.appendChild(sp);
        lg.appendChild(el);
      });
      sec.appendChild(lg);
      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(lg, { opacity: 0, x: 20, duration: 0.5 }, t0 + 0.5);
      tl.to(sec.querySelectorAll(".net-node"), { opacity: 1, duration: 0.6, stagger: 0.12, ease: "power2.out" }, t0 + 0.6);
      tl.fromTo(sec.querySelectorAll(".net-node"), { scale: 0.6, transformOrigin: "50% 50%" },
        { scale: 1, duration: 0.6, stagger: 0.12, ease: "back.out(1.7)" }, t0 + 0.6);
      net.plates.forEach((pl, i) => {
        tl.fromTo(pl.g, { opacity: 0 }, { opacity: 1, duration: 0.45 }, t0 + 1.0 + i * 0.1);
      });
      tl.to(sec.querySelectorAll(".net-link"), { opacity: 0.95, duration: 0.3, stagger: 0.08 }, t0 + 1.8);
      tl.to(sec.querySelectorAll(".net-link"), { strokeDashoffset: 0, duration: 0.9, stagger: 0.08, ease: "power2.out",
        onComplete: function () {
          net.linkEls.forEach((ln) => { if (ln.dataset.dash) ln.setAttribute("stroke-dasharray", ln.dataset.dash); });
        } }, t0 + 1.9);
      net.flows.forEach((fl, i) => {
        const L = parseFloat(fl.dataset.len);
        const seg = parseFloat(fl.dataset.seg);
        const at = t0 + 3.6 + i * 0.18;
        tl.to(fl, { opacity: 0.9, duration: 0.4 }, at);
        tl.fromTo(fl, { strokeDashoffset: L + seg }, { strokeDashoffset: 0, duration: 2.4, ease: "none", repeat: 1 }, at);
        tl.to(fl, { opacity: 0, duration: 0.4 }, at + 4.6);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    quote(sc, sec) {
      const d = sc.data;
      sec.innerHTML +=
        `<div class="iquote">` +
        `<div class="iq-rule"></div>` +
        `<div class="iq-text"></div>` +
        `<div class="iq-src">${d.source || ""}</div>` +
        `</div>`;
      const chs = SK.splitChars(sec.querySelector(".iq-text"), d.segments);
      const t0 = sc.t0;
      sceneIn(sec, t0);
      tl.fromTo(sec.querySelector(".iq-rule"), { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: "power4.out" }, t0 + 0.3);
      tl.from(chs, { opacity: 0, y: 16, duration: 0.7, stagger: 0.014, ease: "power3.out" }, t0 + 0.5);
      tl.from(sec.querySelector(".iq-src"), { opacity: 0, duration: 0.6 }, t0 + 1.8);
      sceneOut(sec, sc.t1 - 0.5);
    },

    bars(sc, sec) {
      const wrap = document.createElement("div");
      sec.appendChild(wrap);
      const panels = SK.buildBarPanels(wrap, sc.data.panels, { accent: ACCENT });
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
        up: SAGE,
        down: OXIDE,
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
        colorByKind: COLORS.market,
        tagByKind: COLORS.marketTag,
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

    // 표 (비교표·매핑표) — 헤더 등장 후 행 순차 stagger, 강조 행은 accent 바/배경.
    // "정적 표를 박는 것"(C0 금지)이 아니라 읽기 흐름이 있는 영상용 표.
    // 셀 선두 기호로 의미색 자동: ✓●→sage / ✗✘✕→oxide / ○→faint.
    table(sc, sec) {
      const d = sc.data;
      const cols = d.columns || [];
      const rows = d.rows || [];
      const nCols = cols.length, nRows = rows.length;

      // 안전 밴드: 헤드(top 150, 제목 54px → ~290) 아래 ~ 자막바(bottom 96 → ~884)/scrim(y850) 위.
      // 표를 이 밴드 안에 가두고 행 높이를 행 수에 맞춰 자동 축소 → 자막 침범 방지.
      const TOP = 300, BOTTOM = 812;
      const availH = BOTTOM - TOP;
      const headerH = 56;
      let rowH = Math.max(34, Math.min(76, (availH - headerH) / Math.max(1, nRows)));
      let cellFont = nCols <= 3 ? 32 : nCols === 4 ? 27 : 23;
      cellFont = Math.max(17, Math.min(cellFont, Math.floor(rowH * 0.5)));
      const headFont = Math.max(16, cellFont - 3);
      const padH = nCols >= 5 ? 12 : 18;
      const containerH = headerH + nRows * rowH;
      const top = Math.round(TOP + Math.max(0, (availH - containerH) / 2));
      const gridCols = cols.map((c) => Math.max(0.4, c.weight || 1) + "fr").join(" ");

      const tone = (v) => {
        const s = (v || "").trim();
        if (s[0] === "✓" || s[0] === "●") return SAGE;
        if (s[0] === "✗" || s[0] === "✘" || s[0] === "✕") return OXIDE;
        if (s[0] === "○") return FAINT;
        return "var(--text)";
      };
      const rgba = (hex, a) => {
        const h = (hex || "").replace("#", "");
        if (h.length < 6) return "rgba(196,162,101," + a + ")";
        const n = parseInt(h.slice(0, 6), 16);
        return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
      };

      const wrap = document.createElement("div");
      wrap.style.cssText = "position:absolute; left:96px; right:96px; top:" + top + "px;";

      const hd = document.createElement("div");
      hd.style.cssText = "display:grid; grid-template-columns:" + gridCols +
        "; align-items:end; height:" + headerH + "px; padding-bottom:12px; box-sizing:border-box;" +
        " border-bottom:2px solid " + rgba(ACCENT, 0.5) + ";";
      cols.forEach((c) => {
        const cell = document.createElement("div");
        cell.textContent = c.label || "";
        cell.style.cssText = "font-weight:700; font-size:" + headFont + "px; line-height:1.2; color:" +
          (c.accent || "var(--muted)") + "; text-align:" + (c.align || "left") +
          "; padding:0 " + padH + "px; letter-spacing:.3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";
        hd.appendChild(cell);
      });
      wrap.appendChild(hd);

      const rowEls = [], barEls = [];
      rows.forEach((r) => {
        const row = document.createElement("div");
        row.style.cssText = "position:relative; display:grid; grid-template-columns:" + gridCols +
          "; align-items:center; height:" + rowH + "px; box-sizing:border-box; overflow:hidden;" +
          " border-bottom:1px solid var(--hairline-soft, rgba(255,255,255,0.06));" +
          (r.highlight ? "background:" + rgba(ACCENT, 0.1) + ";" : "");
        if (r.highlight) {
          const bar = document.createElement("div");
          bar.style.cssText = "position:absolute; left:0; top:0; bottom:0; width:4px; background:" + ACCENT + ";";
          row.appendChild(bar);
          barEls.push(bar);
        }
        cols.forEach((c, ci) => {
          const v = ((r.cells || {})[c.key]) || "";
          const cell = document.createElement("div");
          cell.textContent = v;
          cell.style.cssText = "font-weight:" + (ci === 0 ? 600 : 400) + "; font-size:" + cellFont +
            "px; line-height:1.25; color:" + tone(v) + "; text-align:" + (c.align || "left") +
            "; padding:0 " + padH + "px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";
          row.appendChild(cell);
        });
        wrap.appendChild(row);
        rowEls.push(row);
      });
      sec.appendChild(wrap);

      const t0 = sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      tl.from(hd, { opacity: 0, y: 14, duration: 0.55, ease: "power3.out" }, t0 + 0.4);
      rowEls.forEach((row, i) => {
        tl.from(row, { opacity: 0, y: 18, duration: 0.5, ease: "power3.out" }, t0 + 0.65 + i * 0.11);
      });
      barEls.forEach((bar) => {
        tl.fromTo(bar, { scaleY: 0, transformOrigin: "50% 50%" },
          { scaleY: 1, duration: 0.5, ease: "power2.out" }, t0 + 1.0);
      });
      sceneOut(sec, sc.t1 - 0.5);
    },

    // 보도 사진 (IMAGE_BUNDLE_CONTRACT) — 풀블리드 + Ken Burns + 스크림 위 takeaway.
    // rights 게이트는 변환기(fetch_photos)가 통과시킨 cleared 사진만 여기 도달한다.
    photo(sc, sec) {
      const d = sc.data;
      const originMap = { center: "50% 50%", top: "50% 22%", bottom: "50% 78%",
                          left: "28% 50%", right: "72% 50%" };
      const origin = originMap[d.focus] || originMap.center;

      const box = document.createElement("div");
      box.style.cssText = "position:absolute; inset:0; overflow:hidden;";
      const img = document.createElement("img");
      img.src = d.src;
      img.alt = d.caption || "";
      img.style.cssText = "width:100%; height:100%; object-fit:cover; display:block;" +
        " transform-origin:" + origin + ";";
      box.appendChild(img);
      // 스크림 — 상단(헤드 가독) + 하단(문장·자막 가독)
      const scrimTop = document.createElement("div");
      scrimTop.style.cssText = "position:absolute; left:0; right:0; top:0; height:340px;" +
        " background:linear-gradient(180deg, rgba(10,12,16,0.78) 0%, rgba(10,12,16,0) 100%);";
      const scrimBot = document.createElement("div");
      scrimBot.style.cssText = "position:absolute; left:0; right:0; bottom:0; height:460px;" +
        " background:linear-gradient(0deg, rgba(10,12,16,0.85) 0%, rgba(10,12,16,0) 100%);";
      box.appendChild(scrimTop);
      box.appendChild(scrimBot);
      sec.appendChild(box);

      // takeaway 오버레이 (statement lines 재사용 — em 은 accent)
      const lines = d.lines || [];
      const lwrap = document.createElement("div");
      lwrap.style.cssText = "position:absolute; left:96px; bottom:250px; width:1180px;";
      const rows = lines.map((segs, i) => {
        const row = document.createElement("div");
        row.style.cssText = "font-size:38px; font-weight:700; line-height:1.4;" +
          " color:#f4f6f9; margin-top:" + (i ? 14 : 0) + "px;" +
          " text-shadow:0 2px 14px rgba(0,0,0,0.55);";
        segs.forEach(([txt, em]) => {
          const sp = document.createElement("span");
          sp.textContent = txt;
          if (em) sp.style.color = ACCENT;
          row.appendChild(sp);
        });
        lwrap.appendChild(row);
        return row;
      });
      sec.appendChild(lwrap);

      // 캡션 + 크레딧 (우하단, 자막 영역 오른쪽 여백)
      const cred = document.createElement("div");
      cred.style.cssText = "position:absolute; right:96px; bottom:118px; text-align:right;" +
        " font-size:15px; line-height:1.6; color:rgba(244,246,249,0.75);" +
        " text-shadow:0 1px 6px rgba(0,0,0,0.5);";
      cred.innerHTML = (d.caption ? d.caption + "<br/>" : "") +
        (d.credit ? "사진 · " + d.credit : "");
      sec.appendChild(cred);

      const t0 = sc.t0, dur = sc.t1 - sc.t0;
      sceneIn(sec, t0);
      headIn(sec, t0);
      // Ken Burns — 씬 전체 길이 동안 천천히 (결정론, ease 없는 선형에 가깝게)
      tl.fromTo(img, { scale: 1.12 }, { scale: 1.02, duration: dur, ease: "none" }, t0);
      tl.from(box, { opacity: 0, duration: 0.9, ease: "power2.out" }, t0);
      rows.forEach((row, i) => {
        tl.from(row, { opacity: 0, y: 22, duration: 0.7, ease: "power3.out" },
          t0 + 1.0 + i * 0.5);
      });
      tl.from(cred, { opacity: 0, duration: 0.6 }, t0 + 1.2);
      sceneOut(sec, sc.t1 - 0.5);
    },
  };

  // ── 씬 조립 ──
  const sections = [];
  D.scenes.forEach((sc, i) => {
    const sec = sceneShell(sc, i);
    sc._secId = sec.id;
    sections.push(sec);
    gsap.set(sec, { autoAlpha: 0 });
    chip(sc.t0, sc.chip);
    // 방어적 격리 — 한 씬 빌더가 실패해도 나머지 영상·타임라인은 살린다 (v0.46.0).
    try { BUILDERS[sc.type](sc, sec); }
    catch (e) { console.error("[auto_builder] scene '" + sc.type + "' 빌드 실패:", e); }
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
  // 긴 문장(>62자)은 폰트를 줄여 자막 2줄 유지 (계약 한도 75자 대응)
  const applyCap = (c) => {
    cap.textContent = c.text;
    cap.style.fontSize = c.text.length > 62 ? "33px" : "";
  };
  D.cues.forEach((c, i) => {
    if (i === 0) {
      tl.call(() => { applyCap(c); }, [], c.t - 0.1);
      tl.fromTo(subwrap, { autoAlpha: 0, x: -20 }, { autoAlpha: 1, x: 0, duration: 0.55, overwrite: "auto" }, c.t);
    } else {
      tl.to(subwrap, { autoAlpha: 0, x: -16, duration: 0.25, overwrite: "auto" }, c.t - 0.3);
      tl.call(() => { applyCap(c); }, [], c.t - 0.05);
      tl.fromTo(subwrap, { x: 16 }, { autoAlpha: 1, x: 0, duration: 0.3, overwrite: "auto" }, c.t);
    }
  });

  window.__timelines[root.dataset.compositionId] = tl;
})();
