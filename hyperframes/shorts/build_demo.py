"""씬 플랜 + 아트 디렉션 → 쇼츠 데모 컴포지션 (Phase 3 스타일 데모).

씬킷(`collage_kit.js`)이 실번들 데이터로 실제 조판되는지 확인하는 데모.
전체 22문장(110초)이 아니라 **모션 어휘를 다 보여 주는 앞부분 4씬**만 만든다
(계획 §9 Phase 3 합격선: 10~15초 스타일 데모).

씬 구성:
    HOOK      랜섬 헤드라인 글자 stagger + 스탬프 쾅
    CONTEXT   종이 카드 place + 테이프 + 대형 자막
    ACTORS    인물 컷아웃 bottom-in stagger + 붉은 실 draw-on
    EVIDENCE  차트 플레이트 (bar) + 형광펜 강조

사용::

    python hyperframes/shorts/build_demo.py
    python hyperframes/shorts/build_demo.py --guides    # safe area 오버레이
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SHEET_JSON = REPO_ROOT / "design_sheets" / "shorts_collage_v1.json"
PLAN_JSON = HERE / "scene_plan.json"
AD_JSON = HERE / "art_direction.json"
LIB_MANIFEST = REPO_ROOT / "assets" / "library" / "library_manifest.json"
OUT_HTML = HERE / "index.html"

W, H = 1080, 1920
PACE_OVERHEAD, PACE_PER_CHAR = 0.225, 0.1298


def esc(s) -> str:
    return html.escape(str(s or ""))


def est(text: str) -> float:
    return max(1.5, min(9.0, PACE_OVERHEAD + PACE_PER_CHAR * len(text)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--guides", action="store_true")
    ap.add_argument("--scenes", type=int, default=4, help="앞에서 몇 씬까지")
    args = ap.parse_args()

    from schemas.models import ArtDirection, DesignSheet

    sheet = DesignSheet(**json.loads(SHEET_JSON.read_text(encoding="utf-8")))
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ad = ArtDirection(**json.loads(AD_JSON.read_text(encoding="utf-8")))
    lib = {p["person_id"]: p
           for p in json.loads(LIB_MANIFEST.read_text(encoding="utf-8"))["people"]}

    scenes = plan["scenes"][: args.scenes]

    # --- 자막 큐 타이밍 (문장 길이 비례, 실측 상수) ----------------------
    cues, t = [], 0.6
    for s in scenes:
        for line in s["lines"]:
            cues.append({"t": round(t, 3), "text": line})
            t += est(line) + 0.28
    total = round(t + 0.8, 2)

    # --- 씬 시작 시각 -----------------------------------------------------
    starts, acc = [], 0.6
    for s in scenes:
        starts.append(round(acc, 3))
        acc += sum(est(x) + 0.28 for x in s["lines"])

    css_vars = sheet.to_css_vars()
    css_vars["--paper-crumpled"] = sheet.resolve_paper_tone(ad.paper_tone)
    root_vars = "\n      ".join(f"{k}: {v};" for k, v in sorted(css_vars.items()))

    headline = plan.get("headline", "")
    cast = [c for c in ad.cast if c.person_id][:4]
    cast_js = json.dumps(
        [{"id": c.person_id,
          "name": lib.get(c.person_id, {}).get("name_ko", c.label),
          "role": c.role, "tilt": c.tilt_deg}
         for c in cast],
        ensure_ascii=False,
    )

    # EVIDENCE 씬의 bar 차트 (있으면)
    chart = None
    for s in scenes:
        if (s.get("chart") or {}).get("type") == "bar":
            chart = s["chart"]
            break
    chart_js = json.dumps(chart, ensure_ascii=False) if chart else "null"

    # 크레딧 — CC BY/BY-SA 는 저작자 표기 의무 (C9). URL 이 아니라 이름만 싣는다.
    #: 사람 이름이 아니라 Commons 상용구인 값들 — 크레딧에 실으면 의미가 없다.
    CREDIT_NOISE = {"own work", "self-photographed", "unknown", "미상", ""}

    def credit_name(pid: str) -> str:
        src = (lib.get(pid) or {}).get("source", {}) or {}
        if "CC" not in (src.get("license") or ""):
            return ""                      # PD/CC0 는 표기 의무 없음
        name = (src.get("credit") or "").strip()
        if name.startswith("http") or name.lower() in CREDIT_NOISE:
            return ""
        return name.split(" derivative")[0].strip()[:34]

    credits = sorted({credit_name(c.person_id) for c in cast} - {""})

    doc = f"""<!DOCTYPE html>
<!-- 쇼츠 콜라주 데모 — build_demo.py 자동 생성. 수정 금지: 빌더를 고치고 재실행할 것.
     seed={ad.seed} / paper_tone={ad.paper_tone} / bg={ad.bg_grammar} -->
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width={W}, height={H}">
<title>{esc(headline)}</title>
<link rel="stylesheet" href="../briefing/assets/noto_serif_kr.css">
<link rel="stylesheet" href="assets/collage_kit.css">
<script src="../briefing/assets/gsap.min.js"></script>
<script src="assets/collage_kit.js"></script>
<style>
  @font-face {{ font-family:"Pretendard Variable";
    src:url("../briefing/assets/fonts/PretendardVariable.woff2") format("woff2-variations");
    font-weight:45 920; font-display:block; }}
  :root {{
      {root_vars}
  }}
</style></head>
<body>
<div id="root" class="clip" data-composition-id="shorts-demo"
     data-start="0" data-duration="{total}" data-track-index="0"
     data-width="{W}" data-height="{H}">

  <img class="paper-bg" src="assets/paper_crumpled_1080x1920.png" alt="">
  <div class="paper-tone"></div>
  <div class="stage" id="stage"></div>
  <svg class="strings" id="strings" viewBox="0 0 {W} {H}"></svg>
  <div class="grain"></div>
  <div class="guides"></div>
  <div class="credit">{esc(" · ".join(credits[:3]))}</div>
</div>

<script>
(function () {{
  const K = CollageKit;
  const stage = document.getElementById("stage");
  const strings = document.getElementById("strings");
  const SEED = "{ad.seed}";
  const STARTS = {json.dumps(starts)};
  const CAST = {cast_js};
  const CHART = {chart_js};

  if (new URLSearchParams(location.search).has("guides")) {{
    document.body.classList.add("show-guides");
  }}

  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true, defaults: {{ ease: "power2.out" }} }});

  // ============================================================ S01 HOOK
  const rh = K.RansomHeadline(stage, {json.dumps(headline, ensure_ascii=False)}, {{
    seed: {ad.ransom_seed}, start: 0, duration: 6, track: 6,
  }});
  rh.root.style.left = "var(--safe-left)";
  rh.root.style.top = "300px";
  rh.root.style.width = "820px";
  K.ransomIn(tl, rh, STARTS[0]);

  const stamp = K.StampLabel(stage, "confirm", {{
    x: 620, y: 700, rot: -7, start: 0, duration: 6, track: 7,
  }});
  K.stampIn(tl, stamp, STARTS[0] + 1.1);
  // 헤드라인은 CONTEXT 시작 전에 위로 물린다 — 안 그러면 다음 씬을 덮는다
  K.sceneOut(tl, [rh.root, stamp], STARTS[1] - 0.4);

  // ============================================================ S02 CONTEXT
  const panel = K.PaperPanel(stage, {{
    x: 90, y: 560, w: 800, rot: -1.2, tone: "paper_card",
    start: 0, duration: 8, track: 3,
  }});
  panel.innerHTML = '<div class="deck">'
    + {json.dumps((plan['scenes'][1].get('deck') or plan.get('headline', ''))[:120] if len(plan['scenes']) > 1 else '', ensure_ascii=False)}
    + "</div>";
  const tape1 = K.TapeStrip(stage, {{ x: 150, y: 538, w: 190, rot: -5 }});
  const tape2 = K.TapeStrip(stage, {{ x: 700, y: 546, w: 160, rot: 4 }});
  K.panelIn(tl, panel, STARTS[1]);
  tl.from([tape1, tape2], {{ opacity: 0, duration: 0.2 }}, STARTS[1] + 0.12);
  K.sceneOut(tl, [panel, tape1, tape2], STARTS[2] - 0.4);

  // ============================================================ S03 ACTORS
  const nodes = [], pts = [];
  // 2×2 배치 — safe area(상220/하350/좌60/우140) 안에 가둔다.
  // 아랫줄 bottom 은 자막 상단(하단 안전선 + 자막 높이)보다 위여야 이름표가 안 겹친다.
  const COLS = [70, 530], ROWS = [1030, 620];
  CAST.forEach(function (c, i) {{
    const w = 400;
    const x = COLS[i % 2];
    const bottom = ROWS[Math.floor(i / 2)];
    const n = K.CutoutActor(stage, {{
      src: "assets/cast/" + c.id + ".png",
      x: x, bottom: bottom, w: w, tilt: c.tilt,
      tag: c.name, role: c.role,
      start: 0, duration: 10, track: 5 + i,
    }});
    nodes.push(n);
    pts.push({{ x: x + w / 2, y: {H} - bottom - 120 }});
  }});
  K.actorsIn(tl, nodes, STARTS[3], SEED, 7);

  // 붉은 실 — 번들 stakeholder_map 의 edge 가 근거 (G4)
  const paths = [];
  for (let i = 0; i + 1 < pts.length; i++) {{
    paths.push(K.StringConnector(strings, pts[i], pts[i + 1], {{ seed: SEED }}));
  }}
  K.drawOn(tl, paths, STARTS[3] + 0.9, 0.12);
  

  // ============================================================ S04 EVIDENCE (bar)
  if (CHART) {{
    const cp = K.PaperPanel(stage, {{
      x: 80, y: 1180, w: 800, rot: 0.8, tone: "paper_card",
      start: 0, duration: 8, track: 4,
    }});
    let rows = '<div class="chart-title">' + CHART.title + "</div>";
    const max = Math.max.apply(null, CHART.data.map(function (d) {{ return d.value; }}));
    CHART.data.forEach(function (d, i) {{
      rows += '<div class="bar-row"><span class="bl">' + d.label + "</span>"
        + '<span class="bw"><span class="bt" style="width:'
        + (d.value / max * 100) + '%"></span></span>'
        + '<span class="bv">' + d.value + "</span></div>";
    }});
    cp.innerHTML = rows;
    K.panelIn(tl, cp, STARTS[2]);
    // 정보 요소 = Material decelerate (물성과 섞지 않는다 §1.4)
    tl.from(cp.querySelectorAll(".bt"),
      {{ scaleX: 0, transformOrigin: "0% 50%", duration: 0.55,
         stagger: 0.11, ease: "power2.out" }}, STARTS[2] + 0.3);
    K.sceneOut(tl, [cp], STARTS[3] - 0.4);
  }}



  // ============================================================ 자막 · 카메라
  const sub = K.SubtitleBar(document.getElementById("root"));
  K.subtitleCues(tl, sub, {json.dumps(cues, ensure_ascii=False)});
  K.pushIn(tl, stage, 0, {total});

  window.__timelines["shorts-demo"] = tl;
}})();
</script>
<style>
  .deck {{ font-family:"Noto Serif KR",serif; font-size:44px; font-weight:500;
    line-height:1.5; color:var(--ink-base); word-break:keep-all; }}
  .chart-title {{ font:var(--type-kicker); color:var(--ink-soft);
    margin-bottom:8px; line-height:1.3; }}
  .bar-row {{ display:flex; align-items:center; gap:16px; margin-top:24px; }}
  .bl {{ width:190px; flex:0 0 190px; font-size:30px; font-weight:700; }}
  .bw {{ flex:1 1 auto; display:block; }}
  .bt {{ height:36px; background:var(--mark-pen); display:block; }}
  .bv {{ flex:0 0 auto; font-size:32px; font-weight:900;
    font-variant-numeric:tabular-nums; }}
</style>
</body></html>
"""

    OUT_HTML.write_text(doc, encoding="utf-8")
    print(f"[html] {OUT_HTML}")
    print(f"  씬 {len(scenes)} / 자막 {len(cues)}큐 / 길이 {total}초")
    print(f"  cast {len(cast)}인  seed={ad.seed}  paper={ad.paper_tone}")
    print(f"  차트 {'bar 포함' if chart else '없음'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
