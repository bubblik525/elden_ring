import json
import pytest
from eldenfly.production import frame_count, read_telemetry, font

@pytest.mark.parametrize('value', [0,-1,61,float('nan'),float('inf')])
def test_invalid_duration(value):
    with pytest.raises(ValueError):frame_count(value)

def test_frame_rounding():
    assert frame_count(60)==1440
    assert frame_count(1.01)==24

def test_invalid_telemetry(tmp_path):
    p=tmp_path/'frames.json'
    p.write_text(json.dumps([{'frame':0,'keys':['W']}]))
    with pytest.raises(ValueError):read_telemetry(p,2)
    p.write_text(json.dumps([{'frame':1,'keys':[]}]))
    with pytest.raises(ValueError):read_telemetry(p,1)

def test_valid_telemetry_and_font(tmp_path):
    p=tmp_path/'frames.json';rows=[{'frame':0,'keys':['W']},{'frame':1,'keys':[]}]
    p.write_text(json.dumps(rows))
    assert read_telemetry(p,2)==rows
    assert font(14).getbbox('Eldenfly')[2]>0
