"""여러 곳 연속 타격 샘플(지도 없음, 개략 상대 배치). render_demo 의 기하·토큰을 그대로 쓴다.
A 구간: 문장 하나 = 비행 하나(5곳 차례로), 맞은 자리는 표식이 남아 쌓인다.
B 구간(요약 컷 대안): 비행 없이 표식만 차례로 켜지는 '사흘에 한 번' 몽타주."""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cairo

import render_demo as R
from render_demo import (AMBER, BG, FLIGHT, INK, K, MONO, TEAL, W, H, FPS, clamp01, draw_boom, draw_flight, draw_inset,
                         ease_out, text, vignette, window)

OUT = Path(__file__).parent
FLIGHT["icon"]["size"] = {"drone": 16, "missile": 18, "jet": 19}   # 지도 위 크기 감(계획값 11~14 와 시험값 24~30 사이)
FLIGHT["origin"]["r_px"] = 30; FLIGHT["origin"]["alpha"] = 0.45

ORIGIN = (235, 335)   # 우크라이나 북동부 개략(한 자리에서 계속 숨 쉰다)
SITES = [  # 서부 러시아 개략 상대 배치(설계 px). 사실 문구는 로이터·IEA 집계 범위 안
    dict(name="키리시", sub="전면 중단(로이터 집계)", x=430, y=120),
    dict(name="랴잔", sub="처리량의 약 5% · 10월 15일 재타격", x=478, y=212, inset="inset_ryazan.png", note="위성 · 2026. 10 · NASA GIBS HLS S30"),
    dict(name="노보쿠이비셰프스크", sub="상압증류탑 2기 손상", x=640, y=248),
    dict(name="사라토프", sub="피격(우크라 국방부 발표)", x=560, y=292),
    dict(name="볼고그라드", sub="정격의 4분의 1 가동", x=520, y=345),
]
T_TITLE = 1.5; GAP = 5.2
EVENTS = []
for i, s in enumerate(SITES):
    t0 = T_TITLE + 1.6 + i * GAP
    EVENTS.append(dict(kind="drone", col=TEAL, ox=ORIGIN[0], oy=ORIGIN[1], tx=s["x"], ty=s["y"], label=s["name"], sub=s["sub"],
                       t0=t0, t1=999.0, inset_png=str(OUT / s["inset"]) if s.get("inset") else None, inset_note=s.get("note", "")))
T_A_END = EVENTS[-1]["t0"] + FLIGHT["dur_sec"] + 3.0
T_B = T_A_END + 1.0          # B 구간 시작(암전 뒤)
B_STAGGER = 0.9
T_END = T_B + 1.0 + len(SITES) * B_STAGGER + 3.5
TOTAL = T_END + 3.0


def draw_hit_marker(ctx, t, s, t_hit, keep_label=True):
    """맞은 자리 표식(marker icon: boom 에 해당) — 작은 호박색 점 + 얇은 링, 착탄 뒤 계속 남는다."""
    if t < t_hit: return
    a = clamp01((t - t_hit) / 0.5)
    x, y = s["x"] * K, s["y"] * K
    ctx.arc(x, y, 3.0 * K, 0, 2 * math.pi); ctx.set_source_rgba(*AMBER, 0.95 * a); ctx.fill()
    ctx.arc(x, y, 6.5 * K, 0, 2 * math.pi); ctx.set_source_rgba(*AMBER, 0.45 * a); ctx.set_line_width(1.2 * K); ctx.stroke()
    if keep_label:
        text(ctx, s["name"], x + 10 * K, y - 3 * K, 12, a=a, bold=True)
        text(ctx, s["sub"], x + 10 * K, y + 10 * K, 9.5, a=0.85 * a)


def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    ctx.set_source_rgb(*BG); ctx.paint()
    if t < T_A_END + 0.5:   # ---- A 구간
        for ev, s in zip(EVENTS, SITES):
            t_hit = ev["t0"] + FLIGHT["dur_sec"]
            if ev["t0"] - FLIGHT["origin"]["pulse_sec"] <= t:
                ev2 = dict(ev, t1=T_A_END + 1)
                draw_flight(ctx, t, ev2)
                draw_hit_marker(ctx, t, s, t_hit)
                if ev["inset_png"]:
                    draw_inset(ctx, t, ev2, t_hit)
        da = window(t, T_TITLE, T_A_END, 0.4, 0.4)
        text(ctx, "2026.01 – 10", W - 14 * K, 20 * K, 11, a=0.95 * da, font=MONO, align="right")
        text(ctx, "A · 문장 하나 = 비행 하나, 맞은 자리는 남는다", 14 * K, H - 14 * K, 9.5, a=0.7 * da, halo=2)
    if T_B - 0.5 <= t:        # ---- B 구간(몽타주 대안)
        for i, s in enumerate(SITES):
            th = T_B + 1.0 + i * B_STAGGER
            draw_boom(ctx, s["x"] * K, s["y"] * K, t - th)
            draw_hit_marker(ctx, t, s, th, keep_label=False)
            if t >= th:
                text(ctx, s["name"], s["x"] * K + 10 * K, s["y"] * K + 4 * K, 10.5, a=clamp01((t - th) / 0.5), bold=True)
        db = window(t, T_B, T_END, 0.5, 0.5)
        text(ctx, "사흘에 한 번", W / 2, 60 * K, 22, a=db, align="center", bold=True)
        text(ctx, "B · 요약 컷 대안 — 비행 없이 표식만 차례로", 14 * K, H - 14 * K, 9.5, a=0.7 * db, halo=2)
        text(ctx, "2026.01 – 08", W - 14 * K, 20 * K, 11, a=0.95 * db, font=MONO, align="right")
    # 암전(A→B)
    d = abs(t - T_B + 0.3)
    if d < 0.4:
        ctx.set_source_rgba(0, 0, 0, 1 - d / 0.4); ctx.rectangle(0, 0, W, H); ctx.fill()
    vignette(ctx)
    if t < T_TITLE:
        a = window(t, 0, T_TITLE, 0.3, 0.4)
        text(ctx, "여러 곳 타격 샘플 — 지도 없음(개략 상대 배치)", W / 2, H / 2, 20, a=a, align="center", bold=True)
        text(ctx, "출발 위치 하나에서 다섯 곳으로 차례로 · 아이콘은 지도 위 크기 감", W / 2, H / 2 + 26 * K, 11, a=0.85 * a, align="center")
    if t > TOTAL - 3.0:
        a = window(t, TOTAL - 3.0, TOTAL, 0.5, 0.6)
        ctx.set_source_rgba(0, 0, 0, 0.85 * a); ctx.rectangle(0, 0, W, H); ctx.fill()
        text(ctx, "시험본 · 본편 아님", 60 * K, 190 * K, 15, a=a, bold=True, halo=0)
        text(ctx, "배치는 개략(지도 없음) · 비행 경로·출발 위치는 개략 표현 · 위성: NASA GIBS HLS(공공 저작물)", 60 * K, 215 * K, 10.5, a=0.9 * a, halo=0)
        text(ctx, "출처: 로이터 집계 · IEA 2026 · 우크라이나 국방부 발표(사라토프, 독립 검증 전)", 60 * K, 232 * K, 9.5, a=0.8 * a, halo=0)
    return surf


def main():
    frames = OUT / "frames_multi"; frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"): f.unlink()
    n = int(TOTAL * FPS)
    for i in range(n):
        frame(i / FPS).write_to_png(str(frames / f"f{i:05d}.png"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(OUT / "multi_demo.mp4")], check=True)
    times = [e["t0"] + 1.3 for e in EVENTS] + [T_A_END - 0.5, T_B + 2.0, T_B + 4.0, T_END - 1.0]
    cols, cw, ch = 3, W // 3, H // 3
    rows = math.ceil(len(times) / cols)
    sheet = cairo.ImageSurface(cairo.FORMAT_RGB24, cw * cols, ch * rows); sc = cairo.Context(sheet)
    for j, tt in enumerate(times):
        sc.save(); sc.translate((j % cols) * cw, (j // cols) * ch); sc.scale(1 / 3, 1 / 3); sc.set_source_surface(frame(tt), 0, 0); sc.paint(); sc.restore()
        sc.select_font_face(MONO); sc.set_font_size(14); sc.move_to((j % cols) * cw + 8, (j // cols) * ch + 18); sc.set_source_rgb(1, 1, 1); sc.show_text(f"t={tt:.1f}s")
    sheet.write_to_png(str(OUT / "multi_demo_sheet.png"))
    print("total", round(TOTAL, 1), "s", n, "frames")


if __name__ == "__main__":
    main()
