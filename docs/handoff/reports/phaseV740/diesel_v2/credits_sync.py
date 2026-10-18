"""credits.yaml 의 기사 카드·사진·휘장 행을 연출이 실제로 쓴 미디어에 맞춘다(엔딩 크레딧 누락 = check_direction 오류)."""
import re, sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from engine.media_registry import load_media_registry
from engine.refs import emblem_ids
from engine.entities import load_emblem_registry
p = Path(sys.argv[1]); d = yaml.safe_load((p / "direction.yaml").read_text(encoding="utf-8"))
reg = load_media_registry(); er = load_emblem_registry()
txt = repr(d["events"])
arts = sorted({m for m in re.findall(r"'mid': '([a-z0-9_]+_art_\d+)'", txt)})
photos = [m for m in reg if reg[m].kind == "photo" and f"'{m}'" in txt]
emb = sorted({i for e in d["events"] for i in emblem_ids(e) if er.emblems[i].decision == "use"})
cp = p / "credits.yaml"; head = cp.read_text(encoding="utf-8").split("\n", 1)[0]
cr = yaml.safe_load(cp.read_text(encoding="utf-8"))
secs = cr["sections"]
for s in secs:
    if s["title"] == "기사 카드":
        s["items"][0]["rights"] = [f"media.{m}" for m in arts]
secs[:] = [s for s in secs if s["title"] not in ("사진", "휘장")]
i = next(k for k, s in enumerate(secs) if s["title"] == "기사 카드") + 1
if photos:
    secs.insert(i, {"title": "사진", "column": 0, "items": [
        {"main": f"{reg[m].caption} ({reg[m].file_note.replace('자료사진 · ', '')})", "license": f"{reg[m].credit_author} · {reg[m].license}",
         "rights": [f"media.{m}"]} for m in photos]})
if emb:
    j = next(k for k, s in enumerate(secs) if s["title"] == "국기")
    secs.insert(j, {"title": "휘장", "column": 1, "items": [
        {"main": er.emblems[x].title.replace("File:", "").rsplit(".", 1)[0] if er.emblems[x].title else x,
         "license": f"{er.emblems[x].license} · 용도 한정({er.emblems[x].user_exception})" if er.emblems[x].user_exception else er.emblems[x].license,
         "rights": [f"emblems.{x}"]} for x in emb]})
cp.write_text(head + "\n" + yaml.safe_dump(cr, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
print("articles", len(arts), "photos", photos, "emblems", emb)
