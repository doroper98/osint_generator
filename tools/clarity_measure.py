# v7.4.0 D-0630 §4 — 프로젝트(사본) out/mix.f32 문장별 명료도 → out/clarity.json. 사용: python tools/clarity_measure.py <proj>
import sys, json; sys.path.insert(0,'/home/user/osint_generator')
from pathlib import Path
from audio.qa import stems, narration_clarity, audio_qa
from engine.project import load_plan
proj = Path(sys.argv[1]); S = load_plan(Path("/home/user/osint_generator/projects/cannae_216bc")).sentences
m, vo, mask = stems(proj / "out" / "mix.f32", S); c = narration_clarity(m, vo, S)
q = audio_qa(proj / "out", S, genre="war_history")
json.dump(c, open(proj / "out" / "clarity.json", "w"))
bad = sorted(((k, v) for k, v in c.items() if v < 15.6), key=lambda kv: kv[1])
print(json.dumps({"min": min(c.values()), "n_bad": len(bad), "bad": bad[:14], "music_db": q.music_under_narration_db, "issues": q.issues()}, ensure_ascii=False))
