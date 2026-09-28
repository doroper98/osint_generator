"""engine/camera_suggest — 연출가 제안 경로(v3.3.0, D-0056 작업 5). 제안은 옵션이다(P8)."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.camera_suggest import CameraSuggest, main, suggest
from engine.framing import place, plain_point

ROOT = Path(__file__).resolve().parents[1]
HORMUZ = ROOT / "projects" / "hormuz_korea"
# plan.json·tts 는 생성물(gitignore) — 새 컨테이너엔 없다. artifacts 브랜치 shared/ 복원 뒤 돈다(D-0057 §2 NB15).
_NO_PLAN = "projects/hormuz_korea/plan.json 없음(생성물) — artifacts/phase7-v3.3.0 shared/ 복원 필요(D-0057 NB15)"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


@unittest.skipUnless((HORMUZ / "plan.json").exists(), _NO_PLAN)
class CameraSuggestHormuzTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project  # noqa: PLC0415

        cls.P = load_project(HORMUZ)
        cls.cs = suggest(cls.P)

    def test_schema_roundtrip(self) -> None:
        again = CameraSuggest.model_validate_json(self.cs.model_dump_json())
        self.assertEqual(again, self.cs)
        self.assertEqual(again.schema_version, 1)

    def test_one_entry_per_camera_key(self) -> None:
        self.assertEqual(len(self.cs.shots), len(self.P.keys))

    def test_user_approved_v3_camera_fits(self) -> None:
        """사용자 합격 v3 카메라는 '장소가 화면 안'으로 판정돼야 한다(판정기가 골든을 틀렸다고 하면 판정기가 틀린 것)."""
        bad = [s.t for s in self.cs.shots if s.current_fits is False]
        self.assertEqual(bad, [])

    def test_ending_pullback_not_suggested(self) -> None:
        self.assertIsNone(self.cs.shots[-1].suggested)
        self.assertIn("엔딩 풀백", self.cs.shots[-1].note)

    def test_shot_rules_clean_on_v3(self) -> None:
        self.assertEqual(self.cs.shot_issues_current, [])

    def test_transition_only_from_rule(self) -> None:
        for s in self.cs.shots:
            if s.suggested is not None and s.t > 0:
                self.assertIn(s.suggested_transition, ("move", "dip"))

    def test_cli_does_not_touch_direction(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "hz"
            shutil.copytree(HORMUZ, proj, ignore=shutil.ignore_patterns("prev", "out", "tts", "cache"))
            before = _md5(proj / "direction.yaml")
            self.assertEqual(main([str(proj)]), 0)
            self.assertEqual(_md5(proj / "direction.yaml"), before)
            data = json.loads((proj / "prev" / "camera_suggest.json").read_text(encoding="utf-8"))
            CameraSuggest.model_validate(data)


    def test_suggested_path_passes_offscreen_checker(self) -> None:
        """제안을 받아들인 카메라 경로(이동·드리프트 포함)를 offscreen 검사기(하나의 검사기)로 돌리면 0건."""
        import dataclasses  # noqa: PLC0415

        from engine.camera import build_camera  # noqa: PLC0415
        from engine.camera_suggest import _keys_for  # noqa: PLC0415
        from engine.checks import offscreen_hits  # noqa: PLC0415
        from engine.projection import ym  # noqa: PLC0415
        from engine.style import FPS  # noqa: PLC0415

        sugs = [(s.suggested.lon, ym(s.suggested.lat), s.suggested.w) if s.suggested else None for s in self.cs.shots]
        keys, ev = _keys_for(self.P, sugs, [s.suggested_transition for s in self.cs.shots])
        P2 = dataclasses.replace(self.P, keys=keys, events=ev, cams=build_camera(keys, self.P.n_frames, FPS))  # noqa: N806
        self.assertEqual(offscreen_hits(P2), [])

    def test_resolution_independent(self) -> None:
        """같은 장소·카메라 → 854×480 과 1280×720 에서 같은 (lon, lat, w)·같은 프레임 안 판정(px 여백만 k 배)."""
        from engine.camera_suggest import _points  # noqa: PLC0415
        from engine.framing import frame_points  # noqa: PLC0415

        t = self.P.R.assets.tiers["W"]
        bounds = (t["lon0"], t["lat0"], t["lon1"], t["lat1"])
        keys = sorted(self.P.keys, key=lambda k: k.t)
        for i, s in enumerate(self.cs.shots):
            if s.suggested is None:
                continue
            pts = _points(self.P.events, keys[i].t, s.t_end)
            a = frame_points(pts, width=854, height=480, bounds=bounds)
            b = frame_points(pts, width=1280, height=720, bounds=bounds)
            self.assertEqual(a.ok, b.ok, s.t)
            # 854/480(1.7792)과 1280/720(1.7778)은 화면비가 0.08% 다르다 — 그만큼(w 의 0.1%)만 허용
            for x, y in ((a.lon, b.lon), (a.lat, b.lat), (a.w, b.w)):
                self.assertLessEqual(abs(x - y), a.w * 1e-3, str(s.t))
            c = s.current
            self.assertEqual(place(pts, c.lon, c.lat, c.w, width=854, height=480, bounds=bounds, lenient=True)[0],
                             place(pts, c.lon, c.lat, c.w, width=1280, height=720, bounds=bounds, lenient=True)[0], s.t)


@unittest.skipUnless((HORMUZ / "plan.json").exists(), _NO_PLAN)
class SuggestWiringTest(unittest.TestCase):
    """제안은 옵션(P8): 연출가 입력에 '제안값'으로만, 사람 연출 무변경, provenance 는 suggested/used 를 가른다."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self._tmp.name) / "hz"
        shutil.copytree(HORMUZ, self.proj, ignore=shutil.ignore_patterns("prev", "out", "tts", "cache"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_director_prompt_placeholder(self) -> None:
        from workers.direction_io import camera_suggest_text  # noqa: PLC0415

        self.assertIn("{camera_suggest}", (ROOT / "prompts" / "director_user.md").read_text(encoding="utf-8"))
        txt, sha = camera_suggest_text(self.proj)
        self.assertIsNone(sha)
        self.assertIn("없음", txt)
        self.assertEqual(main([str(self.proj)]), 0)
        txt, sha = camera_suggest_text(self.proj)
        self.assertIsNotNone(sha)
        self.assertIn("cam lon", txt)
        self.assertNotIn("127.35", txt)      # 이전 연출(현재) 카메라 값은 넣지 않는다(15 P9)

    def test_provenance_suggested_vs_used(self) -> None:
        from engine.project import load_project  # noqa: PLC0415
        from engine.provenance import camera_summary  # noqa: PLC0415

        P = load_project(self.proj)  # noqa: N806
        self.assertEqual(camera_summary(self.proj, P.keys)["suggest_ran"], False)
        self.assertEqual(main([str(self.proj)]), 0)
        cam = camera_summary(self.proj, P.keys)
        self.assertTrue(cam["suggest_ran"])
        self.assertGreater(cam["suggested"], 0)
        self.assertEqual(cam["used"], 0)              # 사람 연출은 제안을 받아들이지 않았다
        self.assertTrue(cam["from_current_direction"])
        self.assertFalse(cam["given_to_director"])

    def test_gate2_table(self) -> None:
        from orchestrator.gate_view import preview_gate_view  # noqa: PLC0415

        self.assertIn("카메라 제안 — 없음", preview_gate_view(self.proj)[0])
        self.assertEqual(main([str(self.proj)]), 0)
        text, shown = preview_gate_view(self.proj)
        self.assertIn("카메라 제안 vs 현재", text)
        self.assertIn("camera_suggest", shown)


class LenientLineTest(unittest.TestCase):
    def test_line_point_may_pass_under_subtitle_only_in_lenient(self) -> None:
        low = plain_point(0.0, -7.0, "route#end", avoid_reserve=False)
        self.assertTrue(place([low], 0.0, 0.0, 30.0, lenient=True)[0])
        self.assertFalse(place([low], 0.0, 0.0, 30.0)[0])


if __name__ == "__main__":
    unittest.main()
