"""Production neural-cover and replay-cue pass used for the demo."""
from pathlib import Path
import subprocess,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from eldenfly.production import arguments, font, read_telemetry
args=arguments('guidance')
OUT=args.output; SRC=args.input
frames=read_telemetry(args.telemetry,args.count);FPS=24;W,H=1920,1080
fonts={s:font(s) for s in [12,14,16,18,20,24]}
RED=(255,93,104);WHITE=(227,235,236);MUTED=(125,154,160);CYAN=(106,219,217);BG=(8,18,24)
def txt(d,pos,s,size=14,c=MUTED):d.text(pos,s,font=fonts[size],fill=c)
def arrow(d,pts,c=RED,width=2):
 d.line(pts,fill=c,width=width)
 x,y=pts[-1];px,py=pts[-2];a=math.atan2(y-py,x-px)
 d.polygon([(x,y),(x-10*math.cos(a-.48),y-10*math.sin(a-.48)),(x-10*math.cos(a+.48),y-10*math.sin(a+.48))],fill=c)
def tag(d,x,y,title,sub=None):
 width=max(d.textbbox((0,0),title,font=fonts[14])[2]+24,180)
 d.rectangle((x,y,x+width,y+(48 if sub else 28)),fill=(20,17,23),outline=(124,56,66));txt(d,(x+10,y+6),title,14,RED)
 if sub:txt(d,(x+10,y+29),sub,12,WHITE)
 return width
# Read future observed presses from the recording; these are editorial cues.
rises=[];prev=set()
for f in frames:
 now=set(f['keys']);new=now-prev
 if new:rises.append({'frame':f['frame'],'keys':sorted(new)})
 prev=now
(OUT/'cue-events.json').write_text(json.dumps(rises,indent=2))
label={'W':'MOVE FORWARD','S':'STEP BACK','A':'MOVE LEFT','D':'MOVE RIGHT','F':'PARRY','CTRL':'ROLL','RMB':'ATTACK','LMB':'HEAVY ATTACK','Q':'LOCK TARGET','E':'STANCE / INTERACT','SPACE':'JUMP','SHIFT':'SHIFT INPUT'}
priority=['F','CTRL','RMB','LMB','W','S','A','D','Q','E','SPACE','SHIFT']
# Layered neural projection replacing the source keyboard completely.
sizes=[4,6,8,6,4];layers=[]
for z,num in enumerate(sizes):layers.append([(873+z*88,280+(j+.5)*96/num) for j in range(num)])
dec=subprocess.Popen(['ffmpeg','-v','error','-i',str(SRC),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','24','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE)
for n in range(args.count):
 raw=dec.stdout.read(W*H*3)
 if len(raw)!=W*H*3:raise RuntimeError('Missing video frame')
 im=Image.frombytes('RGB',(W,H),raw);d=ImageDraw.Draw(im);t=n/FPS;on=frames[n]['keys']
 nxt=next((e for e in rises if n<e['frame']<=n+24),None)
 selected=None;remain=0
 if nxt:
  selected=next((k for k in priority if k in nxt['keys']),nxt['keys'][0]);remain=(nxt['frame']-n)/FPS
 # Opaque replacement covers all source keys and mouse, including the white frame.
 d.rectangle((845,230,1263,424),fill=BG,outline=(68,120,131),width=1)
 txt(d,(859,240),'NEURAL LAYER / INPUT INFERENCE',14,CYAN)
 txt(d,(859,262),'VISION',12,MUTED);txt(d,(1023,262),'LATENT',12,MUTED);txt(d,(1185,262),'MOTOR',12,MUTED)
 for z in range(4):
  for j,a in enumerate(layers[z]):
   for k,b in enumerate(layers[z+1]):
    if (j*5+k*3)%4==0:
     active=(j+k+int(t*8)-z*2)%17<2
     d.line((*a,*b),fill=CYAN if active else (37,64,75),width=1)
     if active:
      u=(t*3)%1;x=a[0]+(b[0]-a[0])*u;y=a[1]+(b[1]-a[1])*u;d.ellipse((x-2,y-2,x+2,y+2),fill=WHITE)
 for z,pts in enumerate(layers):
  for j,(x,y) in enumerate(pts):
   active=(j+int(t*7)-z)%9<2;c=RED if z==4 and active else CYAN if active else (86,111,130)
   d.ellipse((x-3,y-3,x+3,y+3),fill=c)
 d.line((859,383,1249,383),fill=(37,64,75))
 txt(d,(859,394),'NEXT / '+(selected or 'OBSERVE'),16,RED if selected else CYAN)
 txt(d,(1105,397),f'T - {round(remain*1000):03d} ms' if selected else 'READING FRAME',12,WHITE)
 # A single upcoming-action callout stays in the game view.
 if selected:
  k=selected; title=f'PREPARE [{k}] / {label.get(k,k)}'
  tag(d,869,442,title,f'NEXT RECORDED INPUT / {remain:.2f}s')
  if k in ['W','S','A','D']:
   origins={'W':((655,670),(655,584)),'S':((655,631),(655,715)),'A':((680,656),(589,656)),'D':((620,656),(711,656))}
   start,end=origins[k];arrow(d,[start,end],RED,3);txt(d,(end[0]+13,end[1]-7),k,20,RED)
   arrow(d,[(886,490),(822,523),(end[0]+22,end[1]-12)],(191,76,86),1)
  elif k in ['F','LMB','RMB']:
   # Point at the equipped weapon/skill HUD, avoiding a guessed enemy position.
   target=(83,752) if k=='F' else (195,750)
   tag(d,63,629,'['+k+'] '+label[k],'INPUT WINDOW APPROACHING')
   arrow(d,[(142,678),(142,708),target],RED,2)
  elif k=='CTRL':
   arrow(d,[(819,553),(765,599),(742,647)],RED,2);txt(d,(784,536),'[CTRL] EVADE',16,RED)
  else:arrow(d,[(922,491),(891,522),(867,549)],RED,2)
 # State overlays rotate between real, fixed HUD elements.
 phase=int(t/3)%3
 if phase==0:
  tag(d,72,322,'PLAYER / HEALTH + STAMINA','HUD REGION READ')
  arrow(d,[(188,321),(188,286),(273,214)],RED,1)
 elif phase==1:
  tag(d,74,512,'EQUIPPED / PARRY SHIELD','DEFENSIVE TOOL')
  arrow(d,[(148,561),(111,609),(83,752)],RED,1)
 else:
  tag(d,355,806,'MALENIA / BOSS VITALS')
  arrow(d,[(485,805),(485,778),(502,736)],RED,1)
 # Execution confirmation appears exactly on observed onset, not randomly.
 recent=next((e for e in reversed(rises) if 0<=n-e['frame']<9),None)
 if recent:
  text='INPUT CONFIRMED / '+' + '.join(recent['keys'])
  d.rectangle((855,530,1247,563),fill=(33,16,22),outline=RED)
  txt(d,(868,539),text,14,RED)
 # Extra recognition details on two verified target intervals only.
 st=t/1.2278
 if .3<st<1.6 or 43.6<st<44.4:
  if st<2:x,y=680,368
  else:x,y=660,329
  txt(d,(390,398),'ENTITY 01 / HOSTILE',14,RED)
  arrow(d,[(543,416),(584,416),(x,y)],RED,1)
 # Keep the synced fly keyboard from the previous version entirely unchanged.
 d.rectangle((1600,1033,1890,1058),fill=(9,17,20));txt(d,(1600,1037),'GUIDANCE / COLOR V04',14,MUTED)
 d.rectangle((32,1033,1290,1058),fill=(9,17,20));txt(d,(32,1037),'REPLAY-BASED CUES / upcoming inputs from the recording; neural layer is illustrative',14,MUTED)
 if n in [0,72,96,480,720,1296]:im.save(OUT/f'preview-{n}.jpg',quality=95)
 enc.stdin.write(im.tobytes())
 if n%240==0:print(f'{n/24:.0f}/{args.seconds:g}',flush=True)
enc.stdin.close();rc=enc.wait();dec.stdout.close();dec.wait()
if rc:raise RuntimeError('FFmpeg encoder failed')
subprocess.run(['ffmpeg','-y','-v','error','-i',str(OUT/'silent.mp4'),'-i',str(SRC),'-map','0:v:0','-map','1:a:0','-t',str(args.seconds),'-c','copy','-movflags','+faststart',str(OUT/'Malenia-Neural-Red-Guidance.mp4')],check=True)
print('DONE',flush=True)
