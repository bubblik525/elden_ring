"""Small deterministic leaky integrate-and-fire network for replay visualization."""
import numpy as np

class SpikeNetwork:
    """Seeded synthetic connectivity; not a FlyWire or MaleCNS connectome.

    Time is in seconds. Voltage is dimensionless. Euler integration uses a
    fixed 1 ms step. A 3 ms absolute refractory period follows each spike.
    Input current and recurrent synaptic state are bounded. Weights are fixed;
    this model does not train a policy or learn to win the fight.
    """
    dt = .001
    tau_m = .020
    tau_s = .010
    threshold = 1.0
    refractory_duration = .003

    def __init__(self, size=96, channels=14, seed=7):
        if size < 2 or channels < 1:
            raise ValueError("size >= 2 and channels >= 1 are required")
        rng = np.random.default_rng(seed)
        edges = rng.random((size,size)) < .045
        np.fill_diagonal(edges, False)
        signs = np.where(rng.random(size) < .2, -1., 1.)
        self.weights = edges * rng.uniform(.02,.12,(size,size)) * signs[None,:]
        self.inputs = rng.uniform(.3,1.2,(size,channels)) * (rng.random((size,channels)) < .2)
        self.v = np.zeros(size)
        self.syn = np.zeros(size)
        self.refractory = np.zeros(size)
        self.spikes = np.zeros(size,dtype=bool)
        self.total_spikes = 0
        self.time = 0.
        self._remainder = 0.

    def advance(self, drive, duration):
        drive = np.asarray(drive, dtype=float)
        if drive.shape != (self.inputs.shape[1],) or not np.isfinite(drive).all():
            raise ValueError("drive must be a finite channel vector")
        if not np.isfinite(duration) or duration < 0:
            raise ValueError("duration must be finite and nonnegative")
        if duration > 10:
            raise ValueError("advance in chunks of at most 10 seconds")
        self._remainder += duration
        steps = int((self._remainder + 1e-12) / self.dt)
        self._remainder -= steps*self.dt
        count = np.zeros(len(self.v),dtype=int)
        current = 2.0 * (self.inputs @ np.clip(drive,0,1))
        for _ in range(steps):
            self.refractory = np.maximum(0.,self.refractory-self.dt)
            self.syn *= np.exp(-self.dt/self.tau_s)
            self.syn += self.weights @ self.spikes
            np.clip(self.syn,-2,2,out=self.syn)
            active = self.refractory <= 1e-12
            self.v[active] += self.dt/self.tau_m * (-self.v[active]+current[active]+self.syn[active])
            self.v[~active] = 0
            self.spikes = active & (self.v >= self.threshold)
            self.v[self.spikes] = 0
            self.refractory[self.spikes] = self.refractory_duration
            count += self.spikes
            self.time += self.dt
        self.total_spikes += int(count.sum())
        return count
