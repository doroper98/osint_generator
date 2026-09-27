"""plan.py — report bundle -> sentence-level plan + narration audio + timeline.

Inherited from doroper98/osint_generator (collage@v1.2.1, hyperframes/scripts/bundle_to_video.py):
  tts_of (Korean TTS normalisation), em_segments_line (emphasis runs), sentence_grounded + build_corpus
  (grounding QA), norm_gantt (chart normaliser). Voice backend mirrors workers/tts_backends.py:
  ElevenLabs is used when ELEVENLABS_API_KEY/ELEVENLABS_VOICE_ID are set, otherwise edge-tts.
"""
import sys, os, json, re, asyncio, subprocess, hashlib
import numpy as np

sys.path.insert(0, '/home/claude/og/hyperframes/scripts'); sys.path.insert(0, '/home/claude/og')
import bundle_to_video as B  # noqa: E402

V = '/home/claude/v2'
b = json.load(open(f'{V}/data/bundle.json'))
R = b['report']
CHARTS = {c['chart_id']: c for c in b['charts']}
SR = 44100
GAP, SEC_GAP, TITLE_CARD, END_CARD, LEAD = 0.45, 0.9, 5.4, 10.0, 1.2

# entity aliases for mention detection (label from bundle nodes + short forms)
NODES = {n['id']: n for n in CHARTS['ch-1']['data']['nodes']}
ALIAS = {}
for nid, n in NODES.items():
    lab = n['label']
    al = {lab}
    if ' ' in lab:
        al.add(lab.split(' ')[-1])
    ALIAS[nid] = sorted(al, key=len, reverse=True)
ALIAS['trump'] += ['트럼프 대통령']; ALIAS['putin'] += ['푸틴']; ALIAS['zelensky'] += ['젤렌스키']
ALIAS['cia'] += ['CIA']; ALIAS['iran'] += ['이란']


def fix_tts(t):
    # repo tts_of reads '18개월' with native numerals (열여덟 개월) — 개월 takes Sino-Korean numerals
    t = re.sub(r'열여덟 개월', '십팔 개월', t)
    return t


def mentions(text):
    out = []
    for nid, al in ALIAS.items():
        for a in al:
            i = text.find(a)
            if i >= 0:
                out.append((nid, i / max(1, len(text)))); break
    return sorted(out, key=lambda x: x[1])


def build_sentences():
    S = []
    corpus = B.build_corpus(b)
    v = R['video']
    for i, t in enumerate(v['intro_narration']):
        tt = (v.get('intro_narration_tts') or [None] * 9)[i] if v.get('intro_narration_tts') else None
        S.append(dict(sid=f'intro_{i}', sec='intro', idx=i, text=t, tts=tt or fix_tts(B.tts_of(t)), emphasis=[]))
    for s in b['sections']:
        vv = s['video']
        for i, t in enumerate(vv['narration']):
            nt = vv.get('narration_tts') or []
            tt = nt[i] if i < len(nt) and nt[i] else fix_tts(B.tts_of(t))
            S.append(dict(sid=f"{s['section_id']}_{i}", sec=s['section_id'], idx=i, text=t, tts=tt, emphasis=vv.get('emphasis', [])))
    for i, t in enumerate(v['outro_narration']):
        S.append(dict(sid=f'outro_{i}', sec='outro', idx=i, text=t, tts=fix_tts(B.tts_of(t)), emphasis=[]))
    for x in S:
        x['segments'] = B.em_segments_line(x['text'], x['emphasis']) if x['emphasis'] else [[x['text'], 0]]
        x['grounded'] = bool(B.sentence_grounded(x['text'], corpus))
        x['mentions'] = mentions(x['text'])
    return S


# ------------------------------------------------------------------ voice
async def edge_one(text, path):
    import edge_tts
    for a in range(4):
        try:
            await edge_tts.Communicate(text, 'ko-KR-InJoonNeural', rate='-2%', pitch='-2Hz').save(path)
            if os.path.getsize(path) > 1000:
                return
        except Exception as e:
            print('retry', e); await asyncio.sleep(2)


def eleven_one(text, path, prev_text, next_text):
    import requests
    key, vid = os.environ['ELEVENLABS_API_KEY'], os.environ['ELEVENLABS_VOICE_ID']
    r = requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps',
                      headers={'xi-api-key': key}, timeout=120,
                      json=dict(text=text, model_id=os.environ.get('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2'),
                                previous_text=prev_text, next_text=next_text,
                                voice_settings=dict(stability=0.65, similarity_boost=0.8, style=0.1)))
    r.raise_for_status(); d = r.json()
    import base64
    open(path, 'wb').write(base64.b64decode(d['audio_base64']))
    json.dump(d.get('alignment'), open(path + '.align.json', 'w'))


def synth(S):
    use_eleven = bool(os.environ.get('ELEVENLABS_API_KEY') and os.environ.get('ELEVENLABS_VOICE_ID'))
    jobs = []
    for k, x in enumerate(S):
        h = hashlib.sha1((x['tts'] + ('el' if use_eleven else 'edge')).encode()).hexdigest()[:10]
        x['mp3'] = f"{V}/tts/{x['sid']}_{h}.mp3"
        if os.path.exists(x['mp3']) and os.path.getsize(x['mp3']) > 1000:
            continue
        if use_eleven:
            eleven_one(x['tts'], x['mp3'], S[k - 1]['tts'] if k else None, S[k + 1]['tts'] if k + 1 < len(S) else None)
        else:
            jobs.append((x['tts'], x['mp3']))

    async def run():
        sem = asyncio.Semaphore(5)

        async def one(t, p):
            async with sem:
                await edge_one(t, p)
        await asyncio.gather(*[one(t, p) for t, p in jobs])
    if jobs:
        asyncio.run(run())
    for x in S:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', x['mp3'], '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        idx = np.where(np.abs(a) > 0.012)[0]
        a = a[max(0, idx[0] - int(0.03 * SR)): min(len(a), idx[-1] + int(0.12 * SR))]
        f = int(0.01 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        x['npy'] = x['mp3'][:-4] + '.npy'; np.save(x['npy'], a)
        x['dur'] = len(a) / SR
    return 'elevenlabs' if use_eleven else 'edge-tts ko-KR-InJoonNeural'


def timeline(S):
    t = LEAD
    cards = []
    prev_sec = None
    sec_start = {}
    for x in S:
        if x['sec'] != prev_sec:
            if prev_sec == 'intro':
                cards.append(dict(kind='title', t0=t, t1=t + TITLE_CARD)); t += TITLE_CARD + 0.3
            elif prev_sec is not None:
                t += SEC_GAP
            sec_start[x['sec']] = t
            prev_sec = x['sec']
        x['t0'] = t; x['t1'] = t + x['dur']
        t = x['t1'] + GAP
    t += 0.8
    cards.append(dict(kind='end', t0=t, t1=t + END_CARD))
    total = t + END_CARD + 0.5
    return cards, sec_start, total


if __name__ == '__main__':
    S = build_sentences()
    voice = synth(S)
    cards, sec_start, total = timeline(S)
    plan = dict(report=dict(headline=R['headline'], deck=R['deck'], date=b['generated_at'][:10], id=R['report_id']),
                voice=voice, sentences=S, cards=cards, sec_start=sec_start, total=total,
                sections={s['section_id']: dict(heading=s['heading'], highlights=s['video'].get('highlights', []),
                                                chart_refs=s['chart_refs']) for s in b['sections']},
                charts=CHARTS, gantt=B.norm_gantt(CHARTS['ch-3'], b['generated_at'][:10]), map=b['map'])
    json.dump(plan, open(f'{V}/plan.json', 'w'), ensure_ascii=False, indent=1)
    ng = [x['sid'] for x in S if not x['grounded']]
    print(f"sentences {len(S)}  voice={voice}  total {total:.1f}s ({total / 60:.2f} min)  ungrounded={ng}")
    for x in S[:3] + S[26:29]:
        print(x['sid'], round(x['t0'], 1), round(x['dur'], 2), x['tts'][:40], x['mentions'])
