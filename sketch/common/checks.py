"""스케치 결정적 검사 틀(D-0140 §4) — hard 위반은 SketchCheckError 로 멈추고(15 P6), warning 은 provenance 에 남긴다.

검사 하나 = `CheckReport` 에 발견을 더하는 함수. 종류별 CLI 는 검사를 다 돌린 뒤 `report.raise_if_hard()` 를 부른다
(`--check` 는 렌더 없이 여기까지, 종료 코드 ≠ 0 = hard 위반). 검사 ID 는 `CHECK_IDS` 밖이면 오류(오타로 새 검사가 생기지 않게).
공통 검사: SK-C1(D-0141)·SK-C2·SK-R1·spec 스키마. 종류별 검사(SK-H1~H6·G1~G3)는 sketch/<kind>/checks.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from schemas.rules_models import SketchChecks
from sketch.common.spec import CheckFinding, CheckRecord, MediaItem

RIGHTS_FILE = "RIGHTS.json"
SK_ID = re.compile(r"\b(SK-[A-Z]\d)\b")

CHECK_IDS: dict[str, str] = {   # ID → 등급(D-0140 §4 표)
    "SK-H1": "hard", "SK-H2": "hard", "SK-H3": "hard", "SK-H4": "hard", "SK-H5": "hard", "SK-H6": "hard",
    "SK-C1": "hard", "SK-C2": "warning", "SK-R1": "hard",
    "SK-G1": "hard", "SK-G2": "hard", "SK-G3": "hard",
    "SK-SPEC": "hard",   # spec 스키마 위반 중 SK 번호가 없는 것(형식·참조 오류)
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


def spec_errors(report: CheckReport, err: ValidationError) -> None:
    """spec 스키마 위반 → 발견. 메시지에 SK 번호가 있으면 그 검사(스키마 단계 SK-H2·H3·H4 등), 없으면 SK-SPEC."""
    for e in err.errors():
        msg = f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}"
        m = SK_ID.search(e["msg"])
        report.add(m.group(1) if m and m.group(1) in CHECK_IDS else "SK-SPEC", msg)


# ---------------------------------------------------------------- SK-R1 권리
class RightsEntry(BaseModel):
    """projects/<pid>/media/RIGHTS.json 항목(D-0142 §3 계약). 필수 다섯 + 설명용 선택 필드."""

    model_config = ConfigDict(extra="forbid")
    source_url: str = Field(min_length=1)
    author: str = Field(min_length=1)
    license: str = Field(min_length=1)
    rights_status: str = Field(min_length=1)
    fetched: str = Field(min_length=1)
    download: Optional[str] = None
    note: Optional[str] = None
    based_on: Optional[str] = None
    use: Optional[str] = None


class RightsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=1, le=1)
    files: dict[str, RightsEntry]
    references_not_stored: dict[str, dict] = Field(default_factory=dict)


def check_rights(report: CheckReport, media_dir: Path, items: list[MediaItem], allowed: list[str]) -> dict[str, RightsEntry]:
    """SK-R1 — spec media 마다 RIGHTS.json 항목(source_url·author·license ∈ 허용 목록·rights_status·fetched)과 파일이 있다.
    spec 의 license 가 RIGHTS.json 과 다르면 위반. 항목 표를 돌려준다(provenance data_files)."""
    report.ran_check("SK-R1")
    if not items:
        return {}
    path = media_dir / RIGHTS_FILE
    if not path.is_file():
        report.add("SK-R1", f"{path} 없음 — media {len(items)}개의 권리 기록이 없다")
        return {}
    try:
        rf = RightsFile.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (ValidationError, json.JSONDecodeError) as e:
        report.add("SK-R1", f"{path} 형식 오류: {e}")
        return {}
    for m in items:
        ent = rf.files.get(m.file)
        if ent is None:
            report.add("SK-R1", f"{m.file}: RIGHTS.json 항목 없음")
            continue
        if ent.license not in allowed:
            report.add("SK-R1", f"{m.file}: 라이선스 {ent.license!r} 가 허용 목록(rules sketch.rights.allowed_licenses) 밖")
        if m.license != ent.license:
            report.add("SK-R1", f"{m.file}: spec 라이선스 {m.license!r} ≠ RIGHTS.json {ent.license!r}")
        if not (media_dir / m.file).is_file():
            report.add("SK-R1", f"{m.file}: 파일 없음({media_dir})")
    return rf.files


# ---------------------------------------------------------------- SK-C2 라벨 겹침(warning)
def check_label_overlap(report: CheckReport, frames: list[tuple[float, list]], th: SketchChecks) -> int:
    """SK-C2 — 같은 프레임 새 라벨 예약 상자끼리 겹침(AABB, 겹친 폭·높이 둘 다 > label_overlap_px). 겹친 프레임 수를 돌려준다."""
    report.ran_check("SK-C2")
    hit: list[float] = []
    for t, boxes in frames:
        found = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                ow = min(a[2], b[2]) - max(a[0], b[0])
                oh = min(a[3], b[3]) - max(a[1], b[1])
                if ow > th.label_overlap_px and oh > th.label_overlap_px:
                    found = True
        if found:
            hit.append(t)
    if hit:
        report.add("SK-C2", f"라벨 예약 상자 겹침 {len(hit)}프레임(첫 t={hit[0]:.2f}s, 끝 t={hit[-1]:.2f}s)")
    return len(hit)
