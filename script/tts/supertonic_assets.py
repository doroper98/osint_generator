"""Supertonic 3 자산 확인(v5.11.0 back_and_forth D-0152 V0, 설계 D147 §2).

모델·스타일·LICENSE 는 git 에 넣지 않는다(380MB). `config.yaml tts.supertonic.assets`(상대 경로 → sha1)가 정본이고,
`python tools/fetch_data.py supertonic` 이 고정 revision 에서 받아 이 함수로 대조한다.
파일이 없거나 sha1 이 다르면 오류다 — edge 등 다른 목소리로 넘어가지 않는다(15 P6).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from orchestrator.config import SupertonicConfig

REPO = Path(__file__).resolve().parents[2]
FETCH_CMD = "python tools/fetch_data.py supertonic"
CHUNK = 1 << 20


class SupertonicAssetError(RuntimeError):
    pass


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def asset_dir(cfg: SupertonicConfig, root: Path = REPO) -> Path:
    return root / cfg.asset_dir


def mismatches(cfg: SupertonicConfig, root: Path = REPO) -> list[str]:
    """없는 파일·sha1 다른 파일 목록(사람이 읽는 한 줄씩). 빈 목록 = 전부 일치."""
    base = asset_dir(cfg, root)
    out: list[str] = []
    for rel, want in cfg.assets.items():
        p = base / rel
        if not p.is_file():
            out.append(f"{rel}: 없음")
            continue
        got = sha1_file(p)
        if got != want:
            out.append(f"{rel}: sha1 {got} ≠ {want}")
    return out


def require_assets(cfg: SupertonicConfig | None, root: Path = REPO) -> Path:
    """자산 폴더를 돌려준다. 설정이 없거나 자산이 모자라면 받는 명령을 담은 오류."""
    if cfg is None:
        raise SupertonicAssetError("config.yaml tts.supertonic 이 없다 — Supertonic 백엔드를 쓸 수 없다(D-0152)")
    bad = mismatches(cfg, root)
    if bad:
        raise SupertonicAssetError(f"Supertonic 자산 {len(bad)}건 문제({asset_dir(cfg, root)}):\n  "
                                   + "\n  ".join(bad) + f"\n받기·대조: {FETCH_CMD}")
    return asset_dir(cfg, root)
