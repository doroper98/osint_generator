"""config.yaml 로더.

본 모듈은 운영 파라미터의 유일한 진입점입니다.
도메인 데이터(프로젝트 상태 등)는 여기에 두지 않습니다.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = REPO_ROOT / "config.yaml"


class CommandCenterConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    worker_slot_count: int = 4
    heartbeat_timeout_sec: int = 60
    log_panel_max_lines: int = 500
    log_router_read_chunk: int = 1024
    tui_refresh_interval_sec: float = 0.5


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    level: str = "INFO"
    file: str = "logs/orchestrator.log"
    rotate_daily: bool = True
    retention_days: int = 30


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    projects_root: str = "projects"
    python_bin: str = "python"


class LLMConfig(BaseModel):
    """구독 LLM 브리지 설정 (v0.43.5, v2.0.0 확장). model 은 `claude -p --model` 에 그대로 전달.

    extra="forbid" — config.yaml 오타·미지 키를 조용히 무시하지 않는다 (docs/handoff/15 P6).
    """

    model_config = ConfigDict(extra="forbid")

    model: str = "claude-opus-5-5"
    invoke_timeout_sec: int = 600
    script_timeout_sec: int = 1200


class OutputProfile(BaseModel):
    """출력 프로파일 한 벌(v3.6.0 D-0066 작업 1) — 장치 크기·fps·인코딩."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)
    crf: int = Field(ge=0, le=51)
    preset: str


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: str = "480p"
    profiles: dict[str, OutputProfile] = Field(default_factory=lambda: {
        "480p": OutputProfile(width=854, height=480, fps=24, crf=19, preset="faster"),
        "1080p": OutputProfile(width=1920, height=1080, fps=24, crf=19, preset="faster")})

    @model_validator(mode="after")
    def _known_default(self) -> "OutputConfig":
        if self.default not in self.profiles:
            raise ValueError(f"engine.output.default {self.default!r} 가 profiles {sorted(self.profiles)} 에 없다")
        return self


class EngineConfig(BaseModel):
    """새 엔진 렌더 설정 (v2.0.0, docs/handoff/19 §5.4; v3.6.0 출력 프로파일)."""

    model_config = ConfigDict(extra="forbid")

    output: OutputConfig = Field(default_factory=OutputConfig)
    trial: str = "480p"     # 프로파일 별칭
    final: str = "1080p"
    jobs: int = 4

    @model_validator(mode="after")
    def _aliases(self) -> "EngineConfig":
        for k in ("trial", "final"):
            if getattr(self, k) not in self.output.profiles:
                raise ValueError(f"engine.{k} {getattr(self, k)!r} 가 engine.output.profiles {sorted(self.output.profiles)} 에 없다")
        return self

    def profile(self, name: str | None = None) -> tuple[str, OutputProfile]:
        """이름(또는 별칭 trial·final, None = default) → (프로파일 이름, 프로파일). 없는 이름 = 오류(P6)."""
        n = name or self.output.default
        n = getattr(self, n) if n in ("trial", "final") else n
        if n not in self.output.profiles:
            raise ValueError(f"출력 프로파일 {name!r} 없음 — config engine.output.profiles: {sorted(self.output.profiles)}")
        return n, self.output.profiles[n]


class VoiceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stability: float = 0.65
    similarity_boost: float = 0.8
    style: float = 0.1


class TTSConfig(BaseModel):
    """TTS 설정 (v2.0.0). voice id·API 키는 .env 로만 (C9)."""

    model_config = ConfigDict(extra="forbid")

    backend_default: str = "elevenlabs"
    edge_voice: str = "ko-KR-InJoonNeural"
    edge_rate: str = "-3%"
    edge_pitch: str = "-2Hz"
    eleven_model_env: str = "ELEVENLABS_MODEL_ID"
    eleven_model_default: str = "eleven_multilingual_v2"
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    local_invoke_timeout_sec: int = 600


class CommonsConfig(BaseModel):
    """위키미디어 공용 요청 설정 (v2.5.5, D-0031 NB4) — tools/commons_fetch·media_fetch·fetch_data 가 공유.
    14 §10.4: 요청 간격 15초, 429 는 60초부터 지수 대기(최대 600초, Retry-After 우선), 시도 상한."""

    model_config = ConfigDict(extra="forbid")

    gap_sec: float = 15.0
    backoff_base_sec: float = 60.0
    backoff_max_sec: float = 600.0
    tries: int = 6
    standard_widths: list[int] = Field(default_factory=lambda: [500, 960, 1280, 1600])


class ReviewGatesConfig(BaseModel):
    """사용자 승인 게이트 (v3.0.0, 16 §5). 키 = 게이트 상태 값, 값은 true 만(끌 수 없다)."""

    model_config = ConfigDict(extra="forbid")

    require_human_approval: dict[str, bool] = Field(
        default_factory=lambda: {"script_approval": True, "preview_approval": True})

    @model_validator(mode="after")
    def _two_gates(self) -> "ReviewGatesConfig":
        keys = set(self.require_human_approval)
        if keys != {"script_approval", "preview_approval"}:
            raise ValueError(f"review_gates.require_human_approval 키는 script_approval·preview_approval 두 개(16 §5): {sorted(keys)}")
        if not all(self.require_human_approval.values()):
            raise ValueError("review_gates.require_human_approval 은 끌 수 없다(true 만, 16 §5)")
        return self


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = 1
    command_center: CommandCenterConfig = Field(default_factory=CommandCenterConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    commons: CommonsConfig = Field(default_factory=CommonsConfig)
    review_gates: ReviewGatesConfig = Field(default_factory=ReviewGatesConfig)


def load_config(path: Path | None = None) -> AppConfig:
    """config.yaml 을 읽어 AppConfig 로 검증해 반환합니다.

    파일이 없으면 기본값으로 동작합니다.
    """
    target = path or CONFIG_PATH
    if not target.exists():
        return AppConfig()
    raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(raw)


def project_dir(project_id: str, cfg: AppConfig | None = None) -> Path:
    """프로젝트 디렉토리 절대경로."""
    cfg = cfg or load_config()
    return REPO_ROOT / cfg.paths.projects_root / project_id
