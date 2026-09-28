"""스타일 토큰 — 색·폰트·출력 규격 (v2.1.0, 19 부록 D `hexc, C, FONT`).

색·폰트 이름은 `rules/video_rules.yaml`, 해상도·fps 는 `config.yaml engine.trial` 에서 온다(15 P3).
이 모듈이 엔진 안에서 규칙 값을 푸는 유일한 곳이다(test_single_config 허용 목록).
요소별 기하 수치(글자 크기·여백·두께)는 v3 합격 값 그대로 각 레이어 모듈에 있다. 해상도 스케일(`px()`)은 Phase 10.
"""

from __future__ import annotations

from orchestrator.config import load_config
from rules import load_rules

_RULES = load_rules()
_CFG = load_config()

W_OUT: int = _CFG.engine.trial.width
H_OUT: int = _CFG.engine.trial.height
FPS: int = _CFG.engine.trial.fps
CRF: int = _CFG.engine.crf

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
