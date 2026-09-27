"""media3 — licensed photos/video/cutouts for the Hormuz video (Wikimedia Commons, all Public domain US gov works)."""
import json, io, os, sys, time, subprocess, urllib.request, urllib.parse, re
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
V='/home/claude/v3'; UA={'User-Agent':'osint-video-trial/0.4 (research)'}
C=json.load(open(f'{V}/data/media_candidates.json'))
def pick(k, sub): return [c for c in C[k] if sub in c['title']][0]
def get(url, dest):
    for a in range(5):
        try:
            d=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120).read(); open(dest,'wb').write(d); return True
        except Exception as e: print('retry',e); time.sleep(5+5*a)
    return False
def thumb_url(c, w):
    u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',titles=c['title'],prop='imageinfo',iiprop='url',iiurlwidth=w,format='json'))
    return list(json.load(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30))['query']['pages'].values())[0]['imageinfo'][0]['thumburl']
REG={}
# 1) photo: US Navy transit of Hormuz (file photo 2023)
c=pick('hormuz_navy','230508'); p=f'{V}/media/hormuz_transit.jpg'
if not os.path.exists(p): get(thumb_url(c,1280),p)
im=Image.open(p).convert('RGB'); w,h=im.size; tw,th=720,450
s=max(tw/w,th/h); im=im.resize((int(w*s)+1,int(h*s)+1),Image.LANCZOS); x0=(im.width-tw)//2; y0=(im.height-th)//2; im=im.crop((x0,y0,x0+tw,y0+th))
im=ImageEnhance.Color(im).enhance(0.82); im=ImageEnhance.Contrast(im).enhance(1.06); im.save(f'{V}/media/hormuz_transit_720.jpg',quality=92)
REG['hormuz_transit']=dict(kind='photo',title=c['title'],license=c['lic'],author=c['artist'] or 'U.S. Navy',date=c['date'],url=c['page'],caption='호르무즈 해협을 통과하는 미 해군 함정',file_note='자료사진 · 2023년 5월')
# 2) cutout: P-8A Poseidon
c=pick('p8','9341123'); p=f'{V}/media/p8.jpg'
if not os.path.exists(p): get(thumb_url(c,960),p)
from rembg import new_session, remove
sess=new_session('isnet-general-use')
cut=remove(Image.open(p).convert('RGB'),session=sess).convert('RGBA')
a=np.asarray(cut.getchannel('A')); ys,xs=np.where(a>40); cut=cut.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
cut=cut.resize((360,int(cut.height*360/cut.width)),Image.LANCZOS); cut.save(f'{V}/media/p8_cut.png')
REG['p8']=dict(kind='cutout',title=c['title'],license=c['lic'],author=c['artist'] or 'U.S. Navy',date=c['date'],url=c['page'],caption='해상초계기 P-8A',file_note='자료사진 · 미 해군')
# 3) video: CENTCOM retaliatory strikes (2026-07-07)
c=pick('hormuz_video','Retaliatory Strikes'); p=f'{V}/media/strikes.webm'
if not os.path.exists(p): get(c['url'],p)
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip() or 0)
REG['strikes']=dict(kind='video',title=c['title'],license=c['lic'],author=c['artist'] or 'U.S. Central Command',date=c['date'],url=c['page'],caption='미 중부사령부 공개 영상',file_note='2026년 7월 7일',duration=dur)
json.dump(REG,open(f'{V}/media/media_registry.json','w'),ensure_ascii=False,indent=1)
print('video dur',dur, os.path.getsize(p)//1024,'KB')
ims=[]
for k in range(12):
    tt=dur*(k+0.5)/12; f=f'{V}/media/vt_{k:02d}.jpg'
    subprocess.run(['ffmpeg','-y','-v','error','-ss',f'{tt:.2f}','-i',p,'-frames:v','1','-vf','scale=320:180',f]); ims.append((tt,Image.open(f)))
sheet=Image.new('RGB',(320*4,200*3+260),(30,30,36))
from PIL import ImageDraw; d=ImageDraw.Draw(sheet)
for i,(tt,im) in enumerate(ims): sheet.paste(im,((i%4)*320,(i//4)*200)); d.text(((i%4)*320+6,(i//4)*200+182),f'{tt:.1f}s',fill=(255,255,0))
ph=Image.open(f'{V}/media/hormuz_transit_720.jpg').resize((360,225)); sheet.paste(ph,(0,610))
cu=Image.open(f'{V}/media/p8_cut.png'); bg=Image.new('RGB',(400,240),(20,50,70)); bg.paste(cu,(20,(240-cu.height)//2),cu); sheet.paste(bg,(380,600))
sheet.save(f'{V}/prev/media_sheet.jpg',quality=85); print(json.dumps({k:(v['license'],v['date']) for k,v in REG.items()},ensure_ascii=False))
