"""전쟁사 트랙 판정 — 시대·부호 세트·당대/후대 라벨·증거 층·지명 유래·병력/사상자 출처 (v7.4.0 W2, back_and_forth D-0600 §2·§4).

값은 `rules/video_rules.yaml war_history:` 한 곳(15 P3). 이 모듈은 판정 함수와 프로젝트 파일 계약만 둔다.
엔진 검사(`engine/checks.py`)·원고 린트·스케치(`sketch/`)가 같은 함수를 부른다 — 한 트랙에만 걸린 장치는 미보호(C12-3).

프로젝트 파일(선택, 전쟁사 장르에서 쓴다):
- `projects/<pid>/toponymy.yaml` — 지명 유래(ToponymyFile). 지도 marker 의 `toponymy: <id>` 가 가리킨다
- `projects/<pid>/forces.yaml` — 병력·사상자 수치(schemas.data_models.ForceFiguresFile). 문장 sources 가 `force:<id>` 로 인용한다
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.era_date import EraDate, badge_text, parse_era_date

Era = Literal["ancient", "early_modern", "modern"]
FORCE_PREFIX = "force:"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _rules():  # noqa: ANN202 — schemas.rules_models.WarHistoryRules
    from rules import load_rules  # noqa: PLC0415

    return load_rules().war_history


# ── 시대·부호 세트 ──
def era_of(d: EraDate | str) -> Era:
    """날짜 → 시대(rules war_history.symbol_set_by_year). 기원전은 ancient."""
    d = parse_era_date(d) if isinstance(d, str) else d
    y = d.astronomical_year
    b = _rules().symbol_set_by_year
    if y <= b.ancient_max:
        return "ancient"
    return "early_modern" if y <= b.early_modern_max else "modern"


def video_era(dates: Iterable[str]) -> Era:
    """영상의 시대 = 문장 날짜 중 가장 이른 날짜의 시대(회고 문장이 있어도 한 영상 한 세트)."""
    ds = sorted(parse_era_date(d) for d in dates)
    if not ds:
        raise ValueError("문장 날짜가 없다 — 시대를 정할 수 없다")
    return era_of(ds[0])


def symbol_set_mixed(era: Era, unit_kinds: Iterable[str]) -> list[str]:
    """[symbol-set-mixed] hard — 영상 시대의 부호 세트 밖 부대 부호. 문구 목록(빈 목록 = 통과)."""
    sets = _rules().symbol_sets.by_era()
    own = set(sets[era].units)
    out = []
    for k in unit_kinds:
        if k in own:
            continue
        other = next((e for e, s in sets.items() if k in s.units), None)
        why = f"{other} 세트 부호" if other else "어느 세트에도 없는 부호"
        out.append(f"[symbol-set-mixed] 부호 {k!r} — {why}, 이 영상은 {era} 세트만(rules war_history.symbol_sets, 한 영상 한 세트)")
    return out


# ── 당대/후대 라벨 ──
def period_art_label(created: Optional[EraDate], event: Optional[EraDate]) -> Optional[str]:
    """작품 제작 연대와 사건(문장) 날짜로 캡션 라벨 줄 — 당대 묘사 / 후대의 묘사(제작 연대). 둘 중 하나가 없으면 None(= 라벨 없음, 검사가 잡는다)."""
    if created is None or event is None:
        return None
    pa = _rules().period_art
    ends = [created.astronomical_year] + ([created.end.astronomical_year] if created.end is not None else [])
    gap = max(abs(event.astronomical_year - y) for y in ends)   # 기간이면 먼 쪽 끝 — 기간 전체가 창 안일 때만 당대
    if gap <= pa.contemporary_gap_years:
        return pa.labels.contemporary
    return pa.labels.later.replace("{created}", badge_text(_created_str(created)))


def _created_str(d: EraDate) -> str:
    """EraDate → 원고 꼴 문자열(뱃지 문구용). 대략은 c., 기간은 시작~끝 연도."""
    def one(x: EraDate) -> str:
        y = x.historical_year
        s = f"-{y}" if x.bce else str(y)
        if x.month:
            s += f".{x.month:02d}"
        if x.day:
            s += f".{x.day:02d}"
        return s

    if d.precision == "circa":
        return "c." + (f"-{d.historical_year}" if d.bce else str(d.historical_year))
    if d.precision == "period" and d.end is not None:
        start = EraDate(astronomical_year=d.astronomical_year, precision="year")
        end = EraDate(astronomical_year=d.end.astronomical_year, precision="year")
        return one(start) + "~" + one(end)
    return one(d)


HANGUL_BASE, JONG_N, RIEUL = 0xAC00, 28, 8


def _ro(word: str) -> str:
    """조사 로/으로 — 받침 없음·ㄹ 받침이면 '로', 그 밖 받침이면 '으로'."""
    ch = word[-1] if word else ""
    if not ("가" <= ch <= "힣"):
        return "로"
    jong = (ord(ch) - HANGUL_BASE) % JONG_N
    return "로" if jong in (0, RIEUL) else "으로"


def probable_caption(caption: str, identification: Optional[str], subject: Optional[str] = None) -> str:
    """동정이 불확실(probable·disputed)하면 '<인물>로 추정되는 <캡션>'(rules war_history.period_art.labels.probable_template)."""
    if identification in ("probable", "disputed") and subject:
        return (_rules().period_art.labels.probable_template.replace("{subject}", subject).replace("{ro}", _ro(subject))
                .replace("{caption}", caption))
    return caption


# ── 지명 유래 ──
class ToponymyEntry(_Strict):
    """지명 하나의 유래 — 언어·뜻·출처·확신도(rules war_history.evidence.toponymy_confidence). 출처 없는 유래는 쓰지 않는다."""

    id: str = Field(min_length=1)
    place: str = Field(min_length=1)          # 화면 지명(당시 이름)
    name: str = Field(min_length=1)           # 원어 표기(예: Cannae)
    language: str = Field(min_length=1)       # 예: 라틴어
    meaning: str = Field(min_length=1)        # 한 줄(지도 핀 라벨 아래) — 예: "canna '갈대' 에서 왔다는 설"
    source: str = Field(min_length=1)         # 저자·서지
    source_url: Optional[str] = None
    confidence: str

    @model_validator(mode="after")
    def _conf(self) -> "ToponymyEntry":
        ok = _rules().evidence.toponymy_confidence
        if self.confidence not in ok:
            raise ValueError(f"{self.id}: 확신도 {self.confidence!r} — {ok} 중 하나")
        return self

    def line(self) -> str:
        """지도 핀 라벨 아래 한 줄(확신도 표기 포함 — 통설이 아니면 괄호로)."""
        return self.meaning if self.confidence == _rules().evidence.toponymy_confidence[0] else f"{self.meaning}({self.confidence})"


class ToponymyFile(_Strict):
    schema_version: Literal[1] = 1
    entries: list[ToponymyEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids(self) -> "ToponymyFile":
        ids = [e.id for e in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError(f"toponymy id 중복: {ids}")
        return self

    def by_id(self) -> dict[str, ToponymyEntry]:
        return {e.id: e for e in self.entries}


def load_toponymy(proj: Path) -> Optional[ToponymyFile]:
    p = proj / "toponymy.yaml"
    return ToponymyFile.model_validate(yaml.safe_load(p.read_text(encoding="utf-8"))) if p.exists() else None


# ── 증거 층 ──
def asset_layers(a) -> set[str]:  # noqa: ANN001 — schemas.media_models.MediaAsset
    """미디어 레지스트리 항목 → 증거 층 이름들(period_art·document·site·photo·clip). 기사·컷아웃·인셋은 증거 층이 아니다.
    site_report(현장 서술 출처)가 있으면 site 층도 채운다 — 현장 사진이든, 현장을 그린 후대 작품이든(D-0601 ② A)."""
    base = {"period_art": "period_art", "document": "document", "photo": "photo", "video": "clip"}.get(a.kind)
    out = {base} if base else set()
    if base and getattr(a, "site_report", None):
        out.add("site")
        out.discard("photo")   # 현장 사진은 photo 가 아니라 site 로 센다(옛 판정 그대로)
    return out


def evidence_missing(era: Era, used: set[str]) -> list[str]:
    """[evidence-layer-missing] hard — 시대별 필수 층(rules war_history.evidence.required_layers) 중 영상에 안 쓰인 층."""
    out = []
    for need in _rules().evidence.required_layers[era]:
        alts = need.split("|")
        if not used & set(alts):
            out.append(f"[evidence-layer-missing] {era} 영상의 필수 증거 층 {need!r} 이 쓰이지 않았다 — 쓰인 층 {sorted(used)}"
                       f"(rules war_history.evidence.required_layers, UF-150)")
    return out


def period_art_label_missing(events: list[dict], assets: dict, sentence_date_at) -> list[str]:  # noqa: ANN001
    """[period-art-label-missing] hard — 작품(period_art) 비트마다 당대/후대 라벨을 계산할 수 있어야 한다(제작 연대·문장 날짜).
    sentence_date_at(t) → 그 시각 문장 날짜 문자열."""
    out = []
    for e in events:
        a = assets.get(e.get("mid"))
        if a is None or a.kind != "period_art":
            continue
        raw = sentence_date_at(e["t0"])
        ev = parse_era_date(raw) if raw else None
        if period_art_label(a.created, ev) is None:
            out.append(f"[period-art-label-missing] {e['type']} {e['mid']} t0={e['t0']:.2f} — 당대/후대 라벨을 못 만든다"
                       f"(제작 연대 created={a.created!r}, 문장 날짜={raw!r})")
        if _rules().period_art.art_history_line and not (a.art_history and a.art_history_source):
            out.append(f"[period-art-label-missing] {e['mid']} — 미술사 한 문장(art_history)·그 출처(art_history_source)가 없다"
                       f"(rules war_history.period_art.art_history_line)")
    return out


# ── 병력·사상자 ──
def casualty_unsourced(sentences: Iterable, forces) -> list[str]:  # noqa: ANN001 — script.schema.Sentence|PlanSentence, ForceFiguresFile|None
    """[casualty-unsourced] hard — 병력·사상자 낱말 + 숫자가 든 문장이 force 레코드를 인용하지 않거나, 레코드가 없다."""
    import re  # noqa: PLC0415

    words = _rules().casualty.trigger_words
    known = set(forces.by_id()) if forces is not None else set()
    out = []
    for s in sentences:
        txt = s.text
        if not (re.search(r"\d", txt) and any(w in txt for w in words)):
            continue
        cited = [x[len(FORCE_PREFIX):] for x in s.sources if x.startswith(FORCE_PREFIX)]
        sid = getattr(s, "sid", "") or ""
        if not cited:
            out.append(f"[casualty-unsourced] {sid} {txt[:40]!r} — 병력·사상자 수치는 sources 에 force:<id>(사료 귀속 + 추정 범위 띠)")
        for c in cited:
            if c not in known:
                out.append(f"[casualty-unsourced] {sid} force:{c} — forces.yaml 에 없는 레코드")
    return out


__all__ = ["Era", "ToponymyEntry", "ToponymyFile", "asset_layers", "casualty_unsourced", "era_of", "evidence_missing",
           "load_toponymy", "period_art_label", "period_art_label_missing", "probable_caption", "symbol_set_mixed", "video_era"]


# ── 사진 라이선스 대조(v7.4.0 D-0606 §2, RIGHTS-AP-001) ──
_PD_RECORD = {"public domain", "public domain mark", "pd-art", "united states government work"}


def _norm_record(lic: str) -> str:
    s = lic.strip().lower()
    return "public domain" if s in _PD_RECORD else s


def norm_license_tag(tag: str) -> "str | None":
    """Commons 라이선스 분류 이름 → 비교 꼴(cc by 2.0 · cc by-sa 2.5 · cc0 · gfdl · public domain). 라이선스 분류가 아니면 None."""
    t = tag.strip()
    lo = t.lower()
    if lo.startswith("cc-by-sa-"):
        return "cc by-sa " + lo[9:]
    if lo.startswith(("cc-by-nc", "cc-by-nd")):
        return lo
    if lo.startswith("cc-by-"):
        return "cc by " + lo[6:]
    if lo in ("cc-zero", "cc0"):
        return "cc0"
    if lo.startswith("gfdl"):
        return "gfdl"
    if lo.startswith(("pd-", "pd ", "public domain", "cc-pd-mark")) or lo == "pd":
        return "public domain"
    return None


def license_mismatch(photo_license: str, tags: list[str]) -> list[str]:
    """[license-mismatch] hard — 레코드 사진 라이선스와 Commons 파일 페이지 라이선스 분류(유물 나이 PD 제외)가 맞는가. 문구 목록(빈 = 통과)."""
    R = _rules().rights  # noqa: N806
    work_age = tuple(x.lower() for x in R.work_age_tags)
    bad = tuple(x.lower() for x in R.disallowed_tags)
    photo = [t for t in tags if not t.lower().startswith(work_age) and norm_license_tag(t)]
    errs = []
    disallowed = [t for t in photo if t.lower().startswith(bad)]
    allowed = [t for t in photo if not t.lower().startswith(bad)]
    if disallowed and not allowed:
        errs.append(f"[license-mismatch] 사진 라이선스 분류가 {disallowed} 뿐 — 유물 PD({[t for t in tags if t.lower().startswith(work_age)]})는 사진의 권리가 아니다(화면 불허)")
    norms = {norm_license_tag(t) for t in tags} - {None}
    if _norm_record(photo_license) not in norms:
        errs.append(f"[license-mismatch] 레코드 사진 라이선스 {photo_license!r} 가 Commons 분류 {sorted(norms)} 에 없다 — 손으로 적은 값과 파일 페이지가 다르다")
    return errs


def photo_license_from_tags(tags: list[str]) -> "str | None":
    """Commons 분류 → 레코드 사진 라이선스 꼴(tools/commons_fetch.py get 자동 기록, D-0606 보충 ①).
    유물 나이 PD 분류를 뺀 사진 분류 중 허용 라이선스가 있으면 그것(CC BY x · CC0 · Public domain), 불허뿐이면 그 불허 값(→ 화면 불가),
    사진 분류가 없고 유물 나이 PD 만 있으면 'Public domain'(PD-Art — 2D 복제에만 성립, 입체 유물은 검수에서 사진 연대 확인)."""
    R = _rules().rights  # noqa: N806
    work_age = tuple(x.lower() for x in R.work_age_tags)
    bad = tuple(x.lower() for x in R.disallowed_tags)
    photo = [t for t in tags if not t.lower().startswith(work_age) and norm_license_tag(t)]

    def rec(t: str) -> str:
        n = norm_license_tag(t) or ""
        if n == "public domain":
            return "Public domain"
        if n == "cc0":
            return "CC0"
        return n.upper() if n.startswith("cc") else t

    ok = [t for t in photo if not t.lower().startswith(bad)]
    if ok:
        return rec(ok[0])
    if photo:
        return rec(photo[0])
    if any(t.lower().startswith(work_age) for t in tags):
        return "Public domain"
    return None


THREE_D_WORKS = ("coin", "sculpture", "relief", "pottery")   # 입체 유물 — 사진가 권리가 따로 있다(PD-Art 는 2D 복제에만, RIGHTS-AP-001)


def photo_pd_basis_needed(work_kind: "str | None", tags: "list[str] | None") -> bool:
    """입체 유물 사진인데 Commons 분류가 유물 나이 PD 뿐(사진 라이선스 분류 없음)이면 True — 사진 자체의 PD 근거를 레코드에 적어야 한다(D710 보강)."""
    if work_kind not in THREE_D_WORKS or not tags:
        return False
    work_age = tuple(x.lower() for x in _rules().rights.work_age_tags)
    return not [t for t in tags if not t.lower().startswith(work_age) and norm_license_tag(t)]
