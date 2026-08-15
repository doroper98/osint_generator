"""공방 산출물을 알파 컷아웃으로 만들어 라이브러리에 승격 등록한다 (Phase 2 — 4·5단계).

    output/{pid}_mono_v01.png          codex 생성물 (순백 배경)
      → 배경 제거 (알파)
    assets/library/people/{pid}_mono_v01.png
      → AssetLibraryManifest 로 등록
    assets/library/library_manifest.json

**섀도는 굽지 않는다** (17 §1.7.0 방식 B) — 사전 자산은 mono 컷아웃 1장뿐이고
색·형태·채움은 렌더 시점에 `compose_mono_shadow` 가 얹는다. 실측(2026-08-15)으로
자산 1장에서 4종 변형이 3초/장에 나오는 것을 확인했다.

사용::

    python assets/library/workshop/promote_to_library.py --dry-run
    python assets/library/workshop/promote_to_library.py
    python assets/library/workshop/promote_to_library.py --only trump
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent          # assets/library/workshop
LIB_ROOT = HERE.parent                                  # assets/library
REPO_ROOT = HERE.parents[2]                             # 저장소 root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT = HERE / "output"
REFS = HERE / "references"
PHOTO_MANIFEST = REFS / "photo_manifest.json"
LIB_PEOPLE = LIB_ROOT / "people"
LIB_MANIFEST = LIB_ROOT / "library_manifest.json"

#: 컷아웃 알파의 최소 전경 비율. 이보다 낮으면 배경 제거가 인물을 먹은 것이다.
#: 실측(2026-08-15): 정상 컷아웃은 55~67%. 정장이 잘려나간 경우 30%대로 떨어졌다.
MIN_FG_RATIO = 0.45
MAX_FG_RATIO = 0.92

#: 배경 제거 색거리 허용치. `background_mask` 기본값(45)은 **일반 사진의 복잡한
#: 배경**을 상정한 값이라, 순백 배경 생성물에는 과하게 번져 어두운 정장 안쪽까지
#: 배경으로 먹어버린다 (실측: 최태원·워시·네타냐후·머스크가 얼굴만 남고 30%대로 붕괴).
#: 12 로 낮추면 깨진 4인이 전부 복구되고 멀쩡하던 인물은 변동 없다(63.6→64.1%).
BG_TOLERANCE = 12.0


def build_cutout(src: pathlib.Path, dest: pathlib.Path) -> dict:
    """순백 배경을 제거해 알파 컷아웃 PNG 로 저장하고 품질 지표를 돌려준다."""
    import numpy as np
    from PIL import Image

    from workers.engraving_stylizer import background_mask

    img = Image.open(src).convert("RGB")
    mask = background_mask(img, tolerance=BG_TOLERANCE)

    fg = float((mask > 0.5).mean())
    soft = mask[(mask > 0.02) & (mask < 0.98)]
    alpha = (np.clip(mask, 0.0, 1.0) * 255.0).round().astype("uint8")

    rgba = img.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha, mode="L"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(dest, format="PNG", optimize=True)

    return {
        "size": list(img.size),
        "fg_ratio": round(fg, 4),
        "soft_edge_px": int(soft.size),
        "bytes": dest.stat().st_size,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not PHOTO_MANIFEST.exists():
        print(f"error: {PHOTO_MANIFEST} 없음")
        return 1
    photos = json.loads(PHOTO_MANIFEST.read_text(encoding="utf-8"))["people"]

    jobs = []
    for png in sorted(OUT.glob("*_mono_v01.png")):
        pid = png.name.removesuffix("_mono_v01.png")
        if args.only and pid not in args.only:
            continue
        if pid not in photos:
            print(f"  ! {pid}: photo_manifest 에 권리 기록이 없어 건너뜀 (C9)")
            continue
        jobs.append((pid, png))

    if not jobs:
        print("대상 없음.")
        return 0

    print(f"대상 {len(jobs)}인\n")
    people: list[dict] = []
    warned: list[str] = []

    for pid, png in jobs:
        rec = photos[pid]
        dest = LIB_PEOPLE / f"{pid}_mono_v01.png"
        if args.dry_run:
            print(f"  {pid:18} {png.name} -> people/{dest.name}")
            continue

        info = build_cutout(png, dest)
        flag = ""
        if not (MIN_FG_RATIO <= info["fg_ratio"] <= MAX_FG_RATIO):
            flag = "  !! 전경 비율 이상 — 배경 제거 실패 의심"
            warned.append(pid)
        print(f"  {pid:18} {info['size'][0]}x{info['size'][1]}  "
              f"전경 {info['fg_ratio']*100:5.1f}%  경계 {info['soft_edge_px']:>6,}px  "
              f"{info['bytes']:>9,}B{flag}")

        people.append({
            "person_id": pid,
            "name_ko": rec["name_ko"],
            "name_en": rec.get("name_en", ""),
            "role": "",
            "aliases": [],
            "accent_hint": "",
            "source": {
                "url": rec.get("source_page", ""),
                "license": rec.get("license", ""),
                # 라이선스 필터를 통과해 수집된 것은 rights_clear, 사용자가 직접 준
                # 것은 manual_user_provided 로 구분해 남긴다 (C9).
                "rights_status": (
                    "manual_user_provided" if rec.get("adopted_by_user")
                    else "rights_clear"
                ),
                "credit": rec.get("credit") or rec.get("artist", ""),
                "note": (
                    f"원본 {rec.get('local_file', '')} / "
                    f"{'CC BY-SA — 파생물 SA 검토 필요' if 'SA' in rec.get('license', '') else 'CLOSING 크레딧 표기 대상' if 'CC BY' in rec.get('license', '') else '크레딧 의무 없음(PD/CC0)'}"
                ),
            },
            "variants": [{
                "style": "mono",
                "pose": "front",
                "path": f"assets/library/people/{dest.name}",
                "generator_version": "",
                "tool": "codex_imagegen",
                "prompt_ref": f"assets/library/workshop/output/{pid}_mono_v01.prompt.txt",
            }],
            "usage_count": 0,
        })

    if args.dry_run:
        return 0

    from schemas.models import AssetLibraryManifest

    manifest = AssetLibraryManifest(people=people)
    LIB_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    LIB_MANIFEST.write_text(
        manifest.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8"
    )

    print(f"\n[컷아웃] {len(people)}장 → {LIB_PEOPLE}")
    print(f"[manifest] {LIB_MANIFEST}  (Pydantic 검증 통과)")
    if warned:
        print(f"\n!! 전경 비율 이상 {len(warned)}건 — 육안 확인 필요: {warned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
