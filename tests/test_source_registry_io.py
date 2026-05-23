"""source_registry_io 단위 테스트 (Phase 5, v0.5.5).

검증 범위
--------
1. load_partials — 결정론적 순서 (parsed task_id asc), missing dir → [].
2. persist_source_registry — atomic 영속화 round-trip.
3. build_and_persist_source_registry — e2e (로딩 → builder → 영속화) + 통계.
4. fail-fast — 손상된 partial JSON 전파, builder invariant (strict None) 전파.

io 격리: AppConfig 의 projects_root 를 절대경로 tmp 디렉토리로 지정하여
REPO_ROOT/projects 를 오염시키지 않는다 (project_dir 가 absolute projects_root 를
그대로 사용).

실행:
    python -m unittest tests.test_source_registry_io
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.config import AppConfig, PathsConfig
from orchestrator.source_registry_io import (
    build_and_persist_source_registry,
    load_partials,
    partials_dir,
    persist_source_registry,
    source_registry_path,
)
from schemas.models import (
    SourceCollectionPartial,
    SourceEntry,
    SourceRegistry,
)


def _entry(sid: str) -> SourceEntry:
    return SourceEntry(source_id=sid, platform="x", source_type="post")


def _partial(
    task_id: str,
    input_item_id: str | None,
    sources: list[SourceEntry],
    *,
    project_id: str = "proj_001",
) -> SourceCollectionPartial:
    return SourceCollectionPartial(
        project_id=project_id,
        task_id=task_id,
        input_item_id=input_item_id,
        collected_sources=sources,
    )


class _TmpProjects(unittest.TestCase):
    """절대경로 tmp projects_root 를 가진 AppConfig 를 제공."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cfg = AppConfig(paths=PathsConfig(projects_root=str(self.root)))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_partial(self, pid: str, partial: SourceCollectionPartial) -> Path:
        pdir = partials_dir(pid, self.cfg)
        pdir.mkdir(parents=True, exist_ok=True)
        path = pdir / f"{partial.task_id}.json"
        path.write_text(partial.model_dump_json(indent=2), encoding="utf-8")
        return path


class LoadPartialsTests(_TmpProjects):
    def test_missing_dir_returns_empty(self):
        self.assertEqual(load_partials("proj_001", self.cfg), [])

    def test_empty_dir_returns_empty(self):
        partials_dir("proj_001", self.cfg).mkdir(parents=True)
        self.assertEqual(load_partials("proj_001", self.cfg), [])

    def test_loads_and_parses_partials(self):
        self._write_partial("proj_001", _partial("t1", "i1", [_entry("s1")]))
        loaded = load_partials("proj_001", self.cfg)
        self.assertEqual(len(loaded), 1)
        self.assertIsInstance(loaded[0], SourceCollectionPartial)
        self.assertEqual(loaded[0].task_id, "t1")
        self.assertEqual(loaded[0].collected_sources[0].source_id, "s1")

    def test_deterministic_order_by_task_id(self):
        # 의도적으로 task_id 역순으로 작성. load 는 항상 task_id asc 로 반환해야 함.
        self._write_partial("proj_001", _partial("t3", "i3", [_entry("s3")]))
        self._write_partial("proj_001", _partial("t1", "i1", [_entry("s1")]))
        self._write_partial("proj_001", _partial("t2", "i2", [_entry("s2")]))
        loaded = load_partials("proj_001", self.cfg)
        self.assertEqual([p.task_id for p in loaded], ["t1", "t2", "t3"])

    def test_corrupted_json_propagates(self):
        pdir = partials_dir("proj_001", self.cfg)
        pdir.mkdir(parents=True)
        (pdir / "bad.json").write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            load_partials("proj_001", self.cfg)

    def test_schema_violation_propagates(self):
        pdir = partials_dir("proj_001", self.cfg)
        pdir.mkdir(parents=True)
        # project_id 누락 → ValidationError (fail-fast, 건너뛰지 않음).
        (pdir / "x.json").write_text(json.dumps({"task_id": "t1"}), encoding="utf-8")
        with self.assertRaises(Exception):
            load_partials("proj_001", self.cfg)

    def test_ignores_non_json_files(self):
        pdir = partials_dir("proj_001", self.cfg)
        pdir.mkdir(parents=True)
        (pdir / "README.txt").write_text("not a partial", encoding="utf-8")
        self._write_partial("proj_001", _partial("t1", "i1", [_entry("s1")]))
        loaded = load_partials("proj_001", self.cfg)
        self.assertEqual([p.task_id for p in loaded], ["t1"])


class PersistTests(_TmpProjects):
    def test_persist_round_trip(self):
        reg = SourceRegistry(project_id="proj_001", sources=[_entry("s1")])
        path = persist_source_registry("proj_001", reg, self.cfg)
        self.assertEqual(path, source_registry_path("proj_001", self.cfg))
        self.assertTrue(path.exists())
        reloaded = SourceRegistry.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded.project_id, "proj_001")
        self.assertEqual([s.source_id for s in reloaded.sources], ["s1"])

    def test_persist_creates_parent_dirs(self):
        reg = SourceRegistry(project_id="proj_001", sources=[])
        path = persist_source_registry("proj_001", reg, self.cfg)
        self.assertTrue(path.parent.exists())

    def test_persist_leaves_no_tmp_file(self):
        reg = SourceRegistry(project_id="proj_001", sources=[_entry("s1")])
        path = persist_source_registry("proj_001", reg, self.cfg)
        tmp = path.with_suffix(path.suffix + ".tmp")
        self.assertFalse(tmp.exists())


class BuildAndPersistTests(_TmpProjects):
    def test_e2e_build_persist_and_stats(self):
        self._write_partial("proj_001", _partial("t1", "i1", [_entry("s1"), _entry("s2")]))
        self._write_partial("proj_001", _partial("t2", "i2", []))
        self._write_partial("proj_001", _partial("t3", "i3", [_entry("s3")]))

        registry, stats = build_and_persist_source_registry("proj_001", cfg=self.cfg)

        self.assertEqual([s.source_id for s in registry.sources], ["s1", "s2", "s3"])
        self.assertEqual(stats["partial_count"], 3)
        self.assertEqual(stats["empty_partial_count"], 1)
        self.assertEqual(stats["source_count"], 3)

        # 디스크에도 같은 내용이 영속화됐는지.
        path = source_registry_path("proj_001", self.cfg)
        reloaded = SourceRegistry.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual([s.source_id for s in reloaded.sources], ["s1", "s2", "s3"])

    def test_no_partials_yields_empty_registry(self):
        registry, stats = build_and_persist_source_registry("proj_001", cfg=self.cfg)
        self.assertEqual(registry.sources, [])
        self.assertEqual(stats, {"partial_count": 0, "empty_partial_count": 0, "source_count": 0})
        # 빈 registry 도 영속화됨.
        self.assertTrue(source_registry_path("proj_001", self.cfg).exists())

    def test_strict_none_input_item_id_propagates(self):
        self._write_partial("proj_001", _partial("t1", None, [_entry("s1")]))
        with self.assertRaises(ValueError) as ctx:
            build_and_persist_source_registry("proj_001", cfg=self.cfg)
        self.assertIn("input_item_id=None", str(ctx.exception))
        # 실패 시 registry 가 쓰이지 않아야 함 (builder 가 영속화 전에 raise).
        self.assertFalse(source_registry_path("proj_001", self.cfg).exists())

    def test_lenient_mode_allows_none(self):
        self._write_partial("proj_001", _partial("t1", None, [_entry("s1")]))
        registry, _ = build_and_persist_source_registry(
            "proj_001", strict_input_item_id=False, cfg=self.cfg
        )
        self.assertEqual([s.source_id for s in registry.sources], ["s1"])

    def test_cross_partial_collision_propagates(self):
        self._write_partial("proj_001", _partial("t1", "i1", [_entry("dup")]))
        self._write_partial("proj_001", _partial("t2", "i2", [_entry("dup")]))
        with self.assertRaises(ValueError) as ctx:
            build_and_persist_source_registry("proj_001", cfg=self.cfg)
        self.assertIn("source_id 충돌", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
