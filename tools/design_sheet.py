"""장르 디자인 시트 — 규칙에서 생성한 거울(v7.4.0 전쟁사 W5, back_and_forth D-0307 §1-2·D-0607 §2-3).

    python tools/design_sheet.py war_history [--out docs/handoff/reports/design_sheet_war_history] [--no-terrain3d]

한 장짜리 HTML = ① 규칙 값 표(rules/video_rules.yaml 에서 읽음 — 손으로 옮기지 않는다) ② 실제 엔진 견본 컷
(sketch.war.scene.WarScene·engine.glyphs·schemas.era_date — 영상과 같은 코드) ③ 반례(실제 검증기가 내는 오류 문구).
규칙이 바뀌면 다시 만든다. 시험 tests/test_design_sheet.py 가 "표의 값 = 규칙 파일 값"을 잰다.
견본 컷을 못 만들면 오류로 끝난다(빈 칸으로 두지 않는다, 15 P6). --no-terrain3d 는 그 사실을 시트에 적는다.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import cairo  # noqa: E402
from PIL import Image  # noqa: E402

from rules import load_rules  # noqa: E402

GENRES = ("war_history",)
DEFAULT_OUT = REPO / "docs" / "handoff" / "reports" / "design_sheet_war_history"

# 표에 싣는 규칙 키(점 경로). 값은 load_rules() 를 거쳐 읽고, 시험은 YAML 원문과 대조한다.
WAR_RULE_KEYS: tuple[tuple[str, str], ...] = (
    ("부호 세트", "war_history.symbol_sets.ancient.units"),
    ("부호 세트", "war_history.symbol_sets.ancient.shapes"),
    ("부호 세트", "war_history.symbol_sets.ancient.glyphs"),
    ("부호 세트", "war_history.symbol_sets.early_modern.units"),
    ("부호 세트", "war_history.symbol_sets.early_modern.shapes"),
    ("부호 세트", "war_history.symbol_sets.modern.units"),
    ("부호 세트", "war_history.symbol_sets.modern.shapes"),
    ("부호 세트", "war_history.symbol_set_by_year.ancient_max"),
    ("부호 세트", "war_history.symbol_set_by_year.early_modern_max"),
    ("입체", "war_history.symbol_sets.depth.side_ratio"),
    ("입체", "war_history.symbol_sets.depth.side_dark"),
    ("입체", "war_history.symbol_sets.depth.shadow_alpha"),
    ("입체", "war_history.symbol_sets.depth.shadow_px"),
    ("입체", "war_history.symbol_sets.depth.rim_alpha"),
    ("입체", "war_history.symbol_sets.rank_grid.shapes"),
    ("입체", "war_history.symbol_sets.rank_grid.gap_px"),
    ("픽토그램", "war_history.symbol_sets.glyph.size_px"),
    ("픽토그램", "war_history.symbol_sets.glyph.halo_px"),
    ("픽토그램", "war_history.symbol_sets.glyph.alpha"),
    ("휘장", "war_history.faction_badge.emblem.legend_px"),
    ("휘장", "war_history.faction_badge.emblem.block_px"),
    ("휘장", "war_history.faction_badge.emblem.alpha"),
    ("휘장", "war_history.faction_badge.emblem.badge_frac"),
    ("휘장", "war_history.faction_badge.emblem.badge_ink"),
    ("날짜 표기", "hud.date_badge.era_format.bce_prefix"),
    ("날짜 표기", "hud.date_badge.era_format.day"),
    ("날짜 표기", "hud.date_badge.era_format.circa"),
    ("날짜 표기", "hud.date_badge.era_format.period_years"),
    ("날짜 표기", "hud.date_badge.era_format.roman_suffix"),
    ("증거 층", "war_history.evidence.required_layers.ancient"),
    ("증거 층", "war_history.evidence.required_layers.early_modern"),
    ("증거 층", "war_history.evidence.required_layers.modern"),
    ("증거 층", "war_history.period_art.contemporary_gap_years"),
    ("증거 층", "war_history.period_art.labels.contemporary"),
    ("증거 층", "war_history.period_art.labels.later"),
    ("증거 층", "war_history.evidence.toponymy_confidence"),
    ("사상자", "war_history.casualty.band_required"),
    ("사상자", "war_history.casualty.band_labels.ancient_range"),
    ("사상자", "war_history.casualty.band_labels.modern_estimate"),
    ("권리", "war_history.rights.allowed_licenses"),
    ("권리", "war_history.rights.disallowed_tags"),
    ("지도 테마", "sketch.war.default_theme"),
    ("지도 테마", "geo.themes.relief.map.label_contrast_fix"),
    ("terrain3d", "sketch.war.terrain3d.exaggeration"),
    ("terrain3d", "sketch.war.terrain3d.camera.elev_deg"),
    ("terrain3d", "sketch.war.terrain3d.camera.radius_factor"),
    ("terrain3d", "sketch.war.terrain3d.camera.period_sec"),
)

# EraDate 견본(원고 날짜 문자열 → 화면 뱃지). 뱃지 문구는 schemas.era_date.badge_text 가 만든다.
ERA_SAMPLES: tuple[str, ...] = ("-216.08.02R", "-216", "-218~-216", "c.-250", "1950.09.15", "1950.09")


@dataclass(frozen=True)
class Cut:
    """견본 컷 한 장 — 실제 엔진 렌더. rule_keys = 이 컷이 보여 주는 규칙 키(표 행과 같은 점 경로)."""

    cid: str
    project: str
    t: float
    theme: str
    title: str
    rule_keys: tuple[str, ...]


WAR_CUTS: tuple[Cut, ...] = (
    Cut("cannae_operational", "projects/cannae_sketch", 8.0, "relief", "작전 지도 — 진군로·기간 날짜(-218~-216)",
        ("sketch.war.default_theme", "hud.date_badge.era_format.period_years")),
    Cut("cannae_tactical", "projects/cannae_sketch", 30.0, "relief", "전술 무대 — 고대 부호 세트·입체·픽토그램·휘장 범례·로마력 날짜",
        ("war_history.symbol_sets.ancient.shapes", "war_history.symbol_sets.depth.side_ratio", "war_history.symbol_sets.glyph.size_px",
         "war_history.faction_badge.emblem.legend_px", "hud.date_badge.era_format.roman_suffix")),
    Cut("cannae_encircle_relief", "projects/cannae_sketch", 36.5, "relief", "포위 — relief 테마",
        ("sketch.war.default_theme", "war_history.symbol_sets.rank_grid.gap_px")),
    Cut("cannae_encircle_dark", "projects/cannae_sketch", 36.5, "dark", "포위 — dark 테마(같은 시각 비교)",
        ("sketch.war.default_theme",)),
    Cut("cannae_art_coin", "projects/cannae_sketch", 42.0, "relief", "증거 층 — 당대 작품(주화 사진, 자르지 않음)",
        ("war_history.period_art.labels.contemporary", "war_history.evidence.required_layers.ancient")),
    Cut("cannae_art_bust", "projects/cannae_sketch", 48.0, "relief", "증거 층 — 후대 작품(흉상)",
        ("war_history.period_art.labels.later", "war_history.period_art.contemporary_gap_years")),
    Cut("cannae_quote", "projects/cannae_sketch", 66.0, "relief", "증거 층 — 사료 인용(저자·권·절, PD 영역본)",
        ("war_history.evidence.required_layers.ancient",)),
    Cut("inchon_modern", "projects/inchon_sketch", 30.0, "relief", "현대 부호 세트(APP-6)",
        ("war_history.symbol_sets.modern.shapes", "war_history.symbol_set_by_year.early_modern_max")),
    Cut("inchon_clip", "projects/inchon_sketch", 45.0, "relief", "증거 층 — 기록 영화(자료 영상)",
        ("war_history.evidence.required_layers.modern",)),
    Cut("inchon_document", "projects/inchon_sketch", 63.0, "relief", "증거 층 — 당시 지도·문서",
        ("war_history.evidence.required_layers.modern",)),
)


def rule_value(root: Any, dotted: str) -> Any:
    """점 경로 값. Pydantic 모델·dict 둘 다(모델 값은 JSON 꼴로 바꾼다)."""
    cur = root
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur[part]
        else:
            cur = getattr(cur, part)
    return plain(cur)


def plain(v: Any) -> Any:
    if hasattr(v, "model_dump"):
        return v.model_dump(mode="json")
    if isinstance(v, tuple):
        return [plain(x) for x in v]
    if isinstance(v, list):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    return v


def rule_rows(keys: tuple[tuple[str, str], ...] = WAR_RULE_KEYS) -> list[dict[str, Any]]:
    R = load_rules()  # noqa: N806
    return [{"group": g, "key": k, "value": rule_value(R, k)} for g, k in keys]


def fmt_value(v: Any) -> str:
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def era_rows() -> list[dict[str, str]]:
    from schemas.era_date import badge_text  # noqa: PLC0415

    return [{"input": s, "badge": badge_text(s)} for s in ERA_SAMPLES]


def counterexamples() -> list[dict[str, str]]:
    """반례 — 실제 검증기에 틀린 값을 넣고 나온 오류 첫 줄. 오류가 안 나면 시트 생성 실패(규칙이 막지 못한다는 뜻)."""
    from engine.events import MarkerEvent  # noqa: PLC0415
    from schemas.data_models import EstimateBand  # noqa: PLC0415
    from schemas.era_date import parse_era_date  # noqa: PLC0415

    cases: list[tuple[str, Callable[[], object]]] = [
        ("부호 세트에 없는 픽토그램", lambda: MarkerEvent.model_validate(
            {"type": "marker", "t0": 1.0, "t1": 2.0, "lon": 16.1, "lat": 41.3, "label": "가", "glyph": "musketeer"})),
        ("픽토그램과 폭발 아이콘을 함께", lambda: MarkerEvent.model_validate(
            {"type": "marker", "t0": 1.0, "t1": 2.0, "lon": 16.1, "lat": 41.3, "label": "가", "glyph": "heavy_inf", "icon": "boom"})),
        ("범위 띠 종류 없음", lambda: EstimateBand.model_validate({"low": 1.0, "high": 2.0, "source": "가"})),
        ("범위 띠 low > high", lambda: EstimateBand.model_validate(
            {"kind": "ancient_range", "low": 9.0, "high": 2.0, "source": "가"})),
        ("로마력 표지를 연도만 있는 날짜에", lambda: parse_era_date("-216R")),
    ]
    out = []
    for name, fn in cases:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — 검증기마다 오류 클래스가 다르다(ValidationError·ValueError)
            errs = getattr(e, "errors", None)
            msg = "; ".join(f"{'.'.join(map(str, x['loc'])) or '모델'}: {x['msg']}" for x in errs()) if callable(errs) else str(e)
            out.append({"case": name, "error": msg.strip()[:300]})
            continue
        raise SystemExit(f"반례가 통과했다(검증기가 막지 못함): {name}")
    return out


def render_cut(cut: Cut, out_dir: Path) -> Path:
    from sketch.common.render import to_image  # noqa: PLC0415
    from sketch.common.spec import load_spec  # noqa: PLC0415
    from sketch.war.scene import WarScene  # noqa: PLC0415
    from sketch.war.spec import WarSpec  # noqa: PLC0415

    project = REPO / cut.project
    spec = load_spec(project, WarSpec)
    scene = WarScene(spec, project, "trial", theme=cut.theme)
    p = out_dir / f"{cut.cid}.jpg"
    to_image(scene.frame(cut.t), scene.out).save(p, quality=88)
    return p


def glyph_swatch(out_dir: Path) -> Path:
    """병종 픽토그램 전부 — engine.glyphs.arms.draw_glyph(지도 위와 같은 함수). 크기는 규칙 값의 4배(읽기용), 굵기 비율 같음."""
    from engine.glyphs.arms import draw_glyph  # noqa: PLC0415

    R = load_rules()  # noqa: N806
    G = R.war_history.symbol_sets.glyph  # noqa: N806
    names = list(dict.fromkeys(R.war_history.symbol_sets.glyph_names()))
    k = 4.0
    cell = int(G.size_px * k * 2)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, cell * len(names), cell)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.42, 0.45, 0.40)
    ctx.paint()
    for i, n in enumerate(names):
        draw_glyph(ctx, n, cell * i + cell / 2, cell / 2, G.size_px * k, (1, 1, 1), G.alpha, tuple(G.halo_rgb), G.halo_px * k)
    p = out_dir / "glyphs.png"
    surf.write_to_png(str(p))
    return p


def emblem_swatch(out_dir: Path) -> tuple[Path, list[dict[str, str]]]:
    """진영 휘장 재작도 전부 — engine.glyphs.emblems.draw_emblem + 근거 유물·사진 권리(assets/emblems/registry.json)."""
    from engine.entities import load_emblem_registry  # noqa: PLC0415
    from engine.glyphs.emblems import draw_emblem  # noqa: PLC0415

    R = load_rules()  # noqa: N806
    E = R.war_history.faction_badge.emblem  # noqa: N806
    rec = load_emblem_registry().reconstructions
    if not rec:
        raise SystemExit("휘장 재작도 레코드가 없다(assets/emblems/registry.json reconstructions)")
    k = 8.0
    cell = int(E.legend_px * k * 1.6)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, cell * len(rec), cell)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.96, 0.96, 0.97)
    ctx.paint()
    rows = []
    for i, (key, r) in enumerate(sorted(rec.items())):
        draw_emblem(ctx, r.glyph, cell * i + cell / 2, cell / 2, E.legend_px * k, tuple(E.badge_ink), E.alpha, (0.96, 0.96, 0.97), 0.0)
        rows.append({"key": key, "faction": r.faction, "basis": r.basis, "photo": f"{r.basis_title} — {r.basis_author}, {r.basis_license}",
                     "label": r.caption_label})
    p = out_dir / "emblems.png"
    surf.write_to_png(str(p))
    return p, rows


def terrain3d_still(out_dir: Path) -> Path:
    """terrain3d 정지 컷(sketch.war.terrain3d — headless Chromium + three.js). 실패하면 오류."""
    proj = REPO / "projects" / "cannae_sketch"
    r = subprocess.run([sys.executable, "-m", "sketch.war.terrain3d", str(proj), "--t", "36.5"], cwd=REPO,
                       capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise SystemExit(f"terrain3d 정지 컷 실패(rc {r.returncode}): {r.stderr[-800:]}")
    src = proj / "out" / "terrain3d" / "terrain3d_still.png"
    p = out_dir / "terrain3d_still.jpg"
    Image.open(src).convert("RGB").save(p, quality=88)
    return p


CSS = """
:root{--bg:#f6f4ef;--ink:#1f1d1a;--sub:#6b665e;--line:#ddd7cc;--acc:#8a5a2b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:"Pretendard","Noto Sans KR","Apple SD Gothic Neo",system-ui,sans-serif;line-height:1.55}
main{max-width:960px;margin:0 auto;padding:20px 16px 60px}h1{font-size:1.45rem;margin:.2em 0}
h2{font-size:1.1rem;margin:2em 0 .6em;border-bottom:2px solid var(--acc);padding-bottom:.2em}
.meta{color:var(--sub);font-size:.85rem}table{width:100%;border-collapse:collapse;font-size:.82rem}
td,th{border-bottom:1px solid var(--line);padding:6px 4px;text-align:left;vertical-align:top;word-break:break-all}
th{color:var(--sub);font-weight:600}code{font-size:.78rem;background:#ece8df;padding:1px 4px;border-radius:3px}
.cuts{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
figure{margin:0;background:#fff;border:1px solid var(--line);border-radius:6px;overflow:hidden}
figure img{width:100%;display:block}figcaption{padding:8px 10px;font-size:.82rem}
.keys{color:var(--sub);font-size:.74rem}.wide img{width:100%;border:1px solid var(--line);border-radius:6px;background:#fff}
.err{color:#9b2c2c}
"""


@dataclass
class Sheet:
    genre: str
    version: str
    rows: list[dict[str, Any]]
    eras: list[dict[str, str]]
    cuts: list[tuple[Cut, str]]
    glyphs: str | None
    emblems: tuple[str, list[dict[str, str]]] | None
    terrain3d: str | None
    bad: list[dict[str, str]]
    notes: list[str] = field(default_factory=list)


def render_html(s: Sheet) -> str:
    e = html.escape
    parts = [f"<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>디자인 시트 — {e(s.genre)} v{e(s.version)}</title><style>{CSS}</style></head><body><main>",
             f"<h1>디자인 시트 — 전쟁사({e(s.genre)})</h1>",
             f"<p class='meta'>v{e(s.version)} · rules/video_rules.yaml 에서 생성(tools/design_sheet.py). 컷은 실제 엔진 렌더(480p 시험 판).</p>"]
    for n in s.notes:
        parts.append(f"<p class='meta'>{e(n)}</p>")
    parts.append("<h2>1. 견본 컷</h2><div class='cuts'>")
    for c, f in s.cuts:
        keys = " · ".join(f"<code>{e(k)}</code>" for k in c.rule_keys)
        parts.append(f"<figure><img src='{e(f)}' alt='{e(c.title)}' loading='lazy'><figcaption>{e(c.title)}<br>"
                     f"<span class='keys'>{e(c.project.split('/')[-1])} t={c.t:g}s · {e(c.theme)} · {keys}</span></figcaption></figure>")
    if s.terrain3d:
        parts.append(f"<figure><img src='{e(s.terrain3d)}' alt='terrain3d' loading='lazy'><figcaption>terrain3d 정지 컷 — 칸나이 t=36.5s"
                     f"<br><span class='keys'><code>sketch.war.terrain3d.*</code> · 무대 등록 전(stages_planned)</span></figcaption></figure>")
    parts.append("</div>")
    if s.glyphs:
        parts.append(f"<h2>2. 병종 픽토그램</h2><div class='wide'><img src='{e(s.glyphs)}' alt='glyphs'></div>"
                     "<p class='meta'>engine.glyphs.arms — 왼쪽부터 규칙 war_history.symbol_sets.*.glyphs 값 순서. 읽기 위해 규칙 크기의 4배.</p>")
    if s.emblems:
        img, rows = s.emblems
        parts.append(f"<h2>3. 진영 휘장(재현)</h2><div class='wide'><img src='{e(img)}' alt='emblems'></div><table>"
                     "<tr><th>키</th><th>진영</th><th>근거 유물</th><th>근거 사진</th><th>화면 라벨</th></tr>")
        parts += [f"<tr><td><code>{e(r['key'])}</code></td><td>{e(r['faction'])}</td><td>{e(r['basis'])}</td><td>{e(r['photo'])}</td>"
                  f"<td>{e(r['label'])}</td></tr>" for r in rows]
        parts.append("</table>")
    parts.append("<h2>4. 날짜 표기(EraDate)</h2><table><tr><th>원고 날짜</th><th>화면 뱃지</th></tr>")
    parts += [f"<tr><td><code>{e(r['input'])}</code></td><td>{e(r['badge'])}</td></tr>" for r in s.eras]
    parts.append("</table><h2>5. 규칙 값</h2><table><tr><th>묶음</th><th>규칙 키</th><th>값</th></tr>")
    parts += [f"<tr><td>{e(r['group'])}</td><td><code>{e(r['key'])}</code></td><td data-key='{e(r['key'])}'>{e(fmt_value(r['value']))}</td></tr>"
              for r in s.rows]
    parts.append("</table><h2>6. 반례 — 검증기가 막는 것</h2><table><tr><th>틀린 입력</th><th>오류</th></tr>")
    parts += [f"<tr><td>{e(r['case'])}</td><td class='err'>{e(r['error'])}</td></tr>" for r in s.bad]
    parts.append("</table></main></body></html>")
    return "\n".join(parts)


def build(genre: str, out: Path, with_terrain3d: bool = True) -> Path:
    if genre not in GENRES:
        raise SystemExit(f"디자인 시트가 없는 장르: {genre!r} — {GENRES}")
    out.mkdir(parents=True, exist_ok=True)
    version = (REPO / "VERSION").read_text(encoding="utf-8").strip()
    cuts = []
    for c in WAR_CUTS:
        cuts.append((c, render_cut(c, out).name))
        print(f"컷 {c.cid}", flush=True)
    t3 = terrain3d_still(out).name if with_terrain3d else None
    notes = [] if with_terrain3d else ["terrain3d 정지 컷은 이번 생성에서 뺐다(--no-terrain3d)."]
    notes.append("근세(early_modern) 부호 세트는 견본 컷이 없다 — 근세 전쟁사 프로젝트가 아직 없다. 값은 5절 표에 있다.")
    em = emblem_swatch(out)
    sheet = Sheet(genre, version, rule_rows(), era_rows(), cuts, glyph_swatch(out).name, (em[0].name, em[1]), t3, counterexamples(), notes)
    (out / "values.json").write_text(json.dumps({"schema_version": 1, "genre": genre, "version": version, "rows": sheet.rows,
                                                 "eras": sheet.eras, "cuts": [{"id": c.cid, "file": f, "project": c.project, "t": c.t,
                                                                               "theme": c.theme, "rule_keys": list(c.rule_keys)} for c, f in cuts]},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    p = out / "index.html"
    p.write_text(render_html(sheet), encoding="utf-8")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python tools/design_sheet.py", description="장르 디자인 시트(규칙 값 + 엔진 견본 컷 + 반례)")
    ap.add_argument("genre", choices=GENRES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--no-terrain3d", action="store_true", help="terrain3d 정지 컷을 빼고 그 사실을 시트에 적는다(Chromium 이 없을 때)")
    a = ap.parse_args(argv)
    print(build(a.genre, a.out, not a.no_terrain3d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
