import sys, numpy as np
sr = 22050
def analisar(nome):
    x = np.fromfile(nome + ".raw", dtype=np.float32)
    hop = 256; fps = sr / hop
    fr = np.lib.stride_tricks.sliding_window_view(x, 1024)[::hop]
    S = np.abs(np.fft.rfft(fr * np.hanning(1024), axis=1))
    on = np.maximum(0, np.diff(np.log1p(100 * S), axis=0)).sum(1); on -= on.mean()
    m = min(len(on), int(60 * fps)); a0 = int(min(20, len(x)/sr/4) * fps)
    seg = on[a0:a0 + m]
    ac = np.correlate(seg, seg, 'full')[len(seg) - 1:]
    idx = np.arange(len(ac))
    best = max(((np.interp(60/b*fps, idx, ac) + .5*np.interp(120/b*fps, idx, ac), b) for b in np.arange(70, 180, .25)))
    bpm = best[1]; per = 60 / bpm * fps
    ph = max(range(int(per)), key=lambda p: on[np.round(np.arange(p, len(on) - 1, per)).astype(int)].sum())
    beat0 = ph / fps; bt = 60 / bpm
    rms = lambda a, b: 10*np.log10(np.mean(x[max(0,int(a*sr)):int(b*sr)]**2) + 1e-12)
    dur = len(x) / sr
    print(f"== {nome}  dur {dur:.1f}s  bpm {bpm}  beat0 {beat0:.3f}  compasso {4*bt:.3f}s")
    print("RMS por 2s: " + " ".join(f"{int(t)}:{rms(t,t+2):.0f}" for t in np.arange(0, dur-1, 2)))
    # saltos de energia no início de compassos
    cands = []
    t = beat0
    while t < dur - 4:
        d = rms(t, t+2) - rms(t-2, t)
        cands.append((d, t)); t += bt
    cands.sort(reverse=True)
    vistos = []
    for d, t in cands:
        if all(abs(t - v) > 4 for _, v in vistos): vistos.append((d, t))
        if len(vistos) == 8: break
    print("Maiores subidas (dB, s): " + "  ".join(f"{d:+.1f}@{t:.2f}" for d, t in sorted(vistos, key=lambda v: v[1])))
for n in sys.argv[1:]: analisar(n)
