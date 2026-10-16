"""Trilhas originais da série "Seu sonho tem caminho" (18 s cada), estilo inspirador com piano.

Uso: python3 trilha_sonho.py <número do vídeo 1-7> <saida.wav>
"""
import sys
import wave

import numpy as np

SR = 48000
DUR = 18.0
N = int(SR * DUR)

# tônica (Hz), BPM, trocas de cena, desenhos aparecendo, botão final, momento "contemplada"
VIDEOS = {
    1: dict(tonica=261.63, bpm=96, trocas=[3.7, 7.6, 11.5, 14.5], desenhos=[3.85, 7.95]),
    2: dict(tonica=293.66, bpm=100, trocas=[3.7, 7.7, 11.5, 14.5], desenhos=[3.85]),
    3: dict(tonica=329.63, bpm=104, trocas=[3.7, 7.7, 11.5, 14.5], desenhos=[3.85]),
    4: dict(tonica=349.23, bpm=100, trocas=[3.5, 6.3, 9.1, 11.9, 14.5], desenhos=[3.75, 6.55, 9.35]),
    5: dict(tonica=196.00, bpm=92, trocas=[3.7, 7.5, 11.5, 14.5], desenhos=[7.75]),
    6: dict(tonica=220.00, bpm=100, trocas=[3.7, 7.5, 11.5, 14.5], desenhos=[]),
    7: dict(tonica=233.08, bpm=96, trocas=[3.7, 7.5, 11.5, 14.5], desenhos=[7.75], contemplada=5.5),
}
CTA = 15.5


def main(numero, saida):
    cfg = VIDEOS[numero]
    rng = np.random.default_rng(100 + numero)
    L = np.zeros(N)
    R = np.zeros(N)
    beat = 60 / cfg["bpm"]
    t0 = cfg["trocas"][0]
    t1 = cfg["trocas"][1]
    fim_ritmo = DUR - 1.0
    tonica = cfg["tonica"]

    def add(sinal, inicio, ganho=1.0, pan=0.0):
        i = int(inicio * SR)
        n = min(len(sinal), N - i)
        if n <= 0 or i < 0:
            return
        L[i:i + n] += sinal[:n] * ganho * np.sqrt((1 - pan) / 2)
        R[i:i + n] += sinal[:n] * ganho * np.sqrt((1 + pan) / 2)

    def tempo(dur):
        return np.arange(int(dur * SR)) / SR

    def passa_baixa(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    def nota(semitom):
        return tonica * 2 ** (semitom / 12)

    def piano(freq, dur=1.6):
        t = tempo(dur)
        s = np.zeros_like(t)
        for h in range(1, 9):
            s += np.sin(2 * np.pi * freq * h * t) / h ** 1.3 * np.exp(-t * (1.8 + 0.9 * h))
        ataque = np.minimum(1, t / 0.004)
        return s * ataque

    def sino(freq, dur=1.2, decai=4.0):
        t = tempo(dur)
        s = sum(a * np.sin(2 * np.pi * freq * p * t) for p, a in ((1, 1), (2.76, .4), (5.4, .2)))
        return s * np.exp(-t * decai)

    # Progressão: IV na abertura (esperança), depois I – V – vi – IV
    I, V, vi, IV = [0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]
    compasso = 4 * beat
    acordes = [(0.0, t0, IV)]
    t = t0
    k = 0
    while t < DUR:
        acordes.append((t, min(t + compasso, DUR), [I, V, vi, IV][k % 4]))
        t += compasso
        k += 1
    acordes[-1] = (acordes[-1][0], DUR, I)  # termina resolvendo

    def acorde_em(tt):
        for ini, fim, ac in acordes:
            if ini <= tt < fim:
                return ac
        return I

    # Pad
    for ini, fim, ac in acordes:
        dur = fim - ini + 0.6
        tt = tempo(dur)
        env = np.clip(np.minimum(tt / (0.9 if ini == 0 else 0.35), (dur - tt) / 0.8), 0, 1)
        for j, st in enumerate(ac):
            f = nota(st - 12)
            for d, pan in ((-0.003, -0.55), (0.003, 0.55)):
                s = sum(np.sin(2 * np.pi * f * h * (1 + d) * tt) / h ** 2 for h in range(1, 5))
                add(s * env, ini, 0.026 if ini == 0 else 0.03, pan * (0.4 + 0.2 * j))

    # Piano dedilhado em colcheias
    padrao = [0, 1, 2, 1, 2, 1, 0, 1]
    for j, b in enumerate(np.arange(0.25, fim_ritmo, beat / 2)):
        ac = acorde_em(b + 0.01)
        f = nota(ac[padrao[j % 8]] + (12 if j % 8 in (2, 4) else 0))
        ganho = 0.07 if b < t0 else 0.095
        add(piano(f), b, ganho, pan=(-0.25 if j % 2 else 0.25))

    # Melodia simples no piano a partir da segunda cena (notas longas)
    for b in np.arange(t1, fim_ritmo, 2 * beat):
        ac = acorde_em(b + 0.01)
        f = nota(ac[2] + 12)
        add(piano(f, 2.2), b, 0.06, pan=0.1)

    # Baixo
    for b in np.arange(t0, fim_ritmo, 2 * beat):
        raiz = nota(acorde_em(b + 0.01)[0] - 24)
        tt = tempo(1.2)
        s = (np.sin(2 * np.pi * raiz * tt) + 0.45 * np.sin(2 * np.pi * raiz * 2 * tt)) * np.exp(-tt * 3)
        add(s * np.minimum(1, tt / 0.01), b, 0.26)

    # Bumbo leve (1 e 3) desde a 1ª troca; palma e chimbal a partir da 2ª
    for b in np.arange(t0, fim_ritmo, 2 * beat):
        tt = tempo(0.3)
        add(np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-tt * 28)) / SR) * np.exp(-tt * 12), b, 0.42)
    for b in np.arange(t1 + beat, fim_ritmo, 2 * beat):
        tt = tempo(0.25)
        ruido = rng.uniform(-1, 1, len(tt))
        add((passa_baixa(ruido, 4) - passa_baixa(ruido, 24)) * np.exp(-tt * 18), b, 0.2)
    for j, b in enumerate(np.arange(t1, fim_ritmo, beat / 2)):
        tt = tempo(0.06)
        ruido = rng.uniform(-1, 1, len(tt))
        add((ruido - passa_baixa(ruido, 3)) * np.exp(-tt * 70), b, 0.05 if j % 2 else 0.03, pan=0.25)

    # Subida antes da 1ª troca e "whoosh" nas outras
    dur = 1.1
    tt = tempo(dur)
    add(passa_baixa(rng.uniform(-1, 1, len(tt)), 8) * (tt / dur) ** 2.4, t0 - dur, 0.13)
    for troca in cfg["trocas"][1:]:
        dur = 0.55
        tt = tempo(dur)
        ruido = passa_baixa(rng.uniform(-1, 1, len(tt)), 10)
        env = np.sin(np.pi * tt / dur) ** 2
        add(ruido * env, troca - 0.3, 0.2, pan=-0.4)
        add(ruido[::-1] * env, troca - 0.3, 0.12, pan=0.4)

    # Brilho quando um desenho aparece
    for d in cfg["desenhos"]:
        ac = acorde_em(d + 0.01)
        for j, st in enumerate(ac + [ac[0] + 12]):
            add(sino(nota(st + 24), 1.4, 3.5), d + 0.07 * j, 0.045, pan=-0.45 + 0.3 * j)

    # Carta contemplada (vídeo 7)
    if "contemplada" in cfg:
        c = cfg["contemplada"]
        tt = tempo(1.4)
        add(np.sin(2 * np.pi * np.cumsum(40 + 55 * np.exp(-tt * 9)) / SR) * np.exp(-tt * 3.5), c, 0.5)
        for j, st in enumerate((0, 4, 7, 12, 16)):
            add(sino(nota(st + 24), 1.6, 3.0), c + 0.05 * j, 0.06, pan=-0.4 + 0.2 * j)

    # Botão final
    for st, atraso in ((7, 0.0), (12, 0.06)):
        tt = tempo(0.8)
        add(piano(nota(st + 12), 0.8), CTA + atraso, 0.12)

    mix = np.stack([L, R], axis=1)
    fade_in = np.minimum(1, np.arange(N) / (0.25 * SR))
    fade_out = np.minimum(1, (N - np.arange(N)) / (1.2 * SR))
    mix *= (fade_in * fade_out)[:, None]
    mix = np.tanh(1.2 * mix) / np.tanh(1.2)
    mix *= 0.89 / np.max(np.abs(mix))
    with wave.open(saida, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
    print("ok", sys.argv[1])
