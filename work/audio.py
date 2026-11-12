# -*- coding: utf-8 -*-
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly
from timeline import *

sr = 44100
N = int(DUR * sr)
rng = np.random.default_rng(3)
t = np.arange(N) / sr
L = np.zeros(N); R = np.zeros(N)

def f(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, 'low', fs=sr, output='sos'), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, 'high', fs=sr, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=sr, output='sos'), x)
def add(buf, x, t0, gain=1.0):
    i = int(t0 * sr)
    if i >= N: return
    x = x[:N - i]
    buf[i:i + len(x)] += x * gain

bpm = 108; beat = 60 / bpm; bar = beat * 4
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Am F C G
roots  = [45, 41, 48, 43]
nbars = int(DUR / bar) + 1

# --- pad
pad = np.zeros(N)
for b in range(nbars):
    ch = chords[b % 4]
    dur = bar + 0.6
    tt = np.arange(int(dur * sr)) / sr
    env = np.minimum(tt / 0.45, 1) * np.clip((dur - tt) / 0.6, 0, 1)
    seg = np.zeros_like(tt)
    for m in ch:
        for det in (-0.004, 0.0, 0.004):
            fr = f(m) * (1 + det)
            for h_, a in ((1, 1.0), (2, .5), (3, .3), (4, .15)):
                seg += a * np.sin(2 * np.pi * fr * h_ * tt + rng.uniform(0, 6.28))
    add(pad, seg * env * 0.05, b * bar)
pad = lp(pad, 1700)
L += pad; R += np.roll(pad, 220) * 0.95

# --- bass
bass = np.zeros(N)
for b in range(nbars):
    for k in (0, 2.5):
        t0 = b * bar + k * beat
        d = beat * 1.6
        tt = np.arange(int(d * sr)) / sr
        x = np.sin(2 * np.pi * f(roots[b % 4]) * tt) * np.exp(-tt * 2.6) * np.minimum(tt / 0.01, 1)
        add(bass, x, t0, 0.33)
L += bass; R += bass

# --- arp pluck (ping-pong)
arp = np.zeros(N)
pattern = [0, 1, 2, 1, 2, 1, 0, 2]
for b in range(nbars):
    ch = chords[b % 4]
    for s in range(8):
        t0 = b * bar + s * beat / 2
        if t0 > DUR: break
        m = ch[pattern[s] % 3] + 12 + (12 if s in (3, 7) else 0)
        d = 0.55
        tt = np.arange(int(d * sr)) / sr
        fr = f(m)
        x = (np.sin(2 * np.pi * fr * tt) + .35 * np.sin(2 * np.pi * fr * 2 * tt) + .15 * np.sin(2 * np.pi * fr * 3 * tt))
        x *= np.exp(-tt * 9) * np.minimum(tt / 0.004, 1)
        g = 0.10 if t0 < SC[1]['t0'] else 0.15
        add(arp, x, t0, g)
dl = int(beat * 0.75 * sr)
wet = np.zeros(N)
for k in range(1, 5):
    wet += np.roll(arp, dl * k) * (0.42 ** k) * (1 if k % 2 else 1)
wet[:dl] = 0
L += arp * 0.8 + np.roll(wet, 0) * 0.9
R += arp * 0.5 + np.roll(wet, dl // 2) * 1.0

# --- drums
drum = np.zeros(N)
start_drum = SC[1]['t0']
for k in range(int(DUR / beat) + 1):
    t0 = k * beat
    if t0 < start_drum - 0.01: continue
    d = 0.22
    tt = np.arange(int(d * sr)) / sr
    fr = 45 + 90 * np.exp(-tt * 28)
    ph = 2 * np.pi * np.cumsum(fr) / sr
    kick = np.sin(ph) * np.exp(-tt * 15)
    add(drum, kick, t0, 0.55)
    # hat on offbeat
    th = t0 + beat / 2
    hh = hp(rng.normal(size=int(0.05 * sr)), 7000) * np.exp(-np.arange(int(0.05 * sr)) / sr * 90)
    add(drum, hh, th, 0.10)
    if t0 >= SC[2]['t0'] and (k % 4) in (1, 3):
        sn = bp(rng.normal(size=int(0.16 * sr)), 1200, 5500) * np.exp(-np.arange(int(0.16 * sr)) / sr * 24)
        add(drum, sn, t0, 0.22)
L += drum; R += drum

music = np.stack([L, R], 1)

# --- sfx
sfx = np.zeros((N, 2))
for sc in SC:
    for m in sc['msgs']:
        ts = show_time(sc, m)
        d = 0.12
        tt = np.arange(int(d * sr)) / sr
        f0, f1 = (880, 1480) if m['side'] == 'L' else (620, 1000)
        ph = 2 * np.pi * np.cumsum(np.linspace(f0, f1, len(tt))) / sr
        x = np.sin(ph) * np.exp(-tt * 28) * np.minimum(tt / 0.003, 1)
        add(sfx[:, 0], x, ts, 0.16); add(sfx[:, 1], x, ts, 0.16)
for sc in SC[1:]:
    b = sc['t0']
    d = 0.7
    n = rng.normal(size=int(d * sr))
    tt = np.arange(len(n)) / sr
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    x = bp(n, 500, 4500) * env
    add(sfx[:, 0], x, b - 0.35, 0.22); add(sfx[:, 1], x[::-1] * 0 + x, b - 0.35, 0.22)

# --- voice
vo = np.zeros(N)
for sc in SC:
    sr_v, w = wavfile.read(f'voice/v{sc["voice"]}.wav')
    w = w.astype(np.float64) / 32768.0
    if w.ndim > 1: w = w.mean(1)
    w = resample_poly(w, sr, sr_v)
    w = hp(w, 90)
    w = w / (np.abs(w).max() + 1e-9) * 0.9
    add(vo, w, sc['t0'] + VOICE_OFFSET)
vo = np.tanh(vo * 1.6) / np.tanh(1.6)

# --- ducking
env = np.abs(vo)
k = int(0.12 * sr)
env = np.convolve(env, np.ones(k) / k, 'same')
duck = 1 - 0.55 * np.clip(env / 0.12, 0, 1)
duck = np.convolve(duck, np.ones(int(0.08 * sr)) / int(0.08 * sr), 'same')

mix = music * (0.62 * duck)[:, None] + sfx * 0.9 + np.stack([vo, vo], 1) * 1.0
# fades
fi = np.clip(t / 0.5, 0, 1); fo = np.clip((DUR - t) / 1.5, 0, 1)
mix *= (fi * fo)[:, None]
mix = np.tanh(mix * 1.1)
mix = mix / np.abs(mix).max() * 0.89
wavfile.write('final_audio.wav', sr, (mix * 32767).astype(np.int16))
print('audio ok', mix.shape)
