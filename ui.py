import pygame
import math
import time
from config import *
from utils import lerp

# Fonts
# We initialize fonts here, but pygame.init() must be called before importing this module
# or we wrap initialization. Since main.py calls pygame.init() first, this is risky if imported at top level.
# Better to initialize fonts in a function or class.
# However, for simplicity in this refactor, we'll assume pygame is initialized.
# To be safe, let's lazy load or initialize in a function.
# But `main.py` imports `ui` *after* `pygame.init()` usually? No, imports happen at top.
# So `pygame.init()` in `main.py` happens *after* imports.
# This means `pygame.font.SysFont` will fail at import time if pygame isn't initialized.
# We should wrap font creation.

_fonts = {}

def get_font(name, size, bold=False):
    key = (name, size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(name, size, bold=bold)
    return _fonts[key]

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


def show_start_screen(screen, clock, sound_manager):
    """Display start screen with difficulty selection"""
    # Initialize fonts if needed (or use get_font)
    title_font_dynamic = get_font('Arial', 72, bold=True) # Placeholder size, will scale
    small_font = get_font('Arial', 24)

    title_pulse = 0

    while True:
        dt = clock.tick(60) / 1000.0
        title_pulse = (title_pulse + dt) % (2 * math.pi)

        # Draw animated background
        draw_gradient_rect(screen, pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                          DARK_BG, DARK_BG2, vertical=True)

        # Floating particles in background
        for i in range(20):
            x = (i * 40 + time.time() * 20) % SCREEN_WIDTH
            y = (i * 30) % SCREEN_HEIGHT
            alpha = int(50 + 50 * math.sin(time.time() + i))
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*VIBRANT_CYAN[:3], alpha), (5, 5), 5)
            screen.blit(s, (x, y))

        # Title with pulsing effect
        title_scale = 1.0 + 0.1 * math.sin(title_pulse)
        title_size = int(72 * title_scale)
        # We need to recreate font for smooth scaling or scale surface?
        # Recreating font is cleaner for text but slower.
        # Let's use get_font to cache sizes if possible, but continuous scaling fills cache.
        # For this refactor, let's just create it.
        current_title_font = pygame.font.SysFont('Arial', title_size, bold=True)

        draw_glow_text(screen, "DROP GAME",
                      (SCREEN_WIDTH // 2 - 150, 80),
                      current_title_font, VIBRANT_PURPLE, VIBRANT_PINK)

        # Subtitle
        subtitle = small_font.render("Type to Survive!", True, VIBRANT_CYAN)
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

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
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset))
            y_offset += 35

        # Difficulty buttons
        easy_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 480, 180, 50)
        medium_rect = pygame.Rect(SCREEN_WIDTH // 2 - 90, 480, 180, 50)
        hard_rect = pygame.Rect(SCREEN_WIDTH // 2 + 120, 480, 180, 50)

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


def show_results_screen(screen, clock, sound_manager, correct_count, mistake_count,
                       typed_mistakes, missed_letters, max_combo, total_score):
    """Display enhanced results screen"""
    results_font = get_font('Arial', 48, bold=True)
    font = get_font('Arial', 36, bold=True)
    small_font = get_font('Arial', 24)

    # Animate score counting
    displayed_score = 0
    score_animation_time = 0

    sound_manager.play('game_over')

    # Need ease_out_cubic, import it or pass it? Imported from utils.
    from utils import ease_out_cubic

    while True:
        dt = clock.tick(60) / 1000.0

        # Draw gradient background
        draw_gradient_rect(screen, pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
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
                      (SCREEN_WIDTH // 2 - 150, 50),
                      results_font, VIBRANT_PURPLE, VIBRANT_PINK)

        # Score display
        score_text = results_font.render(f"Score: {displayed_score:,}", True, VIBRANT_GOLD)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 130))

        # Stats
        stats_y = 220
        stats = [
            (f"Correct: {correct_count}", VIBRANT_GREEN),
            (f"Mistakes: {mistake_count}", DANGER_RED),
            (f"Max Combo: {max_combo}x", VIBRANT_CYAN),
        ]

        for stat_text, color in stats:
            text = font.render(stat_text, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, stats_y))
            stats_y += 50

        # Performance feedback
        if typed_mistakes:
            most_common_mistake = max(typed_mistakes, key=typed_mistakes.get)
            mistake_feedback = small_font.render(
                f"Most typed mistake: '{most_common_mistake}' ({typed_mistakes[most_common_mistake]}x)",
                True, RED)
            screen.blit(mistake_feedback,
                       (SCREEN_WIDTH // 2 - mistake_feedback.get_width() // 2, 400))

        if missed_letters:
            most_common_miss = max(missed_letters, key=missed_letters.get)
            miss_feedback = small_font.render(
                f"Most missed letter: '{most_common_miss}' ({missed_letters[most_common_miss]}x)",
                True, RED)
            screen.blit(miss_feedback,
                       (SCREEN_WIDTH // 2 - miss_feedback.get_width() // 2, 440))

        # Exit prompt
        prompt_text = small_font.render("Press any key to exit", True, VIBRANT_CYAN)
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, 520))

        pygame.display.flip()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return
