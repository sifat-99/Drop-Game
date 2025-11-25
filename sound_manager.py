import pygame
import math
import random
import array
import os
from config import ASSETS_DIR

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.load_assets()
        self.generate_synthetic_sounds()

    def load_assets(self):
        # Load existing correct sound if available
        correct_path = os.path.join(ASSETS_DIR, 'correct.mp3')
        if os.path.exists(correct_path):
            try:
                self.sounds['correct'] = pygame.mixer.Sound(correct_path)
                self.sounds['correct'].set_volume(0.4)
            except:
                print("Could not load correct.mp3")

        # Load letter sounds
        import string
        for letter in string.ascii_uppercase:
            path = os.path.join(ASSETS_DIR, f'{letter}.wav')
            if os.path.exists(path):
                try:
                    self.sounds[f'letter_{letter}'] = pygame.mixer.Sound(path)
                    self.sounds[f'letter_{letter}'].set_volume(0.6)
                except:
                    print(f"Could not load {letter}.wav")

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
