"""Render every calibration phrase to WAVs so the voice can be judged by ear.

    python voice_samples.py [out_dir]     (default: voice_samples/)
    python voice_samples.py --play        also play each one
"""
import os
import shutil
import sys

import voice
from calibration import PHRASES

out_dir = next((a for a in sys.argv[1:] if not a.startswith('-')), 'voice_samples')
os.makedirs(out_dir, exist_ok=True)
for i, text in enumerate(PHRASES):
    path = os.path.join(out_dir, f"{i:02d}_{text.replace(' ', '_').replace(',', '')}.wav")
    shutil.copy(voice.render(text), path)
    print(path)
    if '--play' in sys.argv:
        voice.say(text)
