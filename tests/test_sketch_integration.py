"""스케치 통합 테스트 — 두 프로젝트를 CLI 경로(`__main__.main`)로 끝까지(D-0140 §5 S4, D-0147 §3).

`--check` 종료 0 → `--frames` 3컷(480p) → `sketch_provenance.json` 키·hard 0. 미사일 2D·`--globe`·전황 3 + 도해 카드 없는 사본(선택 확인)
+ 음성(깨진 사본 → 종료 ≠ 0 · 프레임 0 · provenance 없음 = P6) + 결정성(같은 입력 2회 → 프레임 md5 동일) + 스킬 파일 머리말·절.
지형 자산(geo.prep 산출)이 없으면 사유 있는 skip(글꼴 없음은 conftest 가 skip). 자산이 있는 환경에서는 skip 0 이어야 한다.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image

from engine.style import output_profile
from sketch.campaign.__main__ import main as campaign_main
from sketch.missile.__main__ import main as missile_main
from tests.anti_inertia._ast_util import REPO

MISSILE = REPO / "projects" / "d1_missile_sketch"
CAMPAIGN = REPO / "projects" / "uranus_sketch"
LINKED = ("assets", "globe_tex")          # 큰 생성 자산은 복사하지 않고 링크
PROV_KEYS = {"numbers_shown", "numbers_computed", "approximations", "checks", "data_files"}
SKILLS = ("missile-event-map", "campaign-front-map")
SECTIONS = ("①", "②", "③", "④", "⑤", "⑥", "⑦")
PREP = "지형 자산 없음 — python -m geo.prep {p} && python -m geo.prep {p} --res 720p (phaseS0 run_log §0)"


def _need_assets(*projects: Path) -> None:
    for p in projects:
        if not (p / "assets" / "tiers.pkl").is_file():
            raise unittest.SkipTest(PREP.replace("{p}", str(p.relative_to(REPO))))


def _copy(src: Path, dst: Path) -> Path:
    """프로젝트 사본 — out/ 제외, 생성 자산은 심볼릭 링크."""
    dst.mkdir(parents=True)
    for f in src.iterdir():
        if f.name == "out" or f.name == "__pycache__":
            continue
        if f.name in LINKED:
            (dst / f.name).symlink_to(f.resolve(), target_is_directory=True)
        elif f.is_dir():
            shutil.copytree(f, dst / f.name)
        else:
            shutil.copy2(f, dst / f.name)
    return dst


def _edit(proj: Path, fn) -> None:  # noqa: ANN001 — spec dict 를 바꾸는 함수
    p = proj / "sketch.yaml"
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_frames(self, main, proj: Path, times: str, stem: str, extra: list[str] | None = None) -> dict:  # noqa: ANN001
        extra = extra or []
        self.assertEqual(main([str(proj), "--check", *extra]), 0)
        self.assertEqual(main([str(proj), "--frames", times, *extra]), 0)
        out = proj / "out"
        pngs = sorted(out.glob(f"{stem}_*.png"))
        self.assertEqual(len(pngs), len(times.split(",")))
        op = output_profile("trial")
        for p in pngs:
            self.assertEqual(Image.open(p).size, (op.width, op.height))
        prov = json.loads((out / "sketch_provenance.json").read_text(encoding="utf-8"))
        self.assertLessEqual(PROV_KEYS, set(prov))
        self.assertLessEqual({"ran", "hard", "warnings"}, set(prov["checks"]))
        self.assertEqual(prov["checks"]["hard"], [])
        self.assertTrue(prov["data_files"])
        self.assertEqual(prov["render"]["profile"], op.name)
        return prov


class MissileIntegrationTest(_Base):
    def setUp(self) -> None:
        _need_assets(MISSILE, MISSILE / "globe_tex")
        super().setUp()

    def test_2d_frames(self) -> None:
        prov = self.run_frames(missile_main, _copy(MISSILE, self.tmp / "p"), "5,27,34", "sketch_2d")
        self.assertEqual(prov["kind"], "missile")
        self.assertIn("SK-H1", prov["checks"]["ran"])
        self.assertTrue(prov["numbers_shown"])

    def test_globe_frames(self) -> None:
        prov = self.run_frames(missile_main, _copy(MISSILE, self.tmp / "p"), "1,9,15", "sketch_globe", ["--globe"])
        self.assertIn("SK-H6", prov["checks"]["ran"])
        self.assertTrue(prov["numbers_computed"])          # 수평선 패널 기하 계산(D136)

    def test_card_is_optional(self) -> None:
        """권리가 분명한 도해가 없을 때 — media·card 를 빼도 검사·렌더 통과(D-0147 §1)."""
        proj = _copy(MISSILE, self.tmp / "p")
        shutil.rmtree(proj / "media")

        def drop(d: dict) -> None:
            d.pop("card")
            d.pop("media")
            d["sources"] = [s for s in d["sources"] if "도해" not in s["text"]]
        _edit(proj, drop)
        prov = self.run_frames(missile_main, proj, "5,14,27", "sketch_2d")
        self.assertNotIn("card_image", prov["features_drawn"])
        self.assertTrue(all(not f["path"].startswith("media/") for f in prov["data_files"]))

    def test_broken_spec_writes_nothing(self) -> None:
        """P6 — hard 위반이면 프레임도 provenance 도 쓰지 않는다."""
        proj = _copy(MISSILE, self.tmp / "p")
        _edit(proj, lambda d: d["track"].__setitem__("uncertainty_km", 0))     # approx 인데 반경 0 → SK-H2
        self.assertNotEqual(missile_main([str(proj), "--check"]), 0)
        self.assertNotEqual(missile_main([str(proj), "--frames", "5,27,34"]), 0)
        out = proj / "out"
        self.assertEqual(list(out.glob("*.png")) if out.exists() else [], [])
        self.assertFalse((out / "sketch_provenance.json").exists())


class CampaignIntegrationTest(_Base):
    def setUp(self) -> None:
        _need_assets(CAMPAIGN)
        super().setUp()

    def test_campaign_frames(self) -> None:
        prov = self.run_frames(campaign_main, _copy(CAMPAIGN, self.tmp / "p"), "11.5,38.5,51", "sketch_campaign")
        self.assertEqual(prov["kind"], "campaign")
        self.assertLessEqual({"SK-G1", "SK-G2", "SK-G3", "SK-H5"}, set(prov["checks"]["ran"]))
        self.assertEqual({w["id"] for w in prov["checks"]["warnings"]} - {"SK-C2"}, {"SK-G2"})   # D140 미세 조각 2(51초 = 집게 예약 상자 SK-C2)

    def test_deterministic_frames(self) -> None:
        """같은 입력 2회 → 같은 파일 이름·같은 픽셀(md5)."""
        runs = []
        for i in range(2):
            proj = _copy(CAMPAIGN, self.tmp / f"p{i}")
            self.assertEqual(campaign_main([str(proj), "--frames", "20,42"]), 0)
            runs.append({p.name: _md5(p) for p in (proj / "out").glob("*.png")})
        self.assertEqual(sorted(runs[0]), ["sketch_campaign_020.0.png", "sketch_campaign_042.0.png"])
        self.assertEqual(runs[0], runs[1])


class SkillFilesTest(unittest.TestCase):
    def test_frontmatter_and_sections(self) -> None:
        for name in SKILLS:
            p = REPO / ".claude" / "skills" / name / "SKILL.md"
            text = p.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            self.assertIsNotNone(m, name)
            head = yaml.safe_load(m.group(1))
            self.assertEqual(head["name"], name)
            self.assertGreater(len(head["description"]), 20)
            heads = [ln for ln in text.splitlines() if ln.startswith("## ")]
            self.assertEqual([h[3] for h in heads], list(SECTIONS), name)       # ①~⑦ 순서
            self.assertIn("docs/handoff/22_SKETCH_TRACK.md", text)
            self.assertNotIn("```python", text)                                # 코드 없음(D131)


if __name__ == "__main__":
    unittest.main()
