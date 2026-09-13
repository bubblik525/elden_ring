"""Reproducible 1280x800 instrumentation panel rendered with Pillow."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .inputs import KEYS

BG = (10,18,22)
CYAN = (103,211,204)
GOLD = (230,188,92)


def draw_panel(frame, state, network, counts, time):
    image = Image.new("RGB",(1280,800),BG)
    d = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=17)
    small = ImageFont.load_default(size=12)
    def text(x,y,s,color=(174,198,201),tiny=False):
        d.text((x,y),s,font=small if tiny else font,fill=color)
    text(24,18,"ELDENFLY / REPLAY LAB",CYAN)
    text(1040,18,f"t = {time:06.2f} s")
    image.paste(Image.fromarray(frame).resize((864,486)),(24,60))
    d.rectangle((23,59,889,547),outline=(55,89,97))
    text(914,60,"SPIKING READOUT",CYAN)
    text(914,88,"96 units / synthetic graph",tiny=True)
    rng = np.random.default_rng(13)
    points = rng.uniform([923,135],[1250,432],(len(network.v),2))
    for j,k in np.argwhere(network.weights != 0):
        d.line((*points[j],*points[k]),fill=(33,57,65))
    for i,(x,y) in enumerate(points):
        color = GOLD if counts[i] else CYAN if network.v[i]>.4 else (67,103,115)
        radius=3 if counts[i] else 2
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
    text(914,461,f"Spikes this sample: {int(counts.sum())}")
    text(914,491,f"Total spikes: {network.total_spikes}")
    text(24,573,"OBSERVED KEYBOARD / fixed-layout detector",CYAN)
    for i,key in enumerate(KEYS):
        x=24+(i%7)*123;y=609+(i//7)*60
        active=key in state.keys
        d.rounded_rectangle((x,y,x+112,y+46),radius=4,fill=GOLD if active else (25,42,48))
        text(x+10,y+12,key,(19,26,29) if active else (151,181,186))
    text(914,573,"SIGNAL ORIGIN",CYAN)
    text(914,614,"Inputs: visible yellow keys",tiny=True)
    text(914,637,"Spikes: simulated LIF model",tiny=True)
    text(914,660,"Connectivity: seeded random",tiny=True)
    text(914,683,"Control output: none",tiny=True)
    text(24,767,"Offline instrumentation. No autonomous play, learned policy, or biological connectome claim.",tiny=True)
    return image
