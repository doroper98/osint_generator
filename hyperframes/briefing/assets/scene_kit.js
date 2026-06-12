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

  // ───────────────────── ①-e 서펜타인 타임라인 (2단 S자 — 분기점 多) ─────────────────────
  // steps 를 2행으로 흐르게 배치: 윗행 좌→우, U턴, 아랫행 우→좌.
  function buildSerpentineTimeline(svg, steps, opts) {
    const { colors } = opts;
    const field = opts.field || stageField();
    const x0 = opts.x0 ?? 280;
    const x1 = opts.x1 ?? 1560;
    const yTop = opts.yTop ?? 420;
    const yBot = opts.yBot ?? 712;
    const n = steps.length;
    const topN = Math.ceil(n / 2);
    const botN = n - topN;

    // 경로: 윗행 → 우측 라운드 U턴 → 아랫행 (uturn 반경)
    const ur = (yBot - yTop) / 2;
    const cxU = x1 + 30;
    const d =
      `M ${x0 - 30} ${yTop} L ${cxU} ${yTop} ` +
      `A ${ur} ${ur} 0 0 1 ${cxU} ${yBot} ` +
      `L ${x0 - 30} ${yBot}`;
    const path = svgEl("path", { d, fill: "none", stroke: "var(--sk-hairline, rgba(236,233,226,0.2))",
      "stroke-width": 2, "stroke-linecap": "round", class: "tlm-riser" }, svg);
    prepDraw(path);
    field.addSegment(x0 - 30, yTop, cxU, yTop, 14);
    field.addSegment(x0 - 30, yBot, cxU, yBot, 14);
    field.addQuad(cxU, yTop, cxU + ur * 1.4, (yTop + yBot) / 2, cxU, yBot, 14);

    const geo = steps.map((p, i) => {
      if (i < topN) {
        const x = topN === 1 ? x0 : x0 + (i / (topN - 1)) * (x1 - x0);
        return { ...p, x, y: yTop };
      }
      const j = i - topN;
      const x = botN === 1 ? x1 : x1 - (j / (botN - 1)) * (x1 - x0);
      return { ...p, x, y: yBot };
    });
    geo.forEach((p) => field.addCircle(p.x, p.y, 16));

    const leaderLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);
    const items = geo.map((p, i) => {
      const c = colors[p.phase] || "#8a92a8";
      const mg = svgEl("g", { class: "tlm-marker", opacity: 0,
        transform: `translate(${p.x.toFixed(1)} ${p.y})` }, markerLayer);
      svgEl("circle", { r: 10, fill: "var(--sk-ink, #141416)", stroke: c, "stroke-width": 3 }, mg);
      svgEl("circle", { r: 3.5, fill: c }, mg);
      if (p.phase === "present")
        svgEl("circle", { r: 10, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.9 }, mg);
      const plate = plateLabel(plateLayer, [
        { text: p.date, size: 15, fill: c, weight: 800, ls: "1" },
        { text: p.label, size: 17, weight: 700,
          fill: p.phase === "future" ? "var(--sk-dim, #8b877d)" : "var(--sk-text, #ece9e2)" },
      ], { maxW: 210, cls: "tlm-plate" });
      // 윗행은 위, 아랫행은 아래 우선
      const order = p.y === yTop ? ["above", "below", "right", "left"] : ["below", "above", "left", "right"];
      const r = field.place(plate.w, plate.h, slotCandidates(p.x, p.y, plate.w, plate.h, order));
      plate.setPos(r.x, r.y);
      const ld = leader(leaderLayer, p.x, p.y, r, { cls: "tlm-leader" });
      if (ld) prepDraw(ld);
      return { geo: p, marker: mg, plate, leader: ld, color: c };
    });
    return { geo, riser: path, items, field };
  }

  // ───────────────────── ①-f 수직 타임라인 (긴 설명형 — 기사 레일) ─────────────────────
  // 좌측 레일 + 우측 와이드 플레이트. 라벨이 긴 시계열에 적합 (≤6개 권장).
  function buildVerticalTimeline(svg, steps, opts) {
    const { colors } = opts;
    const field = opts.field || stageField();
    const railX = opts.railX ?? 470;
    const y0 = opts.y0 ?? 318;
    const y1 = opts.y1 ?? 830;
    const n = steps.length;

    const rail = svgEl("line", { x1: railX, y1: y0 - 16, x2: railX, y2: y1 + 16,
      stroke: "var(--sk-hairline, rgba(236,233,226,0.2))", "stroke-width": 2,
      "stroke-linecap": "round", class: "tlm-riser" }, svg);
    prepDraw(rail);
    field.addSegment(railX, y0 - 16, railX, y1 + 16, 14);

    const plateLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);
    const items = steps.map((p, i) => {
      const y = n === 1 ? y0 : y0 + (i / (n - 1)) * (y1 - y0);
      const c = colors[p.phase] || "#8a92a8";
      const mg = svgEl("g", { class: "tlm-marker", opacity: 0,
        transform: `translate(${railX} ${y.toFixed(1)})` }, markerLayer);
      svgEl("circle", { r: 10, fill: "var(--sk-ink, #141416)", stroke: c, "stroke-width": 3 }, mg);
      svgEl("circle", { r: 3.5, fill: c }, mg);
      if (p.phase === "present")
        svgEl("circle", { r: 10, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.9 }, mg);
      // 날짜 — 레일 좌측 (plate 없이 텍스트, 우측 정렬)
      const dateT = svgEl("text", { x: railX - 26, y: (y + 6).toFixed(1), "text-anchor": "end",
        fill: c, "font-size": 17, "font-weight": 800, "letter-spacing": "1",
        class: "sk-text tlm-date", opacity: 0 }, svg);
      dateT.textContent = p.date;
      // 라벨 — 레일 우측 와이드 플레이트
      const plate = plateLabel(plateLayer, [
        { text: p.label, size: 19, weight: 700,
          fill: p.phase === "future" ? "var(--sk-dim, #8b877d)" : "var(--sk-text, #ece9e2)" },
      ], { maxW: 980, cls: "tlm-plate" });
      const r = field.place(plate.w, plate.h, [
        { x: railX + 36, y: y - plate.h / 2 },
        { x: railX + 36, y: y - plate.h },
        { x: railX + 36, y: y },
      ]);
      plate.setPos(r.x, r.y);
      return { geo: { ...p, x: railX, y }, marker: mg, plate, dateEl: dateT, leader: null, color: c };
    });
    return { geo: items.map((it) => it.geo), riser: rail, items, field };
  }

  // ───────────────────── ①-g 메트로 타임라인 (국면 구간 색 노선도) ─────────────────────
  // 정거장 사이 구간을 다음 정거장 phase 색으로 칠해 국면 전환을 선 자체로 보여준다.
  function buildMetroTimeline(svg, steps, opts) {
    const { colors } = opts;
    const field = opts.field || stageField();
    const x0 = opts.x0 ?? 250;
    const x1 = opts.x1 ?? 1650;
    const y = opts.y ?? 586;
    const n = steps.length;
    const geo = steps.map((p, i) => ({ ...p, x: x0 + (i / (n - 1)) * (x1 - x0), y }));

    const segLayer = svgEl("g", {}, svg);
    const segs = [];
    for (let i = 1; i < n; i++) {
      const c = colors[geo[i].phase] || "#8a92a8";
      const sg = svgEl("line", { x1: geo[i - 1].x.toFixed(1), y1: y, x2: geo[i].x.toFixed(1), y2: y,
        stroke: c, "stroke-width": 7, "stroke-linecap": "round", opacity: 0.85, class: "metro-seg" }, segLayer);
      prepDraw(sg);
      segs.push(sg);
    }
    field.addSegment(x0, y, x1, y, 16);
    geo.forEach((p) => field.addCircle(p.x, p.y, 18));

    const leaderLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const markerLayer = svgEl("g", {}, svg);
    const items = geo.map((p, i) => {
      const c = colors[p.phase] || "#8a92a8";
      const mg = svgEl("g", { class: "tlm-marker", opacity: 0,
        transform: `translate(${p.x.toFixed(1)} ${p.y})` }, markerLayer);
      svgEl("circle", { r: 13, fill: "var(--sk-ink, #141416)", stroke: c, "stroke-width": 4 }, mg);
      if (p.phase === "present")
        svgEl("circle", { r: 13, fill: "none", stroke: c, "stroke-width": 2, class: "pulse-ring", opacity: 0.9 }, mg);
      const plate = plateLabel(plateLayer, [
        { text: p.date, size: 16, fill: c, weight: 800, ls: "1.2" },
        { text: p.label, size: 18, weight: 700,
          fill: p.phase === "future" ? "var(--sk-dim, #8b877d)" : "var(--sk-text, #ece9e2)" },
      ], { maxW: 220, cls: "tlm-plate" });
      const order = i % 2 === 0 ? ["above", "below", "right", "left"] : ["below", "above", "left", "right"];
      const r = field.place(plate.w, plate.h, slotCandidates(p.x, p.y, plate.w, plate.h, order));
      plate.setPos(r.x, r.y);
      const ld = leader(leaderLayer, p.x, p.y, r, { cls: "tlm-leader" });
      if (ld) prepDraw(ld);
      return { geo: p, marker: mg, plate, leader: ld, color: c };
    });
    return { geo, riser: null, segs, items, field };
  }

  // ───────────────────── ①-h 슬로프 차트 (좌→우 변화 비교) ─────────────────────
  // data: { left_label, right_label, items:[{label, a, b}] } / opts: { accent }
  function buildSlopeChart(svg, data, opts) {
    const field = opts.field || stageField();
    const xL = opts.xL ?? 620;
    const xR = opts.xR ?? 1300;
    const y0 = opts.y0 ?? 350;
    const y1 = opts.y1 ?? 800;
    const accent = opts.accent || "#c4a265";
    const vals = data.items.flatMap((it) => [it.a, it.b]);
    const lo = Math.min(...vals);
    const hi = Math.max(...vals);
    const span = hi - lo || 1;
    const ys = (v) => y1 - ((v - lo) / span) * (y1 - y0);

    // 좌/우 기둥 + 컬럼 라벨
    [[xL, data.left_label], [xR, data.right_label]].forEach(([x, lab]) => {
      svgEl("line", { x1: x, y1: y0 - 26, x2: x, y2: y1 + 26,
        stroke: "var(--sk-hairline, rgba(236,233,226,0.16))", "stroke-width": 1.5 }, svg);
      const t = svgEl("text", { x, y: y0 - 44, "text-anchor": "middle",
        fill: "var(--sk-muted, #a39e92)", "font-size": 18, "font-weight": 700,
        "letter-spacing": "2", class: "sk-text" }, svg);
      t.textContent = lab;
      field.addSegment(x, y0 - 26, x, y1 + 26, 12);
    });

    // 변화 폭 최대 항목 하이라이트
    let hiIdx = 0;
    data.items.forEach((it, i) => {
      if (Math.abs(it.b - it.a) > Math.abs(data.items[hiIdx].b - data.items[hiIdx].a)) hiIdx = i;
    });

    const lineLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const items = data.items.map((it, i) => {
      const yA = ys(it.a);
      const yB = ys(it.b);
      const isHi = i === hiIdx;
      const c = isHi ? accent : "var(--sk-dim, #8b877d)";
      const ln = svgEl("line", { x1: xL, y1: yA.toFixed(1), x2: xR, y2: yB.toFixed(1),
        stroke: c, "stroke-width": isHi ? 3.5 : 2, "stroke-linecap": "round",
        opacity: 0, class: "slope-line" }, lineLayer);
      prepDraw(ln);
      field.addSegment(xL, yA, xR, yB, 10);
      const dotA = svgEl("circle", { cx: xL, cy: yA.toFixed(1), r: isHi ? 6 : 4.5, fill: c, opacity: 0, class: "slope-dot" }, lineLayer);
      const dotB = svgEl("circle", { cx: xR, cy: yB.toFixed(1), r: isHi ? 6 : 4.5, fill: c, opacity: 0, class: "slope-dot" }, lineLayer);
      // 좌: 라벨+시작값 / 우: 종료값
      const pA = plateLabel(plateLayer, [
        { text: `${it.label} · ${it.a.toLocaleString("ko-KR")}`, size: 16, weight: isHi ? 800 : 600,
          fill: isHi ? accent : "var(--sk-muted, #a39e92)" },
      ], { cls: "slope-plate" });
      const rA = field.place(pA.w, pA.h, [
        { x: xL - 30 - pA.w, y: yA - pA.h / 2 },
        { x: xL - 30 - pA.w, y: yA - pA.h },
        { x: xL - 30 - pA.w, y: yA },
      ]);
      pA.setPos(rA.x, rA.y);
      const pB = plateLabel(plateLayer, [
        { text: it.b.toLocaleString("ko-KR"), size: 17, weight: isHi ? 800 : 600,
          fill: isHi ? accent : "var(--sk-muted, #a39e92)" },
      ], { cls: "slope-plate" });
      const rB = field.place(pB.w, pB.h, [
        { x: xR + 30, y: yB - pB.h / 2 },
        { x: xR + 30, y: yB - pB.h },
        { x: xR + 30, y: yB },
      ]);
      pB.setPos(rB.x, rB.y);
      return { line: ln, dots: [dotA, dotB], plates: [pA, pB], hi: isHi };
    });
    return { items, hiIdx, field };
  }

  // ───────────────────── ①-i 도넛 차트 (구성비) ─────────────────────
  // items: [{label, value}] / opts: { cx, cy, r, width, colors[] , centerLabel?, centerValue? }
  function buildDonut(svg, items, opts) {
    const cx = opts.cx ?? 760;
    const cy = opts.cy ?? 580;
    const R = opts.r ?? 175;
    const wdt = opts.width ?? 46;
    const palette = opts.colors;
    const field = opts.field || stageField();
    const total = items.reduce((s, it) => s + it.value, 0) || 1;
    field.addCircle(cx, cy, R + wdt);

    const segLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    let acc = -Math.PI / 2; // 12시 시작
    const segs = items.map((it, i) => {
      const frac = it.value / total;
      const a0 = acc;
      const a1 = acc + frac * Math.PI * 2;
      acc = a1;
      // 아크 path (간격 1.5도)
      const gapA = 0.013;
      const s0 = a0 + gapA;
      const s1 = Math.max(s0 + 0.02, a1 - gapA);
      const large = s1 - s0 > Math.PI ? 1 : 0;
      const p0 = { x: cx + R * Math.cos(s0), y: cy + R * Math.sin(s0) };
      const p1 = { x: cx + R * Math.cos(s1), y: cy + R * Math.sin(s1) };
      const c = palette[i % palette.length];
      const path = svgEl("path", {
        d: `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} A ${R} ${R} 0 ${large} 1 ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`,
        fill: "none", stroke: c, "stroke-width": wdt, opacity: 0, class: "donut-seg",
      }, segLayer);
      prepDraw(path);
      // 라벨 플레이트 + 리더
      const mid = (s0 + s1) / 2;
      const ax = cx + (R + wdt / 2 + 8) * Math.cos(mid);
      const ay = cy + (R + wdt / 2 + 8) * Math.sin(mid);
      const plate = plateLabel(plateLayer, [
        { text: `${it.label} · ${Math.round(frac * 100)}%`, size: 17, weight: 700, fill: c },
      ], { cls: "donut-plate" });
      const ox = Math.cos(mid) >= 0 ? 36 : -36 - plate.w;
      const r = field.place(plate.w, plate.h, [
        { x: ax + ox, y: ay - plate.h / 2 },
        { x: ax + ox, y: ay - plate.h - 8 },
        { x: ax + ox, y: ay + 8 },
      ]);
      plate.setPos(r.x, r.y);
      const ld = leader(plateLayer, ax, ay, r, { cls: "donut-leader" });
      if (ld) prepDraw(ld);
      return { path, plate, leader: ld, frac };
    });
    // 중심 라벨
    if (opts.centerLabel) {
      const t1 = svgEl("text", { x: cx, y: cy - 8, "text-anchor": "middle",
        fill: "var(--sk-muted, #a39e92)", "font-size": 17, "font-weight": 600, class: "sk-text" }, svg);
      t1.textContent = opts.centerLabel;
      const t2 = svgEl("text", { x: cx, y: cy + 32, "text-anchor": "middle",
        fill: "var(--sk-text, #ece9e2)", "font-size": 34, "font-weight": 800, class: "sk-text" }, svg);
      t2.textContent = opts.centerValue || "";
    }
    return { segs, field };
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

  // ───────────────────── ⑨ 스택 바 (구성/점유율 — 가로 누적) ─────────────────────
  // data: { rows:[{label, segments:[{name, value}]}], unit? }
  // opts: { x0,x1,yTop, palette:[color..] }
  function buildStackedBars(svg, data, opts) {
    const x0 = opts.x0 ?? 430;
    const x1 = opts.x1 ?? 1640;
    const palette = opts.palette;
    const rows = data.rows;
    const rowH = rows.length <= 4 ? 64 : 52;
    const gap = rows.length <= 4 ? 46 : 32;
    const blockH = rows.length * rowH + (rows.length - 1) * gap;
    const yTop = opts.yTop ?? Math.max(320, 567 - blockH / 2);
    const maxTotal = Math.max(...rows.map((r) => r.segments.reduce((s, g) => s + g.value, 0)));
    const segNames = [];
    rows.forEach((r) => r.segments.forEach((g) => { if (!segNames.includes(g.name)) segNames.push(g.name); }));
    const colorOf = (name) => palette[segNames.indexOf(name) % palette.length];

    const out = rows.map((r, ri) => {
      const y = yTop + ri * (rowH + gap);
      const lab = svgEl("text", { x: x0 - 26, y: y + rowH / 2 + 6, "text-anchor": "end",
        fill: "var(--sk-muted, #a39e92)", "font-size": 19, "font-weight": 600, class: "sk-text" }, svg);
      lab.textContent = r.label;
      const total = r.segments.reduce((s, g) => s + g.value, 0);
      let cx = x0;
      const segRects = r.segments.map((g) => {
        const w = ((g.value / maxTotal) * (x1 - x0));
        const grp = svgEl("g", { class: "stk-seg", opacity: 0 }, svg);
        svgEl("rect", { x: cx.toFixed(1), y, width: Math.max(0, w - 3).toFixed(1), height: rowH,
          rx: 4, fill: colorOf(g.name), opacity: 0.92 }, grp);
        if (w > 86) {
          const vt = svgEl("text", { x: (cx + 14).toFixed(1), y: y + rowH / 2 + 6,
            fill: "var(--sk-ink, #141416)", "font-size": 16, "font-weight": 800, class: "sk-text" }, grp);
          vt.textContent = g.value.toLocaleString("ko-KR");
        }
        // 세그먼트는 자기 폭만큼 왼쪽에서 자라난다 (scaleX 애니용 origin 저장)
        grp.dataset.ox = String(cx);
        cx += w;
        return grp;
      });
      const totalT = svgEl("text", { x: (cx + 18).toFixed(1), y: y + rowH / 2 + 7,
        fill: "var(--sk-text, #ece9e2)", "font-size": 21, "font-weight": 800,
        class: "sk-text stk-total", opacity: 0 }, svg);
      totalT.textContent = total.toLocaleString("ko-KR") + (data.unit || "");
      return { labelEl: lab, segRects, totalEl: totalT };
    });
    return { rows: out, segNames, colorOf };
  }

  // ───────────────────── ⑩ 워터폴 (증감 브리지) ─────────────────────
  // data: { items:[{label, value, kind:"start"|"delta"|"total"}], unit? }
  // opts: { x0,x1,y0,y1, up, down, accent }
  function buildWaterfall(svg, data, opts) {
    const { up, down, accent } = opts;
    const x0 = opts.x0 ?? 250;
    const x1 = opts.x1 ?? 1660;
    const y0 = opts.y0 ?? 330;
    const y1 = opts.y1 ?? 760;
    const items = data.items;
    // 러닝 합계 → [from, to] 구간
    let run = 0;
    const spans = items.map((it) => {
      if (it.kind === "start" || it.kind === "total") {
        const s = { from: 0, to: it.kind === "start" ? it.value : run, abs: true };
        if (it.kind === "start") run = it.value;
        return s;
      }
      const s = { from: run, to: run + it.value, abs: false };
      run += it.value;
      return s;
    });
    const lo = Math.min(0, ...spans.map((s) => Math.min(s.from, s.to)));
    const hi = Math.max(...spans.map((s) => Math.max(s.from, s.to)));
    const span = hi - lo || 1;
    const ys = (v) => y1 - ((v - lo) / span) * (y1 - y0);
    const n = items.length;
    const slot = (x1 - x0) / n;
    const bw = Math.min(140, slot * 0.58);

    svgEl("line", { x1: x0 - 20, y1: ys(0).toFixed(1), x2: x1 + 20, y2: ys(0).toFixed(1),
      stroke: "var(--sk-hairline, rgba(236,233,226,0.2))", "stroke-width": 1.5 }, svg);

    const cols = items.map((it, i) => {
      const cx = x0 + slot * (i + 0.5);
      const s = spans[i];
      const top = ys(Math.max(s.from, s.to));
      const bot = ys(Math.min(s.from, s.to));
      const color = s.abs ? accent : it.value >= 0 ? up : down;
      const g = svgEl("g", { class: "wf-col", opacity: 0 }, svg);
      svgEl("rect", { x: (cx - bw / 2).toFixed(1), y: top.toFixed(1), width: bw.toFixed(1),
        height: Math.max(3, bot - top).toFixed(1), rx: 4, fill: color, opacity: 0.92 }, g);
      // 값 라벨 (위) + 항목 라벨 (아래)
      const vt = svgEl("text", { x: cx.toFixed(1), y: (top - 14).toFixed(1), "text-anchor": "middle",
        fill: color, "font-size": 19, "font-weight": 800, class: "sk-text sk-halo" }, g);
      vt.textContent = (s.abs ? "" : it.value > 0 ? "+" : "") + it.value.toLocaleString("ko-KR") + (data.unit || "");
      const lt = svgEl("text", { x: cx.toFixed(1), y: y1 + 36, "text-anchor": "middle",
        fill: "var(--sk-muted, #a39e92)", "font-size": 17, "font-weight": 600, class: "sk-text" }, g);
      lt.textContent = it.label;
      // 커넥터 (다음 컬럼으로, 점선)
      let conn = null;
      if (i < n - 1) {
        const ny = ys(s.to);
        conn = svgEl("line", { x1: (cx + bw / 2).toFixed(1), y1: ny.toFixed(1),
          x2: (x0 + slot * (i + 1.5) - bw / 2).toFixed(1), y2: ny.toFixed(1),
          stroke: "var(--sk-dim, #8b877d)", "stroke-width": 1.5, "stroke-dasharray": "4 6",
          opacity: 0, class: "wf-conn" }, svg);
      }
      return { g, conn, cx, top, bot };
    });
    return { cols, ys };
  }

  // ───────────────────── ⑪ 스캐터 (이변량 분포) ─────────────────────
  // data: { points:[{x,y,label?,hi?}], xLabel?, yLabel? }
  // opts: { x0,x1,y0,y1, accent, hiColor, field? }
  function buildScatter(svg, data, opts) {
    const x0 = opts.x0 ?? 360;
    const x1 = opts.x1 ?? 1600;
    const y0 = opts.y0 ?? 320;
    const y1 = opts.y1 ?? 790;
    const pts = data.points;
    const xs = pts.map((p) => p.x);
    const ysv = pts.map((p) => p.y);
    const pad = 0.08;
    const xlo = Math.min(...xs); const xhi = Math.max(...xs);
    const ylo = Math.min(...ysv); const yhi = Math.max(...ysv);
    const xpd = (xhi - xlo || 1) * pad; const ypd = (yhi - ylo || 1) * pad;
    const SX = (v) => x0 + ((v - xlo + xpd) / ((xhi - xlo) + 2 * xpd)) * (x1 - x0);
    const SY = (v) => y1 - ((v - ylo + ypd) / ((yhi - ylo) + 2 * ypd)) * (y1 - y0);

    // 축 + 눈금 4개씩
    const axis = svgEl("g", { class: "sct-axis" }, svg);
    svgEl("line", { x1: x0, y1: y0 - 10, x2: x0, y2: y1, stroke: "var(--sk-hairline, rgba(236,233,226,0.2))", "stroke-width": 1.5 }, axis);
    svgEl("line", { x1: x0, y1: y1, x2: x1 + 10, y2: y1, stroke: "var(--sk-hairline, rgba(236,233,226,0.2))", "stroke-width": 1.5 }, axis);
    const fmtTick = (v, lov, hiv) =>
      Math.abs(hiv - lov) <= 8 ? v.toFixed(1) : Math.round(v).toLocaleString("ko-KR");
    for (let i = 0; i <= 3; i++) {
      const vx = xlo + ((xhi - xlo) * i) / 3;
      const vy = ylo + ((yhi - ylo) * i) / 3;
      const tx = svgEl("text", { x: SX(vx).toFixed(1), y: y1 + 32, "text-anchor": "middle",
        fill: "var(--sk-dim, #8b877d)", "font-size": 15, "font-weight": 600, class: "sk-text" }, axis);
      tx.textContent = fmtTick(vx, xlo, xhi);
      const ty = svgEl("text", { x: x0 - 16, y: (SY(vy) + 5).toFixed(1), "text-anchor": "end",
        fill: "var(--sk-dim, #8b877d)", "font-size": 15, "font-weight": 600, class: "sk-text" }, axis);
      ty.textContent = fmtTick(vy, ylo, yhi);
      if (i > 0) svgEl("line", { x1: x0, y1: SY(vy).toFixed(1), x2: x1, y2: SY(vy).toFixed(1),
        stroke: "var(--sk-grid, #232328)", "stroke-width": 1, "stroke-dasharray": "3 7" }, axis);
    }
    if (data.xLabel) {
      const t = svgEl("text", { x: x1, y: y1 + 64, "text-anchor": "end", fill: "var(--sk-muted, #a39e92)",
        "font-size": 16, "font-weight": 600, "letter-spacing": 1, class: "sk-text" }, axis);
      t.textContent = data.xLabel + " →";
    }
    if (data.yLabel) {
      const t = svgEl("text", { x: x0 - 14, y: y0 - 26, "text-anchor": "end", fill: "var(--sk-muted, #a39e92)",
        "font-size": 16, "font-weight": 600, "letter-spacing": 1, class: "sk-text" }, axis);
      t.textContent = "↑ " + data.yLabel;
    }
    // 대각 기준선 (x=y 스케일이 비슷할 때 — 변화 없음 선)
    let diag = null;
    if (opts.diagonal) {
      const lov = Math.max(xlo, ylo); const hiv = Math.min(xhi, yhi);
      if (hiv > lov) {
        diag = svgEl("line", { x1: SX(lov).toFixed(1), y1: SY(lov).toFixed(1),
          x2: SX(hiv).toFixed(1), y2: SY(hiv).toFixed(1), stroke: "var(--sk-dim, #8b877d)",
          "stroke-width": 1.5, "stroke-dasharray": "6 8", opacity: 0, class: "sct-diag" }, svg);
        prepDraw(diag);
      }
    }

    const field = opts.field || stageField();
    field.addSegment(x0, y1, x1, y1, 16);
    pts.forEach((p) => field.addCircle(SX(p.x), SY(p.y), 16));
    const dotLayer = svgEl("g", {}, svg);
    const plateLayer = svgEl("g", {}, svg);
    const items = pts.map((p) => {
      const cx = SX(p.x); const cy = SY(p.y);
      const c = p.hi ? opts.hiColor : opts.accent;
      const g = svgEl("g", { class: "sct-dot", opacity: 0, transform: `translate(${cx.toFixed(1)} ${cy.toFixed(1)})` }, dotLayer);
      svgEl("circle", { r: 10, fill: c, stroke: "var(--sk-ink, #141416)", "stroke-width": 2 }, g);
      svgEl("circle", { r: 10, fill: "none", stroke: c, "stroke-width": 1.5, opacity: 0.45, class: "sct-halo" }, g);
      let plate = null;
      if (p.label) {
        plate = plateLabel(plateLayer, [{ text: p.label, size: 16, weight: 700,
          fill: "var(--sk-text, #ece9e2)" }], { maxW: 200, cls: "sct-plate", padX: 10, padY: 6 });
        const r = field.place(plate.w, plate.h,
          slotCandidates(cx, cy, plate.w, plate.h, ["right", "above", "below", "left"]));
        plate.setPos(r.x, r.y);
      }
      return { g, plate, cx, cy };
    });
    return { items, diag, SX, SY };
  }

  // ───────────────────── ⑫ 히트맵 (행×열 강도) ─────────────────────
  // data: { rows:[], cols:[], values:[[..]], unit? }
  // opts: { x0,x1,yTop, pos, neg }  — 음수 있으면 diverging(neg↔pos), 아니면 pos 단색 스케일
  function buildHeatmap(svg, data, opts) {
    const rows = data.rows;
    const cols = data.cols;
    const V = data.values;
    const flat = V.flat();
    const lo = Math.min(...flat);
    const hi = Math.max(...flat);
    const diverging = lo < 0;
    const x0 = opts.x0 ?? 470;
    const x1 = opts.x1 ?? 1640;
    const gapC = 8;
    const cw = (x1 - x0 - gapC * (cols.length - 1)) / cols.length;
    const chMax = 96;
    const chH = Math.min(chMax, (480 - 8 * (rows.length - 1)) / rows.length);
    const blockH = rows.length * chH + (rows.length - 1) * 8;
    const yTop = opts.yTop ?? Math.max(330, 580 - blockH / 2);

    cols.forEach((c, ci) => {
      const t = svgEl("text", { x: (x0 + ci * (cw + gapC) + cw / 2).toFixed(1), y: yTop - 22,
        "text-anchor": "middle", fill: "var(--sk-muted, #a39e92)", "font-size": 16,
        "font-weight": 600, class: "sk-text" }, svg);
      t.textContent = c;
    });
    const cellLayer = svgEl("g", {}, svg);
    const cells = [];
    rows.forEach((r, ri) => {
      const y = yTop + ri * (chH + 8);
      const t = svgEl("text", { x: x0 - 22, y: (y + chH / 2 + 6).toFixed(1), "text-anchor": "end",
        fill: "var(--sk-muted, #a39e92)", "font-size": 18, "font-weight": 600, class: "sk-text" }, svg);
      t.textContent = r;
      cols.forEach((c, ci) => {
        const v = V[ri][ci];
        const x = x0 + ci * (cw + gapC);
        let fill; let alpha;
        if (diverging) {
          const m = Math.max(Math.abs(lo), Math.abs(hi)) || 1;
          alpha = 0.1 + 0.85 * (Math.abs(v) / m);
          fill = v >= 0 ? opts.pos : opts.neg;
        } else {
          alpha = 0.08 + 0.87 * ((v - lo) / ((hi - lo) || 1));
          fill = opts.pos;
        }
        const g = svgEl("g", { class: "hm-cell", opacity: 0 }, cellLayer);
        svgEl("rect", { x: x.toFixed(1), y: y.toFixed(1), width: cw.toFixed(1), height: chH.toFixed(1),
          rx: 5, fill, opacity: alpha.toFixed(2) }, g);
        if (alpha > 0.62) {
          const vt = svgEl("text", { x: (x + cw / 2).toFixed(1), y: (y + chH / 2 + 6).toFixed(1),
            "text-anchor": "middle", fill: "var(--sk-ink, #141416)", "font-size": 16,
            "font-weight": 800, class: "sk-text" }, g);
          vt.textContent = (v > 0 && diverging ? "+" : "") + v.toLocaleString("ko-KR");
        }
        cells.push({ g, ri, ci });
      });
    });
    return { cells, rows, cols };
  }

  // ───────────────────── ⑬ 간트 (일정 레인) ─────────────────────
  // data: { tasks:[{label, start:"YYYY-MM-DD", end, phase?}], today? }
  // opts: { x0,x1,yTop, colors(phase map), accent }
  function buildGantt(svg, data, opts) {
    const x0 = opts.x0 ?? 470;
    const x1 = opts.x1 ?? 1660;
    const parse = (s) => new Date(s + "T00:00:00Z").getTime();
    const tasks = data.tasks;
    let lo = Math.min(...tasks.map((t) => parse(t.start)));
    let hi = Math.max(...tasks.map((t) => parse(t.end)));
    if (data.today) { lo = Math.min(lo, parse(data.today)); hi = Math.max(hi, parse(data.today)); }
    const padMs = (hi - lo || 1) * 0.04;
    lo -= padMs; hi += padMs;
    const SX = (ms) => x0 + ((ms - lo) / (hi - lo)) * (x1 - x0);
    const rowH = tasks.length <= 5 ? 54 : 44;
    const gap = tasks.length <= 5 ? 36 : 24;
    const blockH = tasks.length * rowH + (tasks.length - 1) * gap;
    const yTop = opts.yTop ?? Math.max(330, 575 - blockH / 2);

    // 눈금 — 범위에 따라 월/분기/연 단위 자동 전환 (라벨 도배 방지)
    const gridG = svgEl("g", { class: "gn-grid" }, svg);
    const monthsSpan = (hi - lo) / (30.44 * 86400 * 1000);
    const stepM = monthsSpan <= 14 ? 1 : monthsSpan <= 42 ? 3 : 12;
    const multiYear = monthsSpan > 13;
    const d0 = new Date(lo);
    const tick = new Date(Date.UTC(d0.getUTCFullYear(), d0.getUTCMonth() + 1, 1));
    while (stepM > 1 && tick.getUTCMonth() % stepM !== 0) tick.setUTCMonth(tick.getUTCMonth() + 1);
    while (tick.getTime() < hi) {
      const x = SX(tick.getTime());
      svgEl("line", { x1: x.toFixed(1), y1: yTop - 34, x2: x.toFixed(1), y2: yTop + blockH + 16,
        stroke: "var(--sk-grid, #232328)", "stroke-width": 1 }, gridG);
      const t = svgEl("text", { x: x.toFixed(1), y: yTop - 44, "text-anchor": "middle",
        fill: "var(--sk-dim, #8b877d)", "font-size": 15, "font-weight": 600, class: "sk-text" }, gridG);
      t.textContent = multiYear
        ? `${String(tick.getUTCFullYear()).slice(2)}.${tick.getUTCMonth() + 1}`
        : (tick.getUTCMonth() + 1) + "월";
      tick.setUTCMonth(tick.getUTCMonth() + stepM);
    }

    const bars = tasks.map((task, i) => {
      const y = yTop + i * (rowH + gap);
      const bx = SX(parse(task.start));
      const bw = Math.max(10, SX(parse(task.end)) - bx);
      const color = (opts.colors && opts.colors[task.phase]) || opts.accent;
      const lab = svgEl("text", { x: x0 - 24, y: (y + rowH / 2 + 6).toFixed(1), "text-anchor": "end",
        fill: "var(--sk-text, #ece9e2)", "font-size": 18, "font-weight": 600, class: "sk-text gn-lab", opacity: 0 }, svg);
      lab.textContent = task.label;
      const g = svgEl("g", { class: "gn-bar", opacity: 0 }, svg);
      svgEl("rect", { x: bx.toFixed(1), y, width: bw.toFixed(1), height: rowH, rx: 6,
        fill: color, opacity: 0.85 }, g);
      g.dataset.ox = String(bx);
      // 기간 텍스트 (막대 안 또는 우측)
      const dur = monthsSpan > 13
        ? `${task.start.slice(2, 7).replace("-", ".")}–${task.end.slice(2, 7).replace("-", ".")}`
        : `${task.start.slice(5).replace("-", ".")}–${task.end.slice(5).replace("-", ".")}`;
      const inside = bw > 150;
      const dt = svgEl("text", { x: (inside ? bx + 14 : bx + bw + 12).toFixed(1),
        y: (y + rowH / 2 + 5).toFixed(1), fill: inside ? "var(--sk-ink, #141416)" : "var(--sk-dim, #8b877d)",
        "font-size": 14, "font-weight": 700, class: "sk-text gn-dur", opacity: 0 }, svg);
      dt.textContent = dur;
      return { g, lab, dt };
    });

    // 오늘 라인
    let todayG = null;
    if (data.today) {
      const x = SX(parse(data.today));
      todayG = svgEl("g", { class: "gn-today", opacity: 0 }, svg);
      svgEl("line", { x1: x.toFixed(1), y1: yTop - 56, x2: x.toFixed(1), y2: yTop + blockH + 16,
        stroke: opts.accent, "stroke-width": 2, "stroke-dasharray": "5 6" }, todayG);
      const tp = plateLabel(todayG, [{ text: "오늘", size: 14, weight: 800, fill: opts.accent, ls: "2" }],
        { padX: 10, padY: 5 });
      tp.setPos(x - tp.w / 2, yTop - 56 - tp.h - 4);
    }
    return { bars, todayG };
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
    buildSerpentineTimeline,
    buildVerticalTimeline,
    buildMetroTimeline,
    buildSlopeChart,
    buildDonut,
    buildStackedBars,
    buildWaterfall,
    buildScatter,
    buildHeatmap,
    buildGantt,
    buildBarPanels,
    buildCandleChart,
    buildBasemap,
    buildNetwork,
    buildGeoScene,
    buildMarketCards,
    buildProfileCards,
  };
})();
