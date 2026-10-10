"""Q2 받는 경로(v5.15.1 back_and_forth D-0164) — 라이브러리 초상은 바이트 그대로, 권리 상태는 추정하지 않음, 초상 맞춤은 렌더 전.

결함 1: `library_portrait` 가 정규화 완료본을 다시 정규화(비멱등 — 끝 줄·열 탈락 + 재샘플)해 새 컨테이너의 골든이 어긋났다.
결함 2: `fetch_data` 가 권리 상태를 예외 유무로 추정해 예외 없는 restricted 가 rights_clear 로 덮일 수 있었다.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

import tools.asset_library as al
import tools.fetch_data as fd
from engine.assets import Assets, Labels
from engine.context import RenderCtx
from engine.style import BADGE, output_profile
from tests.anti_inertia._ast_util import REPO
from tools.portrait_fallback import library_portrait, normalize_portrait

LIB = REPO / "assets" / "library" / "library_manifest.json"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


class ReceiveBytesTest(unittest.TestCase):
    def test_library_portrait_copies_normalized_variant_bytes(self) -> None:
        """승격된(normalized) 변형은 받을 때 바이트 그대로 — 이재명 v02·노무현 v01. 재정규화는 멱등이 아님을 함께 확인(결함 재현)."""
        lib = {p["person_id"]: p for p in json.loads(LIB.read_text(encoding="utf-8"))["people"]}
        for pid in ("lee_jae_myung", "roh_moo_hyun"):
            v = lib[pid]["variants"][0]
            self.assertTrue(v.get("normalized"), pid)
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / f"{pid}.png"
                library_portrait(pid, out)
                self.assertEqual(_md5(out), _md5(REPO / v["path"]), pid)
        src = Image.open(REPO / lib["lee_jae_myung"]["variants"][0]["path"]).convert("RGBA")
        self.assertNotEqual(normalize_portrait(src).size, src.size)   # 다시 돌리면 줄이 빠진다 — 그래서 복사

    def test_promote_then_receive_roundtrip_is_byte_identical(self) -> None:
        """임시 라이브러리에서 promote → library_portrait 왕복 = 프로젝트 초상과 바이트 동일, 변형에 normalized: true."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            proj = d / "proj"
            (proj / "assets" / "portraits").mkdir(parents=True)
            a = np.zeros((420, 415, 4), np.uint8)
            a[40:, 60:350] = (200, 200, 200, 255)
            Image.fromarray(a, "RGBA").save(proj / "assets" / "portraits" / "zz_person.png")
            (proj / "assets" / "rights_registry.json").write_text(json.dumps({"people": {"zz_person": {
                "src": "x", "license": "CC BY 4.0", "artist": "A", "url": "https://example.org/x", "rights_status": "rights_clear"}}}),
                encoding="utf-8")
            lib = d / "lib.json"
            lib.write_text(json.dumps({"schema_version": 1, "generated_at": "2026-10-10", "people": [], "logos": [], "flags": []}),
                           encoding="utf-8")
            emb = d / "emb.json"
            emb.write_text(json.dumps({"emblems": {}}), encoding="utf-8")
            (d / "people").mkdir()
            with mock.patch.object(al, "LIB", lib), mock.patch.object(al, "PEOPLE_DIR", d / "people"), \
                    mock.patch.object(al, "EMBLEM_REGISTRY", emb), mock.patch.object(al, "EMBLEM_FILES", d / "ef"), \
                    mock.patch.object(al, "_entity_names", return_value=("가", "")):
                done = al.promote(proj, 2)
            self.assertEqual(done["people"], ["zz_person"])
            entry = json.loads(lib.read_text(encoding="utf-8"))["people"][0]
            self.assertTrue(entry["variants"][0]["normalized"])
            self.assertTrue(entry["variants"][0]["path"].endswith("zz_person_mono_v02.png"))
            out = d / "back.png"
            library_portrait("zz_person", out, manifest=lib)
            self.assertEqual(_md5(out), _md5(proj / "assets" / "portraits" / "zz_person.png"))


class RightsPassthroughTest(unittest.TestCase):
    def test_restricted_without_exception_stays_restricted_and_fails_credits(self) -> None:
        """라이브러리에 예외 없는 restricted → 프로젝트도 restricted(덮지 않음) → 크레딧 점검 오류(조용히 통과 금지)."""
        from engine.credits import Credits, RightsError, check_credits  # noqa: PLC0415

        lib = {"source": {"url": "https://example.org/p", "license": "공공누리 제4유형", "rights_status": "restricted", "credit": "기관"},
               "variant": {"path": "assets/library/people/x.png"}}
        r = fd.library_rights(lib)
        self.assertEqual(r["rights_status"], "restricted")
        self.assertNotIn("user_exception", r)
        cr = Credits.model_validate({"schema_version": 1, "sections": [{"title": "인물 사진", "column": 0,
                                     "items": [{"main": "가", "license": "기관", "rights": ["people.zz"]}]}]})
        with self.assertRaises(RightsError) as cm:
            check_credits(cr, {"people": {"zz": r}}, {}, {"people.zz"}, description=[])
        self.assertIn("restricted", str(cm.exception))
        lib["source"]["rights_status"] = "rights_clear"
        self.assertEqual(fd.library_rights(lib)["rights_status"], "rights_clear")


class PreflightFitTest(unittest.TestCase):
    def test_unfit_portrait_is_preflight_error_with_pid_and_R(self) -> None:
        """맞지 않는 초상(꽉 찬 사각형) → preflight 오류 목록에 pid·R(렌더 전, D-0164 §4). 맞는 초상은 오류 없음."""
        from engine.project import portrait_fit_errors  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "assets" / "portraits").mkdir(parents=True)
            Image.fromarray(np.full((512, 420, 4), 255, np.uint8), "RGBA").save(Path(d) / "assets" / "portraits" / "wide.png")
            a = np.zeros((512, 420, 4), np.uint8)
            yy, xx = np.mgrid[0:512, 0:420]
            a[(((xx - 210) / 100) ** 2 + ((yy - 140) / 130) ** 2 <= 1) | (yy >= 260)] = 255
            Image.fromarray(a, "RGBA").save(Path(d) / "assets" / "portraits" / "ok.png")
            R = RenderCtx(assets=Assets(Path(d), Labels(), geo=False), tb=None, out=output_profile("480p"))  # type: ignore[arg-type]  # noqa: N806
            errs = portrait_fit_errors(R, "wide")
            self.assertTrue(errs)
            self.assertTrue(all("portrait:wide" in e for e in errs))
            self.assertIn(f"R{BADGE.R_person_solo:g}", " ".join(errs))
            self.assertEqual(portrait_fit_errors(R, "wide"), [])   # 초상마다 한 번
            self.assertEqual(portrait_fit_errors(R, "ok"), [])


if __name__ == "__main__":
    unittest.main()
