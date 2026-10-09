"""스케치 결정적 검사 틀(D-0140 §4) — hard 위반은 SketchCheckError 로 멈추고(15 P6), warning 은 provenance 에 남긴다.

검사 하나 = `CheckReport` 에 발견을 더하는 함수. 종류별 CLI 는 검사를 다 돌린 뒤 `report.raise_if_hard()` 를 부른다
(`--check` 는 렌더 없이 여기까지, 종료 코드 ≠ 0 = hard 위반). 검사 ID 는 `CHECK_IDS` 밖이면 오류(오타로 새 검사가 생기지 않게).
S0 = 틀 + SK-C1(D-0141). SK-H1~H6·C2·R1·G1~G3 는 S1~S3 에서 이 모듈에 더한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from schemas.rules_models import SketchChecks
from sketch.common.spec import CheckFinding, CheckRecord

CHECK_IDS: dict[str, str] = {   # ID → 등급(D-0140 §4 표)
    "SK-H1": "hard", "SK-H2": "hard", "SK-H3": "hard", "SK-H4": "hard", "SK-H5": "hard", "SK-H6": "hard",
    "SK-C1": "hard", "SK-C2": "warning", "SK-R1": "hard",
    "SK-G1": "hard", "SK-G2": "hard", "SK-G3": "hard",
}


class SketchCheckError(RuntimeError):
    """hard 검사 위반 — 렌더하지 않는다."""

    def __init__(self, findings: list[CheckFinding]) -> None:
        self.findings = findings
        super().__init__("스케치 hard 검사 위반 " + str(len(findings)) + "건:\n"
                         + "\n".join(f"  {f.id} {f.message}" for f in findings))


@dataclass
class CheckReport:
    hard: list[CheckFinding] = field(default_factory=list)
    warnings: list[CheckFinding] = field(default_factory=list)
    ran: list[str] = field(default_factory=list)       # 실제로 돈 검사 ID(P5 — 돌지 않은 검사는 기록하지 않는다)

    def ran_check(self, cid: str) -> None:
        if cid not in CHECK_IDS:
            raise KeyError(f"모르는 검사 ID {cid!r} — CHECK_IDS 에 없다")
        if cid not in self.ran:
            self.ran.append(cid)

    def add(self, cid: str, message: str) -> None:
        self.ran_check(cid)
        f = CheckFinding(id=cid, message=message)
        (self.hard if CHECK_IDS[cid] == "hard" else self.warnings).append(f)

    def record(self) -> CheckRecord:
        return CheckRecord(ran=list(self.ran), hard=list(self.hard), warnings=list(self.warnings))

    def raise_if_hard(self) -> None:
        if self.hard:
            raise SketchCheckError(self.hard)


def check_camera(report: CheckReport, track: np.ndarray, fps: int, th: SketchChecks) -> dict[str, float]:
    """SK-C1 카메라 연속성(D-0141) — 프레임 (x, y, w) 배열(n×3)에서
    |Δ ln w| ≤ max_dlogw_per_frame, |Δ² ln w|·|Δ² x|/w·|Δ² y|/w ≤ max_d2logw_per_frame. 숏 경계 예외 없음.
    1차 = 하드 컷·대점프, 2차 = 속도 급변(멈칫 — 앞 숏 원래 w 에서 이동을 다시 시작한 결함). 실측 최대값을 돌려준다."""
    report.ran_check("SK-C1")
    x, y, w = track[:, 0], track[:, 1], track[:, 2]
    lw = np.log(w)
    d1 = np.abs(np.diff(lw))
    d2 = {"ln w": np.abs(np.diff(lw, 2)),
          "x/w": np.abs(np.diff(x, 2)) / w[1:-1],
          "y/w": np.abs(np.diff(y, 2)) / w[1:-1]}
    worst = {"dlogw": float(d1.max(initial=0))} | {f"d2 {k}": float(v.max(initial=0)) for k, v in d2.items()}
    bad = np.flatnonzero(d1 > th.max_dlogw_per_frame)
    if bad.size:
        i = int(bad[np.argmax(d1[bad])])
        report.add("SK-C1", f"|Δ ln w| {d1[i]:.4f} > {th.max_dlogw_per_frame} — 프레임 {i}→{i + 1}"
                            f"(t={i / fps:.2f}s) 외 {bad.size - 1}곳")
    for k, v in d2.items():
        bad = np.flatnonzero(v > th.max_d2logw_per_frame)
        if bad.size:
            i = int(bad[np.argmax(v[bad])]) + 1
            report.add("SK-C1", f"|Δ² {k}| {v[i - 1]:.4f} > {th.max_d2logw_per_frame} — 프레임 {i}(t={i / fps:.2f}s) "
                                f"외 {bad.size - 1}곳(속도 급변·멈칫)")
    return worst
