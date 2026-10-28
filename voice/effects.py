"""Make a clean TTS voice sound like a small robot (Wall-E-ish). Pure numpy."""
import numpy as np

# Pitch is raised by synthesizing slower (tts length_scale * PITCH) and then
# playing faster by the same factor, so duration is unchanged but pitch and
# formants both rise - a smaller "throat", which is most of the character.
PITCH = 1.13

WARBLE_HZ = 6.2        # vibrato rate
WARBLE_DEPTH = 0.025   # fraction of pitch
GRIT_BITS = 6          # bit depth of the crushed copy
GRIT_MIX = 0.25        # how much crushed signal is blended in
RING_HZ = 36.0         # ring modulator, adds a metallic buzz
RING_MIX = 0.32
BAND = (250.0, 5000.0)  # small-speaker band-pass, Hz
BASS_HZ = 300.0         # boost below this...
BASS_GAIN = 1.0         # ...by this factor (1 = off)


def resample(audio, factor):
    """Play `factor` times faster (shorter, higher)."""
    n = int(len(audio) / factor)
    return np.interp(np.arange(n) * factor, np.arange(len(audio)), audio)


def warble(audio, rate, hz=WARBLE_HZ, depth=WARBLE_DEPTH):
    """Vibrato: read through the audio at a speed that wobbles around 1."""
    t = np.arange(len(audio)) / rate
    speed = 1.0 + depth * np.sin(2 * np.pi * hz * t)
    pos = np.clip(np.cumsum(speed) - speed[0], 0, len(audio) - 1)
    return np.interp(pos, np.arange(len(audio)), audio)


def grit(audio, bits=GRIT_BITS, mix=GRIT_MIX):
    levels = 2 ** (bits - 1)
    crushed = np.round(audio * levels) / levels
    return (1 - mix) * audio + mix * crushed


def ring(audio, rate, hz=RING_HZ, mix=RING_MIX):
    t = np.arange(len(audio)) / rate
    return (1 - mix) * audio + mix * audio * np.sin(2 * np.pi * hz * t)


def band_pass(audio, rate, low=BAND[0], high=BAND[1], bass_hz=BASS_HZ, bass_gain=BASS_GAIN):
    spectrum = np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), 1 / rate)
    spectrum[freqs < bass_hz] *= bass_gain
    spectrum[(freqs < low) | (freqs > high)] = 0
    return np.fft.irfft(spectrum, len(audio))


def walle(audio, rate, pitch=PITCH, warble_hz=WARBLE_HZ, warble_depth=WARBLE_DEPTH,
          ring_hz=RING_HZ, ring_mix=RING_MIX, grit_bits=GRIT_BITS, grit_mix=GRIT_MIX,
          band_low=BAND[0], bass_gain=BASS_GAIN):
    """`audio` should be synthesized `pitch` times slower than normal speech."""
    out = resample(audio, pitch)
    out = warble(out, rate, warble_hz, warble_depth)
    out = ring(out, rate, ring_hz, ring_mix)
    out = grit(out, grit_bits, grit_mix)
    out = band_pass(out, rate, band_low, BAND[1], BASS_HZ, bass_gain)
    peak = np.max(np.abs(out))
    return (0.9 * out / peak if peak > 0 else out).astype(np.float32)
