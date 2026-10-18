"""v7.4.0 back_and_forth D-0229 §2.2(UF-105) — 시점 전환 장치: bridge 문장 앞 호흡(타임라인), plan transitions, 전환 지점 판정."""

from __future__ import annotations

import unittest

from pathlib import Path

import yaml

from rules import load_rules
from script import lint_waivers
from script.lint import lint, transition_issues, transition_points
from script.schema import Script
from script.timeline import layout, sentence_rows

T = load_rules().transition
REPO = Path(__file__).resolve().parent.parent


def _script(bridge: bool) -> Script:
    s = lambda d, t, **k: dict(date=d, text=t, sources=["c1"], **k)  # noqa: E731
    return Script.model_validate(dict(
        title="t", subtitle="s", date="2026.10.18",
        scenes=[dict(id="act1", stage="러시아", sentences=[s("2026.10.01", "가."), s("2026.10.02", "나.")]),
                dict(id="act2", stage="걸프", sentences=[s("2026.06.13", "시점을 올해 6월, 페르시아만으로 옮깁니다.", **({"role": "bridge"} if bridge else {})),
                                                        s("2026.06.13", "다.")])]))


def _two(stage_b: str, date_b: str, role_a: "str | None" = None, role_b: "str | None" = None, extra_b: "dict | None" = None) -> Script:
    s = lambda d, t, r=None: dict(date=d, text=t, sources=["c1"], **({"role": r} if r else {}))  # noqa: E731
    b = [s(date_b, "나.", role_b), s(date_b, "다.")] + ([extra_b] if extra_b else [])
    return Script.model_validate(dict(title="t", subtitle="s", date="2026.10.18", scenes=[
        dict(id="a", stage="러시아", sentences=[s("2026.10.01", "가."), s("2026.10.01", "가가.", role_a)]),
        dict(id="b", stage=stage_b, sentences=b)]))


def _errs(sc: Script) -> list[str]:
    return [i.sid for i in transition_issues(sc) if i.severity == "error"]


class TransitionPointTest(unittest.TestCase):
    def test_stage_and_date_jump(self) -> None:
        pts = transition_points(_script(True))
        self.assertEqual([(i, k) for i, k, _ in pts], [(2, ["stage", "date_jump"])])

    def test_within_scene_small_jump_no_point(self) -> None:
        self.assertEqual(transition_points(_script(True))[0][0], 2)   # act1 안의 하루 차이는 전환이 아니다


class BridgeLintTest(unittest.TestCase):
    """D-0230 §5 (a)~(e)."""

    def test_a_stage_change_hard(self) -> None:
        self.assertEqual(_errs(_two("걸프", "2026.10.02")), ["b_0"])

    def test_b_median_date_jump_hard(self) -> None:
        self.assertEqual(_errs(_two("러시아", "2026.11.05")), ["b_0"])
        self.assertEqual(_errs(_two("러시아", "2026.10.20")), [])   # 19일 = 전환 아님

    def test_c_bridge_passes(self) -> None:
        self.assertEqual(_errs(_two("걸프", "2026.06.13", role_b="bridge")), [])
        self.assertEqual(_errs(_two("걸프", "2026.06.13", role_a="bridge")), [])   # 앞 장면 마지막 문장도 된다
        self.assertIn("transition-bridge", [i.kind for i in lint(_two("걸프", "2026.06.13"), check_sources=False).errors])

    def test_d_in_scene_jump_warning(self) -> None:
        old = dict(date="2004.01", text="2004년에도 비슷했습니다.", sources=["c1"])
        w = [i for i in transition_issues(_two("러시아", "2026.10.02", extra_b=old)) if i.kind == "transition-in-scene"]
        self.assertEqual([i.severity for i in w], ["warning"])
        w = [i for i in transition_issues(_two("러시아", "2026.10.02", extra_b=dict(old, role="background"))) if i.kind == "transition-in-scene"]
        self.assertEqual(w, [])

    def test_e_old_project_waived(self) -> None:
        proj = REPO / "projects" / "hormuz_korea"
        sc = Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))
        rep = lint(sc, check_sources=False)
        self.assertTrue(any(i.kind == "transition-bridge" for i in rep.errors))
        kept, waived = lint_waivers.apply(type(rep)(issues=[i for i in rep.issues if i.kind == "transition-bridge"]),
                                          [w for w in lint_waivers.load(proj) if w.kind == "transition-bridge"], sc)
        self.assertEqual(kept.errors, [])
        self.assertTrue(waived and all(x["decided_by"] == "D-0230" for x in waived))   # plan.lint_waived → provenance


class TimelinePauseTest(unittest.TestCase):
    def _rows(self, bridge: bool) -> tuple[list[dict], list]:
        rows = sentence_rows(_script(bridge))
        for x in rows:
            x["dur"] = 2.0
        tr: list = []
        layout(rows, tr)
        return rows, tr

    def test_bridge_pause_inserted(self) -> None:
        with_b, tr = self._rows(True)
        without, tr0 = self._rows(False)
        self.assertEqual(tr0, [])
        self.assertEqual(len(tr), 1)
        self.assertEqual(tr[0].sid, "act2_0")
        self.assertAlmostEqual(with_b[2]["t0"] - without[2]["t0"], T.bridge_pause_sec)
        self.assertAlmostEqual(tr[0].pause_t0 + tr[0].pause_sec, with_b[2]["t0"])
        self.assertEqual(with_b[2]["role"], "bridge")

    def test_no_bridge_layout_unchanged(self) -> None:
        rows = sentence_rows(_script(False))
        for x in rows:
            x["dur"] = 2.0
        a = layout([dict(r) for r in rows])
        b = layout([dict(r) for r in rows], [])
        self.assertEqual(a[2], b[2])


class TransitionCameraTest(unittest.TestCase):
    def test_fast_move_at_transition_hard(self) -> None:
        import types  # noqa: PLC0415

        from engine.camera import cam  # noqa: PLC0415
        from engine.checks import transition_camera  # noqa: PLC0415
        from script.schema import PlanTransition  # noqa: PLC0415

        tr = [PlanTransition(sid="b_0", pause_t0=10.0, pause_sec=T.bridge_pause_sec, kind=["stage"])]
        sents = [types.SimpleNamespace(sid="b_0", t0=11.5, t1=15.0)]
        fast = [cam(10.5, 0, 0, 20, 2.0, "move")]
        slow = [cam(10.5, 0, 0, 20, T.camera_move_min_sec + 0.5, "move")]
        self.assertEqual(len(transition_camera(tr, sents, fast)), 1)
        self.assertEqual(transition_camera(tr, sents, slow), [])
        self.assertEqual(transition_camera([tr[0].model_copy(update={"kind": []})], sents, fast), [])


if __name__ == "__main__":
    unittest.main()
