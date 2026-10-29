import os
import math
from typing import Dict, List, Tuple
import pygame
from countries import COUNTRY_DATABASE, get_flag_path
from simulator import BattleSimulator, FlagBall

class BattleRenderer:
    def __init__(self, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        
        # Ensure pygame font is ready
        if not pygame.font.get_init():
            pygame.font.init()
            
        # Fonts (Use clean cross-platform fonts that don't produce tofu boxes on Windows or Linux)
        self.font_title = pygame.font.SysFont("Impact, Arial Black, DejaVu Sans, FreeSans, sans-serif", 56)
        self.font_subtitle = pygame.font.SysFont("Arial, DejaVu Sans, FreeSans, sans-serif", 26, bold=True)
        self.font_hud = pygame.font.SysFont("Arial, DejaVu Sans, FreeSans, sans-serif", 22, bold=True)
        self.font_badge = pygame.font.SysFont("Arial, DejaVu Sans, FreeSans, sans-serif", 20, bold=True)
        self.font_winner = pygame.font.SysFont("Impact, Arial Black, DejaVu Sans, FreeSans, sans-serif", 68)
        self.font_elim = pygame.font.SysFont("Impact, Arial Black, DejaVu Sans, FreeSans, sans-serif", 44)
        self.font_cta = pygame.font.SysFont("Arial, DejaVu Sans, FreeSans, sans-serif", 24, bold=True)
        self.font_intro_name = pygame.font.SysFont("Impact, Arial Black, DejaVu Sans, FreeSans, sans-serif", 40)
        self.font_fight = pygame.font.SysFont("Impact, Arial Black, DejaVu Sans, FreeSans, sans-serif", 90)
        
        # Texture cache
        self.flag_textures: Dict[str, pygame.Surface] = {}
        self.hud_flag_textures: Dict[str, pygame.Surface] = {}
        
        # Pre-render static glow surfaces
        self.glow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self.arena_glow = self._create_arena_glow(430.0)

    def _create_arena_glow(self, radius: float) -> pygame.Surface:
        """Pre-renders multi-layer glowing neon ring."""
        size = int((radius + 50) * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        
        # Outer soft glow layers
        glow_colors = [
            (100, 200, 255, 12),
            (120, 210, 255, 20),
            (150, 220, 255, 35),
            (190, 235, 255, 60),
            (230, 245, 255, 130),
            (255, 255, 255, 255)
        ]
        widths = [24, 18, 12, 8, 4, 2]
        
        for col, w in zip(glow_colors, widths):
            pygame.draw.circle(surf, col, center, int(radius), w)
            
        return surf

    def load_flag_textures(self, countries: List[str], ball_radius: float = 38.0):
        """Loads and scales circular flag images."""
        # Ensure a display surface exists so convert_alpha() succeeds in headless mode
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((self.width, self.height))
            
        diameter = int(ball_radius * 2)
        hud_diameter = 42
        
        for c in countries:
            path = get_flag_path(c)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.flag_textures[c] = pygame.transform.smoothscale(img, (diameter, diameter))
                self.hud_flag_textures[c] = pygame.transform.smoothscale(img, (hud_diameter, hud_diameter))
            except Exception as e:
                print(f"Error loading texture for {c}: {e}")
                # Fallback circular surface
                surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                info = COUNTRY_DATABASE.get(c, COUNTRY_DATABASE["Germany"])
                pygame.draw.circle(surf, info.get("bg_color", (100, 100, 100)), (int(ball_radius), int(ball_radius)), int(ball_radius))
                self.flag_textures[c] = surf
                self.hud_flag_textures[c] = pygame.transform.smoothscale(surf, (hud_diameter, hud_diameter))

    def render_frame(self, sim: BattleSimulator, surface: pygame.Surface):
        """Renders one complete 1080x1920 video frame."""
        # 1. Dark sleek background with subtle ambient tint
        surface.fill((10, 14, 22))
        
        # Subtle vignette / background circular glow behind arena
        pygame.draw.circle(surface, (15, 22, 38), (int(sim.arena_cx), int(sim.arena_cy)), int(sim.arena_r * 1.08))

        # 2. Render Arena Glow & Ring
        arena_x = int(sim.arena_cx - self.arena_glow.get_width() // 2)
        arena_y = int(sim.arena_cy - self.arena_glow.get_height() // 2)
        surface.blit(self.arena_glow, (arena_x, arena_y))

        # 3. Render Laser Lines for all alive flags
        # Use an alpha surface for the neon line glow
        self.glow_surf.fill((0, 0, 0, 0))
        
        for f in sim.flags:
            if not f.is_alive or len(f.anchors) == 0:
                continue
                
            col = f.laser_color
            glow_col = (col[0], col[1], col[2], 90)
            core_col = (
                min(255, col[0] + 120),
                min(255, col[1] + 120),
                min(255, col[2] + 120)
            )
            
            p_flag = (int(f.x), int(f.y))
            
            for ax, ay in f.anchors:
                p_anchor = (int(ax), int(ay))
                
                # Outer glow line
                pygame.draw.line(self.glow_surf, glow_col, p_flag, p_anchor, 4)
                # Inner sharp core line
                pygame.draw.line(surface, core_col, p_flag, p_anchor, 2)
                
                # Tiny glowing dot at perimeter anchor point
                pygame.draw.circle(surface, col, p_anchor, 4)
                pygame.draw.circle(surface, (255, 255, 255), p_anchor, 2)
                
        # Blit laser glow
        surface.blit(self.glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

        # 4. Render Particles (sparks, explosions, confetti)
        for p in sim.particles:
            alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
            if p.ptype == "confetti":
                # Rectangle confetti flake
                confetti_surf = pygame.Surface((int(p.size), int(p.size * 0.6)), pygame.SRCALPHA)
                confetti_surf.fill((p.color[0], p.color[1], p.color[2], alpha))
                surface.blit(confetti_surf, (int(p.x), int(p.y)))
            else:
                # Glowing spark dot
                spark_surf = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(spark_surf, (p.color[0], p.color[1], p.color[2], alpha), (int(p.size), int(p.size)), int(p.size))
                surface.blit(spark_surf, (int(p.x - p.size), int(p.y - p.size)), special_flags=pygame.BLEND_ADD)

        # 5. Render Flag Balls
        for f in sim.flags:
            if not f.is_alive:
                continue
                
            fx, fy = int(f.x), int(f.y)
            
            # Neon aura behind flag ball
            aura_size = int(f.radius * 2 + 20)
            aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (f.laser_color[0], f.laser_color[1], f.laser_color[2], 100), (aura_size // 2, aura_size // 2), int(f.radius + 8))
            surface.blit(aura_surf, (fx - aura_size // 2, fy - aura_size // 2), special_flags=pygame.BLEND_ADD)
            
            # Blit circular flag texture
            tex = self.flag_textures.get(f.name)
            if tex:
                surface.blit(tex, (fx - int(f.radius), fy - int(f.radius)))
                
            # Rim border
            pygame.draw.circle(surface, (255, 255, 255), (fx, fy), int(f.radius), 2)
            pygame.draw.circle(surface, f.laser_color, (fx, fy), int(f.radius) + 2, 2)
            
            # Floating line badge under the flag
            badge_text = f"{len(f.anchors)}"
            badge_surf = self.font_badge.render(badge_text, True, (255, 255, 255))
            
            # Badge background pill
            pill_w = max(40, badge_surf.get_width() + 16)
            pill_h = 24
            pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
            pygame.draw.rect(pill_surf, (15, 20, 32, 220), (0, 0, pill_w, pill_h), border_radius=12)
            pygame.draw.rect(pill_surf, f.laser_color, (0, 0, pill_w, pill_h), 2, border_radius=12)
            pill_surf.blit(badge_surf, ((pill_w - badge_surf.get_width()) // 2, (pill_h - badge_surf.get_height()) // 2))
            
            surface.blit(pill_surf, (fx - pill_w // 2, fy + int(f.radius) + 6))

        # 6. Top Header & Title
        title_surf = self.font_title.render("FLAG LINE BATTLE", True, (255, 255, 255))
        title_shadow = self.font_title.render("FLAG LINE BATTLE", True, (0, 180, 255))
        surface.blit(title_shadow, (self.width // 2 - title_surf.get_width() // 2 + 2, 62))
        surface.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 60))
        
        sub_text = "LAST COUNTRY WITH LINES WINS!"
        sub_surf = self.font_subtitle.render(sub_text, True, (255, 215, 0))
        surface.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, 130))

        # 7. Top Scoreboard Cards (HUD)
        self._render_scoreboard(sim, surface)

        # 8. Bottom Call To Action / Social Info
        cta_bg = pygame.Surface((self.width - 120, 64), pygame.SRCALPHA)
        pygame.draw.rect(cta_bg, (18, 25, 40, 200), (0, 0, self.width - 120, 64), border_radius=20)
        pygame.draw.rect(cta_bg, (60, 90, 140, 180), (0, 0, self.width - 120, 64), 2, border_radius=20)
        surface.blit(cta_bg, (60, 1780))
        
        cta_text = "Drop your favorite country in the comments! Follow for more!"
        cta_surf = self.font_cta.render(cta_text, True, (230, 240, 255))
        surface.blit(cta_surf, (self.width // 2 - cta_surf.get_width() // 2, 1798))

        # 9. Elimination Flash Announcement
        self._render_elimination_banner(sim, surface)

        # 10. Winner Grand Celebration
        if sim.game_over and sim.winner:
            self._render_winner_celebration(sim, surface)

    def _render_scoreboard(self, sim: BattleSimulator, surface: pygame.Surface):
        """Draws top HUD cards for each country."""
        n = len(sim.flags)
        card_w = min(230, (self.width - 80) // n - 12)
        card_h = 76
        start_x = (self.width - (n * card_w + (n - 1) * 12)) // 2
        y = 185
        
        for i, f in enumerate(sim.flags):
            x = start_x + i * (card_w + 12)
            
            # Card surface
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            if f.is_alive:
                pygame.draw.rect(card, (20, 28, 45, 210), (0, 0, card_w, card_h), border_radius=14)
                pygame.draw.rect(card, f.laser_color, (0, 0, card_w, card_h), 2, border_radius=14)
                
                # Flag thumbnail
                tex = self.hud_flag_textures.get(f.name)
                if tex:
                    card.blit(tex, (10, (card_h - tex.get_height()) // 2))
                    
                # Name abbreviation & lines count
                short_name = f.name[:7]
                name_surf = self.font_hud.render(short_name, True, (255, 255, 255))
                card.blit(name_surf, (58, 12))
                
                # Lines count bar / text
                lines_text = f"{len(f.anchors)} / {sim.total_lines}"
                lines_surf = self.font_badge.render(lines_text, True, f.laser_color)
                card.blit(lines_surf, (58, 42))
                
            else:
                # Grayed out eliminated card
                pygame.draw.rect(card, (30, 30, 35, 180), (0, 0, card_w, card_h), border_radius=14)
                pygame.draw.rect(card, (150, 40, 40, 160), (0, 0, card_w, card_h), 1, border_radius=14)
                
                tex = self.hud_flag_textures.get(f.name)
                if tex:
                    card.blit(tex, (10, (card_h - tex.get_height()) // 2))
                    
                short_name = f.name[:7]
                name_surf = self.font_hud.render(short_name, True, (120, 120, 120))
                card.blit(name_surf, (58, 12))
                
                elim_surf = self.font_badge.render("ELIMINATED", True, (255, 60, 60))
                card.blit(elim_surf, (58, 42))
                
            surface.blit(card, (x, y))

    def _render_elimination_banner(self, sim: BattleSimulator, surface: pygame.Surface):
        """Shows banner for 1.8 seconds when a country is eliminated."""
        for f in sim.flags:
            if not f.is_alive and f.eliminated_at is not None:
                elapsed = sim.time - f.eliminated_at
                if 0 <= elapsed <= 1.8:
                    banner_w = 700
                    banner_h = 80
                    banner_y = int(sim.arena_cy - 40)
                    banner_x = (self.width - banner_w) // 2
                    
                    banner = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
                    alpha = int(240 * min(1.0, (1.8 - elapsed) / 0.3)) if elapsed > 1.5 else 240
                    pygame.draw.rect(banner, (200, 20, 40, alpha), (0, 0, banner_w, banner_h), border_radius=20)
                    pygame.draw.rect(banner, (255, 255, 255, alpha), (0, 0, banner_w, banner_h), 3, border_radius=20)
                    
                    text = f"{f.name.upper()} ELIMINATED!"
                    t_surf = self.font_elim.render(text, True, (255, 255, 255))
                    banner.blit(t_surf, ((banner_w - t_surf.get_width()) // 2, (banner_h - t_surf.get_height()) // 2))
                    
                    surface.blit(banner, (banner_x, banner_y))
                    break

    def _render_winner_celebration(self, sim: BattleSimulator, surface: pygame.Surface):
        """Draws grandiose winner banner, golden crown, and celebration aura."""
        winner = sim.winner
        pulse = (math.sin(sim.time * 6.0) + 1.0) * 0.5
        
        # Golden halo behind winner ball
        wx, wy = int(winner.x), int(winner.y)
        halo_r = int(winner.radius + 20 + pulse * 14)
        halo_surf = pygame.Surface((halo_r * 2, halo_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (255, 215, 0, 160), (halo_r, halo_r), halo_r)
        surface.blit(halo_surf, (wx - halo_r, wy - halo_r), special_flags=pygame.BLEND_ADD)
        
        # Re-blit flag texture on top of the halo so it remains crisp and vibrant
        tex = self.flag_textures.get(winner.name)
        if tex:
            surface.blit(tex, (wx - int(winner.radius), wy - int(winner.radius)))
        pygame.draw.circle(surface, (255, 255, 255), (wx, wy), int(winner.radius), 2)
        pygame.draw.circle(surface, (255, 215, 0), (wx, wy), int(winner.radius) + 2, 3)
        
        # Procedural Royal Gold Crown above winner ball
        crown_y = wy - int(winner.radius) - 36
        crown_pts = [
            (wx - 26, crown_y + 10),
            (wx - 30, crown_y - 14),
            (wx - 14, crown_y - 2),
            (wx, crown_y - 22),
            (wx + 14, crown_y - 2),
            (wx + 30, crown_y - 14),
            (wx + 26, crown_y + 10)
        ]
        pygame.draw.polygon(surface, (255, 215, 0), crown_pts)
        pygame.draw.polygon(surface, (255, 245, 180), crown_pts, 2)
        # Crown jewels
        pygame.draw.circle(surface, (255, 50, 50), (wx - 30, crown_y - 14), 4)
        pygame.draw.circle(surface, (0, 220, 255), (wx, crown_y - 22), 5)
        pygame.draw.circle(surface, (255, 50, 50), (wx + 30, crown_y - 14), 4)

        # Winner Announcement Card across lower area
        w_card_w = 840
        w_card_h = 160
        w_card_x = (self.width - w_card_w) // 2
        w_card_y = int(sim.arena_cy + sim.arena_r - 90)
        
        w_card = pygame.Surface((w_card_w, w_card_h), pygame.SRCALPHA)
        pygame.draw.rect(w_card, (15, 22, 36, 240), (0, 0, w_card_w, w_card_h), border_radius=28)
        pygame.draw.rect(w_card, (255, 215, 0, 255), (0, 0, w_card_w, w_card_h), 5, border_radius=28)
        
        # Inner glow
        pygame.draw.rect(w_card, (255, 230, 80, 80), (6, 6, w_card_w - 12, w_card_h - 12), 2, border_radius=24)
        
        # Winner text
        win_title = self.font_subtitle.render("WINNER", True, (255, 215, 0))
        w_card.blit(win_title, ((w_card_w - win_title.get_width()) // 2, 20))
        
        win_name = self.font_winner.render(f"{winner.name.upper()}", True, (255, 255, 255))
        w_card.blit(win_name, ((w_card_w - win_name.get_width()) // 2, 65))
        
        surface.blit(w_card, (w_card_x, w_card_y))

    def render_intro_frame(
        self,
        selected_countries: List[str],
        all_countries: List[str],
        intro_time: float,
        intro_duration: float,
        surface: pygame.Surface
    ):
        """Renders the high-suspense slot machine / roulette flag selection intro sequence."""
        # 1. Dark background with ambient radial glow
        surface.fill((8, 12, 20))
        
        # Center glow
        pygame.draw.circle(surface, (18, 28, 48), (self.width // 2, self.height // 2), 520)

        # 2. Header
        title_surf = self.font_title.render("FLAG BATTLE ROYALE", True, (255, 255, 255))
        title_shadow = self.font_title.render("FLAG BATTLE ROYALE", True, (0, 180, 255))
        surface.blit(title_shadow, (self.width // 2 - title_surf.get_width() // 2 + 2, 72))
        surface.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 70))

        sub_pulse = (math.sin(intro_time * 8.0) + 1.0) * 0.5
        sub_col = (int(0 + sub_pulse * 50), int(220 + sub_pulse * 35), 255)
        sub_text = "SELECTING RANDOM COUNTRIES..."
        sub_surf = self.font_subtitle.render(sub_text, True, sub_col)
        surface.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, 140))

        # 3. Calculate slot lock timings based on country count
        n = len(selected_countries)
        # Lock times staggered evenly across first 75% of intro duration
        lock_times = [0.9 + i * (intro_duration * 0.65 / max(1, n - 1)) for i in range(n)]

        # 4. Render Selection Cards
        card_w = 760
        card_h = min(150, int(820 / n))
        start_y = 220 + (820 - n * card_h - (n - 1) * 20) // 2
        
        for i, target_country in enumerate(selected_countries):
            y = start_y + i * (card_h + 20)
            x = (self.width - card_w) // 2
            
            is_locked = intro_time >= lock_times[i]
            
            if is_locked:
                displayed_country = target_country
                time_since_lock = intro_time - lock_times[i]
            else:
                # Roulette spinning rapidly
                cycle_idx = int((intro_time * 16.0 + i * 5) % len(all_countries))
                displayed_country = all_countries[cycle_idx]
                time_since_lock = -1.0

            info = COUNTRY_DATABASE.get(displayed_country, COUNTRY_DATABASE["Germany"])
            laser_col = info["laser_color"]

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            # Card background
            if is_locked:
                bg_col = (18, 26, 42, 240)
                border_col = laser_col
                border_width = 3
                # Flash on lock
                if 0 <= time_since_lock < 0.25:
                    border_col = (255, 255, 255)
                    border_width = 5
            else:
                bg_col = (14, 18, 28, 200)
                border_col = (60, 80, 110, 160)
                border_width = 2

            pygame.draw.rect(card_surf, bg_col, (0, 0, card_w, card_h), border_radius=20)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), border_width, border_radius=20)

            # Draw Flag Thumbnail
            flag_tex = self.flag_textures.get(displayed_country)
            flag_size = min(90, card_h - 24)
            if flag_tex:
                scaled_flag = pygame.transform.smoothscale(flag_tex, (flag_size, flag_size))
                card_surf.blit(scaled_flag, (24, (card_h - flag_size) // 2))
                pygame.draw.circle(card_surf, (255, 255, 255), (24 + flag_size // 2, card_h // 2), flag_size // 2, 2)

            # Slot Number & Country Name
            slot_label = f"SLOT {i + 1}"
            slot_surf = self.font_hud.render(slot_label, True, (120, 140, 170))
            card_surf.blit(slot_surf, (flag_size + 45, 24))

            name_col = (255, 255, 255) if is_locked else (180, 195, 215)
            name_surf = self.font_intro_name.render(displayed_country.upper(), True, name_col)
            card_surf.blit(name_surf, (flag_size + 45, 52))

            # Status Badge on right
            if is_locked:
                badge_text = "LOCKED IN"
                badge_bg = (20, 80, 40, 220)
                badge_col = (0, 255, 120)
            else:
                badge_text = "SPINNING..."
                badge_bg = (30, 45, 70, 200)
                badge_col = (0, 210, 255)

            badge_surf = self.font_badge.render(badge_text, True, badge_col)
            bw = badge_surf.get_width() + 24
            bh = 36
            bx = card_w - bw - 24
            by = (card_h - bh) // 2
            pygame.draw.rect(card_surf, badge_bg, (bx, by, bw, bh), border_radius=12)
            pygame.draw.rect(card_surf, badge_col, (bx, by, bw, bh), 2, border_radius=12)
            card_surf.blit(badge_surf, (bx + 12, by + 8))

            surface.blit(card_surf, (x, y))

        # 5. Battle Start / Fight Overlay in last 1.2s of Intro
        if intro_time >= intro_duration - 1.2:
            time_left = intro_duration - intro_time
            fight_scale = 1.0 + (1.2 - time_left) * 0.3
            
            fight_surf = self.font_fight.render("BATTLE START!", True, (255, 215, 0))
            fight_shadow = self.font_fight.render("BATTLE START!", True, (255, 50, 80))
            
            fx = self.width // 2 - fight_surf.get_width() // 2
            fy = int(start_y + n * (card_h + 20) + 40)
            
            surface.blit(fight_shadow, (fx + 3, fy + 3))
            surface.blit(fight_surf, (fx, fy))

        # 6. Bottom Call to Action
        cta_bg = pygame.Surface((self.width - 120, 64), pygame.SRCALPHA)
        pygame.draw.rect(cta_bg, (18, 25, 40, 200), (0, 0, self.width - 120, 64), border_radius=20)
        pygame.draw.rect(cta_bg, (60, 90, 140, 180), (0, 0, self.width - 120, 64), 2, border_radius=20)
        surface.blit(cta_bg, (60, 1780))
        
        cta_text = "Who will take the crown today? Drop your prediction below!"
        cta_surf = self.font_cta.render(cta_text, True, (230, 240, 255))
        surface.blit(cta_surf, (self.width // 2 - cta_surf.get_width() // 2, 1798))
