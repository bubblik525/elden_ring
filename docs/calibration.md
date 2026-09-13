# Overlay calibration

`eldenfly.inputs.CENTERS` stores button positions in the 1920x1080 reference frame. Coordinates and sample rectangles scale independently with image width and height. Keep the complete frame; a crop changes the coordinate origin.

A sampled pixel is yellow when R > 125, G > 125, B < 0.78 × min(R, G), and |R − G| < 65. A button is active when the fraction exceeds 0.30. Scores describe pixel fractions, not classifier confidence.

F is special: in the source overlay a shield icon can cover its letter and centre. Four corner patches are sampled and their median yellow fraction is used. Other keys use centre patches.

For a new overlay, inspect frames containing presses and releases, update the profile coordinates, add synthetic regression fixtures and manually compare results against multiple source frames. Yellow effects behind a transparent overlay can cause false positives. Crops, alternative layouts, codec artifacts and small images can cause missed presses. The detector rejects images below 480x270.

JSONL records include sample index, source time in seconds, held keys, newly pressed keys, yellow fractions, simulated spikes and accumulated model time. The first observed held key is logged as a press. Releases are visible as changes in `keys`; they do not create press events. Source frames are sampled at the requested rate, so shorter presses may be missed.
