import os
import numpy as np
from scipy.io import wavfile

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

def generate_all_sounds():
    """Generates procedural sound effects for cuts, bounces, elimination, victory, and rhythm beat."""
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    sample_rate = 44100
    
    # 1. Laser / String Cut Sound (Snappy high-pitch slice)
    # Duration ~0.08s
    duration = 0.08
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Fast frequency sweep 2200Hz down to 400Hz
    freq = np.linspace(2200, 400, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    sine = np.sin(phase)
    # Add a bit of white noise snap at start
    noise = (np.random.rand(len(t)) - 0.5) * 0.4
    env = np.exp(-t * 50)
    cut_wave = (sine * 0.7 + noise * 0.3) * env
    cut_wave = (cut_wave / np.max(np.abs(cut_wave)) * 0.8 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "cut.wav"), sample_rate, cut_wave)

    # 2. Wall Bounce (Subtle bass thud)
    # Duration ~0.10s
    duration = 0.10
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = np.linspace(150, 45, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    env = np.exp(-t * 35)
    bounce_wave = np.sin(phase) * env
    bounce_wave = (bounce_wave / np.max(np.abs(bounce_wave)) * 0.5 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "bounce.wav"), sample_rate, bounce_wave)

    # 3. Elimination Boom (Dramatic sub-bass explosion)
    # Duration ~0.7s
    duration = 0.70
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sub_freq = np.linspace(90, 25, len(t))
    sub_phase = 2 * np.pi * np.cumsum(sub_freq) / sample_rate
    sub = np.sin(sub_phase) * np.exp(-t * 5.0)
    noise = (np.random.rand(len(t)) - 0.5) * np.exp(-t * 9.0)
    elim_wave = sub * 0.8 + noise * 0.4
    elim_wave = (elim_wave / np.max(np.abs(elim_wave)) * 0.9 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "eliminate.wav"), sample_rate, elim_wave)

    # 4. Victory Fanfare (Harmonious chime chord C5 - E5 - G5 - C6)
    # Duration ~2.2s
    duration = 2.2
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    vic_wave = np.zeros(len(t))
    for i, freq in enumerate(notes):
        st = i * 0.12  # Staggered arpeggio
        mask = t >= st
        t_note = t[mask] - st
        note_env = np.exp(-t_note * 2.2)
        vic_wave[mask] += (np.sin(2 * np.pi * freq * t_note) + 0.3 * np.sin(4 * np.pi * freq * t_note)) * note_env
    vic_wave = (vic_wave / np.max(np.abs(vic_wave)) * 0.85 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "victory.wav"), sample_rate, vic_wave)

    # 5. Background Rhythm / Beat (Subtle 125 BPM electronic kick/hat beat)
    # Duration: 60 seconds (loopable)
    duration = 60.0
    total_samples = int(sample_rate * duration)
    beat_wave = np.zeros(total_samples, dtype=np.float32)
    
    bpm = 125
    beat_interval = 60.0 / bpm  # ~0.48s
    kick_samples = int(0.12 * sample_rate)
    t_kick = np.linspace(0, 0.12, kick_samples, endpoint=False)
    k_freq = np.linspace(130, 40, kick_samples)
    kick_sig = np.sin(2 * np.pi * np.cumsum(k_freq) / sample_rate) * np.exp(-t_kick * 30)

    cur_time = 0.0
    beat_count = 0
    while cur_time + 0.15 < duration:
        idx = int(cur_time * sample_rate)
        # Add kick on quarter beats
        beat_wave[idx:idx + kick_samples] += kick_sig * 0.22
        
        # Add gentle hi-hat on eighth notes
        hat_idx = idx + int((beat_interval / 2) * sample_rate)
        if hat_idx + 800 < total_samples:
            hat = (np.random.rand(800) - 0.5) * np.exp(-np.linspace(0, 1, 800) * 8) * 0.06
            beat_wave[hat_idx:hat_idx + 800] += hat
            
        cur_time += beat_interval
        beat_count += 1
        
    beat_wave = np.clip(beat_wave, -1.0, 1.0)
    beat_wave = (beat_wave * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "beat.wav"), sample_rate, beat_wave)

    # 6. Intro Slot Roulette Tick Sound (Crisp metallic click)
    duration = 0.03
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tick = np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 180)
    tick = (tick / np.max(np.abs(tick)) * 0.4 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "tick.wav"), sample_rate, tick)

    # 7. Slot Lock / Slam Sound (Heavy punch impact)
    duration = 0.35
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    slam_freq = np.linspace(180, 40, len(t))
    slam = np.sin(2 * np.pi * np.cumsum(slam_freq) / sample_rate) * np.exp(-t * 12)
    noise = (np.random.rand(len(t)) - 0.5) * np.exp(-t * 25) * 0.3
    lock_wave = (slam * 0.7 + noise * 0.3)
    lock_wave = (lock_wave / np.max(np.abs(lock_wave)) * 0.8 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "lock.wav"), sample_rate, lock_wave)

    # 8. Battle Start Horn / Gong (Dramatic cinematic bass drop)
    duration = 1.2
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    horn_freq = np.linspace(120, 50, len(t))
    horn = (np.sin(2 * np.pi * np.cumsum(horn_freq) / sample_rate) + 0.4 * np.sin(4 * np.pi * np.cumsum(horn_freq) / sample_rate)) * np.exp(-t * 3.0)
    horn = (horn / np.max(np.abs(horn)) * 0.9 * 32767).astype(np.int16)
    wavfile.write(os.path.join(SOUNDS_DIR, "start.wav"), sample_rate, horn)

    print("All sound effects generated successfully in assets/sounds/")

if __name__ == "__main__":
    generate_all_sounds()
