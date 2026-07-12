"""orchestrator.tts_pronounce 단위 테스트 (TTS-AP-054 ~ 057, v0.34.10).

목적: ElevenLabs misread (한자어 숫자, 외래어 경음화, 기호 %) 의 회귀 잠금.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.tts_pronounce import (
    apply_pronunciation,
    load_dict,
    num_to_sino_kr,
)


class TestNumToSinoKr(unittest.TestCase):
    def test_zero(self) -> None:
        self.assertEqual(num_to_sino_kr(0), "영")

    def test_ones(self) -> None:
        self.assertEqual(num_to_sino_kr(1), "일")
        self.assertEqual(num_to_sino_kr(9), "구")

    def test_teens(self) -> None:
        # TTS-AP-058: 한 숫자 안 음절은 붙여 쓴다 (연음/운율 보존).
        self.assertEqual(num_to_sino_kr(10), "십")
        self.assertEqual(num_to_sino_kr(19), "십구")
        self.assertEqual(num_to_sino_kr(21), "이십일")

    def test_hundreds(self) -> None:
        self.assertEqual(num_to_sino_kr(100), "백")
        self.assertEqual(num_to_sino_kr(102), "백이")
        self.assertEqual(num_to_sino_kr(114), "백십사")
        self.assertEqual(num_to_sino_kr(120), "백이십")
        self.assertEqual(num_to_sino_kr(168), "백육십팔")  # [뱅뉵씹팔] 연음 유도
        self.assertEqual(num_to_sino_kr(999), "구백구십구")

    def test_thousands(self) -> None:
        self.assertEqual(num_to_sino_kr(1000), "천")
        self.assertEqual(num_to_sino_kr(1024), "천이십사")
        self.assertEqual(num_to_sino_kr(9876), "구천팔백칠십육")

    def test_man(self) -> None:
        self.assertEqual(num_to_sino_kr(10000), "일만")
        self.assertEqual(num_to_sino_kr(12345), "일만이천삼백사십오")


class TestApplyPronunciation(unittest.TestCase):
    def test_no_mapping_passthrough_for_pure_text(self) -> None:
        self.assertEqual(apply_pronunciation("안녕하세요"), "안녕하세요")

    def test_number_auto_to_sino(self) -> None:
        # 단순 숫자만 — sino-Korean 변환 (음절 붙임, TTS-AP-058).
        self.assertEqual(apply_pronunciation("19"), "십구")

    def test_number_then_hangul_unit_attached(self) -> None:
        """TTS-AP-065: 숫자와 단위어는 붙인다 — 한 호흡이어야 연음·경음이 산다.
        (기존 '공백 삽입' 방침은 [백육십팔 / 딸러]로 끊겨 폐기 — 실청취 피드백 2026-07-12)"""
        self.assertEqual(apply_pronunciation("80달러"), "팔십달러")
        self.assertEqual(apply_pronunciation("19일"), "십구일")
        self.assertEqual(apply_pronunciation("5월"), "오월")

    def test_thousands_comma_merged(self) -> None:
        """TTS-AP-064: 천단위 콤마는 하나의 수로 — '일,삼백구십오,영 원' 파탄 방지."""
        self.assertEqual(apply_pronunciation("1,395,000원"), "백삼십구만오천원")
        self.assertEqual(apply_pronunciation("339,500원"), "삼십삼만구천오백원")
        self.assertEqual(apply_pronunciation("2,700"), "이천칠백")

    def test_dict_overrides_take_precedence(self) -> None:
        """TTS-AP-054: 외래어 경음화 매핑."""
        d = {"달러": "딸러", "유가": "유까"}
        self.assertEqual(apply_pronunciation("달러는 유가 지표", d), "딸러는 유까 지표")

    def test_dict_then_number_combined(self) -> None:
        """사용자 사전 적용 후 남은 숫자 자동 변환 — 둘 다 작동."""
        d = {"달러": "딸러"}
        self.assertEqual(apply_pronunciation("102달러", d), "백이딸러")

    def test_percent_mapping(self) -> None:
        """TTS-AP-056: % 직접 사용 회피."""
        d = {"%": " 퍼센트 "}
        # 사용자 사전 적용 → 20 만 남음 → 자동 변환 + 단위 공백.
        self.assertEqual(apply_pronunciation("20%", d), "이십 퍼센트 ")

    def test_long_dict_keys_first(self) -> None:
        """더 긴 key 가 먼저 적용 — '20%' 가 '%' 보다 우선."""
        d = {"%": " 퍼센트 ", "20%": "이십 퍼센트"}
        self.assertEqual(apply_pronunciation("20%", d), "이십 퍼센트")

    def test_no_mapping_none_safe(self) -> None:
        self.assertEqual(apply_pronunciation("102달러", None), "백이달러")

    def test_underscore_key_in_dict_filtered(self) -> None:
        """load_dict 가 _comment 같은 메타 key 를 필터 (적용 안 함)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "pronounce.json"
            p.write_text(
                json.dumps({"_comment": "ignore me", "달러": "딸러"}, ensure_ascii=False),
                encoding="utf-8",
            )
            d = load_dict(p)
            self.assertIn("달러", d)
            self.assertNotIn("_comment", d)

    def test_load_dict_missing_returns_empty(self) -> None:
        self.assertEqual(load_dict(Path("/no/such/file.json")), {})


if __name__ == "__main__":
    unittest.main()
