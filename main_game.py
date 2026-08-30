"""
main_game.py - Maveli AI (Pātāḷa Kāval) 60-Second Challenge
Real-Time Interactive AI-Driven Arcade Game with Cyber-Mythological Kerala Aesthetics

Features:
- Ultra-Premium Cyberpunk-Kerala Glassmorphic UI with Kasavu Gold & Obsidian Neon Theme
- Interactive Keyboard Input Visualizer (Keys: B, L, G, S with real-time active glow)
- Dynamic Theme Incident Stage (SPIRIT, FURNACE, SOLAR, GATE, CHANT) with procedural animations
- Real-Time Live Audio Waveform & Malayalam STT Visualizer
- Underworld Stability Health Bar with dynamic gradient pulse
- Continuous Input Identification & Adaptive Dynamic Difficulty Adjuster
- Multi-Channel Audio Engine & Edge-TTS Malayalam Voice
"""

import sys
import math
import time
import random
import asyncio
from typing import List, Tuple, Dict, Any, Optional

import pygame

# Local module imports
from ml_pipeline import ActionPredictor, ACTIONS
from hardware_bridge import HardwareBridge, TelemetrySnapshot
from maveli_brain import MaveliBrain, UnderworldIncident
from audio_engine import AudioEngine, MicListener

# Screen Configuration
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Palette: Cyber-Mythology Kerala / Kasavu Neon Dark Theme
COLOR_BG_DARK = (10, 11, 18)
COLOR_PANEL_BG = (18, 20, 30)
COLOR_PANEL_BORDER = (38, 42, 60)
COLOR_GOLD = (255, 215, 0)
COLOR_GOLD_DARK = (180, 140, 20)
COLOR_GOLD_NEON = (255, 235, 120)
COLOR_KASAVU = (245, 232, 195)
COLOR_MAROON = (180, 24, 45)
COLOR_EMERALD = (16, 185, 129)
COLOR_EMERALD_NEON = (52, 211, 153)
COLOR_CYAN = (6, 182, 212)
COLOR_CYAN_NEON = (103, 232, 249)
COLOR_AMBER = (245, 158, 11)
COLOR_AMBER_NEON = (251, 191, 36)
COLOR_CRIMSON = (239, 68, 68)
COLOR_WHITE = (248, 249, 250)
COLOR_GREY = (130, 135, 150)
COLOR_KEY_ACTIVE = (255, 215, 0)


class PetalParticle:
    """Floating flower petal for Kerala Onam Athappookkalam atmosphere."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(0.8, 2.0)
        self.angle = random.uniform(0, 360)
        self.v_angle = random.uniform(-2.5, 2.5)
        self.size = random.uniform(4, 8)
        self.color = random.choice([
            (255, 215, 0),   # Yellow marigold
            (245, 158, 11),  # Orange chethi
            (239, 68, 68),   # Red hibiscus
            (248, 250, 252), # White thumbapoo
            (236, 72, 153),  # Pink arali
        ])
        self.alpha = random.randint(120, 210)

    def update(self):
        self.x += self.vx + math.sin(self.y * 0.02) * 0.4
        self.y += self.vy
        self.angle += self.v_angle
        if self.y > SCREEN_HEIGHT + 20:
            self.y = -20
            self.x = random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface: pygame.Surface):
        petal_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        col = (*self.color, self.alpha)
        pygame.draw.ellipse(petal_surf, col, (0, int(self.size * 0.3), int(self.size * 2), int(self.size * 1.4)))
        rotated = pygame.transform.rotate(petal_surf, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)


class ConfettiParticle:
    """Explosive burst particles when a challenge is successfully completed."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 11)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2.5
        self.gravity = 0.24
        self.color = random.choice([COLOR_GOLD, COLOR_EMERALD, COLOR_CYAN, COLOR_MAROON, COLOR_AMBER, COLOR_WHITE])
        self.life = 1.0
        self.decay = random.uniform(0.018, 0.038)
        self.size = random.uniform(4, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay

    def draw(self, surface: pygame.Surface):
        if self.life > 0:
            alpha = int(255 * max(0.0, self.life))
            s = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surface.blit(s, (int(self.x), int(self.y)))


class MaveliArcadeGame:
    """Main Arcade Controller and 60 FPS Pygame Renderer."""
    
    STATE_TITLE = "TITLE"
    STATE_ROUND_START = "ROUND_START"
    STATE_CHALLENGE_ACTIVE = "CHALLENGE_ACTIVE"
    STATE_ACTION_SUCCESS = "ACTION_SUCCESS"
    STATE_GAME_OVER = "GAME_OVER"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maveli AI (Pātāḷa Kāval) - Cyber-Mythological Kerala Arcade")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Premium Typography
        self.font_huge = pygame.font.SysFont("Trebuchet MS,Arial,Helvetica", 54, bold=True)
        self.font_large = pygame.font.SysFont("Trebuchet MS,Arial,Helvetica", 30, bold=True)
        self.font_medium = pygame.font.SysFont("Trebuchet MS,Arial,Helvetica", 20, bold=True)
        self.font_small = pygame.font.SysFont("Trebuchet MS,Arial,Helvetica", 15, bold=False)
        self.font_mono = pygame.font.SysFont("Consolas,Courier New,monospace", 13, bold=True)
        self.font_mono_large = pygame.font.SysFont("Consolas,Courier New,monospace", 18, bold=True)

        # Core Subsystems
        self.hardware = HardwareBridge()
        self.predictor = ActionPredictor()
        self.brain = MaveliBrain()
        self.audio = AudioEngine()
        self.mic = MicListener(callback=self._on_mic_shout)

        # Game State
        self.state = self.STATE_TITLE
        self.total_time_left = 60.0
        self.stability_hp = 100.0
        self.challenge_start_time = 0.0
        self.current_round = 0
        self.score = 0
        self.combo = 0
        self.high_score = 0
        self.current_target_action = "BLOWING"
        self.current_incident: Optional[UnderworldIncident] = None
        self.current_story_prompt = "Press SPACEBAR to start Mahabali's 60-Second Underworld Challenge!"
        self.prompt_display_text = ""
        self.prompt_char_index = 0
        self.prompt_timer = 0.0
        self.feedback_text = ""

        # Keyboard Live Input Tracking
        self.active_keys = {"B": False, "L": False, "G": False, "S": False}
        self.key_glow_timers = {"B": 0.0, "L": 0.0, "G": 0.0, "S": 0.0}

        # Visual Effects
        self.petals: List[PetalParticle] = [
            PetalParticle(random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT))
            for _ in range(45)
        ]
        self.confetti: List[ConfettiParticle] = []
        self.pulse_time = 0.0
        self.success_timer = 0.0
        self.ai_task: Optional[asyncio.Task] = None
        self._milestones_triggered = set()
        self.shift_overview_text = ""

    def _on_mic_shout(self, phrase: str):
        print(f"[MaveliArcade] Malayalam / Mic shout triggered via: {phrase}")
        self.hardware.set_laptop_mic_trigger(True, 1.6)
        self.key_glow_timers["S"] = 1.6

    def start_subsystems(self):
        self.hardware.start()
        self.audio.start_bgm(0.40)
        self.mic.start_listening()
        print("[MaveliArcade] Subsystems started successfully (Malayalam STT & Interactive Keyboard Active).")

    def shutdown_subsystems(self):
        self.hardware.stop()
        self.audio.stop_bgm()
        self.mic.stop_listening()
        pygame.quit()

    def reset_game(self):
        self.total_time_left = 60.0
        self.stability_hp = 100.0
        self.score = 0
        self.combo = 0
        self.current_round = 0
        self.confetti.clear()
        self._milestones_triggered.clear()
        self.shift_overview_text = ""
        self.current_incident = None
        self.state = self.STATE_ROUND_START

    def _trigger_new_challenge(self):
        self.current_round += 1
        self.challenge_start_time = time.time()
        self.prompt_char_index = 0
        self.prompt_display_text = ""
        self.prompt_timer = 0.0

        async def fetch_incident_story():
            hp_val = int(max(10.0, self.stability_hp))
            incident = await self.brain.generate_incident(self.total_time_left, hp_val)
            self.current_incident = incident
            self.current_target_action = incident.action_name
            self.current_story_prompt = f"{incident.incident_title}: {incident.malayalam_alert}"
            self.audio.speak(incident.malayalam_alert)

        self.ai_task = asyncio.create_task(fetch_incident_story())
        self.state = self.STATE_CHALLENGE_ACTIVE

    def handle_keyboard_simulation(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_SPACE:
                if self.state in [self.STATE_TITLE, self.STATE_GAME_OVER]:
                    self.reset_game()
            elif event.key == pygame.K_r:
                self.reset_game()
            elif event.key == pygame.K_b:
                self.active_keys["B"] = True
                self.key_glow_timers["B"] = 0.6
                self.hardware.trigger_simulated_action("BLOWING", 2.2)
            elif event.key == pygame.K_l:
                self.active_keys["L"] = True
                self.key_glow_timers["L"] = 0.6
                self.hardware.trigger_simulated_action("LIGHT_COVERED", 2.2)
            elif event.key == pygame.K_g:
                self.active_keys["G"] = True
                self.key_glow_timers["G"] = 0.6
                self.hardware.trigger_simulated_action("GATE_LOCKED", 2.2)
            elif event.key == pygame.K_s:
                self.active_keys["S"] = True
                self.key_glow_timers["S"] = 0.6
                self.hardware.trigger_simulated_action("SHOUT_MIC", 2.2)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_b:
                self.active_keys["B"] = False
            elif event.key == pygame.K_l:
                self.active_keys["L"] = False
            elif event.key == pygame.K_g:
                self.active_keys["G"] = False
            elif event.key == pygame.K_s:
                self.active_keys["S"] = False

        return True

    def update(self, dt: float):
        self.pulse_time += dt

        for k in self.key_glow_timers:
            self.key_glow_timers[k] = max(0.0, self.key_glow_timers[k] - dt)

        # Hardware START Button Edge Event (GPIO 25)
        telem = self.hardware.get_telemetry()
        if telem.start_event:
            if self.state in [self.STATE_TITLE, self.STATE_GAME_OVER]:
                self.reset_game()
            elif self.state == self.STATE_CHALLENGE_ACTIVE:
                self.reset_game()

        # Sync live laptop microphone shout activity
        if self.mic.is_shout_active():
            self.hardware.set_laptop_mic_trigger(True, 0.5)
            self.key_glow_timers["S"] = 0.5

        for p in self.petals:
            p.update()

        for c in self.confetti[:]:
            c.update()
            if c.life <= 0:
                self.confetti.remove(c)

        if len(self.prompt_display_text) < len(self.current_story_prompt):
            self.prompt_timer += dt
            if self.prompt_timer >= 0.02:
                self.prompt_timer = 0.0
                self.prompt_char_index = min(len(self.current_story_prompt), self.prompt_char_index + 2)
                self.prompt_display_text = self.current_story_prompt[:self.prompt_char_index]
        else:
            self.prompt_display_text = self.current_story_prompt

        if self.state == self.STATE_ROUND_START:
            self._trigger_new_challenge()

        elif self.state == self.STATE_CHALLENGE_ACTIVE:
            self.total_time_left = max(0.0, self.total_time_left - dt)
            self.stability_hp = (self.total_time_left / 60.0) * 100.0

            # Mid-Game Live Dynamic Gemini Commentary Milestones (45s, 30s, 15s)
            for m in [45, 30, 15]:
                if self.total_time_left <= m and m not in self._milestones_triggered:
                    self._milestones_triggered.add(m)
                    async def fetch_commentary(t_left=m):
                        comm = await self.brain.generate_live_commentary(float(t_left), self.score, self.combo)
                        self.current_story_prompt = comm
                        self.audio.speak(comm)
                    asyncio.create_task(fetch_commentary())
                    break

            if self.total_time_left <= 10.0 and int(self.total_time_left * 2) % 2 == 0 and int((self.total_time_left - dt) * 2) % 2 != 0:
                self.audio.play_sfx("warning")

            if self.total_time_left <= 0.0:
                self.state = self.STATE_GAME_OVER
                self.audio.play_sfx("buzzer")
                if self.score > self.high_score:
                    self.high_score = self.score
                
                async def fetch_review():
                    rev = await self.brain.generate_shift_overview(self.score, self.current_round - 1, self.combo, self.score >= 600)
                    self.shift_overview_text = rev
                    self.audio.speak(rev)
                asyncio.create_task(fetch_review())
                return

            pred_action, confidence, probs = self.predictor.predict(
                telem.thermistor, telem.ldr, telem.mic, telem.gate_angle
            )

            # Continuous Dynamic Input Matcher
            if pred_action == self.current_target_action and confidence >= 0.70:
                self._handle_action_success()

        elif self.state == self.STATE_ACTION_SUCCESS:
            self.success_timer -= dt
            if self.success_timer <= 0.0:
                self.state = self.STATE_ROUND_START

    def _handle_action_success(self):
        self.state = self.STATE_ACTION_SUCCESS
        self.success_timer = 1.5
        self.combo += 1
        points_earned = 100 + (self.combo * 30)
        self.score += points_earned

        self.audio.play_sfx("fanfare")
        
        for _ in range(60):
            self.confetti.append(ConfettiParticle(SCREEN_WIDTH // 2, 280))

        time_taken = time.time() - self.challenge_start_time
        async def fetch_praise():
            praise = await self.brain.generate_feedback(True, self.current_target_action, time_taken)
            self.feedback_text = praise
            self.audio.speak(praise)

        asyncio.create_task(fetch_praise())

    def render(self):
        self.screen.fill(COLOR_BG_DARK)
        self._render_ambient_glow()
        for p in self.petals:
            p.draw(self.screen)

        self._render_header()

        if self.state == self.STATE_TITLE:
            self._render_title_screen()
        elif self.state == self.STATE_GAME_OVER:
            self._render_game_over_screen()
        else:
            self._render_gameplay_hud()

        for c in self.confetti:
            c.draw(self.screen)

        self._render_telemetry_and_keyboard_dock()
        pygame.display.flip()

    def _render_ambient_glow(self):
        """Renders subtle cyberpunk neon ambient grid & glow."""
        grid_col = (20, 22, 34)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, grid_col, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, grid_col, (0, y), (SCREEN_WIDTH, y), 1)

    def _render_header(self):
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 75)
        pygame.draw.rect(self.screen, (16, 18, 28), header_rect)
        pygame.draw.line(self.screen, COLOR_GOLD, (0, 72), (SCREEN_WIDTH, 72), 3)
        pygame.draw.line(self.screen, COLOR_MAROON, (0, 75), (SCREEN_WIDTH, 75), 2)

        # Title with glowing gold crown icon
        title_surf = self.font_large.render("👑 MAVELI AI  |  PĀTĀḶA KĀVAL ARCADE", True, COLOR_GOLD)
        self.screen.blit(title_surf, (20, 18))

        # Dynamic Stability HP Bar in Header
        hp_w = 170
        pygame.draw.rect(self.screen, (28, 30, 44), (430, 22, hp_w, 28), border_radius=6)
        fill_hp = int(hp_w * max(0.0, min(1.0, self.stability_hp / 100.0)))
        hp_col = COLOR_EMERALD if self.stability_hp > 50 else (COLOR_AMBER if self.stability_hp > 25 else COLOR_CRIMSON)
        if fill_hp > 0:
            pygame.draw.rect(self.screen, hp_col, (430, 22, fill_hp, 28), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_GOLD_DARK, (430, 22, hp_w, 28), width=1, border_radius=6)
        
        hp_lbl = self.font_mono.render(f"STABILITY: {self.stability_hp:3.0f}%", True, COLOR_WHITE)
        self.screen.blit(hp_lbl, (455, 28))

        telem = self.hardware.get_telemetry()
        # ESP32 Port & Wi-Fi Badge
        if telem.is_connected:
            hw_str = f"ESP32: {telem.port_name}"
            hw_col = COLOR_EMERALD_NEON
        else:
            hw_str = "ESP32: SIMULATED"
            hw_col = COLOR_AMBER

        hw_surf = self.font_mono.render(hw_str, True, hw_col)
        pygame.draw.rect(self.screen, (28, 32, 48), (615, 20, 130, 32), border_radius=6)
        pygame.draw.rect(self.screen, hw_col, (615, 20, 130, 32), width=1, border_radius=6)
        self.screen.blit(hw_surf, (623, 28))

        # AI Backend Badge
        ai_status = f"AI: {self.brain.active_backend}"
        ai_surf = self.font_mono.render(ai_status, True, COLOR_CYAN_NEON)
        pygame.draw.rect(self.screen, (28, 32, 48), (755, 20, 110, 32), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_CYAN, (755, 20, 110, 32), width=1, border_radius=6)
        self.screen.blit(ai_surf, (765, 28))

        # Input & Wi-Fi Badge
        wifi_str = f"WIFI: {telem.wifi_ip}" if (telem.wifi_connected and telem.wifi_ip) else "INPUT: KEY/MIC"
        inp_surf = self.font_mono.render(wifi_str, True, COLOR_EMERALD_NEON)
        pygame.draw.rect(self.screen, (28, 32, 48), (875, 20, 135, 32), border_radius=6)
        pygame.draw.rect(self.screen, COLOR_EMERALD, (875, 20, 135, 32), width=1, border_radius=6)
        self.screen.blit(inp_surf, (883, 28))

    def _render_title_screen(self):
        center_x = SCREEN_WIDTH // 2
        glow_val = int(220 + 35 * math.sin(self.pulse_time * 3))
        gold_glow = (glow_val, int(glow_val * 0.85), 0)
        
        t1 = self.font_huge.render("PĀTĀḶA KĀVAL ARCADE", True, gold_glow)
        self.screen.blit(t1, t1.get_rect(center=(center_x, 165)))

        sub = self.font_medium.render("Underworld Guard: Real-Time Cyber-Mythological AI Challenge (Google Hackathon)", True, COLOR_KASAVU)
        self.screen.blit(sub, sub.get_rect(center=(center_x, 215)))

        box_rect = pygame.Rect(140, 255, 744, 265)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, box_rect, border_radius=14)
        pygame.draw.rect(self.screen, COLOR_GOLD, box_rect, width=2, border_radius=14)

        lines = [
            "⚡ DYNAMIC CONTROLS & HOW TO PLAY:",
            "• King Mahabali & Kāvalan issue real-time AI emergencies from the Underworld!",
            "• Perform the matching action on your Keyboard & Laptop Mic before time expires:",
            "   [KEY: B] -> Furnace Breath / Blow Flame (TOOL_BLOW)",
            "   [KEY: L] -> Shade Pookkalam / Cover Light (TOOL_LIGHT)",
            "   [KEY: G] -> Lock Fortress Gate >120° (TOOL_GATE)",
            "   [KEY: S / MIC] -> Shout 'ARPO IRRO!' in Malayalam into Laptop Mic (TOOL_VOICE)",
            "• Keep Underworld Stability at 100% and chain Combos for Royal Senapathi Rank!"
        ]
        y_off = 270
        for i, l in enumerate(lines):
            col = COLOR_GOLD if i == 0 else (COLOR_EMERALD_NEON if "->" in l else COLOR_WHITE)
            f_surf = self.font_small.render(l, True, col)
            self.screen.blit(f_surf, (165, y_off))
            y_off += 27

        blink = (int(self.pulse_time * 4) % 2) == 0
        if blink:
            start_surf = self.font_large.render(">>> PRESS [SPACE] TO START THE 60s CHALLENGE <<<", True, COLOR_GOLD)
            self.screen.blit(start_surf, start_surf.get_rect(center=(center_x, 560)))

    def _render_gameplay_hud(self):
        self._render_countdown_timer(140, 205, 80)
        self._render_score_panel(760, 95, 235, 220)
        self._render_event_canvas(270, 95, 470, 220)
        self._render_story_panel(25, 330, 974, 195)

    def _render_countdown_timer(self, cx: int, cy: int, radius: int):
        time_ratio = max(0.0, min(1.0, self.total_time_left / 60.0))
        is_urgent = self.total_time_left <= 10.0

        pygame.draw.circle(self.screen, (24, 26, 38), (cx, cy), radius, width=12)
        timer_col = COLOR_CRIMSON if is_urgent else (COLOR_AMBER if self.total_time_left < 25 else COLOR_EMERALD)
        
        n_segments = int(time_ratio * 60)
        for i in range(n_segments):
            ang = -math.pi / 2 + (i / 60.0) * (2 * math.pi)
            px = cx + int((radius - 6) * math.cos(ang))
            py = cy + int((radius - 6) * math.sin(ang))
            pygame.draw.circle(self.screen, timer_col, (px, py), 5)

        time_str = f"{self.total_time_left:04.1f}s"
        t_surf = self.font_large.render(time_str, True, COLOR_WHITE if not is_urgent else COLOR_CRIMSON)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, cy - 8)))

        lbl_surf = self.font_mono.render("SHIFT TIMER", True, COLOR_GREY)
        self.screen.blit(lbl_surf, lbl_surf.get_rect(center=(cx, cy + 26)))

    def _render_score_panel(self, x: int, y: int, w: int, h: int):
        panel_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=1, border_radius=12)

        s_lbl = self.font_mono.render("TOTAL SCORE", True, COLOR_GREY)
        self.screen.blit(s_lbl, (x + 20, y + 16))
        s_val = self.font_large.render(f"{self.score:05d}", True, COLOR_GOLD)
        self.screen.blit(s_val, (x + 20, y + 36))

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (x + 15, y + 78), (x + w - 15, y + 78), 1)

        c_lbl = self.font_mono.render("COMBO MULTIPLIER", True, COLOR_GREY)
        self.screen.blit(c_lbl, (x + 20, y + 90))
        c_val = self.font_large.render(f"🔥 {self.combo}x", True, COLOR_AMBER_NEON if self.combo > 1 else COLOR_WHITE)
        self.screen.blit(c_val, (x + 20, y + 110))

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (x + 15, y + 150), (x + w - 15, y + 150), 1)

        r_lbl = self.font_mono.render("ROUND CLEARED", True, COLOR_GREY)
        self.screen.blit(r_lbl, (x + 20, y + 160))
        r_val = self.font_medium.render(f"Round {self.current_round}", True, COLOR_CYAN_NEON)
        self.screen.blit(r_val, (x + 20, y + 182))

    def _render_event_canvas(self, x: int, y: int, w: int, h: int):
        """Dynamic Incident Stage with real-time procedural animations."""
        canvas_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (14, 16, 24), canvas_rect, border_radius=12)
        
        border_glow = COLOR_GOLD if self.state == self.STATE_ACTION_SUCCESS else COLOR_CYAN
        pygame.draw.rect(self.screen, border_glow, canvas_rect, width=2, border_radius=12)

        action_name = self.current_target_action
        act_title = action_name.replace("_", " ")
        act_surf = self.font_large.render(f"REQUIRED: {act_title}", True, COLOR_GOLD_NEON)
        self.screen.blit(act_surf, act_surf.get_rect(center=(x + w // 2, y + 32)))

        cx, cy = x + w // 2, y + 115

        if action_name == "BLOWING":
            flame_h = 42 + 14 * math.sin(self.pulse_time * 9)
            pygame.draw.polygon(self.screen, (245, 158, 11), [(cx - 36, cy + 30), (cx, cy - flame_h), (cx + 36, cy + 30)])
            pygame.draw.polygon(self.screen, (255, 215, 0), [(cx - 20, cy + 30), (cx, cy - flame_h + 14), (cx + 20, cy + 30)])
            pygame.draw.polygon(self.screen, (255, 255, 255), [(cx - 8, cy + 30), (cx, cy - flame_h + 24), (cx + 8, cy + 30)])
            sub_txt = self.font_mono_large.render("PRESS [B] TO BLOW FLAME", True, COLOR_AMBER_NEON)

        elif action_name == "LIGHT_COVERED":
            for r in range(40, 10, -10):
                pygame.draw.circle(self.screen, (255, 200, 50, 40), (cx, cy), r + int(4 * math.sin(self.pulse_time * 4)), 2)
            pygame.draw.circle(self.screen, (255, 215, 0), (cx, cy), 28)
            # Hand shade shield
            pygame.draw.circle(self.screen, (20, 22, 35), (cx + int(14 * math.sin(self.pulse_time * 3)), cy), 26)
            sub_txt = self.font_mono_large.render("PRESS [L] TO SHADE POOKKALAM", True, COLOR_CYAN_NEON)

        elif action_name == "GATE_LOCKED":
            pygame.draw.rect(self.screen, (60, 65, 85), (cx - 40, cy - 30, 80, 60), border_radius=8)
            rot_angle = math.sin(self.pulse_time * 4.5) * 0.7
            pygame.draw.line(self.screen, COLOR_GOLD, (cx, cy), (cx + int(32 * math.cos(rot_angle)), cy + int(32 * math.sin(rot_angle))), 6)
            pygame.draw.circle(self.screen, COLOR_GOLD, (cx, cy), 8)
            sub_txt = self.font_mono_large.render("PRESS [G] TO LOCK GATE", True, COLOR_KASAVU)

        else:  # SHOUT_MIC
            for r in range(1, 5):
                rad = int((self.pulse_time * 45 + r * 15) % 45)
                alpha = max(0, 255 - rad * 5)
                s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*COLOR_EMERALD_NEON, alpha), (rad, rad), rad, 2)
                self.screen.blit(s, (cx - rad, cy - rad))
            pygame.draw.circle(self.screen, COLOR_EMERALD, (cx, cy), 16)
            sub_txt = self.font_mono_large.render("SHOUT 'ARPO IRRO!' / PRESS [S]", True, COLOR_EMERALD_NEON)

        self.screen.blit(sub_txt, sub_txt.get_rect(center=(cx, y + 190)))

    def _render_story_panel(self, x: int, y: int, w: int, h: int):
        panel_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (18, 20, 30), panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_GOLD_DARK, panel_rect, width=2, border_radius=12)

        # Avatar
        avatar_rect = pygame.Rect(x + 18, y + 20, 95, 95)
        pygame.draw.rect(self.screen, (32, 24, 42), avatar_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOLD, avatar_rect, width=2, border_radius=10)
        
        pygame.draw.polygon(self.screen, COLOR_GOLD, [
            (x + 28, y + 85), (x + 103, y + 85),
            (x + 103, y + 45), (x + 88, y + 60),
            (x + 65, y + 35), (x + 43, y + 60),
            (x + 28, y + 45)
        ])
        pygame.draw.circle(self.screen, COLOR_CRIMSON, (x + 65, y + 35), 5)

        tag_surf = self.font_mono.render("MAVELI AI", True, COLOR_GOLD)
        self.screen.blit(tag_surf, (x + 26, y + 124))

        inc_title = self.current_incident.incident_title.upper() if self.current_incident else "PĀTĀḶA INCIDENT"
        d_hdr = self.font_small.render(f"👑 KING MAHABALI & KĀVALAN  |  {inc_title}", True, COLOR_GOLD)
        self.screen.blit(d_hdr, (x + 130, y + 16))

        if self.current_incident and self.current_incident.visual_description:
            desc_str = f"[{self.current_incident.visual_theme}] {self.current_incident.visual_description}"
            desc_surf = self.font_small.render(desc_str[:90], True, COLOR_CYAN_NEON)
            self.screen.blit(desc_surf, (x + 130, y + 38))

        self._render_wrapped_text(
            self.prompt_display_text,
            x + 130, y + 62, w - 150, self.font_medium, COLOR_WHITE
        )

        if self.state == self.STATE_ACTION_SUCCESS and self.feedback_text:
            fb_surf = self.font_small.render(f"✨ PRAISE: {self.feedback_text}", True, COLOR_EMERALD_NEON)
            self.screen.blit(fb_surf, (x + 130, y + 155))

    def _render_wrapped_text(self, text: str, x: int, y: int, max_width: int, font: pygame.font.Font, color: tuple):
        words = text.split(" ")
        lines = []
        cur_line = ""

        for word in words:
            test_line = f"{cur_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                cur_line = test_line
            else:
                lines.append(cur_line)
                cur_line = word
        if cur_line:
            lines.append(cur_line)

        for i, line in enumerate(lines[:3]):
            surf = font.render(line, True, color)
            self.screen.blit(surf, (x, y + i * 28))

    def _render_telemetry_and_keyboard_dock(self):
        dock_rect = pygame.Rect(0, 540, SCREEN_WIDTH, 228)
        pygame.draw.rect(self.screen, (14, 15, 22), dock_rect)
        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (0, 540), (SCREEN_WIDTH, 540), 2)

        telem = self.hardware.get_telemetry()
        pred_action, confidence, probs = self.predictor.predict(
            telem.thermistor, telem.ldr, telem.mic, telem.gate_angle
        )

        # 1. Hardware / Telemetry Gauges (Left Half)
        g_title = self.font_mono.render("ESP32 HARDWARE SENSOR ARRAY (COM3):", True, COLOR_GOLD)
        self.screen.blit(g_title, (30, 552))

        # Calibrated for user's MQ-3 (baseline ~500, blown 1000-3000), LDR (100-3500), Gate (0-90 deg)
        self._render_sensor_bar("MQ-3 BREATH (B)", telem.mq3_raw, 450, 2600, 30, 576, 180, COLOR_AMBER)
        self._render_sensor_bar("LDR LIGHT (L)", telem.ldr_raw, 100, 3500, 240, 576, 180, COLOR_CYAN)
        self._render_sensor_bar("GATE ANGLE (G)", telem.gate_angle, 0, 90, 30, 630, 180, COLOR_KASAVU)
        
        # Audio / Mic Level
        mic_lvl = self.mic.mic_level if self.mic.is_listening else (1.0 if telem.mic else 0.0)
        self._render_sensor_bar("MIC AUDIO (S)", mic_lvl * 100, 0, 100, 240, 630, 180, COLOR_EMERALD)

        # 2. Interactive Keyboard & Sensor Trigger Deck (Right Half)
        k_title = self.font_mono.render("LIVE INPUT & HARDWARE DETECTION DECK:", True, COLOR_GOLD)
        self.screen.blit(k_title, (460, 552))

        # Detect physical blowing (MQ-3 delta > 120 or raw > 850 or rate > 300)
        is_blowing_active = (telem.mq3_raw > 850) or (telem.mq3_delta > 120) or self.active_keys["B"] or (self.key_glow_timers["B"] > 0)
        is_light_covered = (telem.ldr_raw < 450) or self.active_keys["L"] or (self.key_glow_timers["L"] > 0)
        is_gate_locked = (telem.gate_angle > 65) or self.active_keys["G"] or (self.key_glow_timers["G"] > 0)
        is_shout_active = self.active_keys["S"] or (self.key_glow_timers["S"] > 0) or self.mic.is_shout_active()

        key_data = [
            ("B", "BLOW", is_blowing_active, COLOR_AMBER),
            ("L", "LIGHT", is_light_covered, COLOR_CYAN),
            ("G", "GATE", is_gate_locked, COLOR_KASAVU),
            ("S", "SHOUT", is_shout_active, COLOR_EMERALD)
        ]

        for idx, (k_char, k_name, is_act, k_color) in enumerate(key_data):
            kx = 460 + (idx * 128)
            ky = 576
            self._render_key_cap(k_char, k_name, kx, ky, is_act, k_color)

        # Prediction & Confidence Match Bar
        conf_lbl = self.font_mono.render(f"INPUT MATCH CONFIDENCE: {confidence * 100:.1f}%", True, COLOR_WHITE)
        self.screen.blit(conf_lbl, (460, 672))
        pygame.draw.rect(self.screen, (28, 30, 44), (680, 670, 290, 18), border_radius=4)
        fill_w = int(290 * confidence)
        pygame.draw.rect(self.screen, COLOR_EMERALD if confidence >= 0.70 else COLOR_AMBER, (680, 670, fill_w, 18), border_radius=4)

        help_str = "CONTROLS: [B] Blow | [L] Cover Light | [G] Gate Lock | [S] Laptop Mic Shout | [R] Restart | [ESC] Quit"
        help_surf = self.font_mono.render(help_str, True, (110, 115, 130))
        self.screen.blit(help_surf, (30, 715))

    def _render_key_cap(self, char: str, label: str, x: int, y: int, is_active: bool, color: tuple):
        """Renders an interactive glowing keycap for player inputs."""
        w, h = 115, 68
        bg_col = (50, 45, 25) if is_active else (24, 26, 38)
        border_col = color if is_active else (50, 54, 75)
        
        pygame.draw.rect(self.screen, bg_col, (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), width=2 if not is_active else 3, border_radius=8)

        # Key letter
        k_surf = self.font_large.render(char, True, color if is_active else COLOR_WHITE)
        self.screen.blit(k_surf, (x + 12, y + 10))

        # Action tag
        sub_col = color if is_active else COLOR_GREY
        lbl_surf = self.font_mono.render(label, True, sub_col)
        self.screen.blit(lbl_surf, (x + 12, y + 44))

    def _render_sensor_bar(self, name: str, value: float, v_min: float, v_max: float, x: int, y: int, w: int, color: tuple):
        ratio = max(0.0, min(1.0, (value - v_min) / (v_max - v_min)))
        
        lbl = self.font_mono.render(f"{name}: {value:4.0f}", True, COLOR_WHITE)
        self.screen.blit(lbl, (x, y))

        pygame.draw.rect(self.screen, (28, 30, 44), (x, y + 18, w, 12), border_radius=3)
        fill_w = int(w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (x, y + 18, fill_w, 12), border_radius=3)

    def _render_game_over_screen(self):
        center_x = SCREEN_WIDTH // 2
        t1 = self.font_huge.render("GAME OVER", True, COLOR_CRIMSON)
        self.screen.blit(t1, t1.get_rect(center=(center_x, 145)))

        sub = self.font_medium.render("60-Second Underworld Guard Shift Complete!", True, COLOR_WHITE)
        self.screen.blit(sub, sub.get_rect(center=(center_x, 190)))

        card_rect = pygame.Rect(170, 220, 684, 260)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, card_rect, border_radius=14)
        pygame.draw.rect(self.screen, COLOR_GOLD, card_rect, width=2, border_radius=14)

        if self.score >= 1200:
            rank = "ROYAL UNDERWORLD CHIEF (HERO)"
        elif self.score >= 600:
            rank = "PĀTĀḶA SENAPATHI (COMMANDER)"
        else:
            rank = "JUNIOR ASURA GUARD"

        r_surf = self.font_large.render(f"FINAL SCORE: {self.score}", True, COLOR_GOLD)
        self.screen.blit(r_surf, (200, 240))

        c_surf = self.font_small.render(f"Challenges Cleared: {self.current_round - 1}", True, COLOR_WHITE)
        self.screen.blit(c_surf, (200, 280))

        rk_surf = self.font_small.render(f"RANK: {rank}", True, COLOR_EMERALD_NEON)
        self.screen.blit(rk_surf, (450, 280))

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (190, 315), (834, 315), 1)
        ov_title = self.font_mono.render("KING MAHABALI'S 60-SECOND SHIFT REVIEW (GEMINI AI):", True, COLOR_GOLD)
        self.screen.blit(ov_title, (200, 330))

        review_display = self.shift_overview_text or "Calculating royal shift review with Gemini..."
        self._render_wrapped_text(review_display, 200, 355, 620, self.font_small, COLOR_KASAVU)

        rst_surf = self.font_large.render(">>> PRESS [R] OR [SPACE] TO PLAY AGAIN <<<", True, COLOR_GOLD)
        self.screen.blit(rst_surf, rst_surf.get_rect(center=(center_x, 515)))

    async def run(self):
        self.start_subsystems()
        running = True

        print("[MaveliArcade] Entering 60 FPS Async Main Loop...")
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if not self.handle_keyboard_simulation(event):
                        running = False

            self.update(dt)
            self.render()
            await asyncio.sleep(0.001)

        self.shutdown_subsystems()
        print("[MaveliArcade] Game loop exited gracefully.")


if __name__ == "__main__":
    async def main():
        game = MaveliArcadeGame()
        await game.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[MaveliArcade] Terminated by user.")
        sys.exit(0)
