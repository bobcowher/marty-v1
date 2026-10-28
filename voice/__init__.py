"""Marty's voice: say(text) speaks it in a small-robot voice on the default audio output.

Knows nothing about the arm or the network, so it can move onto the robot unchanged.
Rendered phrases are cached as WAVs; the prompts repeat, so after the first time
they play instantly.

Needs piper-tts, aplay (alsa-utils) and a Piper voice model (MARTY_VOICE_MODEL, default
~/.local/share/piper-voices/en_US-lessac-medium.onnx). Download one with:
    python -m piper.download_voices en_US-lessac-medium --data-dir ~/.local/share/piper-voices
"""
import hashlib
import os
import subprocess
import wave

import numpy as np

from . import effects

MODEL = os.environ.get('MARTY_VOICE_MODEL',
                       os.path.expanduser('~/.local/share/piper-voices/en_US-lessac-medium.onnx'))
CACHE_DIR = os.path.expanduser('~/.cache/marty-voice')
LENGTH_SCALE = 1.28  # piper speaking speed before the effect (>1 is slower)

_voice = None


def _cache_path(text):
    # Any effect/model change gets a new cache entry rather than a stale sound
    with open(effects.__file__, 'rb') as f:
        key = f"{MODEL}|{LENGTH_SCALE}|{text}".encode() + f.read()
    return os.path.join(CACHE_DIR, hashlib.sha1(key).hexdigest()[:16] + '.wav')


def _synthesize(text):
    global _voice
    from piper import PiperVoice, SynthesisConfig
    if _voice is None:
        _voice = PiperVoice.load(MODEL)
    config = SynthesisConfig(length_scale=LENGTH_SCALE * effects.PITCH)
    chunks = list(_voice.synthesize(text, syn_config=config))
    return np.concatenate([c.audio_float_array for c in chunks]), chunks[0].sample_rate


def render(text):
    """Return the path of a WAV of text in the robot voice, rendering it if not cached."""
    path = _cache_path(text)
    if not os.path.exists(path):
        audio, rate = _synthesize(text)
        os.makedirs(CACHE_DIR, exist_ok=True)
        save_wav(path, effects.walle(audio, rate), rate)
    return path


def save_wav(path, audio, rate):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())


def say(text):
    """Speak text and block until it finishes."""
    subprocess.run(['aplay', '-q', render(text)], check=False)
