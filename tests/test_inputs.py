import numpy as np
import pytest
from eldenfly.inputs import OverlayDetector, CENTERS, F_CORNERS, rising_edges

@pytest.mark.parametrize('scale',[1,.5])
def test_scaled_highlights_and_shield_occlusion(scale):
    a=np.zeros((1080,1920,3),dtype=np.uint8)
    x,y=CENTERS['W'];a[y-30:y+30,x-30:x+30]=[220,220,65]
    # No yellow in F's centre: an icon covers it.
    for x,y in F_CORNERS:a[y-6:y+6,x-6:x+6]=[220,220,65]
    if scale==.5:a=a[::2,::2]
    result=OverlayDetector().detect(a)
    assert result.keys==('W','F')
    assert result.scores['F']>.9

@pytest.mark.parametrize('color',[[230,230,230],[255,30,30],[20,20,20]])
def test_non_yellow_is_not_a_press(color):
    a=np.full((540,960,3),color,dtype=np.uint8)
    assert OverlayDetector().detect(a).keys==()

def test_edges_do_not_repeat_held_keys():
    assert rising_edges(('W',),('W','F'))==('F',)
    assert rising_edges(('W',),('W',))==()

def test_reject_invalid_frames():
    with pytest.raises(ValueError):OverlayDetector().detect(np.zeros((10,10)))
    with pytest.raises(ValueError):OverlayDetector(1)
