import json
import subprocess
import sys
import cv2

def test_demo_produces_decodable_video_and_telemetry(tmp_path):
    subprocess.run([sys.executable,'-m','eldenfly','demo','--seconds','0.4','--fps','10','--output',str(tmp_path)],check=True)
    records=[json.loads(s) for s in (tmp_path/'telemetry.jsonl').read_text().splitlines()]
    assert len(records)==4
    assert records[0]['keys']==['W']
    assert records[0]['presses']==['W']
    assert records[1]['presses']==[]
    assert records[-1]['model_time']>.29
    cap=cv2.VideoCapture(str(tmp_path/'replay.mp4'))
    try:
        count=0
        while True:
            ok,frame=cap.read()
            if not ok:break
            assert frame.shape[:2]==(800,1280)
            count+=1
        assert count==4
    finally:cap.release()
    assert (tmp_path/'preview.png').exists()

def test_missing_video_is_actionable(tmp_path):
    p=subprocess.run([sys.executable,'-m','eldenfly','analyze',str(tmp_path/'missing.mp4'),'--output',str(tmp_path/'out')],capture_output=True,text=True)
    assert p.returncode==2
    assert 'Cannot open video' in p.stderr

def test_render_does_not_speed_up_low_fps_source(tmp_path):
    import numpy as np
    source=tmp_path/'source.mp4'
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'mp4v'),5,(960,540))
    assert writer.isOpened()
    for _ in range(5):writer.write(np.zeros((540,960,3),dtype=np.uint8))
    writer.release()
    out=tmp_path/'render'
    subprocess.run([sys.executable,'-m','eldenfly','render',str(source),'--fps','30','--seconds','1','--output',str(out)],check=True)
    cap=cv2.VideoCapture(str(out/'replay.mp4'))
    try:
        assert cap.get(cv2.CAP_PROP_FPS)==5
        assert cap.get(cv2.CAP_PROP_FRAME_COUNT)==5
    finally:cap.release()
