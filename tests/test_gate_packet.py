"""gate packet — 사용자 게이트 승인은 감독 세션이 기록한다(v7.4.0 back_and_forth D-0355, UF-267).

UF-267 원문: "내가 너한테만 교신하면 되는데 왜 이렇게 됐지? 재발 방지해" — 전쟁사 트랙에서 구현 세션이 사용자 승인을 대신 기록하려다
권한 장치(Self-Approval)에 막혀 7시간 멈췄다. 감독 작업 트리에는 out/(콘티 판 기록)·미추적 자산이 없어 approve 가 못 돌았다.
그래서 구현 세션이 projects/{pid}/gate_packet.json(git 추적)에 판정 입력을 묶고, out/ 없는 트리의 approve 는 그것으로 같은 판정을 한다.

(가) out/ 없는 트리에서 packet 으로 게이트 ② 승인이 기록된다
(나) packet 지문(digest)이 어긋나거나 packet 이 없으면 거부
(다) packet 의 원고 지문이 현재 원고와 다르면 거부(게이트 ①·②)
(라) out/ 이 있으면 지금처럼 out/ 로 판정한다(packet 무시)
(마) 게이트 ① 도 packet 으로 기록된다
"""

from __future__ import annotations

import json
import shutil

import pytest

from orchestrator.project_manager import (
    AnimaticMissingError, GatePacketError, approve_gate, build_gate_packet, load_manifest,
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
        """감독 작업 트리 흉내 — out/ 은 저장소 미추적이라 없다."""
        shutil.rmtree(self.pdir / "out")

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
        self.assertIn(f"gate packet {pkt.digest[:10]}", shown["animatic"])
        self.assertIn("impl-session", shown["animatic"])
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

    def test_c2_gate2_animatic_from_other_script_rejected(self) -> None:   # (다) 게이트 ② — 콘티 판 원고 ≠ 승인 원고
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self._to_gate2()
        prov = self.pdir / "out" / "animatic_provenance.json"
        d = json.loads(prov.read_text(encoding="utf-8"))
        d["animatic_run"]["script_sha1"] = "f" * 40
        prov.write_text(json.dumps(d), encoding="utf-8")
        build_gate_packet(self.pdir, created_by="impl")
        self._drop_out()
        with self.assertRaisesRegex(AnimaticMissingError, "승인 원고"):
            approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)

    def test_d_out_path_unchanged(self) -> None:   # (라)
        self.to_gate1()
        self.m = approve_gate(self.m, "script_approval", by="t", cfg=self.cfg)
        self._to_gate2()
        (self.pdir / "gate_packet.json").write_text("{깨진 packet", encoding="utf-8")   # out/ 이 있으면 packet 은 읽지 않는다
        m = approve_gate(self.m, "preview_approval", by="t", cfg=self.cfg)
        self.assertEqual(m.current_state, "render")
        self.assertNotIn("gate packet", load_manifest("p", self.cfg).gate_decisions[-1].shown["animatic"])

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

    def test_build_requires_out(self) -> None:
        self._drop_out()
        with self.assertRaisesRegex(GatePacketError, "out 이 없다"):
            build_gate_packet(self.pdir, created_by="impl")
