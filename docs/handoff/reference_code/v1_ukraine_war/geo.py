import shapefile, pickle, math
from shapely.geometry import shape, box, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely import make_valid

NE = '/home/claude/ne/'
BB = box(15, 37.5, 49, 59.5)   # generous crop

def read(path, filt=None):
    r = shapefile.Reader(NE + path, encoding='utf-8', encodingErrors='replace')
    out = []
    for sr in r.iterShapeRecords():
        d = sr.record.as_dict()
        if filt and not filt(d):
            continue
        try:
            g = make_valid(shape(sr.shape.__geo_interface__))
        except Exception:
            continue
        if not g.intersects(BB):
            continue
        out.append((d, g.intersection(BB)))
    return out

# ---- admin1 : Ukraine oblasts incl. Crimea & Sevastopol
adm1 = read('ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp',
            lambda d: (d.get('iso_3166_2') or '').startswith('UA-'))
oblasts = {d['iso_3166_2']: g for d, g in adm1}
names = {d['iso_3166_2']: d['name_en'] for d, g in adm1}
ukraine = unary_union(list(oblasts.values())).buffer(0)
crimea = unary_union([oblasts['UA-43'], oblasts['UA-40']]).buffer(0)
print('oblasts', len(oblasts), 'ukraine area deg2', round(ukraine.area, 2))

# ---- admin0 countries
adm0 = read('ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
countries = {}
for d, g in adm0:
    a3 = d['ADM0_A3']
    if a3 == 'UKR':
        continue
    if a3 == 'RUS':
        g = g.difference(crimea.buffer(0.002))
    countries[a3] = g.buffer(0)
countries['UKR'] = ukraine
print('countries', sorted(countries.keys()))

# ---- rivers (major) & lakes
rv = read('ne_10m_rivers_lake_centerlines/ne_10m_rivers_lake_centerlines.shp',
          lambda d: (d.get('scalerank') or 99) <= 7)
rivers = []
for d, g in rv:
    nm = d.get('name_en') or d.get('name') or ''
    rivers.append((nm, d.get('scalerank'), g))
print('rivers', len(rivers), sorted(set(r[0] for r in rivers))[:60])
lk = read('ne_10m_lakes/ne_10m_lakes.shp', lambda d: (d.get('scalerank') or 99) <= 8)
lakes = [g for d, g in lk]
land = unary_union([g for d, g in read('ne_10m_land/ne_10m_land.shp')]).buffer(0)

# ---------------------------------------------------------------- snapshots
def east_of(line, closing):
    """polygon built from a front line + closing points on the Russian / sea side"""
    return Polygon(list(line) + list(closing)).buffer(0)

donlug = unary_union([oblasts['UA-14'], oblasts['UA-09']])

# 2015-2022 line of contact (approx.)
LOC = [(37.76, 46.95), (37.76, 47.08), (37.66, 47.22), (37.62, 47.40), (37.63, 47.62),
       (37.62, 47.75), (37.56, 47.88), (37.60, 47.96), (37.70, 48.08), (37.80, 48.17),
       (37.93, 48.30), (38.00, 48.40), (38.25, 48.43), (38.42, 48.40), (38.45, 48.48),
       (38.47, 48.58), (38.47, 48.66), (38.58, 48.71), (38.85, 48.76), (39.10, 48.74),
       (39.25, 48.70), (39.45, 48.62), (39.70, 48.60), (40.30, 48.62)]
sep2015 = east_of(LOC, [(40.8, 48.62), (40.8, 46.8), (38.3, 46.7)]).intersection(donlug)
occ2014 = unary_union([crimea, sep2015]).buffer(0)

CLOSE_SEA = [(31.3, 46.45), (31.3, 45.6), (32.5, 44.0), (36.8, 44.2), (39.5, 46.6),
             (41.2, 47.2), (41.2, 50.9), (37.0, 51.0)]

# peak (late March 2022), east & south
FM = [(36.20, 50.40), (36.30, 50.10), (36.55, 49.95), (36.80, 49.70), (36.90, 49.45),
      (37.15, 49.22), (37.55, 49.08), (37.95, 49.00), (38.25, 48.98), (38.40, 48.90),
      (38.45, 48.72), (38.47, 48.60), (38.45, 48.48), (38.42, 48.40), (38.25, 48.43),
      (38.00, 48.40), (37.93, 48.30), (37.80, 48.17), (37.70, 48.08), (37.60, 47.96),
      (37.56, 47.88), (37.35, 47.80), (37.15, 47.78), (36.85, 47.80), (36.55, 47.68),
      (36.25, 47.56), (35.95, 47.55), (35.70, 47.52), (35.40, 47.62), (35.20, 47.64),
      (35.00, 47.56), (34.60, 47.50), (34.25, 47.46), (33.95, 47.55), (33.55, 47.52),
      (33.20, 47.33), (32.85, 47.12), (32.45, 46.92), (32.10, 46.75), (31.85, 46.62),
      (31.60, 46.52)]
peak_se = east_of(FM, CLOSE_SEA + [(36.2, 50.9)]).intersection(ukraine)
KYIV_W = Polygon([(29.30, 51.60), (29.40, 51.15), (29.55, 50.85), (29.75, 50.55), (29.95, 50.45),
                  (30.20, 50.47), (30.30, 50.55), (30.45, 50.72), (30.50, 51.00), (30.60, 51.30),
                  (30.70, 51.65)]).intersection(ukraine)
occ2022peak = unary_union([peak_se, occ2014, KYIV_W]).buffer(0)

# Dnipro axis (reservoir + lower river) used by later lines
DNIPRO = [(35.10, 47.62), (34.95, 47.58), (34.55, 47.52), (34.20, 47.45), (33.95, 47.35),
          (33.85, 47.20), (33.65, 47.00), (33.45, 46.83), (33.10, 46.72), (32.75, 46.66),
          (32.55, 46.61), (32.35, 46.56), (32.10, 46.55), (31.80, 46.58), (31.50, 46.60)]

# after Kherson (Nov 2022)
FN = [(37.95, 50.35), (38.00, 50.05), (38.02, 49.75), (38.02, 49.45), (38.08, 49.25),
      (38.12, 49.05), (38.10, 48.92), (38.15, 48.80), (38.05, 48.70), (38.06, 48.58),
      (38.00, 48.45), (37.95, 48.38), (37.90, 48.28), (37.80, 48.17), (37.72, 48.08),
      (37.62, 47.97), (37.52, 47.92), (37.40, 47.82), (37.25, 47.74), (36.95, 47.75),
      (36.75, 47.73), (36.45, 47.62), (36.25, 47.58), (36.00, 47.50), (35.80, 47.49),
      (35.55, 47.52), (35.30, 47.55)] + DNIPRO
occ2022nov = unary_union([east_of(FN, CLOSE_SEA[1:] + [(37.9, 51.0)]).intersection(ukraine),
                          crimea]).buffer(0)

# Kherson right bank (occupied Mar–Nov 2022)
RB = Polygon(FM[FM.index((33.95, 47.55)):] + list(reversed(DNIPRO[3:]))).buffer(0).intersection(ukraine)
occ2022oct = unary_union([occ2022nov, RB]).buffer(0)

# current (Sept 2026) — approximate
FC = [(36.70, 50.42), (36.80, 50.30), (37.05, 50.25), (37.25, 50.36), (37.45, 50.40),
      (37.55, 50.10), (37.63, 49.85), (37.75, 49.60), (37.95, 49.40), (37.95, 49.20),
      (37.88, 49.06), (37.98, 48.96), (38.02, 48.86), (37.95, 48.75), (37.80, 48.63),
      (37.76, 48.53), (37.60, 48.43), (37.45, 48.38), (37.25, 48.36), (37.08, 48.33),
      (37.00, 48.20), (36.88, 48.05), (36.66, 47.95), (36.50, 47.80), (36.20, 47.72),
      (35.95, 47.62), (35.85, 47.52), (35.60, 47.48), (35.38, 47.55)] + DNIPRO
occ2026 = unary_union([east_of(FC, CLOSE_SEA[1:] + [(36.6, 51.0)]).intersection(ukraine),
                       crimea]).buffer(0)

# Kursk incursion (Aug 2024), inside Russia
KURSK = Polygon([(34.95, 51.25), (35.05, 51.42), (35.35, 51.49), (35.62, 51.36), (35.62, 51.12),
                 (35.45, 51.02), (35.10, 51.05)]).difference(ukraine).intersection(countries['RUS'])

# Ukraine-held Donetsk (2026)
don_free = oblasts['UA-14'].difference(occ2026).buffer(0)

# Kakhovka flood corridor
flood = LineString([(33.40, 46.78), (33.10, 46.70), (32.75, 46.64), (32.50, 46.58),
                    (32.25, 46.53), (31.95, 46.52)]).buffer(0.07).intersection(land)

KM2_PER_DEG2 = lambda lat: (111.32 * math.cos(math.radians(lat))) * 110.57
def km2(g):
    return g.area * KM2_PER_DEG2(g.centroid.y)
UA_KM2 = 603628
for nm, g in [('crimea', crimea), ('sep2015', sep2015), ('occ2014', occ2014), ('peak', occ2022peak),
              ('oct22', occ2022oct), ('nov22', occ2022nov), ('2026', occ2026), ('kursk', KURSK)]:
    print(nm, round(km2(g)), f'{km2(g)/UA_KM2*100:.1f}%')

data = dict(countries=countries, ukraine=ukraine, crimea=crimea, oblasts=oblasts, names=names,
            rivers=rivers, lakes=lakes, land=land,
            snap=dict(occ2014=occ2014, crimea=crimea, sep2015=sep2015, peak=occ2022peak,
                      oct22=occ2022oct, nov22=occ2022nov, c2026=occ2026, kursk=KURSK,
                      don_free=don_free, flood=flood, donlug=donlug,
                      annex4=unary_union([oblasts[k] for k in ('UA-14', 'UA-09', 'UA-23', 'UA-65')])),
            lines=dict(LOC=LOC, FM=FM, FN=FN, FC=FC, DNIPRO=DNIPRO))
pickle.dump(data, open('/home/claude/geo.pkl', 'wb'))
print('saved')
