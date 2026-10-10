"""영상 시리즈 레지스트리 모델 (v5.18.0, back_and_forth D-0171, DECISIONS D165).

`rules/series_registry.yaml` 한 파일이 시리즈와 소속 프로젝트를 정한다(direction 에 적지 않는다 — 연출 LLM 이 다시 쓰는 파일).
시리즈 테마는 한 번 적으면 사용자 결정 없이 바꾸지 않는다. 한 프로젝트가 두 시리즈에 있으면 로드 오류.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VideoSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    map_theme: str = Field(min_length=1)
    decided_by: str = Field(pattern=r"^D-\d{4}$")
    projects: list[str] = Field(default_factory=list)


class SeriesRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    series: dict[str, VideoSeries] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _unique(self) -> "SeriesRegistry":
        seen: dict[str, str] = {}
        for sid, s in self.series.items():
            for p in s.projects:
                if p in seen:
                    raise ValueError(f"프로젝트 {p!r} 가 시리즈 {seen[p]!r}·{sid!r} 둘에 있다 — 한 시리즈에만")
                seen[p] = sid
        return self

    def series_of(self, project_id: str) -> "tuple[str, VideoSeries] | None":
        return next(((sid, s) for sid, s in self.series.items() if project_id in s.projects), None)
