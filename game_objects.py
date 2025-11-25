import pygame
import random
import math
from config import *
from utils import ease_out_cubic, lerp

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


class PowerUp:
    def __init__(self, type_name):
        self.type = type_name
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = 0
        self.speed = 2
        self.size = 25
        self.angle = 0

        # We need a font for the symbol, but we can't easily pass it in __init__ without changing signature everywhere
        # For now, let's create a small font locally or assume it's passed.
        # Better: Pass font in draw() or use a static/class variable.
        # Let's use a default font for now if not provided, but ideally we pass it.
        # The original code used a global 'font'. Let's assume we'll pass font to draw().

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

    def draw(self, surface, font):
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


class FallingLetter:
    def __init__(self, speed_multiplier=1.0):
        self.char = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.x = random.randint(50, SCREEN_WIDTH - 50)
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
        if self.y > DANGER_LINE_Y - 100:
            self.pulse = (self.pulse + dt * 5) % (2 * math.pi)
            danger_factor = (self.y - (DANGER_LINE_Y - 100)) / 100
            self.size_scale = 1.0 + 0.2 * math.sin(self.pulse) * danger_factor

    def draw(self, surface):
        # Calculate color based on danger level
        if self.y > DANGER_LINE_Y - 100:
            danger_factor = min(1.0, (self.y - (DANGER_LINE_Y - 100)) / 100)
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
        # Note: We need to create fonts here or pass them. Creating fonts every frame is bad.
        # But FallingLetter needs dynamic size. Pygame font creation is somewhat expensive.
        # Optimization: Cache fonts or use a limited set of sizes.
        # For this refactor, I'll keep it as is (creating font) to match original behavior,
        # but ideally we'd have a FontManager.
        letter_font = pygame.font.SysFont('Arial', int(36 * self.size_scale), bold=True)

        # Shadow
        shadow_surf = letter_font.render(self.char, True, (0, 0, 0, 100))
        surface.blit(shadow_surf, (int(self.x - shadow_surf.get_width() // 2 + 2),
                                   int(self.y - shadow_surf.get_height() // 2 + 2)))

        # Main letter
        text_surf = letter_font.render(self.char, True, color)
        surface.blit(text_surf, (int(self.x - text_surf.get_width() // 2),
                                int(self.y - text_surf.get_height() // 2)))


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
