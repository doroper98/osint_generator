"""증거 카드 원본 받기(v7.4.0 전쟁사 W4) — projects/<pid>/media.json 레코드의 Commons 파일 → media_src/<file>, 원본 md5 → source_hash.

    python -m sketch.war.fetch projects/<pid> [--tags-only]

v2(D-0606 §2): 파일 페이지 라이선스 분류를 license_tags 로 자동 기록한다. 손으로 적은 photo_license 와 다르면 레코드 검증이
[license-mismatch] 로 실패한다(MediaAsset). --tags-only = 원본은 다시 받지 않고 분류만 갱신.

레코드 tool.params: {commons_title: "File:…", width: 1280}. 라이선스·Restrictions 판정은 tools.commons_fetch(07 §3.2) 그대로,
그 위에 rules war_history.rights.allowed_licenses(MediaAsset 검증). 레코드 형식이 틀리면 받지 않는다(P6).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from schemas.media_models import MediaRegistryFile
from sketch.war.scene import MEDIA_DIR, MEDIA_FILE


def main(argv: list[str] | None = None) -> int:
    from tools import commons_fetch as cf  # noqa: PLC0415

    args = list(argv if argv is not None else sys.argv[1:])
    tags_only = "--tags-only" in args
    project = Path(next(x for x in args if not x.startswith("--")))
    p = project / MEDIA_FILE
    raw = json.loads(p.read_text(encoding="utf-8"))
    for mid, a in raw["assets"].items():
        prm = a["tool"]["params"]
        a["license_tags"] = cf.license_tags(prm["commons_title"])
        print(mid, "license_tags", a["license_tags"])
        if tags_only:
            continue
        dest = project / MEDIA_DIR / a["file"]
        ii = cf.fetch(prm["commons_title"], dest, width=prm.get("width"))
        if ii["lic"] != a["license"] and not (a["license"] == "Public domain" and ii["lic"].lower().startswith("public domain")):
            raise SystemExit(f"{mid}: Commons 라이선스 {ii['lic']!r} ≠ 레코드 {a['license']!r}")
        a["source_hash"] = hashlib.md5(dest.read_bytes()).hexdigest()
        print(mid, dest, a["source_hash"])
    MediaRegistryFile.model_validate(raw)
    p.write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
