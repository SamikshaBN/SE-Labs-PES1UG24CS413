import pygame
import math
from .marble import Marble
from .wall import Wall
from array import array

BOUNCE_COOLDOWN_MS = 120   # minimum gap between bounce sounds
BOUNCE_MIN_SPEED = 1.5     # impact speed below this is "rubbing", so stay silent
# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)
# One place to tune every difficulty. Medium matches the original values.
DIFFICULTIES = {
    "Easy":   {"tilt_strength": 0.9,  "friction": 0.05,  "time_limit_ms": 70000},
    "Medium": {"tilt_strength": 0.6,  "friction": 0.02,  "time_limit_ms": 45000},
    "Hard":   {"tilt_strength": 0.35, "friction": 0.008, "time_limit_ms": 30000},
}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.max_speed = 9

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = width - 60, height - 60, 22

        self.font = pygame.font.SysFont("Arial", 26)
        self.big_font = pygame.font.SysFont("Arial", 64, bold=True)  # Game Over / menu title

        self._init_sounds()  # NEW
        self._start_round("Medium")

    def _build_maze(self):
        walls = []
        t = 16  # wall thickness

        # outer boundary
        walls.append(Wall(0, 0, self.width, t))
        walls.append(Wall(0, self.height - t, self.width, t))
        walls.append(Wall(0, 0, t, self.height))
        walls.append(Wall(self.width - t, 0, t, self.height))

        # a few internal walls forming a simple winding path
        walls.append(Wall(0, 140, self.width - 140, t))
        walls.append(Wall(140, 260, self.width - 140, t))
        walls.append(Wall(0, 380, self.width - 140, t))

        return walls
    
    def _start_round(self, difficulty):
        """Apply a difficulty and reset everything that belongs to a single round."""
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.tilt_strength = settings["tilt_strength"]
        self.friction = settings["friction"]
        self.time_limit_ms = settings["time_limit_ms"]

        self.marble = Marble(50, 50)  # resets position and velocity
        self.start_ticks = pygame.time.get_ticks()

        self.game_over = False
        self.result = None  # "solved" or "timeout"
        self.finish_time_ms = None
        self.in_menu = False
    
    def _menu_buttons(self):
        """Return [(action, label, rect), ...]. action is a difficulty name, or None for Exit."""
        labels = [(name, f"{i + 1} - {name}") for i, name in enumerate(DIFFICULTIES)]
        labels.append((None, "Esc - Exit"))

        btn_w, btn_h, gap = 260, 48, 16
        total_h = len(labels) * btn_h + (len(labels) - 1) * gap
        top = self.height // 2 - total_h // 2 + 30

        buttons = []
        for i, (action, label) in enumerate(labels):
            rect = pygame.Rect(0, 0, btn_w, btn_h)
            rect.centerx = self.width // 2
            rect.y = top + i * (btn_h + gap)
            buttons.append((action, label, rect))
        return buttons

    def _tone_samples(self, rate, f0, f1, ms, volume):
        """Mono 16-bit samples for a sine sweep from f0 to f1 Hz, with a short fade in/out."""
        n = int(rate * ms / 1000)
        attack = max(1, int(rate * 0.005))
        samples = []
        phase = 0.0
        for i in range(n):
            t = i / n
            phase += 2 * math.pi * (f0 + (f1 - f0) * t) / rate
            env = min(1.0, i / attack) * (1 - t)
            samples.append(int(32767 * volume * env * math.sin(phase)))
        return samples
    
    def _make_sound(self, samples, channels):
        data = array("h")
        for s in samples:
            for _ in range(channels):
                data.append(s)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _init_sounds(self):
        """Build all sounds in code. If audio is unavailable, self.sounds stays empty."""
        self.sounds = {}
        self.last_bounce_ms = -BOUNCE_COOLDOWN_MS
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            rate, fmt, channels = pygame.mixer.get_init()
            if fmt != -16:
                raise RuntimeError("unsupported audio format")

            tone = lambda f0, f1, ms, vol: self._tone_samples(rate, f0, f1, ms, vol)

            bounce = tone(220, 150, 70, 0.5)
            win = []
            for freq in (523, 659, 784, 1047):          # C5 E5 G5 C6 arpeggio
                win += tone(freq, freq, 110, 0.5)
            timeout = tone(440, 110, 600, 0.5)          # falling sweep

            self.sounds = {
                "bounce": self._make_sound(bounce, channels),
                "win": self._make_sound(win, channels),
                "timeout": self._make_sound(timeout, channels),
            }
        except Exception:
            self.sounds = {}  # no audio device: play silently
    
    def _play(self, name, volume=1.0):
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(volume)
            sound.play()

    def _play_bounce(self, impact_speed):
        """Throttled, volume scales with impact speed. Resting/rubbing contact is silent."""
        if impact_speed < BOUNCE_MIN_SPEED:
            return
        now = pygame.time.get_ticks()
        if now - self.last_bounce_ms < BOUNCE_COOLDOWN_MS:
            return
        self.last_bounce_ms = now
        self._play("bounce", 0.3 + 0.7 * min(1.0, impact_speed / self.max_speed))      

    def handle_event(self, event):
        # Movement is driven by the mouse position in handle_input;
        # events only matter once the round is over.
        if not self.game_over:
            return

        # Game over screen: any key or click opens the menu
        if not self.in_menu:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.in_menu = True
            return

        # Menu: 1/2/3 or click to pick a difficulty, Esc or click to exit
        choice = "none"
        if event.type == pygame.KEYDOWN:
            names = list(DIFFICULTIES)
            if event.key == pygame.K_ESCAPE:
                choice = None
            elif pygame.K_1 <= event.key < pygame.K_1 + len(names):
                choice = names[event.key - pygame.K_1]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, _, rect in self._menu_buttons():
                if rect.collidepoint(event.pos):
                    choice = action
                    break

        if choice is None:
            pygame.event.post(pygame.event.Event(pygame.QUIT))  # main() quits cleanly
        elif choice != "none":
            self._start_round(choice)

    def handle_input(self):
        if self.game_over:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.width // 2
        dy = mouse_y - self.height // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ax = (dx / dist) * self.tilt_strength
        ay = (dy / dist) * self.tilt_strength
        self.marble.vx += ax
        self.marble.vy += ay

    def update(self):
        if self.game_over:
            return

        elapsed = pygame.time.get_ticks() - self.start_ticks
        if elapsed >= self.time_limit_ms:
            self.game_over = True
            self.result = "timeout"
            self._play("timeout")  # NEW (runs once: update returns early once game_over)
            return

        self.marble.vx *= (1 - self.friction)
        self.marble.vy *= (1 - self.friction)

        speed = (self.marble.vx ** 2 + self.marble.vy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.marble.vx *= scale
            self.marble.vy *= scale

        self.marble.x += self.marble.vx
        self.marble.y += self.marble.vy

        self._resolve_wall_collisions()

        gx = self.goal_x - self.marble.x
        gy = self.goal_y - self.marble.y
        if (gx ** 2 + gy ** 2) ** 0.5 <= self.goal_radius:
            self.game_over = True
            self.result = "solved"
            self.finish_time_ms = elapsed
            self._play("win")  # NEW
    
    def _resolve_wall_collisions(self):
        r = self.marble.radius
        for wall in self.walls:
            wall_rect = wall.rect()

            # Closest point on the wall rect to the marble's center
            closest_x = max(wall_rect.left, min(self.marble.x, wall_rect.right))
            closest_y = max(wall_rect.top, min(self.marble.y, wall_rect.bottom))

            dx = self.marble.x - closest_x
            dy = self.marble.y - closest_y
            dist_sq = dx * dx + dy * dy

            if dist_sq >= r * r:
                continue  # no collision (circle doesn't touch the wall)

            if dist_sq > 0:
                # Center is outside the rect: normal points from closest point to center
                dist = math.sqrt(dist_sq)
                nx, ny = dx / dist, dy / dist
                penetration = r - dist
            else:
                # Center is inside/on edge: push out through nearest side
                left = self.marble.x - wall_rect.left
                right = wall_rect.right - self.marble.x
                top = self.marble.y - wall_rect.top
                bottom = wall_rect.bottom - self.marble.y
                nearest = min(left, right, top, bottom)

                if nearest == left:
                    nx, ny = -1.0, 0.0
                elif nearest == right:
                    nx, ny = 1.0, 0.0
                elif nearest == top:
                    nx, ny = 0.0, -1.0
                else:
                    nx, ny = 0.0, 1.0
                penetration = nearest + r

            # Push the marble out along the collision normal
            self.marble.x += nx * penetration
            self.marble.y += ny * penetration

            # Reflect velocity component along normal if moving into wall
            vn = self.marble.vx * nx + self.marble.vy * ny
            if vn < 0:
                self.marble.vx -= (1 + 0.3) * vn * nx
                self.marble.vy -= (1 + 0.3) * vn * ny
                self._play_bounce(-vn)  # NEW

    def _render_menu(self, screen):
        title = self.big_font.render("Play Again?", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 150)))

        mouse_pos = pygame.mouse.get_pos()
        for _, label, rect in self._menu_buttons():
            fill = (70, 70, 70) if rect.collidepoint(mouse_pos) else (40, 40, 40)
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
            text = self.font.render(label, True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))

    def render(self, screen):
        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        if self.game_over:
            # Freeze the HUD timer once the round ends
            elapsed = self.finish_time_ms if self.result == "solved" else self.time_limit_ms
        else:
            elapsed = pygame.time.get_ticks() - self.start_ticks
        seconds_left = max(0, (self.time_limit_ms - elapsed) // 1000)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, WHITE)
        screen.blit(timer_text, (10, 10))

        if self.game_over:
            # Dim the maze behind the message
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200 if self.in_menu else 180))
            screen.blit(overlay, (0, 0))

            if self.in_menu:
                self._render_menu(screen)
                return

            cx, cy = self.width // 2, self.height // 2

            if self.result == "solved":
                title = self.big_font.render("You Win!", True, GOAL_COLOR)
                screen.blit(title, title.get_rect(center=(cx, cy - 50)))
                time_text = self.font.render(
                    f"Finish time: {self.finish_time_ms / 1000:.1f}s", True, WHITE)
                screen.blit(time_text, time_text.get_rect(center=(cx, cy + 10)))
            else:
                title = self.big_font.render("Time's Up!", True, WHITE)
                screen.blit(title, title.get_rect(center=(cx, cy - 30)))

            prompt = self.font.render("Press any key or click to continue", True, WHITE)
            screen.blit(prompt, prompt.get_rect(center=(cx, cy + 70)))
