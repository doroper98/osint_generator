"""Supertonic 3 자산·설정(v5.11.0 back_and_forth D-0152 V0, 사용자 결정 D146·설계 D147).

sha1 대조 통과·불일치 오류, 자산 없음 → 오류에 받는 명령, 설정 없음 오류, SupertonicConfig extra·sha1 형식 거부,
config.yaml 값 = 사용자 결정(M3 × 0.95). 저장소 자산 대조는 받아 둔 환경에서만(사유 있는 skip).
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from orchestrator.config import SupertonicConfig, load_config
from script.tts import supertonic_assets as sa

CFG = load_config().tts.supertonic


def _cfg(files: dict[str, bytes], **over: object) -> SupertonicConfig:
    assert CFG is not None
    data = CFG.model_dump()
    data["assets"] = {rel: hashlib.sha1(b).hexdigest() for rel, b in files.items()}
    data.update(over)
    return SupertonicConfig.model_validate(data)


def _write(root: Path, cfg: SupertonicConfig, files: dict[str, bytes]) -> None:
    for rel, b in files.items():
        p = root / cfg.asset_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)


FILES = {"onnx/a.onnx": b"model-a", "voice_styles/M3.json": b'{"style": 1}', "LICENSE": b"license"}


class SupertonicConfigTest(unittest.TestCase):
    def test_user_decision_values(self) -> None:
        assert CFG is not None
        self.assertEqual((CFG.voice_style, CFG.speed), ("M3", 0.95))     # D146
        self.assertIn(f"voice_styles/{CFG.voice_style}.json", CFG.assets)
        self.assertEqual(len(CFG.revision), 40)

    def test_extra_and_sha1_format_rejected(self) -> None:
        assert CFG is not None
        with self.assertRaises(ValidationError):
            SupertonicConfig.model_validate({**CFG.model_dump(), "pitch": 1.0})
        with self.assertRaises(ValidationError):
            SupertonicConfig.model_validate({**CFG.model_dump(), "assets": {"LICENSE": "e6ab935a"}})   # 앞 8자리만


class SupertonicAssetsTest(unittest.TestCase):
    def test_match_passes(self) -> None:
        cfg = _cfg(FILES)
        with tempfile.TemporaryDirectory() as d:
            _write(Path(d), cfg, FILES)
            self.assertEqual(sa.mismatches(cfg, Path(d)), [])
            self.assertEqual(sa.require_assets(cfg, Path(d)), Path(d) / cfg.asset_dir)

    def test_sha1_mismatch_fails(self) -> None:
        cfg = _cfg(FILES)
        with tempfile.TemporaryDirectory() as d:
            _write(Path(d), cfg, {**FILES, "onnx/a.onnx": b"model-a-changed"})
            with self.assertRaises(sa.SupertonicAssetError) as cm:
                sa.require_assets(cfg, Path(d))
            self.assertIn("onnx/a.onnx: sha1", str(cm.exception))
            self.assertIn(sa.FETCH_CMD, str(cm.exception))

    def test_missing_assets_names_fetch_command(self) -> None:
        cfg = _cfg(FILES)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(sa.SupertonicAssetError) as cm:
                sa.require_assets(cfg, Path(d))
            msg = str(cm.exception)
            self.assertIn(f"{len(FILES)}건", msg)
            self.assertIn("LICENSE: 없음", msg)
            self.assertIn("python tools/fetch_data.py supertonic", msg)

    def test_no_config_fails(self) -> None:
        with self.assertRaises(sa.SupertonicAssetError):
            sa.require_assets(None)

    @unittest.skipUnless(CFG is not None and (sa.asset_dir(CFG) / "LICENSE").is_file(),
                         "Supertonic 자산 없음 — python tools/fetch_data.py supertonic")
    def test_repo_assets_match_config(self) -> None:
        assert CFG is not None
        self.assertEqual(sa.mismatches(CFG), [])


if __name__ == "__main__":
    unittest.main()
