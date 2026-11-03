"""조각 캐시 전역 키 — 글꼴 환경 지문(v7.4.0 back_and_forth D-1005, RENDER-AP-032 후속).

탐침 프레임에 글자가 없는 조각도 글꼴 설정이 바뀌면 무효여야 한다. 전역 키가 바뀌면 chunk_key 가 전부 바뀌어 전 조각 rendered,
그대로면 전부 같은 키 → reused(engine.render 는 키가 같은 조각만 다시 쓴다).
- fonts.conf 한 줄을 바꾼 사본 → 지문·전역 키·모든 조각 키가 다르다.
- 같은 설정 → 같다(프로세스 캐시를 비우고 다시 재도 같다).
- 글꼴 파일 바이트 하나를 바꾼 사본 → 지문이 다르다.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from engine import chunk_cache as cc
from engine.fontenv import config_file


def fake_project(root: Path) -> SimpleNamespace:
    return SimpleNamespace(R=SimpleNamespace(out=SimpleNamespace(record=lambda: {"name": "480p"})), root=root,
                           plan=SimpleNamespace(total=30.0), n_frames=900)


class FontEnvKeyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.conf = self.dir / "fonts.conf"
        shutil.copy(config_file(), self.conf)
        cc._FONT_ENV.clear()

    def tearDown(self) -> None:
        cc._FONT_ENV.clear()
        self.tmp.cleanup()

    def keys(self, conf: Path) -> tuple[str, list[str]]:
        with mock.patch.object(cc, "font_env_fingerprint", lambda: cc.__dict__["_real_fp"](conf)):
            g = cc.global_key(fake_project(self.dir), "animatic", ["-crf", "20"])
        return g, [cc.chunk_key(g, f"slice{i}", f"probe{i}") for i in range(6)]

    def test_same_conf_reused(self) -> None:
        a = cc.font_env_fingerprint(self.conf)
        cc._FONT_ENV.clear()
        self.assertEqual(a, cc.font_env_fingerprint(self.conf))
        g1, k1 = self.keys(self.conf)
        cc._FONT_ENV.clear()
        g2, k2 = self.keys(self.conf)
        self.assertEqual((g1, k1), (g2, k2))

    def test_conf_line_change_invalidates_all(self) -> None:
        g1, k1 = self.keys(self.conf)
        changed = self.dir / "fonts_changed.conf"
        changed.write_text(self.conf.read_text(encoding="utf-8").replace("<const>hintslight</const>", "<const>hintfull</const>"),
                           encoding="utf-8")
        self.assertNotEqual(changed.read_text(encoding="utf-8"), self.conf.read_text(encoding="utf-8"))
        g2, k2 = self.keys(changed)
        self.assertNotEqual(g1, g2)
        self.assertTrue(all(a != b for a, b in zip(k1, k2)), "전 조각 키가 바뀌어야(rendered)")

    def test_comment_only_change_still_invalidates(self) -> None:
        """내용 sha1 — 한 줄이면 주석이라도 무효(보수적, 탐침이 못 보는 차이를 놓치지 않는다)."""
        a = cc.font_env_fingerprint(self.conf)
        c2 = self.dir / "fonts_c.conf"
        c2.write_text(self.conf.read_text(encoding="utf-8") + "<!-- x -->\n", encoding="utf-8")
        self.assertNotEqual(a, cc.font_env_fingerprint(c2))

    def test_include_chain_read(self) -> None:
        paths = [p for p, _ in cc.conf_chain(self.conf)]
        self.assertGreater(len(paths), 1, "include 체인(/etc/fonts/fonts.conf …)을 따라가야")
        self.assertIn(str(Path("/etc/fonts/fonts.conf").resolve()), paths)

    def test_font_file_byte_change(self) -> None:
        real = cc.fc_props("IBM Plex Sans KR", False)["file"].split('"')[1]
        copy = self.dir / "font.ttf"
        shutil.copy(real, copy)
        fake = {k: "x" for k in cc.FC_PROPS} | {"file": f'"{copy}"(s)'}
        with mock.patch.object(cc, "fc_props", lambda *a, **k: fake):
            a = cc.font_env_fingerprint(self.conf)
            cc._FONT_ENV.clear()
            b = bytearray(copy.read_bytes())
            b[len(b) // 2] ^= 0xFF
            copy.write_bytes(bytes(b))
            self.assertNotEqual(a, cc.font_env_fingerprint(self.conf))

    def test_props_cover_render_attributes(self) -> None:
        pr = cc.fc_props("IBM Plex Sans KR", False)
        self.assertEqual(set(pr), {*cc.FC_PROPS, "file"})
        self.assertTrue(all(pr[k] for k in cc.FC_PROPS), pr)


cc.__dict__["_real_fp"] = cc.font_env_fingerprint

if __name__ == "__main__":
    unittest.main()
