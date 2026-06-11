/* SceneKit — OSINT 브리핑 컴포지션 공용 엔진 (v0.35.0)
 *
 * 목적: "라벨이 서로 겹치고, 글자가 연결선 위에 얹히는" 사고의 구조적 차단.
 * ZE 브랜치(v0.34.13)의 일회성 하드코딩 레이아웃을 데이터 주도 빌더 + 충돌 회피
 * 배치기로 리팩토링한 엔진 레이어.
 *
 * 구성:
 *  - LAYOUT      : 1920x1080 안전영역 밴드 (헤더 / 스테이지 / 자막)
 *  - estTextWidth: 결정론적 텍스트 폭 추정 (폰트 로드 타이밍 무관 → 시킹 렌더 안전)
 *  - LabelField  : 장애물 등록(선분/곡선/원/사각) + 후보 슬롯 + 밀어내기 탐색
 *  - plateLabel  : 반투명 플레이트 + 멀티라인 SVG 라벨 (자동 줄바꿈)
 *  - leader      : 마커 ↔ 플레이트 리더선
 *  - prepDraw    : getTotalLength 기반 draw-on 준비 (하드코딩 dasharray 제거)
 *  - buildStepTimeline / buildBasemap / buildNetwork(지오 앵커·국기 노드) /
 *    buildGeoScene(실측 베이스맵) / buildMarketCards / buildProfileCards
 *
 * 규약 (HyperFrames 계약):
 *  - 결정론만 허용 — Date.now() / Math.random() / fetch 금지.
 *  - GSAP 타임라인은 호출측(index.html)이 소유. 본 엔진은 DOM 빌드 + 기하만 담당.
 */
(function () {
  "use strict";

  const SVGNS = "http://www.w3.org/2000/svg";
  const W = 1920;
  const H = 1080;

  const LAYOUT = {
    W: W,
    H: H,
    marginX: 96,
    headTop: 150, // scene-head(kicker+title) 시작 y
    stageTop: 268, // 씬 콘텐츠 상한 (scene-head 아래)
    stageBottom: 866, // 씬 콘텐츠 하한 (자막 밴드 위)
    sceneNo: { x: 1650, y: 150, w: 194, h: 134 }, // 우상단 씬 번호 장식 영역
  };

  function svgEl(tag, attrs = {}, parent = null) {
    const n = document.createElementNS(SVGNS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  // ── 결정론적 텍스트 폭 추정 (em 단위 가중치 × font-size) ──
  function charW(ch) {
    const c = ch.codePointAt(0);
    if (c >= 0xac00 && c <= 0xd7a3) return 1.0; // 한글 음절
    if (c >= 0x4e00 && c <= 0x9fff) return 1.0; // CJK
    if (c >= 0x3000 && c <= 0x303f) return 1.0; // CJK 문장부호
    if (ch === "·") return 0.42; // ·
    if (ch === "…") return 1.0; // …
    if (c >= 0x2018 && c <= 0x201f) return 0.46; // ‘ ’ “ ”
    if (ch === "—" || ch === "–") return 0.92; // — –
    if (/[0-9]/.test(ch)) return 0.62;
    if (/[A-Z]/.test(ch)) return 0.74;
    if (/[a-z]/.test(ch)) return 0.56;
    if (ch === " ") return 0.3;
    if (/[.,:;%'"!?()[\]\-+~/]/.test(ch)) return 0.36;
    return 0.64;
  }

  function estTextWidth(text, size) {
    let units = 0;
    for (const ch of text) units += charW(ch);
    return units * size;
  }

  // 명시 \n 우선, 없으면 공백 단위 greedy wrap (한국어 keep-all 전제)
  function wrapText(text, size, maxW) {
    if (text.includes("\n")) return text.split("\n");
    if (estTextWidth(text, size) <= maxW) return [text];
    const words = text.split(" ");
    const lines = [];
    let cur = "";
    for (const w of words) {
      const cand = cur ? cur + " " + w : w;
      if (cur && estTextWidth(cand, size) > maxW) {
        lines.push(cur);
        cur = w;
      } else {
        cur = cand;
      }
    }
    if (cur) lines.push(cur);
    return lines;
  }

  const rectsOverlap = (a, b, pad = 0) =>
    a.x < b.x + b.w + pad &&
    a.x + a.w + pad > b.x &&
    a.y < b.y + b.h + pad &&
    a.y + a.h + pad > b.y;

  // ── 충돌 회피 라벨 배치기 ──
  class LabelField {
    constructor(bounds) {
      this.bounds = bounds;
      this.obstacles = [];
    }
    addRect(x, y, w, h) {
      this.obstacles.push({ x, y, w, h });
    }
    addCircle(cx, cy, r) {
      this.addRect(cx - r, cy - r, 2 * r, 2 * r);
    }
    // 선분을 작은 사각 장애물로 샘플링
    addSegment(x1, y1, x2, y2, thick = 12, step = 20) {
      const n = Math.max(1, Math.ceil(Math.hypot(x2 - x1, y2 - y1) / step));
      for (let i = 0; i <= n; i++) {
        const x = x1 + ((x2 - x1) * i) / n;
        const y = y1 + ((y2 - y1) * i) / n;
        this.obstacles.push({ x: x - thick / 2, y: y - thick / 2, w: thick, h: thick });
      }
    }
    // 이차 베지어를 샘플링해 장애물 등록
    addQuad(ax, ay, cx, cy, bx, by, thick = 12, steps = 30) {
      let px = ax;
      let py = ay;
      for (let i = 1; i <= steps; i++) {
        const t = i / steps;
        const u = 1 - t;
        const x = u * u * ax + 2 * u * t * cx + t * t * bx;
        const y = u * u * ay + 2 * u * t * cy + t * t * by;
        this.addSegment(px, py, x, y, thick, 26);
        px = x;
        py = y;
      }
    }
    fits(r, pad = 8) {
      const b = this.bounds;
      if (r.x < b.x || r.y < b.y || r.x + r.w > b.x + b.w || r.y + r.h > b.y + b.h)
        return false;
      for (const o of this.obstacles) if (rectsOverlap(r, o, pad)) return false;
      return true;
    }
    // 후보 슬롯 순회 → 전부 충돌이면 수직 밀어내기 탐색
    place(w, h, candidates, pad = 8) {
      const clampX = (x) =>
        Math.min(Math.max(x, this.bounds.x + 2), this.bounds.x + this.bounds.w - w - 2);
      const cs = candidates.map((c) => ({ x: clampX(c.x), y: c.y }));
      for (const c of cs) {
        const r = { x: c.x, y: c.y, w, h };
        if (this.fits(r, pad)) {
          this.obstacles.push(r);
          return r;
        }
      }
      for (let d = 10; d <= 420; d += 10) {
        for (const base of cs) {
          for (const s of [-1, 1]) {
            const r = { x: base.x, y: base.y + s * d, w, h };
            if (this.fits(r, pad)) {
              this.obstacles.push(r);
              return r;
            }
          }
        }
      }
      // 최후 폴백 — 이론상 도달하지 않지만 배치 자체는 보장
      const r = { x: cs[0].x, y: cs[0].y, w, h };
      this.obstacles.push(r);
      return r;
    }
  }

  // 스테이지 밴드 + 씬 번호 장식 영역이 미리 등록된 LabelField
  function stageField() {
    const f = new LabelField({
      x: 80,
      y: LAYOUT.stageTop,
      w: W - 160,
      h: LAYOUT.stageBottom - LAYOUT.stageTop,
    });
    const sn = LAYOUT.sceneNo;
    f.addRect(sn.x, sn.y, sn.w, sn.h);
    return f;
  }

  // ── 플레이트 라벨 (반투명 배경 + 멀티라인) ──
  // lines: [{ text, size, weight?, fill?, ls? }]
  function plateLabel(parent, lines, opts = {}) {
    const padX = opts.padX ?? 14;
    const padY = opts.padY ?? 10;
    const gap = opts.gap ?? 5;
    const maxW = opts.maxW ?? 260;
    const flat = [];
    lines.forEach((L) => {
      wrapText(L.text, L.size, maxW).forEach((t) => flat.push({ ...L, text: t }));
    });
    let w = 0;
    flat.forEach((L) => {
      w = Math.max(w, estTextWidth(L.text, L.size));
    });
    w = Math.ceil(w + padX * 2);
    const g = svgEl("g", { class: "sk-plate" + (opts.cls ? " " + opts.cls : "") }, parent);
    const bg = svgEl("rect", { rx: opts.rx ?? 4, class: "sk-plate-bg" }, g);
    let cy = padY;
    flat.forEach((L, i) => {
      const t = svgEl(
        "text",
        {
          x: padX,
          y: (cy + L.size * 0.92).toFixed(1),
          class: "sk-text",
          fill: L.fill || "var(--sk-text, #ece9e2)",
          "font-size": L.size,
          "font-weight": L.weight ?? 700,
        },
        g,
      );
      if (L.ls) t.setAttribute("letter-spacing", L.ls);
      t.textContent = L.text;
      cy += L.size * 1.22 + (i < flat.length - 1 ? gap : 0);
    });
    const h = Math.ceil(cy + padY);
    bg.setAttribute("width", w);
    bg.setAttribute("height", h);
    return {
      g,
      w,
      h,
      x: 0,
      y: 0,
      setPos(x, y) {
        this.x = x;
        this.y = y;
        g.setAttribute("transform", `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      },
    };
  }

  // 마커(mx,my) 기준 4방 후보 슬롯
  function slotCandidates(mx, my, w, h, order) {
    const m = {
      above: { x: mx - w / 2, y: my - 24 - h },
      below: { x: mx - w / 2, y: my + 24 },
      left: { x: mx - 30 - w, y: my - h / 2 },
      right: { x: mx + 30, y: my - h / 2 },
    };
    return order.map((k) => m[k]);
  }

  // 마커 → 플레이트 리더선 (가까우면 생략)
  function leader(parent, ax, ay, rect, opts = {}) {
    const nx = Math.max(rect.x, Math.min(ax, rect.x + rect.w));
    const ny = Math.max(rect.y, Math.min(ay, rect.y + rect.h));
    const d = Math.hypot(nx - ax, ny - ay);
    if (d < 16) return null;
    const t0 = 14 / d; // 마커 원에서 살짝 떨어진 지점부터
    const sx = ax + (nx - ax) * t0;
    const sy = ay + (ny - ay) * t0;
    return svgEl(
      "line",
      {
        x1: sx.toFixed(1),
        y1: sy.toFixed(1),
        x2: nx.toFixed(1),
        y2: ny.toFixed(1),
        class: "sk-leader" + (opts.cls ? " " + opts.cls : ""),
      },
      parent,
    );
  }

  // draw-on 준비: 실측 길이로 dasharray/dashoffset 세팅 (+점선 환원용 dash 보관)
  function prepDraw(elGeom, dashAfter) {
    let len = 1000;
    try {
      len = Math.ceil(elGeom.getTotalLength()) + 2;
    } catch (e) {
      /* 기하 미지원 폴백 */
    }
    elGeom.setAttribute("stroke-dasharray", len);
    elGeom.setAttribute("stroke-dashoffset", len);
    elGeom.dataset.len = String(len);
    if (dashAfter) elGeom.dataset.dash = dashAfter;
    return len;
  }

  function quadAt(a, c, b, t) {
    const u = 1 - t;
    return {
      x: u * u * a.x + 2 * u * t * c.x + t * t * b.x,
      y: u * u * a.y + 2 * u * t * c.y + t * t * b.y,
    };
  }

  // 직각(orthogonal) 라우팅 path — 모서리 라운드 (단정한 연결선).
  // |dx| 우세 → H-V-H, |dy| 우세 → V-H-V. ra/rb 는 양 끝 노드 반지름 stub.
  function orthoPath(a, b, opts = {}) {
    const cr = opts.corner ?? 14;
    const ra = opts.ra ?? 0;
    const rb = opts.rb ?? 0;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const f = (v) => +v.toFixed(1);
    if (Math.abs(dx) >= Math.abs(dy)) {
      const sgx = Math.sign(dx) || 1;
      const sx = a.x + sgx * ra;
      const ex = b.x - sgx * rb;
      if (Math.abs(dy) < cr * 2 + 4) return `M ${f(sx)} ${f(a.y)} L ${f(ex)} ${f(b.y)}`;
      const mx = sx + (ex - sx) * (opts.frac ?? 0.5);
      if (Math.abs(ex - sx) < cr * 2 + 4) return `M ${f(sx)} ${f(a.y)} L ${f(ex)} ${f(b.y)}`;
      const sgy = Math.sign(dy);
      return (
        `M ${f(sx)} ${f(a.y)} L ${f(mx - sgx * cr)} ${f(a.y)} ` +
        `Q ${f(mx)} ${f(a.y)} ${f(mx)} ${f(a.y + sgy * cr)} ` +
        `L ${f(mx)} ${f(b.y - sgy * cr)} ` +
        `Q ${f(mx)} ${f(b.y)} ${f(mx + sgx * cr)} ${f(b.y)} ` +
        `L ${f(ex)} ${f(b.y)}`
      );
    }
    const sgy = Math.sign(dy) || 1;
    const sy = a.y + sgy * ra;
    const ey = b.y - sgy * rb;
    if (Math.abs(dx) < cr * 2 + 4) return `M ${f(a.x)} ${f(sy)} L ${f(b.x)} ${f(ey)}`;
    const my = (sy + ey) / 2;
    if (Math.abs(ey - sy) < cr * 2 + 4) return `M ${f(a.x)} ${f(sy)} L ${f(b.x)} ${f(ey)}`;
    const sgx = Math.sign(dx);
    return (
      `M ${f(a.x)} ${f(sy)} L ${f(a.x)} ${f(my - sgy * cr)} ` +
      `Q ${f(a.x)} ${f(my)} ${f(a.x + sgx * cr)} ${f(my)} ` +
      `L ${f(b.x - sgx * cr)} ${f(my)} ` +
      `Q ${f(b.x)} ${f(my)} ${f(b.x)} ${f(my + sgy * cr)} ` +
      `L ${f(b.x)} ${f(ey)}`
    );
  }

  // 글자 단위 split (SplitText 대체) — lines: [[ [txt, em], ... ], ...]
  // 글자 span 은 단어 span(.word, inline-block) 안에 묶어 단어 중간 줄바꿈을 차단.
  function splitChars(container, lines) {
    const chs = [];
    lines.forEach((segs) => {
      const lineEl = document.createElement("span");
      lineEl.className = "line";
      segs.forEach(([txt, em]) => {
        txt.split(/( )/).forEach((tok) => {
          if (tok === "") return;
          if (tok === " ") {
            lineEl.appendChild(document.createTextNode(" "));
            return;
          }
          const word = document.createElement("span");
          word.className = "word";
          for (const c of tok) {
            const s = document.createElement("span");
            s.className = "ch" + (em ? " em" : "");
            s.textContent = c;
            word.appendChild(s);
            chs.push(s);
          }
          lineEl.appendChild(word);
        });
      });
      container.appendChild(lineEl);
    });
    return chs;
  }

  // 숫자 카운터 tween (타임라인 소유는 호출측)
  function counter(tl, target, to, fmt, at, dur, ease) {
    const o = { v: 0 };
    tl.to(
      o,
      {
        v: to,
        duration: dur,
        ease: ease || "power1.out",
        onUpdate: () => {
          target.textContent = fmt(o.v);
        },
      },
      at,
    );
  }

  // ───────────────────── ① 스텝 타임라인 (에스컬레이션 사다리) ─────────────────────
  // steps: [{ date, label, phase }] / opts: { x0,x1,yBottom,yTop, colors, gradId, gradStops, field? }
  function buildStepTimeline(svg, steps, opts) {
    const { x0, x1, yBottom, yTop, colors, gradId } = opts;
    const field = opts.field || stageField();
    const n = steps.length;
    const geo = steps.map((p, i) => ({
      ...p,
      x: x0 + (i / (n - 1)) * (x1 - x0),
      y: yBottom - (i / (n - 1)) * (yBottom - yTop),
    }));

    const defs = svgEl("defs", {}, svg);
    const lg = svgEl("linearGradient", { id: gradId, x1: "0", y1: "1", x2: "1", y2: "0" }, defs);
    (opts.gradStops || []).forEach((s) => svgEl("stop", { offset: s[0], "stop-color": s[1] }, lg));

    let d = `M ${geo[0].x} ${geo[0].y}`;
    for (let i = 1; i < n; i++) d += ` L ${geo[i].x} ${geo[i - 1].y} L ${geo[i].x} ${geo[i].y}`;
    const riser = svgEl(
      "path",
      {
        d,
        fill: "none",
        stroke: `url(#${gradId})`,
        "stroke-width": 3,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
        opacity: 0.6,
        class: "tlm-riser",
      },
      svg,
    );
    prepDraw(riser);

    // 충돌장: 연결선 + 마커를 장애물로
    for (let i = 1; i < n; i++) {
      field.addSegment(geo[i - 1].x, geo[i - 1].y, geo[i].x, geo[i - 1].y, 14);
      field.addSegment(geo[i].x, geo[i - 1].y, geo[i].x, geo[i].y, 14);
    }
    geo.forEach((p) => field.addCircle(p.x, p.y, 18));

    const leaderLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);

    const items = geo.map((p, i) => {
      const c = colors[p.phase] || "#8a92a8";
      const mg = svgEl(
        "g",
        { class: "tlm-marker", opacity: 0, transform: `translate(${p.x} ${p.y})` },
        markerLayer,
      );
      svgEl("circle", { r: 12, fill: "var(--sk-ink, #141416)", stroke: c, "stroke-width": 3 }, mg);
      svgEl("circle", { r: 4.5, fill: c }, mg);
      if (p.phase === "present")
        svgEl(
          "circle",
          { r: 12, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.9 },
          mg,
        );
      const plate = plateLabel(
        plateLayer,
        [
          { text: p.date, size: 17, fill: c, weight: 800, ls: "1.2" },
          {
            text: p.label,
            size: 19,
            weight: 700,
            fill: p.phase === "future" ? "var(--sk-dim, #8b877d)" : "var(--sk-text, #ece9e2)",
          },
        ],
        { maxW: 236, cls: "tlm-plate" },
      );
      const order =
        i % 2 === 0 ? ["above", "below", "right", "left"] : ["below", "above", "left", "right"];
      const r = field.place(plate.w, plate.h, slotCandidates(p.x, p.y, plate.w, plate.h, order));
      plate.setPos(r.x, r.y);
      const ld = leader(leaderLayer, p.x, p.y, r, { cls: "tlm-leader" });
      if (ld) prepDraw(ld);
      return { geo: p, marker: mg, plate, leader: ld, color: c };
    });
    return { geo, riser, items, field };
  }

  // ───────────────────── ①-b 수평 축 타임라인 (캘린더형 시계열) ─────────────────────
  // 계단(에스컬레이션 서사)과 달리 중립적 시계열에 쓰는 수평 축 변형.
  // steps: [{ date, label, phase }] / opts: { x0,x1,y, colors, field? }
  function buildAxisTimeline(svg, steps, opts) {
    const { x0, x1, y, colors } = opts;
    const field = opts.field || stageField();
    const n = steps.length;
    const geo = steps.map((p, i) => ({ ...p, x: x0 + (i / (n - 1)) * (x1 - x0), y }));

    const axis = svgEl(
      "line",
      { x1: x0 - 24, y1: y, x2: x1 + 24, y2: y, stroke: "var(--sk-hairline, rgba(236,233,226,0.2))",
        "stroke-width": 2, "stroke-linecap": "round", class: "tlm-riser" },
      svg,
    );
    prepDraw(axis);
    field.addSegment(x0 - 24, y, x1 + 24, y, 14);
    geo.forEach((p) => field.addCircle(p.x, p.y, 18));

    const leaderLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);

    const items = geo.map((p, i) => {
      const c = colors[p.phase] || "#8a92a8";
      const mg = svgEl(
        "g",
        { class: "tlm-marker", opacity: 0, transform: `translate(${p.x.toFixed(1)} ${p.y})` },
        markerLayer,
      );
      svgEl("circle", { r: 11, fill: "var(--sk-ink, #141416)", stroke: c, "stroke-width": 3 }, mg);
      svgEl("circle", { r: 4, fill: c }, mg);
      if (p.phase === "present")
        svgEl("circle", { r: 11, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.9 }, mg);
      const plate = plateLabel(
        plateLayer,
        [
          { text: p.date, size: 16, fill: c, weight: 800, ls: "1.2" },
          { text: p.label, size: 18, weight: 700,
            fill: p.phase === "future" ? "var(--sk-dim, #8b877d)" : "var(--sk-text, #ece9e2)" },
        ],
        { maxW: 220, cls: "tlm-plate" },
      );
      // 위/아래 교차 우선 — 충돌 시 LabelField 가 재배치
      const order = i % 2 === 0 ? ["above", "below", "right", "left"] : ["below", "above", "left", "right"];
      const r = field.place(plate.w, plate.h, slotCandidates(p.x, p.y, plate.w, plate.h, order));
      plate.setPos(r.x, r.y);
      const ld = leader(leaderLayer, p.x, p.y, r, { cls: "tlm-leader" });
      if (ld) prepDraw(ld);
      return { geo: p, marker: mg, plate, leader: ld, color: c };
    });
    return { geo, riser: axis, items, field };
  }

  // ───────────────────── ①-c 가로 바 패널 (전망/목표가 비교) ─────────────────────
  // panels: [{ title, unit, items:[{label, value, note?}], hiIndex? }]
  // opts: { accent, top? } — HTML 기반, 컨테이너에 .barpanel 카드 생성.
  function buildBarPanels(wrap, panels, opts) {
    const accent = opts.accent || "#c4a265";
    const count = panels.length;
    const pw = count === 1 ? 1240 : 836;
    const gap = 56;
    const total = count * pw + (count - 1) * gap;
    const startX = (W - total) / 2;
    return panels.map((panel, pi) => {
      const card = document.createElement("div");
      card.className = "barpanel";
      card.style.left = (startX + pi * (pw + gap)) + "px";
      card.style.width = pw + "px";
      const maxV = Math.max(...panel.items.map((it) => it.value));
      const hi = panel.hiIndex ?? panel.items.findIndex((it) => it.value === maxV);
      let html = `<div class="bp-title">${panel.title}` +
        (panel.unit ? `<span class="bp-unit">단위 · ${panel.unit}</span>` : "") + `</div>`;
      panel.items.forEach((it, i) => {
        html +=
          `<div class="bp-row">` +
          `<div class="bp-label">${it.label}</div>` +
          `<div class="bp-track"><div class="bp-fill" style="background:${accent};` +
          `opacity:${i === hi ? 1 : 0.55};width:${((it.value / maxV) * 100).toFixed(1)}%"></div></div>` +
          `<div class="bp-val" style="color:${i === hi ? accent : "var(--muted)"}">0</div>` +
          `</div>` +
          (it.note ? `<div class="bp-note">${it.note}</div>` : "");
      });
      card.innerHTML = html;
      wrap.appendChild(card);
      const fills = [...card.querySelectorAll(".bp-fill")];
      const vals = [...card.querySelectorAll(".bp-val")];
      return { card, rows: panel.items.map((it, i) => ({ fill: fills[i], valEl: vals[i], value: it.value, unit: panel.unit || "" })) };
    });
  }

  // ───────────────────── ①-d 캔들 차트 (일봉) ─────────────────────
  // ohlc: [{date,open,high,low,close}] / opts: { x0,x1,y0,y1, up, down }
  function buildCandleChart(svg, ohlc, opts) {
    const { x0, x1, y0, y1, up, down } = opts;
    const lo = Math.min(...ohlc.map((d) => d.low));
    const hi = Math.max(...ohlc.map((d) => d.high));
    const span = hi - lo || 1;
    const ys = (v) => y1 - ((v - lo) / span) * (y1 - y0);
    const n = ohlc.length;
    const step = (x1 - x0) / n;
    const bw = Math.max(4, Math.min(18, step * 0.62));

    // 가이드라인 3개 + 우측 가격 라벨
    const gl = svgEl("g", {}, svg);
    [lo, (lo + hi) / 2, hi].forEach((v) => {
      svgEl("line", { x1: x0, y1: ys(v).toFixed(1), x2: x1, y2: ys(v).toFixed(1),
        stroke: "var(--sk-grid, #232328)", "stroke-width": 1, "stroke-dasharray": "3 6" }, gl);
      const t = svgEl("text", { x: x1 + 14, y: (ys(v) + 5).toFixed(1), fill: "var(--sk-dim, #8b877d)",
        "font-size": 15, "font-weight": 600, class: "sk-text" }, gl);
      t.textContent = Math.round(v).toLocaleString("ko-KR");
    });

    const candleLayer = svgEl("g", {}, svg);
    const candles = ohlc.map((d, i) => {
      const cx = x0 + step * (i + 0.5);
      const c = d.close >= d.open ? up : down;
      const g = svgEl("g", { class: "cd", opacity: 0 }, candleLayer);
      svgEl("line", { x1: cx.toFixed(1), y1: ys(d.high).toFixed(1), x2: cx.toFixed(1), y2: ys(d.low).toFixed(1),
        stroke: c, "stroke-width": 1.4 }, g);
      const top = ys(Math.max(d.open, d.close));
      const bot = ys(Math.min(d.open, d.close));
      svgEl("rect", { x: (cx - bw / 2).toFixed(1), y: top.toFixed(1), width: bw.toFixed(1),
        height: Math.max(1.5, bot - top).toFixed(1), fill: c, rx: 1 }, g);
      return g;
    });

    // 마지막 종가 라인 + 라벨
    const last = ohlc[n - 1].close;
    const lastLine = svgEl("line", { x1: x0, y1: ys(last).toFixed(1), x2: x1, y2: ys(last).toFixed(1),
      stroke: up, "stroke-width": 1.5, "stroke-dasharray": "6 7", opacity: 0, class: "cd-last" }, svg);
    const lastPlate = plateLabel(svg, [
      { text: "종가 " + Math.round(last).toLocaleString("ko-KR"), size: 17, weight: 800, fill: up },
    ], { cls: "cd-plate" });
    lastPlate.setPos(x1 - lastPlate.w, Math.max(y0, ys(last) - lastPlate.h - 10));
    return { candles, lastLine, lastPlate, lo, hi };
  }

  // ───────────────────── ② 베이스맵 (사전 계산 실측 지도) ─────────────────────
  // map: window.MIDEAST_MAP 형태 { countries:[{d,hi,name}], labels:[{name,x,y}] }
  function buildBasemap(svg, map, opts = {}) {
    const g = svgEl("g", { class: "basemap", opacity: opts.opacity ?? 1 }, svg);
    // 헤더 밴드 보호: 상단을 마스크로 페이드 (타이틀 밑으로 육지가 파고들지 않게)
    if (opts.fadeTop !== false) {
      const mid = (svg.id || "bm") + "-fade";
      const defs = svgEl("defs", {}, svg);
      const lg = svgEl(
        "linearGradient",
        { id: mid + "-g", x1: 0, y1: 175, x2: 0, y2: 345, gradientUnits: "userSpaceOnUse" },
        defs,
      );
      svgEl("stop", { offset: "0", "stop-color": "#fff", "stop-opacity": "0" }, lg);
      svgEl("stop", { offset: "0.55", "stop-color": "#fff", "stop-opacity": "0.55" }, lg);
      svgEl("stop", { offset: "1", "stop-color": "#fff", "stop-opacity": "1" }, lg);
      const mk = svgEl("mask", { id: mid }, defs);
      svgEl("rect", { x: 0, y: 0, width: W, height: H, fill: `url(#${mid}-g)` }, mk);
      g.setAttribute("mask", `url(#${mid})`);
    }
    map.countries.forEach((c) => {
      svgEl("path", { d: c.d, class: c.hi ? "bm-land bm-hi" : "bm-land" }, g);
    });
    if (opts.labels !== false)
      (map.labels || []).forEach((lb) => {
        const t = svgEl(
          "text",
          { x: lb.x, y: lb.y, "text-anchor": "middle", class: "sk-text bm-label" },
          g,
        );
        t.textContent = lb.name;
      });
    return g;
  }

  // ───────────────────── ③ 행위자 네트워크 (지오 앵커 + 국기/모노그램 노드) ─────────────────────
  // nodes: [{ id,label,role,kind, img?, initials?, anchor?{x,y}, x?,y? }]
  //   - anchor 가 있으면 노드 원을 anchor 주위에 충돌 회피 배치 + 앵커 점/리더선.
  //   - img 가 있으면 원 안에 국기/인물 이미지 클립 (C9: 권리는 assets/flags/RIGHTS.md).
  // links: [{ s,t,type }] / opts: { linkColors, dashByType, nodeColor(nd), nodeR?, field? }
  function buildNetwork(svg, nodes, links, opts) {
    const field = opts.field || stageField();
    const R = opts.nodeR ?? 54;
    const defs = svgEl("defs", {}, svg);
    const anchorLayer = svgEl("g", {}, svg);
    const linkLayer = svgEl("g", {}, svg);
    const nodeLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);

    // 1) 배치 — anchor 노드는 충돌장, 고정 노드는 장애물 등록만
    const N = {};
    nodes.forEach((nd) => {
      nd.r = R;
      if (nd.anchor) {
        const a = nd.anchor;
        const cand = [
          { x: a.x + 30, y: a.y - R }, // right
          { x: a.x - 2 * R - 30, y: a.y - R }, // left
          { x: a.x - R, y: a.y - 2 * R - 34 }, // above
          { x: a.x - R, y: a.y + 34 }, // below
        ];
        const rect = field.place(2 * R, 2 * R, cand, 10);
        nd.x = rect.x + R;
        nd.y = rect.y + R;
      } else {
        field.addCircle(nd.x, nd.y, R);
      }
      N[nd.id] = nd;
    });

    // 2) 노드 + 앵커 점/리더 + 이름 플레이트 — 링크보다 먼저 (링크가 회피할 대상 확정)
    const anchors = [];
    const plates = [];
    const nodeGs = nodes.map((nd) => {
      const c = opts.nodeColor(nd);
      if (nd.anchor) {
        const ag = svgEl(
          "g",
          { class: "net-anchor", opacity: 0, transform: `translate(${nd.anchor.x} ${nd.anchor.y})` },
          anchorLayer,
        );
        svgEl("circle", { r: 5, fill: c, stroke: "var(--sk-ink, #141416)", "stroke-width": 1.5 }, ag);
        const ld = leader(anchorLayer, nd.anchor.x, nd.anchor.y,
          { x: nd.x - nd.r, y: nd.y - nd.r, w: 2 * nd.r, h: 2 * nd.r }, { cls: "net-anchor-leader" });
        if (ld) prepDraw(ld);
        anchors.push({ g: ag, leader: ld });
      }
      const g = svgEl(
        "g",
        { class: "net-node", opacity: 0, transform: `translate(${nd.x} ${nd.y})` },
        nodeLayer,
      );
      svgEl(
        "circle",
        { r: nd.r, fill: "var(--sk-node-fill, rgba(29,29,33,0.94))",
          stroke: "var(--sk-hairline, rgba(236,233,226,0.14))", "stroke-width": 1 },
        g,
      );
      if (nd.img) {
        const cpId = `nclip-${nd.id}`;
        const cp = svgEl("clipPath", { id: cpId }, defs);
        svgEl("circle", { r: nd.r - 1, cx: 0, cy: 0 }, cp);
        svgEl(
          "image",
          { href: nd.img, x: -nd.r, y: -nd.r, width: 2 * nd.r, height: 2 * nd.r,
            "clip-path": `url(#${cpId})`, preserveAspectRatio: "xMidYMid slice",
            class: "net-img" },
          g,
        );
      } else {
        const mono = svgEl(
          "text",
          { x: 0, y: 11, "text-anchor": "middle", fill: c, "font-size": 30,
            "font-weight": 800, "letter-spacing": 1, class: "sk-text net-mono" },
          g,
        );
        mono.textContent = nd.initials || nd.label.slice(0, 2);
      }
      svgEl(
        "circle",
        { r: nd.r, fill: "none", stroke: c, "stroke-width": 2.5,
          opacity: nd.kind === "mediator" ? 1 : 0.9 },
        g,
      );
      if (nd.kind === "mediator")
        svgEl(
          "circle",
          { r: nd.r, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.7 },
          g,
        );
      // 이름 플레이트 (노드 아래 우선, 충돌 회피)
      const plate = plateLabel(
        plateLayer,
        [
          { text: nd.role, size: 13, weight: 700, fill: c, ls: "1.5" },
          { text: nd.label, size: 21, weight: 800, fill: "var(--sk-text, #ece9e2)" },
        ],
        { maxW: 220, cls: "net-plate", padX: 12, padY: 8 },
      );
      const rPos = field.place(
        plate.w,
        plate.h,
        slotCandidates(nd.x, nd.y, plate.w, plate.h, ["below", "above", "right", "left"]).map(
          (cd, i) => (i < 2 ? { x: cd.x, y: cd.y + (i === 0 ? nd.r - 14 : -(nd.r - 14)) } : {
            x: cd.x + (i === 2 ? nd.r : -nd.r), y: cd.y }),
        ),
      );
      plate.setPos(rPos.x, rPos.y);
      plates.push(plate);
      return g;
    });

    // 3) 링크 — 하이브리드 라우팅 + 노드 원·이름 플레이트 회피 + 흐름 펄스.
    //    근거리 = 직각(라운드 코너), 원거리/lk.curve = 위쪽 아치.
    //    후보 경로를 샘플링해 다른 노드(국기)·플레이트와 간섭하지 않는 경로를 선택:
    //    ① 노드·플레이트 모두 회피 → ② 노드만 회피 → ③ 원안 (이론상 도달 안 함).
    const flows = [];
    const ptToward = (p, q, dist) => {
      const dx = q.x - p.x;
      const dy = q.y - p.y;
      const L = Math.hypot(dx, dy) || 1;
      return { x: +(p.x + (dx / L) * dist).toFixed(1), y: +(p.y + (dy / L) * dist).toFixed(1) };
    };
    const PAD_NODE = 14;
    const PAD_PLATE = 6;
    const nodeHits = (pts, a, b) =>
      pts.reduce(
        (n, pt) =>
          n +
          (nodes.some(
            (nd) => nd !== a && nd !== b && Math.hypot(pt.x - nd.x, pt.y - nd.y) < nd.r + PAD_NODE,
          )
            ? 1
            : 0),
        0,
      );
    const plateHits = (pts) =>
      pts.reduce(
        (n, pt) =>
          n +
          (plates.some(
            (pl) =>
              pt.x > pl.x - PAD_PLATE &&
              pt.x < pl.x + pl.w + PAD_PLATE &&
              pt.y > pl.y - PAD_PLATE &&
              pt.y < pl.y + pl.h + PAD_PLATE,
          )
            ? 1
            : 0),
        0,
      );
    const inBand = (pts) => pts.every((pt) => pt.y > 272 && pt.y < 862 && pt.x > 84 && pt.x < 1836);
    const sampleSeg = (pts, x1, y1, x2, y2, step = 22) => {
      const n = Math.max(1, Math.ceil(Math.hypot(x2 - x1, y2 - y1) / step));
      for (let i = 0; i <= n; i++)
        pts.push({ x: x1 + ((x2 - x1) * i) / n, y: y1 + ((y2 - y1) * i) / n });
    };

    const linkEls = links.map((lk) => {
      const a = N[lk.s];
      const b = N[lk.t];
      const dist = Math.hypot(b.x - a.x, b.y - a.y);
      const useCurve = lk.curve ?? dist > (opts.curveDist ?? 430);
      // 위쪽 정규화 normal
      let nx = -(b.y - a.y) / dist;
      let ny = (b.x - a.x) / dist;
      if (ny > 0) {
        nx = -nx;
        ny = -ny;
      }
      const baseBend = Math.min(150, Math.max(56, dist * 0.16));

      const curveGeom = (bend, dir) => {
        const c = {
          x: (a.x + b.x) / 2 + nx * bend * dir,
          y: (a.y + b.y) / 2 + ny * bend * dir,
        };
        const sa = ptToward(a, c, a.r + 7);
        const sb = ptToward(b, c, b.r + 7);
        const pts = [];
        for (let i = 0; i <= 28; i++) pts.push(quadAt(sa, c, sb, i / 28));
        return { d: `M ${sa.x} ${sa.y} Q ${c.x.toFixed(1)} ${c.y.toFixed(1)} ${sb.x} ${sb.y}`, pts };
      };
      const orthoGeom = (frac) => {
        const d = orthoPath(a, b, { ra: a.r + 7, rb: b.r + 7, corner: 16, frac });
        const pts = [];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        if (Math.abs(dx) >= Math.abs(dy)) {
          const sgx = Math.sign(dx) || 1;
          const sx = a.x + sgx * (a.r + 7);
          const ex = b.x - sgx * (b.r + 7);
          const mx = sx + (ex - sx) * frac;
          sampleSeg(pts, sx, a.y, mx, a.y);
          sampleSeg(pts, mx, a.y, mx, b.y);
          sampleSeg(pts, mx, b.y, ex, b.y);
        } else {
          const sgy = Math.sign(dy) || 1;
          const sy = a.y + sgy * (a.r + 7);
          const ey = b.y - sgy * (b.r + 7);
          const my = sy + (ey - sy) * frac;
          sampleSeg(pts, a.x, sy, a.x, my);
          sampleSeg(pts, a.x, my, b.x, my);
          sampleSeg(pts, b.x, my, b.x, ey);
        }
        return { d, pts };
      };

      const cands = [];
      if (useCurve) {
        for (const dir of [1, -1])
          for (const extra of [0, 45, 90, 140]) cands.push(curveGeom(baseBend + extra, dir));
      } else {
        for (const fr of [0.5, 0.35, 0.65, 0.25, 0.75]) cands.push(orthoGeom(fr));
        for (const dir of [1, -1])
          for (const extra of [0, 60, 120]) cands.push(curveGeom(60 + extra, dir));
      }
      let chosen = null;
      let okNodesOnly = null;
      for (const g of cands) {
        if (!inBand(g.pts)) continue;
        const nh = nodeHits(g.pts, a, b);
        if (nh > 0) continue;
        if (plateHits(g.pts) === 0) {
          chosen = g;
          break;
        }
        if (!okNodesOnly) okNodesOnly = g;
      }
      const geom = chosen || okNodesOnly || cands[0];
      const d = geom.d;
      const ln = svgEl(
        "path",
        {
          d,
          fill: "none",
          stroke: opts.linkColors[lk.type],
          "stroke-width": lk.type === "영향" ? 2 : 3,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          opacity: 0,
          class: "net-link",
        },
        linkLayer,
      );
      prepDraw(ln, opts.dashByType[lk.type] || "");
      // 흐름 펄스: 같은 경로 위를 밝은 세그먼트가 s→t 로 순환 (영향 방향)
      const flow = svgEl(
        "path",
        { d, fill: "none", stroke: (opts.flowColors && opts.flowColors[lk.type]) || "#f2efe8",
          "stroke-width": 3, "stroke-linecap": "round", "stroke-linejoin": "round",
          opacity: 0, class: "net-flow" },
        linkLayer,
      );
      const L = Math.ceil(flow.getTotalLength()) + 2;
      const seg = Math.min(30, Math.floor(L / 4));
      flow.setAttribute("stroke-dasharray", `${seg} ${L}`);
      flow.setAttribute("stroke-dashoffset", L + seg);
      flow.dataset.len = String(L);
      flow.dataset.seg = String(seg);
      flows.push(flow);
      return ln;
    });

    return { nodeGs, linkEls, flows, plates, anchors, N };
  }

  // ───────────────────── ④ 지오 씬 (베이스맵/그래티큘 + 마커 + 아크) ─────────────────────
  // data: { regions:[{name,x,y}], markers:[{id,name,note,x,y,hi}],
  //         arcs:[{id,from,to,bend,color,width?,dash?,label?,glow?,cls?}] }
  // opts: { basemap?, grid?:{x0,x1,y0,y1,dx,dy}, hiColor, field? }
  function buildGeoScene(svg, data, opts) {
    const field = opts.field || stageField();
    let basemap = null;
    if (opts.basemap) basemap = buildBasemap(svg, opts.basemap, { labels: false });
    if (opts.grid) {
      const grid = svgEl("g", { opacity: 0.45, class: "geo-grid" }, svg);
      for (let gx = opts.grid.x0; gx <= opts.grid.x1; gx += opts.grid.dx)
        svgEl(
          "line",
          { x1: gx, y1: opts.grid.y0, x2: gx, y2: opts.grid.y1, stroke: "var(--sk-grid, #232328)", "stroke-width": 1 },
          grid,
        );
      for (let gy = opts.grid.y0; gy <= opts.grid.y1; gy += opts.grid.dy)
        svgEl(
          "line",
          { x1: opts.grid.x0, y1: gy, x2: opts.grid.x1, y2: gy, stroke: "var(--sk-grid, #232328)", "stroke-width": 1 },
          grid,
        );
    }

    (data.regions || []).forEach((rg) => {
      const t = svgEl(
        "text",
        {
          x: rg.x,
          y: rg.y,
          fill: "var(--sk-region, rgba(163,158,146,0.26))",
          "font-size": 27,
          "font-weight": 800,
          "letter-spacing": 6,
          class: "sk-text geo-region",
        },
        svg,
      );
      t.textContent = rg.name;
    });

    const arcLayer = svgEl("g", {}, svg);
    const leaderLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);

    const M = {};
    data.markers.forEach((m) => (M[m.id] = m));

    const arcs = (data.arcs || []).map((ac) => {
      const a = M[ac.from];
      const b = M[ac.to];
      const mx = (a.x + b.x) / 2;
      const my = (a.y + b.y) / 2;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const len = Math.hypot(dx, dy);
      const c = { x: mx + (-dy / len) * ac.bend, y: my + (dx / len) * ac.bend };
      const p = svgEl(
        "path",
        {
          d: `M ${a.x} ${a.y} Q ${c.x.toFixed(1)} ${c.y.toFixed(1)} ${b.x} ${b.y}`,
          fill: "none",
          stroke: ac.color,
          "stroke-width": ac.width || 2.5,
          "stroke-linecap": "round",
          opacity: 0,
          class: ac.cls || "geo-arc",
        },
        arcLayer,
      );
      if (ac.glow) p.setAttribute("filter", `drop-shadow(0 0 10px ${ac.glow})`);
      prepDraw(p, ac.dash || "");
      field.addQuad(a.x, a.y, c.x, c.y, b.x, b.y, 14);
      return { ...ac, a, b, c, path: p };
    });

    data.markers.forEach((m) => field.addCircle(m.x, m.y, 16));

    const markerItems = data.markers.map((m) => {
      const c = m.hi ? opts.hiColor : "#8a92a8";
      const g = svgEl(
        "g",
        { class: "map-marker", opacity: 0, transform: `translate(${m.x} ${m.y})` },
        markerLayer,
      );
      svgEl("circle", { r: 9, fill: c, stroke: "var(--sk-ink, #141416)", "stroke-width": 2.5 }, g);
      svgEl(
        "circle",
        { r: 9, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.8 },
        g,
      );
      const plate = plateLabel(
        plateLayer,
        [
          { text: m.name, size: 23, weight: 800, fill: "var(--sk-text, #ece9e2)" },
          { text: m.note, size: 16, weight: 600, fill: "var(--sk-muted, #a39e92)" },
        ],
        { maxW: 250, cls: "map-plate" },
      );
      const order =
        m.x < W / 2 ? ["right", "left", "below", "above"] : ["left", "right", "below", "above"];
      const r = field.place(plate.w, plate.h, slotCandidates(m.x, m.y, plate.w, plate.h, order));
      plate.setPos(r.x, r.y);
      const ld = leader(leaderLayer, m.x, m.y, r, { cls: "map-leader" });
      if (ld) prepDraw(ld);
      return { m, g, plate, leader: ld };
    });

    const arcLabels = arcs
      .filter((ac) => ac.label)
      .map((ac) => {
        const mid = quadAt(ac.a, ac.c, ac.b, 0.5);
        const plate = plateLabel(
          plateLayer,
          [{ text: ac.label, size: 18, weight: 800, fill: ac.color, ls: "0.5" }],
          { maxW: 460, cls: "arc-plate" + (ac.labelCls ? " " + ac.labelCls : "") },
        );
        const slots = {
          above: { x: mid.x - plate.w / 2, y: mid.y - 26 - plate.h },
          below: { x: mid.x - plate.w / 2, y: mid.y + 26 },
          right: { x: mid.x + 34, y: mid.y - plate.h / 2 },
          left: { x: mid.x - 34 - plate.w, y: mid.y - plate.h / 2 },
        };
        const order = ac.labelOrder || ["above", "below", "right", "left"];
        const r = field.place(plate.w, plate.h, order.map((kk) => slots[kk]));
        plate.setPos(r.x, r.y);
        return { ac, plate };
      });

    return { arcs, markerItems, arcLabels, field, M, basemap };
  }

  // ───────────────────── ④ 마켓 카드 (HTML + 스파크라인) ─────────────────────
  // markets: [{ name,last,pct,kind,arr }] / opts: { colorByKind, tagByKind, cardW?, gap?, top? }
  function buildMarketCards(wrap, markets, opts) {
    const cw = opts.cardW || 360;
    const gap = opts.gap || 56;
    const total = markets.length * cw + (markets.length - 1) * gap;
    const startX = (W - total) / 2;
    return markets.map((mk, i) => {
      const card = document.createElement("div");
      card.className = "mcard";
      card.style.left = (startX + i * (cw + gap)) + "px";
      const col = opts.colorByKind[mk.kind];
      const tag = opts.tagByKind[mk.kind];
      card.innerHTML =
        `<div class="mtop" style="background:${col}"></div>` +
        `<div class="mhead"><span class="mname">${mk.name}</span>` +
        `<span class="mtag" style="color:${col};border-color:${col}55">${tag}</span></div>` +
        `<div class="mpct" style="color:${col}">+0.0%</div>` +
        `<div class="msub">현재 ${mk.last.toLocaleString("ko-KR")}</div>`;
      const Wp = cw - 68;
      const Hp = 150;
      const pad = 10;
      const min = Math.min(...mk.arr);
      const max = Math.max(...mk.arr);
      const span = max - min || 1;
      const xs = (k) => (k / (mk.arr.length - 1)) * Wp;
      const ys = (v) => Hp - pad - ((v - min) / span) * (Hp - 2 * pad);
      let d = `M ${xs(0).toFixed(1)} ${ys(mk.arr[0]).toFixed(1)}`;
      mk.arr.forEach((v, k) => {
        if (k) d += ` L ${xs(k).toFixed(1)} ${ys(v).toFixed(1)}`;
      });
      const svg = svgEl("svg", { viewBox: `0 0 ${Wp} ${Hp}` });
      const defs = svgEl("defs", {}, svg);
      const grad = svgEl("linearGradient", { id: `skmg${i}`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
      svgEl("stop", { offset: 0, "stop-color": col, "stop-opacity": 0.3 }, grad);
      svgEl("stop", { offset: 1, "stop-color": col, "stop-opacity": 0 }, grad);
      const area = svgEl(
        "path",
        { d: `${d} L ${Wp} ${Hp} L 0 ${Hp} Z`, fill: `url(#skmg${i})`, opacity: 0, class: "spark-area" },
        svg,
      );
      if (min < 0 && max > 0)
        svgEl(
          "line",
          {
            x1: 0,
            y1: ys(0).toFixed(1),
            x2: Wp,
            y2: ys(0).toFixed(1),
            stroke: "var(--sk-hairline, rgba(236,233,226,0.16))",
            "stroke-width": 1,
            "stroke-dasharray": "3 5",
          },
          svg,
        );
      const line = svgEl(
        "path",
        {
          d,
          fill: "none",
          stroke: col,
          "stroke-width": 3,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          class: "spark-line",
        },
        svg,
      );
      prepDraw(line);
      const end = svgEl(
        "circle",
        {
          cx: xs(mk.arr.length - 1).toFixed(1),
          cy: ys(mk.arr[mk.arr.length - 1]).toFixed(1),
          r: 5,
          fill: col,
          class: "spark-end",
          opacity: 0,
        },
        svg,
      );
      card.appendChild(svg);
      wrap.appendChild(card);
      return { card, line, area, end, pctEl: card.querySelector(".mpct"), data: mk, color: col };
    });
  }

  // ───────────────────── ⑤ 프로필 카드 (키 플레이어, 날리지식 패턴 ③) ─────────────────────
  // people: [{ initials, name, org, line, stance(0=자제..1=확전), stanceLabel, color, img? }]
  // opts: { cardW?, cardH?, gap?, top? }
  // C9: 인물 사진/AI 이미지 대신 모노그램 + 컬러 링 (권리 안전 기본값).
  function buildProfileCards(wrap, people, opts = {}) {
    const cw = opts.cardW || 390;
    const ch = opts.cardH || 440;
    const gap = opts.gap || 48;
    const total = people.length * cw + (people.length - 1) * gap;
    const startX = (W - total) / 2;
    const trackW = cw - 68; // 카드 padding 34*2
    const gauge = { left: "자제", right: "확전", tag: "분석 추정", ...(opts.gauge || {}) };
    return people.map((p, i) => {
      const card = document.createElement("div");
      card.className = "pcard";
      card.style.left = (startX + i * (cw + gap)) + "px";
      card.style.width = cw + "px";
      card.style.height = ch + "px";
      card.innerHTML =
        `<div class="ptop" style="background:${p.color}"></div>` +
        `<div class="phead">` +
        `<div class="pmono">${p.img
          ? `<img src="${p.img}" alt="" />`
          : `<span style="color:${p.color}">${p.initials}</span>`}</div>` +
        `<div class="pid"><div class="pname">${p.name}</div><div class="porg">${p.org}</div></div>` +
        `</div>` +
        `<div class="pline">${p.line}</div>` +
        `<div class="pgauge">` +
        `<div class="glabels"><span>${gauge.left}</span><span class="gtag">${gauge.tag}</span><span>${gauge.right}</span></div>` +
        `<div class="gtrack"><div class="gdot" style="background:${p.color};box-shadow:0 0 14px ${p.color}"></div></div>` +
        `<div class="gstance" style="color:${p.color}">${p.stanceLabel}</div>` +
        `</div>`;
      // 모노그램 링 (draw-on 용 SVG 원)
      const mono = card.querySelector(".pmono");
      const ringSvg = svgEl("svg", { viewBox: "0 0 92 92", class: "pring-svg" });
      const ring = svgEl(
        "circle",
        { cx: 46, cy: 46, r: 42, fill: "none", stroke: p.color, "stroke-width": 3,
          "stroke-linecap": "round", transform: "rotate(-90 46 46)", class: "pring" },
        ringSvg,
      );
      prepDraw(ring);
      mono.appendChild(ringSvg);
      return {
        card,
        ring,
        dot: card.querySelector(".gdot"),
        lineEl: card.querySelector(".pline"),
        stanceEl: card.querySelector(".gstance"),
        dotX: p.stance * trackW,
        data: p,
      };
    }).map((it) => (wrap.appendChild(it.card), it));
  }

  window.SceneKit = {
    LAYOUT,
    svgEl,
    estTextWidth,
    wrapText,
    LabelField,
    stageField,
    plateLabel,
    slotCandidates,
    leader,
    prepDraw,
    quadAt,
    orthoPath,
    splitChars,
    counter,
    buildStepTimeline,
    buildAxisTimeline,
    buildBarPanels,
    buildCandleChart,
    buildBasemap,
    buildNetwork,
    buildGeoScene,
    buildMarketCards,
    buildProfileCards,
  };
})();
