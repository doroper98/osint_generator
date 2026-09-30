"""G8 콘티 판(animatic) 루틴 (v4.9.0, back_and_forth D-0108, 사용자 결정 D97).

합격 조건 "자산 없는 환경에서도 렌더 가능"(D-0108·D-0114)을 지키려고, 모든 테스트는 **추적 파일만** 임시 폴더로 복사한
합성 프로젝트를 쓴다 — plan.json 은 TTS 없이 글자 수로 만든 합성 시각(정렬 없음 = ratio 앵커), 자산·미디어·tts 폴더 없음.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

REPO = Path(__file__).resolve().parent.parent


def synthetic_project(name: str, dst: Path) -> Path:
    """projects/<name> 의 git 추적 파일만 dst 로 복사 + 합성 plan.json(TTS 없음). 자산 폴더를 만들지 않는다."""
    from script.plan import load_script
    from script.schema import Plan
    from script.timeline import layout, sentence_rows

    files = subprocess.run(["git", "ls-files", f"projects/{name}"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    src = REPO / "projects" / name
    for f in files:
        q = dst / (REPO / f).relative_to(src)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / f, q)
    sc = load_script(dst)
    rows = sentence_rows(sc)
    for x in rows:
        x["mp3"] = str(dst / "tts" / f"{x['sid']}.mp3")
        x["npy"] = x["mp3"] + ".npy"
        x["dur"] = round(0.8 + 0.085 * len(x["text"]), 3)
        x["trim_offset"] = 0.0
    cards, ss, total = layout(rows)
    plan = Plan(sentences=rows, cards=cards, scene_start=ss, total=total, voice="synthetic", title=sc.title,
                subtitle=sc.subtitle, date=sc.date)
    (dst / "plan.json").write_text(plan.model_dump_json(), encoding="utf-8")
    return dst


def no_files():  # noqa: ANN201 — 이미지·영상·지형 래스터를 읽으면 실패하게 하는 패치 묶음
    def boom(*a, **k):  # noqa: ANN002, ANN003, ANN202
        raise AssertionError("콘티 판이 자산 파일을 읽었다")

    from engine.assets import Assets
    from engine.stage import MercatorStage

    return [mock.patch.object(Assets, n, boom) for n in ("load_image", "load_clip", "original", "raster", "scaled", "source_width")] \
        + [mock.patch.object(MercatorStage, "base_image", boom), mock.patch.object(Assets, "_load_geo", boom)]


class _Hormuz(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    proj: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj = synthetic_project("hormuz_korea", Path(cls.tmp.name) / "hormuz_korea")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def load(self):  # noqa: ANN201
        from engine.project import load_project

        return load_project(self.proj, animatic=True)


class PlaceholderLabelTest(unittest.TestCase):
    def test_kinds_and_labels(self) -> None:
        """요소 종류별 자리표시 문구(D-0108 예: `[뱃지: 김정은]` `[국기: KR]` `[휘장: 청와대]`). 목록 밖 = 오류(P10)."""
        from engine.layers.animatic import PLACEHOLDERS, label
        from rules import load_rules

        kinds = load_rules().animatic.placeholder.kinds
        self.assertEqual(set(kinds), {"person", "flag", "emblem", "photo", "clip", "cutout", "article", "post", "primitive", "panel", "card",
                                        "backdrop", "island"})   # v5.1.0 D-0123·D-0126 배경·아일랜드
        self.assertEqual(set(PLACEHOLDERS), {"badge", "photo", "clip", "cutout", "article", "post", "card", "panel", "primitive", "backdrop"})
        self.assertEqual((label("person", "김정은"), label("flag", "KR"), label("emblem", "청와대")),
                         ("[뱃지: 김정은]", "[국기: KR]", "[휘장: 청와대]"))
        self.assertEqual(label("panel", "relation — 제목"), "[패널: relation — 제목]")
        self.assertTrue(label("photo", "가" * 80).endswith("…]"))
        with self.assertRaises(KeyError):
            label("stamp", "x")

    def test_resolve_swaps_only_placeholder_types(self) -> None:
        from engine.layers.animatic import PLACEHOLDERS, resolve_animatic
        from engine.registry import FULL_LAYERS, resolve

        self.assertIs(FULL_LAYERS.resolve, resolve)
        for key in ("marker", "route", "boom", "series", "country", "ships", "dip", "barrier", "tanker_loop"):
            self.assertIs(resolve_animatic(key).render, resolve(key).render, key)   # 마커·경로·타격 링·시리즈 그대로
        self.assertIs(resolve_animatic("panel:relation").render, PLACEHOLDERS["panel"])
        self.assertIs(resolve_animatic("badge").render, PLACEHOLDERS["badge"])


class NoAssetRenderTest(_Hormuz):
    def test_renders_without_assets(self) -> None:
        """자산 없는 환경(추적 파일 + 합성 plan)에서 로드·렌더 — 이미지·영상·타일 파일 접근 0(패치가 읽으면 실패)."""
        from engine.render import render_frame
        from engine.stage import FlatMercatorStage

        self.assertFalse((self.proj / "assets").exists() or (self.proj / "media").exists())
        pats = no_files()
        for p in pats:
            p.start()
        try:
            P = self.load()  # noqa: N806
            self.assertIsInstance(P.R.stage, FlatMercatorStage)
            self.assertTrue(P.animatic)
            kinds = {e["type"] for e in P.events}
            self.assertTrue({"badge", "photo", "clip", "cutout", "card", "panel"} <= kinds)   # 요소 종류가 실제로 지나간다
            for e in P.events:
                if e["type"] in ("badge", "photo", "clip", "cutout", "card", "panel", "article"):
                    render_frame(P, min(P.n_frames - 1, int((e["t0"] + e["t1"]) / 2 * 24)))
        finally:
            for p in pats:
                p.stop()

    def test_missing_font_is_error(self) -> None:
        """콘티 판의 전제 자산 = 글꼴만(D-0115). 글꼴이 없으면 대체 글꼴로 조용히 그리지 않고 FontMissingError(P6)."""
        from engine import typography
        from engine.render import render_frame

        P = self.load()  # noqa: N806
        typography.require_family.cache_clear()
        try:
            with mock.patch.object(typography, "family_found", lambda fam: False), self.assertRaises(typography.FontMissingError):
                render_frame(P, P.n_frames // 2)
        finally:
            typography.require_family.cache_clear()

    def test_camera_bounds_equal_geo_yaml_tier(self) -> None:
        """막지도 경계 = geo.yaml 티어 W bbox(geo.prep tier_record 와 같은 값) — 카메라 클램프가 전편과 같다."""
        from engine.stage import ym
        from geo.prep import load_conf

        w = next(t for t in load_conf(self.proj).tiers if t.name == "W")
        self.assertEqual(self.load().R.stage.bounds, (w.bbox[0], ym(w.bbox[1]), w.bbox[2], ym(w.bbox[3])))

    def test_deterministic_md5(self) -> None:
        """결정성 — 같은 입력으로 두 번 로드·렌더한 프레임과 조각 mp4 의 md5 가 같다."""
        from engine.render import render_chunk, render_frame

        idx = [0, 400, 1200, 2600, 4000]
        a = [hashlib.md5(bytes(render_frame(self.load(), i)[1])).hexdigest() for i in idx]
        b = [hashlib.md5(bytes(render_frame(self.load(), i)[1])).hexdigest() for i in idx]
        self.assertEqual(a, b)
        outs = []
        for k in range(2):
            o = Path(self.tmp.name) / f"chunk{k}.mp4"
            render_chunk(self.load(), 1200, 1260, o)
            outs.append(hashlib.md5(o.read_bytes()).hexdigest())
        self.assertEqual(outs[0], outs[1])

    def test_band_on_top_even_in_black(self) -> None:
        """표식 띠 — 화면 위 가운데, 전체 페이드(첫 프레임 = 검정) 뒤에도 보인다. 전편 렌더에는 없다."""
        from engine.render import render_frame
        from rules import load_rules

        bg = load_rules().animatic.band.bg
        P = self.load()  # noqa: N806
        for i in (0, P.n_frames // 2, P.n_frames - 1):
            s, buf = render_frame(P, i)
            px = np.frombuffer(bytes(buf), np.uint8).reshape(480, 854, 4)[3, 427 - 60]   # BGRX, 띠 안(글자 밖)
            self.assertLess(abs(int(px[2]) - round(bg[0] * 255 * bg[3])), 40, (i, px))
            self.assertLess(int(px[1]), 60, (i, px))

    def test_checks_profile(self) -> None:
        """checks 콘티 프로파일 — rules animatic.checks_skip 은 돌지 않고 skipped 로 남는다. 나머지는 돈다."""
        from engine.checks import HARD, HONESTY, WARN, run_checks
        from engine.honesty import CHECK_IDS
        from engine.mux import project_provenance
        from engine.render import ANIMATIC_STAGES, auto_preview_times
        from rules import load_rules

        self.assertEqual(HONESTY, CHECK_IDS)
        P = self.load()  # noqa: N806
        skip = sorted(load_rules().animatic.checks_skip)
        self.assertTrue(set(skip) <= set(HARD) | set(WARN))
        ts = auto_preview_times(P)
        c = run_checks(P, ts, project_provenance(P, ANIMATIC_STAGES), [], None)
        self.assertEqual((c["profile"], c["skipped"]), ("animatic", skip))
        self.assertEqual(sorted(i["id"] for i in c["items"] if i.get("skipped")), skip)
        ran = {i["id"] for i in c["items"] if not i.get("skipped")}
        self.assertTrue({"offscreen", "subtitles", "shots", "stage_continuity", "overlap", "date"} <= ran)
        from engine.checks import profile_skips

        bad = load_rules()
        bad.animatic.checks_skip = ["nope"]
        with mock.patch("engine.checks.R_", bad), self.assertRaises(ValueError):
            profile_skips(P)


class CrimeaFlatMapTest(unittest.TestCase):
    def test_crimea_to_ua(self) -> None:
        """110m 국가 파일은 크림을 RU 에 넣는다 — crimea_to_ua 면 UA 로(04 §3.2)."""
        from shapely.geometry import MultiPolygon, Point, Polygon

        from engine.layers.animatic import load_flat_polygons

        pt = Point(34.1, 45.0)

        def owner(polys: dict) -> set[str]:
            return {k for k in ("RU", "UA") if MultiPolygon([Polygon(p[0], p[1:]) for p in polys[k]]).buffer(0).contains(pt)}

        self.assertEqual(owner(load_flat_polygons(False)), {"RU"})
        self.assertEqual(owner(load_flat_polygons(True)), {"UA"})


class AnimaticRunTest(unittest.TestCase):
    """render_animatic 전 과정(짧은 fed_timeline_demo 합성 + 합성 믹스) — mp4·provenance·deliver 거부."""

    @classmethod
    def setUpClass(cls) -> None:
        from engine.project import load_project
        from engine.render import render_animatic

        cls.tmp = tempfile.TemporaryDirectory()
        proj = synthetic_project("fed_timeline_demo", Path(cls.tmp.name) / "demo")
        P = load_project(proj, animatic=True)  # noqa: N806
        (proj / "out").mkdir()
        n = int(P.plan.total * 44100) + 44100
        tone = (0.05 * np.sin(np.arange(n) * 2 * np.pi * 220 / 44100)).astype(np.float32)
        np.repeat(tone[:, None], 2, 1).tofile(proj / "out" / "mix.f32")
        cls.proj = proj
        cls.final, cls.prov = render_animatic(P, 2)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_outputs_and_provenance(self) -> None:
        from rules import load_rules

        AN = load_rules().animatic  # noqa: N806
        self.assertEqual(self.final, self.proj / "out" / AN.output)
        self.assertFalse((self.proj / "out" / "video_noaudio.mp4").exists())   # 전편 산출물 자리를 쓰지 않는다
        disk = json.loads((self.proj / "out" / "animatic_provenance.json").read_text(encoding="utf-8"))
        self.assertIs(disk["animatic"], True)
        run = disk["animatic_run"]
        self.assertEqual((run["profile"], run["fps"], run["band"]), (AN.profile, 24, AN.band.text))
        self.assertEqual(run["checks_skipped"], sorted(AN.checks_skip))
        self.assertEqual((disk["stages"]["render"], disk["stages"]["mux"], disk["stages"]["mix"]), (False, False, True))
        probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format_tags=comment",
                                           "-of", "json", str(self.final)], capture_output=True, text=True, check=True).stdout)
        v = next(s for s in probe["streams"] if s["codec_type"] == "video")
        self.assertEqual((v["width"], v["height"], v["r_frame_rate"]), (854, 480, "24/1"))
        self.assertIn("audio", {s["codec_type"] for s in probe["streams"]})
        self.assertEqual(probe["format"]["tags"]["comment"], AN.mp4_comment)

    def test_deliver_refuses_animatic(self) -> None:
        """deliver(engine.mux)는 콘티 판을 거부 — video_noaudio.mp4 로 복사해도 메타데이터 표식으로 잡는다."""
        from engine.mux import AnimaticDeliverError, main, refuse_animatic

        with self.assertRaises(AnimaticDeliverError):
            refuse_animatic(self.final)
        with self.assertRaises(AnimaticDeliverError):
            refuse_animatic(self.proj / "out" / "animatic_noaudio.mp4")
        clean = Path(self.tmp.name) / "clean.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x36:d=0.2", str(clean)], check=True)
        refuse_animatic(clean)   # 전편(표식 없음)은 통과
        shutil.copy(self.proj / "out" / "animatic_noaudio.mp4", self.proj / "out" / "video_noaudio.mp4")
        try:
            with mock.patch("builtins.print") as pr:
                self.assertEqual(main([str(self.proj)]), 1)
            res = json.loads(pr.call_args[0][0])
            self.assertIn("콘티 판", res["errors"][0])
        finally:
            (self.proj / "out" / "video_noaudio.mp4").unlink()


if __name__ == "__main__":
    unittest.main()
