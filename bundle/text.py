"""bundle.text — agents_reviewer 번들 텍스트 순수 함수 (v2.0.0 이관).

`hyperframes/scripts/bundle_to_video.py`(archive/hyperframes-briefing 브랜치)에서 HTML·파일 I/O
없는 텍스트 함수만 **본문 무변경**으로 옮겼다 (docs/handoff/19 §3.2·§5.3).
버그 수정(개월·소수 표기)은 Phase 4, 번들→원고 어댑터는 Phase 9.
"""

from __future__ import annotations

import json
import re

from orchestrator.tts_pronounce import DEFAULT_DICT_PATH, apply_pronunciation, load_dict, num_to_sino_kr

_PRONOUNCE = load_dict(DEFAULT_DICT_PATH)

def char_units(ch: str) -> float:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """SceneKit.estTextWidth 와 같은 결정론 폭 추정 (em 단위)."""
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3 or 0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F:
        return 1.0
    if ch == "·":
        return 0.42
    if ch.isdigit():
        return 0.62
    if ch == " ":
        return 0.3
    if ch.isupper():
        return 0.74
    if ch.islower():
        return 0.56
    return 0.5


def est_units(text: str) -> float:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    return sum(char_units(c) for c in text)


def clip(text: str, n: int) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    text = text.strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def sentences(text: str) -> list[str]:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    # 구두점(. ! ?) 뒤에서만 분할 — 바 "다 "(보다/한다 중간) 오분할 방지
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def wrap_units(text: str, max_units: float) -> list[str]:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """공백 단위 greedy wrap (keep-all)."""
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if cur and est_units(cand) > max_units:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def date_kr(iso: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if not m:
        return iso
    return f"{int(m.group(2))}월 {int(m.group(3))}일"


NUM_TOKEN = re.compile(r"\d[\d,\.]*")


_NATIVE = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열",
           "열한", "열두", "열세", "열네", "열다섯", "열여섯", "열일곱", "열여덟", "열아홉", "스무"]


def native_count(n: int) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """수사+단위(개/곳/가지)용 고유어 — '7개'를 '칠 개'가 아니라 '일곱 개'로."""
    return _NATIVE[n] if 0 < n <= 20 else None  # 초과는 한자어로 폴백


def josa(word: str, with_jong: str, without_jong: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """받침 유무로 조사 선택 (이/가, 은/는, 을/를)."""
    if not word:
        return without_jong
    o = ord(word[-1])
    if 0xAC00 <= o <= 0xD7A3 and (o - 0xAC00) % 28:
        return with_jong
    return without_jong


# 월 발음 — 6월(유월)·10월(시월) 불규칙 포함. "육 월 오 일" 끊어 읽기 방지 (TTS-AP-054 계열)
_MONTH_KR = {1: "일월", 2: "이월", 3: "삼월", 4: "사월", 5: "오월", 6: "유월",
             7: "칠월", 8: "팔월", 9: "구월", 10: "시월", 11: "십일월", 12: "십이월"}


# 표기 정규화 — 번들 transliteration 을 영상 표기로 (검수 반영)
_DISPLAY_NORMALIZE = {"장보고-엔": "장보고 N", "장보고 엔": "장보고 N",
                      "오커스(AUKUS)": "AUKUS", "오커스 (AUKUS)": "AUKUS", "오커스": "AUKUS"}


def normalize_display(text: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    for a, b in _DISPLAY_NORMALIZE.items():
        text = text.replace(a, b)
    return text


def iso_to_kr(s: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """ISO 날짜(YYYY-MM-DD) → 'M월 D일' 표시. 그 외는 원본."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", s.strip())
    return f"{int(m.group(2))}월 {int(m.group(3))}일" if m else s


def _date_kr_tts(m: re.Match) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    mon = _MONTH_KR.get(int(m.group(1)), m.group(1) + "월")
    day = num_to_sino_kr(int(m.group(2)))
    return f"{mon} {day}일"


# 고유어 수사를 쓰는 단위 (가지/개/곳/척/명/번 …) — "5가지" → "다섯 가지"
_NATIVE_UNITS = "가지|개|곳|척|명|번|살|발|건|차례|대"


def _sino_months(m: re.Match) -> str:
    """'18개월' → '십팔 개월'. 개월은 한자어 수사(TTS-AP-064) — 고유어 '개' 규칙보다 먼저."""
    return f"{num_to_sino_kr(int(m.group(1)))} 개월"


def _native_unit(m: re.Match) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    n = int(m.group(1))
    nat = native_count(n)
    return f"{nat} {m.group(2)}" if nat else f"{num_to_sino_kr(n)} {m.group(2)}"


def _iso_date_tts(m: re.Match) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    mon = _MONTH_KR.get(int(m.group(2)), m.group(2) + "월")
    return f"{mon} {num_to_sino_kr(int(m.group(3)))}일"


def _slash_date_tts(m: re.Match) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """'7/13' → '칠월 십삼일'. 월 1~12·일 1~31 아니면 원본 유지 (비율/분수 오변환 방지)."""
    mo, dy = int(m.group(1)), int(m.group(2))
    if not (1 <= mo <= 12 and 1 <= dy <= 31):
        return m.group(0)
    return f"{_MONTH_KR[mo]} {num_to_sino_kr(dy)}일"


def _decimal_tts(m: re.Match) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """'168.49' → '백육십팔쩜사구' (TTS-AP-059). 소수점은 '쩜', 소수부는 자릿수별 낭독.
    붙여 써서 반박자 쉼·연음 끊김 방지."""
    intp = num_to_sino_kr(int(m.group(1)))
    frac = "".join(num_to_sino_kr(int(d)) for d in m.group(2))
    return f"{intp}쩜{frac}"


def tts_of(text: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """템플릿/계약 문장 → 발음 표기: 부호/날짜/소수/수사 정리 후 사전+숫자 한글화.

    계약 narration_tts(producer 제공)에도 동일 적용 — 소수·슬래시날짜·말끝 '…' 을
    producer 가 안 풀어 보내도 소비측에서 마지막으로 교정 (멱등)."""
    s = normalize_display(text)
    # 구두점 — em대시/가운뎃점/화살괄호는 음성에서 어색 (검수 반영)
    s = s.replace("—", ", ").replace(" – ", ", ").replace(" - ", ", ")
    s = s.replace("·", ", ").replace("<", "").replace(">", "")
    s = s.replace("+", " 플러스 ").replace("−", " 마이너스 ")
    # 소수 (168.49 → 백육십팔쩜사구) — 날짜/단위 변환보다 먼저 (점 소실 방지)
    s = re.sub(r"(?<!\d)(\d+)\.(\d+)(?!\d)", _decimal_tts, s)
    # producer 가 이미 "십삼 점 일" 처럼 풀어 보낸 소수 — 한글 숫자 사이 " 점 "→"쩜"
    # (TTS-AP-059). 숫자가 남아있지 않아 위 규칙이 못 잡는 계약 tts 커버.
    _SINO = "영일이삼사오육칠팔구십백천만"
    s = re.sub(rf"([{_SINO}])\s*점\s*([{_SINO}])", r"\1쩜\2", s)
    # ISO 날짜 YYYY-MM-DD → "M월 D일" (연도 생략 — 근접 시점)
    s = re.sub(r"(\d{4})-(\d{2})-(\d{2})", _iso_date_tts, s)
    # 슬래시 날짜 M/D → "M월 D일" ('분기' 앞은 제외 = 1/4분기 오변환 방지)
    s = re.sub(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)(?!\s*분기)", _slash_date_tts, s)
    s = re.sub(r"(\d{1,2})월\s*(\d{1,2})일", _date_kr_tts, s)
    s = re.sub(r"(?<![\d가-힣])(\d{1,2})월", lambda m: _MONTH_KR.get(int(m.group(1)), m.group(0)), s)
    # 개월은 한자어 수사 (TTS-AP-064) — '개' 가 고유어 단위라 먼저 처리하지 않으면 '열여덟 개월'
    s = re.sub(r"(\d+)\s*개월", _sino_months, s)
    # 고유어 수사 (사전/한자어 변환 전에)
    s = re.sub(rf"(\d{{1,2}})\s*({_NATIVE_UNITS})", _native_unit, s)
    # 말끝 정리 — 절단 표식 '…'/'...' 은 음성에서 말이 끊긴 것처럼 들리므로 제거 (TTS-AP-060)
    s = s.replace("…", " ").replace("...", " ")
    s = re.sub(r"[\s,]*(?:플러스|및|와|과)\s*$", "", s)  # 절단으로 남은 접속 꼬리 제거
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+", " ", apply_pronunciation(s, _PRONOUNCE)).strip()


# 받침 ㄴ 인 한글 음절 전부 — '-ㄴ다' 현재형 종결 판별용
_N_JONG = "".join(chr(0xAC00 + i * 28 + 4) for i in range(11172 // 28))


def _n_da_polite(m: re.Match) -> str:
    """'낮춘다' → '낮춥니다.' — 받침 ㄴ 을 ㅂ 으로 바꾸고 '니다.'."""
    return chr(ord(m.group(1)) - 4 + 17) + "니다."


# 논설체 → 다큐 경어체 (versus 등 원문 노출 cue/카드 용 — 반말 사고 해소)
# 구체 규칙이 먼저, 일반 규칙(마지막 폴백)이 나중 — 순서 뒤집히면 "본다"→"본습니다"
# 처럼 일반 규칙이 구체 규칙을 가려버린다 (TTS-AP-061).
_POLITE_TAIL = [
    (re.compile(r"이다\.?$"), "입니다."),
    (re.compile(r"한다\.?$"), "합니다."), (re.compile(r"된다\.?$"), "됩니다."),
    (re.compile(r"본다\.?$"), "봅니다."), (re.compile(r"있다\.?$"), "있습니다."),
    (re.compile(r"없다\.?$"), "없습니다."), (re.compile(r"크다\.?$"), "큽니다."),
    (re.compile(r"높다\.?$"), "높습니다."), (re.compile(r"낮다\.?$"), "낮습니다."),
    (re.compile(r"같다\.?$"), "같습니다."), (re.compile(r"든다\.?$"), "듭니다."),
    (re.compile(r"하다\.?$"), "합니다."),  # 우세하다→우세합니다 등 '하다' 류
    (re.compile(rf"([{_N_JONG}])다\.?$"), _n_da_polite),  # '-ㄴ다' 현재형: 낮춘다→낮춥니다 (TTS-AP-061 후속)
    (re.compile(r"([가-힣])다\.?$"), r"\1습니다."),  # 일반 폴백 — 반드시 마지막
]


def to_polite(text: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """문장 종결을 다큐 경어체로. 끝맺지 않은(절단된) 문장은 그대로."""
    s = text.strip()
    for rx, rep in _POLITE_TAIL:
        if rx.search(s):
            return rx.sub(rep, s)
    return s


def build_corpus(b: dict) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """검증용 말뭉치 — 번들 전체를 콤마/공백 제거 직렬화."""
    return re.sub(r"[,\s]", "", json.dumps(b, ensure_ascii=False))


def sentence_grounded(sent: str, corpus: str) -> bool:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """계약 G4: 문장 속 모든 수치 토큰이 번들에 실재해야 한다."""
    for tok in NUM_TOKEN.findall(sent):
        norm = tok.replace(",", "").rstrip(".")
        if norm and norm not in corpus:
            return False
    return True


def em_segments_line(text: str, emphasis: list[str]) -> list:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """emphasis 부분 문자열을 em=1 세그먼트로 분할한 한 줄."""
    spans = []
    for term in emphasis or []:
        start = 0
        while term:
            i = text.find(term, start)
            if i < 0:
                break
            spans.append((i, i + len(term)))
            start = i + len(term)
    spans.sort()
    # 겹침 제거
    merged = []
    for a, bnd in spans:
        if merged and a < merged[-1][1]:
            continue
        merged.append((a, bnd))
    segs = []
    pos = 0
    for a, bnd in merged:
        if a > pos:
            segs.append([text[pos:a], 0])
        segs.append([text[a:bnd], 1])
        pos = bnd
    if pos < len(text):
        segs.append([text[pos:], 0])
    return segs or [[text, 0]]


# 번들 narration 어구 안전망 — A 미반영분 교정 (검수: "물러설 한계선" 등 비문)
_PHRASING_FIXES = [
    (re.compile(r"물러설 (한계선|선|지점|영역|레드라인)"), r"물러설 수 없는 \1"),
    (re.compile(r"양보할 (한계선|선|지점)"), r"양보할 수 없는 \1"),
]


def fix_phrasing(text: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    for rx, rep in _PHRASING_FIXES:
        text = rx.sub(rep, text)
    return text


EM_NUM = re.compile(r"\d[\d,\.]*\s?(?:조원|만원|억원|원|%|배|달러)")


def quote_segments(text: str) -> list:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """숫자+단위를 강조(em) 세그먼트로 분할."""
    segs = []
    pos = 0
    for m in EM_NUM.finditer(text):
        if m.start() > pos:
            segs.append([text[pos:m.start()], 0])
        segs.append([m.group(0), 1])
        pos = m.end()
    if pos < len(text):
        segs.append([text[pos:], 0])
    return [segs or [[text, 0]]]

