"""DesignSheet 명명 규약 회귀 (docs/17_COLLAGE_DESIGN_SHEET.md §0, v1.0.6).

시트는 재사용되는 어휘집이므로 이름이 규칙 없이 늘어나면 재활용 시점에 전수 개명이
필요해진다. 본 테스트는 §0 규약을 코드가 실제로 집행하는지, 그리고 실제 배포 시트
(`design_sheets/shorts_collage_v1.json`)가 규약을 통과하는지 고정한다.
"""

from __future__ import annotations

import json
import pathlib
import re
import unittest

from pydantic import ValidationError

from schemas.models import (
    MOTION_UNIT_SUFFIXES,
    PALETTE_GROUPS,
    DesignSheet,
    css_var_name,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SHEET_PATH = REPO_ROOT / "design_sheets" / "shorts_collage_v1.json"


def _sheet(**overrides) -> dict:
    """규약을 통과하는 최소 시트 + 부분 덮어쓰기."""
    base = {
        "sheet_id": "shorts_collage_v1",
        "format": "shorts",
        "palette": {"paper_base": "#E8DFC9"},
        "typography": {"type_subtitle": "800 68px sans-serif"},
        "motion": {"motion_place_ms": 220},
    }
    base.update(overrides)
    return base


class TestSheetId(unittest.TestCase):
    """§0.1 — {format}_{concept}_v{gen}."""

    def test_valid_ids(self) -> None:
        for sheet_id, fmt in (
            ("shorts_collage_v1", "shorts"),
            ("shorts_dark_ink_v2", "shorts"),
            ("briefing_dark_ink_v12", "briefing"),
        ):
            with self.subTest(sheet_id=sheet_id):
                DesignSheet(**_sheet(sheet_id=sheet_id, format=fmt))

    def test_missing_generation_suffix(self) -> None:
        with self.assertRaisesRegex(ValidationError, "sheet_id 명명 규약 위반"):
            DesignSheet(**_sheet(sheet_id="shorts_collage"))

    def test_rejects_non_snake(self) -> None:
        for bad in ("Shorts_Collage_v1", "shorts-collage-v1", "shorts_collage_V1"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValidationError, "sheet_id 명명 규약 위반"):
                    DesignSheet(**_sheet(sheet_id=bad))

    def test_rejects_unknown_format_prefix(self) -> None:
        with self.assertRaisesRegex(ValidationError, "sheet_id 명명 규약 위반"):
            DesignSheet(**_sheet(sheet_id="reels_collage_v1"))

    def test_prefix_must_match_format_field(self) -> None:
        """접두어와 format 필드가 갈라지면 시트 조회가 거짓말을 하게 된다."""
        with self.assertRaisesRegex(ValidationError, "불일치"):
            DesignSheet(**_sheet(sheet_id="briefing_collage_v1", format="shorts"))


class TestTokenGroups(unittest.TestCase):
    """§0.2 — 그룹 접두어."""

    def test_all_palette_groups_accepted(self) -> None:
        palette = {f"{group}_sample": "#000000" for group in PALETTE_GROUPS}
        sheet = DesignSheet(**_sheet(palette=palette))
        self.assertEqual(len(sheet.palette), len(PALETTE_GROUPS))

    def test_palette_rejects_foreign_group(self) -> None:
        """`type_`/`motion_` 은 palette 그룹이 아니다."""
        for bad in ("type_subtitle", "motion_place_ms", "colour_red"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValidationError, "그룹 접두어"):
                    DesignSheet(**_sheet(palette={bad: "#000000"}))

    def test_palette_rejects_ungrouped_key(self) -> None:
        """v1.0.5 까지 쓰이던 무접두어 키 (`ink`, `tape`) 차단."""
        for bad in ("ink", "tape"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValidationError, "문법 위반"):
                    DesignSheet(**_sheet(palette={bad: "#000000"}))

    def test_typography_requires_type_group(self) -> None:
        with self.assertRaisesRegex(ValidationError, "그룹 접두어"):
            DesignSheet(**_sheet(typography={"paper_subtitle": "x"}))

    def test_rejects_uppercase_and_hyphen(self) -> None:
        for bad in ("paper_Base", "paper-base"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValidationError, "문법 위반"):
                    DesignSheet(**_sheet(palette={bad: "#000000"}))


class TestSpacingAxis(unittest.TestCase):
    """§0.2 `space_` 그룹 — v1.0.7 신설. 사용자 제시 시트 샘플 3종이 여백을 색·타이포와
    동급 축으로 다루는데 v1.0.6 까지 본 시트에는 축 자체가 없었다."""

    def test_accepts_space_group(self) -> None:
        sheet = DesignSheet(**_sheet(spacing={"space_gutter_px": 40}))
        self.assertEqual(sheet.spacing["space_gutter_px"], 40)

    def test_rejects_foreign_group(self) -> None:
        with self.assertRaisesRegex(ValidationError, "그룹 접두어"):
            DesignSheet(**_sheet(spacing={"motion_gutter_px": 40}))

    def test_requires_unit_suffix(self) -> None:
        with self.assertRaisesRegex(ValidationError, "단위 접미어가 없음"):
            DesignSheet(**_sheet(spacing={"space_gutter": 40}))

    def test_reaches_css_vars(self) -> None:
        sheet = DesignSheet(**_sheet(spacing={"space_gutter_px": 40}))
        self.assertEqual(sheet.to_css_vars()["--space-gutter-px"], "40")


class TestDisplayName(unittest.TestCase):
    """§0.10 — 기계 조회 키와 사람이 부르는 이름의 분리."""

    def test_optional_and_independent_of_sheet_id(self) -> None:
        sheet = DesignSheet(**_sheet(display_name="DOSSIER · KRAFT"))
        self.assertEqual(sheet.sheet_id, "shorts_collage_v1")
        self.assertEqual(sheet.display_name, "DOSSIER · KRAFT")

    def test_defaults_empty(self) -> None:
        self.assertEqual(DesignSheet(**_sheet()).display_name, "")


class TestMotionUnits(unittest.TestCase):
    """§0.2 — motion 토큰은 단위 접미어로 '단일 스칼라' 를 이름으로 보증한다."""

    def test_every_documented_suffix_accepted(self) -> None:
        motion = {f"motion_sample{suffix}": 1.0 for suffix in MOTION_UNIT_SUFFIXES}
        sheet = DesignSheet(**_sheet(motion=motion))
        self.assertEqual(len(sheet.motion), len(MOTION_UNIT_SUFFIXES))

    def test_rejects_v105_multivalue_tokens(self) -> None:
        """v1.0.5 문서의 복수값 토큰 이름은 이제 통과하지 못한다.

        `push_in_scale`(1.0→1.08) / `paper_breath`(scale 3, 8s) /
        `grain_loop`(4장 12fps) / `draw_on`(기법) — 전부 dict[str, float] 에
        담기지 않아 직렬화에서 유실되던 것들.
        """
        for legacy in ("push_in_scale", "paper_breath", "grain_loop", "draw_on"):
            with self.subTest(legacy=legacy):
                with self.assertRaises(ValidationError):
                    DesignSheet(**_sheet(motion={legacy: 1.0}))

    def test_rejects_missing_unit_suffix(self) -> None:
        with self.assertRaisesRegex(ValidationError, "단위 접미어가 없음"):
            DesignSheet(**_sheet(motion={"motion_place": 220}))


class TestCssVarMapping(unittest.TestCase):
    """§0.3 — 토큰 ↔ CSS 변수 기계적 1:1."""

    def test_mapping_is_mechanical(self) -> None:
        self.assertEqual(css_var_name("paper_crumpled"), "--paper-crumpled")
        self.assertEqual(css_var_name("motion_place_ms"), "--motion-place-ms")

    def test_to_css_vars_covers_all_tokens_and_safe_area(self) -> None:
        sheet = DesignSheet(**_sheet())
        css = sheet.to_css_vars()
        self.assertEqual(css["--paper-base"], "#E8DFC9")
        self.assertEqual(css["--type-subtitle"], "800 68px sans-serif")
        self.assertEqual(css["--motion-place-ms"], "220")   # 220.0 이 아니라 220
        self.assertEqual(css["--safe-top"], "220px")
        self.assertEqual(css["--safe-right"], "140px")

    def test_fractional_motion_kept(self) -> None:
        sheet = DesignSheet(**_sheet(motion={"motion_jitter_deg": 0.3}))
        self.assertEqual(sheet.to_css_vars()["--motion-jitter-deg"], "0.3")


class TestShippedSheet(unittest.TestCase):
    """배포 시트가 규약을 통과하고 17 문서의 토큰을 실제로 담고 있는지."""

    def setUp(self) -> None:
        self.sheet = DesignSheet(**json.loads(SHEET_PATH.read_text(encoding="utf-8")))

    def test_parses(self) -> None:
        self.assertEqual(self.sheet.sheet_id, "shorts_collage_v1")
        self.assertEqual((self.sheet.width, self.sheet.height), (1080, 1920))
        self.assertEqual(self.sheet.fps, 30)

    def test_safe_area_matches_doc(self) -> None:
        sa = self.sheet.safe_area
        self.assertEqual((sa.top, sa.bottom, sa.left, sa.right), (220, 350, 60, 140))

    def test_absorbed_drift_tokens_present(self) -> None:
        """코드에만 있던 `--paper-card` / `--hl-yellow` 가 정규 토큰으로 흡수됐는지."""
        self.assertEqual(self.sheet.palette["paper_card"], "#F4EFE3")
        self.assertEqual(self.sheet.palette["mark_highlighter"], "#F2D24B")

    def test_split_motion_tokens_present(self) -> None:
        """복수값이던 4개 토큰이 스칼라 쌍으로 쪼개져 실제로 담겼는지."""
        m = self.sheet.motion
        self.assertEqual(m["motion_push_in_from_scale"], 1.0)
        self.assertEqual(m["motion_push_in_to_scale"], 1.08)
        self.assertEqual(m["motion_breath_scale"], 3)
        self.assertEqual(m["motion_breath_period_ms"], 8000)
        self.assertEqual(m["motion_grain_count"], 4)
        self.assertEqual(m["motion_grain_fps"], 12)
        self.assertEqual(m["motion_draw_on_ms"], 400)

    def test_spacing_axis_populated(self) -> None:
        """v1.0.7 신설 축이 실제로 채워졌는지 (빈 dict 로 두면 축 신설의 의미가 없다)."""
        self.assertGreaterEqual(len(self.sheet.spacing), 4)
        self.assertEqual(self.sheet.spacing["space_gutter_px"], 40)

    def test_has_display_name(self) -> None:
        self.assertEqual(self.sheet.display_name, "DOSSIER · KRAFT")

    def test_all_four_verification_stamps_present(self) -> None:
        """G4 — 검증 라벨 4종은 시트에서 빠질 수 없다."""
        for key in (
            "stamp_confirm", "stamp_inferred", "stamp_unverified", "stamp_refuted",
        ):
            self.assertIn(key, self.sheet.palette)

    def test_round_trip(self) -> None:
        again = DesignSheet(**json.loads(self.sheet.model_dump_json()))
        self.assertEqual(again.model_dump(), self.sheet.model_dump())


class TestSpecimenTokenSync(unittest.TestCase):
    """스페시먼이 시트와 갈라지지 않는지 (17 §0.3).

    CSS 변수는 §0.3 매핑으로 검증하고, SVG data URI 처럼 var() 를 못 쓰는 자리는
    하드코딩 사본이 시트 값과 같은지 확인한다 — 사본이 조용히 갈라지는 것이
    v1.0.5 까지의 실제 드리프트 원인이었다.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.sheet = DesignSheet(**json.loads(SHEET_PATH.read_text(encoding="utf-8")))
        cls.html = (
            REPO_ROOT / "hyperframes" / "shorts" / "specimen_typo.html"
        ).read_text(encoding="utf-8")

    def test_declared_vars_exist_in_sheet(self) -> None:
        """`:root` 에 선언된 변수는 모두 시트에 출처가 있어야 한다."""
        declared = set(re.findall(r"^\s*(--[a-z-]+):", self.html, re.MULTILINE))
        known = set(self.sheet.to_css_vars())
        self.assertEqual(
            declared - known,
            set(),
            "시트에 없는 CSS 변수가 스페시먼에서 태어났다 (17 §0.3 위반)",
        )

    def test_used_vars_are_declared(self) -> None:
        """`var()` 로 참조하는 변수는 모두 선언돼 있어야 한다 (오타 방지)."""
        declared = set(re.findall(r"^\s*(--[a-z-]+):", self.html, re.MULTILINE))
        used = set(re.findall(r"var\((--[a-z-]+)\)", self.html))
        self.assertEqual(used - declared, set())

    def test_hardcoded_highlighter_matches_sheet(self) -> None:
        """형광펜 색은 data URI 안에 복제된다 — 시트 값과 일치해야 한다."""
        token = self.sheet.palette["mark_highlighter"].lstrip("#").upper()
        copies = re.findall(r"%23([0-9A-Fa-f]{6})'/></svg>", self.html)
        self.assertTrue(copies, "형광펜 data URI 사본을 찾지 못했다 — 패턴 갱신 필요")
        for copy in copies:
            self.assertEqual(copy.upper(), token)


if __name__ == "__main__":
    unittest.main()
