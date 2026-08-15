"""스타일 프리뷰 시트 렌더러 (계획 §6.0.1 승인 게이트의 표면).

**영상을 만들기 전에** 이 편의 조판 선택을 한 장으로 보여 준다. 사용자는 이 시트만
보고 승인 / 리롤 / 항목 조정을 결정한다 — 정적 렌더라 초 단위·무비용이고, 승인된
아트 디렉션이 곧 렌더 입력이라 **검수한 것과 렌더되는 것이 정의상 일치**한다.

시트에 실리는 것 (17 §0.9 플레이트 ID 부여):
    P 01 팔레트 / T 01 타이포 / W 01 여백 / M 01 모션
    B    배경 문법 (선택분 강조)
    CAST 투입 인물 + **미보유 인물 경고** (§3.0.1 — 인물 승인도 이 게이트에서)
    S    씬 플랜 스토리보드

사용::

    python hyperframes/shorts/render_preview_sheet.py
    python hyperframes/shorts/render_preview_sheet.py --html-only
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
OUT_HTML = HERE / "preview_sheet.html"
OUT_PNG = HERE / "preview_sheet.png"
THUMBS = HERE / "thumbs"

WIDTH = 1240
CHROMIUM_FALLBACK = "/opt/pw-browsers/chromium"

#: §1.6 배경 문법 후보군 (B 01~B 06)
BG_GRAMMARS = [
    ("sunburst", "선버스트"), ("stage_curtain", "무대 커튼"),
    ("file_desk", "서류 책상"), ("paper_map", "종이 지도"),
    ("montage_wall", "사진 벽"), ("plain_grain", "정적 종이"),
]

SCENE_KO = {
    "HOOK": "훅", "CONTEXT": "맥락", "ACTORS": "인물",
    "EVIDENCE": "근거", "TURN": "반전", "CLOSING": "맺음",
}


def esc(s: str) -> str:
    return html.escape(str(s or ""))


def build_html(sheet, plan: dict, cast: dict, ad) -> str:
    css_vars = sheet.to_css_vars()
    root_vars = "\n      ".join(f"{k}: {v};" for k, v in sorted(css_vars.items()))

    # --- P 01 팔레트 -----------------------------------------------------
    swatches = "".join(
        f'<div class="sw"><div class="chip" style="background:{v}"></div>'
        f'<div class="k">{esc(k)}</div><div class="h">{esc(v)}</div></div>'
        for k, v in sheet.palette.items()
    )

    # --- T 01 타이포 -----------------------------------------------------
    typo = "".join(
        f'<div class="ty"><div class="aa" style="font:{v}">Aa 가나</div>'
        f'<div class="k">{esc(k)}</div></div>'
        for k, v in sheet.typography.items()
    )

    # --- W 01 여백 / M 01 모션 -------------------------------------------
    def numrows(d: dict) -> str:
        def fmt(v) -> str:
            # `:g` 는 큰 정수를 과학표기로 바꾼다 (seed 938543205 -> 9.38543e+08).
            # 시드는 리롤 이력 추적의 키라 정확한 자릿수로 보여야 한다.
            if isinstance(v, int) or (isinstance(v, float) and float(v).is_integer()):
                return f"{int(v):,}"
            return f"{v:g}"

        return "".join(
            f'<div class="nr"><span class="k">{esc(k)}</span>'
            f'<span class="v">{fmt(v)}</span></div>' for k, v in d.items()
        )

    # --- B 배경 문법 ------------------------------------------------------
    chosen = ad.bg_grammar
    bgs = "".join(
        f'<div class="bg{" on" if key == chosen else ""}">'
        f'<span class="id">B {i:02d}</span>{esc(ko)}</div>'
        for i, (key, ko) in enumerate(BG_GRAMMARS, 1)
    )

    # --- CAST -------------------------------------------------------------
    have_cards = "".join(
        f'<div class="p"><img src="{esc(p["img"])}" alt="">'
        f'<div class="n">{esc(p["name"])}</div>'
        f'<div class="r"><span class="dot" style="background:{esc(p.get("accent"))}"></span>'
        f'{esc(p.get("shadow"))}</div></div>'
        for p in cast["have"]
    )
    miss_cards = "".join(
        f'<div class="p miss"><div class="ph">?</div>'
        f'<div class="n">{esc(m["name"])}</div><div class="r">{esc(m["role"])}</div></div>'
        for m in cast["missing"]
    )
    miss_block = (
        f'<div class="warn"><b>미보유 인물 {len(cast["missing"])}인</b> — 승인하시면 '
        f'수집·가공 후 라이브러리에 영구 등록됩니다. 미승인 시 해당 씬은 이름 태그로 '
        f'대체 조판됩니다.</div><div class="cast">{miss_cards}</div>'
        if cast["missing"] else
        '<div class="ok">미보유 인물 없음 — 전원 라이브러리 보유.</div>'
    )

    # --- S 씬 플랜 --------------------------------------------------------
    cards = []
    for i, s in enumerate(plan["scenes"], 1):
        badge = ""
        if s.get("chart"):
            badge = f'<span class="tag">{esc(s["chart"]["type"])}</span>'
        if s["scene"] == "TURN":
            badge = (f'<span class="tag">{esc(s.get("label_a"))}</span>'
                     f'<span class="vs">vs</span>'
                     f'<span class="tag">{esc(s.get("label_b"))}</span>')
        lines = "".join(f"<li>{esc(t)}</li>" for t in s["lines"])
        # 씬킷이 실제로 조판한 썸네일 (build_scene_thumbs.py). 없으면 자리표시.
        thumb_path = THUMBS / f"{s['id']}.png"
        thumb = (
            f'<img class="th" src="thumbs/{esc(s["id"])}.png" alt="">'
            if thumb_path.is_file()
            else '<div class="th th-none">조판<br>미생성</div>'
        )
        cards.append(
            f'<div class="sc">{thumb}<div class="sc-body">'
            f'<div class="sh"><span class="id">S {i:02d}</span>'
            f'<b>{esc(SCENE_KO.get(s["scene"], s["scene"]))}</b>'
            f'<span class="sid">{esc(s["id"])}</span>{badge}</div>'
            f'<ul>{lines}</ul></div></div>'
        )

    return f"""<!DOCTYPE html>
<!-- 스타일 프리뷰 시트 — render_preview_sheet.py 자동 생성. 수정 금지. -->
<html lang="ko"><head><meta charset="utf-8">
<title>스타일 프리뷰 — {esc(plan.get('report_id'))}</title>
<link rel="stylesheet" href="../briefing/assets/noto_serif_kr.css">
<style>
  @font-face {{ font-family:"Pretendard Variable";
    src:url("../briefing/assets/fonts/PretendardVariable.woff2") format("woff2-variations");
    font-weight:45 920; font-display:block; }}
  :root {{
      {root_vars}
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:{WIDTH}px; background:var(--paper-crumpled);
    font-family:"Pretendard Variable",Pretendard,sans-serif; color:var(--ink-base);
    -webkit-font-smoothing:antialiased; padding:28px 30px 40px; }}
  .hd {{ display:flex; justify-content:space-between; align-items:flex-end;
    border-bottom:3px solid var(--ink-base); padding-bottom:12px; }}
  .nm {{ font-family:"Noto Serif KR",serif; font-size:38px; font-weight:700;
    letter-spacing:.02em; }}
  .sub {{ font-size:15px; color:var(--ink-soft); margin-top:4px; letter-spacing:.04em; }}
  .meta {{ text-align:right; font-size:14px; color:var(--ink-soft); line-height:1.7; }}
  .stats {{ display:flex; gap:34px; margin:18px 0 6px; }}
  .st b {{ display:block; font-size:34px; font-weight:900; line-height:1; }}
  .st span {{ font-size:12px; color:var(--ink-soft); letter-spacing:.09em; }}
  h2 {{ font-size:13px; letter-spacing:.16em; color:var(--ink-soft); font-weight:700;
    margin:26px 0 10px; display:flex; align-items:center; gap:10px; }}
  h2 .id {{ background:var(--ink-base); color:var(--paper-card); font-size:11px;
    padding:2px 7px; border-radius:3px; letter-spacing:.08em; }}
  .card {{ background:var(--paper-card); padding:16px 18px;
    box-shadow:7px 8px 0 rgba(28,26,23,.14), 1px 2px 3px rgba(28,26,23,.24); }}
  .pal {{ display:grid; grid-template-columns:repeat(9,1fr); gap:9px; }}
  .chip {{ height:44px; border:1px solid rgba(28,26,23,.28); }}
  .sw .k {{ font-size:10px; margin-top:4px; word-break:break-all; line-height:1.25; }}
  .sw .h {{ font-size:9px; color:var(--ink-soft); font-variant-numeric:tabular-nums; }}
  .typ {{ display:flex; gap:26px; flex-wrap:wrap; align-items:flex-end; }}
  .aa {{ line-height:1.1; }}
  .ty .k {{ font-size:10px; color:var(--ink-soft); margin-top:6px; }}
  .two {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  .nr {{ display:flex; justify-content:space-between; font-size:12px;
    padding:3px 0; border-bottom:1px dotted rgba(28,26,23,.18); }}
  .nr .v {{ font-weight:700; font-variant-numeric:tabular-nums; }}
  .bgs {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .bg {{ font-size:12px; padding:7px 12px; border:1px dashed rgba(28,26,23,.35);
    color:var(--ink-soft); display:flex; gap:7px; align-items:center; }}
  .bg.on {{ background:var(--ink-base); color:var(--paper-card); border-style:solid;
    font-weight:700; }}
  .bg .id {{ font-size:9px; opacity:.7; }}
  .cast {{ display:flex; gap:11px; flex-wrap:wrap; }}
  .p {{ width:96px; text-align:center; }}
  .p img {{ width:96px; height:120px; object-fit:cover; object-position:top center;
    background:var(--paper-base); border:1px solid rgba(28,26,23,.2); }}
  .p .ph {{ width:96px; height:120px; display:flex; align-items:center;
    justify-content:center; font-size:34px; color:#fff;
    background:var(--stamp-unverified); border:1px solid rgba(28,26,23,.2); }}
  .p .n {{ font-size:11px; margin-top:4px; line-height:1.3; }}
  .p .r {{ font-size:9px; color:var(--ink-soft); }}
  .warn {{ background:var(--stamp-unverified); color:#fff; font-size:12px;
    padding:9px 12px; margin-bottom:11px; line-height:1.5; }}
  .ok {{ font-size:12px; color:var(--ink-soft); }}
  .sc {{ background:var(--paper-card); padding:11px 13px; margin-bottom:9px;
    box-shadow:5px 6px 0 rgba(28,26,23,.12);
    display:flex; gap:14px; align-items:flex-start; }}
  .sc-body {{ flex:1 1 auto; min-width:0; }}
  .th {{ flex:0 0 auto; width:104px; height:185px; object-fit:cover;
    border:1px solid rgba(28,26,23,.28); background:var(--paper-base); }}
  .th-none {{ flex:0 0 auto; width:104px; height:185px;
    border:1px dashed rgba(28,26,23,.32); color:var(--ink-soft);
    font-size:11px; display:flex; align-items:center; justify-content:center;
    text-align:center; line-height:1.5; }}
  .sh {{ display:flex; align-items:center; gap:9px; margin-bottom:5px; }}
  .sh .id {{ background:var(--ink-base); color:var(--paper-card); font-size:10px;
    padding:2px 6px; }}
  .sh b {{ font-size:15px; }}
  .sh .sid {{ font-size:10px; color:var(--ink-soft); letter-spacing:.06em; }}
  .tag {{ font-size:10px; background:var(--mark-highlighter); padding:2px 7px; }}
  .vs {{ font-size:10px; color:var(--ink-soft); }}
  .sc ul {{ list-style:none; }}
  .sc li {{ font-size:12px; line-height:1.6; color:var(--ink-soft);
    padding-left:12px; position:relative; word-break:keep-all; }}
  .sc li::before {{ content:"·"; position:absolute; left:2px; }}
  .dot {{ display:inline-block; width:10px; height:10px; margin-right:4px;
    border:1px solid rgba(28,26,23,.35); vertical-align:-1px; }}
  .ft {{ margin-top:24px; border-top:2px solid var(--ink-base); padding-top:10px;
    font-size:12px; color:var(--ink-soft); display:flex; justify-content:space-between; }}
</style></head><body>

<div class="hd">
  <div><div class="nm">{esc(sheet.display_name)}</div>
    <div class="sub">STYLE PREVIEW · {esc(sheet.sheet_id)} · seed {ad.seed} · reroll {ad.reroll_count} · {"승인됨" if ad.approved else "승인 전 렌더 금지"}</div></div>
  <div class="meta">{esc(plan.get('report_id'))}<br>
    {sheet.width}×{sheet.height} @ {sheet.fps}fps</div>
</div>

<div class="stats">
  <div class="st"><b>{len(plan['scenes'])}</b><span>SCENES</span></div>
  <div class="st"><b>{plan['sentence_count']}</b><span>SENTENCES</span></div>
  <div class="st"><b>{plan['estimated_sec']:.0f}s</b><span>EST. LENGTH</span></div>
  <div class="st"><b>{len(cast['have'])}</b><span>CAST READY</span></div>
  <div class="st"><b>{len(cast['missing'])}</b><span>CAST MISSING</span></div>
</div>

<h2><span class="id">P 01</span>PALETTE · {len(sheet.palette)} tokens</h2>
<div class="card pal">{swatches}</div>

<h2><span class="id">T 01</span>TYPOGRAPHY</h2>
<div class="card typ">{typo}</div>

<div class="two">
  <div><h2><span class="id">W 01</span>SPACING</h2>
    <div class="card">{numrows(sheet.spacing)}</div></div>
  <div><h2><span class="id">M 01</span>MOTION</h2>
    <div class="card">{numrows(sheet.motion)}</div></div>
</div>

<h2><span class="id">V 01</span>SEED VARIATION · 리롤하면 이 값들이 바뀝니다</h2>
<div class="card two">
  <div>{numrows({
      "seed": ad.seed, "reroll_count": ad.reroll_count,
      "tape_layout": ad.tape_layout,
  })}</div>
  <div><div class="nr"><span class="k">paper_tone</span>
      <span class="v">{esc(ad.paper_tone)}
      <span class="dot" style="background:{sheet.resolve_paper_tone(ad.paper_tone)}"></span></span></div>
    <div class="nr"><span class="k">sunburst_rotation_deg</span>
      <span class="v">{ad.sunburst_rotation_deg:.0f}°</span></div>
    <div class="nr"><span class="k">ransom_seed</span>
      <span class="v">{ad.ransom_seed:,}</span></div></div>
</div>

<h2><span class="id">B</span>BACKGROUND GRAMMAR</h2>
<div class="bgs">{bgs}</div>

<h2><span class="id">CAST</span>인물 자산</h2>
<div class="card">
  <div class="cast">{have_cards}</div>
  <div style="margin-top:13px">{miss_block}</div>
</div>

<h2><span class="id">S</span>SCENE PLAN</h2>
{''.join(cards)}

<div class="ft"><span>승인 / 리롤(시드 재추첨) / 항목 조정 — 블록 ID 로 지정</span>
  <span>계획 §6.0.1 style_preview_review</span></div>
</body></html>
"""


def collect_cast(ad) -> dict:
    """씬 플랜의 인물 ↔ 라이브러리 매칭 (§3.0.1)."""
    lib = json.loads(LIB_MANIFEST.read_text(encoding="utf-8"))["people"]
    by_id = {p["person_id"]: p for p in lib}

    have, missing = [], []
    for c in ad.cast:
        p = by_id.get(c.person_id)
        if p:
            have.append({"name": p["name_ko"],
                         "img": "../../" + p["variants"][0]["path"],
                         "shadow": f"{c.shadow_mode}+{c.shadow_fill}",
                         "accent": c.accent})
        else:
            missing.append({"name": c.label, "role": c.role})

    return {"have": have, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html-only", action="store_true")
    args = ap.parse_args()

    from schemas.models import DesignSheet

    from schemas.models import ArtDirection

    sheet = DesignSheet(**json.loads(SHEET_JSON.read_text(encoding="utf-8")))
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    if not AD_JSON.exists():
        print(f"error: {AD_JSON} 없음 — build_art_direction.py 를 먼저 실행하십시오.")
        return 1
    ad = ArtDirection(**json.loads(AD_JSON.read_text(encoding="utf-8")))
    cast = collect_cast(ad)

    OUT_HTML.write_text(build_html(sheet, plan, cast, ad), encoding="utf-8")
    print(f"[html] {OUT_HTML}")
    print(f"  시트 {sheet.display_name} / 토큰 palette {len(sheet.palette)} "
          f"type {len(sheet.typography)} space {len(sheet.spacing)} motion {len(sheet.motion)}")
    print(f"  씬 {len(plan['scenes'])} / 문장 {plan['sentence_count']} / "
          f"{plan['estimated_sec']}초")
    print(f"  인물 보유 {len(cast['have'])} / 미보유 {len(cast['missing'])}")
    if args.html_only:
        return 0

    from playwright.sync_api import Error as PWError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except PWError:
            browser = pw.chromium.launch(executable_path=CHROMIUM_FALLBACK)
        page = browser.new_page(viewport={"width": WIDTH, "height": 1600},
                                device_scale_factor=1)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(OUT_HTML.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(350)
        page.screenshot(path=str(OUT_PNG), full_page=True)
        h = page.evaluate("document.body.scrollHeight")
        browser.close()

    if errors:
        print(f"[warn] page errors: {errors}")
    print(f"[png ] {OUT_PNG}  ({WIDTH}x{h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
