"""화면 숫자 포맷터 — SK-H1 의 구현 지점 하나(D-0142 §1).

화면에 나오는 발표·사양 수치는 spec 의 `{키}` 자리표시를 이 모듈이 채운 것뿐이다. 계산한 거리·시간을 문자열로
만들지 않는다(980km 대 발표 1,000km 사고, CONVENTIONS §2). 채운 값은 `shown` 에 남아 provenance `numbers_shown` 이 된다.
자리표시 키: `{기관.값}`(announced), `{track.distance_km}`, `{sensor.range_km}`(그 자산), `{profile.ref_km}`.
자유 문구(출처 줄·엔딩 카드)에 단위 붙은 숫자가 있으면 그 값도 허용 집합 안이어야 한다(`free_text_violations`).
"""

from __future__ import annotations

import re

from rules import load_rules
from sketch.missile.spec import MissileSpec, Num, Sensor

SECONDS_PER_MINUTE = 60
PLACEHOLDER = re.compile(r"\{([a-z0-9_]+\.[a-z0-9_]+)\}")
NU = load_rules().sketch.numbers


def _unit_pattern() -> re.Pattern[str]:
    """단위 붙은 숫자(자유 문구 검사용) — 규칙 단위 표의 접두·접미 그대로."""
    alts = []
    for u in NU.units.values():
        if not u.check:
            continue
        if u.suffix:
            alts.append(r"(?P<n%d>\d[\d,]*(?:\.\d+)?)\s*" % len(alts) + re.escape(u.suffix))
        if u.prefix:
            alts.append(re.escape(u.prefix.strip()) + r"\s*(?P<n%d>\d[\d,]*(?:\.\d+)?)" % len(alts))
    return re.compile("|".join(alts))


UNIT_NUM = _unit_pattern()


def fmt(n: Num) -> str:
    """Num → 화면 문자열. 소수 자릿수는 spec 에 적은 그대로(999.2 → '999.2', 1000 → '1,000')."""
    if n.unit not in NU.units:
        raise KeyError(f"단위 {n.unit!r} 가 rules sketch.numbers.units 에 없다")
    u = NU.units[n.unit]
    v = int(n.v) if float(n.v).is_integer() else n.v
    body = f"{u.prefix}{v:,}{u.suffix}"
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
        self.sensor_ranges = [Num(v=s.range_km, unit="km", approx=s.range_approx)
                              for s in spec.sensors if s.range_km is not None]
        self.shown: dict[str, str] = {}

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
            if key == "sensor.range_km":
                if sensor is None or sensor.range_km is None:
                    raise KeyError(f"{s!r}: sensor.range_km 자리표시인데 자산 범위가 없다")
                n = Num(v=sensor.range_km, unit="km", approx=sensor.range_approx)
                key = f"sensor.range_km:{sensor.name}"
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
            if key == "sensor.range_km":
                if sensor is None or sensor.range_km is None:
                    bad.append(key)
            elif key not in self.table:
                bad.append(key)
        return bad

    def free_text_violations(self, s: str) -> list[str]:
        """자리표시를 뺀 자유 문구 안 '단위 붙은 숫자' 중 허용 값이 아닌 것."""
        allowed = self.allowed_values()
        bare = PLACEHOLDER.sub("", s)
        bad = []
        for m in UNIT_NUM.finditer(bare):
            idx = next(i for i, g in enumerate(m.groups()) if g is not None)
            val = float(m.groups()[idx].replace(",", ""))
            unit = self._unit_of(m.group(0))
            if val not in allowed.get(unit, set()):
                bad.append(m.group(0).strip())
        return bad

    @staticmethod
    def _unit_of(token: str) -> str:
        for name, u in NU.units.items():
            if not u.check:
                continue
            if (u.suffix and token.strip().endswith(u.suffix)) or (u.prefix and token.strip().startswith(u.prefix.strip())):
                return name
        raise KeyError(token)

    def clock(self, sec: float) -> str:
        """비행 경과 계기 '+mm:ss' — 발표 비행 시간 × 진행 비율(계기, 발표 수치 아님)."""
        m, s = divmod(int(sec), SECONDS_PER_MINUTE)
        return f"{NU.clock_prefix}{m:02d}:{s:02d}"
