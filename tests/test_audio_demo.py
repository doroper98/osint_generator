"""build-audio-demo (v0.32.2) — stub backend 로 end-to-end.

ElevenLabs / local 백엔드 실 호출은 사용자 머신 전용이라 stub 으로만 검증.
stub 은 무음 wav 를 만들고 narration 글자수에 비례한 가짜 duration 반환.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.audio_demo import build_audio_demo


_DEMO = {
    "title": "테스트 데모",
    "scenes": [
        {
            "sceneId": "s1",
            "startSec": 0,
            "durationSec": 5,
            "caption": "첫 장면",
            "narration": "안녕하세요. 첫 장면입니다.",
            "label": None,
            "sourceLinkRequired": False,
        },
        {
            "sceneId": "s2",
            "startSec": 5,
            "durationSec": 5,
            "caption": "두 번째",
            "narration": "이건 두 번째 장면이에요.",
            "label": None,
            "sourceLinkRequired": False,
        },
        {
            "sceneId": "s3",
            "startSec": 10,
            "durationSec": 3,
            "caption": "무음",
            "narration": "",  # 비어있으면 audio 생략, durationSec 그대로.
            "label": None,
            "sourceLinkRequired": False,
        },
    ],
}


class TestAudioDemo(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.props = self.tmp / "demo_props.json"
        self.props.write_text(
            json.dumps(_DEMO, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def test_stub_backend_writes_audio_and_updates_props(self) -> None:
        out = build_audio_demo(self.props, backend="stub")
        self.assertTrue(out.exists())
        self.assertEqual(out.name, "demo_props_with_audio.json")

        result = json.loads(out.read_text(encoding="utf-8"))
        scenes = result["scenes"]
        # 첫 두 scene: audioPath 박혔고, demo_audio 폴더에 파일 생성.
        self.assertTrue(scenes[0]["audioPath"].startswith("demo_audio/s1"))
        self.assertTrue((self.tmp / scenes[0]["audioPath"]).exists())
        self.assertTrue(scenes[1]["audioPath"].startswith("demo_audio/s2"))
        self.assertTrue((self.tmp / scenes[1]["audioPath"]).exists())
        # 세번째: narration 비어있어 audioPath 안 박힘.
        self.assertNotIn("audioPath", scenes[2])

    def test_startsec_recumulated_to_actual_durations(self) -> None:
        out = build_audio_demo(self.props, backend="stub")
        scenes = json.loads(out.read_text(encoding="utf-8"))["scenes"]
        # 누적 startSec 가 단조 증가.
        self.assertEqual(scenes[0]["startSec"], 0.0)
        self.assertEqual(scenes[1]["startSec"], scenes[0]["durationSec"])
        # 마지막 scene 의 startSec = 앞 두 scene 누적 duration.
        self.assertAlmostEqual(
            scenes[2]["startSec"],
            scenes[0]["durationSec"] + scenes[1]["durationSec"],
            places=2,
        )

    def test_missing_props_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            build_audio_demo(self.tmp / "no_such.json", backend="stub")

    def test_empty_scenes_raises(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"title": "x", "scenes": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            build_audio_demo(bad, backend="stub")


if __name__ == "__main__":
    unittest.main()
