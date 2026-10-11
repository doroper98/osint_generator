"""v5.22.4 D-0205 §3 — 원장 소급 open 항목을 닫은 장치들: 발음 사전(UF-26·29), 차트 눈금 중복(UF-57), 문장마다 카메라(UF-19),
공용 자산 게이트(UF-69), 표준 음성 값(UF-95·96, CLAUDE.md C0.2)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

from engine.checks import HARD, check_camera_per_sentence
from engine.panels.dual_line import DuplicateTickError, tick_labels
from orchestrator.project_manager import AssetLibraryPendingError, require_asset_library
from script.lint import pronounce_tts
from tests.anti_inertia._ast_util import REPO


class TestPronounce(unittest.TestCase):
    def test_mdl_split(self) -> None:
        """UF-29 — "군사분계선"을 [군사분 계선]으로 끊어 읽지 않게 의미 단위로 고정."""
        self.assertEqual(pronounce_tts("군사분계선 남쪽"), "군사 분계선 남쪽")

    def test_domain_reading(self) -> None:
        """UF-26 — "LB.ua" 를 글자 그대로 읽지 않는다(엘비 닷 유에이)."""
        out = pronounce_tts("우크라이나 매체 LB.ua는")
        self.assertNotIn("LB", out)
        self.assertIn("닷", out)


class TestChartTicks(unittest.TestCase):
    def test_duplicate_tick_labels_error(self) -> None:
        """UF-57 — 같은 글자 눈금("$6·$6·$6")은 렌더 전 오류."""
        ok = tick_labels({"y_min": 5.6, "y_max": 6.4, "y_step": 0.4, "y_prefix": "$"})
        self.assertEqual(len({s for _, s in ok}), 3)
        import engine.panels.dual_line as D
        orig = D.step_decimals
        try:
            D.step_decimals = lambda step: 0   # 옛 결함(자릿수 0 고정) 재현
            with self.assertRaises(DuplicateTickError):
                tick_labels({"y_min": 5.6, "y_max": 6.4, "y_step": 0.4, "y_prefix": "$"})
        finally:
            D.step_decimals = orig


class TestCameraPerSentence(unittest.TestCase):
    def test_every_sentence_moving_is_hard(self) -> None:
        """UF-19 — 연속 3문장이 모두 이동을 시작하면 hard."""
        self.assertIn("camera_per_sentence", HARD)
        S = [SimpleNamespace(sid=f"s{i}", t0=i * 5.0, t1=i * 5.0 + 4.5) for i in range(4)]
        mv = lambda t: SimpleNamespace(t=t, mode="move")  # noqa: E731
        bad = SimpleNamespace(plan=SimpleNamespace(sentences=S), keys=[mv(0.5), mv(5.5), mv(10.5)])
        ok = SimpleNamespace(plan=SimpleNamespace(sentences=S), keys=[mv(0.5), mv(10.5)])
        self.assertEqual(len(check_camera_per_sentence(bad)), 1)
        self.assertEqual(check_camera_per_sentence(ok), [])


class TestAssetLibraryGate(unittest.TestCase):
    def test_pending_portrait_blocks_gate2(self) -> None:
        """UF-69(C8.7) — 공용 자산으로 올리지 않은 초상이 있으면 게이트 ② 거부."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "assets" / "portraits").mkdir(parents=True)
            self.assertIn("0", require_asset_library(p))
            (p / "assets" / "portraits" / "nobody_not_in_library_x.png").write_bytes(b"x")
            with self.assertRaises(AssetLibraryPendingError):
                require_asset_library(p)


class TestStandardVoice(unittest.TestCase):
    def test_standard_voice_matches_c02(self) -> None:
        """UF-95·96(CLAUDE.md C0.2) — 표준 음성 값이 바뀌면 실패(바꾸려면 사용자 지적 → 규칙 개정, 이 시험도 같이)."""
        cfg = yaml.safe_load((REPO / "config.yaml").read_text(encoding="utf-8"))
        tts = cfg["tts"]
        self.assertEqual(tts["backend_default"], "supertonic")
        self.assertEqual((tts["supertonic"]["voice_style"], tts["supertonic"]["speed"]), ("M3", 0.95))
        self.assertFalse(tts.get("elevenlabs_allowed", False))
        rules = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))
        ff = rules["tts_rules"]["prosody"]["final_fall"]
        self.assertEqual((ff["enabled"], ff["suffix"], ff["span_chars"], ff["semitones"]), (True, "니다", 3, 4.0))
        self.assertEqual(rules["audio"]["bed_gain"], 0.43)


if __name__ == "__main__":
    unittest.main()
