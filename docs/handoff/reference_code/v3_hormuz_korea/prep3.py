"""prep3 — assets for the Hormuz/Korea video.
Fix vs v2: geometry flattening is recursive (GeometryCollection > MultiPolygon > Polygon) and every country's
land coverage is verified after rasterisation (v2 dropped France from the land mask).
"""
import json, math, pickle, time, io, os, sys, glob, re, subprocess, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from shapely.geometry import shape, box, Point
from shapely.ops import unary_union

V = '/home/claude/v3'; D = '/home/claude/data'; OG = '/home/claude/og'
UA = {'User-Agent': 'osint-video-trial/0.3 (research)'}


def ym(lat): return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


TIERS = {
    'W': dict(lon0=28.0, lon1=140.0, lat0=-12.0, lat1=48.0, ppd=24, tiles=f'{V}/data/t5', z=5),
    'G': dict(lon0=46.0, lon1=62.0, lat0=20.5, lat1=32.5, ppd=96, tiles=f'{V}/data/tg', z=7),
    'K': dict(lon0=122.5, lon1=131.8, lat0=32.3, lat1=39.8, ppd=96, tiles=f'{V}/data/tk', z=7),
}


# ------------------------------------------------------------------ fonts
def fonts():
    fd = os.path.expanduser('~/.fonts'); os.makedirs(fd, exist_ok=True)
    G = 'https://raw.githubusercontent.com/google/fonts/main/ofl'
    want = {f'{G}/ibmplexsanskr/IBMPlexSansKR-{w}.ttf': f'IBMPlexSansKR-{w}.ttf' for w in ('Regular', 'Medium', 'SemiBold', 'Bold')}
    want.update({f'{G}/ibmplexmono/IBMPlexMono-{w}.ttf': f'IBMPlexMono-{w}.ttf' for w in ('Medium', 'SemiBold')})
    for u, n in want.items():
        p = f'{fd}/{n}'
        if not os.path.exists(p):
            try: urllib.request.urlretrieve(u, p)
            except Exception as e: print('font fail', n, e)
    from fontTools.ttLib import TTFont
    for w in ('Bold', 'Medium'):
        p = f'{fd}/GmarketSans{w}.otf'
        if not os.path.exists(p):
            raw = urllib.request.urlopen(urllib.request.Request(f'https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSans{w}.woff', headers=UA), timeout=60).read()
            f = TTFont(io.BytesIO(raw)); f.flavor = None; f.save(p)
    subprocess.run(['fc-cache', '-f'], capture_output=True)
    out = subprocess.run(['fc-list', ':', 'family'], capture_output=True, text=True).stdout
    fam = sorted({l.strip() for l in out.splitlines() if any(k in l for k in ('IBM Plex', 'Gmarket', 'Serif CJK KR'))})
    print('fonts:', fam)


# ------------------------------------------------------------------ geometry
def polys(g):
    """recursive flatten -> list of Polygons"""
    if g is None or g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    if hasattr(g, 'geoms'):
        out = []
        for x in g.geoms: out += polys(x)
        return out
    return []


def rings(g, tol):
    out = []
    for p in polys(g.simplify(tol, preserve_topology=True)):
        out.append(np.asarray(p.exterior.coords, np.float32)[:, :2])
        for r in p.interiors: out.append(np.asarray(r.coords, np.float32)[:, :2])
    return out


def load_countries(bb):
    ctry = json.load(open(f'{D}/ne_10m_admin_0_countries.geojson'))
    G, META = {}, {}
    for f in ctry['features']:
        p = f['properties']; g = shape(f['geometry']).buffer(0)
        if not g.intersects(bb): continue
        k = p['ISO_A2_EH'] if p.get('ISO_A2_EH') not in (None, '-99') else p['ADMIN']
        G[k] = g.intersection(bb)
        META[k] = dict(name=p['ADMIN'], ko=p.get('NAME_KO') or p['ADMIN'], lx=p.get('LABEL_X'), ly=p.get('LABEL_Y'),
                       minlab=p.get('MIN_LABEL', 5), rank=p.get('LABELRANK', 5))
    return G, META


def load_admin1(codes, bb):
    adm = json.load(open(f'{D}/ne_10m_admin_1_states_provinces.geojson'))
    out = {}
    for f in adm['features']:
        p = f['properties']
        if p.get('iso_a2') not in codes: continue
        g = shape(f['geometry']).buffer(0)
        if not g.intersects(bb): continue
        out.setdefault(p['iso_a2'], []).append(dict(name=p.get('name_ko') or p.get('name'), g=g, lx=p.get('longitude'), ly=p.get('latitude')))
    return out


def load_places(bb):
    pp = json.load(open(f'{V}/data/ne_10m_populated_places.geojson'))
    out = []
    for f in pp['features']:
        p = f['properties']; x, y = f['geometry']['coordinates'][:2]
        if not (bb.bounds[0] <= x <= bb.bounds[2] and bb.bounds[1] <= y <= bb.bounds[3]): continue
        ko = p.get('NAME_KO') or p.get('name_ko')
        if not ko: continue
        out.append(dict(ko=ko, lon=x, lat=y, rank=p.get('SCALERANK', p.get('scalerank', 9)), cap=('capital' in (p.get('FEATURECLA') or '').lower()) or p.get('ADM0CAP') == 1,
                        iso=p.get('ADM0_A3') or p.get('SOV_A3'), pop=p.get('POP_MAX') or 0))
    return out


# ------------------------------------------------------------------ terrain & tiers
def mosaic(tdir, z):
    fs = [f for f in glob.glob(f'{tdir}/*.png') if os.path.getsize(f) > 100]
    xs = sorted({int(os.path.basename(f).split('_')[0]) for f in fs}); ys = sorted({int(os.path.basename(f).split('_')[1][:-4]) for f in fs})
    x0, y0 = xs[0], ys[0]
    M = np.zeros(((ys[-1] - y0 + 1) * 256, (xs[-1] - x0 + 1) * 256), np.float32)
    for f in fs:
        x, y = map(int, os.path.basename(f)[:-4].split('_'))
        try: a = np.asarray(Image.open(f).convert('RGB'), np.float32)
        except Exception: continue
        M[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return M, x0, y0


def lerp_col(stops, v):
    v = np.clip(v, stops[0][0], stops[-1][0]); out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (v >= a) & (v <= b); f = ((v - a) / (b - a))[m][:, None]
        out[m] = np.array(ca, np.float32) * (1 - f) + np.array(cb, np.float32) * f
    return out


def hexc(h): h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def build_tier(name, T, G):
    t0 = time.time(); M, x0, y0 = mosaic(T['tiles'], T['z']); S = 256 * 2 ** T['z']; ppd = T['ppd']
    W = int(round((T['lon1'] - T['lon0']) * ppd)); H = int(round((ym(T['lat1']) - ym(T['lat0'])) * ppd))
    ext = ((T['lon0'] + 180) / 360 * S - x0 * 256, (1 - ym(T['lat1']) / 180) / 2 * S - y0 * 256,
           (T['lon1'] + 180) / 360 * S - x0 * 256, (1 - ym(T['lat0']) / 180) / 2 * S - y0 * 256)
    E = np.asarray(Image.fromarray(M, 'F').transform((W, H), Image.EXTENT, ext, Image.BICUBIC), np.float32)
    lat_rows = np.degrees(2 * np.arctan(np.exp(np.radians(ym(T['lat1']) - (np.arange(H) + 0.5) / ppd))) - np.pi / 2)
    mpp = (111320 * np.cos(np.radians(lat_rows)) / ppd)[:, None]
    tol = 0.02 if ppd < 64 else 0.003
    mimg = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(mimg)
    cover = {}
    for k, g in G.items():
        rs = rings(g, tol); n = 0
        for r in rs:
            xs = (r[:, 0] - T['lon0']) * ppd; ys = (ym(T['lat1']) - ym(r[:, 1])) * ppd
            if xs.max() < 0 or xs.min() > W or ys.max() < 0 or ys.min() > H: continue
            dr.polygon(list(zip(xs.tolist(), ys.tolist())), fill=255); n += 1
        cover[k] = n
    # coverage check: every country whose representative point lies in the tier must be land there
    miss = []
    for k, g in G.items():
        rp = g.representative_point()
        x = (rp.x - T['lon0']) * ppd; y = (ym(T['lat1']) - ym(rp.y)) * ppd
        if 0 <= x < W and 0 <= y < H and mimg.getpixel((int(x), int(y))) < 128: miss.append(k)
    land = np.asarray(mimg.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    ex = 2.8 if ppd < 64 else 2.0
    gy, gx = np.gradient(np.maximum(E, 0) * ex); gx /= mpp; gy /= mpp
    az, alt = math.radians(315), math.radians(42)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    hs = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    lc = lerp_col([(0, hexc('#2b313a')), (400, hexc('#30353c')), (1500, hexc('#3b3a3a')), (4000, hexc('#4b4640'))], np.clip(E, 0, 4000))
    lc = lc * np.clip((0.58 + 0.95 * (hs - np.sin(alt)))[..., None], 0.5, 1.5)
    sc = lerp_col([(0, hexc('#1c4a66')), (60, hexc('#18415c')), (400, hexc('#11304a')), (2000, hexc('#0c2236')), (6000, hexc('#081626'))], np.clip(-E, 0, 6000))
    glow = np.asarray(mimg.filter(ImageFilter.GaussianBlur(3 if ppd < 64 else 8)), np.float32)[..., None] / 255
    sc = sc + np.array(hexc('#3a9cb8'), np.float32) * glow * 0.2
    out = sc * (1 - land[..., None]) + lc * land[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB')
    lv = [ppd]; img.save(f'{V}/assets/base_{name}_{ppd}.png'); cur = img
    for k in range(2):
        cur = cur.resize((cur.width // 2, cur.height // 2), Image.LANCZOS); cur.save(f'{V}/assets/base_{name}_{ppd // 2 ** (k + 1)}.png'); lv.append(ppd // 2 ** (k + 1))
    print(f'tier {name} {W}x{H} {time.time() - t0:.0f}s  land-miss={miss}', flush=True)
    return lv


# ------------------------------------------------------------------ portraits / emblems / flags
def commons_get(title, dest, width=960):
    import urllib.parse
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(action='query', titles=title, prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=width, format='json'))
    for a in range(6):
        try:
            ii = list(json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))['query']['pages'].values())[0]['imageinfo'][0]
            for src in (ii.get('thumburl'), ii['url']):
                try:
                    d = urllib.request.urlopen(urllib.request.Request(src, headers=UA), timeout=40).read()
                    Image.open(io.BytesIO(d)).verify(); open(dest, 'wb').write(d); return ii
                except Exception as e: print('src fail', title[:30], e); time.sleep(5)
        except Exception as e: print('api fail', e); time.sleep(6 + 5 * a)
    return None


def mono(im):
    a = im.getchannel('A'); g = ImageOps.autocontrast(ImageOps.grayscale(im.convert('RGB')), cutoff=1.2).filter(ImageFilter.UnsharpMask(2, 90, 2))
    arr = np.asarray(g, np.float32) / 255; arr = 0.5 + np.tanh((arr - 0.52) * 2.6) / (2 * np.tanh(1.3))
    g = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), 'L'); return Image.merge('RGBA', (g, g, g, a))


def normalize_portrait(im, out_w=420):
    a = np.asarray(im.getchannel('A')); ys, xs = np.where(a > 40)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); w = x1 - x0; h = min(y1 - y0, int(w * 1.22))
    c = im.crop((x0, y0, x1, y0 + h)); return c.resize((out_w, int(c.height * out_w / c.width)), Image.LANCZOS)


def portraits_emblems():
    cand = json.load(open(f'{V}/data/commons_v3.json'))
    lib = {p['person_id']: p for p in json.load(open(f'{OG}/assets/library/library_manifest.json'))['people']}
    pm = json.load(open(f'{OG}/assets/library/workshop/references/photo_manifest.json'))['people']
    reg = {}
    for pid in ('trump', 'khamenei'):
        im = Image.open(f"{OG}/{lib[pid]['variants'][0]['path']}").convert('RGBA'); normalize_portrait(im).save(f'{V}/assets/portraits/{pid}.png')
        reg[pid] = dict(src='repo_library', license=lib[pid]['source']['license'], artist=re.sub('<[^>]+>', '', pm.get(pid, {}).get('artist', '')), url=lib[pid]['source']['url'])
    picks = {'lee_jae_myung': ('lee_jae_myung', 'File:Lee Jae Myung portrait.jpg'), 'roh_moo_hyun': ('roh_moo_hyun', 'File:Roh Moo-hyun presidential portrait.jpg')}
    from rembg import new_session, remove
    sess = new_session('u2net_human_seg')
    for pid, (ck, t) in picks.items():
        c = [x for x in cand[ck] if x['title'] == t][0]
        p = f'{V}/assets/photo_{pid}.jpg'
        if not os.path.exists(p): commons_get(t, p); time.sleep(2)
        cut = remove(Image.open(p).convert('RGB'), session=sess).convert('RGBA'); cut.putalpha(cut.getchannel('A').filter(ImageFilter.GaussianBlur(0.8)))
        normalize_portrait(mono(cut)).save(f'{V}/assets/portraits/{pid}.png')
        reg[pid] = dict(src='wikimedia_commons', license=c['lic'], artist=c['artist'], url=c['page'], title=t)
    em = {}
    c = [x for x in cand['centcom'] if 'Naval Forces Central Command patch' in x['title']][0]
    p = f'{V}/assets/emblems/navcent.png'
    if not os.path.exists(p): commons_get(c['title'], p, 500)
    em['navcent'] = dict(license=c['lic'], url=c['page'], title=c['title'], restrictions=c['restr'])
    json.dump(dict(people=reg, emblems=em), open(f'{V}/assets/rights_registry.json', 'w'), ensure_ascii=False, indent=1)
    print('portraits', list(reg), 'emblems', list(em))


def flags():
    import cairosvg
    extra = ['au', 'nl', 'ca', 'it', 'eu']
    for c in extra:
        for kind in ('1x1', '4x3'):
            dst = f'{V}/assets/flags_svg/{c}.svg' if kind == '1x1' else f'{V}/assets/flags_svg/{c}_4x3.svg'
            if not os.path.exists(dst): urllib.request.urlretrieve(f'https://raw.githubusercontent.com/lipis/flag-icons/main/flags/{kind}/{c}.svg', dst)
    for f in glob.glob(f'{V}/assets/flags_svg/*.svg'):
        n = os.path.basename(f)[:-4]
        if n.endswith('_4x3'): cairosvg.svg2png(url=f, write_to=f'{V}/assets/flags/{n}.png', output_width=480, output_height=360)
        else: cairosvg.svg2png(url=f, write_to=f'{V}/assets/flags/{n}_1x1.png', output_width=256, output_height=256)
    print('flags', len(glob.glob(f'{V}/assets/flags/*.png')))


if __name__ == '__main__':
    what = sys.argv[1:] or ['fonts', 'geo', 'base', 'people', 'flags']
    if 'fonts' in what: fonts()
    bb = box(20, -20, 150, 60)
    if 'geo' in what or 'base' in what:
        G, META = load_countries(bb)
        if 'geo' in what:
            ADM = load_admin1({'KR', 'IR', 'OM', 'AE', 'SA', 'QA', 'KW', 'BH', 'IQ', 'KP', 'JP', 'YE'}, bb)
            geo = dict(coarse={k: rings(g, 0.03) for k, g in G.items()}, fine={k: rings(g, 0.005) for k, g in G.items()}, meta=META,
                       admin1={k: [dict(name=a['name'], lx=a['lx'], ly=a['ly'], rings=rings(a['g'], 0.006)) for a in v] for k, v in ADM.items()},
                       places=load_places(bb), tiers=TIERS)
            pickle.dump(geo, open(f'{V}/assets/geo3.pkl', 'wb')); print('geo', len(G), 'admin1', {k: len(v) for k, v in ADM.items()}, 'places', len(geo['places']), flush=True)
        if 'base' in what:
            for n, T in TIERS.items(): T['levels'] = build_tier(n, T, G)
            pickle.dump(TIERS, open(f'{V}/assets/tiers.pkl', 'wb'))
    if 'people' in what: portraits_emblems()
    if 'flags' in what: flags()
