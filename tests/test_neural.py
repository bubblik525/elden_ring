import numpy as np
import pytest
from eldenfly.neural import SpikeNetwork

def test_silence_and_driven_spiking():
    net=SpikeNetwork()
    assert net.advance(np.zeros(14),.1).sum()==0
    counts=net.advance(np.ones(14),.5)
    assert counts.sum()>0
    assert np.max(counts)<=167 # refractory period imposes a rate bound
    assert np.isfinite(net.v).all()
    assert np.all(net.v<1)

def test_seed_reproducibility_and_partition_invariance():
    a,b=SpikeNetwork(),SpikeNetwork()
    drive=np.ones(14)
    all_counts=a.advance(drive,.3)
    split_counts=sum((b.advance(drive,.01) for _ in range(30)))
    np.testing.assert_array_equal(all_counts,split_counts)
    np.testing.assert_allclose(a.v,b.v)
    assert a.total_spikes==b.total_spikes

def test_fractional_frames_preserve_time():
    net=SpikeNetwork()
    for _ in range(60):net.advance(np.zeros(14),1/60)
    assert net.time==pytest.approx(1)

def test_drive_validation():
    n=SpikeNetwork()
    with pytest.raises(ValueError):n.advance([np.nan]*14,.1)
    with pytest.raises(ValueError):n.advance([0],.1)
    with pytest.raises(ValueError):n.advance([0]*14,-1)
