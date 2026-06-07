"""compose_narration 단위테스트 — 순수 타임라인/문장분할 + 실 TTS(stub)+ffmpeg 조립.

ffmpeg 는 본 환경에 있음(imageio-ffmpeg 또는 시스템). StubTTSBackend 는 무음 wav 를
결정론 길이로 내므로 네트워크 불요.
"""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from orchestrator.compose_narration import (
    NarrationResult,
    build_scene_narration,
    plan_narration_timeline,
    split_sentences,
)
from orchestrator.hyperframes_compose import (
    ComposedCue,
    ComposedScene,
    render_composition_html,
)
from workers.tts_backends import StubTTSBackend


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return shutil.which("ffmpeg") or "ffmpeg"


class TestPlanTimeline(unittest.TestCase):
    def test_cue_timings_and_totals(self) -> None:
        units = [
            ("s1", "문장 A", 2.0),
            ("s1", "문장 B", 3.0),
            ("s2", "문장 C", 1.0),
        ]
        res = plan_narration_timeline(
            units, lead_sec=0.5, pause_sec=0.5, tail_sec=0.8
        )
        self.assertIsInstance(res, NarrationResult)
        ats = [c.at_sec for c in res.cues]
        # cursor: lead=0.5 → s1A@0.5; +2.0+0.5 → s1B@3.0; +3.0+0.5 → s2C@6.5
        self.assertEqual(ats, [0.5, 3.0, 6.5])
        self.assertEqual([c.duration_sec for c in res.cues], [2.0, 3.0, 1.0])
        # total: cursor_end = 6.5+1.0+0.5 = 8.0; total = 8.0 - 0.5(마지막 pause) + 0.8 = 8.3
        self.assertAlmostEqual(res.total_sec, 8.3, places=3)
        # scene_durations: s1 = (2+0.5)+(3+0.5)=6.0 ; s2 = (1+0.5)=1.5
        self.assertAlmostEqual(res.scene_durations["s1"], 6.0, places=3)
        self.assertAlmostEqual(res.scene_durations["s2"], 1.5, places=3)
        # 합 == cursor_end - lead = 8.0 - 0.5 = 7.5
        self.assertAlmostEqual(sum(res.scene_durations.values()), 7.5, places=3)

    def test_empty_units(self) -> None:
        res = plan_narration_timeline([], lead_sec=0.5, pause_sec=0.5, tail_sec=0.8)
        self.assertEqual(res.cues, [])
        self.assertEqual(res.scene_durations, {})
        self.assertAlmostEqual(res.total_sec, 1.3, places=3)
        self.assertIsNone(res.audio_path)


class TestSplitSentences(unittest.TestCase):
    def test_korean_multi_sentence(self) -> None:
        text = "첫 번째 문장입니다. 두 번째 문장이에요! 세 번째는 질문일까요? 끝."
        out = split_sentences(text)
        self.assertEqual(out, [
            "첫 번째 문장입니다.",
            "두 번째 문장이에요!",
            "세 번째는 질문일까요?",
            "끝.",
        ])

    def test_no_terminator_single(self) -> None:
        self.assertEqual(split_sentences("종결부호 없는 한 줄"), ["종결부호 없는 한 줄"])

    def test_empty(self) -> None:
        self.assertEqual(split_sentences("   "), [])
        self.assertEqual(split_sentences(""), [])


class TestBuildSceneNarration(unittest.TestCase):
    def test_two_scenes_stub_backend(self) -> None:
        scenes = [
            ComposedScene(
                scene_id="s1", section_id="s1", start_sec=0.0, duration_sec=5.0,
                kind="text", narration="첫 씬 문장 하나. 첫 씬 문장 둘.",
            ),
            ComposedScene(
                scene_id="s2", section_id="s2", start_sec=5.0, duration_sec=5.0,
                kind="text", narration="둘째 씬 문장 하나. 둘째 씬 문장 둘.",
            ),
        ]
        with TemporaryDirectory() as tmp:
            audio_out = Path(tmp) / "audio" / "proj.mp3"
            res = build_scene_narration(
                scenes,
                backend=StubTTSBackend(),
                voice=None,
                audio_out=audio_out,
                ffmpeg_bin=_ffmpeg(),
                pronounce_dict=None,
            )
            # 오디오 파일 존재 + 비어있지 않음.
            self.assertTrue(audio_out.exists())
            self.assertGreater(audio_out.stat().st_size, 0)
            self.assertEqual(res.audio_path, str(audio_out))
            # 문장 2x2 = 4 큐.
            self.assertEqual(len(res.cues), 4)
            # 자막 텍스트 == 원본 문장.
            self.assertEqual(
                [c.text for c in res.cues],
                ["첫 씬 문장 하나.", "첫 씬 문장 둘.", "둘째 씬 문장 하나.", "둘째 씬 문장 둘."],
            )
            # scene_durations 에 두 scene_id.
            self.assertIn("s1", res.scene_durations)
            self.assertIn("s2", res.scene_durations)
            # total ≈ lead + sum(part dur) + pauses(3) + tail (stub 결정론 길이).
            sum_parts = sum(c.duration_sec for c in res.cues)
            # 4 큐 → 3 pause(마지막 pause 는 tail 로 대체). total = lead + sum + 3*pause + tail.
            self.assertAlmostEqual(res.total_sec, round(0.5 + sum_parts + 0.5 * 3 + 0.8, 3), places=2)

    def test_empty_narration_returns_valid_result(self) -> None:
        scenes = [
            ComposedScene(
                scene_id="s1", section_id="s1", start_sec=0.0, duration_sec=5.0,
                kind="chart", component="candle",  # narration/body/heading 전부 없음
            ),
        ]
        with TemporaryDirectory() as tmp:
            audio_out = Path(tmp) / "audio" / "proj.mp3"
            res = build_scene_narration(
                scenes,
                backend=StubTTSBackend(),
                voice=None,
                audio_out=audio_out,
                ffmpeg_bin=_ffmpeg(),
            )
            self.assertEqual(res.cues, [])
            self.assertAlmostEqual(res.total_sec, 1.3, places=3)
            # 빈 경우에도 무음 mp3 를 써 둔다.
            self.assertTrue(audio_out.exists())


class TestRenderWithAudio(unittest.TestCase):
    def test_audio_block_injected(self) -> None:
        scenes = [
            ComposedScene(
                scene_id="s1", section_id="s1", start_sec=0.0, duration_sec=3.0,
                kind="text", heading="제목", body="본문",
            ),
            ComposedScene(
                scene_id="s2", section_id="s2", start_sec=3.0, duration_sec=4.0,
                kind="text", heading="제목2", body="본문2",
            ),
        ]
        cues = [ComposedCue(text="자막1", at_sec=0.5)]
        html_str = render_composition_html(
            title="테스트", scenes=scenes, cues=cues,
            audio_src="../assets/audio/proj.mp3",
        )
        self.assertIn("<audio", html_str)
        self.assertIn('src="../assets/audio/', html_str)
        self.assertIn('data-track-index="100"', html_str)
        # total = 3.0 + 4.0 = 7.0 → data-duration="7.000"
        self.assertIn('data-duration="7.000"', html_str)

    def test_no_audio_when_src_none(self) -> None:
        scenes = [
            ComposedScene(
                scene_id="s1", section_id="s1", start_sec=0.0, duration_sec=3.0,
                kind="text", heading="제목", body="본문",
            ),
        ]
        html_str = render_composition_html(title="테스트", scenes=scenes, cues=[])
        self.assertNotIn("<audio", html_str)

    def test_total_override_drives_root_and_audio_duration(self) -> None:
        # 나레이션 경로: 씬이 lead 오프셋에서 시작하므로 sum(씬) 이 아니라 실 총길이로
        # 루트·audio data-duration 을 강제해야 마지막 씬/음성이 안 잘린다(drift 회피).
        scenes = [
            ComposedScene(
                scene_id="s1", section_id="s1", start_sec=0.5, duration_sec=3.0,
                kind="text", heading="H", body="b",
            ),
            ComposedScene(
                scene_id="s2", section_id="s2", start_sec=3.5, duration_sec=4.0,
                kind="text", heading="H2", body="b2",
            ),
        ]
        html_str = render_composition_html(
            title="t", scenes=scenes, cues=[ComposedCue(text="c", at_sec=0.5)],
            audio_src="../assets/audio/p.mp3", total_override=8.3,
        )
        # sum(씬)=7.0 이지만 override=8.3 이 루트·audio 양쪽에 들어가야 함.
        self.assertEqual(html_str.count('data-duration="8.300"'), 2)
        self.assertNotIn('data-duration="7.000"', html_str)


if __name__ == "__main__":
    unittest.main()
