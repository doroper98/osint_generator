"""gate packet — 사용자 게이트 승인은 감독 세션이 기록한다(v7.4.0 back_and_forth D-0355, UF-267).

UF-267 원문: "내가 너한테만 교신하면 되는데 왜 이렇게 됐지? 재발 방지해" — 전쟁사 트랙에서 구현 세션이 사용자 승인을 대신 기록하려다
권한 장치(Self-Approval)에 막혀 7시간 멈췄다. 감독 작업 트리에는 out/(콘티 판 기록)·미추적 자산이 없어 approve 가 못 돌았다.
그래서 구현 세션이 projects/{pid}/gate_packet.json(git 추적)에 판정 입력을 묶고, out/ 없는 트리의 approve 는 그것으로 같은 판정을 한다.

v7.4.0 UF-914(콘티 판 단계 폐지): 게이트 ② 구역은 프리뷰 기록(prev/provenance.json)에서 만든다. out/·prev/ 둘 다 없는 트리가 packet 판정.

(가) out/·prev/ 없는 트리에서 packet 으로 게이트 ② 승인이 기록된다
(나) packet 지문(digest)이 어긋나거나 packet 이 없으면 거부
(다) packet 의 원고 지문이 현재 원고와 다르면 거부(게이트 ①·②)
(라) 프리뷰 기록이 있으면 작업 트리로 판정한다(packet 무시)
(바) 추적된 옛(콘티 판 기반) packet 은 그대로 읽히고 digest 가 맞지만 게이트 ② 근거로는 거부된다
(마) 게이트 ① 도 packet 으로 기록된다
"""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

import pytest

from orchestrator.project_manager import (
    GatePacketError, PreviewRecordError, approve_gate, build_gate_packet, gate_packet_digest, load_gate_packet, load_manifest,
    require_preview,
)
from schemas.models import GatePacket, ProjectState
from tests.test_gates_pipeline import _Proj

S = ProjectState


@pytest.mark.slow   # C8.3(D187) — 게이트 ① 미디어 계획 표를 실제로 만든다(느린 묶음)
class GatePacketTest(_Proj):
    @property
    def pdir(self):  # noqa: ANN201
        return self.root / "p"

    def _drop_out(self) -> None:
        """감독 작업 트리 흉내 — out/·prev/ 는 저장소 미추적이라 없다."""
        for d in ("out", "prev"):
            if (self.pdir / d).exists():
                shutil.rmtree(self.pdir / d)

    def _to_gate2(self) -> None:
        self.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)

    def test_a_gate2_from_packet_without_out(self) -> None:   # (가)
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        pkt = build_gate_packet(self.pdir, created_by="impl-session")
        self._drop_out()
        self._to_gate2()
        m = approve_gate(self.m, "preview_approval", by="사용자 원문 \"승인\" (UF-999)", cfg=self.cfg)
        self.assertEqual(m.current_state, "render")
        shown = load_manifest("p", self.cfg).gate_decisions[-1].shown
        self.assertIn(f"gate packet {pkt.digest[:10]}", shown["preview"])
        self.assertIn("impl-session", shown["preview"])
        self.assertNotIn("animatic", shown)
        self.assertTrue((self.pdir / "gate_packet.json").exists())

    def test_b_digest_mismatch_or_missing_rejected(self) -> None:   # (나)
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self._to_gate2()
        build_gate_packet(self.pdir, created_by="impl")
        self._drop_out()
        p = self.pdir / "gate_packet.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d["preview"]["pending_people"] = []           # 같은 값이라도
        d["preview"]["total_sec"] += 1.0              # 손으로 고친 값 = digest 불일치
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(GatePacketError, "digest"):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        p.unlink()
        with self.assertRaisesRegex(GatePacketError, "gate packet 없음"):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertEqual(load_manifest("p", self.cfg).current_state, "preview_approval")   # 기록 없음

    def test_c_script_changed_rejected(self) -> None:   # (다)
        self.to_gate1()
        build_gate_packet(self.pdir, created_by="impl")
        self._drop_out()
        sp = self.pdir / "script.yaml"
        sp.write_text(sp.read_text(encoding="utf-8") + "\n# 승인 뒤 고친 원고\n", encoding="utf-8")
        with self.assertRaisesRegex(GatePacketError, "script.yaml 가 바뀌었다"):
            approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        # 원천 지문(sources)을 빼도 게이트 ① 구역의 원고 지문으로 거부 — digest 를 다시 맞춘 위조
        from orchestrator.project_manager import gate_packet_digest  # noqa: PLC0415

        pkt = GatePacket.model_validate_json((self.pdir / "gate_packet.json").read_text(encoding="utf-8"))
        pkt.sources = {}
        pkt.digest = gate_packet_digest(pkt)
        (self.pdir / "gate_packet.json").write_text(pkt.model_dump_json(), encoding="utf-8")
        with self.assertRaisesRegex(GatePacketError, "원고 지문"):
            approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)

    def test_c2_gate2_script_changed_after_packet_rejected(self) -> None:   # (다) 게이트 ② — 승인 원고 ≠ 현재 원고
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self._to_gate2()
        sp = self.pdir / "script.yaml"
        sp.write_text(sp.read_text(encoding="utf-8") + "\n# 승인 뒤 고친 원고\n", encoding="utf-8")
        build_gate_packet(self.pdir, created_by="impl")   # 고친 원고로 다시 만든 packet 이어도
        self._drop_out()
        with self.assertRaisesRegex(PreviewRecordError, "게이트 ①"):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)

    def test_d_out_path_unchanged(self) -> None:   # (라)
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self._to_gate2()
        (self.pdir / "gate_packet.json").write_text("{깨진 packet", encoding="utf-8")   # 프리뷰 기록이 있으면 packet 은 읽지 않는다
        m = approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertEqual(m.current_state, "render")
        self.assertNotIn("gate packet", load_manifest("p", self.cfg).gate_decisions[-1].shown["preview"])

    def test_e_gate1_from_packet(self) -> None:   # (마)
        self.to_gate1()
        pkt = build_gate_packet(self.pdir, created_by="impl", preview=False)
        self.assertIsNone(pkt.preview)
        self._drop_out()
        m = approve_gate(self.m, "script_approval", by="사용자 원문 \"원고 승인\" (UF-998)", cfg=self.cfg)
        self.assertEqual(m.current_state, "voice_timeline")
        shown = load_manifest("p", self.cfg).gate_decisions[-1].shown
        self.assertEqual(shown["script_sha1"], pkt.script.script_sha1)
        self.assertIn(f"gate packet {pkt.digest[:10]}", shown["media_plan"])

    def test_build_refuses_preview_of_other_direction(self) -> None:
        """프리뷰를 만든 뒤 연출을 바꾸면 게이트 ② 구역을 만들지 않는다(옛 프리뷰로 승인 방지). 게이트 ① 구역만은 된다."""
        (self.pdir / "direction.yaml").write_text("events: []\n", encoding="utf-8")
        with self.assertRaisesRegex(PreviewRecordError, "현재 direction.yaml"):
            build_gate_packet(self.pdir, created_by="impl")
        self.assertIsNone(build_gate_packet(self.pdir, created_by="impl", preview=False).preview)

    def test_build_requires_impl_tree(self) -> None:
        self._drop_out()
        with self.assertRaisesRegex(GatePacketError, "구현 작업 트리"):
            build_gate_packet(self.pdir, created_by="impl")


class TrackedPacketCompatTest(unittest.TestCase):   # (바) — C3 호환: 선택 필드를 더해도 옛 packet digest 가 그대로 맞는다
    REPO = Path(__file__).resolve().parent.parent

    def test_old_animatic_packets_still_valid_but_refused_for_gate2(self) -> None:
        for pid in ("showcase_econ", "showcase_geo"):
            with self.subTest(pid=pid):
                pdir = self.REPO / "projects" / pid
                raw = json.loads((pdir / "gate_packet.json").read_text(encoding="utf-8"))
                pkt = GatePacket.model_validate(raw)
                self.assertEqual(gate_packet_digest(pkt), raw["digest"])
                self.assertEqual(load_gate_packet(pdir).digest, raw["digest"])
                if pkt.preview is None:   # 게이트 ① 구역만 있는 packet(showcase_geo)
                    continue
                self.assertIsNone(pkt.preview.preview_provenance_sha1)
                if not (pdir / "out").exists() and not (pdir / "prev" / "provenance.json").exists():
                    with self.assertRaisesRegex(GatePacketError, "옛 콘티 판 기반"):
                        require_preview(pdir, pkt.script.script_sha1)  # type: ignore[union-attr]
