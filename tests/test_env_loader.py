"""`.env` 자동 로딩(v0.32.1)이 의도대로 동작하는지 테스트.

핵심 invariant:
1. .env 가 있으면 키가 로드된다.
2. 이미 환경에 같은 키가 있으면 .env 가 override 하지 않는다(`override=False`).
3. .env 가 없으면 silent no-op.
4. `python-dotenv` 미설치는 silent no-op (이 환경에선 설치되어 있어 직접 검증 불가,
   `_load_env_file` 의 try/except 경로만 신뢰).
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from orchestrator.main import _load_env_file


class TestEnvLoader(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            "TEST_OSINT_KEY_A": os.environ.pop("TEST_OSINT_KEY_A", None),
            "TEST_OSINT_KEY_B": os.environ.pop("TEST_OSINT_KEY_B", None),
        }

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def _patch_env_path(self, env_text: str | None) -> mock._patch[mock.MagicMock]:
        """`_load_env_file` 가 보는 .env 경로를 임시 파일로 패치."""
        tmpdir = tempfile.mkdtemp()
        env_path = Path(tmpdir) / ".env"
        if env_text is not None:
            env_path.write_text(env_text, encoding="utf-8")
        # parent.parent 구조 흉내: env_loader 가 보는 경로가 tmpdir/.env 가 되도록
        # __file__ 을 tmpdir/orchestrator/main.py 처럼 흉내.
        orch_dir = Path(tmpdir) / "orchestrator"
        orch_dir.mkdir()
        fake_main = orch_dir / "main.py"
        fake_main.touch()
        return mock.patch("orchestrator.main.__file__", str(fake_main))

    def test_loads_keys_when_env_present(self) -> None:
        env_text = "TEST_OSINT_KEY_A=value-from-env\n"
        with self._patch_env_path(env_text):
            _load_env_file()
        self.assertEqual(os.environ.get("TEST_OSINT_KEY_A"), "value-from-env")

    def test_does_not_override_existing(self) -> None:
        os.environ["TEST_OSINT_KEY_A"] = "shell-exported"
        env_text = "TEST_OSINT_KEY_A=value-from-env\n"
        with self._patch_env_path(env_text):
            _load_env_file()
        # 운영 환경의 export 가 우선.
        self.assertEqual(os.environ["TEST_OSINT_KEY_A"], "shell-exported")

    def test_silent_when_env_missing(self) -> None:
        # 파일 없음 → no-op, 키 없음 유지.
        with self._patch_env_path(None):
            _load_env_file()
        self.assertIsNone(os.environ.get("TEST_OSINT_KEY_A"))

    def test_silent_when_dotenv_missing(self) -> None:
        # dotenv 가 없는 환경 흉내. ImportError 가 흡수되는지만 검증.
        env_text = "TEST_OSINT_KEY_B=should-not-be-set\n"
        with self._patch_env_path(env_text):
            with mock.patch.dict("sys.modules", {"dotenv": None}):
                _load_env_file()
        # dotenv import 실패면 키 안 들어옴. (조용히 통과 = OK)
        self.assertIsNone(os.environ.get("TEST_OSINT_KEY_B"))


if __name__ == "__main__":
    unittest.main()
