"""타격 애니메이션 + 위성 인셋 시험 영상 (지도 없음). D-0206 flight 이벤트 기하의 독립 시제품.
렌더 수치는 D-0206 §3 제안 토큰(480p 설계 px × k). 엔진 코드와 무관한 scratch 스크립트."""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import cairo

OUT = Path(__file__).parent
W, H = 1280, 720
K = H / 480.0                      # 설계 px(480p) → 장치 px
FPS = 30

# --- D-0206 §3 토큰(설계 px) ---
FLIGHT = dict(dur_sec=2.4, bulge_ratio=0.18,
              trail=dict(width=2.0, dash=(7, 5), alpha=0.9, fade_sec=1.4),
              origin=dict(r_px=40, alpha=0.55, pulse_sec=1.6),
              icon=dict(size={"drone": 30, "missile": 28, "jet": 30}, halo=2.4,   # 시험본: 지도 없음이라 형태 확인용으로 2배
                        drone=[(0, -7.4), (0.9, -6.4), (0.9, -3.4), (4.6, 3.6), (5.4, 3.4), (5.4, 5.9), (4.2, 5.9), (0.9, 5.3), (0.9, 6.8), (1.7, 7.0), (1.7, 7.5),
                               (-1.7, 7.5), (-1.7, 7.0), (-0.9, 6.8), (-0.9, 5.3), (-4.2, 5.9), (-5.4, 5.9), (-5.4, 3.4), (-4.6, 3.6), (-0.9, -3.4), (-0.9, -6.4)],   # 샤헤드-136/게란-2 상면 실루엣(델타익·동체·날개 끝 핀·후방 프로펠러)
                        drone_body=[(0.9, -3.4), (0.9, 5.3), (-0.9, 5.3), (-0.9, -3.4)],   # 동체 구분선(안쪽 어두운 선)
                        missile=[(0, -7), (1.2, -5.5), (1.2, -0.5), (3.2, 0.5), (3.2, 1.3), (1.2, 1.0), (1.2, 4.5), (3.4, 6.2), (3.4, 7), (1.2, 6.6), (1.2, 7.2),
                                 (-1.2, 7.2), (-1.2, 6.6), (-3.4, 7), (-3.4, 6.2), (-1.2, 4.5), (-1.2, 1.0), (-3.2, 1.3), (-3.2, 0.5), (-1.2, -0.5), (-1.2, -5.5)],   # 순항미사일 상면(동체·중간 날개·꼬리 핀)
                        jet=[(0, -7), (2, -2), (7, 2), (2, 3), (1.5, 6), (3, 7), (-3, 7), (-1.5, 6), (-2, 3), (-7, 2), (-2, -2)]),
              inset=dict(w_px=118, gap_px=10, hold_sec=3.0, fade=(0.35, 0.45)))
AMBER = (1.0, 0.70, 0.28)          # rules accents amber #ffb347
RU = (0.93, 0.36, 0.33)
TEAL = (0.36, 0.80, 0.82)
BG = (0.035, 0.045, 0.068)         # stage_timeline.bg_rgb 와 같은 어두운 바탕
INK = (0.92, 0.92, 0.90)


def fc_has(family: str) -> bool:
    r = subprocess.run(["fc-match", family], capture_output=True, text=True)
    return family.split()[0].lower() in r.stdout.lower()


SANS = next((f for f in ("IBM Plex Sans KR", "Noto Sans CJK KR", "WenQuanYi Zen Hei") if fc_has(f)), "sans-serif")
MONO = "IBM Plex Mono" if fc_has("IBM Plex Mono") else "DejaVu Sans Mono"


def clamp01(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def smooth(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def window(t, t0, t1, fin=0.5, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(smooth((t - t0) / fin) if fin > 0 else 1, smooth((t1 - t) / fout) if fout > 0 else 1)


def text(ctx, s, x, y, size, col=INK, a=1.0, font=None, bold=False, halo=3.0, align="left"):
    ctx.select_font_face(font or SANS, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size * K)
    ext = ctx.text_extents(s)
    if align == "right": x -= ext.x_advance
    elif align == "center": x -= ext.x_advance / 2
    ctx.move_to(x, y)
    ctx.text_path(s)
    if halo:
        ctx.set_source_rgba(0, 0, 0, 0.75 * a); ctx.set_line_width(halo * K); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgba(*col, a); ctx.fill()
    return ext.x_advance


def bezier(s, c, e, u):
    return ((1-u)**2*s[0] + 2*(1-u)*u*c[0] + u*u*e[0], (1-u)**2*s[1] + 2*(1-u)*u*c[1] + u*u*e[1])


def icon_path(ctx, kind, size):
    """진행 방향 = -y. 다각형은 설계 px, size 로 긴 변 정규화."""
    ic = FLIGHT["icon"]
    pts = ic[kind]; span = max(abs(p[1]) for p in pts) * 2; sc = size / span
    ctx.move_to(pts[0][0]*sc, pts[0][1]*sc)
    for p in pts[1:]: ctx.line_to(p[0]*sc, p[1]*sc)
    ctx.close_path()


def draw_icon(ctx, kind, size, col):
    F = FLIGHT
    icon_path(ctx, kind, size)
    ctx.set_source_rgba(0, 0, 0, 0.8); ctx.set_line_width(F["icon"]["halo"]*K); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgba(*col, 1); ctx.fill()
    if kind == "drone":   # 동체 구분선 — 날개와 동체를 나눠 '화살표'로 안 보이게
        pts = F["icon"]["drone_body"]; span = 14.9; sc = size / span
        ctx.move_to(pts[0][0]*sc, pts[0][1]*sc); ctx.line_to(pts[1][0]*sc, pts[1][1]*sc)
        ctx.move_to(pts[2][0]*sc, pts[2][1]*sc); ctx.line_to(pts[3][0]*sc, pts[3][1]*sc)
        ctx.set_source_rgba(0, 0, 0, 0.55); ctx.set_line_width(0.9*K); ctx.stroke()


def draw_boom(ctx, x, y, lt, col=AMBER):
    """engine/layers/effects.py draw_boom 과 같은 기하(링 3겹)."""
    if lt < 0 or lt > 1.6: return
    for k in range(3):
        r = (6 + 50 * ease_out((lt - k * 0.12) / 1.2)) * K
        ctx.arc(x, y, max(r, 0.1), 0, 2*math.pi)
        ctx.set_source_rgba(*col, 0.6 * (1 - clamp01(lt / 1.6)))
        ctx.set_line_width(2 * K); ctx.stroke()


def draw_flight(ctx, t, ev):
    t0 = ev["t0"]; col = ev["col"]; F = FLIGHT
    s = (ev["ox"]*K, ev["oy"]*K); e = (ev["tx"]*K, ev["ty"]*K)
    dx, dy = e[0]-s[0], e[1]-s[1]; d = math.hypot(dx, dy)
    n = (-dy/d, dx/d) if d else (0, 0)
    c = ((s[0]+e[0])/2 + n[0]*d*F["bulge_ratio"], (s[1]+e[1])/2 + n[1]*d*F["bulge_ratio"])
    t_hit = t0 + F["dur_sec"]
    # 1) 출발 발광(점·라벨 없음)
    O = F["origin"]
    if t0 - O["pulse_sec"] <= t <= t0 + 0.4:
        a = window(t, t0 - O["pulse_sec"], t0 + 0.4, 0.5, 0.4)
        br = 0.75 + 0.25*math.sin((t - t0) * 2*math.pi / O["pulse_sec"])
        g = cairo.RadialGradient(s[0], s[1], 0, s[0], s[1], O["r_px"]*K)
        g.add_color_stop_rgba(0, *col, O["alpha"]*a*br); g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g); ctx.arc(s[0], s[1], O["r_px"]*K, 0, 2*math.pi); ctx.fill()
    # 2) 꼬리선(점선 = 개략)
    p = ease_out((t - t0) / F["dur_sec"]) if t >= t0 else 0.0
    T = F["trail"]
    ta = T["alpha"] * (1.0 if t < t_hit else max(0.0, 1 - (t - t_hit)/T["fade_sec"]))
    if p > 0 and ta > 0:
        ctx.move_to(*s)
        for i in range(1, 33):
            ctx.line_to(*bezier(s, c, e, p * i/32))
        ctx.set_dash([v*K for v in T["dash"]]); ctx.set_line_width(T["width"]*K); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*col, ta); ctx.stroke(); ctx.set_dash([])
    # 3) 아이콘
    if 0 < p < 1:
        x, y = bezier(s, c, e, p); x2, y2 = bezier(s, c, e, min(1, p + 0.01))
        ang = math.atan2(y2 - y, x2 - x) + math.pi/2
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
        draw_icon(ctx, ev["kind"], F["icon"]["size"][ev["kind"]] * K, col)
        ctx.restore()
    # 4) 착탄 링
    if ev.get("impact", True):
        draw_boom(ctx, e[0], e[1], t - t_hit)
    return t_hit


def draw_marker(ctx, t, ev, t_show):
    a = window(t, t_show, ev["t1"], 0.4, 0.5)
    if a <= 0: return
    x, y = ev["tx"]*K, ev["ty"]*K
    ctx.arc(x, y, 3.2*K, 0, 2*math.pi); ctx.set_source_rgba(0, 0, 0, 0.7*a); ctx.set_line_width(2.5*K); ctx.stroke_preserve()
    ctx.set_source_rgba(*INK, a); ctx.fill()
    text(ctx, ev["label"], x + 10*K, y - 4*K, 13, a=a, bold=True)
    text(ctx, ev["sub"], x + 10*K, y + 11*K, 10.5, a=0.9*a)


def draw_inset(ctx, t, ev, t_hit):
    I = FLIGHT["inset"]; t0 = t_hit - 0.2; t1 = t_hit + I["hold_sec"] + 1.6
    a = window(t, t0, t1, *I["fade"])
    if a <= 0: return
    w = I["w_px"]*K; h = w * 0.72
    x = ev["tx"]*K - w/2; y = ev["ty"]*K - h - 34*K   # 마커 위(라벨·부제와 겹치지 않게)
    img = ev.get("inset_png")
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    if img and Path(img).exists():
        surf = cairo.ImageSurface.create_from_png(img); sc = max(w/surf.get_width(), h/surf.get_height())
        ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.set_source_surface(surf, 0, 0); ctx.paint_with_alpha(a); ctx.restore()
    else:
        ctx.set_source_rgba(0.18, 0.2, 0.24, a); ctx.rectangle(x, y, w, h); ctx.fill()
        for i in range(0, int(w), int(14*K)):   # 자리표시 격자
            ctx.move_to(x+i, y); ctx.line_to(x+i, y+h)
        for j in range(0, int(h), int(14*K)):
            ctx.move_to(x, y+j); ctx.line_to(x+w, y+j)
        ctx.set_source_rgba(1, 1, 1, 0.07*a); ctx.set_line_width(1); ctx.stroke()
        text(ctx, "위성 타일 자리", x + w/2, y + h/2 - 4*K, 10.5, a=a, align="center", halo=0)
        text(ctx, "권리 확인 뒤 삽입", x + w/2, y + h/2 + 9*K, 8.5, a=0.8*a, align="center", halo=0)
    ctx.restore()
    ctx.rectangle(x, y, w, h); ctx.set_source_rgba(1, 1, 1, 0.55*a); ctx.set_line_width(1*K); ctx.stroke()
    text(ctx, ev["inset_note"], x, y - 5*K, 8.5, a=0.85*a, halo=2)


def vignette(ctx):
    g = cairo.RadialGradient(W/2, H/2, H*0.45, W/2, H/2, H*0.95)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()


# --- 시험 내용: 세 사건(드론·미사일·전투기 아이콘 각 1회). 좌표는 지도가 없으므로 화면 배치값(설계 px) ---
LEN = 8.0
EVENTS = [
    dict(kind="drone", col=TEAL, ox=90, oy=330, tx=540, ty=245, label="랴잔 정유소", sub="우크라이나 드론 · 러시아 처리량의 약 5%(로이터)",
         date="2026.10.15", inset_note="위성 · 2026. 10 · NASA HLS(Sentinel-2/Landsat)"),
    dict(kind="missile", col=RU, ox=110, oy=350, tx=560, ty=250, label="라스라판 LNG", sub="이란 미사일 · 콜드박스 2기 손상(로이터)",
         date="2026.03", inset_note="위성 · 2026. 03 · NASA HLS(Sentinel-2/Landsat)"),
    dict(kind="jet", col=AMBER, ox=80, oy=370, tx=530, ty=240, label="하르그섬", sub="미군 공습(군사 표적) · 석유 시설 미타격",
         date="2026.04", inset_note="위성 · 2026. 04 · NASA HLS(Sentinel-2/Landsat)"),
]
for i, ev in enumerate(EVENTS):
    ev["start"] = 1.5 + i * LEN; ev["t0"] = ev["start"] + 1.8; ev["t1"] = ev["start"] + LEN - 0.3

TOTAL = 1.5 + len(EVENTS) * LEN + 3.0


def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    ctx.set_source_rgb(*BG); ctx.paint()
    for ev in EVENTS:
        if ev["start"] - 0.4 <= t <= ev["t1"] + 0.5:
            t_hit = draw_flight(ctx, t, ev)
            draw_marker(ctx, t, ev, t_hit - 0.3)
            draw_inset(ctx, t, ev, t_hit)
            da = window(t, ev["start"], ev["t1"], 0.4, 0.4)
            text(ctx, ev["date"], W - 14*K, 20*K, 11, a=0.95*da, font=MONO, align="right")   # 모서리에는 날짜만
            # 장면 사이 짧은 암전(dip)
    for ev in EVENTS[1:]:
        d = abs(t - ev["start"] + 0.2)
        if d < 0.35:
            ctx.set_source_rgba(0, 0, 0, 1 - d/0.35); ctx.rectangle(0, 0, W, H); ctx.fill()
    vignette(ctx)
    if t < 1.5:   # 제목 카드(시험용)
        a = window(t, 0, 1.5, 0.3, 0.4)
        text(ctx, "타격 애니메이션 시험 — 지도 없음", W/2, H/2, 20, a=a, align="center", bold=True)
        text(ctx, "D-0206 flight 이벤트 기하 · 출발 위치는 개략(발광), 경로는 점선", W/2, H/2 + 26*K, 11, a=0.85*a, align="center")
    if t > TOTAL - 3.0:
        a = window(t, TOTAL - 3.0, TOTAL, 0.5, 0.6)
        ctx.set_source_rgba(0, 0, 0, 0.85*a); ctx.rectangle(0, 0, W, H); ctx.fill()
        text(ctx, "시험본 · 본편 아님", 60*K, 190*K, 15, a=a, bold=True, halo=0)
        text(ctx, "비행 경로·출발 위치는 개략 표현. 위성 타일은 권리 확인(Sentinel-2·NASA) 뒤 삽입 예정.", 60*K, 215*K, 10.5, a=0.9*a, halo=0)
        text(ctx, "출처: 로이터 집계(랴잔·라스라판) · CNN 2026.04.07(하르그섬) · 아이콘·링·꼬리선은 코드 벡터", 60*K, 232*K, 9.5, a=0.8*a, halo=0)
    return surf


def main():
    frames = OUT / "frames"; frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"): f.unlink()
    n = int(TOTAL * FPS)
    for i in range(n):
        frame(i / FPS).write_to_png(str(frames / f"f{i:05d}.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(OUT / "strike_demo.mp4")], check=True)
    # 컨택트 시트(사건마다 4시각)
    times = []
    for ev in EVENTS:
        times += [ev["t0"] - 0.8, ev["t0"] + 1.2, ev["t0"] + 2.6, ev["t0"] + 4.2]
    cols, cw, ch = 4, W//3, H//3
    rows = math.ceil(len(times)/cols)
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, cw*cols, ch*rows); sc = cairo.Context(sheet)
    for j, tt in enumerate(times):
        sc.save(); sc.translate((j % cols)*cw, (j//cols)*ch); sc.scale(1/3, 1/3); sc.set_source_surface(frame(tt), 0, 0); sc.paint(); sc.restore()
        sc.select_font_face(MONO); sc.set_font_size(14); sc.move_to((j % cols)*cw + 8, (j//cols)*ch + 18)
        sc.set_source_rgb(1, 1, 1); sc.show_text(f"t={tt:.1f}s")
    sheet.write_to_png(str(OUT / "strike_demo_sheet.png"))
    print("font:", SANS, "| total", TOTAL, "s |", n, "frames")


if __name__ == "__main__":
    main()
