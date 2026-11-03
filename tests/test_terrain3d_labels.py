"""terrain3d 부대 이름 자리·겹침(v7.4.0 back_and_forth D-0627, 사용자 의견 UF-257 "진형 씬에서 너무 글씨들이 겹치는 현상이 있어").

- 옛 자리(이름 = 라벨 점 바로 아래, v1)는 블록이 붙은 진형에서 이름끼리·다른 블록 위에 겹친다 → label_block_hits 가 잡는다.
- layout_labels: 블록 바깥(진형 바깥쪽 먼저) 자리, 같은 이름은 한 번, 자리가 없으면 short 이름, 그래도 없으면 접는다 → 겹침 0.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.checks import label_block_hits
from engine.layers import terrain3d as t3l
from engine.style import FPS, Output
from schemas.war_units import WarForces


def _project() -> SimpleNamespace:
    forces = WarForces.model_validate({
        "approximate": True, "sources": ["s"], "factions": {"a": {"token": "ru", "name": "A"}, "b": {"token": "us", "name": "B"}},
        "units": [{"faction": "a", "symbol": "heavy_inf", "name": "아프리카 중무장보병", "short": "아프리카 보병",
                   "keys": [{"t": 0, "lon": 0, "lat": 0, "length_km": 1, "depth_km": 1}]}]})
    out = Output("fx", 854, 480, FPS, 23, "medium", 512)   # k = 1, pad 0 — 3D 좌표 = 장치 px
    return SimpleNamespace(R=SimpleNamespace(out=out, cache={"terrain3d_forces": forces}))


def _rec(i: int, name: str, block: tuple, k: float = 854 / 1280) -> dict:
    """block = 설계 좌표 상자 → 3D 렌더 px(스케치 폭 1280 기준이 아니라 이 시험 장치 = 설계)."""
    x0, y0, x1, y1 = block
    return {"k": "unit", "i": i, "name": name, "glyph": "heavy_inf", "x": (x0 + x1) / 2, "y": (y0 + y1) / 2, "behind": False,
            "block": [x0, y0, x1, y1]}


# 칸나이 v1 150초 근처를 닮은 빽빽한 진형 — 블록이 서로 붙어 있다
DENSE = [_rec(0, "로마 중무장보병", (330, 200, 520, 260)), _rec(1, "히스파니아·켈트 보병", (360, 262, 490, 290)),
         _rec(2, "아프리카 중무장보병", (280, 230, 328, 300)), _rec(3, "아프리카 중무장보병", (522, 230, 570, 300)),
         _rec(4, "누미디아 기병", (560, 170, 620, 200)), _rec(5, "", (300, 170, 340, 198))]


class LabelLayoutTest(unittest.TestCase):
    def test_old_layout_overlaps_detected(self) -> None:
        """v1 자리(점 바로 아래 이름) — 이름이 다른 블록 위에 놓인다."""
        P = _project()  # noqa: N806
        from engine.typography import adv  # noqa: PLC0415

        sz = 12.0
        pair = [_rec(0, "히스파니아·켈트 보병", (370, 240, 420, 270)), _rec(1, "아프리카 중무장보병", (430, 240, 480, 270))]   # v1 150초: 두 이름이 한 줄처럼
        names = []
        for j, r in enumerate(pair):
            if r["name"]:
                w = adv(r["name"], sz, "sansm") / 2
                names.append((r["name"], (r["x"] - w, r["y"] + sz - sz * 0.85, r["x"] + w, r["y"] + sz + sz * 0.25), j))
        blocks = [t3l.block_box(P, r) for r in pair]
        hits = label_block_hits(names, blocks)
        self.assertIn(("히스파니아·켈트 보병", "아프리카 중무장보병"), hits)
        placed, _ = t3l.layout_labels(P, pair)   # 새 자리는 같은 두 부대에서 겹침 0
        self.assertEqual(label_block_hits([(q.text, q.box, pair.index(q.rec)) for q in placed], blocks), [])

    def test_new_layout_no_overlap(self) -> None:
        P = _project()  # noqa: N806
        placed, folded = t3l.layout_labels(P, DENSE)
        names = [(p.text, p.box, DENSE.index(p.rec)) for p in placed]
        blocks = [t3l.block_box(P, r) for r in DENSE]
        self.assertEqual(label_block_hits(names, blocks), [])
        texts = [p.text for p in placed]
        self.assertEqual(len(texts), len(set(texts)))   # 같은 이름은 한 번
        self.assertFalse(any(t in ("아프리카 중무장보병", "아프리카 보병") for t in folded) and
                         any(t.startswith("아프리카") for t in texts))
        self.assertEqual(len(placed) + len(folded), 4)  # 이름 있는 부대 이름 넷(아프리카 둘은 하나로)

    def test_labels_outside_blocks(self) -> None:
        P = _project()  # noqa: N806
        placed, _ = t3l.layout_labels(P, DENSE)
        for p in placed:
            own = t3l.block_box(P, p.rec)
            inter_w = min(own[2], p.box[2]) - max(own[0], p.box[0])
            inter_h = min(own[3], p.box[3]) - max(own[1], p.box[1])
            self.assertFalse(inter_w > 2 and inter_h > 2, p.text)   # 자기 블록 위에도 놓지 않는다(바깥 자리)

    def test_fold_when_no_room(self) -> None:
        """화면 가장자리에 꽉 낀 블록 — 자리가 없으면 short, 그래도 없으면 접힌 이름으로 기록."""
        P = _project()  # noqa: N806
        wall = [_rec(0, "아프리카 중무장보병", (8, 22, 846, 409))]   # 안전 영역 전체를 덮는 블록
        placed, folded = t3l.layout_labels(P, wall)
        self.assertEqual(placed, [])
        self.assertEqual(folded, ["아프리카 중무장보병"])


if __name__ == "__main__":
    unittest.main()
