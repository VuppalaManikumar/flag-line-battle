#!/usr/bin/env python3
"""
Flag Line Battle - Interactive Web Studio & Video Generator.
Run this script to launch a modern browser interface for previewing battles live,
customizing countries, and generating high-res MP4 videos for Facebook Reels.
"""

import os
import sys
import glob
import random
import threading
from flask import Flask, render_template_string, jsonify, request, send_from_directory
from countries import COUNTRY_DATABASE, get_flag_path, preload_countries
from video_builder import generate_battle_video, OUTPUT_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = Flask(__name__)
FLAGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "flags")

# Track generation status
generation_lock = threading.Lock()
current_task = {
    "status": "idle",
    "progress": 0,
    "message": "",
    "last_file": ""
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flag Line Battle Studio - Viral Video Generator</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0a0e17;
            --bg-card: #121826;
            --bg-card-hover: #182236;
            --accent-cyan: #00f0ff;
            --accent-pink: #ff007f;
            --accent-gold: #ffd700;
            --text-main: #f0f4fc;
            --text-dim: #8fa0c0;
            --border-col: #1f2b42;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            padding: 20px 40px;
            background: rgba(18, 24, 38, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-col);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .logo-box {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .logo-icon {
            font-size: 32px;
            filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.6));
        }
        .logo-text h1 {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 1px;
            background: linear-gradient(135deg, #00f0ff, #ff007f);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo-text p {
            font-size: 13px;
            color: var(--text-dim);
        }
        .badge-reel {
            background: linear-gradient(135deg, #ff007f, #8a2be2);
            color: #fff;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        main {
            display: grid;
            grid-template-columns: 380px 1fr 380px;
            gap: 24px;
            padding: 28px 40px;
            flex: 1;
        }
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-col);
            border-radius: 20px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }
        .panel-title {
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-main);
            border-bottom: 1px solid var(--border-col);
            padding-bottom: 12px;
        }
        /* Country picker styling */
        .preset-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .btn-preset {
            background: var(--bg-card-hover);
            border: 1px solid var(--border-col);
            color: var(--text-dim);
            padding: 10px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-preset:hover {
            border-color: var(--accent-cyan);
            color: var(--text-main);
            transform: translateY(-2px);
        }
        .country-selector {
            max-height: 240px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-right: 6px;
        }
        .country-selector::-webkit-scrollbar { width: 6px; }
        .country-selector::-webkit-scrollbar-thumb { background: var(--border-col); border-radius: 3px; }
        .country-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background: rgba(255,255,255,0.03);
            border: 1px solid transparent;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .country-item:hover {
            background: var(--bg-card-hover);
        }
        .country-item.selected {
            background: rgba(0, 240, 255, 0.12);
            border-color: var(--accent-cyan);
        }
        .country-info {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 600;
        }
        .color-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .check-box {
            font-size: 14px;
            color: var(--accent-cyan);
        }
        /* Sliders */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .form-group label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-dim);
            display: flex;
            justify-content: space-between;
        }
        input[type="range"] {
            width: 100%;
            accent-color: var(--accent-cyan);
        }
        /* Canvas Center View */
        .preview-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }
        .canvas-wrapper {
            position: relative;
            width: 360px;
            height: 640px; /* 9:16 aspect ratio */
            background: #060911;
            border-radius: 28px;
            overflow: hidden;
            border: 3px solid #202b40;
            box-shadow: 0 15px 40px rgba(0,0,0,0.6), 0 0 30px rgba(0, 240, 255, 0.15);
        }
        #simCanvas {
            width: 100%;
            height: 100%;
            display: block;
        }
        .canvas-controls {
            display: flex;
            gap: 12px;
            width: 360px;
        }
        .btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-secondary {
            background: var(--bg-card);
            border: 1px solid var(--border-col);
            color: var(--text-main);
        }
        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-cyan);
        }
        .btn-primary {
            background: linear-gradient(135deg, #00f0ff, #0077ff);
            color: #000;
            box-shadow: 0 4px 15px rgba(0, 240, 255, 0.4);
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 240, 255, 0.6);
        }
        .btn-generate {
            background: linear-gradient(135deg, #ff007f, #ff5e00);
            color: #fff;
            box-shadow: 0 6px 25px rgba(255, 0, 127, 0.5);
            font-size: 16px;
            padding: 16px;
        }
        .btn-generate:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(255, 0, 127, 0.7);
        }
        .btn-generate:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        /* Right Panel: Video Library */
        .video-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
            max-height: 480px;
            overflow-y: auto;
            padding-right: 6px;
        }
        .video-item {
            background: var(--bg-card-hover);
            border: 1px solid var(--border-col);
            border-radius: 14px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: all 0.2s ease;
        }
        .video-item:hover {
            border-color: var(--accent-cyan);
        }
        .video-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .video-title {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-main);
            word-break: break-all;
        }
        .video-size {
            font-size: 12px;
            color: var(--text-dim);
        }
        .video-actions {
            display: flex;
            gap: 8px;
        }
        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .status-box {
            background: rgba(0,0,0,0.3);
            border: 1px solid var(--border-col);
            border-radius: 12px;
            padding: 14px;
            font-size: 13px;
            display: none;
        }
        .status-box.active { display: block; }
        .progress-bar-bg {
            height: 8px;
            background: #1f2b42;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff007f, #00f0ff);
            width: 0%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>

<header>
    <div class="logo-box">
        <div class="logo-icon">⚔️</div>
        <div class="logo-text">
            <h1>FLAG LINE BATTLE STUDIO</h1>
            <p>Viral Vertical Video Generator (1080x1920 HD @ 60 FPS)</p>
        </div>
    </div>
    <div class="badge-reel">Designed for Facebook Reels & Shorts</div>
</header>

<main>
    <!-- LEFT PANEL: CUSTOMIZATION -->
    <div class="panel">
        <div class="panel-title"><span>⚙️</span> Battle Setup</div>
        
        <div class="form-group">
            <label>Quick Presets</label>
            <div class="preset-buttons">
                <button class="btn-preset" onclick="selectPreset('random3')">🎲 Random 3</button>
                <button class="btn-preset" onclick="selectPreset('random4')">🎲 Random 4</button>
                <button class="btn-preset" onclick="selectPreset('europe')">🇪🇺 Europe Battle</button>
                <button class="btn-preset" onclick="selectPreset('americas')">🌎 Americas War</button>
            </div>
        </div>

        <div class="form-group">
            <label><span>Select Countries (<span id="selectedCount">3</span> selected)</span></label>
            <div class="country-selector" id="countryList">
                <!-- Injected via JavaScript -->
            </div>
        </div>

        <div class="form-group">
            <label><span>Initial Lines per Flag</span><span id="linesVal">30</span></label>
            <input type="range" id="linesInput" min="10" max="50" value="30" oninput="document.getElementById('linesVal').innerText=this.value; restartSim();">
        </div>

        <div class="form-group">
            <label><span>Flag Move Speed</span><span id="speedVal">1.0x</span></label>
            <input type="range" id="speedInput" min="0.6" max="2.0" step="0.1" value="1.0" oninput="document.getElementById('speedVal').innerText=this.value+'x';">
        </div>
    </div>

    <!-- CENTER PANEL: LIVE SIMULATION PREVIEW -->
    <div class="preview-container">
        <div class="canvas-wrapper">
            <canvas id="simCanvas" width="540" height="960"></canvas>
        </div>
        <div class="canvas-controls">
            <button class="btn btn-secondary" onclick="restartSim()">🔄 Replay Simulation</button>
            <button class="btn btn-secondary" onclick="randomizeAll()">🎲 Randomize</button>
        </div>
        
        <button class="btn btn-generate" id="btnExport" onclick="exportMP4()" style="width: 360px;">
            ⚡ Render 1080x1920 MP4 Video
        </button>

        <div class="status-box" id="statusBox" style="width: 360px;">
            <div id="statusText">Simulating battle & encoding MP4...</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progressFill"></div>
            </div>
        </div>
    </div>

    <!-- RIGHT PANEL: VIDEO LIBRARY -->
    <div class="panel">
        <div class="panel-title">
            <span>🎬</span> Generated Videos
            <button class="btn-preset" style="margin-left:auto;" onclick="batchGenerate(3)">🔥 Batch 3</button>
        </div>
        <p style="font-size: 13px; color: var(--text-dim);">
            Videos are rendered directly to 1080x1920 MP4 with synced sound effects, ready to upload to Facebook Pages & Reels.
        </p>

        <div class="video-list" id="videoList">
            <!-- Populated via JS -->
        </div>
    </div>
</main>

<script>
const COUNTRY_DB = {{ country_data|tojson }};
let selectedCountries = ["Germany", "Austria", "Ireland"];

function renderCountryList() {
    const container = document.getElementById("countryList");
    container.innerHTML = "";
    Object.keys(COUNTRY_DB).sort().forEach(c => {
        const item = document.createElement("div");
        const isSel = selectedCountries.includes(c);
        item.className = "country-item" + (isSel ? " selected" : "");
        const hex = COUNTRY_DB[c].hex || "#00f0ff";
        
        item.innerHTML = `
            <div class="country-info">
                <span class="color-dot" style="background:${hex}; box-shadow: 0 0 6px ${hex};"></span>
                <span>${c}</span>
            </div>
            <span class="check-box">${isSel ? "✓" : ""}</span>
        `;
        item.onclick = () => toggleCountry(c);
        container.appendChild(item);
    });
    document.getElementById("selectedCount").innerText = selectedCountries.length;
}

function toggleCountry(c) {
    const idx = selectedCountries.indexOf(c);
    if (idx >= 0) {
        if (selectedCountries.length > 2) {
            selectedCountries.splice(idx, 1);
        } else {
            alert("Minimum 2 countries required for battle!");
        }
    } else {
        if (selectedCountries.length < 6) {
            selectedCountries.push(c);
        } else {
            alert("Maximum 6 countries for best visuals!");
        }
    }
    renderCountryList();
    restartSim();
}

function selectPreset(type) {
    const all = Object.keys(COUNTRY_DB);
    if (type === "random3") {
        selectedCountries = shuffle(all).slice(0, 3);
    } else if (type === "random4") {
        selectedCountries = shuffle(all).slice(0, 4);
    } else if (type === "europe") {
        selectedCountries = ["Germany", "France", "Italy", "Spain"];
    } else if (type === "americas") {
        selectedCountries = ["United States", "Brazil", "Argentina", "Canada"];
    }
    renderCountryList();
    restartSim();
}

function randomizeAll() {
    selectPreset(Math.random() > 0.5 ? "random3" : "random4");
}

function shuffle(arr) {
    return [...arr].sort(() => Math.random() - 0.5);
}

/* --- LIVE CANVAS SIMULATOR --- */
const canvas = document.getElementById("simCanvas");
const ctx = canvas.getContext("2d");

const ARENA_CX = 270;
const ARENA_CY = 450;
const ARENA_R = 210;
const BALL_R = 18;

let simFlags = [];
let simParticles = [];
let simOver = false;
let simWinner = null;
let animationFrameId = null;

class SimBall {
    constructor(name, baseAngle, totalLines) {
        this.name = name;
        this.color = COUNTRY_DB[name]?.hex || "#00f0ff";
        this.baseAngle = baseAngle;
        this.totalLines = totalLines;
        this.isAlive = true;
        
        const dist = ARENA_R * 0.45;
        this.x = ARENA_CX + dist * Math.cos(baseAngle);
        this.y = ARENA_CY + dist * Math.sin(baseAngle);
        
        const toCenter = Math.atan2(ARENA_CY - this.y, ARENA_CX - this.x);
        const speed = 140 + Math.random() * 40;
        const ang = toCenter + (Math.random() - 0.5) * 0.8;
        this.vx = speed * Math.cos(ang);
        this.vy = speed * Math.sin(ang);
        
        const arc = 1.1; // ~65 deg
        this.anchors = [];
        for (let i = 0; i < totalLines; i++) {
            const off = totalLines === 1 ? 0 : (i / (totalLines - 1) - 0.5) * arc;
            const a = baseAngle + off;
            this.anchors.push({
                x: ARENA_CX + ARENA_R * Math.cos(a),
                y: ARENA_CY + ARENA_R * Math.sin(a)
            });
        }
        this.lastCut = 0;
    }
}

function restartSim() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    simFlags = [];
    simParticles = [];
    simOver = false;
    simWinner = null;
    
    const lines = parseInt(document.getElementById("linesInput").value);
    const n = selectedCountries.length;
    const baseRot = Math.random() * Math.PI * 2;
    
    selectedCountries.forEach((c, i) => {
        const ang = baseRot + (i * 2 * Math.PI) / n;
        simFlags.push(new SimBall(c, ang, lines));
    });
    
    lastTime = performance.now();
    loop();
}

let lastTime = 0;
function loop() {
    const now = performance.now();
    const dt = Math.min(0.05, (now - lastTime) / 1000);
    lastTime = now;
    
    update(dt);
    draw();
    
    animationFrameId = requestAnimationFrame(loop);
}

function update(dt) {
    const speedScale = parseFloat(document.getElementById("speedInput").value);
    const alive = simFlags.filter(f => f.isAlive);
    
    // Update particles
    simParticles = simParticles.filter(p => {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.life -= dt;
        return p.life > 0;
    });

    if (simOver) return;

    // Movement & Arena Wall Collisions
    alive.forEach(f => {
        f.x += f.vx * dt * speedScale;
        f.y += f.vy * dt * speedScale;
        
        const dx = f.x - ARENA_CX;
        const dy = f.y - ARENA_CY;
        const d = Math.hypot(dx, dy);
        const maxD = ARENA_R - BALL_R;
        
        if (d > maxD) {
            const nx = dx / d;
            const ny = dy / d;
            f.x = ARENA_CX + nx * maxD;
            f.y = ARENA_CY + ny * maxD;
            
            const dot = f.vx * nx + f.vy * ny;
            f.vx = f.vx - 2 * dot * nx;
            f.vy = f.vy - 2 * dot * ny;

            // Touch circle creates a line from the exact contact point
            const now = nowSec();
            if (now - (f.lastWallTouch || 0) > 0.12) {
                f.lastWallTouch = now;
                const contactX = ARENA_CX + nx * ARENA_R;
                const contactY = ARENA_CY + ny * ARENA_R;
                if (f.anchors.length < f.totalLines) {
                    f.anchors.push({x: contactX, y: contactY});
                } else {
                    f.anchors.shift();
                    f.anchors.push({x: contactX, y: contactY});
                }
            }
        }
    });

    // Flag vs Flag Bounce
    for (let i = 0; i < alive.length; i++) {
        for (let j = i + 1; j < alive.length; j++) {
            const f1 = alive[i];
            const f2 = alive[j];
            const dx = f2.x - f1.x;
            const dy = f2.y - f1.y;
            const dist = Math.hypot(dx, dy);
            if (dist < BALL_R * 2 && dist > 0.001) {
                const nx = dx / dist;
                const ny = dy / dist;
                const k = (f1.vx * nx + f1.vy * ny - f2.vx * nx - f2.vy * ny);
                f1.vx -= k * nx;
                f1.vy -= k * ny;
                f2.vx += k * nx;
                f2.vy += k * ny;
            }
        }
    }

    // Line Cutting: cut all lines touched by opponent ("how many touch equal to that many lines cut")
    alive.forEach(b => {
        alive.forEach(a => {
            if (a === b || !a.isAlive || a.anchors.length === 0) return;
            const toCut = [];
            for (let idx = 0; idx < a.anchors.length; idx++) {
                const anc = a.anchors[idx];
                const vx = anc.x - a.x;
                const vy = anc.y - a.y;
                const lenSq = vx * vx + vy * vy;
                if (lenSq === 0) continue;
                
                let t = ((b.x - a.x) * vx + (b.y - a.y) * vy) / lenSq;
                t = Math.max(0, Math.min(1, t));
                const qx = a.x + t * vx;
                const qy = a.y + t * vy;
                const dist = Math.hypot(b.x - qx, b.y - qy);
                
                if (dist < BALL_R && t > 0.12) {
                    toCut.push({idx, qx, qy});
                }
            }
            if (toCut.length > 0) {
                for (let i = toCut.length - 1; i >= 0; i--) {
                    const c = toCut[i];
                    a.anchors.splice(c.idx, 1);
                    for (let s = 0; s < 4; s++) {
                        const ang = Math.random() * Math.PI * 2;
                        const spd = 40 + Math.random() * 80;
                        simParticles.push({
                            x: c.qx, y: c.qy,
                            vx: spd * Math.cos(ang),
                            vy: spd * Math.sin(ang),
                            color: a.color,
                            life: 0.25, maxLife: 0.25, size: 2
                        });
                    }
                }
            }
        });
    });

    // Check Eliminations
    alive.forEach(f => {
        if (f.anchors.length === 0) {
            f.isAlive = false;
            // Explosion
            for (let s = 0; s < 30; s++) {
                const ang = Math.random() * Math.PI * 2;
                const spd = 60 + Math.random() * 120;
                simParticles.push({
                    x: f.x, y: f.y,
                    vx: spd * Math.cos(ang),
                    vy: spd * Math.sin(ang),
                    color: f.color,
                    life: 0.5, maxLife: 0.5, size: 3
                });
            }
        }
    });

    // Check Winner
    const remaining = simFlags.filter(f => f.isAlive);
    if (remaining.length === 1 && !simOver) {
        simOver = true;
        simWinner = remaining[0];
    }
}

function nowSec() { return performance.now() / 1000; }

function draw() {
    ctx.fillStyle = "#0a0e17";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Glowing Arena Circle
    ctx.save();
    ctx.strokeStyle = "rgba(0, 240, 255, 0.4)";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.arc(ARENA_CX, ARENA_CY, ARENA_R, 0, Math.PI * 2);
    ctx.stroke();

    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(ARENA_CX, ARENA_CY, ARENA_R, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // Lines
    simFlags.forEach(f => {
        if (!f.isAlive) return;
        ctx.strokeStyle = f.color;
        ctx.lineWidth = 1.6;
        f.anchors.forEach(anc => {
            ctx.beginPath();
            ctx.moveTo(f.x, f.y);
            ctx.lineTo(anc.x, anc.y);
            ctx.stroke();
            
            // Dot on ring
            ctx.fillStyle = f.color;
            ctx.beginPath();
            ctx.arc(anc.x, anc.y, 2.5, 0, Math.PI * 2);
            ctx.fill();
        });
    });

    // Particles
    simParticles.forEach(p => {
        const alpha = p.life / p.maxLife;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
    });

    // Flag Balls
    simFlags.forEach(f => {
        if (!f.isAlive) return;
        
        ctx.save();
        ctx.shadowColor = f.color;
        ctx.shadowBlur = 10;
        ctx.fillStyle = f.color;
        ctx.beginPath();
        ctx.arc(f.x, f.y, BALL_R, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();

        // Lines badge
        ctx.fillStyle = "rgba(10, 14, 23, 0.85)";
        ctx.fillRect(f.x - 14, f.y + BALL_R + 3, 28, 14);
        ctx.strokeStyle = f.color;
        ctx.strokeRect(f.x - 14, f.y + BALL_R + 3, 28, 14);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(f.anchors.length, f.x, f.y + BALL_R + 14);
    });

    // Winner Banner
    if (simOver && simWinner) {
        ctx.fillStyle = "rgba(15, 24, 40, 0.9)";
        ctx.strokeStyle = "#ffd700";
        ctx.lineWidth = 3;
        ctx.fillRect(40, ARENA_CY - 40, canvas.width - 80, 80);
        ctx.strokeRect(40, ARENA_CY - 40, canvas.width - 80, 80);
        
        ctx.fillStyle = "#ffd700";
        ctx.font = "bold 16px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("🏆 WINNER 🏆", canvas.width / 2, ARENA_CY - 12);
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 24px sans-serif";
        ctx.fillText(simWinner.name.toUpperCase(), canvas.width / 2, ARENA_CY + 22);
    }
}

/* --- API CALLS --- */
async function exportMP4() {
    const btn = document.getElementById("btnExport");
    const statusBox = document.getElementById("statusBox");
    const statusText = document.getElementById("statusText");
    const fill = document.getElementById("progressFill");
    
    btn.disabled = true;
    statusBox.classList.add("active");
    statusText.innerText = "Starting video simulation & render...";
    fill.style.width = "20%";

    try {
        const lines = parseInt(document.getElementById("linesInput").value);
        const res = await fetch("/api/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                countries: selectedCountries,
                lines: lines
            })
        });
        fill.style.width = "80%";
        const data = await res.json();
        
        if (data.success) {
            fill.style.width = "100%";
            statusText.innerText = "Video ready: " + data.filename;
            loadVideos();
        } else {
            statusText.innerText = "Error: " + data.error;
        }
    } catch (err) {
        statusText.innerText = "Generation failed: " + err;
    } finally {
        setTimeout(() => {
            btn.disabled = false;
        }, 1500);
    }
}

async function batchGenerate(count) {
    if (!confirm(`Generate ${count} distinct flag battle videos for Facebook Reels?`)) return;
    const statusBox = document.getElementById("statusBox");
    const statusText = document.getElementById("statusText");
    statusBox.classList.add("active");
    statusText.innerText = `Batch generating ${count} videos in background...`;
    
    try {
        await fetch("/api/batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ count: count })
        });
        alert(`Started batch generation of ${count} videos! Check the library in a minute.`);
        loadVideos();
    } catch (e) {
        alert("Batch error: " + e);
    }
}

async function loadVideos() {
    try {
        const res = await fetch("/api/videos");
        const list = await res.json();
        const container = document.getElementById("videoList");
        container.innerHTML = "";
        
        if (list.length === 0) {
            container.innerHTML = "<p style='color:var(--text-dim); font-size:13px;'>No generated videos yet. Click 'Render MP4' to create your first video!</p>";
            return;
        }

        list.forEach(v => {
            const item = document.createElement("div");
            item.className = "video-item";
            item.innerHTML = `
                <div class="video-meta">
                    <span class="video-title">${v.filename}</span>
                    <span class="video-size">${v.size}</span>
                </div>
                <div class="video-actions">
                    <a href="/output/${v.filename}" target="_blank" class="btn btn-secondary btn-small">▶️ Preview</a>
                    <a href="/output/${v.filename}" download class="btn btn-primary btn-small">⬇️ Download</a>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (e) {
        console.error(e);
    }
}

// Initial bootstrap
renderCountryList();
restartSim();
loadVideos();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, country_data=COUNTRY_DATABASE)

@app.route("/api/countries")
def get_countries():
    return jsonify(COUNTRY_DATABASE)

@app.route("/api/videos")
def get_videos():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = glob.glob(os.path.join(OUTPUT_DIR, "*.mp4"))
    files.sort(key=os.path.getmtime, reverse=True)
    res = []
    for f in files:
        name = os.path.basename(f)
        size_mb = os.path.getsize(f) / (1024 * 1024)
        res.append({
            "filename": name,
            "size": f"{size_mb:.2f} MB"
        })
    return jsonify(res)

@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route("/assets/flags/<path:filename>")
def serve_flag(filename):
    return send_from_directory(FLAGS_DIR, filename)

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}
    countries = data.get("countries", ["Germany", "Austria", "Ireland"])
    lines = int(data.get("lines", 30))
    intro_sec = float(data.get("intro_duration", 4.8))
    
    try:
        out_path = generate_battle_video(
            countries=countries,
            total_lines=lines,
            intro_duration=intro_sec
        )
        return jsonify({
            "success": True,
            "filename": os.path.basename(out_path)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/batch", methods=["POST"])
def api_batch():
    data = request.json or {}
    count = int(data.get("count", 3))
    all_c = list(COUNTRY_DATABASE.keys())
    
    def run_batch():
        for _ in range(count):
            k = random.choice([3, 4])
            c_sel = random.sample(all_c, k)
            generate_battle_video(countries=c_sel, total_lines=30, intro_duration=4.8)
            
    threading.Thread(target=run_batch, daemon=True).start()
    return jsonify({"success": True, "message": f"Started {count} videos batch"})

if __name__ == "__main__":
    print("\n🚀 Starting Flag Line Battle Web Studio on http://localhost:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
