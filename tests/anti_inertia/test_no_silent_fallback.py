"""test_no_silent_fallback — 강제 오류 시 옛 스타일 출력 없이 중단 (docs/handoff/15 P6, 19 부록 B).

(a) 미등재 이벤트 타입 → RegistryError   (Phase 2)
(b) 권리 필드 없는 미디어 → RightsError   (Phase 6.5)
(c) 손상 manifest → 오류, created 폴백 아님 (Phase 6.8)
(d) `main.py build-scene` → LegacyRemovedError (커밋 ② — D13 으로 보류 중)
"""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import pytest


class NoSilentFallbackTest(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="Phase 2 — engine.registry.RegistryError 미구현")
    def test_a_unregistered_event_type(self) -> None:
        registry = importlib.import_module("engine.registry")
        with self.assertRaises(registry.RegistryError):  # type: ignore[attr-defined]
            registry.resolve("stamp")  # type: ignore[attr-defined]

    @pytest.mark.xfail(strict=True, reason="Phase 6.5 — engine.layers.media.RightsError 미구현")
    def test_b_media_without_rights(self) -> None:
        media = importlib.import_module("engine.layers.media")
        with self.assertRaises(media.RightsError):  # type: ignore[attr-defined]
            media.validate_media({"kind": "photo", "img": "x.jpg"})  # type: ignore[attr-defined]

    @pytest.mark.xfail(strict=True, reason="Phase 6.8 — command_center 가 손상 manifest 를 created 로 폴백")
    def test_c_corrupt_manifest_is_error(self) -> None:
        # Phase 6.8 계약: command_center.load_project_state 가 손상 manifest 에서
        # orchestrator.errors.ManifestCorruptError 를 던진다 (지금은 created 로 폴백).
        from orchestrator import command_center
        from orchestrator.config import AppConfig, PathsConfig
        from orchestrator.errors import ManifestCorruptError  # type: ignore[attr-defined]

        loader = command_center.load_project_state  # type: ignore[attr-defined]
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "broken"
            pdir.mkdir()
            (pdir / "project_manifest.json").write_text("{not json", encoding="utf-8")
            cfg = AppConfig(paths=PathsConfig(projects_root=tmp))
            with self.assertRaises(ManifestCorruptError):
                loader("broken", cfg)

    @pytest.mark.xfail(
        strict=True,
        reason="커밋 ②(레거시 삭제·LegacyRemovedError) 보류 — DECISIONS D13. 적용 후 XPASS → 마커 제거",
    )
    def test_d_build_scene_raises(self) -> None:
        from orchestrator.errors import LegacyRemovedError  # type: ignore[import-not-found]
        from orchestrator.main import main

        with self.assertRaises(LegacyRemovedError):
            main(["build-scene", "demo"])


if __name__ == "__main__":
    unittest.main()
