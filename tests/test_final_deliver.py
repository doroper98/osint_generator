"""v7.4.0 D-0634 §3-3 — 전달본 분할은 한도를 넘을 때만(UF-268 "30메가 넘으면 분할해서 보내줘", UF-269 "꼭 분할이 필요한 상황이라면 말이지")."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rules import load_rules
from tools import final_deliver as FD


def _clip(path: Path, sec: int = 6) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=24:duration={sec}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={sec}", "-c:v", "libx264", "-g", "24", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", str(path)], check=True)


class NeedsSplitTest(unittest.TestCase):
    def test_only_over_limit(self) -> None:
        m = load_rules().delivery_package.deliver_file.max_bytes
        self.assertFalse(FD.needs_split(m, m))          # 한도와 같으면 한 파일
        self.assertFalse(FD.needs_split(28_885_844, m))  # 칸나이 v1 전달본 크기 — 조각 없음
        self.assertTrue(FD.needs_split(m + 1, m))

    def test_rules_target_under_limit(self) -> None:
        c = load_rules().delivery_package.deliver_file
        self.assertLessEqual(c.target_bytes, c.max_bytes)
        self.assertLessEqual(c.piece_max_bytes, c.max_bytes)


class DeliverTest(unittest.TestCase):
    def test_under_limit_makes_no_parts_and_clears_old(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _clip(d / "final.mp4")
            (d / "final_parts").mkdir()
            (d / "final_parts" / "part_00.mp4").write_bytes(b"old")
            rec = FD.deliver(d / "final.mp4", d / "final_deliver.mp4", d / "final_parts")
            self.assertEqual(rec["parts"], [])
            self.assertFalse((d / "final_parts").exists())
            self.assertLessEqual(rec["bytes"], load_rules().delivery_package.deliver_file.max_bytes)

    def test_over_limit_splits_keyframe_pieces(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _clip(d / "final.mp4", 8)
            size = (d / "final.mp4").stat().st_size
            cfg = load_rules().delivery_package.deliver_file.model_copy(update={"max_bytes": size // 3, "target_bytes": size // 3,
                                                                                 "piece_max_bytes": size // 3})
            with mock.patch.object(FD, "encode", lambda s, t, k, p: t.write_bytes(s.read_bytes())), \
                 mock.patch.object(FD, "load_rules") as lr:
                lr.return_value.delivery_package.deliver_file = cfg
                rec = FD.deliver(d / "final.mp4", d / "final_deliver.mp4", d / "final_parts")
            self.assertGreaterEqual(len(rec["parts"]), 2)
            self.assertTrue(all(p["bytes"] <= cfg.piece_max_bytes for p in rec["parts"]))
            self.assertAlmostEqual(sum(p["sec"] for p in rec["parts"]), rec["sec"], delta=0.1)
            for p in rec["parts"]:   # 조각마다 단독 재생(ffprobe 길이 읽힘)
                self.assertGreater(FD.duration(d / "final_parts" / p["file"]), 0)


if __name__ == "__main__":
    unittest.main()
