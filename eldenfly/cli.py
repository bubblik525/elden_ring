"""CLI for a self-contained demo and instrumentation of local recordings."""
import argparse
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from .inputs import OverlayDetector, KEYS, CENTERS, F_CORNERS, rising_edges
from .neural import SpikeNetwork
from .render import draw_panel


def synthetic_frame(index):
    """Generated calibration scene; includes no third-party gameplay."""
    im=Image.new("RGB",(1920,1080),(24,33,39));d=ImageDraw.Draw(im)
    for j in range(18):
        y=400+j*38;d.line((0,y,1920,y),fill=(36,51,55),width=2)
    x=630+int(120*math.sin(index*.04))
    d.ellipse((x,420,x+100,520),fill=(183,168,139))
    d.rectangle((x+10,520,x+90,760),fill=(83,101,111))
    d.polygon([(1050,400),(1120,610),(990,610)],fill=(127,60,63))
    d.rectangle((963,385,1140,630),outline=(222,103,90),width=3)
    keys=("W",) if index%90<45 else ("F",) if index%90<60 else ("RMB",)
    for key,(cx,cy) in CENTERS.items():
        d.rectangle((cx-38,cy-38,cx+38,cy+38),fill=(220,220,70) if key in keys else (34,42,44),outline="white")
    if "F" in keys:
        for cx,cy in F_CORNERS:d.rectangle((cx-7,cy-7,cx+7,cy+7),fill=(220,220,70))
    return np.array(im)


def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if not 1 <= args.fps <= 60 or not math.isfinite(args.seconds) or args.seconds<=0:
        raise ValueError("fps must be 1..60 and seconds must be positive and finite")
    cap=None
    if args.command != "demo":
        cap=cv2.VideoCapture(str(args.video))
        if not cap.isOpened():
            cap.release()
            raise ValueError(f"Cannot open video: {args.video}")
        source_fps=cap.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(source_fps) or source_fps<=0:
            cap.release()
            raise ValueError("Video has no valid frame rate")
    output_fps = args.fps if cap is None else min(args.fps, source_fps)
    writer=None
    detector=OverlayDetector();net=SpikeNetwork();previous=();sample=0;source_index=0;next_time=0.;last_time=None
    try:
        if args.command != "analyze":
            writer=cv2.VideoWriter(str(out/"replay.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),output_fps,(1280,800))
            if not writer.isOpened():
                raise RuntimeError("OpenCV cannot initialize the MP4 encoder")
        with (out/"telemetry.jsonl").open("w") as log:
            while True:
                if cap is None:
                    time=sample/args.fps
                    if time>=args.seconds:break
                    frame=synthetic_frame(round(time*30))
                else:
                    ok,bgr=cap.read()
                    if not ok:break
                    time=source_index/source_fps;source_index+=1
                    if time>=args.seconds:break
                    if time+1e-9<next_time:continue
                    next_time+=1/output_fps
                    frame=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
                state=detector.detect(frame)
                dt=0. if last_time is None else time-last_time
                counts=net.advance([k in state.keys for k in KEYS],dt)
                record={"frame":sample,"time":time,"keys":state.keys,"presses":rising_edges(previous,state.keys),
                        "yellow_fraction":state.scores,"spikes":int(counts.sum()),"model_time":net.time}
                log.write(json.dumps(record)+"\n")
                if writer is not None:
                    panel=draw_panel(frame,state,net,counts,time)
                    writer.write(cv2.cvtColor(np.array(panel),cv2.COLOR_RGB2BGR))
                    if sample==0 or sample==round(args.fps*2):panel.save(out/"preview.png")
                previous=state.keys;last_time=time;sample+=1
    finally:
        if cap is not None:cap.release()
        if writer is not None:writer.release()
    if sample==0:raise ValueError("Video contained no decodable samples")
    print(json.dumps({"samples":sample,"output":str(out),"total_spikes":net.total_spikes}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ["demo","analyze","render"]:
        p=sub.add_parser(name)
        if name!="demo":p.add_argument("video",type=Path)
        p.add_argument("--output",default=f"runs/{name}")
        p.add_argument("--seconds",type=float,default=6 if name=="demo" else 60)
        p.add_argument("--fps",type=int,default=30)
    args=parser.parse_args()
    try:run(args)
    except (ValueError,RuntimeError) as error:parser.exit(2,f"error: {error}\n")
