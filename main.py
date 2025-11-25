import pygame
import random
import time
import math
from collections import defaultdict
import os

# Initialize pygame first
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Import modules after initialization
from config import *
from utils import lerp, ease_out_cubic
from sound_manager import SoundManager
from game_objects import Particle, FloatingText, PowerUp, FallingLetter, ScreenShake
from ui import draw_gradient_rect, draw_glow_text, show_start_screen, show_results_screen

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("DropGame - Type to Survive!")

# Fonts
# We need to initialize fonts here to pass them to objects if needed,
# or rely on them being created in functions.
# For main loop, we need fonts for HUD.
font = pygame.font.SysFont('Arial', 36, bold=True)
small_font = pygame.font.SysFont('Arial', 24)
results_font = pygame.font.SysFont('Arial', 48, bold=True)

# Game clock
clock = pygame.time.Clock()

def main():
    # Initialize Sound Manager
    sound_manager = SoundManager()

    # Show start screen
    difficulty = show_start_screen(screen, clock, sound_manager)
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
                        FloatingText("SPEED UP >>", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                   VIBRANT_CYAN, font)
                    )
                elif event.key == pygame.K_DOWN:
                    speed_multiplier = max(speed_multiplier - 0.2, 0.5)
                    sound_manager.play('speed_down')
                    floating_texts.append(
                        FloatingText("<< SLOW DOWN", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
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
                            FloatingText("MISS!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
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
            if letter.y >= DANGER_LINE_Y:
                letters.remove(letter)
                mistake_count += 1
                missed_letters[letter.char] += 1
                combo = 0
                screen_shake.add_trauma(0.5)
                sound_manager.play('miss')

        for powerup in power_ups[:]:
            powerup.update()
            if powerup.y > SCREEN_HEIGHT:
                power_ups.remove(powerup)
            # Check collision with player area (bottom of screen)
            elif powerup.y > SCREEN_HEIGHT - 100:
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
                    FloatingText(f"{powerup.symbol} Power-Up!", SCREEN_WIDTH // 2,
                               SCREEN_HEIGHT - 150, powerup.color, font)
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
        bg_offset = (bg_offset + dt * 10) % SCREEN_HEIGHT
        draw_gradient_rect(screen, pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                          DARK_BG, DARK_BG2, vertical=True)

        # Background particles
        for i in range(30):
            x = (i * 27 + bg_offset * 2) % SCREEN_WIDTH
            y = (i * 20 + bg_offset) % SCREEN_HEIGHT
            alpha = int(30 + 20 * math.sin(current_time + i))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*VIBRANT_PURPLE[:3], alpha), (3, 3), 3)
            screen.blit(s, (x, y))

        # Apply screen shake
        shake_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Danger line with glow
        danger_glow_size = 10
        for i in range(danger_glow_size):
            alpha = int(100 * (1 - i / danger_glow_size))
            pygame.draw.line(shake_surface, (*DANGER_RED[:3], alpha),
                           (0, DANGER_LINE_Y - i),
                           (SCREEN_WIDTH, DANGER_LINE_Y - i), 2)
        pygame.draw.line(shake_surface, DANGER_RED, (0, DANGER_LINE_Y),
                        (SCREEN_WIDTH, DANGER_LINE_Y), 4)

        # Draw game objects
        for letter in letters:
            letter.draw(shake_surface)

        for powerup in power_ups:
            powerup.draw(shake_surface, font) # Pass font to powerup

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
                          (SCREEN_WIDTH // 2 - 80, 10),
                          combo_font_dynamic, combo_color, VIBRANT_PURPLE)

        # Timer with progress bar
        time_left = game_duration - int(elapsed_time)
        progress = 1 - (elapsed_time / game_duration)

        # Progress bar background
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 10
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
            shake_surface.blit(slow_text, (SCREEN_WIDTH - 150, powerup_y))
            powerup_y += 30

        if freeze_time > 0:
            freeze_text = small_font.render(f"❄ Freeze: {int(freeze_time)}s",
                                          True, VIBRANT_PURPLE)
            shake_surface.blit(freeze_text, (SCREEN_WIDTH - 150, powerup_y))
            powerup_y += 30

        # Blit shake surface with offset
        screen.blit(shake_surface, (int(screen_shake.offset_x), int(screen_shake.offset_y)))

        pygame.display.flip()

    # Show results
    show_results_screen(screen, clock, sound_manager, correct_count, mistake_count,
                       typed_mistakes, missed_letters, max_combo, total_score)
    pygame.quit()


if __name__ == '__main__':
    main()
