"""영상 주문 `projects/<pid>/order.yaml` — Pydantic 계약 (v4.4.0, docs/handoff/20 §11, back_and_forth D-0090 작업 4).

주문 템플릿(20 §11)을 파일로 남긴다. 장르 프롬프트 층(workers/prompt_loader.py)이 여기서 장르를 읽는다.
주문이 없는 프로젝트(v3·v4 지정학 영상)는 기본 장르(genres.load.DEFAULT_GENRE)이고 provenance 에 declared false.
장르 이름은 `genres/<genre>.yaml` 이 있어야 한다(없으면 GenreError — 조용히 기본 장르로 넘어가지 않는다, 15 P6).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrderData(_Strict):
    """데이터 요구(20 §5.1) — 레코드 id(data/series/<id>). 값은 주문에 쓰지 않는다."""

    series: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)   # 원문 대조 자료(성명서 등) — intake 소스 id 또는 URL
    notes: list[str] = Field(default_factory=list)


class OrderMedia(_Strict):
    """미디어 요구(20 §8) — 종류와 권리 조건. 실제 자산은 미디어 레지스트리."""

    wanted: list[str] = Field(min_length=1)
    rights: str = Field(min_length=1)


class OrderDecision(_Strict):
    """사용자 결정 항목(D-0090 표)의 현재 값과 출처 — user(사용자 답) | default(지침 기본값, 사용자 미확정)."""

    value: str
    by: Literal["user", "default"]
    ref: str = ""   # 근거 D 번호 등


class Order(_Strict):
    schema_version: Literal[1] = 1
    topic: str = Field(min_length=2)
    genre: str
    invariant_layer: Literal["docs/handoff/20 §1.1"] = "docs/handoff/20 §1.1"   # 불변 층은 협상 대상 아님(20 §1.3)
    length: Literal["내용이 정한다"] = "내용이 정한다"                              # 고정 막 금지(20 §11)
    instructions: list[str] = Field(min_length=1)                                  # 20 §11 주문 문장 그대로
    data: OrderData = Field(default_factory=OrderData)
    media: OrderMedia
    decisions: dict[str, OrderDecision] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _genre_exists(self) -> "Order":
        from genres.load import load_genre  # noqa: PLC0415 — 순환 import 회피

        load_genre(self.genre)
        return self


__all__ = ["Order", "OrderData", "OrderDecision", "OrderMedia"]
