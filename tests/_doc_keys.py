"""문서가 인용한 규칙·설정 키 대조 (v4.0.0, back_and_forth D-0072 작업 1·8).

문서는 수치를 복사하지 않고 키로 가리킨다(15 P3). 인용 형식은 백틱 안의 `rules:점.경로`(rules/video_rules.yaml)와
`config:점.경로`(config.yaml)다. 여기서는 그 경로가 실제 파일에 있는지만 본다.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
KEY = re.compile(r"`(rules|config):([A-Za-z0-9_.]+)`")
FILES = {"rules": REPO / "rules" / "video_rules.yaml", "config": REPO / "config.yaml"}


@lru_cache(maxsize=None)
def _doc(kind: str) -> dict:
    return yaml.safe_load(FILES[kind].read_text(encoding="utf-8"))


def key_exists(kind: str, path: str) -> bool:
    node: object = _doc(kind)
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def cited_keys(text: str) -> list[tuple[str, str]]:
    return KEY.findall(text)


def missing_keys(text: str) -> list[str]:
    return [f"{k}:{p}" for k, p in cited_keys(text) if not key_exists(k, p)]
