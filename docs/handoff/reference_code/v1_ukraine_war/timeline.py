import json
from script_data import CHAPTERS

DURS = json.load(open('/home/claude/tts/durs.json'))
GAP = 0.55
EXTRA = {'C7_6': 17.0}   # silent timelapse after this sentence
CARD = 3.6
TITLE_CARD = 5.2
END_CARD = 8.0

T, TE = {}, {}          # sentence start / end
SENT = {}               # sid -> dict(text, date, year, chapter)
CARDS = []              # (t0, t1, kind, chapter_key)
CH_START, CH_END = {}, {}
ORDER = []

t = 1.6
for key, num, title, yrs, sents in CHAPTERS:
    if key == 'C1':
        # title card after prologue
        CARDS.append((t, t + TITLE_CARD, 'title', None))
        t += TITLE_CARD + 0.2
    if num is not None:
        CARDS.append((t, t + CARD, 'chapter', key))
        t += CARD + 0.35
    CH_START[key] = t
    for sid, dl, yf, text in sents:
        T[sid] = t
        TE[sid] = t + DURS[sid]
        SENT[sid] = dict(text=text, date=dl, year=yf, chapter=key)
        ORDER.append(sid)
        t = TE[sid] + GAP + EXTRA.get(sid, 0.0)
    CH_END[key] = t
    t += 0.9
CARDS.append((t, t + END_CARD, 'end', None))
TOTAL = t + END_CARD + 0.4
CHAPTER_INFO = {key: (num, title, yrs) for key, num, title, yrs, s in CHAPTERS}


def fmt(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f'{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec - int(sec)) * 1000)):03d}'


def write_srt(path):
    lines = []
    for i, sid in enumerate(ORDER, 1):
        lines += [str(i), f'{fmt(T[sid])} --> {fmt(TE[sid] + 0.15)}', SENT[sid]['text'], '']
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))


if __name__ == '__main__':
    print('total', round(TOTAL, 1), 's  =', round(TOTAL / 60, 2), 'min')
    for c in CARDS:
        print(c)
    for k in CH_START:
        m, s = divmod(int(CH_START[k] - (CARD + 0.35 if k not in ('P', 'E') else 0)), 60)
        print(k, f'{m}:{s:02d}')
