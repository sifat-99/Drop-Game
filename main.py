import pygame
import random
import time
import math
from collections import defaultdict
import os
import array

# 1. Setup and Initialization
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Screen dimensions
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("DropGame - Type to Survive!")

# Modern Color Palette (Dark mode with vibrant accents)
DARK_BG = (15, 15, 35)
DARK_BG2 = (25, 25, 50)
VIBRANT_PURPLE = (138, 43, 226)
VIBRANT_CYAN = (0, 255, 255)
VIBRANT_PINK = (255, 20, 147)
VIBRANT_GOLD = (255, 215, 0)
VIBRANT_GREEN = (0, 255, 127)
WHITE = (255, 255, 255)
RED = (255, 69, 58)
DANGER_RED = (255, 45, 85)

# Fonts
title_font = pygame.font.SysFont('Arial', 72, bold=True)
font = pygame.font.SysFont('Arial', 36, bold=True)
small_font = pygame.font.SysFont('Arial', 24)
results_font = pygame.font.SysFont('Arial', 48, bold=True)

# Game clock
clock = pygame.time.Clock()

# Danger Line
danger_line_y = screen_height - 80

# Assets Directory
assets_dir = os.path.join(os.path.dirname(__file__), 'assets')


# 2. Sound Manager
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.load_assets()
        self.generate_synthetic_sounds()

    def load_assets(self):
        # Load existing correct sound if available
        correct_path = os.path.join(assets_dir, 'correct.mp3')
        if os.path.exists(correct_path):
            try:
                self.sounds['correct'] = pygame.mixer.Sound(correct_path)
                self.sounds['correct'].set_volume(0.4)
            except:
                print("Could not load correct.mp3")

    def generate_synthetic_sounds(self):
        # Generate fallback sounds if assets missing or for other effects
        if 'correct' not in self.sounds:
            self.sounds['correct'] = self._generate_beep(440, 0.1, 'sine')

        self.sounds['miss'] = self._generate_noise(0.3)
        self.sounds['speed_up'] = self._generate_slide(300, 600, 0.2)
        self.sounds['speed_down'] = self._generate_slide(600, 300, 0.2)
        self.sounds['powerup'] = self._generate_chord([523, 659, 784], 0.4) # C Major
        self.sounds['game_over'] = self._generate_slide(400, 100, 1.0)

    def _generate_beep(self, frequency, duration, wave_type='square'):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buffer = array.array('h', [0] * n_samples * 2)

        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == 'sine':
                value = int(32767.0 * math.sin(2.0 * math.pi * frequency * t))
            else: # square
                value = 32767 if int(t * frequency * 2) % 2 == 0 else -32768

            # Stereo
            buffer[i * 2] = value
            buffer[i * 2 + 1] = value

        return pygame.mixer.Sound(buffer)

    def _generate_noise(self, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buffer = array.array('h', [0] * n_samples * 2)

        for i in range(n_samples):
            value = random.randint(-32768, 32767)
            buffer[i * 2] = value
            buffer[i * 2 + 1] = value

        return pygame.mixer.Sound(buffer)

    def _generate_slide(self, start_freq, end_freq, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buffer = array.array('h', [0] * n_samples * 2)

        for i in range(n_samples):
            t = float(i) / sample_rate
            progress = i / n_samples
            freq = start_freq + (end_freq - start_freq) * progress
            value = int(32767.0 * math.sin(2.0 * math.pi * freq * t))

            # Apply envelope (fade out)
            if progress > 0.8:
                value = int(value * (1.0 - (progress - 0.8) * 5))

            buffer[i * 2] = value
            buffer[i * 2 + 1] = value

        return pygame.mixer.Sound(buffer)

    def _generate_chord(self, freqs, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buffer = array.array('h', [0] * n_samples * 2)

        for i in range(n_samples):
            t = float(i) / sample_rate
            value = 0
            for f in freqs:
                value += math.sin(2.0 * math.pi * f * t)
            value = int((value / len(freqs)) * 32767.0)

            # Fade out
            if i > n_samples * 0.8:
                value = int(value * (1 - (i - n_samples * 0.8) / (n_samples * 0.2)))

            buffer[i * 2] = value
            buffer[i * 2 + 1] = value

        return pygame.mixer.Sound(buffer)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()


# 3. Utility Functions
def lerp(start, end, t):
    """Linear interpolation"""
    return start + (end - start) * t


def ease_out_cubic(t):
    """Easing function for smooth animations"""
    return 1 - pow(1 - t, 3)


def draw_gradient_rect(surface, rect, color1, color2, vertical=True):
    """Draw a gradient rectangle"""
    if vertical:
        for y in range(rect.height):
            t = y / rect.height
            color = (
                int(lerp(color1[0], color2[0], t)),
                int(lerp(color1[1], color2[1], t)),
                int(lerp(color1[2], color2[2], t))
            )
            pygame.draw.line(surface, color,
                           (rect.x, rect.y + y),
                           (rect.x + rect.width, rect.y + y))
    else:
        for x in range(rect.width):
            t = x / rect.width
            color = (
                int(lerp(color1[0], color2[0], t)),
                int(lerp(color1[1], color2[1], t)),
                int(lerp(color1[2], color2[2], t))
            )
            pygame.draw.line(surface, color,
                           (rect.x + x, rect.y),
                           (rect.x + x, rect.y + rect.height))


def draw_glow_text(surface, text, pos, font, color, glow_color):
    """Draw text with glow effect"""
    # Draw glow layers
    for offset in range(3, 0, -1):
        glow_alpha = int(100 / offset)
        glow_surf = font.render(text, True, glow_color)
        glow_surf.set_alpha(glow_alpha)
        surface.blit(glow_surf, (pos[0] - offset, pos[1] - offset))
        surface.blit(glow_surf, (pos[0] + offset, pos[1] - offset))
        surface.blit(glow_surf, (pos[0] - offset, pos[1] + offset))
        surface.blit(glow_surf, (pos[0] + offset, pos[1] + offset))

    # Draw main text
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, pos)


# 4. Particle System
class Particle:
    def __init__(self, x, y, color, velocity=None):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity if velocity else [random.uniform(-2, 2), random.uniform(-4, -1)]
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.size = random.randint(3, 6)

    def update(self, dt):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity[1] += 0.2  # Gravity
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            size = int(self.size * (self.lifetime / self.max_lifetime))
            if size > 0:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color_with_alpha = (*self.color[:3], alpha)
                pygame.draw.circle(s, color_with_alpha, (size, size), size)
                surface.blit(s, (int(self.x - size), int(self.y - size)))


class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.font = font
        self.lifetime = 1.5
        self.max_lifetime = 1.5

    def update(self, dt):
        self.lifetime -= dt
        progress = 1 - (self.lifetime / self.max_lifetime)
        self.y = self.start_y - ease_out_cubic(progress) * 50

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            text_surf = self.font.render(self.text, True, self.color)
            text_surf.set_alpha(alpha)
            surface.blit(text_surf, (int(self.x), int(self.y)))


# 5. Power-up System
class PowerUp:
    def __init__(self, type_name):
        self.type = type_name
        self.x = random.randint(50, screen_width - 50)
        self.y = 0
        self.speed = 2
        self.size = 25
        self.angle = 0

        if type_name == "slow":
            self.color = VIBRANT_CYAN
            self.symbol = "⏱"
        elif type_name == "time":
            self.color = VIBRANT_GOLD
            self.symbol = "⏰"
        elif type_name == "freeze":
            self.color = VIBRANT_PURPLE
            self.symbol = "❄"

    def update(self):
        self.y += self.speed
        self.angle += 5

    def draw(self, surface):
        # Draw rotating glow
        for i in range(3):
            s = pygame.Surface((self.size * 2 + i * 10, self.size * 2 + i * 10), pygame.SRCALPHA)
            color_with_alpha = (*self.color[:3], 50)
            pygame.draw.circle(s, color_with_alpha, (self.size + i * 5, self.size + i * 5), self.size + i * 5)
            surface.blit(s, (int(self.x - self.size - i * 5), int(self.y - self.size - i * 5)))

        # Draw power-up circle
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size, 3)

        # Draw symbol
        symbol_surf = font.render(self.symbol, True, WHITE)
        surface.blit(symbol_surf,
                    (int(self.x - symbol_surf.get_width() // 2),
                     int(self.y - symbol_surf.get_height() // 2)))


# 6. Game Objects (The Falling Letters)
class FallingLetter:
    def __init__(self, speed_multiplier=1.0):
        self.char = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.x = random.randint(50, screen_width - 50)
        self.y = -20
        self.target_y = self.y
        self.speed = random.uniform(1, 3) * speed_multiplier
        self.size_scale = 1.0
        self.angle = random.uniform(-5, 5)
        self.spawn_time = 0
        self.pulse = 0

    def update(self, dt, is_frozen=False):
        # Spawn animation
        if self.spawn_time < 0.5:
            self.spawn_time += dt
            self.size_scale = ease_out_cubic(min(1.0, self.spawn_time / 0.5))

        # Movement
        if not is_frozen:
            self.y += self.speed

        # Pulse effect when near danger line
        if self.y > danger_line_y - 100:
            self.pulse = (self.pulse + dt * 5) % (2 * math.pi)
            danger_factor = (self.y - (danger_line_y - 100)) / 100
            self.size_scale = 1.0 + 0.2 * math.sin(self.pulse) * danger_factor

    def draw(self, surface):
        # Calculate color based on danger level
        if self.y > danger_line_y - 100:
            danger_factor = min(1.0, (self.y - (danger_line_y - 100)) / 100)
            color = (
                int(lerp(255, 255, danger_factor)),
                int(lerp(255, 69, danger_factor)),
                int(lerp(255, 58, danger_factor))
            )
        else:
            color = WHITE

        # Draw glow effect
        glow_size = int(40 * self.size_scale)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*VIBRANT_CYAN[:3], 30), (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))

        # Draw letter with shadow
        letter_font = pygame.font.SysFont('Arial', int(36 * self.size_scale), bold=True)

        # Shadow
        shadow_surf = letter_font.render(self.char, True, (0, 0, 0, 100))
        surface.blit(shadow_surf, (int(self.x - shadow_surf.get_width() // 2 + 2),
                                   int(self.y - shadow_surf.get_height() // 2 + 2)))

        # Main letter
        text_surf = letter_font.render(self.char, True, color)
        surface.blit(text_surf, (int(self.x - text_surf.get_width() // 2),
                                int(self.y - text_surf.get_height() // 2)))


# 7. Screen Shake Effect
class ScreenShake:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.trauma = 0

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        if self.trauma > 0:
            self.trauma = max(0, self.trauma - dt * 2)
            shake_amount = self.trauma * self.trauma * 10
            self.offset_x = random.uniform(-shake_amount, shake_amount)
            self.offset_y = random.uniform(-shake_amount, shake_amount)
        else:
            self.offset_x = 0
            self.offset_y = 0


# 8. Start Screen
def show_start_screen(sound_manager):
    """Display start screen with difficulty selection"""
    screen_shake = ScreenShake()
    title_pulse = 0

    while True:
        dt = clock.tick(60) / 1000.0
        title_pulse = (title_pulse + dt) % (2 * math.pi)

        # Draw animated background
        draw_gradient_rect(screen, pygame.Rect(0, 0, screen_width, screen_height),
                          DARK_BG, DARK_BG2, vertical=True)

        # Floating particles in background
        for i in range(20):
            x = (i * 40 + time.time() * 20) % screen_width
            y = (i * 30) % screen_height
            alpha = int(50 + 50 * math.sin(time.time() + i))
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*VIBRANT_CYAN[:3], alpha), (5, 5), 5)
            screen.blit(s, (x, y))

        # Title with pulsing effect
        title_scale = 1.0 + 0.1 * math.sin(title_pulse)
        title_size = int(72 * title_scale)
        title_font_dynamic = pygame.font.SysFont('Arial', title_size, bold=True)

        draw_glow_text(screen, "DROP GAME",
                      (screen_width // 2 - 150, 80),
                      title_font_dynamic, VIBRANT_PURPLE, VIBRANT_PINK)

        # Subtitle
        subtitle = small_font.render("Type to Survive!", True, VIBRANT_CYAN)
        screen.blit(subtitle, (screen_width // 2 - subtitle.get_width() // 2, 180))

        # Instructions
        instructions = [
            "Type the falling letters before they reach the danger line!",
            "UP/DOWN Arrows to control speed manually",
            "Build combos for higher scores!",
            "Collect power-ups for special abilities!",
            "",
            "Select Difficulty:"
        ]

        y_offset = 250
        for instruction in instructions:
            text = small_font.render(instruction, True, WHITE)
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, y_offset))
            y_offset += 35

        # Difficulty buttons
        easy_rect = pygame.Rect(screen_width // 2 - 300, 480, 180, 50)
        medium_rect = pygame.Rect(screen_width // 2 - 90, 480, 180, 50)
        hard_rect = pygame.Rect(screen_width // 2 + 120, 480, 180, 50)

        mouse_pos = pygame.mouse.get_pos()

        # Draw buttons with hover effect
        for rect, text, color in [
            (easy_rect, "EASY", VIBRANT_GREEN),
            (medium_rect, "MEDIUM", VIBRANT_GOLD),
            (hard_rect, "HARD", DANGER_RED)
        ]:
            is_hover = rect.collidepoint(mouse_pos)
            border_width = 4 if is_hover else 2

            # Button background with glow on hover
            if is_hover:
                glow_rect = rect.inflate(10, 10)
                s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(s, (*color[:3], 50), s.get_rect(), border_radius=10)
                screen.blit(s, glow_rect.topleft)

            pygame.draw.rect(screen, DARK_BG2, rect, border_radius=10)
            pygame.draw.rect(screen, color, rect, border_width, border_radius=10)

            button_text = small_font.render(text, True, color if not is_hover else WHITE)
            screen.blit(button_text,
                       (rect.centerx - button_text.get_width() // 2,
                        rect.centery - button_text.get_height() // 2))

        pygame.display.flip()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_rect.collidepoint(event.pos):
                    sound_manager.play('correct')
                    return "easy"
                elif medium_rect.collidepoint(event.pos):
                    sound_manager.play('correct')
                    return "medium"
                elif hard_rect.collidepoint(event.pos):
                    sound_manager.play('correct')
                    return "hard"


# 9. Results Screen
def show_results_screen(correct_count, mistake_count, typed_mistakes, missed_letters,
                       max_combo, total_score, sound_manager):
    """Display enhanced results screen"""
    # Animate score counting
    displayed_score = 0
    score_animation_time = 0

    sound_manager.play('game_over')

    while True:
        dt = clock.tick(60) / 1000.0

        # Draw gradient background
        draw_gradient_rect(screen, pygame.Rect(0, 0, screen_width, screen_height),
                          DARK_BG, DARK_BG2, vertical=True)

        # Animated score reveal
        if score_animation_time < 2.0:
            score_animation_time += dt
            progress = ease_out_cubic(min(1.0, score_animation_time / 2.0))
            displayed_score = int(total_score * progress)
        else:
            displayed_score = total_score

        # Title
        draw_glow_text(screen, "GAME OVER",
                      (screen_width // 2 - 150, 50),
                      results_font, VIBRANT_PURPLE, VIBRANT_PINK)

        # Score display
        score_text = results_font.render(f"Score: {displayed_score:,}", True, VIBRANT_GOLD)
        screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, 130))

        # Stats
        stats_y = 220
        stats = [
            (f"Correct: {correct_count}", VIBRANT_GREEN),
            (f"Mistakes: {mistake_count}", DANGER_RED),
            (f"Max Combo: {max_combo}x", VIBRANT_CYAN),
        ]

        for stat_text, color in stats:
            text = font.render(stat_text, True, color)
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, stats_y))
            stats_y += 50

        # Performance feedback
        if typed_mistakes:
            most_common_mistake = max(typed_mistakes, key=typed_mistakes.get)
            mistake_feedback = small_font.render(
                f"Most typed mistake: '{most_common_mistake}' ({typed_mistakes[most_common_mistake]}x)",
                True, RED)
            screen.blit(mistake_feedback,
                       (screen_width // 2 - mistake_feedback.get_width() // 2, 400))

        if missed_letters:
            most_common_miss = max(missed_letters, key=missed_letters.get)
            miss_feedback = small_font.render(
                f"Most missed letter: '{most_common_miss}' ({missed_letters[most_common_miss]}x)",
                True, RED)
            screen.blit(miss_feedback,
                       (screen_width // 2 - miss_feedback.get_width() // 2, 440))

        # Exit prompt
        prompt_text = small_font.render("Press any key to exit", True, VIBRANT_CYAN)
        screen.blit(prompt_text, (screen_width // 2 - prompt_text.get_width() // 2, 520))

        pygame.display.flip()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return


# 10. Main Game Loop
def main():
    # Initialize Sound Manager
    sound_manager = SoundManager()

    # Show start screen
    difficulty = show_start_screen(sound_manager)
    if difficulty is None:
        return

    # Difficulty settings
    if difficulty == "easy":
        speed_multiplier = 0.7
        spawn_rate = 80
        game_duration = 60
    elif difficulty == "medium":
        speed_multiplier = 1.0
        spawn_rate = 60
        game_duration = 60
    else:  # hard
        speed_multiplier = 1.3
        spawn_rate = 45
        game_duration = 60

    running = True
    letters = []
    particles = []
    floating_texts = []
    power_ups = []
    spawn_timer = 0
    powerup_spawn_timer = 0
    recent_performance = []
    correct_count = 0
    mistake_count = 0
    typed_mistakes = defaultdict(int)
    missed_letters = defaultdict(int)
    start_time = time.time()

    # Combo system
    combo = 0
    max_combo = 0
    combo_display_scale = 1.0

    # Power-up states
    slow_motion_time = 0
    freeze_time = 0

    # Score
    total_score = 0

    # Screen shake
    screen_shake = ScreenShake()

    # Background animation
    bg_offset = 0

    while running:
        dt = clock.tick(60) / 1000.0
        current_time = time.time()
        elapsed_time = current_time - start_time

        if elapsed_time >= game_duration:
            running = False

        # Update power-up timers
        if slow_motion_time > 0:
            slow_motion_time -= dt
            effective_dt = dt * 0.5
        else:
            effective_dt = dt

        if freeze_time > 0:
            freeze_time -= dt

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Manual Speed Control
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    speed_multiplier = min(speed_multiplier + 0.2, 5.0)
                    sound_manager.play('speed_up')
                    floating_texts.append(
                        FloatingText("SPEED UP >>", screen_width // 2, screen_height // 2,
                                   VIBRANT_CYAN, font)
                    )
                elif event.key == pygame.K_DOWN:
                    speed_multiplier = max(speed_multiplier - 0.2, 0.5)
                    sound_manager.play('speed_down')
                    floating_texts.append(
                        FloatingText("<< SLOW DOWN", screen_width // 2, screen_height // 2,
                                   VIBRANT_GREEN, font)
                    )

                # Typing Logic
                pressed_key = pygame.key.name(event.key).upper()
                if 'A' <= pressed_key <= 'Z' and len(pressed_key) == 1:
                    found = False
                    for letter in letters[:]:
                        if letter.char == pressed_key:
                            letters.remove(letter)
                            correct_count += 1
                            combo += 1
                            max_combo = max(max_combo, combo)

                            # Calculate score with combo multiplier
                            points = 10 * (1 + combo * 0.1)
                            total_score += int(points)

                            # Visual feedback
                            combo_display_scale = 1.5
                            floating_texts.append(
                                FloatingText(f"+{int(points)}", letter.x, letter.y,
                                           VIBRANT_GOLD, font)
                            )

                            # Audio feedback
                            sound_manager.play('correct')

                            # Particle explosion
                            for _ in range(15):
                                particles.append(
                                    Particle(letter.x, letter.y, VIBRANT_CYAN)
                                )

                            recent_performance.append((current_time, "correct"))
                            found = True
                            break

                    if not found:
                        mistake_count += 1
                        typed_mistakes[pressed_key] += 1
                        recent_performance.append((current_time, "mistake"))
                        combo = 0
                        screen_shake.add_trauma(0.3)
                        sound_manager.play('miss')

                        # Visual feedback for mistake
                        floating_texts.append(
                            FloatingText("MISS!", screen_width // 2, screen_height // 2,
                                       DANGER_RED, font)
                        )

        # Adaptive difficulty
        recent_performance = [(t, p) for t, p in recent_performance if current_time - t < 15]
        if len(recent_performance) > 5:
            recent_correct = sum(1 for _, p in recent_performance if p == "correct")
            accuracy = recent_correct / len(recent_performance)
            if accuracy > 0.85:
                new_speed = min(speed_multiplier * 1.02, 3.0)
                if int(new_speed * 10) > int(speed_multiplier * 10): # Only play sound on significant change
                     sound_manager.play('speed_up')
                speed_multiplier = new_speed
                spawn_rate = max(spawn_rate * 0.98, 20)
            elif accuracy < 0.6:
                new_speed = max(speed_multiplier * 0.98, 0.5)
                if int(new_speed * 10) < int(speed_multiplier * 10):
                    sound_manager.play('speed_down')
                speed_multiplier = new_speed
                spawn_rate = min(spawn_rate * 1.02, 120)

        # Spawn letters
        spawn_timer += 1
        if spawn_timer >= spawn_rate:
            letters.append(FallingLetter(speed_multiplier))
            spawn_timer = 0

        # Spawn power-ups
        powerup_spawn_timer += dt
        if powerup_spawn_timer >= 15:  # Every 15 seconds
            power_type = random.choice(["slow", "time", "freeze"])
            power_ups.append(PowerUp(power_type))
            powerup_spawn_timer = 0

        # Update game objects
        for letter in letters[:]:
            letter.update(effective_dt, freeze_time > 0)
            if letter.y >= danger_line_y:
                letters.remove(letter)
                mistake_count += 1
                missed_letters[letter.char] += 1
                combo = 0
                screen_shake.add_trauma(0.5)
                sound_manager.play('miss')

        for powerup in power_ups[:]:
            powerup.update()
            if powerup.y > screen_height:
                power_ups.remove(powerup)
            # Check collision with player area (bottom of screen)
            elif powerup.y > screen_height - 100:
                power_ups.remove(powerup)
                sound_manager.play('powerup')
                if powerup.type == "slow":
                    slow_motion_time = 5.0
                elif powerup.type == "time":
                    game_duration += 10
                elif powerup.type == "freeze":
                    freeze_time = 3.0

                # Visual feedback
                floating_texts.append(
                    FloatingText(f"{powerup.symbol} Power-Up!", screen_width // 2,
                               screen_height - 150, powerup.color, font)
                )

        for particle in particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                particles.remove(particle)

        for text in floating_texts[:]:
            text.update(dt)
            if text.lifetime <= 0:
                floating_texts.remove(text)

        # Update screen shake
        screen_shake.update(dt)

        # Update combo scale
        if combo_display_scale > 1.0:
            combo_display_scale = lerp(combo_display_scale, 1.0, dt * 5)

        # === DRAWING ===

        # Animated gradient background
        bg_offset = (bg_offset + dt * 10) % screen_height
        draw_gradient_rect(screen, pygame.Rect(0, 0, screen_width, screen_height),
                          DARK_BG, DARK_BG2, vertical=True)

        # Background particles
        for i in range(30):
            x = (i * 27 + bg_offset * 2) % screen_width
            y = (i * 20 + bg_offset) % screen_height
            alpha = int(30 + 20 * math.sin(current_time + i))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*VIBRANT_PURPLE[:3], alpha), (3, 3), 3)
            screen.blit(s, (x, y))

        # Apply screen shake
        shake_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

        # Danger line with glow
        danger_glow_size = 10
        for i in range(danger_glow_size):
            alpha = int(100 * (1 - i / danger_glow_size))
            pygame.draw.line(shake_surface, (*DANGER_RED[:3], alpha),
                           (0, danger_line_y - i),
                           (screen_width, danger_line_y - i), 2)
        pygame.draw.line(shake_surface, DANGER_RED, (0, danger_line_y),
                        (screen_width, danger_line_y), 4)

        # Draw game objects
        for letter in letters:
            letter.draw(shake_surface)

        for powerup in power_ups:
            powerup.draw(shake_surface)

        for particle in particles:
            particle.draw(shake_surface)

        for text in floating_texts:
            text.draw(shake_surface)

        # HUD
        # Score
        score_text = font.render(f"Score: {total_score:,}", True, VIBRANT_GOLD)
        shake_surface.blit(score_text, (10, 10))

        # Correct/Mistakes
        stats_text = small_font.render(f"✓ {correct_count}  ✗ {mistake_count}", True, WHITE)
        shake_surface.blit(stats_text, (10, 50))

        # Speed Indicator
        speed_text = small_font.render(f"Speed: {speed_multiplier:.1f}x", True, VIBRANT_CYAN)
        shake_surface.blit(speed_text, (10, 90))

        # Combo meter
        if combo > 0:
            combo_size = int(36 * combo_display_scale)
            combo_font_dynamic = pygame.font.SysFont('Arial', combo_size, bold=True)
            combo_color = VIBRANT_CYAN if combo < 10 else VIBRANT_PINK
            draw_glow_text(shake_surface, f"{combo}x COMBO!",
                          (screen_width // 2 - 80, 10),
                          combo_font_dynamic, combo_color, VIBRANT_PURPLE)

        # Timer with progress bar
        time_left = game_duration - int(elapsed_time)
        progress = 1 - (elapsed_time / game_duration)

        # Progress bar background
        bar_width = 200
        bar_height = 20
        bar_x = screen_width - bar_width - 10
        bar_y = 10

        pygame.draw.rect(shake_surface, DARK_BG2,
                        (bar_x, bar_y, bar_width, bar_height), border_radius=10)

        # Progress bar fill with gradient
        if progress > 0:
            fill_width = int(bar_width * progress)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            if progress > 0.5:
                draw_gradient_rect(shake_surface, fill_rect, VIBRANT_GREEN, VIBRANT_CYAN)
            elif progress > 0.25:
                draw_gradient_rect(shake_surface, fill_rect, VIBRANT_GOLD, VIBRANT_GREEN)
            else:
                draw_gradient_rect(shake_surface, fill_rect, DANGER_RED, VIBRANT_GOLD)

        # Timer text
        timer_text = small_font.render(f"{time_left // 60:02d}:{time_left % 60:02d}",
                                      True, WHITE)
        shake_surface.blit(timer_text,
                          (bar_x + bar_width // 2 - timer_text.get_width() // 2,
                           bar_y + 2))

        # Active power-up indicators
        powerup_y = 80
        if slow_motion_time > 0:
            slow_text = small_font.render(f"⏱ Slow: {int(slow_motion_time)}s",
                                         True, VIBRANT_CYAN)
            shake_surface.blit(slow_text, (screen_width - 150, powerup_y))
            powerup_y += 30

        if freeze_time > 0:
            freeze_text = small_font.render(f"❄ Freeze: {int(freeze_time)}s",
                                          True, VIBRANT_PURPLE)
            shake_surface.blit(freeze_text, (screen_width - 150, powerup_y))
            powerup_y += 30

        # Blit shake surface with offset
        screen.blit(shake_surface, (int(screen_shake.offset_x), int(screen_shake.offset_y)))

        pygame.display.flip()

    # Show results
    show_results_screen(correct_count, mistake_count, typed_mistakes, missed_letters,
                       max_combo, total_score, sound_manager)
    pygame.quit()


if __name__ == '__main__':
    main()
