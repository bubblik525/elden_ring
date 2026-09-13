# Third-party materials

- `assets/preview.png` includes a still from a user-supplied Elden Ring recording, processed with this project's renderer. Game imagery remains the property of its respective rights holders and is not covered by the code's MIT license. The underlying gameplay recording is not distributed.
- `assets/demo.png` is generated from the synthetic calibration scene in this project.
- Stonkfly is linked as an architectural inspiration; no Stonkfly source or connectome data is included.
- NumPy, Pillow and OpenCV are installed dependencies governed by their own licenses.

- `assets/production-preview.jpg` is an output from the production renderer. It combines user-supplied game imagery and a brain projection with an externally loaded flybody model; it is not covered by the code's MIT license. The brain reference is not distributed as a standalone asset.
- Production rendering loads assets from [TuragaLab/flybody](https://github.com/TuragaLab/flybody), supplied separately under its upstream licensing. MuJoCo is an optional dependency with its own license. No flybody meshes are vendored here.
