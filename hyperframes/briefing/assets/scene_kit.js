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
 *  - buildStepTimeline / buildNetwork / buildGeoScene / buildMarketCards / buildProfileCards
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
    const bg = svgEl("rect", { rx: opts.rx ?? 10, class: "sk-plate-bg" }, g);
    let cy = padY;
    flat.forEach((L, i) => {
      const t = svgEl(
        "text",
        {
          x: padX,
          y: (cy + L.size * 0.92).toFixed(1),
          class: "sk-text",
          fill: L.fill || "#e8ecef",
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
      svgEl("circle", { r: 12, fill: "#11152a", stroke: c, "stroke-width": 3 }, mg);
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
            fill: p.phase === "future" ? "#aeb6cf" : "#eef1f5",
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

  // ───────────────────── ② 행위자 네트워크 ─────────────────────
  // nodes: [{ id,label,role,x,y,kind }] / links: [{ s,t,type }]
  // opts: { linkColors, dashByType, nodeColor(nd)→color }
  function buildNetwork(svg, nodes, links, opts) {
    const N = {};
    nodes.forEach((nd) => {
      const nameW = estTextWidth(nd.label, 23);
      const roleW = estTextWidth(nd.role, 14);
      nd.r = Math.min(88, Math.max(58, nameW / 2 + 20, roleW / 2 + 18));
      N[nd.id] = nd;
    });
    const linkLayer = svgEl("g", {}, svg);
    const linkEls = links.map((lk) => {
      const a = N[lk.s];
      const b = N[lk.t];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const len = Math.hypot(dx, dy);
      const ux = dx / len;
      const uy = dy / len;
      // 노드 원 가장자리에서 끊기 — 원/라벨 밑으로 파고들지 않게
      const ln = svgEl(
        "line",
        {
          x1: (a.x + ux * (a.r + 8)).toFixed(1),
          y1: (a.y + uy * (a.r + 8)).toFixed(1),
          x2: (b.x - ux * (b.r + 8)).toFixed(1),
          y2: (b.y - uy * (b.r + 8)).toFixed(1),
          stroke: opts.linkColors[lk.type],
          "stroke-width": lk.type === "영향" ? 2 : 3,
          "stroke-linecap": "round",
          opacity: 0,
          class: "net-link",
        },
        linkLayer,
      );
      prepDraw(ln, opts.dashByType[lk.type] || "");
      return ln;
    });
    const nodeLayer = svgEl("g", {}, svg);
    const nodeGs = nodes.map((nd) => {
      const c = opts.nodeColor(nd);
      const g = svgEl(
        "g",
        { class: "net-node", opacity: 0, transform: `translate(${nd.x} ${nd.y})` },
        nodeLayer,
      );
      svgEl(
        "circle",
        { r: nd.r, fill: "rgba(31,36,64,0.93)", stroke: "rgba(58,64,96,0.6)", "stroke-width": 1 },
        g,
      );
      svgEl(
        "circle",
        {
          r: nd.r,
          fill: "none",
          stroke: c,
          "stroke-width": 3,
          opacity: nd.kind === "mediator" ? 1 : 0.85,
        },
        g,
      );
      if (nd.kind === "mediator")
        svgEl(
          "circle",
          { r: nd.r, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.7 },
          g,
        );
      const role = svgEl(
        "text",
        {
          x: 0,
          y: -12,
          "text-anchor": "middle",
          fill: c,
          "font-size": 14,
          "font-weight": 700,
          "letter-spacing": 2,
          class: "sk-text",
        },
        g,
      );
      role.textContent = nd.role;
      const lab = svgEl(
        "text",
        {
          x: 0,
          y: 20,
          "text-anchor": "middle",
          fill: "#eef1f5",
          "font-size": 23,
          "font-weight": 800,
          class: "sk-text",
        },
        g,
      );
      lab.textContent = nd.label;
      return g;
    });
    return { nodeGs, linkEls, N };
  }

  // ───────────────────── ③ 지오 씬 (그래티큘 + 마커 + 아크) ─────────────────────
  // data: { regions:[{name,x,y}], markers:[{id,name,note,x,y,hi}],
  //         arcs:[{id,from,to,bend,color,width?,dash?,label?,glow?,cls?}] }
  // opts: { grid:{x0,x1,y0,y1,dx,dy}, hiColor, field? }
  function buildGeoScene(svg, data, opts) {
    const field = opts.field || stageField();
    const grid = svgEl("g", { opacity: 0.45, class: "geo-grid" }, svg);
    for (let gx = opts.grid.x0; gx <= opts.grid.x1; gx += opts.grid.dx)
      svgEl(
        "line",
        { x1: gx, y1: opts.grid.y0, x2: gx, y2: opts.grid.y1, stroke: "#262c4e", "stroke-width": 1 },
        grid,
      );
    for (let gy = opts.grid.y0; gy <= opts.grid.y1; gy += opts.grid.dy)
      svgEl(
        "line",
        { x1: opts.grid.x0, y1: gy, x2: opts.grid.x1, y2: gy, stroke: "#262c4e", "stroke-width": 1 },
        grid,
      );

    (data.regions || []).forEach((rg) => {
      const t = svgEl(
        "text",
        {
          x: rg.x,
          y: rg.y,
          fill: "rgba(138,146,168,0.30)",
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
      svgEl("circle", { r: 9, fill: c, stroke: "#0b0e1f", "stroke-width": 2.5 }, g);
      svgEl(
        "circle",
        { r: 9, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.8 },
        g,
      );
      const plate = plateLabel(
        plateLayer,
        [
          { text: m.name, size: 23, weight: 800, fill: "#eef1f5" },
          { text: m.note, size: 16, weight: 600, fill: "#9aa2b8" },
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
        const r = field.place(plate.w, plate.h, [
          { x: mid.x - plate.w / 2, y: mid.y - 26 - plate.h },
          { x: mid.x - plate.w / 2, y: mid.y + 26 },
          { x: mid.x + 34, y: mid.y - plate.h / 2 },
          { x: mid.x - 34 - plate.w, y: mid.y - plate.h / 2 },
        ]);
        plate.setPos(r.x, r.y);
        return { ac, plate };
      });

    return { arcs, markerItems, arcLabels, field, M };
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
            stroke: "#3a4060",
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
  // people: [{ initials, name, org, line, stance(0=자제..1=확전), stanceLabel, color }]
  // opts: { cardW?, cardH?, gap?, top? }
  // C9: 인물 사진/AI 이미지 대신 모노그램 + 컬러 링 (권리 안전 기본값).
  function buildProfileCards(wrap, people, opts = {}) {
    const cw = opts.cardW || 390;
    const ch = opts.cardH || 440;
    const gap = opts.gap || 48;
    const total = people.length * cw + (people.length - 1) * gap;
    const startX = (W - total) / 2;
    const trackW = cw - 68; // 카드 padding 34*2
    return people.map((p, i) => {
      const card = document.createElement("div");
      card.className = "pcard";
      card.style.left = (startX + i * (cw + gap)) + "px";
      card.style.width = cw + "px";
      card.style.height = ch + "px";
      card.innerHTML =
        `<div class="ptop" style="background:${p.color}"></div>` +
        `<div class="phead">` +
        `<div class="pmono"><span style="color:${p.color}">${p.initials}</span></div>` +
        `<div class="pid"><div class="pname">${p.name}</div><div class="porg">${p.org}</div></div>` +
        `</div>` +
        `<div class="pline">${p.line}</div>` +
        `<div class="pgauge">` +
        `<div class="glabels"><span>자제</span><span class="gtag">분석 추정</span><span>확전</span></div>` +
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
    splitChars,
    counter,
    buildStepTimeline,
    buildNetwork,
    buildGeoScene,
    buildMarketCards,
    buildProfileCards,
  };
})();
