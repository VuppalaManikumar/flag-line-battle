import os
import sys
import shutil
import subprocess
import time
import random
from typing import List, Optional, Any
import numpy as np
from scipy.io import wavfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Set headless SDL video driver before importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from countries import COUNTRY_DATABASE, preload_countries
from sound_gen import generate_all_sounds, SOUNDS_DIR
from simulator import BattleSimulator
from renderer import BattleRenderer

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def find_ffmpeg() -> str:
    """Finds ffmpeg executable either on PATH or in scratch/ffmpeg directory."""
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg
        
    # Check known scratch path
    scratch_ffmpeg = r"C:\Users\manik\.gemini\antigravity\scratch\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
    if os.path.exists(scratch_ffmpeg):
        return scratch_ffmpeg
        
    raise FileNotFoundError("Could not locate ffmpeg.exe on system.")

def build_audio_track(sound_events: list, duration: float, sample_rate: int = 44100) -> str:
    """Mixes background beat and all sound events into a single synced WAV file."""
    total_samples = int(duration * sample_rate) + sample_rate  # extra buffer
    mixed = np.zeros(total_samples, dtype=np.float32)
    
    # 1. Load sound effect files
    def load_wav(filename: str):
        path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(path):
            generate_all_sounds()
        sr, data = wavfile.read(path)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        return data

    sfx = {
        "cut": load_wav("cut.wav"),
        "bounce": load_wav("bounce.wav"),
        "eliminate": load_wav("eliminate.wav"),
        "victory": load_wav("victory.wav"),
        "beat": load_wav("beat.wav"),
        "tick": load_wav("tick.wav"),
        "lock": load_wav("lock.wav"),
        "start": load_wav("start.wav")
    }

    # 2. Add subtle background beat
    beat_data = sfx["beat"]
    beat_len = len(beat_data)
    pos = 0
    while pos < total_samples:
        chunk = min(beat_len, total_samples - pos)
        mixed[pos:pos + chunk] += beat_data[:chunk] * 0.35
        pos += chunk

    # 3. Overlay simulation sound events
    # Limit dense cut events to avoid ear-piercing audio clipping
    last_cut_sample = -1000
    for t, event_type in sound_events:
        idx = int(t * sample_rate)
        if idx >= total_samples:
            continue
            
        if event_type == "cut":
            if idx - last_cut_sample < int(0.03 * sample_rate):
                continue
            last_cut_sample = idx
            
        data = sfx.get(event_type)
        if data is not None:
            end_idx = min(total_samples, idx + len(data))
            chunk_len = end_idx - idx
            # Adjust volume per event type
            vol = 0.9 if event_type in ("eliminate", "victory") else (0.5 if event_type == "cut" else 0.15)
            mixed[idx:end_idx] += data[:chunk_len] * vol

    # Normalize audio
    max_val = np.max(np.abs(mixed))
    if max_val > 0.001:
        mixed = mixed / max_val * 0.92
        
    out_audio = os.path.join(OUTPUT_DIR, "temp_mixed_audio.wav")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    wavfile.write(out_audio, sample_rate, (mixed * 32767).astype(np.int16))
    return out_audio

def generate_battle_video(
    countries: Optional[List[str]] = None,
    total_lines: int = 30,
    output_filename: Optional[str] = None,
    width: int = 1080,
    height: int = 1920,
    fps: int = 60,
    max_duration: float = 65.0,
    intro_duration: float = 4.8,
    return_meta: bool = False
) -> Any:
    """Simulates and renders a complete flag battle video ready for Facebook Pages / Reels."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ffmpeg_exe = find_ffmpeg()
    
    # If no countries given, pick 3 or 4 random countries from database
    all_countries = list(COUNTRY_DATABASE.keys())
    if not countries or len(countries) < 2:
        count = random.choice([3, 4])
        countries = random.sample(all_countries, count)
        
    print(f"\n==========================================")
    print(f"🎬 Starting Flag Battle Video Generation")
    print(f"🎲 Random Selection Intro: {intro_duration:.1f}s")
    print(f"⚔️  Participants ({len(countries)}): {', '.join(countries)}")
    print(f"📏 Initial Lines per flag: {total_lines}")
    print(f"📐 Resolution: {width}x{height} @ {fps}fps")
    print(f"==========================================")

    # Preload flag textures for participants and roulette pool
    roulette_pool = list(set(all_countries[:15] + countries))
    preload_countries(roulette_pool)
    generate_all_sounds()

    # Initialize Pygame and simulation
    pygame.init()
    surface = pygame.Surface((width, height))
    renderer = BattleRenderer(width, height)
    renderer.load_flag_textures(roulette_pool)
    
    # Seed for deterministic simulation across simulation and rendering passes
    sim_seed = random.randint(1, 999999)
    random.seed(sim_seed)
    
    sim = BattleSimulator(countries, total_lines=total_lines, width=width, height=height)
    
    # 1. Run simulation pass to calculate motion, cuts, and timestamps
    print("▶️  Simulating physics and battle outcomes...")
    dt = 1.0 / fps
    
    step = 0
    t0 = time.time()
    while not sim.is_finished() and sim.time < max_duration:
        sim.update(dt)
        step += 1
        
    battle_duration = sim.time
    total_battle_frames = step
    total_intro_frames = int(intro_duration * fps)
    total_frames = total_intro_frames + total_battle_frames
    total_duration = intro_duration + battle_duration
    winner_name = sim.winner.name if sim.winner else "None"
    print(f"🏆 Battle finished in {battle_duration:.1f}s! Total video with intro: {total_duration:.1f}s. Winner: {winner_name}!")
    
    # 2. Build combined audio track (Intro sound effects + Battle sound effects)
    print("🎵 Mixing sound effects and background rhythm...")
    combined_sound_events = []
    
    # Intro sound events (roulette ticks, lock slams, battle start horn)
    n = len(countries)
    lock_times = [0.9 + i * (intro_duration * 0.65 / max(1, n - 1)) for i in range(n)]
    
    # Rapid tick sound during slot spin
    t_tick = 0.2
    while t_tick < lock_times[-1]:
        combined_sound_events.append((float(t_tick), "tick"))
        t_tick += 0.14
        
    # Lock slams for each country
    for lt in lock_times:
        combined_sound_events.append((float(lt), "lock"))
        
    # Start horn
    combined_sound_events.append((float(max(0.0, intro_duration - 1.2)), "start"))
    
    # Add simulation events with intro_duration time offset
    for t_sim, ev in sim.sound_events:
        combined_sound_events.append((intro_duration + t_sim, ev))
        
    audio_path = build_audio_track(combined_sound_events, total_duration)

    # 3. Setup output file
    if not output_filename:
        c_short = "_vs_".join([c[:3].upper() for c in countries])
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"flag_battle_{c_short}_{timestamp}.mp4"
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)

    # 4. Render frames and pipe to ffmpeg
    print(f"🎥 Rendering video frames to MP4 ({final_output_path})...")
    
    # Reset simulation with the exact same seed for 100% synchronized rendering
    random.seed(sim_seed)
    sim_render = BattleSimulator(countries, total_lines=total_lines, width=width, height=height)
    
    cmd = [
        ffmpeg_exe, "-y",
        "-loglevel", "warning",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",               # Input 0: Raw video frames via stdin pipe
        "-i", audio_path,        # Input 1: Mixed audio WAV
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",            # Crisp high visual quality
        "-pix_fmt", "yuv420p",   # Broad mobile & social media compatibility
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_output_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    render_start = time.time()
    
    # Phase 1: Render Intro Roulette Selection Frames
    for intro_idx in range(total_intro_frames):
        t_intro = intro_idx / fps
        renderer.render_intro_frame(countries, roulette_pool, t_intro, intro_duration, surface)
        frame_bytes = pygame.image.tobytes(surface, "RGB")
        try:
            proc.stdin.write(frame_bytes)
        except (BrokenPipeError, OSError):
            break
            
        if (intro_idx + 1) % 120 == 0:
            pct = (intro_idx + 1) / total_frames * 100
            elapsed = time.time() - render_start
            cur_fps = (intro_idx + 1) / (elapsed + 1e-5)
            print(f"   [Intro Selection] {pct:5.1f}% | Frame {intro_idx + 1}/{total_frames} | {cur_fps:.1f} fps", flush=True)

    # Phase 2: Render Arena Battle Frames
    for battle_idx in range(total_battle_frames):
        sim_render.update(dt)
        renderer.render_frame(sim_render, surface)
        frame_bytes = pygame.image.tobytes(surface, "RGB")
        try:
            proc.stdin.write(frame_bytes)
        except (BrokenPipeError, OSError):
            break
            
        global_idx = total_intro_frames + battle_idx + 1
        if global_idx % 150 == 0 or battle_idx == total_battle_frames - 1:
            pct = global_idx / total_frames * 100
            elapsed = time.time() - render_start
            cur_fps = global_idx / (elapsed + 1e-5)
            print(f"   [Battle Royale]   {pct:5.1f}% | Frame {global_idx}/{total_frames} | {cur_fps:.1f} fps", flush=True)

    proc.stdin.close()
    proc.wait()
    
    # Clean up temp audio
    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except OSError:
            pass

    total_time = time.time() - t0
    file_size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
    print(f"\n✅ Video generation complete in {total_time:.1f}s!")
    print(f"📦 Output file: {final_output_path} ({file_size_mb:.2f} MB)")
    print(f"👑 Winner: {winner_name}\n", flush=True)
    if return_meta:
        return final_output_path, countries, winner_name
    return final_output_path

if __name__ == "__main__":
    # Test generation with 3 countries from the user's uploaded screenshot
    test_countries = ["Germany", "Austria", "Ireland"]
    generate_battle_video(test_countries, total_lines=30, max_duration=60.0)
