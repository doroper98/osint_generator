"""v7.4.0 back_and_forth D-0238(UF-118 "사진을 고른거 같은데 그 사진들이 누락되지 않고 영상에 잘 쓰이게 챙겨") — [media-unused] hard.
(a) 등재 2·배치 1 → hard (b) drop 사유 있으면 통과 (c) 배치 2(기사 카드 press 포함) → 통과 (d) 옛 프로젝트 무변화."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from engine.checks import HARD, media_unused
from engine.media_registry import load_media_registry
from schemas.media_models import MediaNotes

REPO = Path(__file__).resolve().parent.parent
PID = "diesel_road_2026"
A, B = f"{PID}_trump_1006", f"{PID}_moscow_fire_0618"


class MediaUnusedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = load_media_registry()
        self.others = [{"type": "photo", "mid": m, "t0": 30, "t1": 35} for m, a in self.reg.items()
                       if m.startswith(PID + "_") and a.kind == "photo" and m not in (A, B)]   # 이 프로젝트의 나머지 등재 사진은 배치된 것으로

    def test_hard(self) -> None:
        self.assertIn("media_unused", HARD)

    def test_a_one_missing(self) -> None:
        ev = [{"type": "article", "mid": f"{PID}_art_0032", "press": A, "t0": 0, "t1": 5}, *self.others]
        out = media_unused(PID, ev, self.reg, {})
        self.assertEqual(len(out), 1)
        self.assertIn(B, out[0])

    def test_b_drop_reason(self) -> None:
        ev = [{"type": "article", "mid": f"{PID}_art_0032", "press": A, "t0": 0, "t1": 5}, *self.others]
        self.assertEqual(media_unused(PID, ev, self.reg, {B: "장소 특정 문장만 남아 오해 소지"}), [])
        with self.assertRaises(ValueError):   # 사유 없는 drop 은 스키마가 막는다
            MediaNotes.model_validate({"drop": [{"mid": B, "reason": ""}]})

    def test_c_both_used(self) -> None:
        ev = [{"type": "article", "mid": f"{PID}_art_0032", "press": A, "t0": 0, "t1": 5},
              {"type": "photo", "mid": B, "t0": 20, "t1": 25}, *self.others]
        self.assertEqual(media_unused(PID, ev, self.reg, {}), [])

    def test_d_old_projects(self) -> None:
        for proj in ("hormuz_korea",):   # 프로젝트 접두 사진이 없다 → 검사 대상 0
            pdir = REPO / "projects" / proj
            doc = yaml.safe_load((pdir / "direction.yaml").read_text(encoding="utf-8"))
            self.assertEqual(media_unused(proj, doc["events"], self.reg, {}), [])


class ReceivedPhotoTest(unittest.TestCase):
    """v7.4.0 UF-916(UF-118 재발, PIPELINE-AP-030 — "제작 단계에서 저런 이미지들을 많이 찾았따가 영상완성된 후에 보면 많이 안보이더라구.
    꼭 다 보이도록 해.") — 사진 id 가 프로젝트 id 로 시작하지 않아도, 프로젝트 media/ 에 원본을 받아 둔 등재 사진은 검사 대상이다."""

    def setUp(self) -> None:
        import tempfile  # noqa: PLC0415

        self.reg = load_media_registry()
        self.mid = next(m for m, a in self.reg.items() if a.kind == "photo" and (a.tool.params or {}).get("source")
                        and a.rights_status != "unverified" and not m.startswith("some_new_video_"))
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmp.name) / "some_new_video"
        (self.proj / "media").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_photo_not_received_is_out_of_scope(self) -> None:
        from engine.checks import received_photos  # noqa: PLC0415

        self.assertEqual(received_photos(self.proj, self.reg), set())
        self.assertEqual(media_unused(self.proj.name, [], self.reg, {}, received_photos(self.proj, self.reg)), [])

    def test_received_photo_missing_from_direction_is_hard(self) -> None:
        from engine.checks import received_photos  # noqa: PLC0415

        (self.proj / "media" / str(self.reg[self.mid].tool.params["source"])).write_bytes(b"x")
        recv = received_photos(self.proj, self.reg)
        self.assertEqual(recv, {self.mid})
        out = media_unused(self.proj.name, [], self.reg, {}, recv)
        self.assertEqual(len(out), 1)
        self.assertIn(self.mid, out[0])
        self.assertEqual(media_unused(self.proj.name, [{"type": "photo", "mid": self.mid, "t0": 1, "t1": 9}], self.reg, {}, recv), [])
        self.assertEqual(media_unused(self.proj.name, [], self.reg, {self.mid: "주제와 맞지 않아 뺌"}, recv), [])


if __name__ == "__main__":
    unittest.main()
