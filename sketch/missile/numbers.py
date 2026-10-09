"""화면 숫자 포맷터 — SK-H1 의 구현 지점 하나(D-0142 §1).

화면에 나오는 발표·사양 수치는 spec 의 `{키}` 자리표시를 이 모듈이 채운 것뿐이다. 계산한 거리·시간을 문자열로
만들지 않는다(980km 대 발표 1,000km 사고, docs/handoff/22 §2.3). 채운 값은 `shown` 에 남아 provenance `numbers_shown` 이 된다.
자리표시 키: `{기관.값}`(announced), `{track.distance_km}`, `{sensor.range_km}`(그 자산), `{profile.ref_km}`,
3D 라벨용 `{sensor.range_plain}`('약' 없이)·`{sensor.az}`·`{sensor.el}`(개념값), 상수 `{const.earth_radius_km}`.
좌표·지구 반지름으로 계산한 기하값(수평선 패널, D136)은 `computed()` 로만 만들고 `computed_log` 에 따로 남는다(numbers_shown 과 섞지 않는다).
자유 문구(출처 줄·엔딩 카드)에 단위 붙은 숫자가 있으면 그 값도 허용 집합 안이어야 한다(`free_text_violations`).
"""

from __future__ import annotations

import re

from rules import load_rules
from sketch.common.geodesy import EARTH_KM
from sketch.common.numbers import UNIT_NUM, unit_of
from sketch.common.spec import ComputedNumber
from sketch.missile.spec import MissileSpec, Num, Sensor

SECONDS_PER_MINUTE = 60
CLOCK_KEY = "track.flight_sec"
PLACEHOLDER = re.compile(r"\{([a-z0-9_]+\.[a-z0-9_]+)\}")
NU = load_rules().sketch.numbers



def flight_source(spec: MissileSpec) -> tuple[str | None, list[str]]:
    """시계 원천(D-0149 3-3) — track.flight_sec 와 같은 announced `sec` 값의 키. sec 값이 하나도 없을 때만 `min` × 60.
    돌려주는 것: (원천 키 또는 None, 후보 발표값 목록 — 오류 메시지용)."""
    secs = [(f"{k}.{n}", v) for k, ag in spec.announced.items() for n, v in ag.values.items() if v.unit == "sec"]
    mins = [(f"{k}.{n}", v) for k, ag in spec.announced.items() for n, v in ag.values.items() if v.unit == "min"]
    want = float(spec.track.flight_sec)
    if secs:
        cands = [f"{key}={v.v}" for key, v in secs]
        hit = next((key for key, v in secs if float(v.v) == want), None)
    else:
        cands = [f"{key}={v.v}×{SECONDS_PER_MINUTE}" for key, v in mins]
        hit = next((f"{key}×{SECONDS_PER_MINUTE}" for key, v in mins if float(v.v) * SECONDS_PER_MINUTE == want), None)
    return hit, cands


def _num(v: float) -> str:
    return f"{int(v) if float(v).is_integer() else v:,}"


def fmt(n: Num) -> str:
    """Num → 화면 문자열. 소수 자릿수는 spec 에 적은 그대로(999.2 → '999.2', 1000 → '1,000'). 범위(hi)는 '0~60°'."""
    if n.unit not in NU.units:
        raise KeyError(f"단위 {n.unit!r} 가 rules sketch.numbers.units 에 없다")
    u = NU.units[n.unit]
    val = _num(n.v) if n.hi is None else f"{_num(n.v)}{NU.range_sep}{_num(n.hi)}"
    body = f"{u.prefix}{val}{u.suffix}"
    return (NU.approx_prefix + body) if n.approx else body


class Numbers:
    """spec 에서 자리표시 → Num 표를 만들고, 채울 때마다 기록한다."""

    def __init__(self, spec: MissileSpec) -> None:
        self.table: dict[str, Num] = {}
        for key, ag in spec.announced.items():
            for k, n in ag.values.items():
                self.table[f"{key}.{k}"] = n
        self.table["track.distance_km"] = Num(v=spec.track.distance_km, unit="km", approx=spec.track.approx)
        if spec.profile:
            self.table["profile.ref_km"] = spec.profile.reference.km
        self.table["const.earth_radius_km"] = Num(v=EARTH_KM, unit="km")
        self.sensor_ranges = [Num(v=s.range_km, unit="km", approx=s.range_approx)
                              for s in spec.sensors if s.range_km is not None]
        self.shown: dict[str, str] = {}
        self.computed_log: dict[str, ComputedNumber] = {}
        self.clock_source, _ = flight_source(spec)

    def allowed_values(self) -> dict[str, set[float]]:
        """단위 → 허용 값(자유 문구 검사)."""
        out: dict[str, set[float]] = {}
        for n in list(self.table.values()) + self.sensor_ranges:
            out.setdefault(n.unit, set()).add(float(n.v))
        return out

    def fill(self, s: str, sensor: Sensor | None = None) -> str:
        """자리표시를 채운다. 모르는 키 = 오류(조용히 비우지 않는다)."""
        def rep(m: re.Match[str]) -> str:
            key = m.group(1)
            if key.startswith("sensor."):
                n = self._sensor_num(key, sensor, s)
                key = f"{key}:{sensor.name}"   # type: ignore[union-attr]
            elif key in self.table:
                n = self.table[key]
            else:
                raise KeyError(f"{s!r}: 자리표시 {{{key}}} 가 announced·track·profile 에 없다")
            out = fmt(n)
            self.shown[key] = out
            return out
        return PLACEHOLDER.sub(rep, s)

    def placeholders_ok(self, s: str, sensor: Sensor | None = None) -> list[str]:
        """채울 수 없는 자리표시(검사용, 기록하지 않는다)."""
        bad = []
        for m in PLACEHOLDER.finditer(s):
            key = m.group(1)
            if key.startswith("sensor."):
                try:
                    self._sensor_num(key, sensor, s)
                except KeyError:
                    bad.append(key)
            elif key not in self.table:
                bad.append(key)
        return bad

    @staticmethod
    def _sensor_num(key: str, sensor: Sensor | None, s: str) -> Num:
        if sensor is None:
            raise KeyError(f"{s!r}: {key} 자리표시인데 자산 문맥이 없다")
        if key in ("sensor.range_km", "sensor.range_plain"):
            if sensor.range_km is None:
                raise KeyError(f"{s!r}: {key} 자리표시인데 자산 범위가 없다")
            return Num(v=sensor.range_km, unit="km", approx=sensor.range_approx and key == "sensor.range_km")
        if key == "sensor.az" and sensor.az_width_deg is not None:
            return Num(v=sensor.az_width_deg, unit="deg")
        if key == "sensor.el" and sensor.el_deg is not None:
            return Num(v=sensor.el_deg[0], unit="deg", hi=sensor.el_deg[1])
        raise KeyError(f"{s!r}: {key} — 자산 {sensor.name} 에 값이 없다")

    def computed(self, key: str, value: float, unit: str, formula: str, inputs: dict[str, float], approx: bool = False) -> str:
        """기하 계산값(D136) — 정수 반올림 문자열. 발표값이 아니므로 numbers_shown 이 아니라 computed_log 에 남는다."""
        u = NU.units[unit]
        body = f"{u.prefix}{value:,.0f}{u.suffix}"
        out = (NU.approx_prefix + body) if approx else body
        self.computed_log[key] = ComputedNumber(key=key, value=value, shown=out, formula=formula, inputs=inputs)
        return out

    def free_text_violations(self, s: str) -> list[str]:
        """자리표시를 뺀 자유 문구 안 '단위 붙은 숫자' 중 허용 값이 아닌 것."""
        allowed = self.allowed_values()
        bare = PLACEHOLDER.sub("", s)
        bad = []
        for m in UNIT_NUM.finditer(bare):
            val = float(next(g for g in m.groups() if g is not None).replace(",", ""))
            if val not in allowed.get(unit_of(m.group(0)), set()):
                bad.append(m.group(0).strip())
        return bad

    def clock(self, sec: float) -> str:
        """비행 경과 계기 '+mm:ss' — 발표 비행 시간 × 진행 비율. 마지막으로 그린 값을 `track.flight_sec ← 원천` 키로 남긴다(D-0149)."""
        m, s = divmod(int(sec), SECONDS_PER_MINUTE)
        out = f"{NU.clock_prefix}{m:02d}:{s:02d}"
        self.shown[self.clock_key()] = out
        return out

    def clock_key(self) -> str:
        return f"{CLOCK_KEY} ← {self.clock_source}"
