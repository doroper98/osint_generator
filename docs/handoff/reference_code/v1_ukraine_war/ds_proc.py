import json, pickle, math
from shapely.geometry import shape
from shapely.ops import unary_union, transform
G = pickle.load(open('geo.pkl','rb'))
UA = G['ukraine'].buffer(0); CR = G['crimea']
sel = json.load(open('data/ds_sel.json'))
def sinu(g): return transform(lambda x,y,z=None:(x*math.cos(math.radians(y))*111.32, y*110.57), g)
UA_AREA = sinu(UA).area
def load(fid, peak=False):
    d = json.load(open(f'data/ds/{fid}.json')); gs=[]
    for f in d['features']:
        if f['geometry']['type'] not in ('Polygon','MultiPolygon'): continue
        n = f['properties'].get('name','').lower()
        ok = any(k in n for k in ('occupied','окуп','ордло','ordlo','crimea','крим','tuzla','тузла'))
        if peak: ok = ok or any(k in n for k in ('звільн','liberat','під питанням','невідомо','24.03'))
        if ok:
            try: gs.append(shape(f['geometry']).buffer(0))
            except Exception: pass
    g = unary_union(gs + [CR]).buffer(0.004).buffer(-0.004)
    return g.intersection(UA).simplify(0.004, preserve_topology=True)
out = {}; pct = {}
for k,(fid,dt) in sorted(sel.items()):
    key = 'ds_' + k
    g = load(fid); G['snap'][key] = g; pct[key] = round(100*sinu(g).area/UA_AREA,1)
G['snap']['ds_peak'] = load(1648989208, peak=True); pct['ds_peak'] = round(100*sinu(G['snap']['ds_peak']).area/UA_AREA,1)
G['ds_pct'] = pct; G['ds_dates'] = {('ds_'+k): v[1] for k,v in sel.items()}
pickle.dump(G, open('geo.pkl','wb'))
print({k:pct[k] for k in ['ds_peak','ds_2022-04-01','ds_2022-09-05','ds_2022-11-15','ds_2023-12-01','ds_2024-12-01','ds_2025-12-01','ds_2026-09-26']})
