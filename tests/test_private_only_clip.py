"""v7.4.0 사용자 결정 D264 — 비공개 시청 전제: 저작권 있는 공개 영상 클립은 권리를 기록만(scope private_only + rights_status restricted).

D264 원문: "어짜피 어딘가에 올릴 영상도 아니고 … 무단이용에 대한 제한은 없으니 그부분을 너무 강제로 막거나 하지 마"
- 레지스트리: kind video + scope private_only 는 rights_status restricted 로만(권리 확인 자산이 아니다). 사진 등 다른 종류는 여전히 불가.
- 렌더 권리 게이트: 그 클립은 통과, provenance private_only_assets 에 남는다(공개 배포 금지 표시).
"""

from __future__ import annotations

import unittest

from engine.layers.media import RightsError, validate_media
from schemas.media_models import MediaAsset

BASE = dict(kind="video", title="FOMC Introductory Statement, September 16, 2026", license="저작권 있음 · 비공개 시청 한정(D264)",
            author="Federal Reserve", credit_author="미 연준", date="2026-09-16", url="https://www.youtube.com/watch?v=x",
            caption="워시 연준 의장 성명 낭독", file_note="2026. 09. 16", depicts=["케빈 워시 연준 의장"], is_file_photo=False,
            verified_by={"by": "t", "on": "2026-10-29", "casualty_free": True, "relevance": "r", "segment_checked": (1.0, 5.0)},
            rights_status="restricted", retrieved_at="2026-10-29", tool={"name": "media_fetch.clip", "params": {}},
            source_hash="0" * 32, file="c", duration=10.0, segment=(1.0, 5.0), scope="private_only")


class PrivateOnlyClipTest(unittest.TestCase):
    def test_video_private_only_requires_restricted(self) -> None:
        MediaAsset.model_validate(BASE)
        with self.assertRaisesRegex(ValueError, "restricted"):
            MediaAsset.model_validate({**BASE, "rights_status": "rights_clear"})

    def test_photo_private_only_still_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "inset·video"):
            MediaAsset.model_validate({**BASE, "kind": "photo", "duration": None, "segment": None,
                                       "verified_by": {**BASE["verified_by"], "segment_checked": None}})

    def test_render_gate_passes_private_only_clip_only(self) -> None:
        a = MediaAsset.model_validate(BASE)
        self.assertIs(validate_media({"type": "clip", "mid": "m", "t0": 0}, {"m": a}), a)
        b = MediaAsset.model_validate({**BASE, "scope": None})
        with self.assertRaises(RightsError):
            validate_media({"type": "clip", "mid": "m", "t0": 0}, {"m": b})


if __name__ == "__main__":
    unittest.main()
