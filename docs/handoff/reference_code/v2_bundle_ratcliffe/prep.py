"""prep.py — assets for the bundle video.
- base tiers W (world, z5 terrain) and E (Eastern Europe, z7 terrain) in Web-Mercator 'degree' space
- vector geometry (countries, coarse/fine) in lon/lat
- portraits: repo library (RGBA) + licensed Commons photos -> rembg cutout -> mono
- flags: flag-icons (MIT) 1x1 + 4x3 via cairosvg
- entity registry keyed by bundle node ids
"""
import json, math, pickle, time, io, os, sys, glob, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
from shapely.geometry import shape, box
from shapely.ops import unary_union

V = '/home/claude/v2'; D = '/home/claude/data'; OG = '/home/claude/og'
os.makedirs(f'{V}/assets/portraits', exist_ok=True); os.makedirs(f'{V}/assets/flags', exist_ok=True)


def ym(lat):
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


TIERS = {
    'W': dict(lon0=-90.0, lon1=67.0, lat0=12.0, lat1=68.0, ppd=32, tiles=f'{V}/data/terr5', z=5),
    'E': dict(lon0=18.0, lon1=46.0, lat0=38.0, lat1=58.0, ppd=128, tiles=f'{D}/terr', z=7),
}


# ------------------------------------------------------------------ geometry
def load_geo():
    ctry = json.load(open(f'{D}/ne_10m_admin_0_countries.geojson'))
    adm1 = json.load(open(f'{D}/ne_10m_admin_1_states_provinces.geojson'))
    crimea = unary_union([shape(f['geometry']).buffer(0) for f in adm1['features']
                          if f['properties']['name_en'] in ('Autonomous Republic of Crimea', 'Sevastopol')])
    bb = box(-110, 0, 80, 78)
    G = {}
    for f in ctry['features']:
        p = f['properties']
        g = shape(f['geometry']).buffer(0)
        if not g.intersects(bb):
            continue
        G[p['ISO_A2_EH'] if p.get('ISO_A2_EH') not in (None, '-99') else p['ADMIN']] = (p['ADMIN'], g.intersection(bb))
    ua = G['UA']; ru = G['RU']
    G['UA'] = (ua[0], unary_union([ua[1], crimea]).buffer(0))
    G['RU'] = (ru[0], ru[1].difference(crimea.buffer(0.001)).buffer(0))
    return G


def rings(g, tol):
    gs = g.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(gs, 'geoms', [gs]):
        if p.geom_type != 'Polygon' or p.is_empty:
            continue
        out.append(np.asarray(p.exterior.coords, np.float32)[:, :2])
        for r in p.interiors:
            out.append(np.asarray(r.coords, np.float32)[:, :2])
    return out


# ------------------------------------------------------------------ terrain
def mosaic(tdir, z):
    fs = glob.glob(f'{tdir}/*.png')
    xs = sorted({int(os.path.basename(f).split('_')[0]) for f in fs}); ys = sorted({int(os.path.basename(f).split('_')[1][:-4]) for f in fs})
    x0, y0 = xs[0], ys[0]
    M = np.zeros(((ys[-1] - y0 + 1) * 256, (xs[-1] - x0 + 1) * 256), np.float32)
    for f in fs:
        x, y = os.path.basename(f)[:-4].split('_'); x, y = int(x), int(y)
        try:
            a = np.asarray(Image.open(f).convert('RGB'), np.float32)
        except Exception:
            continue
        M[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return M, x0, y0


def tier_elev(T):
    M, x0, y0 = mosaic(T['tiles'], T['z'])
    S = 256 * 2 ** T['z']
    W = int(round((T['lon1'] - T['lon0']) * T['ppd'])); H = int(round((ym(T['lat1']) - ym(T['lat0'])) * T['ppd']))
    Xa = (T['lon0'] + 180) / 360 * S - x0 * 256; Xb = (T['lon1'] + 180) / 360 * S - x0 * 256
    Ya = (1 - ym(T['lat1']) / 180) / 2 * S - y0 * 256; Yb = (1 - ym(T['lat0']) / 180) / 2 * S - y0 * 256
    im = Image.fromarray(M, 'F').transform((W, H), Image.EXTENT, (Xa, Ya, Xb, Yb), Image.BICUBIC)
    return np.asarray(im, np.float32), W, H


def lerp_col(stops, v):
    v = np.clip(v, stops[0][0], stops[-1][0])
    out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (v >= a) & (v <= b)
        f = ((v - a) / (b - a))[m][:, None]
        out[m] = np.array(ca, np.float32) * (1 - f) + np.array(cb, np.float32) * f
    return out


def hexc(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def build_tier(name, T, G):
    t0 = time.time()
    E, W, H = tier_elev(T)
    ppd = T['ppd']
    lat_rows = np.degrees(2 * np.arctan(np.exp(np.radians(ym(T['lat1']) - np.arange(H) / ppd))) - np.pi / 2)
    mpp = (111320 * np.cos(np.radians(lat_rows)) / ppd)[:, None]
    # land mask from vector
    tol = 0.02 if ppd < 64 else 0.004
    mimg = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(mimg)
    for k, (nm, g) in G.items():
        for r in rings(g, tol):
            xs = (r[:, 0] - T['lon0']) * ppd; ys = (ym(T['lat1']) - ym(r[:, 1])) * ppd
            if xs.max() < 0 or xs.min() > W or ys.max() < 0 or ys.min() > H:
                continue
            dr.polygon(list(zip(xs.tolist(), ys.tolist())), fill=255)
    # holes (lakes) are ignored intentionally (they read as land at these scales)
    land = np.asarray(mimg.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    # hillshade
    ex = 2.6 if ppd < 64 else 1.8
    gy, gx = np.gradient(np.maximum(E, 0) * ex)
    gx = gx / mpp; gy = gy / mpp
    az, alt = math.radians(315), math.radians(42)
    slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)
    elev = np.clip(E, 0, 4000)
    lc = lerp_col([(0, hexc('#1c2129')), (400, hexc('#22272e')), (1500, hexc('#2c2d31')), (4000, hexc('#3a3834'))], elev)
    shade = (0.55 + 0.9 * (hs - np.sin(alt)))[..., None]
    lc = lc * np.clip(shade, 0.45, 1.5)
    depth = np.clip(-E, 0, 6000)
    sc = lerp_col([(0, hexc('#1a3f58')), (120, hexc('#163650')), (600, hexc('#10283c')), (2000, hexc('#0b1d2d')), (6000, hexc('#07131f'))], depth)
    # coastal glow in sea
    glow = np.asarray(mimg.filter(ImageFilter.GaussianBlur(3 if ppd < 64 else 7)), np.float32)[..., None] / 255
    sc = sc + np.array(hexc('#2e8aa6'), np.float32) * glow * 0.22
    out = sc * (1 - land[..., None]) + lc * land[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGB')
    img.save(f'{V}/assets/base_{name}_{ppd}.png')
    lv = [ppd]
    cur = img
    for k in range(2):
        cur = cur.resize((cur.width // 2, cur.height // 2), Image.LANCZOS)
        cur.save(f'{V}/assets/base_{name}_{ppd // 2 ** (k + 1)}.png'); lv.append(ppd // 2 ** (k + 1))
    print(f'tier {name} {W}x{H} levels {lv} {time.time() - t0:.0f}s', flush=True)
    return lv


# ------------------------------------------------------------------ portraits
def commons_fetch(pid, title, width=960):
    import urllib.parse
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(action='query', titles=title, prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=width, format='json'))
    hdr = {'User-Agent': 'osint-video-trial/0.1 (contact: research use)'}
    for attempt in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=30))
            ii = list(r['query']['pages'].values())[0]['imageinfo'][0]
            time.sleep(2.0)
            data = None
            for src in (ii['thumburl'], ii['url']):
                try:
                    d = urllib.request.urlopen(urllib.request.Request(src, headers=hdr), timeout=40).read()
                    Image.open(io.BytesIO(d)).verify(); data = d; break
                except Exception as e2:
                    print('src fail', pid, src[-40:], e2, flush=True); time.sleep(4)
            if data is None:
                raise RuntimeError('no valid image')
            open(f'{V}/assets/photo_{pid}.jpg', 'wb').write(data)
            return True
        except Exception as e:
            print('retry', pid, e, flush=True); time.sleep(6 + attempt * 6)
    return False


def mono(im):
    """high-contrast mono in the spirit of the repo's library portraits"""
    a = im.getchannel('A')
    g = ImageOps.grayscale(im.convert('RGB'))
    g = ImageOps.autocontrast(g, cutoff=1.2)
    g = g.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
    arr = np.asarray(g, np.float32) / 255
    arr = 0.5 + np.tanh((arr - 0.52) * 2.6) / (2 * np.tanh(1.3))
    g = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), 'L')
    out = Image.merge('RGBA', (g, g, g, a))
    return out


def normalize_portrait(im, out_w=420):
    a = np.asarray(im.getchannel('A'))
    ys, xs = np.where(a > 40)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w = x1 - x0; h = min(y1 - y0, int(w * 1.22))
    crop = im.crop((x0, y0, x1, y0 + h))
    s = out_w / crop.width
    return crop.resize((out_w, int(crop.height * s)), Image.LANCZOS)


def build_portraits():
    lib = json.load(open(f'{OG}/assets/library/library_manifest.json'))
    libp = {p['person_id']: p for p in lib['people']}
    newm = json.load(open(f'{V}/assets/photo_manifest_new.json')) if os.path.exists(f'{V}/assets/photo_manifest_new.json') else {}
    picks = {'ratcliffe': 'File:Official Portrait of CIA Director John Ratcliffe.webp', 'naryshkin': 'File:Sergey Naryshkin (2016-07-14).jpg', 'bortnikov': 'File:Bortnikov 2019 crop.jpg'}
    cand = json.load(open(f'{V}/data/commons_candidates.json'))
    for pid, t in picks.items():
        if not os.path.exists(f'{V}/assets/photo_{pid}.jpg'):
            commons_fetch(pid, t)
        x = [c for c in cand[pid] if c['title'] == t][0]
        newm[pid] = dict(title=t, license=x['lic'], artist=x['artist'], credit=x['credit'], page=x['page'], restrictions=x['restr'])
    json.dump(newm, open(f'{V}/assets/photo_manifest_new.json', 'w'), ensure_ascii=False, indent=1)
    reg = {}
    for pid in ('trump', 'putin', 'zelensky'):
        im = Image.open(f"{OG}/{libp[pid]['variants'][0]['path']}").convert('RGBA')
        normalize_portrait(im).save(f'{V}/assets/portraits/{pid}.png')
        s = libp[pid]['source']
        reg[pid] = dict(src='repo_library', license=s['license'], credit=s.get('credit', ''), url=s['url'], tool=libp[pid]['variants'][0]['tool'])
    try:
        from rembg import new_session, remove
        sess = new_session('u2net_human_seg')
    except Exception as e:
        print('rembg unavailable', e); sess = None
    for pid in ('ratcliffe', 'naryshkin', 'bortnikov'):
        p = f'{V}/assets/photo_{pid}.jpg'
        if not os.path.exists(p):
            print('missing photo', pid); continue
        im = Image.open(p).convert('RGB')
        if sess is not None:
            cut = remove(im, session=sess).convert('RGBA')
            a = cut.getchannel('A').filter(ImageFilter.GaussianBlur(0.8))
            cut.putalpha(a)
        else:
            cut = im.convert('RGBA')
        normalize_portrait(mono(cut)).save(f'{V}/assets/portraits/{pid}.png')
        m = newm[pid]
        reg[pid] = dict(src='wikimedia_commons', license=m['license'], credit=m['artist'] or m['credit'], url=m['page'], tool='rembg+mono(prep.py)')
    return reg


# ------------------------------------------------------------------ flags
def build_flags():
    import cairosvg
    codes = ['us', 'ru', 'ua', 'ir', 'lv', 'pl', 'ro', 'de', 'eu', 'ee', 'lt']
    for c in codes:
        p1 = f'{V}/assets/flags_svg/{c}.svg'
        cairosvg.svg2png(url=p1, write_to=f'{V}/assets/flags/{c}_1x1.png', output_width=256, output_height=256)
        p43 = f'{V}/assets/flags_svg/{c}_4x3.svg'
        if not os.path.exists(p43):
            try:
                urllib.request.urlretrieve(f'https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{c}.svg', p43)
            except Exception as e:
                print('4x3 fail', c, e); continue
        cairosvg.svg2png(url=p43, write_to=f'{V}/assets/flags/{c}_4x3.png', output_width=480, output_height=360)
    return codes


if __name__ == '__main__':
    what = sys.argv[1:] or ['geo', 'base', 'portraits', 'flags']
    G = None
    if 'geo' in what or 'base' in what:
        G = load_geo()
        geo = {'coarse': {k: rings(g, 0.03) for k, (n, g) in G.items()}, 'fine': {k: rings(g, 0.006) for k, (n, g) in G.items()},
               'names': {k: n for k, (n, g) in G.items()}, 'tiers': TIERS}
        pickle.dump(geo, open(f'{V}/assets/geo2.pkl', 'wb'))
        print('geo countries', len(G), flush=True)
    if 'base' in what:
        for n, T in TIERS.items():
            T['levels'] = build_tier(n, T, G)
        pickle.dump(TIERS, open(f'{V}/assets/tiers.pkl', 'wb'))
    reg = {}
    if 'portraits' in what:
        reg = build_portraits()
        json.dump(reg, open(f'{V}/assets/portrait_registry.json', 'w'), ensure_ascii=False, indent=1)
        print('portraits', list(reg), flush=True)
    if 'flags' in what:
        print('flags', build_flags(), flush=True)
