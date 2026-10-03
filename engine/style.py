"""스타일 토큰 — 색·폰트·출력 규격 (v2.1.0, 19 부록 D `hexc, C, FONT`).

색·폰트 이름은 `rules/video_rules.yaml`, 출력 프로파일(장치 크기·인코딩)은 `config.yaml engine.output` 에서 온다(15 P3).
이 모듈이 엔진 안에서 규칙 값을 푸는 유일한 곳이다(test_single_config 허용 목록).

v3.6.0 해상도(D-0066 작업 1·2, D-0067 A): **설계 좌표는 854×480 고정**(`W_OUT`·`H_OUT` = rules `layout_480p.base`).
레이어·패널·자막·배치·검사는 설계 좌표만 본다. 장치 크기는 `Output`(렌더 진입의 `ctx.scale(k)` 한 곳, 래스터 준비, 인코딩)만 안다.
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator.config import load_config
from rules import load_rules

_RULES = load_rules()
_CFG = load_config()

_BASE = _RULES.layout_480p.base
W_OUT: int = _BASE.w          # 설계 좌표 폭(854) — 해상도와 무관
H_OUT: int = _BASE.h          # 설계 좌표 높이(480)
FPS: int = _BASE.fps


@dataclass(frozen=True)
class Output:
    """출력 프로파일(장치). k = height / 480. 설계 폭 × k 와 장치 폭의 차는 좌우 균등(pad_x, 음수 = 양옆을 그만큼 잘라냄 —
    1080p 는 854 × 2.25 = 1921.5 > 1920 이라 −0.75px)."""

    name: str
    width: int
    height: int
    fps: int
    crf: int
    preset: str
    mem_per_job_mb: int

    @property
    def k(self) -> float:
        return self.height / H_OUT

    @property
    def pad_x(self) -> float:
        return (self.width - W_OUT * self.k) / 2

    def px(self, n: float) -> float:
        """설계 px → 장치 px(실수). 반올림하지 않는다 — 비율을 깨지 않게(D-0067 요건 2)."""
        return n * self.k

    def px_i(self, n: float) -> int:
        """정수가 필요한 곳(표면·래스터·타일 폭)만."""
        return max(1, round(n * self.k))

    def record(self) -> dict:
        """provenance `render.resolution`."""
        return {"profile": self.name, "width": self.width, "height": self.height, "fps": self.fps, "k": self.k,
                "pad_x": self.pad_x, "crf": self.crf, "preset": self.preset}


def output_profile(name: str | None = None) -> Output:
    """config engine.output 의 프로파일(이름·별칭 trial/final, None = default). 설계 fps 와 다르면 오류."""
    n, p = _CFG.engine.profile(name)
    if p.fps != FPS:
        raise ValueError(f"출력 프로파일 {n} fps {p.fps} ≠ 설계 fps {FPS} — 타이밍이 프레임 단위라 바꿀 수 없다")
    return Output(n, p.width, p.height, p.fps, p.crf, p.preset, p.mem_per_job_mb)

Color = tuple[float, float, float]


def hexc(h: str) -> Color:
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


_c = _RULES.colors
C: dict[str, Color] = {
    "ru": hexc(_c.ru), "us": hexc(_c.us), "gold": hexc(_c.gold), "teal": hexc(_c.teal), "green": hexc(_c.green),
    "muted": hexc(_c.muted), "amber": hexc(_c.amber), "white": (1, 1, 1), "kr": hexc(_c.gold), "water": hexc(_c.water),
}
SEA_LABEL: Color = hexc(_c.sea_label)
BADGE_BG: Color = hexc(_c.badge_bg)

_f = _RULES.fonts
# (family, bold) — v3 FONT 표와 같은 키. 굵기 변형 이름은 fontconfig 패밀리 이름 규칙(19a §B)을 따른다.
FONT: dict[str, tuple[str, int]] = {
    "sans": (_f.sans, 0), "sansm": (f"{_f.sans} Medium", 0), "sansb": (f"{_f.sans} SemiBold", 0), "sansbb": (_f.sans, 1),
    "disp": (f"{_f.display}Bold", 0), "dispm": (f"{_f.display}Medium", 0),
    "mono": (f"{_f.mono} SemiBold", 0), "monom": (f"{_f.mono} Medium", 0),
    "serif": (_f.serif, 0), "serifb": (_f.serif, 1),
}
DISPLAY_SPACE: float = _f.display_space_advance

_L = _RULES.layout_480p
SUBTITLE = _L.subtitle
SUBTITLE_WRAP_PX: int = _RULES.script_schema.subtitle_wrap_px_480p  # 자막 줄바꿈 폭 — 린트(script/lint)와 렌더가 공유
PANEL = _L.panel
FADE = _L.fade
CARD = _L.card
ARTICLE = _L.article_card
TITLE_CARD = _L.title_card
END_CARD = _L.end_card
BADGE = _L.badge
DATE_BADGE = _RULES.hud.date_badge
CARD_BG: tuple[float, float, float, float] = tuple(_RULES.colors.card_bg)   # type: ignore[assignment] — 카드 바탕(09 §7)
# v4.2.0 D-0081 작업 4 — 프리미티브 레이아웃 토큰(rules primitives.<id>). 프리미티브 모듈은 이 값과 PrimitiveStyle 만 쓴다(20 §4.2)
PRIMITIVES: dict[str, object] = {k: v for k, v in _RULES.primitives if v is not None}
ANIMATIC = _RULES.animatic   # v4.9.0 D-0108 — 콘티 판(engine/layers/animatic.py 만 읽는다)
ISLAND = _RULES.island   # v5.1.0 D-0123 §1·D-0126 — 아일랜드 공통 규칙
CASCADE = _RULES.cascade     # v5.2.0 — 겹침 카드(v5.3.0 D-0139 채택)
QUOTE = _RULES.quote_center  # v5.4.0 — 인물 발언 인용(정규)
BORDER_GLOW = _RULES.border_glow   # v5.4.0 — 국경선 글로우(정규, 지도 기본)
BACKDROP = _RULES.stage_backdrop   # v5.1.0 D-0121 §B·D-0123 — 사진 배경 무대·backdrop 이벤트 토큰
TIMELINE = _RULES.stage_timeline   # v4.3.0 D-0084 작업 3 — 시간축 무대·시리즈 레이어 토큰
QUOTE_MAX_CHARS: int = _RULES.verification.quote_max_chars   # 인용 상한 — 프리미티브 statement_diff 문구 상한(v4.2.0)
