import math
import random
from typing import List, Dict, Any, Tuple
from countries import COUNTRY_DATABASE

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], size: float, life: float, ptype: str = "spark"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life
        self.ptype = ptype
        self.gravity = 120.0 if ptype == "confetti" else 0.0

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0

class FlagBall:
    def __init__(self, name: str, cx: float, cy: float, arena_r: float, base_angle: float, total_lines: int = 30):
        self.name = name
        info = COUNTRY_DATABASE.get(name, COUNTRY_DATABASE["Germany"])
        self.laser_color = info["laser_color"]
        self.radius = 38.0
        self.max_lines = total_lines
        self.total_lines = total_lines
        self.is_alive = True
        self.base_angle = base_angle
        
        # Initial position: placed near the circle edge where it starts
        spawn_dist = arena_r * 0.75
        self.x = cx + spawn_dist * math.cos(base_angle)
        self.y = cy + spawn_dist * math.sin(base_angle)
        
        # Initial velocity: moving towards the arena center with random angle
        to_center_angle = math.atan2(cy - self.y, cx - self.x)
        speed = random.uniform(250.0, 310.0)
        perturb = random.uniform(-0.4, 0.4)
        move_angle = to_center_angle + perturb
        self.vx = speed * math.cos(move_angle)
        self.vy = speed * math.sin(move_angle)
        
        # Generate initial lines anchored where it touched the circle at start
        # Spanning an arc around its initial touch point on the circle
        arc_span = math.radians(65.0)
        self.anchors: List[Tuple[float, float]] = []
        for i in range(total_lines):
            offset = 0.0 if total_lines == 1 else (i / (total_lines - 1) - 0.5) * arc_span
            angle = base_angle + offset
            ax = cx + arena_r * math.cos(angle)
            ay = cy + arena_r * math.sin(angle)
            self.anchors.append((ax, ay))
            
        self.last_wall_touch_time = -1.0
        self.eliminated_at = None

class BattleSimulator:
    def __init__(self, countries: List[str], total_lines: int = 30, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        self.arena_cx = width / 2.0
        self.arena_cy = 920.0
        self.arena_r = 430.0
        self.total_lines = total_lines
        
        self.flags: List[FlagBall] = []
        n = len(countries)
        base_rotation = random.uniform(0, 2 * math.pi)
        for i, c_name in enumerate(countries):
            angle = base_rotation + (2.0 * math.pi * i) / n
            ball = FlagBall(c_name, self.arena_cx, self.arena_cy, self.arena_r, angle, total_lines)
            self.flags.append(ball)
            
        self.particles: List[Particle] = []
        self.sound_events: List[Tuple[float, str]] = []  # (timestamp, sound_name)
        self.events_log: List[Dict[str, Any]] = []
        
        self.time = 0.0
        self.winner: FlagBall = None
        self.game_over = False
        self.victory_timer = 0.0
        self.max_victory_time = 4.0  # seconds to celebrate winner

    def update(self, dt: float):
        self.time += dt
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # If game is over, celebrate winner with confetti
        if self.game_over:
            self.victory_timer += dt
            if random.random() < 0.4:
                # Add confetti
                cx = random.uniform(self.arena_cx - self.arena_r, self.arena_cx + self.arena_r)
                cy = self.arena_cy - self.arena_r + random.uniform(-50, 50)
                colors = [(255, 215, 0), (255, 50, 50), (50, 255, 50), (50, 150, 255), (255, 100, 255)]
                p = Particle(cx, cy, random.uniform(-60, 60), random.uniform(80, 200), random.choice(colors), random.uniform(6, 12), random.uniform(2.0, 3.5), "confetti")
                self.particles.append(p)
            return

        alive_flags = [f for f in self.flags if f.is_alive]
        
        # 1. Update flag positions & Arena wall collisions
        for f in alive_flags:
            f.x += f.vx * dt
            f.y += f.vy * dt
            
            # Distance from arena center
            dx = f.x - self.arena_cx
            dy = f.y - self.arena_cy
            dist = math.hypot(dx, dy)
            max_dist = self.arena_r - f.radius
            
            if dist > max_dist:
                # Collision normal
                nx = dx / dist
                ny = dy / dist
                f.x = self.arena_cx + nx * max_dist
                f.y = self.arena_cy + ny * max_dist
                
                # Reflect velocity: v' = v - 2(v . n)n
                dot = f.vx * nx + f.vy * ny
                f.vx = f.vx - 2 * dot * nx
                f.vy = f.vy - 2 * dot * ny
                
                # Tiny random angle perturbance (up to +/- 5 deg)
                speed = math.hypot(f.vx, f.vy)
                ang = math.atan2(f.vy, f.vx) + random.uniform(-0.08, 0.08)
                f.vx = speed * math.cos(ang)
                f.vy = speed * math.sin(ang)
                
                self.sound_events.append((self.time, "bounce"))
                
                # Wall touch creates a line from the exact contact point on the circle
                if self.time - f.last_wall_touch_time > 0.12:
                    f.last_wall_touch_time = self.time
                    contact_x = self.arena_cx + nx * self.arena_r
                    contact_y = self.arena_cy + ny * self.arena_r
                    
                    if len(f.anchors) < f.max_lines:
                        f.anchors.append((contact_x, contact_y))
                    else:
                        # Replace oldest anchor with new contact point
                        f.anchors.pop(0)
                        f.anchors.append((contact_x, contact_y))
                
                # Wall spark
                for _ in range(4):
                    self.particles.append(Particle(
                        f.x, f.y,
                        random.uniform(-80, 80) - nx * 60,
                        random.uniform(-80, 80) - ny * 60,
                        (255, 255, 255),
                        random.uniform(2, 4),
                        random.uniform(0.15, 0.3)
                    ))

        # 2. Flag-to-Flag Elastic Collisions
        for i in range(len(alive_flags)):
            for j in range(i + 1, len(alive_flags)):
                f1 = alive_flags[i]
                f2 = alive_flags[j]
                dx = f2.x - f1.x
                dy = f2.y - f1.y
                dist = math.hypot(dx, dy)
                min_dist = f1.radius + f2.radius
                
                if dist < min_dist and dist > 0.001:
                    nx = dx / dist
                    ny = dy / dist
                    overlap = min_dist - dist
                    f1.x -= nx * (overlap * 0.5)
                    f1.y -= ny * (overlap * 0.5)
                    f2.x += nx * (overlap * 0.5)
                    f2.y += ny * (overlap * 0.5)
                    
                    # Elastic collision impulse
                    k = 2 * (f1.vx * nx + f1.vy * ny - f2.vx * nx - f2.vy * ny) / 2.0
                    f1.vx -= k * nx
                    f1.vy -= k * ny
                    f2.vx += k * nx
                    f2.vy += k * ny
                    self.sound_events.append((self.time, "bounce"))

        # 3. Line-to-Flag Slicing / Cutting
        # When an opposing flag touches lines, ALL lines it touches are cut immediately!
        # ("how many touch equal to that many lines cut")
        for b in alive_flags:
            for a in alive_flags:
                if a == b or not a.is_alive or len(a.anchors) == 0:
                    continue
                
                to_cut_indices = []
                cut_sparks = []
                
                for idx, (ax, ay) in enumerate(a.anchors):
                    vx = ax - a.x
                    vy = ay - a.y
                    seg_len_sq = vx * vx + vy * vy
                    if seg_len_sq == 0:
                        continue
                    
                    t = ((b.x - a.x) * vx + (b.y - a.y) * vy) / seg_len_sq
                    t = max(0.0, min(1.0, t))
                    
                    # Closest point on line segment
                    qx = a.x + t * vx
                    qy = a.y + t * vy
                    dist_to_line = math.hypot(b.x - qx, b.y - qy)
                    
                    # If flag B touches this line (and isn't inside flag A's body)
                    if dist_to_line < b.radius and t > 0.12:
                        to_cut_indices.append(idx)
                        cut_sparks.append((qx, qy))
                
                # Cut all touched lines at once
                if to_cut_indices:
                    # Pop from highest index to lowest
                    for idx in reversed(to_cut_indices):
                        a.anchors.pop(idx)
                    
                    self.sound_events.append((self.time, "cut"))
                    
                    # Trigger spark particles for every cut line
                    for (qx, qy) in cut_sparks:
                        for _ in range(6):
                            sp_ang = random.uniform(0, 2 * math.pi)
                            sp_speed = random.uniform(80, 220)
                            self.particles.append(Particle(
                                qx, qy,
                                sp_speed * math.cos(sp_ang),
                                sp_speed * math.sin(sp_ang),
                                a.laser_color,
                                random.uniform(3, 5),
                                random.uniform(0.15, 0.35)
                            ))

        # 4. Check for Eliminations
        for f in alive_flags:
            if len(f.anchors) == 0:
                f.is_alive = False
                f.eliminated_at = self.time
                self.sound_events.append((self.time, "eliminate"))
                self.events_log.append({
                    "time": self.time,
                    "event": "elimination",
                    "country": f.name
                })
                # Big explosion of particles
                for _ in range(45):
                    ang = random.uniform(0, 2 * math.pi)
                    spd = random.uniform(100, 360)
                    self.particles.append(Particle(
                        f.x, f.y,
                        spd * math.cos(ang),
                        spd * math.sin(ang),
                        f.laser_color,
                        random.uniform(4, 9),
                        random.uniform(0.4, 0.8)
                    ))

        # 5. Check for Winner
        remaining = [f for f in self.flags if f.is_alive]
        
        # Sudden-death speed boost if battle takes > 18s to guarantee exciting pacing
        if self.time > 18.0 and len(remaining) <= 2:
            for f in remaining:
                spd = math.hypot(f.vx, f.vy)
                if spd < 460.0:
                    f.vx *= 1.0008
                    f.vy *= 1.0008

        if len(remaining) == 1 and not self.game_over:
            self.winner = remaining[0]
            self.game_over = True
            self.sound_events.append((self.time, "victory"))
            self.events_log.append({
                "time": self.time,
                "event": "winner",
                "country": self.winner.name
            })
            # Immediate victory confetti
            for _ in range(70):
                ang = random.uniform(0, 2 * math.pi)
                spd = random.uniform(150, 400)
                colors = [(255, 215, 0), (255, 255, 255), self.winner.laser_color]
                self.particles.append(Particle(
                    self.winner.x, self.winner.y,
                    spd * math.cos(ang),
                    spd * math.sin(ang),
                    random.choice(colors),
                    random.uniform(5, 10),
                    random.uniform(1.2, 2.5),
                    "confetti"
                ))

    def is_finished(self) -> bool:
        """Returns True when victory celebration has concluded or timeout reached."""
        if self.game_over and self.victory_timer >= self.max_victory_time:
            return True
        if self.time > 75.0:  # Safety upper bound
            return True
        return False
