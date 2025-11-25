# DropGame - Type to Survive! 🎮

DropGame is a modern, visually stunning typing survival game built with Python and Pygame. Test your typing speed and accuracy as you defend against falling letters, build massive combos, and utilize power-ups to survive!

![DropGame Banner](assets/background.webp)

## ✨ Features

### 🎨 Visual Experience
- **Modern Dark Mode**: Sophisticated dark gradient background with vibrant neon accents.
- **Particle System**: Explosive particle effects on correct hits and dynamic background ambience.
- **Smooth Animations**: Easing functions for UI elements, letter spawns, and floating text.
- **Screen Shake**: Impactful visual feedback for mistakes and misses.
- **Glow Effects**: Multi-layered glow rendering for text and game objects.

### 🔊 Immersive Audio
- **Dynamic Sound Engine**: Custom `SoundManager` generates retro-style synthetic sound effects on the fly (no external files required!).
- **Adaptive Audio**: Distinct sounds for hits, misses, speed changes, and power-ups.
- **Audio Feedback**: Audio cues sync with visual events for a cohesive experience.

### 🕹️ Gameplay Mechanics
- **Combo System**: Build multipliers (up to 10x+) by typing consecutively without errors.
- **Power-Ups**:
  - ⏱ **Slow Motion**: Slows down time for 5 seconds.
  - ⏰ **Bonus Time**: Adds 10 seconds to the clock.
  - ❄ **Freeze**: Stops all letters for 3 seconds.
- **Adaptive Difficulty**: Game speed adjusts automatically based on your accuracy (85%+ speeds up, <60% slows down).
- **Manual Speed Control**: Take control of the pace with manual speed adjustments.

---

## 🚀 Installation & Usage

### Prerequisites
- Python 3.x
- Pygame (`pip install pygame`)

### Running the Game
1. Clone or download the repository.
2. Navigate to the project directory.
3. Run the game:
   ```bash
   python main.py
   ```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| **A - Z** | Type the matching falling letter to destroy it. |
| **UP Arrow** | Increase game speed manually (Speed Up). |
| **DOWN Arrow** | Decrease game speed manually (Slow Down). |
| **Mouse** | Select difficulty on the Start Screen. |
| **ESC / Quit** | Exit the game. |

---

## ⚙️ Game Structure & Code Overview

The game is built in a single `main.py` file for portability, organized into distinct classes and systems.

### 1. Core Systems

#### `SoundManager`
Handles all audio generation and playback.
- **Synthetic Audio**: Uses Python's `array` and `math` modules to generate wave data (Sine, Square, Noise) for sound effects, removing the need for external asset dependencies.
- **Functions**: `_generate_beep`, `_generate_slide`, `_generate_chord`, `_generate_noise`.

#### `ScreenShake`
Manages the "trauma" level of the screen to create shake effects.
- **Logic**: Decay-based trauma system where `shake_offset = trauma² * max_offset`.

### 2. Game Objects

#### `FallingLetter`
Represents a single enemy letter.
- **Attributes**: Character, position, speed, size scale, pulse state.
- **Update Logic**: Handles movement, danger line detection, and "pulse" animation when near the bottom.

#### `Particle` & `FloatingText`
Visual polish elements.
- **Particles**: Physics-based sparks with gravity and alpha fade-out.
- **FloatingText**: UI feedback numbers that float up and fade out (used for scores, speed changes).

#### `PowerUp`
Special items that fall alongside letters.
- **Types**: Slow Motion (Cyan), Bonus Time (Gold), Freeze (Purple).
- **Collision**: Auto-collected when they reach the player zone (bottom of screen).

### 3. Main Loop & States

#### `main()`
The central game loop handling:
- Event processing (Keyboard/Mouse).
- Game state updates (Movement, Spawning, Collision).
- Rendering (Drawing layers, UI, Effects).
- **Adaptive Difficulty Logic**: Monitors `recent_performance` window to adjust `speed_multiplier` and `spawn_rate`.

#### `show_start_screen()`
Interactive menu with animated background and difficulty selection (Easy/Medium/Hard).

#### `show_results_screen()`
End-game summary showing:
- Final Score with animated count-up.
- Detailed stats (Correct, Mistakes, Max Combo).
- Performance analysis (Most frequent mistake/miss).

---

## 🛠️ Customization

### Adding Custom Sounds
Place `.mp3` or `.wav` files in the `assets/` folder. The `SoundManager` will prioritize loading `correct.mp3` if found, otherwise it falls back to the synthetic generator.

### Adjusting Difficulty
Modify the `difficulty` presets in the `main()` function:
```python
if difficulty == "easy":
    speed_multiplier = 0.7
    spawn_rate = 80
```

---

## 📝 License
Free to use and modify for educational and personal projects.

Enjoy the game! 🚀
