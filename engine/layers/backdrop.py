"""backdrop 이벤트 — 사진 배경 무대의 블러 배경 사진 (v5.1.0, back_and_forth D-0121 §B·D-0123 §1, 사용자 결정 D106·D108).

- 사진 = 미디어 레지스트리 kind photo·rights_clear 만(`validate_backdrop`, C9·G4-10). 파일을 직접 가리킬 수 없다.
- 그리기: 화면을 덮는(cover) 크기로 맞춘 뒤 블러(blur_px × k)·채도 낮춤(desaturate)을 한 번 만들어 두고(캐시),
  이벤트 길이에 걸친 느린 확대(1 → 1 + ken_burns, 연속 변환)로 그린다. 검정 덮개(dim)는 표면에 구워 둔다 —
  crossfade 로 두 장이 겹칠 때 덮개가 두 번 겹쳐 어두워지지 않게.
- 전환 = crossfade 만: 등장 t0 부터 crossfade_sec 동안 페이드 인, 끝 t1 부터 crossfade_sec 동안 페이드 아웃(render_frame 이
  t1 + crossfade_sec 까지 부른다). 줌 범프 없음. 캡션 바 없음(장식) — 크레딧은 credits.yaml.
수치는 전부 `rules stage_backdrop`(코드 리터럴 0, 15 P3).
"""

from __future__ import annotations

import cairo
from PIL import ImageEnhance, ImageFilter, ImageOps

from engine.assets import surf_from_pil
from engine.context import RenderCtx
from engine.credits import RightsError
from engine.media_registry import load_media_registry
from engine.projection import View
from engine.style import BACKDROP, H_OUT, W_OUT
from engine.timebase import smooth


def validate_backdrop(e: dict, assets: dict | None = None):  # noqa: ANN201 — schemas.media_models.MediaAsset
    """배경 사진 권리 게이트 — 레지스트리 참조·종류(photo)·권리 상태(rights_clear). 어기면 RightsError(렌더 전)."""
    img = e.get("img")
    where = f"backdrop t0={e.get('t0', '?')}"
    reg = assets if assets is not None else load_media_registry()
    if not img or img not in reg:
        raise RightsError(f"배경 사진이 미디어 레지스트리에 없음: img={img!r} ({where}) — 권리 기록 있는 실사진만(C9·G4-10)")
    a = reg[img]
    if a.kind != BACKDROP.kind:
        raise RightsError(f"배경 사진 종류 불일치: {img}.kind={a.kind} ≠ {BACKDROP.kind} ({where})")
    if a.rights_status != "rights_clear":
        raise RightsError(f"권리 미확인 배경 사진({a.rights_status}): {img} ({where}) — 렌더 금지(C9)")
    if not a.file:
        raise RightsError(f"배경 사진 파일이 레지스트리에 없음: {img} ({where})")
    return a


def backdrop_alpha(t: float, e: dict) -> float:
    """crossfade — t0 부터 페이드 인, t1 부터 페이드 아웃(둘 다 crossfade_sec)."""
    xf = BACKDROP.crossfade_sec
    return min(smooth((t - e["t0"]) / xf), 1 - smooth((t - e["t1"]) / xf))


def backdrop_surface(R: RenderCtx, img: str) -> tuple[cairo.ImageSurface, float]:  # noqa: N803
    """장치 해상도 × (1 + ken_burns) 로 화면을 덮게 맞춘 블러·채도 낮춤·덮개(dim) 표면(캐시) → (표면, 장치 배율 k)."""
    cache = R.cache.setdefault("backdrop_surf", {})
    k = R.out.k
    if img not in cache:
        m = R.assets.media_assets[img]
        key = f"media:{m.file}"
        R.assets.load_image(key)
        s = 1 + BACKDROP.ken_burns
        size = (max(1, round(W_OUT * k * s)), max(1, round(H_OUT * k * s)))
        im = ImageOps.fit(R.assets.img[key].convert("RGB"), size)
        im = ImageEnhance.Color(im).enhance(1 - BACKDROP.desaturate)
        im = im.filter(ImageFilter.GaussianBlur(BACKDROP.blur_px * k))
        im = ImageEnhance.Brightness(im).enhance(1 - BACKDROP.dim)   # 검정 덮개 알파 dim 과 같은 값
        cache[img] = surf_from_pil(im)
    return cache[img][0], k


def draw_backdrop(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    a = backdrop_alpha(t, e)
    if a <= 0.001:
        return
    surf, k = backdrop_surface(R, e["img"])
    span = max(e["t1"] - e["t0"], 1e-6)
    z = 1 + BACKDROP.ken_burns * min(1.0, max(0.0, (t - e["t0"]) / span))   # 1 → 1 + ken_burns(연속)
    sw, sh = surf.get_width() / k, surf.get_height() / k   # 설계 px
    ctx.save()
    ctx.translate(W_OUT / 2, H_OUT / 2)
    ctx.scale(z / (1 + BACKDROP.ken_burns) / k, z / (1 + BACKDROP.ken_burns) / k)
    ctx.set_source_surface(surf, -sw * k / 2, -sh * k / 2)
    ctx.paint_with_alpha(a)
    ctx.restore()


def backdrop_report(events: list[dict], assets: dict) -> dict:
    """배경 사진 검사·provenance 한 결과(v5.1.0 D-0123 §3). photos = 등장 순 img, rights = 권리 문제(checks backdrop_rights hard),
    repeat = 연속 같은 사진·서로 다른 사진 수가 [min_photos, max_photos] 밖(checks backdrop_repeat hard). 배경이 없으면 빈 dict."""
    bs = sorted((e for e in events if e["type"] == "backdrop"), key=lambda e: e["t0"])
    if not bs:
        return {}
    rights: list[str] = []
    for e in bs:
        try:
            validate_backdrop(e, assets)
        except RightsError as ex:
            rights.append(f"[backdrop-rights] {ex}")
    repeat = [f"[backdrop-repeat] t={b['t0']:.2f} 앞 배경과 같은 사진 {b['img']!r} — 연속 같은 사진 금지"
              for a, b in zip(bs, bs[1:]) if a["img"] == b["img"]]
    uniq = list(dict.fromkeys(e["img"] for e in bs))
    if not BACKDROP.min_photos <= len(uniq) <= BACKDROP.max_photos:
        repeat.append(f"[backdrop-photos] 서로 다른 배경 사진 {len(uniq)}장 — rules stage_backdrop {BACKDROP.min_photos}~{BACKDROP.max_photos}장")
    return {"photos": [{"img": e["img"], "t0": round(e["t0"], 2), "t1": round(e["t1"], 2)} for e in bs], "unique": len(uniq),
            "rights": rights, "repeat": repeat}


__all__ = ["backdrop_alpha", "backdrop_report", "backdrop_surface", "draw_backdrop", "validate_backdrop"]
