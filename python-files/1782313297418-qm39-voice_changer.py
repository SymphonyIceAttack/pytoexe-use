"""
Female Voice Changer for Discord
---------------------------------
Requirements:
  pip install sounddevice numpy scipy

Also install VB-Cable (free): https://vb-audio.com/Cable/
Restart your PC after installing VB-Cable.

How to use:
  1. Run this script: python voice_changer.py
  2. Pick your real microphone as INPUT
  3. Pick "CABLE Input (VB-Audio Virtual Cable)" as OUTPUT
  4. In Discord: Settings > Voice & Video > Input Device = "CABLE Output (VB-Audio Virtual Cable)"
  5. Talk normally — Discord will hear your shifted voice!

Press Ctrl+C to stop.
"""

import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly
import math
import sys

CHUNK = 1024
SAMPLERATE = 44100
PITCH_SEMITONES = 8       # How many semitones to shift up (8 = natural female range)
FORMANT_SHIFT = True       # Brighten vocal resonance for a more feminine tone
VOLUME = 1.0               # Output volume multiplier (1.0 = normal)

def list_devices():
    print("\nAvailable audio devices:\n")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        ins = d['max_input_channels']
        outs = d['max_output_channels']
        tag = []
        if ins > 0: tag.append("IN")
        if outs > 0: tag.append("OUT")
        print(f"  [{i:2d}] {d['name']}  ({'/'.join(tag)})")
    print()

def pick_device(prompt, kind):
    while True:
        try:
            idx = int(input(prompt))
            d = sd.query_devices(idx)
            if kind == 'input' and d['max_input_channels'] < 1:
                print("  That device has no input channels, try again.")
                continue
            if kind == 'output' and d['max_output_channels'] < 1:
                print("  That device has no output channels, try again.")
                continue
            return idx
        except (ValueError, sd.PortAudioError):
            print("  Invalid selection, try again.")

def pitch_shift(audio, semitones, sr):
    factor = 2 ** (semitones / 12.0)
    # Resample to change pitch, then resample back to original length
    orig_len = len(audio)
    numer = 1000
    denom = max(1, round(numer * factor))
    shifted = resample_poly(audio, numer, denom)
    # Trim or pad to original length
    if len(shifted) >= orig_len:
        return shifted[:orig_len]
    else:
        return np.pad(shifted, (0, orig_len - len(shifted)))

def formant_brighten(audio, sr):
    """Simple high-shelf boost to simulate higher formants."""
    from scipy.signal import butter, lfilter
    # Gentle high shelf: boost above 1.5kHz
    b, a = butter(2, 1500 / (sr / 2), btype='high')
    boosted = lfilter(b, a, audio) * 0.5
    return np.clip(audio + boosted, -1.0, 1.0)

def main():
    print("=" * 55)
    print("  Female Voice Changer for Discord")
    print("=" * 55)

    list_devices()

    in_dev = pick_device("Enter INPUT device number (your real mic): ", 'input')
    out_dev = pick_device("Enter OUTPUT device number (CABLE Input): ", 'output')

    print(f"\nSettings:")
    print(f"  Pitch shift   : +{PITCH_SEMITONES} semitones")
    print(f"  Formant shift : {'On' if FORMANT_SHIFT else 'Off'}")
    print(f"  Volume        : {int(VOLUME * 100)}%")
    print(f"\nRunning! Press Ctrl+C to stop.\n")
    print("In Discord: Settings > Voice & Video > Input = CABLE Output\n")

    overflow_buffer = np.zeros(0, dtype=np.float32)

    def callback(indata, outdata, frames, time, status):
        nonlocal overflow_buffer

        mono = indata[:, 0].copy()

        # Pitch shift
        shifted = pitch_shift(mono, PITCH_SEMITONES, SAMPLERATE)

        # Formant brightening
        if FORMANT_SHIFT:
            shifted = formant_brighten(shifted, SAMPLERATE)

        # Volume
        shifted = np.clip(shifted * VOLUME, -1.0, 1.0)

        # Fill output (mono to all channels)
        out_channels = outdata.shape[1]
        for ch in range(out_channels):
            outdata[:, ch] = shifted

    try:
        with sd.Stream(
            device=(in_dev, out_dev),
            samplerate=SAMPLERATE,
            blocksize=CHUNK,
            dtype='float32',
            channels=(1, sd.query_devices(out_dev)['max_output_channels']),
            callback=callback,
            latency='low'
        ):
            print("Streaming... (Ctrl+C to quit)")
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Check your device selections and try again.")

if __name__ == '__main__':
    main()
