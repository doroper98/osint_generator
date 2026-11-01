"""전쟁사 스케치 장면 — 시대별 기반 지도(현대 국경·현대 지명 없음) 위에 강·경로·부대(시대 부호)·당시 지명(+지명 유래)·
증거 카드(작품·사진·기록 + 당대/후대 라벨 + 미술사 한 문장)·사료 인용·진영 범례·EraDate 뱃지·출처·엔딩
(v7.4.0 전쟁사 W3·W4, back_and_forth D-0600 §2·§5·§6). 수치 = rules sketch.war·fade·text, 사실·연출 = spec·레코드.

작전 지도와 전술 무대는 같은 좌표계다 — 숏 w 가 작아지면 전장 축척(카메라 연속, 새 캔버스 없음).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cairo
import numpy as np
from PIL import Image

from engine.assets import Assets, load_labels, surf_from_pil
from engine.layers.media import caption_bar_h, media_caption, media_tag
from engine.projection import View
from engine.stage import MercatorStage, ym
from engine.style import C, CARD_BG, DATE_BADGE, H_OUT, W_OUT, Output, output_profile
from engine.timebase import ease_out, smooth, window
from engine.typography import rrect, text, tw
from rules import load_rules
from schemas.era_date import badge_text, parse_era_date
from schemas.media_models import MediaAsset, MediaRegistryFile
from schemas.war_history import ToponymyEntry, load_toponymy, period_art_label, probable_caption
from sketch.common import geodesy as GEO
from sketch.common.camera import CameraPath
from sketch.common.draw import SK, WHITE
from sketch.common.render import BGRA
from sketch.war.spec import Evidence, Quote, WarSpec
from engine.glyphs.emblems import draw_emblem
from sketch.war.units import WarUnitLayer

W, F, T = SK.war, SK.fade, SK.text
WH = load_rules().war_history
CREDIT_FMT = load_rules().media_beats.credit_formats
LABELS_FILE = "labels.yaml"
MEDIA_FILE = "media.json"
MEDIA_DIR = "media_src"
PLACES_FILE = "ancient_geo/places.json"
ROADS_FILE = "ancient_geo/roads.json"
DRAINAGE_FILE = "drainage.json"
BGRX = "BGRX"


def load_media(project: Path) -> dict[str, MediaAsset]:
    p = project / MEDIA_FILE
    if not p.is_file():
        return {}
    return MediaRegistryFile.model_validate(json.loads(p.read_text(encoding="utf-8"))).assets


def load_places(project: Path) -> dict[str, dict]:
    p = project / PLACES_FILE
    return {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.is_file() else {}


def date_at(spec: WarSpec, t: float) -> str:
    return [d for d in spec.dates if t >= d.t][-1].date


def card_texts(a: MediaAsset, event_date: str) -> tuple[str, str]:
    """(캡션, 출처 줄) — 작품이면 출처 줄 앞에 당대/후대 라벨(engine.media_registry.media_credit 와 같은 함수 계열)."""
    cap = probable_caption(a.caption, a.identification, a.identified_as)
    base = a.credit_line(CREDIT_FMT[a.kind])
    if a.kind != "period_art":
        return cap, base
    lab = period_art_label(a.created, parse_era_date(event_date))
    return cap, base if lab is None else lab + WH.period_art.labels.sep + base


def wrap(ctx: cairo.Context, s: str, size: float, font: str, maxw: float, max_lines: int) -> list[str]:
    """낱말 단위 줄바꿈(넘치면 마지막 줄 끝 말줄임)."""
    lines: list[str] = []
    for word in s.split(" "):
        if lines and tw(ctx, lines[-1] + " " + word, size, font) <= maxw:
            lines[-1] += " " + word
        else:
            lines.append(word)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


class SceneError(ValueError):
    pass


def faction_emblems(spec: WarSpec) -> dict:
    """진영 id → EmblemReconstruction(assets/emblems/registry.json reconstructions). spec 이 가리킨 키가 없으면 오류 — 조용히 빼지 않는다(P6)."""
    from engine.entities import load_emblem_registry  # noqa: PLC0415

    want = {k: f.emblem for k, f in spec.factions.items() if f.emblem}
    if not want:
        return {}
    rec = load_emblem_registry().reconstructions
    miss = sorted(v for v in want.values() if v not in rec)
    if miss:
        raise SceneError(f"휘장 재작도 레코드 없음 {miss} — assets/emblems/registry.json reconstructions(유물 근거만, D-0606)")
    return {k: rec[v] for k, v in want.items()}


class WarScene:
    def __init__(self, spec: WarSpec, project: Path, res: str, theme: "str | None" = None) -> None:
        self.spec, self.project, self.theme = spec, project, theme
        self.out: Output = output_profile(res)
        default = output_profile(None).name
        assets = Assets(project, load_labels(project / LABELS_FILE), None if self.out.name == default else self.out.name, theme=theme)
        self.stage = MercatorStage(assets, out=self.out, proposed_theme=theme if theme in load_rules().geo.themes.proposed else None)
        cam = SK.camera
        self.camera = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
        self.emblems = faction_emblems(spec)   # v2(D-0606 A) — 진영 → 재작도 레코드(없는 키 = 오류, P6)
        self.units = WarUnitLayer(spec, {k: r.glyph for k, r in self.emblems.items()})
        self.media = load_media(project)
        self.places = load_places(project)
        rp = project / ROADS_FILE
        self.roads = json.loads(rp.read_text(encoding="utf-8")) if spec.ancient_roads_t and rp.is_file() else []
        tf = load_toponymy(project)
        self.topo: dict[str, ToponymyEntry] = tf.by_id() if tf is not None else {}
        self._img: dict[str, tuple] = {}
        dp = project / DRAINAGE_FILE   # 구상 컷 A(D-0604) — 고도 타일 수계(tools/dem_drainage.py), 테마 overlays 에 drainage 가 있을 때만
        self.drainage = json.loads(dp.read_text(encoding="utf-8")) if "drainage" in self._overlays() and dp.is_file() else []
        self.res_boxes: list[tuple[float, list]] = []
        self.card_boxes: list[tuple[float, list]] = []   # 프레임마다 보이는 카드 상자(SK-W6 — 카드가 라벨·부대를 덮는가)
        self.overflow: list[tuple[float, str]] = []      # 핀이 화면 안인데 글자가 화면 밖(SK-W5)
        self.drawn: dict[str, int] = {f"theme:{theme or 'dark'}": 1}   # provenance 에 이번 렌더 테마(D-0607 ③)

    def _overlays(self) -> list[str]:
        """테마별 지도 안 요소(rules sketch.war.theme_overlays) — dark(v1) = 없음, relief(구상) = 수계·축척 막대."""
        return list(W.theme_overlays.get(self.theme or "dark", []))

    def features_drawn(self) -> dict[str, int]:
        out = dict(self.drawn)
        for k, v in self.units.drawn.items():
            out[k] = out.get(k, 0) + v
        return out

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    def place_xy(self, p) -> tuple[float, float]:  # noqa: ANN001 — WarPlace
        if p.pleiades is not None:
            r = self.places[p.pleiades]
            return r["lon"], r["lat"]
        return p.lon, p.lat

    # ---------------------------------------------------------------- 프레임
    def frame(self, t: float) -> bytes:
        sp, OP = self.spec, self.out
        view = View(self.stage, np.array(self.camera.at(t)))
        im = self.stage.base_image(view, OP)            # 지형(DEM 음영)만 — 현대 국경·행정구역선·현대 지명은 그리지 않는다(basemap_era ancient)
        buf = bytearray(im.tobytes("raw", BGRX))
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * BGRA)
        ctx = cairo.Context(surf)
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
        ctx.set_source_rgba(*W.terrain_dim)
        ctx.paint()
        Lf = W.lift
        lift = smooth((W_OUT / view.w - Lf.from_ppd) / Lf.span_ppd) if (self.theme or "dark") in Lf.themes else 0
        if lift > F.min_alpha:   # 전술 축척 바탕(D-0602 ④) — 평탄한 평야도 무대로 보이게
            ctx.set_operator(cairo.OPERATOR_ADD)
            ctx.set_source_rgba(*Lf.rgb, lift)
            ctx.paint()
            ctx.set_operator(cairo.OPERATOR_OVER)
        res: list = []
        self._drainage(ctx, view)
        self._roads(ctx, view, t)
        self._rivers(ctx, view, t)
        self._routes(ctx, view, t)
        self.units.draw(ctx, view, t, res)
        self._places(ctx, view, t, res)
        dim = max((window(t, e.t0, e.t1, W.card.in_sec, W.card.out_sec) for e in sp.evidence), default=0)
        if dim > F.min_alpha:
            ctx.set_source_rgba(0, 0, 0, W.card.dim_alpha * dim)
            ctx.paint()
        cards: list = []
        for e in sp.evidence:
            box = self._evidence(ctx, e, t)
            if box is not None:
                cards.append(box)
        self.card_boxes.append((t, cards))
        for q in sp.quotes:
            self._quote(ctx, q, t)
        self.res_boxes.append((t, list(res)))
        self._legend(ctx, t)
        if "scale_bar" in self._overlays():
            self._scale_bar(ctx, view)
        self._source(ctx, t)
        self._date(ctx, t)
        self._end(ctx, t)
        fa = 1 - min(smooth(t / F.open_sec), smooth((sp.duration_sec - t) / F.close_sec))
        if fa > F.black_min:
            ctx.set_source_rgba(0, 0, 0, fa)
            ctx.paint()
        surf.flush()
        return bytes(buf)

    # ---------------------------------------------------------------- 지도 층
    def _drainage(self, ctx: cairo.Context, view: View) -> None:
        if not self.drainage:
            return
        Dr = W.drainage
        for ln in self.drainage:
            pts = [view.to_screen(lon, ym(lat)) for lon, lat in ln]
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
        ctx.set_source_rgba(*Dr.rgb, Dr.alpha)
        ctx.set_line_width(Dr.w)
        ctx.stroke()
        self._note("drainage")

    def _scale_bar(self, ctx: cairo.Context, view: View) -> None:
        """지도 안 축척 막대(모서리 요소 아님, C0) — 길이는 카메라 축척에서 계산(출처 없는 숫자 아님): 화면 중앙 위도의 km/px × 막대 px,
        rules sketch.war.scale_bar.nice 의 가수 × 10^k 중 target_px 이하 최대."""
        Sb = W.scale_bar
        lat = math.degrees(math.atan(math.sinh(math.radians(view.y1 - view.h / 2))))
        km_per_px = view.w * GEO.KM_PER_DEG * math.cos(math.radians(lat)) / W_OUT
        best = None
        for e in range(Sb.exp_range[0], Sb.exp_range[1] + 1):
            for mnt in Sb.nice:
                km = mnt * Sb.base ** e
                if km / km_per_px <= Sb.target_px and (best is None or km > best):
                    best = km
        if best is None:
            return
        px = best / km_per_px
        x, y = Sb.x, Sb.y
        ctx.rectangle(x, y, px, Sb.h)
        ctx.set_source_rgba(*Sb.rgb, Sb.alpha)
        ctx.fill()
        lab = (f"{best:g} km") if best >= 1 else f"{best * GEO.M_PER_KM:g} m"
        L = Sb.label
        text(ctx, lab, x + px + L.dx, y + L.dy, L.size, L.font, WHITE, L.alpha, L.halo)
        self._note("scale_bar")

    def _roads(self, ctx: cairo.Context, view: View, t: float) -> None:
        if not self.roads:
            return
        t0, t1 = self.spec.ancient_roads_t
        a = window(t, t0, t1, W.place.in_sec, W.place.in_sec)
        if a <= F.min_alpha:
            return
        Rd = W.ancient_road
        ctx.set_dash(list(Rd.dash))
        for ln in self.roads:
            pts = [view.to_screen(lon, ym(lat)) for lon, lat in ln]
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
        ctx.set_source_rgba(*Rd.rgb, Rd.alpha * a)
        ctx.set_line_width(Rd.w)
        ctx.stroke()
        ctx.set_dash([])
        self._note("ancient_road")

    def _rivers(self, ctx: cairo.Context, view: View, t: float) -> None:
        R = W.river
        for r in self.spec.rivers:
            a = smooth((t - r.t) / W.place.in_sec)
            if a <= F.min_alpha:
                continue
            pts = [view.to_screen(lon, ym(lat)) for lon, lat in r.pts]
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.set_source_rgba(*R.rgb, R.alpha * a)
            ctx.set_line_width(R.w)
            ctx.stroke()
            x, y = view.to_screen(r.label_at[0], ym(r.label_at[1]))
            L = R.label
            text(ctx, r.name, x, y, L.size, L.font, tuple(R.rgb), L.alpha * a, L.halo, "c")
            self._note("river")

    def _routes(self, ctx: cairo.Context, view: View, t: float) -> None:
        Ro = W.route
        for r in self.spec.routes:
            k = smooth((t - r.t0) / (r.t1 - r.t0))
            a = smooth((t - r.t0) / W.unit.in_sec) * (1 - smooth((t - r.t_out) / W.unit.in_sec) if r.t_out is not None else 1)
            if k <= 0 or a <= F.min_alpha:
                continue
            pts = np.array([view.to_screen(lon, ym(lat)) for lon, lat in r.pts])
            seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
            cum = np.concatenate([[0], np.cumsum(seg)])
            upto = cum[-1] * k
            n = int(np.searchsorted(cum, upto))
            path = list(pts[:n]) if n else [pts[0]]
            if n < len(pts) and n > 0:
                f = (upto - cum[n - 1]) / max(seg[n - 1], Ro.w)
                path.append(pts[n - 1] + (pts[n] - pts[n - 1]) * min(f, 1))
            col = C[self.spec.factions[r.faction].token]
            ctx.move_to(*path[0])
            for p in path[1:]:
                ctx.line_to(*p)
            ctx.set_source_rgba(*col, Ro.alpha * a)
            ctx.set_line_width(Ro.w)
            ctx.stroke()
            if len(path) > 1:
                tip, prev = np.array(path[-1]), np.array(path[-2])
                d = tip - prev
                d = d / (np.linalg.norm(d) or 1)
                nrm = np.array([-d[1], d[0]])
                base = tip - d * Ro.head
                ctx.move_to(*tip)
                ctx.line_to(*(base + nrm * Ro.head * Ro.head_wing))
                ctx.line_to(*(base - nrm * Ro.head * Ro.head_wing))
                ctx.close_path()
                ctx.fill()
                L = Ro.label
                if k >= 1:
                    mid = pts[len(pts) // 2]
                    text(ctx, r.name, mid[0], mid[1] + L.dy, L.size, L.font, col, a, L.halo, "c")
            self._note("route")

    def _places(self, ctx: cairo.Context, view: View, t: float, res: list) -> None:
        P, Tp, Nw = W.place, W.toponymy, W.place_now
        for p in self.spec.places:
            a = smooth((t - p.t) / P.in_sec) * (1 - smooth((t - p.t_out) / P.in_sec) if p.t_out is not None else 1)
            if a <= F.min_alpha:
                continue
            lon, lat = self.place_xy(p)
            x, y = view.to_screen(lon, ym(lat))
            if not (0 < x < W_OUT and 0 < y < H_OUT):
                continue
            ctx.arc(x, y, P.dot_r, 0, 2 * np.pi)
            ctx.set_source_rgba(*WHITE, a)
            ctx.fill()
            text(ctx, p.name, x + P.dx, y + P.dy, P.size, P.font, WHITE, P.alpha * a, P.halo)
            wd = tw(ctx, p.name, P.size, P.font)
            bottom = y + Nw.dy
            if p.toponymy:
                Wr = W.toponymy_wrap
                line = f"{self.topo[p.toponymy].name} — {self.topo[p.toponymy].line()}"
                one = view.w > W.lod.toponymy_one_line_w   # 물러난 숏 = 핀 아래 한 줄(D-0602 ②)
                lines = wrap(ctx, line, Tp.size, Tp.font, Wr.max_w, 1 if one else Wr.max_lines)
                if one:
                    self._note("lod:toponymy_one_line")
                for i, ln in enumerate(lines):
                    text(ctx, ln, x + P.dx, y + Tp.dy + i * Wr.dy, Tp.size, Tp.font, C["gold"], Tp.alpha * a, Tp.halo)
                    wd = max(wd, tw(ctx, ln, Tp.size, Tp.font))
                bottom = max(bottom, y + Tp.dy + (len(lines) - 1) * Wr.dy)
                self._note("toponymy")
            now_dy = Nw.dy + (bottom - y - Tp.dy if p.toponymy else 0)
            if p.now:
                text(ctx, p.now, x + P.dx, y + now_dy, Nw.size, Nw.font, C["muted"], Nw.alpha * a, Nw.halo)
            if x + P.dx + wd > W_OUT:
                self.overflow.append((t, p.name))
            res.append((x, y - P.size, x + P.dx + wd, y + now_dy))
            self._note("place")

    # ---------------------------------------------------------------- 증거 층
    def _image(self, mid: str) -> tuple:
        if mid not in self._img:
            a = self.media[mid]
            im = Image.open(self.project / MEDIA_DIR / a.file)
            self._img[mid] = (*surf_from_pil(im), im.width, im.height)
        return self._img[mid]

    def _clip(self, mid: str) -> tuple:
        """기록 영상 구간(segment) 프레임 — ffmpeg 로 한 번 풀어 둔다(원본은 media_src 에 그대로 보존, v2 D-0607 §2 인천 필름 clip 층).
        반환 (프레임 배열 [n, h, w, 3], 원본 fps). 결정적: 구간·폭은 레코드·규칙 값."""
        key = f"clip:{mid}"
        if key not in self._img:
            import subprocess  # noqa: PLC0415

            a = self.media[mid]
            src = self.project / MEDIA_DIR / a.file
            s0, s1 = a.segment
            w = int(W.card.clip_px_w)
            probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                                    "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True).stdout.strip().split(",")
            sw, sh = int(probe[0]), int(probe[1])
            num, den = (int(x) for x in probe[2].split("/"))
            fps = num / den
            h = int(round(w * sh / sw / 2)) * 2
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s0}", "-t", f"{s1 - s0}", "-i", str(src), "-vf", f"scale={w}:{h}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
            if not len(frames):
                raise SceneError(f"{mid}: 영상 구간 {a.segment} 에서 프레임을 풀지 못했다 — {src}")
            self._img[key] = (frames, fps)
        return self._img[key]

    def _evidence(self, ctx: cairo.Context, e: Evidence, t: float) -> "tuple | None":
        Cd = W.card
        a = window(t, e.t0, e.t1, Cd.in_sec, Cd.out_sec)
        if a <= F.min_alpha:
            return None
        m = self.media[e.mid]
        if m.kind == "video":   # 기록 영상 카드 — 카드가 뜬 뒤 흐른 시간만큼 구간 안에서 재생(끝에 닿으면 마지막 프레임 유지)
            frames, fps = self._clip(e.mid)
            fr = frames[min(len(frames) - 1, max(0, int((t - e.t0) * fps)))]
            surf, _buf, iw, ih = (*surf_from_pil(Image.fromarray(fr)), fr.shape[1], fr.shape[0])
        else:
            surf, _buf, iw, ih = self._image(e.mid)
        w = Cd.w
        h = min(Cd.max_img_h, w * ih / iw)
        w_img = h * iw / ih
        x = Cd.x_left if e.side == "left" else W_OUT - Cd.x_right_margin - w
        y = Cd.y + (1 - ease_out(min(1, (t - e.t0) / Cd.in_sec))) * Cd.rise_px
        cap, credit = card_texts(m, date_at(self.spec, e.t0))
        bar = caption_bar_h(cap, credit, w)
        ctx.rectangle(x, y, w, h)
        ctx.set_source_rgba(*CARD_BG[:3], Cd.art_bg_alpha * a)
        ctx.fill()
        ctx.save()
        ctx.translate(x + (w - w_img) / 2, y)
        ctx.scale(w_img / iw, h / ih)
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint_with_alpha(a)
        ctx.restore()
        media_tag(ctx, x, y, WH.media_tags.get(m.kind, "VIDEO" if m.kind == "video" else "PHOTO"), a)
        media_caption(ctx, x, y + h, w, cap, credit, a)
        if m.art_history:
            Ar = Cd.art
            lines = wrap(ctx, m.art_history, Ar.size, Ar.font, w - 2 * Cd.art_pad, Cd.art_lines)
            y0 = y + h + bar
            ctx.rectangle(x, y0, w, Cd.art_pad + len(lines) * Ar.dy)
            ctx.set_source_rgba(*CARD_BG[:3], Cd.art_bg_alpha * a)
            ctx.fill()
            for i, ln in enumerate(lines):
                text(ctx, ln, x + Cd.art_pad, y0 + Ar.dy * (i + 1), Ar.size, Ar.font, WHITE, Ar.alpha * a, Ar.halo)
        self._note(f"evidence:{m.kind}")
        bottom = y + h + bar + ((Cd.art_pad + len(lines) * Cd.art.dy) if m.art_history else 0)
        return (x, y, x + w, bottom, a)

    def _quote(self, ctx: cairo.Context, q: Quote, t: float) -> None:
        Q = W.quote
        a = window(t, q.t0, q.t1, Q.in_sec, Q.out_sec)
        if a <= F.min_alpha:
            return
        x = (W_OUT - Q.w) / 2
        lines = wrap(ctx, q.text, Q.text.size, Q.text.font, Q.w - 2 * Q.pad, Q.text_lines)
        orig = wrap(ctx, q.original, Q.original.size, Q.original.font, Q.w - 2 * Q.pad, Q.text_lines)
        h = Q.pad + len(lines) * Q.text.dy + len(orig) * Q.original.dy + Q.locator.dy + Q.pad
        rrect(ctx, x, Q.y, Q.w, h, Q.bar_w)
        ctx.set_source_rgba(*CARD_BG[:3], Q.bg_alpha * a)
        ctx.fill()
        ctx.rectangle(x, Q.y, Q.bar_w, h)
        ctx.set_source_rgba(*C["gold"], a)
        ctx.fill()
        yy = Q.y + Q.pad
        for ln in lines:
            yy += Q.text.dy
            text(ctx, ln, x + Q.pad, yy, Q.text.size, Q.text.font, WHITE, a, Q.text.halo)
        for ln in orig:
            yy += Q.original.dy
            text(ctx, ln, x + Q.pad, yy, Q.original.size, Q.original.font, C["muted"], Q.original.alpha * a, Q.original.halo)
        yy += Q.locator.dy
        text(ctx, f"{q.locator} · {q.translation}", x + Q.pad, yy, Q.locator.size, Q.locator.font, C["gold"], Q.locator.alpha * a,
             Q.locator.halo, role="source")
        self._note("quote")

    # ---------------------------------------------------------------- HUD
    def _legend(self, ctx: cairo.Context, t: float) -> None:
        t0, t1 = self.spec.legend_t
        a = window(t, t0, t1, F.note_in, F.note_out) if t1 > t0 else 0
        if a <= F.min_alpha:
            return
        Lg = W.legend
        EM = load_rules().war_history.faction_badge.emblem  # noqa: N806
        fs = list(self.spec.factions.items())
        notes = [f"{f.name.split('(')[0]} 휘장 — {self.emblems[k].caption_label}" for k, f in fs if k in self.emblems]
        em_dx = EM.legend_dx if self.emblems else 0   # 휘장 칸(어느 진영이든 있으면 모든 줄을 같은 만큼 민다)
        bx, by, bw, bh = Lg.bg
        w_note = max((tw(ctx, n, EM.note.size, EM.note.font) for n in notes), default=0) - bx * 2   # 라벨 줄이 상자 밖으로 나가지 않게
        rrect(ctx, Lg.x + bx, Lg.y + by, max(bw + em_dx, w_note), len(fs) * Lg.row_dy + bh + len(notes) * EM.note.dy, Lg.radius)
        ctx.set_source_rgba(*CARD_BG[:3], Lg.alpha * a)
        ctx.fill()
        L = Lg.label
        for i, (k, f) in enumerate(fs):
            y = Lg.y + i * Lg.row_dy
            ctx.rectangle(Lg.x, y + Lg.chip_dy, *Lg.chip)
            ctx.set_source_rgba(*C[f.token], a)
            ctx.fill()
            if k in self.emblems:
                draw_emblem(ctx, self.emblems[k].glyph, Lg.x + Lg.label_dx + EM.legend_px / 2, y + EM.legend_dy, EM.legend_px,
                            WHITE, EM.alpha * a, load_rules().war_history.symbol_sets.glyph.halo_rgb, EM.halo_px)
                self._note(f"emblem:{self.emblems[k].glyph}")
            text(ctx, f.name, Lg.x + Lg.label_dx + em_dx, y, L.size, L.font, WHITE, a, L.halo)
        N = EM.note  # noqa: N806
        for j, ln in enumerate(notes):   # "…재현" 라벨(코드 조판, D-0606) — 근거 유물 표기
            text(ctx, ln, Lg.x, Lg.y + (len(fs) - 1) * Lg.row_dy + (j + 1) * N.dy, N.size, N.font, WHITE, N.alpha * a, N.halo, role="source")
        self._note("faction_legend")

    def _source(self, ctx: cairo.Context, t: float) -> None:
        S = T.source
        for n in self.spec.notes.source_lines:
            a = window(t, n.t0, n.t1, F.note_in, F.note_out)
            text(ctx, n.text, S.x, S.y, S.size, S.font, C["muted"], W.source_alpha * a, S.halo, role="source")

    def _end_t0(self) -> float:
        return self.spec.duration_sec - self.spec.notes.end_sec

    def _date(self, ctx: cairo.Context, t: float) -> None:
        B = DATE_BADGE
        cur = [d for d in self.spec.dates if t >= d.t][-1]
        k = smooth((t - cur.t - W.date_delay) / B.slide_sec)
        a = F.date_alpha * k * (1 - smooth((t - (self._end_t0() - F.date_hide_lead_sec)) / F.date_hide_sec))
        w = text(ctx, badge_text(cur.date), W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, WHITE, a, F.date_halo, "r")
        ctx.set_source_rgba(*C["gold"], F.date_line_alpha * a)
        ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
        ctx.fill()

    def _end(self, ctx: cairo.Context, t: float) -> None:
        a = smooth((t - self._end_t0()) / F.end_in_sec)
        if a <= F.min_alpha:
            return
        ctx.set_source_rgba(*F.end_bg, F.end_dim_alpha * a)
        ctx.paint()
        E, Tt, Ln, Nt = W.end, T.end_title, T.end_line, T.end_note
        text(ctx, self.spec.notes.end_title, E.x, Tt.y, Tt.size, Tt.font, WHITE, a, Tt.halo)
        for i, s in enumerate(self.spec.sources):
            text(ctx, s.text, E.x, Ln.y0 + i * Ln.dy, E.line_size, Ln.font, C["muted"], a, Ln.halo, role="credit")
        text(ctx, self.spec.notes.end_note, E.x, E.note_y, Nt.size, Nt.font, C["muted"], Nt.alpha * a, Nt.halo, role="credit")
