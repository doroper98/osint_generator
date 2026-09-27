"""rules/video_rules.yaml SSOT + config 단일화 (v2.0.0, docs/handoff/19 §5.4)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pydantic
import yaml

from orchestrator.config import CONFIG_PATH, load_config
from rules import RULES_PATH, load_rules, rules_hash


class RulesLoaderTest(unittest.TestCase):
    def test_loads_and_validates(self) -> None:
        r = load_rules()
        self.assertEqual(r.schema_version, 1)
        self.assertEqual(r.script_schema.scene_count, "free")
        self.assertIsNone(r.script_schema.duration_limit_sec)
        self.assertFalse(r.shot_grammar.zoom_bump)
        self.assertIn("vignette", r.hud.forbidden_components)
        self.assertIn("stamp", r.hud.forbidden_components)

    def test_decimal_policy_is_d6(self) -> None:
        self.assertEqual(load_rules().tts_rules.decimal_policy, "repo_jjeom_no_space")

    def test_unknown_key_fails_loud(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
        raw["hud"]["brand_mark"] = True
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.yaml"
            p.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
            with self.assertRaises(pydantic.ValidationError):
                load_rules(p)

    def test_hash_is_file_sha1(self) -> None:
        h = rules_hash()
        self.assertEqual(len(h), 40)
        self.assertEqual(h, rules_hash(RULES_PATH))


class ConfigSingleSourceTest(unittest.TestCase):
    def test_engine_llm_tts_sections(self) -> None:
        cfg = load_config(Path(CONFIG_PATH))
        self.assertEqual((cfg.engine.trial.width, cfg.engine.trial.height, cfg.engine.trial.fps), (854, 480, 24))
        self.assertEqual(cfg.llm.script_timeout_sec, 1200)
        self.assertEqual(cfg.tts.eleven_model_default, "eleven_multilingual_v2")

    def test_script_worker_timeout_from_config(self) -> None:
        from workers.script_worker import ScriptWorker

        self.assertEqual(ScriptWorker.invoke_timeout_key, "script_timeout_sec")

    def test_unknown_llm_key_fails_loud(self) -> None:
        raw = yaml.safe_load(Path(CONFIG_PATH).read_text(encoding="utf-8"))
        raw["llm"]["modle"] = "typo"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.yaml"
            p.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
            with self.assertRaises(pydantic.ValidationError):
                load_config(p)


if __name__ == "__main__":
    unittest.main()
