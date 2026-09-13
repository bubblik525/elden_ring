"""Production color-sync renderer, adapted from the script used for the demo."""
from pathlib import Path
import numpy as np, math, subprocess, json, xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
from eldenfly.production import arguments, font
args=arguments('scene')
import mujoco
OUT=args.output
W,H,FPS=1920,1080,24;VW,VH=1240,698
BG=(9,17,20);PANEL=(12,22,26);LINE=(32,52,58);MUTED=(126,151,157);WHITE=(220,231,230);CYAN=(101,218,222);YELLOW=(245,214,99);RED=(240,97,104)
fonts={s:font(s) for s in [12,14,16,18,20,22,24,28,34]}
mono={s:font(s, mono=True) for s in [12,14,16,18,20,22,24]}
def txt(d,xy,s,size=16,c=MUTED,m=False):d.text(xy,s,font=(mono if m else fonts)[size],fill=c)
def panel(d,b):d.rectangle(b,fill=PANEL,outline=LINE)
keypts={'TAB':(1310,158),'Q':(1410,158),'W':(1507,158),'E':(1598,158),'R':(1690,158),'SHIFT':(1310,250),'A':(1410,250),'S':(1507,250),'D':(1598,250),'F':(1690,250),'CTRL':(1310,340),'SPACE':(1500,340),'LMB':(1777,218),'RMB':(1846,218)}
keynames=list(keypts)
def readkeys(a):
 on=[];scores={}
 for k,(xx,yy) in keypts.items():
  x,y=int(xx*VW/1920),int(yy*VH/1080);rx,ry=int(24*VW/1920),int(27*VH/1080)
  roi=a[y-ry:y+ry,x-rx:x+rx].astype(float);r,g,b=roi[:,:,0],roi[:,:,1],roi[:,:,2]
  mask=(r>125)&(g>125)&(b<.78*np.minimum(r,g))&(abs(r-g)<65);v=float(mask.mean())
  if k=='F':
   corner_scores=[]
   for cx,cy in [(1730,217),(1648,282),(1668,218),(1720,280)]:
    u,z=int(cx*VW/1920),int(cy*VH/1080);q=a[z-2:z+3,u-2:u+3].astype(float);rr,gg,bb=q[:,:,0],q[:,:,1],q[:,:,2]
    corner_scores.append(float(((rr>125)&(gg>125)&(bb<.78*np.minimum(rr,gg))&(abs(rr-gg)<65)).mean()))
   v=float(np.median(corner_scores))
  scores[k]=round(v,3)
  if v>.30:on.append(k)
 return on,scores

# Actual fly mesh on an articulated, illuminated keyboard.
assets=args.fly_assets.resolve()
root=ET.parse(assets/'fruitfly.xml').getroot();root.find('compiler').set('meshdir',str(assets))
visual=ET.SubElement(root,'visual');ET.SubElement(visual,'global',offwidth='640',offheight='480');ET.SubElement(visual,'headlight',ambient='.4 .4 .4',diffuse='.7 .7 .7',specular='.2 .2 .2')
wb=root.find('worldbody');ET.SubElement(wb,'geom',name='ground',type='plane',size='3 3 .1',pos='0 0 -.185',rgba='.055 .065 .067 1')
ET.SubElement(wb,'geom',name='keyboard_base',type='box',size='.235 .185 .012',pos='0 0 -.169',rgba='.025 .031 .035 1')
# rows run across the x axis, so the fly's six legs occupy the keys.
layout=[['TAB','Q','W','E','R'],['SHIFT','A','S','D','F'],['CTRL','SPACE','LMB','RMB']]
keypos={}
for row,labels in enumerate(layout):
 for col,label in enumerate(labels):
  x=(col-2)*.088;y=(row-1)*.103;z=-.143
  keypos[label]=[x,y,z]
  ET.SubElement(wb,'geom',name='key_'+label,type='box',size='.04 .045 .012',pos=f'{x} {y} {z}',rgba='.17 .19 .20 1',contype='0',conaffinity='0')
model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'));data=mujoco.MjData(model);baseq=data.qpos.copy()
renderer=mujoco.Renderer(model,330,588);camera=mujoco.MjvCamera();camera.lookat[:]=[0,0,-.065];camera.distance=.80;camera.azimuth=120;camera.elevation=-28
geomids={k:model.geom('key_'+k).id for k in keynames};smooth=np.zeros(len(keynames));keylog=[]

def flyimage(on,t):
 global smooth
 target=np.array([float(k in on) for k in keynames]);smooth=smooth*.45+target*.55
 data.qpos[:]=baseq
 for j in range(model.njnt):
  name=model.joint(j).name or '';a=model.jnt_qposadr[j]
  side='left' if 'left' in name else 'right'; leg=1 if 'T1' in name else 2 if 'T2' in name else 3
  groups={('left',1):['W','Q','E'],('right',1):['F','LMB','RMB'],('left',2):['A','SHIFT','TAB'],('right',2):['D','R'],('left',3):['CTRL','SPACE'],('right',3):['S']}
  amount=max([smooth[keynames.index(k)] for k in groups.get((side,leg),[])],default=0)
  if name.startswith('femur_T'):data.qpos[a]=baseq[a]+amount*.20
  elif name.startswith('tibia_T'):data.qpos[a]=baseq[a]-amount*.15
  elif name.startswith('coxa_abduct_T'):data.qpos[a]=baseq[a]+amount*.045
  elif name=='head':data.qpos[a]=.045*math.sin(t*2)+.04*float('F' in on)
  elif name.startswith('antenna_'):data.qpos[a]=.045*math.sin(t*5+j)
  elif name.startswith('wing_yaw'):data.qpos[a]=.38+.04*math.sin(t*6)
  elif name.startswith('wing_roll'):data.qpos[a]=.28
 for k,g in geomids.items():
  v=smooth[keynames.index(k)];model.geom_rgba[g]=[.17+.77*v,.19+.59*v,.20+.13*v,1];model.geom_pos[g,2]=keypos[k][2]-.006*v
 mujoco.mj_forward(model,data);renderer.update_scene(data,camera=camera)
 img=Image.fromarray(renderer.render().copy());dd=ImageDraw.Draw(img)
 c0,c1=renderer.scene.camera;pos=(c0.pos+c1.pos)/2;forward=c0.forward;up=c0.up;right=np.cross(forward,up);f=330/(2*math.tan(math.radians(model.vis.global_.fovy)/2))
 for k,p in keypos.items():
  if k not in ['TAB','Q','W','E','R','D','F']:continue
  pp=np.array(p)+[0,0,.014] - pos;depth=np.dot(pp,forward)
  if depth>0:
   xx=294+np.dot(pp,right)*f/depth;yy=165-np.dot(pp,up)*f/depth
   label=k;bb=dd.textbbox((0,0),label,font=fonts[12]);dd.text((xx-(bb[2]-bb[0])/2,yy-5),label,font=fonts[12],fill=(25,28,28) if k in on else (158,175,176))
 return img

ref=Image.open(args.brain).convert('RGB');a=np.array(ref);ys,xs=np.where(a.max(axis=2)>62);rng=np.random.default_rng(9);ids=rng.choice(len(xs),min(8000,len(xs)),replace=False);xs=xs[ids];ys=ys[ids];phase=rng.uniform(0,6.28,len(xs))
# Rotate the supplied projection to echo the reference's horizontal brain/cord layout.
xn=1345+(ys-140)*.59;yn=277+(xs-320)*.37
base=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(base)
txt(d,(32,26),'NEUROLINK',28,CYAN);txt(d,(238,33),'CONNECTOME  >  FLY  >  KEYBOARD  >  MALENIA',20,WHITE,True)
txt(d,(32,70),'Visual recognition / observed keyboard input / motor response',16)
d.line((32,104,1888,104),fill=LINE)
txt(d,(32,124),'01 / COMBAT FEED',16,CYAN,True);txt(d,(1040,124),'ELDEN RING',16,MUTED,True)
txt(d,(1300,124),'02 / NEURAL ACTIVITY',16,CYAN,True)
panel(d,(1300,160,1888,400));panel(d,(1300,463,1888,793));panel(d,(1300,811,1888,1018));panel(d,(32,901,1272,1018))
txt(d,(1300,432),'03 / FLY + KEYBOARD',16,CYAN,True)
txt(d,(32,1037),'INPUTS EXTRACTED FROM VIDEO / fly motion and neural activity are illustrative',14,MUTED,True)
txt(d,(1600,1037),'SYNC / COLOR V03',14,MUTED,True)
txt(d,(50,918),'SCENE UNDERSTANDING',14,CYAN,True)
txt(d,(1318,826),'OBSERVED KEYS',14,CYAN,True)
source=str(args.input)
dec=subprocess.Popen(['ffmpeg','-loglevel','error','-i',source,'-vf',f'setpts=PTS*1.2278,fps=24,scale={VW}:{VH}','-t',str(args.seconds),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE)
# Brief editorial recognition annotations, placed from inspected frames.
keys=np.array([[0,220,29,62,100],[1,203,27,78,116],[2,202,15,73,116],[3,200,57,80,115],[4,213,40,68,112],[5,153,25,102,126],[20,222,35,118,145],[43,168,115,66,80],[43.5,192,60,71,89],[44,173,21,87,102],[44.5,209,39,62,103],[45,205,7,67,115],[45.5,213,61,80,102]])
prevon=set();events=[];last=None
for n in range(args.count):
 t=n/FPS;st=t/1.2278;raw=dec.stdout.read(VW*VH*3)
 if len(raw)!=VW*VH*3:raise RuntimeError('Source ended before the requested duration')
 last=Image.frombytes('RGB',(VW,VH),raw)
 arr=np.array(last);on,scores=readkeys(arr);keylog.append({'frame':n,'time':round(t,4),'source_time':round(st,4),'keys':on,'scores':scores})
 for k in on:
  if k not in prevon:events.append((t,k))
 prevon=set(on)
 im=base.copy();im.paste(last,(32,162));d=ImageDraw.Draw(im);d.rectangle((31,161,1273,861),outline=LINE)
 txt(d,(1725,33),f'{int(t):02d}.{n%24:02d} s',22,CYAN,True)
 txt(d,(32,878),'TARGET / MALENIA',14,RED,True);txt(d,(430,878),'PLAYER / MELEE + PARRY',14,MUTED,True)
 # Keep original game colours and original keyboard overlay plainly visible.
 if (.2<st<1.7) or (3.1<st<4.8) or (43.5<st<45.3):
  b=[np.interp(st,keys[:,0],keys[:,j]) for j in range(1,5)];x,y,bw,bh=b;x=32+x*VW/480;y=162+y*VH/270;bw*=VW/480;bh*=VH/270
  d.rectangle((x,y,x+bw,y+bh),outline=(120,65,69))
  for xx,yy,sx,sy in [(x,y,1,1),(x+bw,y,-1,1),(x,y+bh,1,-1),(x+bw,y+bh,-1,-1)]:
   d.line((xx,yy,xx+16*sx,yy),fill=RED,width=2);d.line((xx,yy,xx,yy+16*sy),fill=RED,width=2)
  txt(d,(x,y-21),'MALENIA / HOSTILE',14,RED,True)
 # A small player tag, anchored to the red costume by simple colour segmentation.
 import cv2
 hsv=cv2.cvtColor(arr,cv2.COLOR_RGB2HSV);mask=(((hsv[:,:,0]<9)|(hsv[:,:,0]>171))&(hsv[:,:,1]>115)&(hsv[:,:,2]>65)).astype('uint8')
 mask[:int(VH*.45)]=0;mask[int(VH*.9):]=0;mask[:,:int(VW*.23)]=0;mask[:,int(VW*.74):]=0
 count,labels,stats,centroids=cv2.connectedComponentsWithStats(mask)
 cand=[j for j in range(1,count) if stats[j,4]>100]
 if cand and int(t)%7<3:
  j=min(cand,key=lambda j:np.linalg.norm(centroids[j]-[VW*.5,VH*.67]));x,y,ww,hh,area=stats[j]
  if hh>15:
   px,py=32+x,162+y;txt(d,(px,py-19),'PLAYER',12,CYAN,True);d.line((px,py,px+14,py),fill=CYAN,width=2);d.line((px,py,px,py+12),fill=CYAN,width=2)
 # Neural pulse strength follows the observed inputs instead of a random trace.
 intensity=min(1,len(on)*.22+.1);v=.22+.5*(.5+.5*np.sin(phase+t*3))**5
 wave=np.exp(-((ys-((t*160)%1020))/110)**2)*(intensity+.2)
 for j in range(len(xs)):
  bright=min(1,v[j]+wave[j]);col=(int(110*bright),int(218*bright),int(209*bright)) if ys[j]<390 else (int(170*bright),int(168*bright),int(231*bright))
  d.point((xn[j],yn[j]),fill=col)
 txt(d,(1318,375),'BRAIN',12,CYAN,True);txt(d,(1692,375),'VENTRAL NERVE CORD',12,(160,150,195),True)
 im.paste(flyimage(on,t),(1300,463));d=ImageDraw.Draw(im)
 # Mirror precisely the same observed key states in compact digital keycaps.
 rows=[['TAB','Q','W','E','R','SHIFT','CTRL'],['A','S','D','F','SPACE','LMB','RMB']]
 for ri,row in enumerate(rows):
  for ci,k in enumerate(row):
   xx=1318+ci*79;yy=857+ri*43;active=k in on
   d.rounded_rectangle((xx,yy,xx+71,yy+33),radius=3,fill=YELLOW if active else (21,33,38),outline=(132,121,66) if active else LINE)
   txt(d,(xx+8,yy+8),k,14,(24,28,27) if active else MUTED,True)
 pressed=' + '.join(on) if on else 'NONE / RELEASED';txt(d,(1318,967),pressed,14,YELLOW if on else MUTED,True)
 # Short descriptions reflect the visible inputs; no invented confidence scores.
 if 'E' in on:description='Equipment / stance input';detail='E held: changing weapon stance or interacting.'
 elif 'F' in on:description='Parry input';detail='F pressed: shield skill / parry command.'
 elif 'CTRL' in on:description='Evasion input';detail='CTRL pressed: roll command.'
 elif 'LMB' in on or 'RMB' in on:description='Attack input';detail=('RMB: normal attack.' if 'RMB' in on else 'LMB: strong attack.')
 elif 'W' in on:description='Closing the distance';detail='W held: moving forward toward the opponent.'
 elif 'S' in on:description='Creating distance';detail='S held: moving backward from the opponent.'
 elif 'A' in on or 'D' in on:description='Lateral movement';detail=('A held: moving left.' if 'A' in on else 'D held: moving right.')
 elif 'Q' in on:description='Target lock input';detail='Q pressed: lock-on command.'
 else:description='Close-range duel';detail='No highlighted keys. Opponent and player remain in view.'
 txt(d,(50,945),description,24,WHITE);txt(d,(50,982),detail,16,MUTED)
 # One small coloured event raster, instead of a dashboard full of charts.
 txt(d,(912,919),'RECENT INPUT EVENTS',12,MUTED,True)
 for et,k in events:
  age=t-et
  if 0<=age<6:
   xx=1249-age*53;yy=945+(keynames.index(k)%5)*10;d.rectangle((xx,yy,xx+3,yy+6),fill=YELLOW if k in ['F','RMB','LMB'] else CYAN)
 d.line((906,999,1253,999),fill=LINE)
 if n in [0,96,480,720,1296]:im.save(OUT/f'preview-{n}.jpg',quality=95)
 enc.stdin.write(im.tobytes())
 if n%240==0:print(f'{n/FPS:.0f} / {args.seconds:g} sec; keys={on}',flush=True)
enc.stdin.close();rc=enc.wait();dec.stdout.close();dec.wait();renderer.close()
if rc:raise RuntimeError('FFmpeg encoder failed')
(OUT/'observed-inputs.json').write_text(json.dumps(keylog))
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(OUT/'silent.mp4'),'-i',source,'-map','0:v:0','-map','1:a:0?','-af','atempo=0.81447,apad','-t',str(args.seconds),'-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(OUT/'Malenia-Fly-Keyboard-Sync.mp4')],check=True)
print('DONE',flush=True)
