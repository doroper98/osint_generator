"""영상 제작 중 만든 자산을 저장소 공용 자산으로 승격 (v5.6.0, 사용자 결정 2026-10-04).

사용자 지시: "영상을 만들며 제작한 자산들 하나하나 자산으로 잘 보관 — 다른 영상에서 필요할 때 새로 제작하는 게 아니라 자산으로 활용".
프로젝트 `assets/` 는 저장소에 올리지 않는다(.gitignore). 그래서 프로젝트에서 만든 초상·휘장은 이 도구로 공용 자리에 옮겨 둔다.

    python tools/asset_library.py promote projects/<pid>     # 초상 → assets/library/people, 휘장 → assets/emblems/files
    python tools/asset_library.py check projects/<pid>       # 승격 안 된 자산 목록(있으면 exit 1)

- 초상: 프로젝트 `assets/portraits/<pid>.png` 중 라이브러리에 없는 인물 → `assets/library/people/<pid>_mono_v01.png` +
  `library_manifest.json` people 항목(권리 = 프로젝트 rights_registry people.<pid>: 출처 URL·라이선스·작가·가공 기록).
  권리 기록이 없으면 승격하지 않는다(C9 — 출처 모르는 자산은 공용으로 만들지 않는다).
- 휘장: 프로젝트 `assets/emblems/<file>` 중 휘장 레지스트리 decision=use 인 것 → `assets/emblems/files/<file>`.
  다음 영상에서는 `tools/commons_fetch.py emblems` 가 이 파일을 복사한다(재다운로드·재가공 없음).
- 라이브러리 인물은 엔티티에 자동 등재된다(engine.entities) — assets/entities.yaml 은 국기·직함 보강만.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LIB = REPO / "assets" / "library" / "library_manifest.json"
PEOPLE_DIR = REPO / "assets" / "library" / "people"
EMBLEM_FILES = REPO / "assets" / "emblems" / "files"
EMBLEM_REGISTRY = REPO / "assets" / "emblems" / "registry.json"


def _rights(proj: Path) -> dict:
    p = proj / "assets" / "rights_registry.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _entity_names(pid: str) -> tuple[str, str]:
    import yaml  # noqa: PLC0415

    ents = yaml.safe_load((REPO / "assets" / "entities.yaml").read_text(encoding="utf-8"))["entities"]
    e = ents.get(pid) or {}
    names = e.get("names") or [pid]
    return names[0], e.get("role_default", "")


def pending(proj: Path) -> dict[str, list[str]]:
    """승격 안 된 자산 — {"people": [...], "emblems": [...]}."""
    lib = json.loads(LIB.read_text(encoding="utf-8"))
    have = {p["person_id"] for p in lib["people"]}
    people = sorted(p.stem for p in (proj / "assets" / "portraits").glob("*.png") if p.stem not in have)
    reg = json.loads(EMBLEM_REGISTRY.read_text(encoding="utf-8"))["emblems"]
    emb = sorted(e["file"] for e in reg.values()
                 if e.get("decision") == "use" and e.get("file") and (proj / "assets" / "emblems" / e["file"]).exists()
                 and not (EMBLEM_FILES / e["file"]).exists())
    return {"people": people, "emblems": emb}


def promote(proj: Path, version: int = 1) -> dict[str, list[str]]:
    """version = 초상 변형 번호(v5.15.0 D-0160 — 같은 인물의 다른 사진이면 2 이상, 파일 `<pid>_mono_vNN.png`)."""
    from schemas.models import AssetLibraryManifest  # noqa: PLC0415

    todo = pending(proj)
    rights = _rights(proj)
    lib = json.loads(LIB.read_text(encoding="utf-8"))
    done: dict[str, list[str]] = {"people": [], "emblems": [], "skipped": []}
    for pid in todo["people"]:
        r = rights.get("people", {}).get(pid)
        if not r or r.get("src") == "repo_library" or not r.get("url"):
            done["skipped"].append(f"people.{pid}: 권리 기록(출처 URL) 없음 — 승격 안 함")
            continue
        dest = PEOPLE_DIR / f"{pid}_mono_v{version:02d}.png"
        shutil.copyfile(proj / "assets" / "portraits" / f"{pid}.png", dest)
        name_ko, role = _entity_names(pid)
        proc = r.get("processing") or {}
        lib["people"].append({
            "person_id": pid, "name_ko": name_ko, "name_en": "", "role": role, "aliases": [], "accent_hint": "",
            "source": {"url": r["url"], "license": r["license"], "rights_status": r.get("rights_status") or "rights_clear",
                       "credit": r.get("artist", ""), "note": f"{proj.name} 에서 승격(v5.6.0) · 원본 {proc.get('source_file', '')}",
                       **({"user_exception": r["user_exception"], "exception": r.get("exception", "")} if r.get("user_exception") else {})},
            "variants": [{"style": "mono", "pose": "front", "path": (dest.relative_to(REPO) if dest.is_relative_to(REPO) else dest).as_posix(), "generator_version": "",
                          "tool": f"{proc.get('tool', 'tools/portrait_fallback.py')} --style {proc.get('style', 'engraving')}",
                          "prompt_ref": "", "normalized": True}],   # v5.15.1 D-0164 — 프로젝트 초상 = 정규화 완료본
            "usage_count": 0,
        })
        done["people"].append(pid)
    AssetLibraryManifest.model_validate(lib)
    LIB.write_text(json.dumps(lib, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    EMBLEM_FILES.mkdir(parents=True, exist_ok=True)
    for f in todo["emblems"]:
        shutil.copyfile(proj / "assets" / "emblems" / f, EMBLEM_FILES / f)
        done["emblems"].append(f)
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("promote", "check"))
    ap.add_argument("proj", type=Path)
    ap.add_argument("--version", type=int, default=1, help="초상 변형 번호(같은 인물의 다른 사진이면 2 이상, v5.15.0 D-0160)")
    a = ap.parse_args(argv)
    proj = a.proj.resolve()
    if a.cmd == "check":
        p = pending(proj)
        print(json.dumps(p, ensure_ascii=False))
        return 1 if p["people"] or p["emblems"] else 0
    print(json.dumps(promote(proj, a.version), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
