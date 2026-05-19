"""Pydantic 모델 패키지.

SSOT 주의:
- 본 패키지의 Pydantic 클래스가 도메인 데이터 구조의 단일 출처입니다.
- 마크다운 문서는 본 패키지에서 파생됩니다. 필드 변경 시 코드 먼저, 문서 나중.
"""

from schemas.models import __schema_version__

__all__ = ["__schema_version__"]
