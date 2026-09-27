"""plan3 — script for '호르무즈와 한국' (free structure, no fixed acts).
Subtitle text keeps digits; TTS text is written in Hangul numerals without inner spaces (TTS-AP-058),
with no symbols (%, ~, /, :, ->, parentheses: TTS-AP-021..025). A lint enforces both, plus the banned
'AI slop' phrase list supplied by the user.
"""
import json, os, re, sys, asyncio, hashlib, subprocess
import numpy as np

V = '/home/claude/v3'; SR = 44100
GAP, SCENE_GAP, TITLE_CARD, END_CARD, LEAD = 0.5, 1.0, 5.6, 11.0, 1.2

# (scene, date_badge, subtitle, tts or None(=same), emphasis)
SCRIPT = [
    ('open', '2026.09.18', '9월 18일, 이재명 대통령이 기자회견을 열었습니다.', '구월 십팔일, 이재명 대통령이 기자회견을 열었습니다.', []),
    ('open', '2026.09.18', '전쟁에 개입하는 파병은 하지 않겠다는 발표였습니다.', None, ['파병은 하지 않겠다']),
    ('open', '2026.09.18', '한국 선박과 국민을 보호하는 최소한의 활동만 이어가겠다고 했습니다.', None, ['최소한의 활동']),
    ('open', '2026.09.18', '미국이 동맹국들에 해협 방어를 요구한 지 여섯 달 만에 나온 결론입니다.', None, []),

    ('route', '2025', '호르무즈 해협은 페르시아만에서 먼바다로 나가는 유일한 바닷길입니다.', None, ['유일한 바닷길']),
    ('route', '2025', '지난해 한국이 수입한 원유의 61%가 이 해협을 지났습니다.', '지난해 한국이 수입한 원유의 육십일 퍼센트가 이 해협을 지났습니다.', ['61%']),
    ('route', '2025', '플라스틱의 원료인 나프타도 54%가 같은 길로 들어왔습니다.', '플라스틱의 원료인 나프타도 오십사 퍼센트가 같은 길로 들어왔습니다.', ['54%']),
    ('route', '2025', '유조선은 해협을 나와 인도양을 건너고, 믈라카 해협을 거쳐 한국 남해안에 닿습니다.', None, []),

    ('war', '2026.02.28', '올해 2월 28일, 미국과 이스라엘이 이란을 공습했습니다.', '올해 이월 이십팔일, 미국과 이스라엘이 이란을 공습했습니다.', []),
    ('war', '2026.02.28', '이 공격으로 이란의 최고지도자 알리 하메네이가 숨졌습니다.', None, []),
    ('war', '2026.03.02', '이란은 곧바로 호르무즈 해협을 닫았습니다.', None, ['해협을 닫았습니다']),
    ('war', '2026.03', '이란이 허가한 배만 지나갈 수 있었고, 대부분 중국과 인도로 가는 유조선이었습니다.', None, []),

    ('ask', '2026.03.15', '3월 15일, 트럼프 대통령은 이 해협으로 석유를 받는 나라들이 직접 지키라고 요구했습니다.', '삼월 십오일, 트럼프 대통령은 이 해협으로 석유를 받는 나라들이 직접 지키라고 요구했습니다.', []),
    ('ask', '2026.03.16', '다음 날 독일, 영국, 일본, 호주, 그리고 한국이 이 요구를 거절했습니다.', None, ['거절']),
    ('ask', '2026.03.16', '독일 국방장관은 우리가 시작한 전쟁이 아니라고 말했습니다.', None, []),
    ('ask', '2026.03.17', '트럼프 대통령은 동맹들의 결정을 매우 어리석은 실수라고 비판했습니다.', None, []),
    ('ask', '2026.03.21', '3월 21일, 한국은 영국, 프랑스, 일본 등 일곱 나라의 공동성명에 이름을 올렸습니다.', '삼월 이십일일, 한국은 영국, 프랑스, 일본 등 일곱 나라의 공동성명에 이름을 올렸습니다.', []),
    ('ask', '2026.03.21', '이란의 공격을 규탄하고, 항행의 자유를 지키는 노력에 함께한다는 내용이었습니다.', None, ['항행의 자유']),

    ('timeline', '2026.04', '그 뒤 여섯 달 동안 전쟁과 협상이 번갈아 이어졌습니다.', None, []),
    ('timeline', '2026.04.07', '4월 7일, 해협을 열기 위한 무력 사용 결의안은 러시아와 중국의 거부권에 막혔습니다.', '사월 칠일, 해협을 열기 위한 무력 사용 결의안은 러시아와 중국의 거부권에 막혔습니다.', []),
    ('timeline', '2026.04.13', '4월 13일, 미국은 이란 항구를 드나드는 배를 막는 해상 봉쇄에 들어갔습니다.', '사월 십삼일, 미국은 이란 항구를 드나드는 배를 막는 해상 봉쇄에 들어갔습니다.', []),
    ('timeline', '2026.06.17', '6월 17일에는 미국과 이란이 전쟁을 끝내는 양해각서에 서명했습니다.', '유월 십칠일에는 미국과 이란이 전쟁을 끝내는 양해각서에 서명했습니다.', []),
    ('timeline', '2026.07.08', '하지만 7월 8일, 해협에서 상선들이 공격받고 미국이 다시 이란을 공습하면서 휴전은 무너졌습니다.', '하지만 칠월 팔일, 해협에서 상선들이 공격받고 미국이 다시 이란을 공습하면서 휴전은 무너졌습니다.', ['휴전은 무너졌습니다']),
    ('timeline', '2026.08.25', '8월 25일, 미국은 해협 통항로의 기뢰를 모두 제거했다고 밝혔습니다.', '팔월 이십오일, 미국은 해협 통항로의 기뢰를 모두 제거했다고 밝혔습니다.', []),

    ('cost', '2026.06.11', '국제해사기구는 6월 11일까지 선박 공격 46건과 선원 14명의 죽음을 확인했습니다.', '국제해사기구는 유월 십일일까지 선박 공격 사십육 건과 선원 열네 명의 죽음을 확인했습니다.', ['46건', '14명']),
    ('cost', '2026.06.11', '배 천여 척과 선원 2만 명이 걸프 안쪽에 발이 묶였습니다.', '배 천여 척과 선원 이만 명이 걸프 안쪽에 발이 묶였습니다.', []),

    ('review', '2026.09.03', '9월 초, 국내 방송사들은 정부가 연내 파병을 준비하고 있다고 보도했습니다.', '구월 초, 국내 방송사들은 정부가 연내 파병을 준비하고 있다고 보도했습니다.', []),
    ('review', '2026.09.03', '해상초계기와 군수지원함 같은 선택지가 거론됐습니다.', None, []),
    ('review', '2026.09.04', '대통령실은 군사적 방안을 포함해 검토하고 있지만, 결정된 것은 없다고 밝혔습니다.', None, []),
    ('review', '2026.09.04', '실제로 보낸다면 2009년 청해부대 이후 한반도 밖으로 나가는 첫 해상 파견이 될 수 있었습니다.', '실제로 보낸다면 이천구 년 청해부대 이후 한반도 밖으로 나가는 첫 해상 파견이 될 수 있었습니다.', []),

    ('past', '2004', '한국이 이런 결정을 내려야 했던 것은 처음이 아닙니다.', None, []),
    ('past', '2004', '2004년 노무현 정부는 이라크 아르빌에 자이툰 부대를 보냈습니다.', '이천사 년 노무현 정부는 이라크 아르빌에 자이툰 부대를 보냈습니다.', []),
    ('past', '2004', '북핵 6자회담에서 미국의 지지를 지키려는 판단이었지만, 국내 여론은 싸늘했습니다.', '북핵 육자회담에서 미국의 지지를 지키려는 판단이었지만, 국내 여론은 싸늘했습니다.', []),
    ('past', '2020.01', '2020년에는 청해부대의 작전 구역을 호르무즈까지 넓히되, 지휘권은 한국군이 갖는 방식을 택했습니다.', '이천이십 년에는 청해부대의 작전 구역을 호르무즈까지 넓히되, 지휘권은 한국군이 갖는 방식을 택했습니다.', ['지휘권은 한국군']),

    ('debate', '2026.09.07', '9월 7일, 정부는 전투가 격해지고 반대 여론이 커지자 계획을 다시 조정하기 시작했습니다.', '구월 칠일, 정부는 전투가 격해지고 반대 여론이 커지자 계획을 다시 조정하기 시작했습니다.', []),
    ('debate', '2026.09.08', '다음 날 서울 미국대사관 근처에서는 대학생들이 파병 반대 집회를 열었습니다.', None, []),
    ('debate', '2026.09.08', '파병을 지지하는 쪽은 호르무즈가 곧 한국의 경제 안보라고 말합니다.', None, ['경제 안보']),
    ('debate', '2026.09.10', '반대하는 쪽은 비전투 부대라도 미사일과 드론이 오가는 곳에서는 표적이 될 수 있다고 봅니다.', None, ['표적']),
    ('debate', '2026.09.10', '미국의 방공 미사일 재고가 줄고 있다는 점도 반대 논리의 근거가 됐습니다.', None, []),

    ('decision', '2026.09.18', '그리고 9월 18일, 이재명 대통령은 전쟁에 들어가는 파병은 없다고 분명히 했습니다.', '그리고 구월 십팔일, 이재명 대통령은 전쟁에 들어가는 파병은 없다고 분명히 했습니다.', ['파병은 없다']),
    ('decision', '2026.09.18', '대신 분쟁의 주변부에서 한국군이 맡을 역할은 열어 두었습니다.', None, []),

    ('now', '2026.09', '미군은 호위 작전으로 원유 10억 배럴을 해협 밖으로 내보냈다고 밝혔습니다.', '미군은 호위 작전으로 원유 십억 배럴을 해협 밖으로 내보냈다고 밝혔습니다.', ['10억 배럴']),
    ('now', '2026.09', '전쟁은 아직 끝나지 않았고, 해협의 통행도 정상으로 돌아오지 않았습니다.', None, []),
    ('now', '2026.09', '지난해 기준 원유 수입의 61%가 이 해협에 기대고 있다는 사실도 그대로입니다.', '지난해 기준 원유 수입의 육십일 퍼센트가 이 해협에 기대고 있다는 사실도 그대로입니다.', []),
    ('now', '2026.09', '청해부대가 어디까지 움직일지, 국회가 이 문제를 어떻게 다룰지는 아직 정해지지 않았습니다.', None, []),
]

BANNED = [r'가지.{0,8}(화살|문제|흐름).{0,12}모인다', r'한\s?번에 흔들', r'세\s?겹', r'방향을 정한다', r'같은 자리로 돌아',
          r'로 읽으면', r'승부는', r'진짜 뉴스', r'계약서에', r'서 있는 자리', r'만 보면', r'로 읽힌다', r'말하지 않는 것',
          r'이것이 바로', r'핵심은 .{0,10}(이다|입니다)$']


def lint():
    bad = []
    for sc, d, t, tt, em in SCRIPT:
        for p in BANNED:
            if re.search(p, t): bad.append(('slop', p, t))
        s = tt or t
        if re.search(r'[0-9%~/:→()\[\]]', s): bad.append(('tts-symbol', s))
        for e in em:
            if e not in t: bad.append(('emphasis-missing', e, t))
    return bad


async def edge_one(text, path):
    import edge_tts
    for a in range(4):
        try:
            await edge_tts.Communicate(text, 'ko-KR-InJoonNeural', rate='-3%', pitch='-2Hz').save(path)
            if os.path.getsize(path) > 1000: return
        except Exception as e:
            print('retry', e); await asyncio.sleep(2)


def eleven_one(text, path, prev_text, next_text):
    """ElevenLabs with-timestamps: audio + character alignment (saved next to the mp3)."""
    import requests, base64
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ['ELEVENLABS_VOICE_ID']}/with-timestamps",
                      headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY']}, timeout=120,
                      json=dict(text=text, model_id=os.environ.get('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2'), previous_text=prev_text, next_text=next_text,
                                voice_settings=dict(stability=0.65, similarity_boost=0.8, style=0.1)))
    r.raise_for_status(); d = r.json()
    open(path, 'wb').write(base64.b64decode(d['audio_base64'])); json.dump(d.get('alignment'), open(path + '.align.json', 'w'))


def build():
    S = []
    cnt = {}
    for sc, d, t, tt, em in SCRIPT:
        cnt[sc] = cnt.get(sc, 0) + 1
        segs = [[t, 0]]
        for e in em:
            ns = []
            for s_, f in segs:
                if f or e not in s_: ns.append([s_, f]); continue
                i = s_.index(e); ns += [x for x in ([s_[:i], 0], [e, 1], [s_[i + len(e):], 0]) if x[0]]
            segs = ns
        S.append(dict(sid=f'{sc}_{cnt[sc] - 1}', scene=sc, date=d, text=t, tts=tt or t, segments=segs))
    jobs = []; eleven = bool(os.environ.get('ELEVENLABS_API_KEY') and os.environ.get('ELEVENLABS_VOICE_ID'))
    for k, x in enumerate(S):
        h = hashlib.sha1((x['tts'] + ('|el|' + os.environ.get('ELEVENLABS_VOICE_ID', '') if eleven else '')).encode()).hexdigest()[:10]; x['mp3'] = f"{V}/tts/{x['sid']}_{h}.mp3"
        if os.path.exists(x['mp3']) and os.path.getsize(x['mp3']) > 1000: continue
        if eleven: eleven_one(x['tts'], x['mp3'], S[k - 1]['tts'] if k else None, S[k + 1]['tts'] if k + 1 < len(S) else None)
        else: jobs.append((x['tts'], x['mp3']))

    async def run():
        sem = asyncio.Semaphore(5)
        async def one(t, p):
            async with sem: await edge_one(t, p)
        await asyncio.gather(*[one(t, p) for t, p in jobs])
    if jobs: asyncio.run(run())
    for x in S:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', x['mp3'], '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; idx = np.where(np.abs(a) > 0.012)[0]
        a = a[max(0, idx[0] - int(0.03 * SR)): min(len(a), idx[-1] + int(0.12 * SR))]
        f = int(0.01 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        x['npy'] = x['mp3'][:-4] + '.npy'; np.save(x['npy'], a); x['dur'] = len(a) / SR
    t = LEAD; prev = None; cards = []; scene_start = {}
    for x in S:
        if x['scene'] != prev:
            if prev == 'open': cards.append(dict(kind='title', t0=t + 0.2, t1=t + 0.2 + TITLE_CARD)); t += TITLE_CARD + 0.6
            elif prev is not None: t += SCENE_GAP
            scene_start[x['scene']] = t; prev = x['scene']
        x['t0'] = t; x['t1'] = t + x['dur']; t = x['t1'] + GAP
    t += 1.2; cards.append(dict(kind='end', t0=t, t1=t + END_CARD))
    return dict(sentences=S, cards=cards, scene_start=scene_start, total=t + END_CARD + 0.5, voice=('elevenlabs' if eleven else 'edge-tts ko-KR-InJoonNeural'),
                title='호르무즈와 한국', subtitle='한국은 왜 파병하지 않았나', date='2026.09.26')


if __name__ == '__main__':
    bad = lint()
    if bad:
        for b in bad: print('LINT', b)
        sys.exit(1)
    P = build(); json.dump(P, open(f'{V}/plan.json', 'w'), ensure_ascii=False, indent=1)
    print(f"lint ok · sentences {len(P['sentences'])} · total {P['total']:.1f}s ({P['total'] / 60:.2f} min)")
    print({k: round(v, 1) for k, v in P['scene_start'].items()})
