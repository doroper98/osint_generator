import asyncio, json, os, subprocess, numpy as np, wave
import edge_tts
from script_data import CHAPTERS, TTS_FIX

VOICE = 'ko-KR-InJoonNeural'
RATE = '-3%'
PITCH = '-2Hz'
OUT = '/home/claude/tts'
os.makedirs(OUT, exist_ok=True)
SR = 44100


def tts_text(t):
    for k, v in TTS_FIX.items():
        t = t.replace(k, v)
    return t


async def one(sid, text, sem):
    mp3 = f'{OUT}/{sid}.mp3'
    if os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
        return
    async with sem:
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(tts_text(text), VOICE, rate=RATE, pitch=PITCH)
                await c.save(mp3)
                if os.path.getsize(mp3) > 1000:
                    return
            except Exception as e:
                print('retry', sid, e)
                await asyncio.sleep(2)


async def main():
    sem = asyncio.Semaphore(5)
    jobs = []
    for key, num, title, yrs, sents in CHAPTERS:
        for sid, dl, yf, text in sents:
            jobs.append(one(sid, text, sem))
    await asyncio.gather(*jobs)

asyncio.run(main())

# decode, trim, measure
durs = {}
for key, num, title, yrs, sents in CHAPTERS:
    for sid, dl, yf, text in sents:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{OUT}/{sid}.mp3', '-f', 's16le', '-ac', '1',
                              '-ar', str(SR), '-'], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        env = np.abs(x)
        thr = 0.012
        idx = np.where(env > thr)[0]
        a = max(0, idx[0] - int(0.03 * SR)); b = min(len(x), idx[-1] + int(0.12 * SR))
        y = x[a:b]
        # short fades
        f = int(0.01 * SR)
        y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        np.save(f'{OUT}/{sid}.npy', y)
        durs[sid] = len(y) / SR
json.dump(durs, open(f'{OUT}/durs.json', 'w'), indent=1)
print('total narration sec', round(sum(durs.values()), 1), 'n', len(durs))
