<!--
tier: 2
last_synced_with: v1.2.2
ssot_for: [v3-reference-code-inventory]
depends_on: [docs/handoff/19_FABLE_ANALYSIS_AND_OPUS_EXECUTION_PLAN.md, docs/handoff/reference_code/README.md]
last_review: 2026-09-27
origin: Fable 분석 세션 서브에이전트 실측 — 사실만 기록, 판단 없음. Phase 1·2에서 체크리스트로 사용
-->

# v3_hormuz_korea — Engineering Inventory (facts only)

Source root: `/tmp/claude-0/-home-user-osint-generator/c5f24b59-72f0-5987-bbaf-c03182d9b2d0/scratchpad/handoff/osint_video_pipeline_handoff/handoff/reference_code/v3_hormuz_korea/`
Files: `plan3.py` (160 L), `prep3.py` (260 L), `render3.py` (997 L), `mix3.py` (77 L), `media3.py` (50 L), `media3b_round2.md`, `plan.json`, `media_registry.json`, `rights_registry.json`.
Run order (README): plan3 → prep3 (`fonts geo base people flags`) → media3 (+ round-2 manual steps) → render3 → mix3 → ffmpeg mux (docs 11 §2 / 10 §5, not in this dir).

---

## A. Per-file inventory (functions, line ranges, constants, sandbox assumptions)

### A.1 `plan3.py`

| Name | Lines | Purpose |
|---|---|---|
| module consts | 9-10 | `V='/home/claude/v3'`, `SR=44100`, `GAP=0.5, SCENE_GAP=1.0, TITLE_CARD=5.6, END_CARD=11.0, LEAD=1.2` |
| `SCRIPT` | 13-69 | 45 tuples `(scene, date_badge, subtitle, tts_or_None, emphasis_list)`; 11 scenes: open, route, war, ask, timeline, cost, review, past, debate, decision, now |
| `BANNED` | 71-73 | 15 regexes (see G) |
| `lint()` | 76-85 | returns list of `('slop', pattern, text)`, `('tts-symbol', tts_text)`, `('emphasis-missing', e, text)` |
| `edge_one(text, path)` async | 88-95 | edge-tts synth, 4 attempts, accept if file >1000 bytes, `asyncio.sleep(2)` between retries |
| `eleven_one(text, path, prev_text, next_text)` | 98-106 | ElevenLabs `/with-timestamps`; writes mp3 + `path+'.align.json'` |
| `build()` | 109-150 | segments, cache key, synth dispatch (semaphore 5), ffmpeg decode + trim + 10 ms fades, timeline, returns plan dict |
| `__main__` | 153-160 | lint → exit 1 on any finding; writes `{V}/plan.json` (`ensure_ascii=False, indent=1`) |

Sandbox/paths to re-parameterise: `V='/home/claude/v3'` (L9); output `{V}/tts/{sid}_{hash}.mp3` / `.npy` (L124, L140); `{V}/plan.json` (L158). Env vars: `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID` (default `eleven_multilingual_v2`). External URL: `https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps`. Binary: `ffmpeg` (L136). Hard-coded metadata in return: `title='호르무즈와 한국'`, `subtitle='한국은 왜 파병하지 않았나'`, `date='2026.09.26'`, `voice='edge-tts ko-KR-InJoonNeural'` (L149-150).

### A.2 `prep3.py`

| Name | Lines | Purpose |
|---|---|---|
| module consts | 11-12 | `V='/home/claude/v3'`, `D='/home/claude/data'`, `OG='/home/claude/og'`, `UA={'User-Agent':'osint-video-trial/0.3 (research)'}` |
| `ym(lat)` | 15 | numpy Mercator y in degrees (no clip) |
| `TIERS` | 18-22 | W/G/K tier dicts (see H) |
| `fonts()` | 26-45 | download IBM Plex Sans KR ×4, IBM Plex Mono ×2 (Google fonts raw), GmarketSans Bold/Medium (woff→otf via fontTools) into `~/.fonts`; `fc-cache -f`; prints families matching 'IBM Plex', 'Gmarket', 'Serif CJK KR' |
| `polys(g)` | 49-57 | recursive flatten any geometry → list[Polygon] |
| `rings(g, tol)` | 60-65 | simplify(tol, preserve_topology) → list of float32 (N,2) arrays (exterior + interiors) |
| `load_countries(bb)` | 68-78 | NE admin0; key = `ISO_A2_EH` unless None/'-99' → `ADMIN`; geometry `.buffer(0).intersection(bb)`; META: name, ko(`NAME_KO`), lx/ly(`LABEL_X/Y`), minlab(`MIN_LABEL`,5), rank(`LABELRANK`,5) |
| `load_admin1(codes, bb)` | 81-90 | NE admin1 filtered by `iso_a2 in codes`; dict code→[{name(name_ko or name), g, lx(longitude), ly(latitude)}] |
| `load_places(bb)` | 93-103 | NE populated places inside bbox with `NAME_KO`/`name_ko`; fields ko, lon, lat, rank(SCALERANK), cap(FEATURECLA contains 'capital' or ADM0CAP==1), iso(ADM0_A3/SOV_A3), pop(POP_MAX) |
| `mosaic(tdir, z)` | 107-117 | terrarium PNG tiles `{x}_{y}.png` (size>100 B) → float32 elevation mosaic; decode `R*256+G+B/256-32768`; returns (M, x0, y0) |
| `lerp_col(stops, v)` | 120-125 | piecewise-linear colour ramp |
| `hexc(h)` | 128 | hex → [r,g,b] 0-255 ints (differs from render3.hexc) |
| `build_tier(name, T, G)` | 131-172 | raster base map + hillshade + land mask + coverage check; saves 3 mip levels; returns `[ppd, ppd//2, ppd//4]` |
| `commons_get(title, dest, width=960)` | 176-188 | Wikimedia Commons imageinfo API (thumburl then url), 6 attempts, PIL verify |
| `mono(im)` | 191-194 | RGBA → B/W stylised portrait (autocontrast cutoff 1.2, UnsharpMask(2,90,2), tanh curve centre 0.52 gain 2.6) |
| `normalize_portrait(im, out_w=420)` | 197-200 | crop to alpha>40 bbox, height ≤ w*1.22, resize to 420 wide |
| `portraits_emblems()` | 203-227 | trump/khamenei from repo library; lee_jae_myung/roh_moo_hyun from Commons + rembg `u2net_human_seg` + alpha blur 0.8 + mono; NAVCENT patch (500 px); writes `rights_registry.json` |
| `flags()` | 230-241 | fetch extra flag SVGs (au,nl,ca,it,eu) from lipis/flag-icons; cairosvg → `{c}_4x3.png` 480×360 and `{c}_1x1.png` 256×256 |
| `__main__` | 244-260 | args subset of `fonts geo base people flags`; `bb=box(20,-20,150,60)`; geo → `geo3.pkl`; base → `tiers.pkl` (TIERS + levels) |

Sandbox/paths: `V`, `D`, `OG` (L11); `~/.fonts` (L27); `{D}/ne_10m_admin_0_countries.geojson` (L69); `{D}/ne_10m_admin_1_states_provinces.geojson` (L82); `{V}/data/ne_10m_populated_places.geojson` (L94); `{V}/data/t5|tg|tk/` (TIERS); `{V}/assets/base_{name}_{lv}.png` (L168,170); `{V}/data/commons_v3.json` (L204); `{OG}/assets/library/library_manifest.json` (L205); `{OG}/assets/library/workshop/references/photo_manifest.json` (L206); `{OG}/{lib[pid]['variants'][0]['path']}` (L209); `{V}/assets/portraits/{pid}.png`, `{V}/assets/photo_{pid}.jpg`, `{V}/assets/emblems/navcent.png`, `{V}/assets/rights_registry.json`; `{V}/assets/flags_svg/*.svg`, `{V}/assets/flags/*.png`; `{V}/assets/geo3.pkl`, `{V}/assets/tiers.pkl`. Binaries: `fc-cache`, `fc-list`. Hard-coded picks: `'File:Lee Jae Myung portrait.jpg'`, `'File:Roh Moo-hyun presidential portrait.jpg'`, `'Naval Forces Central Command patch'` substring; admin1 code set `{'KR','IR','OM','AE','SA','QA','KW','BH','IQ','KP','JP','YE'}`.

### A.3 `render3.py`

| Name | Lines | Purpose |
|---|---|---|
| module setup | 1-11 | `V='/home/claude/v3'`; `P=plan.json`; `FPS=24; W_OUT,H_OUT=854,480`; `TOTAL=P['total']; N=int(TOTAL*FPS)`; `SENT` (sid→sentence), `ORDER`, `SC0=P['scene_start']`, `SCN=list(SC0)` |
| `S(sid, off=0.0)` | 14 | sentence start + off |
| `E(sid, off=0.0)` | 15 | sentence end + off |
| `SC(s)` | 16 | scene start |
| `SC_END(s)` | 17-18 | next scene start − 0.35, or TOTAL for last scene |
| `at_word(sid, word)` | 19-20 | `t0 + (index_of_word / len(text)) * dur` (linear char-position estimate; index −1 → 0) |
| `ym(lat)` | 23 | scalar Mercator (math) |
| `ymv(lat)` | 24 | numpy Mercator, lat clipped ±85 |
| `clamp01`, `smooth`, `ease_io`, `ease_out`, `ease_back` | 25-29 | easing (see D) |
| `window(t,t0,t1,fin=0.5,fout=0.5)` | 30-32 | 0 outside; `min(smooth((t-t0)/fin), smooth((t1-t)/fout))` |
| `hexc(h)` | 33 | hex → tuple floats 0-1 |
| `C` | 36-37 | colour tokens (see E) |
| `FONT` | 40-42 | font map (see E) |
| `font(ctx,name,size)` | 45-47 | `select_font_face(family, NORMAL, BOLD if flag else NORMAL)` + size |
| `HANGUL` | 50 | regex `[ᄀ-ᇿ㄰-㆏가-힣]` |
| `mixed_runs(s,name)` | 53-61 | split string into (run, fontname) runs; Hangul runs in mono fall back to `'sans'` (monom) / `'sansm'` (mono); spaces inherit previous run |
| `text(ctx,s,x,y,size,name='sansm',col,a,halo=3.0,anchor='l',spacing=0.0,halo_a=0.8)` | 64-88 | text with halo stroke `rgba(0.02,0.03,0.05,halo_a*a)` width `halo`, round join; anchors l/c/r; per-char spacing; disp fonts: space = `size*0.3`; returns advance width |
| `tw(ctx,s,size,name)` | 91-95 | text width consistent with `text` |
| `rrect(ctx,x,y,w,h,r)` | 98-100 | rounded rect path |
| `wrap(ctx,s,maxw,size,name)` | 103-110 | greedy word wrap on spaces |
| asset load | 114-117 | `TIERS=tiers.pkl`, `BASE[(tier,lv)]` PIL RGB, `GEO=geo3.pkl`, `REG=rights_registry.json` |
| `to_uv(rings)` | 120-124 | rings → list of `(uv float64 (N,2), min, max)` |
| `BORD`, `ADM`, `PLC*` arrays | 127-131 | pre-projected borders (coarse/fine), admin1, places arrays (`PLC_LON, PLC_V, PLC_RANK, PLC_POP, PLC_CAP`) |
| `KO` | 132-136 | 41 ISO2→Korean country name overrides |
| `SEAS` | 137-139 | 10 sea labels `(name, lon, lat, wmin, wmax)` |
| `surf_from_pil(im)` | 142-146 | PIL RGBA → premultiplied BGRA cairo ImageSurface; returns `(surface, buf)` |
| `PIL_IMG` | 149-153, 166-169 | portraits (lee_jae_myung, roh_moo_hyun, trump, khamenei), `navcent`, flags for 13 codes as `{c}43` and `{c}11`, `photo_hormuz`, `cut_p8`, `photo_rok_iraq` |
| `scaled(key, w)` | 157-161 | cached scaled surface; width quantised to multiples of 3, min 8 |
| `MEDIA`, `CLIP` | 165-168 | media_registry.json; `CLIP={'strikes','niovi'}` np.load mmap of `*_480.npy` (frames,H,W,3) |
| `CAM, EV` | 173 | direction lists |
| `cam(t,lon,lat,w,dur=3.0,mode='move')` | 176 | append `(t, lon, ym(lat), w, dur, mode)` |
| `ev(typ,t0,t1,**kw)` | 177 | append event dict `{type,t0,t1,**kw}`; returns it |
| `dip(t)` | 178 | `ev('dip', t-0.5, t+0.5)` + `cam(t, *CUT_TARGET.pop(0), dur=0, mode='cut')` |
| `PL` | 181-182 | 8 named places (hormuz, seoul, ulsan, busan, kharg, aden, embassy, erbil) |
| `ROUTE` | 183-185 | 20 lon/lat pts Hormuz→Ulsan |
| `CHEONG` | 186-187 | 18 pts Busan→Aden |
| direction section | 190-266 | see C |
| `build_camera()` | 270-285 | per-frame (lon, v, w) array (see D) |
| `CAMS`, `TW` | 288-289 | camera array; `TW=TIERS['W']` |
| `class View` | 292-318 | per-frame viewport: `xy`, `uvs`, `visible`, `inside`, `base`, `_tier` |
| `path_rings(ctx,view,rings,min_px=1.0)` | 322-329 | add visible rings to path, skipping rings smaller than min_px; returns count |
| `draw_borders(ctx,view)` | 332-343 | country borders + admin1 dashed at close zoom |
| `RESERVED` | 346 | per-frame list of (x0,y0,x1,y1) rects that labels avoid |
| `draw_labels(ctx,view,t,la)` | 349-395 | seas / countries / admin1 / cities with LOD + collision |
| `draw_country(ctx,view,t,e)` | 398-407 | fill+3 strokes on country polygons |
| `catmull(pts,n=10)` | 410-416 | Catmull-Rom spline |
| `route_uv(pts)` | 419-420 | lon/lat → (lon, ym) then catmull n=12 |
| `glow_line(ctx,S_,col,a,w,dash=None)` | 423-429 | 3-pass glow stroke |
| `tanker(ctx,x,y,ang,a,sc=1.0)` | 432-438 | tanker glyph with radial glow |
| `draw_route(ctx,view,t,e)` | 441-456 | growing spline, optional ship head, dashed arrowhead, label |
| `draw_tanker_loop(ctx,view,t,e)` | 459-465 | 3 tankers looping on route (26 s period) |
| `draw_barrier(ctx,view,t,e)` | 468-472 | red growing line + '봉쇄' label |
| `SHIPS` / `draw_ships(ctx,view,t,e)` | 475-494 | 150 random twinkling dots in Gulf avoiding land (seed 4) |
| `icon(ctx,kind,x,y,col,a)` | 497-505 | 'boom' 10-point star (amber) or dot |
| `draw_marker(ctx,view,t,e)` | 508-523 | pulse rings + icon + label/sub; appends RESERVED |
| `draw_boom(ctx,view,t,e)` | 526-530 | 3 expanding amber rings |
| `media_frame(ctx,x,y,w,h,a)` | 534-536 | drop shadow |
| `media_caption(ctx,x,y,w,cap,credit,a,tag)` | 539-542 | 38 px caption bar |
| `media_tag(ctx,x,y,s_,a)` | 545-548 | 'PHOTO'/'VIDEO' pill |
| `draw_photo(ctx,t,e)` | 551-561 | screen-space photo with Ken Burns 7 % |
| `_CLIPSURF` / `draw_clip(ctx,t,e)` | 564-577 | video frame from npy at `int((t-t0)*FPS)` |
| `draw_article(ctx,t,e)` | 580-602 | paper "clipping" card top-right with highlight sweep |
| `draw_cutout(ctx,view,t,e)` | 605-617 | map-anchored cutout with slide/bob/tilt + label; appends RESERVED |
| `flag_wave(ctx,key,cx,cy,wdt,a,t)` | 621-627 | 14-strip sine wave flag |
| `badge_at(ctx,x,y,e,t,a)` | 630-659 | circular badge (person/flag/emblem) with ease_back pop, label/role; appends RESERVED |
| `draw_badge(ctx,view,t,e)` | 662-665 | map-anchored badge_at |
| `draw_card(ctx,t,e)` | 669-695 | right-side info card (tag/bigs/lines/src/quote) |
| `panel_title(ctx,a,s,sub=None)` | 699-701 | centred panel title/subtitle |
| `edge_curve(x0,y0,x1,y1,prog,n=36)` | 704-709 | cubic bezier partial curve for refusal panel |
| `P_refusal` | 712-734 | Trump badge → 5 flags with edges turning red at at_word('ask_1', name); two quotes |
| `P_statement` | 737-745 | 7 flags row + KR badge at at_word('ask_4','한국') |
| `TL_EVENTS` | 748-751 | 8 timeline entries `(date, label, col, side, sid|None|'END')` |
| `P_timeline` | 754-782 | horizontal axis Feb–Sep 2026, month ticks, ceasefire band, events, cursor |
| `P_precedent` | 785-801 | 4 cards 2004/2009/2020/2026 + Roh badge |
| `P_versus` | 804-818 | two columns 지지/반대 with staggered bullets |
| `PANELS` | 821 | kind→function map |
| `draw_panel(ctx,t,e)` | 824-827 | dark overlay `rgba(0.025,0.03,0.045,0.8a)` + dispatch |
| `cur_sentence(t)` | 831-835 | last sentence with `t0-0.3 <= t` |
| `in_fullcard(t)` | 838 | inside any card ±0.3 |
| `draw_date(ctx,t)` | 841-851 | date badge top-right, hidden during full cards |
| `draw_subtitle(ctx,t)` | 854-870 | wrapped subtitle with emphasis runs |
| `credit_sections()` | 873-887 | 5 credit sections (hard-coded strings; licences from REG) |
| `credits()` | 890-891 | flat string list (unused by render) |
| `draw_endcard(ctx,t,c,a)` | 894-917 | two-column credits |
| `draw_fullcards(ctx,t)` | 920-935 | title card + end card |
| `build_vignette()` / `VIG` | 938-947 | vignette surface — **built but never painted in render_frame** |
| `MAPDRAW`, `LAYER` | 948-950 | map-layer dispatch + order |
| `render_frame(i)` | 953-981 | frame composition (see C) |
| `__main__` | 984-997 | `--preview t1,t2` or `START END out.mp4` ffmpeg pipe |

Sandbox/paths: `V` (L6); `{V}/plan.json`; `{V}/assets/tiers.pkl`, `base_{n}_{lv}.png`, `geo3.pkl`, `rights_registry.json`, `portraits/{p}.png`, `emblems/navcent.png`, `flags/{c}_4x3.png`, `flags/{c}_1x1.png`; `{V}/media/media_registry.json`, `hormuz_transit_720.jpg`, `p8_cut.png`, `strikes_480.npy`, `niovi_480.npy`, `rok_iraq_720.jpg`; `{V}/prev/p_{tt:07.2f}.png`; `{V}/video_noaudio.mp4`. Binary: `ffmpeg`. Font family names assume fontconfig-installed fonts (`IBM Plex Sans KR[ Medium| SemiBold]`, `GmarketSansBold/Medium`, `IBM Plex Mono SemiBold/Medium`, `Noto Serif CJK KR`). Flag list hard-coded: `kr us ir cn in de gb jp au fr it nl ca`. Portrait ids hard-coded. Media keys hard-coded. `credit_sections()` content is story-specific.

### A.4 `mix3.py` (module-level script, no `main`)

| Name | Lines | Purpose |
|---|---|---|
| consts | 4-8 | `V`, `SR=44100`, `TOT=P['total']+0.5`, `N=int(TOT*SR)`, `rng=default_rng(3)`, `BGM='/home/claude/og/hyperframes/briefing/assets/audio/bgm/The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3'` |
| bed load/loop | 9-19 | ffmpeg f32le stereo decode; loop with 4 s linear crossfade until ≥N; peak-normalise |
| intensity `K` | 24-26 | keyframes `(0,.6),(route,.62),(war,.74),(ask,.6),(timeline,.66),(cost,.7),(review,.6),(past,.55),(debate,.66),(decision,.72),(now,.66),(TOT-7,.62),(TOT,0)` |
| VO + duck | 28-34 | each sentence npy normalised to 0.8 peak at t0; duck mask t0−0.25…t1+0.3 smoothed by 0.35 s box; `bed_gain = inten*(1-0.5*duck)*0.47` |
| `add(t,y)` | 39-42 | mix into fx at t |
| `whoosh(t_end,dur=1.2,v=1.0)` | 45-50 | filtered-noise rise ending at t_end, gain 0.2*v |
| `boom(t,v=1.0)` | 53-57 | 2.6 s sine sweep 78→34 Hz + LP noise |
| `tick(t,v=1.0)` | 60-62 | 1800 Hz 0.12 s blip — **defined, never called** |
| placement | 65-69 | title: `whoosh(t0+0.2,1.4,1.0)` + `boom(t0+0.2,0.6)`; each scene except open: `whoosh(t0-0.05,0.9,0.55)`; `boom(S['war_0'].t0+1.2, 0.5)` |
| master | 70-77 | fade in 1.2 s / out 4 s; `L/R = bg*bed_gain + fx*(1-0.25*duck) + vo`; limit peak to 0.97; writes `{V}/mix.f32` (float32 interleaved stereo) |

Sandbox: `V`, `BGM` path (repo path under `/home/claude/og`), `{V}/plan.json`, sentence `npy` paths from plan.json (absolute sandbox paths). Binary: `ffmpeg`.

### A.5 `media3.py` (module-level script)

| Name | Lines | Purpose |
|---|---|---|
| consts | 5-6 | `V`, `UA 'osint-video-trial/0.4 (research)'`, `C=json.load({V}/data/media_candidates.json)` |
| `pick(k, sub)` | 7 | first candidate in `C[k]` whose title contains `sub` |
| `get(url, dest)` | 8-13 | download, 5 attempts, sleep `5+5a`, timeout 120 |
| `thumb_url(c, w)` | 14-16 | Commons imageinfo thumburl at width w |
| photo | 18-24 | `hormuz_navy`/'230508' → thumb 1280 → cover-crop 720×450 → Color 0.82, Contrast 1.06 → `hormuz_transit_720.jpg` q92 |
| cutout | 25-33 | `p8`/'9341123' → thumb 960 → rembg `isnet-general-use` → crop alpha>40 → width 360 → `p8_cut.png` |
| video | 34-40 | `hormuz_video`/'Retaliatory Strikes' → original webm → ffprobe duration; writes `media_registry.json` |
| contact sheet | 41-50 | 12 thumbnails 320×180 via ffmpeg `-ss` → sheet 1280×860 bg (30,30,36) → `{V}/prev/media_sheet.jpg` |

`media3b_round2.md` (manual round 2): zaytun photo `Southkoreansoldiersiraq.jpg` (PD 2003) → `rok_iraq_720.jpg` (same crop/tone); Niovi seizure webm (PD 2023-05-03) segment 28.0–33.0 s; extraction command: `ffmpeg -ss 28.0 -t 5.0 -i media/niovi.webm -vf "scale=480:270,fps=24" -f rawvideo -pix_fmt rgb24 media/niovi_480.rgb` → `np.fromfile(...).reshape(-1,270,480,3)` → `niovi_480.npy`; strikes: `-ss 1.5 -t 5.0` → `strikes_480.npy`. Commons 429 handling: wait 60–90 s, 15 s between requests; artist template pollution cleaned to 'U.S. Government (PD-USGov)'. Article cards have no asset (rendered by `ev('article', …)`).

### A.6 JSON structures

`plan.json` top-level: `sentences[45]`, `cards[2]`, `scene_start{11}`, `total` (292.4369), `voice`, `title`, `subtitle`, `date`. Sentence keys: `sid, scene, date, text, tts, segments[[str, 0|1]...], mp3, npy, dur, t0, t1` (mp3/npy are absolute sandbox paths). Cards: `{kind:'title', t0:20.27, t1:25.87}`, `{kind:'end', t0:280.94, t1:291.94}`. scene_start: open 1.2, route 26.27, war 49.20, ask 69.56, timeline 110.89, cost 149.31, review 161.79, past 186.63, debate 211.45, decision 242.55, now 255.11.

`media_registry.json`: `{key: {kind: photo|cutout|video, title, license, author, date, url, caption, file_note, [duration]}}`; keys hormuz_transit, p8, strikes, rok_iraq, tanker (CC BY 4.0 — unused in render3), niovi.

`rights_registry.json`: `{people: {pid: {src: repo_library|wikimedia_commons, license, artist, url, [title]}}, emblems: {navcent: {license, url, title, restrictions}}}`.

---

## B. External dependencies

**Python third-party** (by file): `numpy` (all); `cairo` = pycairo (render3); `PIL` Pillow (prep3, render3, media3: Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance); `shapely` (prep3: shape, box, Point, unary_union[imported, unused]; render3 lazy: Point, prepared.prep, Polygon); `scipy.signal.lfilter` (mix3); `edge_tts` (plan3, lazy); `requests` (plan3, lazy, ElevenLabs only); `fontTools.ttLib.TTFont` (prep3, lazy); `rembg` (prep3 `u2net_human_seg`, media3 `isnet-general-use`; lazy); `cairosvg` (prep3.flags, lazy). Stdlib: json, os, re, sys, asyncio, hashlib, subprocess, math, pickle, time, io, glob, urllib.request/parse, base64, datetime.date.

**External binaries**: `ffmpeg` (plan3 decode mp3→s16le; render3 encode; mix3 decode BGM; media3 thumbnails/extract), `ffprobe` (media3), `fc-cache`, `fc-list` (prep3). Fontconfig must see `~/.fonts`; `Noto Serif CJK KR` is assumed pre-installed (never downloaded).

**External data/URLs**:
- Natural Earth 10m: admin_0_countries, admin_1_states_provinces, populated_places (GeoJSON, local files)
- Terrarium terrain tiles z5 (W) / z7 (G,K) as `{x}_{y}.png` (AWS Terrain Tiles per credits) — local dirs
- `https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsanskr/IBMPlexSansKR-{Regular,Medium,SemiBold,Bold}.ttf`, `.../ibmplexmono/IBMPlexMono-{Medium,SemiBold}.ttf`
- `https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSans{Bold,Medium}.woff`
- `https://commons.wikimedia.org/w/api.php` (imageinfo; prep3 + media3)
- `https://raw.githubusercontent.com/lipis/flag-icons/main/flags/{1x1|4x3}/{c}.svg`
- `https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps`
- Repo (`/home/claude/og`): `assets/library/library_manifest.json`, `assets/library/workshop/references/photo_manifest.json`, portrait variant paths, BGM mp3
- `{V}/data/commons_v3.json`, `{V}/data/media_candidates.json` (pre-generated Commons search results; generator lives in docs 04/07, not here)

---

## C. Direction layer (render3.py L189-266)

### C.1 Camera keys (10 total: 5 cuts, 5 moves)

| # | Line | Call | Anchor | Target (lon, lat, w) | dur | mode |
|---|---|---|---|---|---|---|
| 1 | 192 | `cam(0, 127.35, 36.35, 6.4, 0, 'cut')` | t=0 | Korea | 0 | cut |
| 2 | 198 | `cam(title['t0']+2.9, *CUT_TARGET.pop(0), dur=0, mode='cut')` | title card +2.9 | (57.6, 25.3, 24) | 0 | cut (hidden under `dip under=True` at title+2.4…+3.4) |
| 3 | 201 | `cam(S('route_1',-0.6), 88.5, 19.5, 90, 3.4)` | route_1 −0.6 | Indian Ocean wide | 3.4 | move |
| 4 | 206 | `cam(S('war_0',-1.2), 54.8, 27.0, 14.0, 3.4)` | war_0 −1.2 | Gulf | 3.4 | move |
| 5 | 222 | `cam(SC('cost')-1.0, 52.4, 27.2, 13.5, 3.0)` | cost −1.0 | Gulf | 3.0 | move |
| 6 | 226 | `dip(SC('review')-0.55)` | review −0.55 | (88.5, 21.5, 92) | 0 | cut |
| 7 | 234 | `dip(SC('debate')-0.55)` | debate −0.55 | (127.0, 37.45, 3.4) | 0 | cut |
| 8 | 239 | `cam(SC('decision')-0.8, 127.35, 36.6, 6.4, 3.2)` | decision −0.8 | Korea | 3.2 | move |
| 9 | 244 | `dip(SC('now')-0.55)` | now −0.55 | (88.5, 19.5, 90) | 0 | cut |
| 10 | 251 | `cam(S('now_3',-0.5), 90, 20, 96, 9.0)` | now_3 −0.5 | slow widen | 9.0 | move |

`CUT_TARGET = [(57.6,25.3,24), (88.5,21.5,92), (127.0,37.45,3.4), (88.5,19.5,90)]` consumed in order by L198 then the three `dip()` calls.

### C.2 Events (48 total)

| Type | Count | Lines & anchors |
|---|---|---|
| marker | 8 | 194 `S('open_0',.2)→SC_END('open')` seoul; 200 `S('route_0',.1)→SC_END('route')` hormuz; 209 `S('war_0',1.2)→E('war_0',.5)` kharg icon=boom side=left; 211 `S('war_2',0)→SC_END('war')` hormuz; 228 `S('review_0',4.6)→SC_END('review')` aden side=bottom; 235 `S('debate_1',.2)→SC_END('debate')` embassy; 240 `SC('decision')→SC_END('decision')` seoul; 250 `SC('now')→TOTAL` hormuz |
| badge | 8 | 195 `S('open_0',.6)→SC_END('open')` person lee R34 flag kr (125.05,37.25); 204 `E('route_3',-.5)→SC_END('route')` flag kr R18 '울산' (127.0,31.3); 210 `S('war_1',.2)→E('war_1',.8)` person khamenei R32 accent ru (57.6,29.35); 214 `S('war_3',1.6)→SC_END('war')` flag cn R17 (59.4,23.35); 215 `S('war_3',2.0)→…` flag in R17 (60.9,23.35); 229 `S('review_0',.3)→SC_END('review')` flag kr R18 '부산에서 출항' (125.6,22.3); 241 `S('decision_0',.4)→SC_END('decision')` person lee R34; 247 `S('now_0',.2)→TOTAL` emblem navcent R28 accent us (61.8,20.2) |
| card | 7 | 196 `S('open_1',.1)→E('open_2',.6)` lines; 203 `S('route_1',.5)→E('route_2',.7)` bigs 61%/54% src; 224 `S('cost_0',.4)→SC_END('cost')-.2` lines accent ru; 230 `S('review_1',0)→E('review_2',.6)` lines accent teal src; 242 `S('decision_0',.8)→SC_END('decision')-.1` quote=True; 248 `S('now_0',.5)→E('now_1',.4)` bigs 10억 배럴 accent us; 249 `S('now_2',.1)→E('now_2',.8)` bigs 61% |
| panel | 5 | 217 `SC('ask')-.2→E('ask_3',.5)` refusal; 218 `S('ask_4',-.3)→SC_END('ask')` statement; 220 `SC('timeline')-.2→SC_END('timeline')` timeline; 232 `SC('past')-.2→SC_END('past')` precedent; 237 `S('debate_2',-.3)→SC_END('debate')` versus |
| route | 4 | 202 `S('route_1',.6)→SC_END('route')` pts=ROUTE grow=`E('route_3',-.4)-S('route_1',.6)` col gold ship=True; 213 `S('war_3',.2)→SC_END('war')` 3 pts grow 1.8 teal dashed label '허가받은 배만 통과'; 227 `S('review_0',.3)→SC_END('review')` pts=CHEONG grow 4.5 teal ship=True; 245 `SC('now')-.2→TOTAL` pts=ROUTE grow .01 gold glow_only |
| dip | 4 | 198 `title.t0+2.4→+3.4` under=True; 226/234/244 via `dip()` (±0.5 around anchor, drawn on top) |
| article | 2 | 236 `S('debate_0',.3)→E('debate_0',1.0)` Korea Herald 2026.09.07 hl '재조정'; 259 `S('review_0',.3)→E('review_0',.9)` Reuters 2026.09.04 hl '결정된 것은 없다' |
| clip | 2 | 255 `S('war_2',.2)→+5.0` niovi x40 y150 w300; 263 `S('timeline_4',.3)→+5.0` strikes x207 y112 w440 |
| photo | 2 | 257 `S('past_1',.6)→E('past_2',.2)` photo_rok_iraq x292 y138 w280; 261 `S('now_0',1.0)→E('now_1',.4)` photo_hormuz x560 y196 w262 |
| country | 1 | 207 `S('war_0',.1)→SC_END('war')` codes ['IR'] col ru a=0.07 |
| boom | 1 | 208 `S('war_0',1.2)→S('war_0',3.4)` kharg |
| barrier | 1 | 212 `S('war_2',.3)→SC_END('war')` p0 (56.28,27.05) p1 (56.42,26.28) |
| ships | 1 | 223 `S('cost_0',.2)→SC_END('cost')` |
| tanker_loop | 1 | 246 `SC('now')→TOTAL` pts=ROUTE |
| cutout | 1 | 265 `S('review_1',.1)→E('review_2',.4)` cut_p8 at (112.0,12.5) w150 |

`at_word` is used only inside panels: `at_word('ask_1', nm)` (P_refusal), `at_word('ask_4','한국')` (P_statement), `at_word('past_3','호르무즈')` (P_precedent).

### C.3 Layer order in `render_frame(i)` (L953-981), verbatim sequence

```
1  t = i/FPS; view = View(i); RESERVED.clear()
2  im = view.base()  -> PIL RGB (tier W, blended with G/K)  -> cairo FORMAT_RGB24 surface (BGRX bytes)
3  act = [e for e in EV if e.t0-0.05 <= t <= e.t1+0.05]
4  panel_a = max(window(t, panel.t0, panel.t1, 0.6, 0.6) over active panels, 0)
5  draw_borders(ctx, view)
6  for L in LAYER = ['country','ships','route','tanker_loop','barrier','boom','cutout','marker','badge']:
       for e in act: if e.type == L: MAPDRAW[L](ctx, view, t, e)
7  if panel_a < 0.99: draw_labels(ctx, view, t, la = 1 - panel_a)     # after markers so RESERVED is populated
8  dip events with under=True: paint black 0.93 * sin(pi * progress)
9  panel events: draw_panel (dark overlay + P_* function)
10 photo / clip events: draw_photo / draw_clip
11 card / article events: draw_card / draw_article
12 draw_date(ctx,t); draw_fullcards(ctx,t); draw_subtitle(ctx,t)
13 dip events without under: paint black 0.93 * sin(pi * progress)
14 global fade: fa = 1 - min(smooth(t/1.2), smooth((TOTAL-t)/1.6)); paint black fa
15 surf.flush(); return (surf, buf)
```
`VIG` (vignette) is never composited. Subtitles are drawn after full cards (so they appear over the title card region if timing overlaps; in practice no sentence overlaps cards).

---

## D. Time-anchor & camera API

| Function | Signature | Semantics |
|---|---|---|
| `S` | `S(sid, off=0.0)` | `SENT[sid]['t0'] + off` |
| `E` | `E(sid, off=0.0)` | `SENT[sid]['t1'] + off` |
| `SC` | `SC(scene)` | `scene_start[scene]` |
| `SC_END` | `SC_END(scene)` | start of next scene − 0.35; `TOTAL` for last |
| `at_word` | `at_word(sid, word)` | `t0 + max(0, text.find(word)) / len(text) * dur` — linear char-proportional estimate over subtitle text (not TTS alignment) |
| `cur_sentence` | `cur_sentence(t)` | last sid with `t0 - 0.3 <= t` |
| `in_fullcard` | `in_fullcard(t)` | any card with `t0-0.3 <= t <= t1+0.3` |
| `clamp01` | `clamp01(x)` | clamp |
| `smooth` | `smooth(x)` | smoothstep `x²(3−2x)` on clamped x |
| `ease_io` | `ease_io(x)` | cubic in-out: `4x³` if x<.5 else `1−(−2x+2)³/2` |
| `ease_out` | `ease_out(x)` | `1−(1−x)³` |
| `ease_back` | `ease_back(x)` | overshoot, c=1.7: `1+(c+1)(x−1)³+c(x−1)²` |
| `window` | `window(t,t0,t1,fin=0.5,fout=0.5)` | 0 outside [t0,t1]; else `min(smooth((t−t0)/fin), smooth((t1−t)/fout))`; fin/fout=0 → 1 |

**Camera key**: `cam(t, lon, lat, w, dur=3.0, mode='move')` → tuple `(t, lon, ym(lat), w, dur, mode)`; `w` = viewport width in Mercator degrees (lon span). `dip(t)` = 1 s black dip centred at t + a `cut` to the next `CUT_TARGET`.

**`build_camera()`** (L270-285): keys sorted by t. Per frame i (t=i/FPS): advance to the latest key with `t_key <= t`; on each activation set start state `frm = out[i-1]` (previous frame, incl. drift) if `mode != 'cut'` and i>0, else the key's own target (so a cut jumps instantly). `e = ease_io((t−t0)/dur)` (1.0 if dur==0). lon and v interpolate linearly; **w interpolates in log space**: `exp(log(frm_w) + (log(w) − log(frm_w))·e)`. After the move ends (`da = t − (t0+dur) > 0`) a **drift zoom-in** is applied: `w *= 1 − 0.03·(1 − exp(−da/9.0))` (asymptotically 3 % narrower, time constant 9 s). Output array shape (N,3) = (lon, v, w).

**`View(i)`** (L292-318): clamps w to `min(w, W.lon1−W.lon0−0.01, (ym(W.lat1)−ym(W.lat0)−0.01)·W_OUT/H_OUT)`; `h = w·H_OUT/W_OUT`; `s = W_OUT/w` (px per Mercator degree); `u0` clamped inside W tier; `v1` (top) clamped. `xy(lon,lat) = ((lon−u0)·s, (v1−ym(lat))·s)`; `uvs(uv)` vectorised; `visible(mn,mx)` bbox test; `inside(T, m=0.05)` view fully within tier T with margin. `base()`: `need = W_OUT/w` px/deg; start from tier W; for G then K, if `inside(T)`: `a = smooth((need−26)/18)`; if a>0.01 `Image.blend(im, tier_im, a)`. `_tier(n, need)`: pick smallest level ≥ `need·0.95` else largest; crop `box=((u0−lon0)·lv, (ym(lat1)−v1)·lv, +w·lv, +h·lv)` and `resize((854,480), BILINEAR)`. Border LOD: `fine` when `view.w < 22`. Admin1 fade: `0.3·smooth((24−w)/10)`.

---

## E. Style constants (user-approved numbers, do not change)

**FONT** (L40-42): `sans=('IBM Plex Sans KR',0)`, `sansm=('IBM Plex Sans KR Medium',0)`, `sansb=('IBM Plex Sans KR SemiBold',0)`, `sansbb=('IBM Plex Sans KR',1)`, `disp=('GmarketSansBold',0)`, `dispm=('GmarketSansMedium',0)`, `mono=('IBM Plex Mono SemiBold',0)`, `monom=('IBM Plex Mono Medium',0)`, `serif=('Noto Serif CJK KR',0)`, `serifb=('Noto Serif CJK KR',1)`. Second element = cairo BOLD flag.

**C colours** (L36-37): `ru #ff5566`, `us #5aa9ff`, `gold #e8b860`, `teal #5cc8da`, `green #8fd08a`, `muted #a9b0bd`, `amber #ffb347`, `white (1,1,1)`, `kr #e8b860`, `water #7fc4ff`. Halo colour `(0.02,0.03,0.05)` alpha `halo_a·a` (default 0.8). Sea label colour `#9cc8e6`. Badge inner `#1b2a3a`. Article paper `(0.95,0.935,0.905)`, ink `(0.1,0.105,0.12)`, grey `(0.38,0.39,0.42)`, highlight `(1.0,0.8,0.3,0.55)`.

| Element | Numbers |
|---|---|
| Canvas | 854×480, 24 fps |
| Subtitle | size 19, font sansm (emphasis sansb gold), wrap 700 px, baseline `452 − (nlines−1)·26`, line height 26, halo 5.0, halo_a 0.92; visible `t0−0.05 … t1+0.25`; fade in 0.18 s, out 0.2 s |
| Date badge | mono 15, right at x=W−26, y=`40 − (1−k)·6`, alpha 0.95·k, `k=smooth((t−t_change)/0.45)`, halo 3; gold underline y=48 h=1.4 alpha 0.9 grows with k; text `'.'→'. '` if len>4; hidden during full cards |
| Marker | window 0.35/0.5; 2 pulse rings `r=4+20·ease_out(f)`, `f=(lt·0.5+k/2)%1`, alpha 0.5(1−f), lw 1.3; dot r 3.3 white + black 0.6 stroke lw 1; boom star radii (9,4)/(6,3) amber; label 13 sansb white halo 3.2; sub 10.5 sansm gold halo 3 at +15; offsets right(12,4) left(−12,4) top(0,−14) bottom(0,22); label alpha `smooth((lt−0.2)/0.4)`; colour gold if hl else white |
| Badge | R default 30 (used 17/18/19/24/28/30/32/34/36); pop `ease_back(lt/0.55)`; shadows (R+7, .10),(R+4, .18) offset (1.5,3); person flag_wave width R·2.3 at (R·0.25, −R·0.05) alpha .92; flag 1x1 width R·2.1; emblem bg (0.96,0.96,0.97) img R·1.96; portrait width R·1.72, clip circle ∪ rect(−R·.66, −R·2.4, R·1.32, R·2.4), y = R−ph+R·0.02; ring black (0.03,0.04,0.06) lw 3.2 then accent lw 1.5 alpha .92; label alpha `smooth((lt−0.3)/0.35)`; side=right: label 13 sansb at (x+R·k+10, y+1), role 10 sansm accent at +17; else pill (w+16)×20 r3 bg (0.03,0.04,0.06,0.84) label 12 sansb at y+R·k+19.5, role 10 sansm at y+R·k+38; draw_badge window 0.01/0.45 |
| flag_wave | 14 strips; `dy = sin(t·2.6 + i·0.5)·wdt·0.032`; shade alpha `0.16·(0.5+0.5·sin(t·2.6+i·0.5+1.2))` |
| Card | window 0.45/0.45; slide 30 px over 0.55 s ease_out; min width 230; padding 44; tag 10.5 sansb accent spacing 0.4 at (+18,+23); bigs 30 disp white + caption 11 sansm muted, block h 62, gap 26; lines 13 sansm (serifb if quote) colour (0.94,0.92,0.9) pitch 21 starting yy+17; src 9.5 sans muted alpha .9 at y+h−12; `h = 42 + bh + 21·nlines + (18 if src)`; x = W−wdt−24+slide; y default 70; bg (0.05,0.06,0.09,0.86) r5; accent bar 3 px at (x, y+10, h−20) |
| Panel | overlay (0.025,0.03,0.045, 0.8·a); window 0.6/0.6; title 19 serifb centred y=74; sub 11 sansm muted y=96; labels fade by `1−panel_a` |
| Borders | fine if w<22; colour (0.82,0.86,0.92) alpha .36 (w<40) / .26; lw 0.75; admin1 dash [2.5,2.5] colour (0.8,0.84,0.9) lw 0.55 alpha `0.3·smooth((24−w)/10)` min_px 2 |
| Labels | seas serif 11 (w>30) / 12, alpha .62, spacing 2.2, no halo, per-sea w range; country rank thr 2/4/6/9 for w>60/>30/>12/else, skip KR at w<12, 12 (w>30)/13 sansm (0.9,0.92,0.96) alpha .55 halo 2.2 spacing 1.8, margins x 30, y 60..H−70; admin1 (w<8.5, KR/KP only) 9.5 sans (0.78,0.82,0.88) alpha .42 halo 1.8; cities rank ≤ 1/2/4/6/8 for w>60/>25/>12/>5/else (capitals rank ≤ rk+2), margins 12/58/72, top 40 by (rank, −pop), max 18 drawn, dot r 2.4 cap / 1.9, dot (0.95,0.96,0.98) alpha .9 + black .6 lw .8, text 11.5 sansb (cap) / 10.5 sansm at (+5,+4) colour (0.93,0.94,0.97) alpha .82 halo 2.6 |
| Country fill | window 0.8/0.6; fill alpha `e['a']` (0.07 used); strokes (6,.07),(2.6,.2),(1.1,.85); even-odd |
| glow_line | passes (w·4.5,.08),(w·2.2,.22),(w,.95); round cap/join |
| Route | window 0.35/0.6; line w 1.9; dash [5,4]; glow_only alpha ×0.75; catmull n=12; label 11.5 sansb halo 3 at mid y−11 after grow; arrowhead 9 px for dashed |
| Tanker glyph | glow radial r15 (1,0.85,0.5,.45a); hull (9,0)(5,−3)(−8,−3)(−8,3)(5,3) white, black .5 lw .6; bridge rect (−7,−2,3,4) (0.2,0.25,0.3) |
| Tanker loop | 3 ships, period 26 s, phase k/3, scale .85, alpha .95; window 0.6/0.6 |
| Barrier | window 0.4/0.5; grow ease_out(lt/0.8); ru lw 3.2; '봉쇄' 12.5 sansb ru halo 3 anchor r at mid (−12,+4) when k>.95 |
| Ships | 150 pts lon 48.3–56.2 lat 24.2–29.9, seed 4, land-avoid on GEO['fine']; appear after ph·1.6 s; r 1.7 colour (1,.82,.5) alpha `.85·a·(0.6+0.4·sin(2t+9ph))`; window 0.8/0.6 |
| Boom | window 0.05/0.8; 3 rings `r=6+50·ease_out((lt−k·0.12)/1.2)` amber alpha `.6·a·(1−clamp01(lt/1.6))` lw 2 |
| Media frame | shadows (6,.10),(3,.18) offset (+2,+4) r 4+d; border white .22 lw 1 |
| Media caption | bar h 38 bg (0.04,0.05,0.07,.9); caption 10.5 sansm at (+10,+16); credit 7.8 monom muted ×.95 at (+10,+30) |
| Media tag | 7.5 mono gold spacing .8; pill at (+8,+8) (w+12)×14 r2 bg (0.02,0.03,0.05,.75) |
| Photo | window 0.5/0.5; drop-in 12 px over 0.6 s; h = w·0.625; Ken Burns scale 1+0.07·progress, offset (−(fw−w)·.35, −(fh−h)·.5) |
| Clip | window 0.35/0.45; frame idx `int((t−t0)·FPS)` clamped; h from array aspect (270/480) |
| Article | window .45/.45; w 300; x = W−300−24 + slide 30 over .55 s; y 68; headline 13.5 serifb wrap w−32 pitch 20 from y+54; sub 9.5 sans pitch 14 after +4; h = 44+20·nh+6+14·ns+24; shadows (6,.12),(3,.2) r 3+d; pub 12.5 serifb at (+16,+25); date 8.5 monom right; rule y+33 h .8 alpha .35; highlight `hk=ease_io((lt−0.8)/0.7)` rect (x0−2, yy−12, (ww+4)·hk, 16); 'ARTICLE' 7.5 mono spacing .8 at y+h−11; note 7.8 sans right |
| Cutout | window .6/.5; slide −40 px over 1.2 s; bob sin(1.3t)·2.2; tilt −0.04+0.015·sin(0.9t); shadow ellipse alpha .25 at (6,14) sy .25 r fw·.36; label 12 sansb halo 3 at +fh/2+16; sub 8.5 monom muted halo 2.4 at +30; label alpha smooth((lt−.5)/.4) |
| Title card | window .7/.7; gradient (0,.86),(.5,.7),(1,.92) colour (0.01,0.015,0.03); title 46 disp y `232−(1−k)·10` k=ease_out(lt/1.0) alpha smooth((lt−.1)/.6); gold rule 220×1.6 at y 254 grows ease_io((lt−.5)/.9) alpha .95; subtitle 18 serifb (0.92,0.9,0.88) y 290 alpha smooth((lt−.8)/.6); date 12 mono gold y 322 alpha smooth((lt−1.1)/.6) |
| End card | bg (0.018,0.022,0.032,.94); 'SOURCES  &  CREDITS' 8.5 mono gold spacing 2.4 at (64,84); '자료 및 출처' 17 serif (0.96,0.95,0.93) spacing 1.0 at (64,110); gold rule 36·k×1.1 y 122; rule alpha .08 y 140 width W−128; columns x 64 / 456 from y 158; section placement [0,0,1,0,1]; header 8.5 sansb gold spacing 1.4 alpha .9, +15; item 9.2 sans (0.86,0.87,0.9); licence 7.8 monom muted, row 23 (with licence) / 14; section gap +10; stagger .18/section, .03/item; footer alpha smooth((lt−1.6)/.8), rule at H−44, date 7.8 monom spacing .6, disclaimer 7.8 sans right at H−26 |
| Dip | black alpha `0.93·sin(π·progress)` over 1.0 s |
| Global fade | in 1.2 s, out 1.6 s |
| Vignette (unused) | radial H·.36→W·.72 alpha 0→.55; bottom 110 px 0→.55; top 80 px .4→0 |
| P_refusal | trump badge (235,262) R36 at t0+.4; flags x 590, y 138+62i, R19, t0+1.0+.2i; edge start 2.2+.75i, ease_io/1.3, lw 1.5, alpha .8−.25·red, dash [4,4] when red>.5; '거절' 12 sansb ru at (fx+78, fy+5); caption '해협 방어 참여 요구' 11 sansb gold (400,150) after 3.2 s; quote A 13 serifb (W/2,414); quote B 12.5 serifb us at (ux, uy+92) |
| P_statement | 7 flags x 110+92i y 230 R24 t0+.5+.22i; KR badge (W/2,345) R30; dashed gold line y 292 x 110…W−190 dash [3,4] lw 1 alpha .5 |
| P_timeline | X0 80, X1 774, Y 262; range 2026-02-01…2026-09-30; axis ease_io(lt/1.2) lw 1.4 alpha .35; month tick 1×8, label 10.5 sansm muted at (+3, Y+22); ceasefire band 04-08…07-08 green .18 h 14 + label 10.5 sansm at Y+40; stem 44 (|side|=1) / 96 (|side|=2) lw 1.2; dot r 4.5; date 11 mono; label 11.5 sansb; END alpha .55 at t1−3.0; cursor gold dash [2,3] y 118…400 alpha .35 |
| P_precedent | cards x 58+190i, y 150 (rise 16), 172×212 r6 bg (0.07,0.08,0.12,.92), top bar 3; year 28 disp; title 14 sansb at +68; lines 11.5 sansm muted pitch 20 from +96; Roh badge (x+136,y+172) R24; name 10.5 sansb teal at +196 |
| P_versus | columns x 60 / 450, y 120, 344×262 r6; title 16 sansb (+22,156); bullets r3 at x+26; items 13.5 serifb at (x+38, 196+50i); src 10 sans muted (x+22,366); col alpha smooth((t−first_item+.6)/.5) |

---

## F. Rendering pipeline mechanics

- Resolution 854×480, FPS 24, `N = int(total·24)`. Frame surface: PIL base → `tobytes('raw','BGRX')` → `cairo.ImageSurface.create_for_data(buf, FORMAT_RGB24, 854, 480, 854·4)`; buffer written to ffmpeg as-is.
- ffmpeg (L991-992): `ffmpeg -y -v error -f rawvideo -pix_fmt bgr0 -s 854x480 -r 24 -i - -c:v libx264 -preset faster -crf 19 -pix_fmt yuv420p -g 48 OUT`.
- Chunking: `python render3.py START END [out.mp4]` renders frames `[START, END)` (defaults 0, N; out `{V}/video_noaudio.mp4`); progress print every 480 frames. Chunks are concatenated externally (not in this dir).
- Preview: `python render3.py --preview t1,t2,...` → frame `min(N−1, int(t·FPS))` → `{V}/prev/p_{t:07.2f}.png`.
- Random seeds: `draw_ships` `default_rng(4)` (lazy, cached in global `SHIPS`); mix3 `default_rng(3)`. No other randomness.
- Caches: `_SC` scaled-surface cache keyed (key, width quantised to 3 px); `e['uv']` memoised on route events; `_CLIPSURF['last']` holds clip buffer alive; `RESERVED` cleared per frame.
- Audio mux happens separately (`mix.f32` float32 stereo 44.1 kHz + video_noaudio.mp4).

---

## G. `plan3.py` details

**lint()** rules: (1) each `BANNED` regex searched in subtitle `text`; (2) TTS text (`tts or text`) must not match `[0-9%~/:→()\[\]]`; (3) each emphasis string must be a substring of subtitle text.

**BANNED verbatim**:
```
r'가지.{0,8}(화살|문제|흐름).{0,12}모인다', r'한\s?번에 흔들', r'세\s?겹', r'방향을 정한다', r'같은 자리로 돌아',
r'로 읽으면', r'승부는', r'진짜 뉴스', r'계약서에', r'서 있는 자리', r'만 보면', r'로 읽힌다', r'말하지 않는 것',
r'이것이 바로', r'핵심은 .{0,10}(이다|입니다)$'
```

**TTS backends**: edge-tts `Communicate(text, 'ko-KR-InJoonNeural', rate='-3%', pitch='-2Hz').save(path)`, 4 attempts, valid if >1000 bytes, concurrency `Semaphore(5)`. ElevenLabs: POST `/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/with-timestamps`, header `xi-api-key`, timeout 120, json `{text, model_id (env ELEVENLABS_MODEL_ID or 'eleven_multilingual_v2'), previous_text, next_text, voice_settings{stability .65, similarity_boost .8, style .1}}`; saves base64 audio + `alignment` to `path.align.json`. Selected when both `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` set; ElevenLabs calls are sequential (not async).

**Cache key**: `sha1(tts_text + ('|el|' + VOICE_ID if eleven else '')).hexdigest()[:10]`; file `{V}/tts/{sid}_{hash}.mp3`; skip synth if exists and >1000 bytes. `sid = f'{scene}_{index_within_scene}'`.

**Segments**: emphasis strings split subtitle into `[text, flag]` runs (first occurrence only, non-nested).

**Trim**: ffmpeg → s16le mono 44100 → float; keep from `first |a|>0.012 − 0.03 s` to `last |a|>0.012 + 0.12 s`; 10 ms linear fade in/out; save `.npy`; `dur = len/SR`.

**Timeline**: `t = LEAD (1.2)`; on scene change: if previous scene was `'open'` → title card `t0 = t+0.2, t1 = t0+5.6`, then `t += 5.6+0.6`; else `t += SCENE_GAP (1.0)`; record `scene_start[scene]=t`. Each sentence `t0=t, t1=t+dur, t = t1 + GAP (0.5)`. After last: `t += 1.2`; end card `[t, t+11.0]`; `total = t + 11.0 + 0.5`.

**plan.json fields**: `sentences[{sid, scene, date, text, tts, segments, mp3, npy, dur, t0, t1}]`, `cards[{kind, t0, t1}]`, `scene_start{}`, `total`, `voice`, `title`, `subtitle`, `date`.

---

## H. `prep3.py` details

**TIERS**: `W: lon 28→140, lat −12→48, ppd 24, tiles t5, z 5`; `G: lon 46→62, lat 20.5→32.5, ppd 96, tiles tg, z 7`; `K: lon 122.5→131.8, lat 32.3→39.8, ppd 96, tiles tk, z 7`. After `build_tier`, `T['levels'] = [ppd, ppd//2, ppd//4]` (W: 24,12,6; G/K: 96,48,24). Geometry bbox `box(20,−20,150,60)`.

**build_tier**: `S = 256·2^z`; `W = round((lon1−lon0)·ppd)`, `H = round((ym(lat1)−ym(lat0))·ppd)`; elevation resampled with `Image.EXTENT` BICUBIC from tile mosaic; `mpp = 111320·cos(lat_row)/ppd`; ring simplify tol `0.02` (ppd<64) / `0.003`; land mask via ImageDraw polygons (255) → GaussianBlur 0.6 → /255; **coverage check**: for every country whose `representative_point()` falls in the tier, mask pixel must be ≥128 else reported in `land-miss`; vertical exaggeration `2.8` (ppd<64) / `2.0`; hillshade azimuth 315°, altitude 42°, `hs = clip(sin(alt)cos(slope) + cos(alt)sin(slope)cos(az−aspect), 0, 1)`.

**Palette**: land stops `(0,#2b313a),(400,#30353c),(1500,#3b3a3a),(4000,#4b4640)` × `clip(0.58 + 0.95·(hs − sin(alt)), 0.5, 1.5)`; sea (on −E) `(0,#1c4a66),(60,#18415c),(400,#11304a),(2000,#0c2236),(6000,#081626)` + coast glow `#3a9cb8 · blur(mask, 3 (ppd<64) / 8) · 0.2`; composite `sea·(1−land) + land_col·land`. Outputs `base_{name}_{ppd}.png` + 2 LANCZOS half-res levels.

**Natural Earth files**: `ne_10m_admin_0_countries.geojson` (props ISO_A2_EH, ADMIN, NAME_KO, LABEL_X, LABEL_Y, MIN_LABEL, LABELRANK), `ne_10m_admin_1_states_provinces.geojson` (iso_a2, name_ko/name, longitude, latitude), `ne_10m_populated_places.geojson` (NAME_KO, SCALERANK, FEATURECLA, ADM0CAP, ADM0_A3/SOV_A3, POP_MAX).

**polys()**: returns `[g]` for Polygon, recurses over `.geoms` for Multi*/GeometryCollection, `[]` otherwise. `rings(g, tol)` simplify → exterior + interiors float32.

**geo3.pkl**: `coarse` (tol 0.03), `fine` (tol 0.005), `meta`, `admin1` (tol 0.006, codes KR IR OM AE SA QA KW BH IQ KP JP YE), `places`, `tiers`.

**fonts()** sources: Google Fonts GitHub raw (IBM Plex Sans KR Regular/Medium/SemiBold/Bold, IBM Plex Mono Medium/SemiBold), jsDelivr `projectnoonnu/noonfonts_2001@1.1` GmarketSans Bold/Medium (woff → otf via fontTools, `flavor=None`), into `~/.fonts`, then `fc-cache -f`. Noto Serif CJK KR assumed present.

**portraits_emblems()** sources: trump, khamenei ← repo library (`library_manifest.json` `people[].variants[0].path`, licence/url from `source`, artist from `photo_manifest.json` with HTML stripped); lee_jae_myung, roh_moo_hyun ← Commons candidates `commons_v3.json` by exact title, `commons_get` at 960 px, rembg `u2net_human_seg`, alpha GaussianBlur 0.8, `mono`, `normalize_portrait` (420 wide); emblem navcent ← Commons 500 px. **Rights registry format**: `people[pid] = {src, license, artist, url, [title]}`, `emblems[key] = {license, url, title, restrictions}`.

**flags()**: extra codes au nl ca it eu from lipis/flag-icons (1x1 and 4x3); cairosvg renders `*_4x3.svg → {c}_4x3.png` 480×360, `{c}.svg → {c}_1x1.png` 256×256.

---

## I. `mix3.py` / `media3.py`

**mix3**: bed peak-normalised then `bed_gain = intensity(t) · (1 − 0.5·duck) · 0.47`; duck mask = 1 from `t0−0.25` to `t1+0.3` per sentence, box-smoothed 0.35 s; VO per sentence normalised to 0.8 peak; SFX ducked by `(1 − 0.25·duck)`. SFX synthesis: `whoosh(t_end, dur, v)` = one-pole LP noise `lfilter([0.08],[1,−0.92])` fading to HP noise, envelope `(t/dur)^2.2`, tail decay 0.05 s, gain `0.2·v`; `boom(t, v)` = 2.6 s sine sweep `f = 34 + 44·e^{−t/0.25}` decay 0.8 s ×0.55 + LP noise `[0.02],[1,−0.98]` decay 0.3 s ×0.6; `tick` unused. Placement: title `whoosh(+0.2, 1.4, 1.0)` + `boom(+0.2, 0.6)`; every scene start except open `whoosh(t0−0.05, 0.9, 0.55)`; `boom(war_0.t0+1.2, 0.5)`. Master fade in 1.2 s, out 4 s; peak limiter to 0.97; output `{V}/mix.f32` float32 interleaved stereo @44.1 kHz, length `total+0.5` s. BGM loop: 4 s linear crossfade.

**media3**: fetches and processes three round-1 assets from `media_candidates.json` (Commons): photo cover-crop 720×450 + Color 0.82 / Contrast 1.06 (q92); cutout via rembg isnet + alpha>40 crop + width 360; video original download + ffprobe duration; writes `media_registry.json`; builds a 12-thumbnail contact sheet for manual segment picking. Round 2 (md) adds rok_iraq photo and niovi/strikes 5 s 480×270@24 fps rgb24 → npy.

---

## J. Mapping v3 function → target module

| v3 function / symbol | Source | Target module | Note |
|---|---|---|---|
| `S`, `E`, `SC`, `SC_END`, `at_word`, `cur_sentence`, `in_fullcard` | render3 | `engine/timebase.py` | anchors bound to a loaded plan |
| `clamp01`, `smooth`, `ease_io`, `ease_out`, `ease_back`, `window` | render3 | `engine/timebase.py` | easing helpers |
| `ym`, `ymv`, `to_uv`, `class View` | render3 | `engine/projection.py` | split `View.base/_tier` into `engine/layers/base.py` (tier selection/blend) |
| `cam`, `dip`, `build_camera`, `CAM`, `CUT_TARGET` | render3 | `engine/camera.py` | `dip` also registers an event via `ev` |
| `ev`, `EV`, `MAPDRAW`, `LAYER`, `render_frame`, `build_vignette`, `__main__` (preview, ffmpeg pipe, chunking) | render3 | `engine/render.py` | vignette currently unused — decide keep/drop |
| `font`, `mixed_runs`, `text`, `tw`, `rrect`, `wrap`, `HANGUL` | render3 | `engine/typography.py` | |
| `fonts()` | prep3 | `engine/typography.py` | install/verify step; no natural home in layout (alt: `assets/fonts.py`) |
| `hexc` (float), `C`, `FONT`, `KO`, `SEAS`, `PL` | render3 | `engine/style.py` | `PL`/`ROUTE`/`CHEONG` are story data → move to script/direction data |
| `surf_from_pil`, `scaled`, `PIL_IMG`, `_SC` | render3 | `engine/layers/media.py` | shared surface cache; imported by badges/photo/cutout |
| `path_rings`, `draw_borders`, `BORD`, `ADM` | render3 | `engine/layers/borders.py` | |
| `draw_labels`, `RESERVED`, `PLC*` | render3 | `engine/layers/labels.py` | |
| `draw_country` | render3 | `engine/layers/areas.py` | |
| `catmull`, `route_uv`, `glow_line`, `tanker`, `draw_route`, `draw_tanker_loop`, `draw_barrier` | render3 | `engine/layers/routes.py` | |
| `draw_ships`, `draw_boom`, `SHIPS` | render3 | `engine/layers/effects.py` | |
| `icon`, `draw_marker` | render3 | `engine/layers/markers.py` | |
| `flag_wave`, `badge_at`, `draw_badge` | render3 | `engine/layers/badges.py` | `badge_at` also used screen-space by panels |
| `media_frame`, `media_caption`, `media_tag`, `draw_photo`, `draw_clip`, `draw_cutout`, `CLIP`, `MEDIA`, `_CLIPSURF` | render3 | `engine/layers/media.py` | |
| `draw_card`, `draw_article` | render3 | `engine/cards.py` | article is asset-less clipping card |
| `panel_title`, `edge_curve`, `draw_panel`, `PANELS` | render3 | `engine/panels/__init__.py` | base + registry |
| `P_refusal` | render3 | `engine/panels/refusal.py` | |
| `P_statement` | render3 | `engine/panels/statement.py` | |
| `P_timeline`, `TL_EVENTS` | render3 | `engine/panels/timeline.py` | TL_EVENTS is story data |
| `P_precedent` | render3 | `engine/panels/precedent.py` | |
| `P_versus` | render3 | `engine/panels/versus.py` | |
| `draw_date` | render3 | `engine/hud.py` | |
| `draw_subtitle` | render3 | `engine/subtitles.py` | |
| `credit_sections`, `credits`, `draw_endcard`, `draw_fullcards` | render3 | `engine/fullcards.py` | credit content must become data |
| `ym` (numpy), `TIERS`, `mosaic`, `lerp_col`, `hexc` (int), `build_tier` | prep3 | `geo/prep_tiers.py` | dedupe `ym` with projection.ymv |
| `polys`, `rings`, `load_countries`, `load_admin1`, `load_places`, `__main__` geo branch | prep3 | `geo/prep_geometry.py` | |
| `commons_get`, `mono`, `normalize_portrait`, `portraits_emblems` | prep3 | **no target module** — propose `assets/people.py` (+ `assets/commons.py` for `commons_get`) | |
| `flags` | prep3 | **no target module** — propose `assets/flags.py` | |
| `SCRIPT` (tuple list) | plan3 | `script/schema.py` | becomes Pydantic model + data file |
| `lint`, `BANNED` | plan3 | `script/lint.py` | |
| `edge_one` | plan3 | `script/tts/edge.py` | |
| `eleven_one` | plan3 | `script/tts/elevenlabs.py` | |
| `build` | plan3 | `script/timeline.py` | split: segments → schema; hash → `script/tts/cache.py`; ffmpeg decode+trim → `script/tts/trim.py`; timeline math stays |
| `add`, `whoosh`, `boom`, `tick`, module body (bed loop, intensity K, duck, master) | mix3 | `audio/mix.py` | K keyframes are story data |
| `pick`, `get`, `thumb_url`, module body, round-2 procedure | media3 / md | **no target module** — propose `assets/media.py` | |

---

## K. Functions in v1/v2 absent from v3 (porting candidates)

**v2 `render2.py`** (`v2_bundle_ratcliffe/render2.py`):
| Function | Line | One-line |
|---|---|---|
| `SEC_END(sec)` | 20 | v3 `SC_END` equivalent (−0.3 instead of −0.35) |
| `geo_rings(g, tol)` | 77 | non-recursive ring flatten (superseded by prep3.polys) |
| `arc_ev(fr, to, t0, t1, grow, **kw)` | 189 | registers arc event from `ARCS` table between two place ids |
| `marker_ev(mid, t0, t1, **kw)` | 195 | marker from place/metric table `M`/`PL` |
| `badge_ev(t0,t1,x,y,lon,lat,**kw)` | 202 | badge accepting screen (x,y) or geo anchor |
| `card(t0,t1,tag,big,lines,accent,**kw)` | 206 | card helper |
| `panel(kind,t0,t1,**kw)` | 210 | panel helper |
| `person(pid,t0,t1,**kw)` | 218 | person badge from `PERSON` table (name/role/flag) |
| `make_hatch(col,sp,wd,al)` | 419 | hatch pattern surface |
| `draw_occupied(ctx,view,t,e)` | 429 | hatched occupied-area layer (DeepState) |
| `bezier(p0,p1,n,bulge)` | 441 | great-arc-like bulged bezier in Mercator |
| `arrowhead(ctx,S_,col,a,size)` | 461 | arrowhead at polyline end |
| `plane_glyph(ctx,x,y,ang,a,sc)` | 470 | aircraft glyph with glow |
| `draw_arc(ctx,view,t,e)` | 481 | animated arc + plane |
| `draw_channel(ctx,view,t,e)` | 500 | channel/corridor line |
| `stamp(ctx,x,y,s,a,rot,col)` | 534 | rotated rubber-stamp text |
| `draw_shield(ctx,view,t,e)` | 569 | shield glyph layer |
| `prov_tag(ctx,chart,a,x,y)` | 667 | provenance/verification tag for charts (`<미검증>` handling) |
| `panel_head(ctx,a,kicker,title)` | 676 | kicker + title header (v3 uses `panel_title`) |
| `P_network` | 682 | stakeholder network graph panel (chart-driven) |
| `P_dots` | 726 | dot-matrix panel |
| `P_gantt` | 752 | gantt timeline panel |
| `P_dual` | 776 | dual line chart panel |
| `P_fork` | 822 | scenario fork panel |
| `P_check` | 840 | checklist panel |
| `draw_hud(ctx,t)` | 871 | section HUD |
| `draw_brand(ctx,t)` | 885 | '◆ OSINT BRIEFING' brand mark |
| `credits_lines()` | 919 | credits from photo_manifest |
| `draw_cards_full` | 937 | v3 `draw_fullcards` equivalent |
(`draw_flag_wave`→`flag_wave`, `draw_badge_at`→`badge_at` are renames; v2 `P_versus` is chart-driven vs v3 hard-coded.)

**v2 `plan.py`**: `fix_tts(t)` L34 — regex pronunciation fixes; `mentions(text)` L40 — alias-based entity mention detection; `build_sentences()` L50 — bundle→sentences via repo `bundle_to_video`; `synth(S)` L98 — edge/eleven dispatch (cache key `sha1(tts+'el'|'edge')`, edge rate −2%); `timeline(S)` L131 — timeline builder.

**v1 `render.py`** (`v1_ukraine_war/render.py`):
| Function | Line | One-line |
|---|---|---|
| `P200(lon,lat)` | 60 | project to level-0 (200 ppd) px |
| `rings_of(g,tol)` | 65 | ring extraction |
| `lines_of(g,tol)` | 84 | linestring extraction |
| `class Geo` | 97 | pre-projected geometry cache, 2 LODs |
| `ring_path(ctx,R)` | 224 | path from ring |
| `poly_path(ctx,view,key)` | 231 | path for keyed polygon |
| `make_hatch` | 247 | hatch pattern |
| `draw_area(ctx,view,t,e)` | 271 | area fill/hatch with fade params |
| `draw_ukraine_border(ctx,view,t)` | 303 | glowing border |
| `pts_screen(view,pts_geo)` | 322 | geo pts → screen |
| `cut_polyline(S,frac)` | 327 | cut polyline at length fraction (arc-length accurate growth; v3 uses point-count) |
| `draw_line(ctx,view,t,e)` | 342 | animated line |
| `draw_arrow(ctx,view,t,e)` | 383 | invasion arrow |
| `draw_dots(ctx,view,t,e)` | 559 | troop dots |
| `draw_particles(ctx,view,t,e)` | 580 | particle effect |
| `draw_movers(ctx,view,t,e)` | 599 | dots moving along path (ships) |
| `draw_glowline_pts` | 618 | glow polyline |
| `draw_static_labels(ctx,view,t,suppressed)` | 628 | labels with suppression (v3 `draw_labels`) |
| `draw_date_badge(ctx,t)` | 714 | date badge (v3 `draw_date`) |
| `draw_note(ctx,t)` | 844 | footnote overlay |
| `draw_tl(ctx,t,e)` | 852 | timeline scrubber/chapter card |

Notable facts for the plan: `VIG` unused; `tick` unused; `credits()` unused; `unary_union` imported unused; `at_word` is a linear estimate (ElevenLabs alignment JSON is saved but never consumed); all sandbox roots are `/home/claude/v3`, `/home/claude/data`, `/home/claude/og`, `~/.fonts`.