"""NB5 — check_env 가 프록시 CA 가 certifi 번들에 붙었는지 검사한다(D-0031)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import check_env  # noqa: E402


def test_missing_proxy_ca_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "ca.crt"
    fake.write_text("-----BEGIN CERTIFICATE-----\nNOT-IN-CERTIFI-0123456789\n-----END CERTIFICATE-----\n", encoding="utf-8")
    monkeypatch.setenv("EXTRA_CA_BUNDLE", str(fake))
    row = check_env._proxy_ca_row()
    assert row is not None and row[2] is False and "missing" in row[3]


def test_no_proxy_ca_no_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRA_CA_BUNDLE", str(tmp_path / "absent.crt"))
    assert check_env._proxy_ca_row() is None
