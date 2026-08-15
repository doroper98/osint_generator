"""승인된 `art_direction.json` → 씬에 바로 놓을 자산 PNG 생성 (Phase 3).

라이브러리 컷아웃(알파, 섀도 없음)에 **아트 디렉션이 정한 섀도 3축**을 입혀
씬용 PNG 를 만든다. 17 §1.7 의 "섀도는 런타임 처리" 는 *라이브러리 자산에 굽지
않는다* 는 뜻이고, 아트 디렉션이 승인으로 고정된 뒤의 빌드 합성은 그 요건을
만족한다 — 오히려 브라우저에서 하드에지 hatch/dots 섀도를 만드는 것보다
결정론적이고 정확하다.

사용::

    python hyperframes/shorts/build_scene_assets.py
    python hyperframes/shorts/build_scene_assets.py --force
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AD_JSON = HERE / "art_direction.json"
SHEET_JSON = REPO_ROOT / "design_sheets" / "shorts_collage_v1.json"
LIB_MANIFEST = REPO_ROOT / "assets" / "library" / "library_manifest.json"
OUT_DIR = HERE / "assets" / "cast"

#: 섀도가 캔버스 밖으로 나가 잘리지 않게 주는 여백 (실측 2026-08-15).
PAD = (70, 70, 70, 70)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    from schemas.models import ArtDirection, DesignSheet

    ad = ArtDirection(**json.loads(AD_JSON.read_text(encoding="utf-8")))
    sheet = DesignSheet(**json.loads(SHEET_JSON.read_text(encoding="utf-8")))
    lib = {p["person_id"]: p
           for p in json.loads(LIB_MANIFEST.read_text(encoding="utf-8"))["people"]}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made, skipped = 0, 0

    from workers.engraving_stylizer import compose_mono_shadow

    print(f"art_direction seed={ad.seed}  cast {len(ad.cast)}인\n")
    for c in ad.cast:
        if not c.person_id:
            print(f"  - {c.label}: 라이브러리 미보유 — 건너뜀")
            continue
        person = lib.get(c.person_id)
        if not person:
            print(f"  ! {c.label}: manifest 에 {c.person_id} 없음")
            continue

        src = REPO_ROOT / person["variants"][0]["path"]
        dest = OUT_DIR / f"{c.person_id}.png"
        if dest.exists() and not args.force:
            skipped += 1
            continue

        # paper=None → 투명 배경 유지. 씬 배경은 컴포지션이 깐다.
        out = compose_mono_shadow(
            src,
            accent=c.accent,
            shadow_mode=c.shadow_mode,
            shadow_fill=c.shadow_fill,
            paper=None,
            pad=PAD,
            seed=ad.seed,
        )
        out.save(dest, format="PNG", optimize=True)
        made += 1
        print(f"  + {dest.name:24} {c.shadow_mode:7} {c.shadow_fill:5} {c.accent}  "
              f"{out.size[0]}x{out.size[1]}  {dest.stat().st_size:,}B")

    print(f"\n[생성] {made}장 (건너뜀 {skipped}) → {OUT_DIR}")
    print(f"       종이 톤 = {ad.paper_tone} ({sheet.resolve_paper_tone(ad.paper_tone)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
