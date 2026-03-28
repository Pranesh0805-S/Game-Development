"""
Attractive 2D Platformer (Pygame) — Menu + Sounds + Figure Sprites + Coins + Enemies
------------------------------------------------------------------------------------
Controls:
  A / D  : Move left/right
  SPACE  : Jump
  R      : Restart level
  ESC    : Pause -> Menu
  M      : Mute/Unmute SFX

Menu:
  Start Game, Continue Game, Quit
  Button clicks play sounds

Gameplay SFX:
  Jump, Coin pickup, Enemy hit, Button click

This file is self‑contained: it generates simple WAV sound effects on first run.
Requires: pygame (pip install pygame)
"""

import os
import sys
import json
import math
import random
import wave
import struct
from dataclasses import dataclass, field

import pygame

# -----------------------------
# Config
# -----------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
FPS = 60
GRAVITY = 0.6
PLAYER_SPEED = 4.2
JUMP_SPEED = -11.5
SAVE_PATH = "savegame.json"

ASSET_DIR = os.path.join(os.path.dirname(__file__) if '__file__' in globals() else '.', "assets", "sfx")
os.makedirs(ASSET_DIR, exist_ok=True)

SFX_FILES = {
    "ui": os.path.join(ASSET_DIR, "ui_click.wav"),
    "jump": os.path.join(ASSET_DIR, "jump.wav"),
    "coin": os.path.join(ASSET_DIR, "coin.wav"),
    "hit": os.path.join(ASSET_DIR, "hit.wav"),
}

# -----------------------------
# Utility: generate tiny WAVs
# -----------------------------
def generate_tone_wav(path, freq=440.0, duration_ms=120, volume=0.35, sample_rate=44100, shape="sine", slide_to=None):
    if os.path.exists(path):
        return
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            # simple pitch slide if requested
            f = freq
            if slide_to is not None:
                f = freq + (slide_to - freq) * (i / max(1, n_samples - 1))
            if shape == "square":
                val = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
            elif shape == "saw":
                val = 2.0 * (t * f - math.floor(0.5 + t * f))
            else:
                val = math.sin(2 * math.pi * f * t)
            # quick decay envelope
            env = 1.0 - (i / n_samples)
            sample = int(max(-1, min(1, val * env * volume)) * 32767)
            wf.writeframesraw(struct.pack("<h", sample))
        wf.writeframes(b"")

# Generate sfx (only once)
generate_tone_wav(SFX_FILES["ui"], freq=740, duration_ms=90, shape="square")
generate_tone_wav(SFX_FILES["jump"], freq=520, duration_ms=140, shape="sine", slide_to=420)
generate_tone_wav(SFX_FILES["coin"], freq=1200, duration_ms=170, shape="sine", slide_to=1600)
generate_tone_wav(SFX_FILES["hit"], freq=220, duration_ms=220, shape="saw")

# -----------------------------
# Data structures
# -----------------------------
@dataclass
class RectObj:
    rect: pygame.Rect
    color: tuple

@dataclass
class Coin:
    x: float
    y: float
    radius: int = 10
    taken: bool = False
    spin: float = 0.0

    def update(self, dt):
        self.spin += dt * 6.0

    def draw(self, surf, camera_x):
        if self.taken: return
        cx = int(self.x - camera_x)
        cy = int(self.y)
        # spin shimmer: ellipse width oscillates
        w = self.radius + int(4 * abs(math.sin(self.spin)))
        h = self.radius
        pygame.draw.ellipse(surf, (248, 220, 70), pygame.Rect(cx - w//2, cy - h//2, w, h))
        pygame.draw.ellipse(surf, (255, 255, 200), pygame.Rect(cx - w//4, cy - h//4, w//2, h//2), 2)

    def collide(self, player_rect):
        if self.taken: return False
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2).colliderect(player_rect)

@dataclass
class Enemy:
    rect: pygame.Rect
    speed: float = 2.0
    patrol_range: int = 80
    base_x: int = 0
    dir: int = 1
    alive: bool = True
    anim: float = 0.0

    def update(self, dt):
        if not self.alive: return
        self.rect.x += int(self.speed * self.dir)
        if abs(self.rect.x - self.base_x) > self.patrol_range:
            self.dir *= -1
        self.anim += dt * 10

    def draw(self, surf, camera_x):
        if not self.alive: return
        x = self.rect.x - camera_x
        y = self.rect.y
        # Red "figure" enemy (simple robot-ish character)
        # body
        pygame.draw.rect(surf, (200, 40, 40), (x, y, self.rect.w, self.rect.h), border_radius=8)
        # head
        pygame.draw.rect(surf, (220, 60, 60), (x + self.rect.w//4, y - self.rect.h//2, self.rect.w//2, self.rect.h//2), border_radius=6)
        # eyes blinking
        eye_h = 6 if int(self.anim) % 20 < 18 else 2
        pygame.draw.rect(surf, (30,30,30), (x + self.rect.w//4 + 6, y - self.rect.h//2 + 10, 8, eye_h), border_radius=2)
        pygame.draw.rect(surf, (30,30,30), (x + self.rect.w//2 + 6, y - self.rect.h//2 + 10, 8, eye_h), border_radius=2)
        # arms swing
        arm_offset = int(4 * math.sin(self.anim * 0.5))
        pygame.draw.rect(surf, (180, 30, 30), (x-6, y+10+arm_offset, 6, self.rect.h//2), border_radius=3)
        pygame.draw.rect(surf, (180, 30, 30), (x+self.rect.w, y+10-arm_offset, 6, self.rect.h//2), border_radius=3)

@dataclass
class Player:
    rect: pygame.Rect
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    facing: int = 1    # 1 right, -1 left
    walk_anim: float = 0.0
    alive: bool = True
    coins: int = 0
    muted: bool = False

    def handle_input(self, keys):
        ax = 0.0
        if keys.get(KEY_BINDINGS["left"]): ax -= PLAYER_SPEED
        if keys.get(KEY_BINDINGS["right"]): ax += PLAYER_SPEED
        self.vx = ax
        if ax != 0: self.facing = 1 if ax > 0 else -1

    def jump(self, sfx_jump):
        if self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False
            if not self.muted and sfx_jump: sfx_jump.play()

    def update(self, platforms, enemies, coins, dt, sfx_coin, sfx_hit):
        # gravity
        self.vy += GRAVITY

        # horizontal
        self.rect.x += int(self.vx)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left = p.rect.right

        # vertical
        self.rect.y += int(self.vy)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

        # coins
        for c in coins:
            c.update(dt)
            if c.collide(self.rect):
                c.taken = True
                self.coins += 1
                if not self.muted and sfx_coin: sfx_coin.play()

        # enemies
        for e in enemies:
            e.update(dt)
            if e.alive and self.rect.colliderect(e.rect):
                # stomp if falling
                if self.vy > 2 and self.rect.bottom - e.rect.top < 20:
                    e.alive = False
                    self.vy = JUMP_SPEED * 0.7
                else:
                    # hit
                    self.alive = False
                    if not self.muted and sfx_hit: sfx_hit.play()

        # walking anim
        if abs(self.vx) > 0.1 and self.on_ground:
            self.walk_anim += dt * 12.0
        else:
            self.walk_anim = 0.0

    def draw(self, surf, camera_x):
        x = self.rect.x - camera_x
        y = self.rect.y
        # Person-like figure: head, body, limbs
        # body
        body_w, body_h = 26, 34
        head_r = 12
        # legs animate
        step = int(6 * math.sin(self.walk_anim)) if self.on_ground else 0
        # torso
        pygame.draw.rect(surf, (50, 120, 200), (x, y, body_w, body_h), border_radius=6)
        # head
        pygame.draw.circle(surf, (250, 220, 190), (x + body_w//2, y - head_r), head_r)
        # simple face
        eye_dx = 4 * self.facing
        pygame.draw.circle(surf, (30,30,30), (x + body_w//2 - 4 + eye_dx, y - head_r), 2)
        pygame.draw.circle(surf, (30,30,30), (x + body_w//2 + 4 + eye_dx, y - head_r), 2)
        # arms
        pygame.draw.rect(surf, (40, 100, 180), (x - 6, y + 6, 6, 18), border_radius=3)
        pygame.draw.rect(surf, (40, 100, 180), (x + body_w, y + 6, 6, 18), border_radius=3)
        # legs (animated)
        pygame.draw.rect(surf, (30, 80, 160), (x + 4, y + body_h - 6, 8, 16 + step), border_radius=3)
        pygame.draw.rect(surf, (30, 80, 160), (x + body_w - 12, y + body_h - 6, 8, 16 - step), border_radius=3)
        # shoes
        pygame.draw.rect(surf, (20,20,20), (x + 2, y + body_h + 10 + step, 12, 4), border_radius=2)
        pygame.draw.rect(surf, (20,20,20), (x + body_w - 14, y + body_h + 10 - step, 12, 4), border_radius=2)

# -----------------------------
# Level data
# -----------------------------
def make_level_1():
    platforms = []
    # ground
    platforms.append(RectObj(pygame.Rect(0, 540, 1600, 60), (50, 50, 60)))
    platforms.append(RectObj(pygame.Rect(1700, 540, 800, 60), (50,50,60)))
    # floating
    platforms += [
        RectObj(pygame.Rect(220, 460, 140, 20), (70, 70, 90)),
        RectObj(pygame.Rect(420, 400, 120, 20), (70, 70, 90)),
        RectObj(pygame.Rect(620, 360, 120, 20), (70, 70, 90)),
        RectObj(pygame.Rect(900, 480, 160, 20), (70, 70, 90)),
        RectObj(pygame.Rect(1200, 430, 140, 20), (70, 70, 90)),
    ]
    enemies = [
        Enemy(pygame.Rect(680, 320, 34, 34), speed=1.6, patrol_range=60, base_x=680),
        Enemy(pygame.Rect(1280, 390, 34, 34), speed=2.2, patrol_range=90, base_x=1280),
    ]
    coins = [Coin(240, 420), Coin(460, 360), Coin(640, 320), Coin(940, 440), Coin(1240, 390)]
    start_x, start_y = 60, 480
    end_rect = pygame.Rect(1550, 480, 40, 60)
    return platforms, enemies, coins, start_x, start_y, end_rect, "Level 1"

def make_level_2():
    platforms = []
    platforms.append(RectObj(pygame.Rect(0, 540, 2000, 60), (50, 50, 60)))
    platforms += [
        RectObj(pygame.Rect(200, 460, 120, 20), (60, 60, 80)),
        RectObj(pygame.Rect(380, 420, 120, 20), (60, 60, 80)),
        RectObj(pygame.Rect(560, 380, 120, 20), (60, 60, 80)),
        RectObj(pygame.Rect(740, 340, 160, 20), (60, 60, 80)),
        RectObj(pygame.Rect(980, 300, 160, 20), (60, 60, 80)),
        RectObj(pygame.Rect(1240, 340, 160, 20), (60, 60, 80)),
    ]
    enemies = [
        Enemy(pygame.Rect(760, 300, 34, 34), speed=2.2, patrol_range=100, base_x=760),
        Enemy(pygame.Rect(1000, 260, 34, 34), speed=2.6, patrol_range=120, base_x=1000),
        Enemy(pygame.Rect(1260, 300, 34, 34), speed=2.2, patrol_range=90, base_x=1260),
    ]
    coins = [Coin(220, 420), Coin(400, 380), Coin(580, 340), Coin(820, 300), Coin(1060, 260), Coin(1300, 300)]
    start_x, start_y = 40, 480
    end_rect = pygame.Rect(1880, 480, 40, 60)
    return platforms, enemies, coins, start_x, start_y, end_rect, "Level 2"

LEVEL_BUILDERS = [make_level_1, make_level_2]

# -----------------------------
# Menu / Buttons
# -----------------------------
class Button:
    def __init__(self, text, center, w=260, h=50):
        self.text = text
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = center
        self.hover = False

    def draw(self, surf, font):
        color = (60, 160, 240) if self.hover else (40, 120, 200)
        pygame.draw.rect(surf, color, self.rect, border_radius=14)
        pygame.draw.rect(surf, (255,255,255), self.rect, 3, border_radius=14)
        txt = font.render(self.text, True, (255,255,255))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def check(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# -----------------------------
# Save / Load
# -----------------------------
def save_game(level_index, player):
    data = {"level": level_index, "x": player.rect.x, "y": player.rect.y, "coins": player.coins}
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f)

def load_game():
    if not os.path.exists(SAVE_PATH): return None
    try:
        with open(SAVE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None

# -----------------------------
# Main Game
# -----------------------------
def main():
    pygame.init()
    pygame.display.set_caption("Attractive Platformer")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # audio
    mixer_ok = True
    try:
        pygame.mixer.pre_init(44100, -16, 1, 256)
        pygame.mixer.init()
    except Exception:
        mixer_ok = False

    sfx_ui = pygame.mixer.Sound(SFX_FILES["ui"]) if mixer_ok else None
    sfx_jump = pygame.mixer.Sound(SFX_FILES["jump"]) if mixer_ok else None
    sfx_coin = pygame.mixer.Sound(SFX_FILES["coin"]) if mixer_ok else None
    sfx_hit = pygame.mixer.Sound(SFX_FILES["hit"]) if mixer_ok else None

    def play_ui():
        if mixer_ok and sfx_ui and not player.muted: sfx_ui.play()

    font_big = pygame.font.SysFont("arial", 48, bold=True)
    font = pygame.font.SysFont("arial", 24, bold=True)

    # state
    state = "menu"
    level_index = 0
    platforms, enemies, coins, sx, sy, end_rect, level_name = LEVEL_BUILDERS[level_index]()
    player = Player(pygame.Rect(sx, sy, 26, 50))

    camera_x = 0

    # buttons
    btn_start = Button("Start Game", (SCREEN_WIDTH//2, 260))
    btn_continue = Button("Continue Game", (SCREEN_WIDTH//2, 330))
    btn_settings = Button("Settings", (SCREEN_WIDTH//2, 400))
    btn_quit = Button("Quit", (SCREEN_WIDTH//2, 470))

    def reset_level(idx):
        nonlocal platforms, enemies, coins, sx, sy, end_rect, level_name, camera_x
        platforms, enemies, coins, sx, sy, end_rect, level_name = LEVEL_BUILDERS[idx]()
        player.rect.topleft = (sx, sy)
        player.vx = player.vy = 0
        player.alive = True
        camera_x = max(0, player.rect.centerx - SCREEN_WIDTH//2)

    running = True
    while running:
        dt = clock.tick(FPS) / 60.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if state == "game":
                    if event.key == KEY_BINDINGS['jump']:
                        player.jump(sfx_jump)
                    elif event.key == pygame.K_r:
                        reset_level(level_index)
                    elif event.key == pygame.K_ESCAPE:
                        save_game(level_index, player)
                        state = "menu"
                    elif event.key == pygame.K_m:
                        player.muted = not player.muted
                elif state == "menu":
                    if event.key == pygame.K_m:
                        player.muted = not player.muted

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu":
                    pos = pygame.mouse.get_pos()
                    # Start
                    if btn_start.clicked(pos):
                        difficulty_menu(screen, font, font_big, sfx_ui, player)
                        play_ui()
                        level_index = 0
                        reset_level(level_index)
                        state = "game"
                    # Continue
                    elif btn_continue.clicked(pos):
                        saved = load_game()
                        if saved:
                            play_ui()
                            level_index = max(0, min(saved.get("level", 0), len(LEVEL_BUILDERS)-1))
                            reset_level(level_index)
                            player.rect.x = int(saved.get("x", player.rect.x))
                            player.rect.y = int(saved.get("y", player.rect.y))
                            player.coins = int(saved.get("coins", 0))
                            state = "game"
                        else:
                            # no save -> little "thud"
                            if mixer_ok and not player.muted:
                                sfx_hit.play()
                    elif btn_settings.clicked(pos):
                        play_ui()
                        settings_menu(screen, font, font_big, sfx_ui, player)
                    elif btn_quit.clicked(pos):
                        play_ui()
                        running = False

        if state == "menu":
            screen.fill((20, 24, 36))
            mx, my = pygame.mouse.get_pos()
            for b in (btn_start, btn_continue, btn_settings, btn_quit):
                b.check((mx, my))

            title = font_big.render("Attractive Platformer", True, (255,255,255))
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 150)))

            # Disable "Continue" if no save
            if not os.path.exists(SAVE_PATH):
                pygame.draw.rect(screen, (80,80,80), btn_continue.rect, border_radius=14)
                pygame.draw.rect(screen, (200,200,200), btn_continue.rect, 3, border_radius=14)
                txt = font.render("Continue Game (no save)", True, (200,200,200))
                screen.blit(txt, txt.get_rect(center=btn_continue.rect.center))
            else:
                btn_continue.draw(screen, font)

            btn_start.draw(screen, font)
            btn_quit.draw(screen, font)

            hint = font.render("Press M to mute/unmute SFX", True, (200,200,220))
            screen.blit(hint, (20, SCREEN_HEIGHT - 40))

        elif state == "game":
            keys = pygame.key.get_pressed()
            player.handle_input(keys)
            player.update([*platforms], enemies, coins, dt, sfx_coin, sfx_hit)

            # camera follows player
            camera_x = max(0, min(player.rect.centerx - SCREEN_WIDTH//2, 2000))

            # background gradient
            screen.fill((135, 200, 255))
            sky = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for i in range(SCREEN_HEIGHT):
                c = 255 - int(100 * (i / SCREEN_HEIGHT))
                sky.fill((135, 200, c), pygame.Rect(0, i, SCREEN_WIDTH, 1))
            screen.blit(sky, (0,0))

            # ground / platforms
            for p in platforms:
                r = pygame.Rect(p.rect.x - camera_x, p.rect.y, p.rect.w, p.rect.h)
                pygame.draw.rect(screen, p.color, r, border_radius=6)

            # coins & enemies draw
            for c in coins:
                c.draw(screen, camera_x)
            for e in enemies:
                e.draw(screen, camera_x)

            # end flag
            pygame.draw.rect(screen, (30,30,30), (end_rect.x - camera_x, end_rect.y - 60, 6, 60))
            pygame.draw.polygon(screen, (255, 90, 90),
                                [(end_rect.x - camera_x + 6, end_rect.y - 60),
                                 (end_rect.x - camera_x + 60, end_rect.y - 45),
                                 (end_rect.x - camera_x + 6, end_rect.y - 30)])

            # player
            player.draw(screen, camera_x)

            # HUD
            hud = font.render(f"{level_name}   Coins: {player.coins}   M: {'Muted' if player.muted else 'Sound ON'}", True, (20,20,30))
            pygame.draw.rect(screen, (255,255,255), (10, 10, hud.get_width()+20, 36), border_radius=10)
            screen.blit(hud, (20, 15))

            # win / next level
            if player.rect.colliderect(end_rect):
                level_index += 1
                if level_index >= len(LEVEL_BUILDERS):
                    # back to menu after simple win display
                    save_game(0, player)  # reset save to level 0
                    # win screen flash
                    screen.fill((255, 240, 180))
                    win = font_big.render("You Win!", True, (30,30,30))
                    screen.blit(win, win.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
                    pygame.display.flip()
                    pygame.time.delay(1200)
                    state = "menu"
                    level_index = 0
                    reset_level(level_index)
                else:
                    reset_level(level_index)

            # death
            if not player.alive:
                # small death pause
                pygame.display.flip()
                pygame.time.delay(500)
                reset_level(level_index)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

# -----------------------------
# Global controls & difficulty
# -----------------------------
KEY_BINDINGS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "jump": pygame.K_SPACE,
}
DIFFICULTY = "Medium"  # default


def difficulty_settings():
    global PLAYER_SPEED, JUMP_SPEED
    if DIFFICULTY == "Easy":
        PLAYER_SPEED = 4.5
        JUMP_SPEED = -12
    elif DIFFICULTY == "Hard":
        PLAYER_SPEED = 3.6
        JUMP_SPEED = -10.5
    else:  # Medium
        PLAYER_SPEED = 4.2
        JUMP_SPEED = -11.5


# -----------------------------
# Settings Menu
# -----------------------------
def settings_menu(screen, font, font_big, sfx_ui, player):
    selecting = True
    rebinding = None
    while selecting:
        screen.fill((30, 36, 50))
        title = font_big.render("Settings", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))

        y = 200
        for action, key in KEY_BINDINGS.items():
            label = f"{action.capitalize()} : {pygame.key.name(key)}"
            col = (255,200,200) if rebinding == action else (255,255,255)
            txt = font.render(label, True, col)
            rect = txt.get_rect(center=(SCREEN_WIDTH//2, y))
            screen.blit(txt, rect)
            y += 50

        hint = font.render("Click action to rebind key. Press ESC to return.", True, (200,200,220))
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-60)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if rebinding:
                    KEY_BINDINGS[rebinding] = event.key
                    rebinding = None
                    if sfx_ui and not player.muted: sfx_ui.play()
                elif event.key == pygame.K_ESCAPE:
                    selecting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # detect click on action text
                y = 200
                for action, key in KEY_BINDINGS.items():
                    rect = pygame.Rect(SCREEN_WIDTH//2 - 120, y-20, 240, 40)
                    if rect.collidepoint(event.pos):
                        rebinding = action
                        break
                    y += 50


# -----------------------------
# Difficulty Menu
# -----------------------------
def difficulty_menu(screen, font, font_big, sfx_ui, player):
    global DIFFICULTY
    choices = ["Easy", "Medium", "Hard"]
    selected = 1
    choosing = True
    while choosing:
        screen.fill((36, 24, 30))
        title = font_big.render("Select Difficulty", True, (255,255,255))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 150)))

        for i, ch in enumerate(choices):
            col = (255,255,100) if i == selected else (220,220,220)
            txt = font.render(ch, True, col)
            screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, 250 + i*60)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(choices)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(choices)
                elif event.key == pygame.K_RETURN:
                    DIFFICULTY = choices[selected]
                    difficulty_settings()
                    if sfx_ui and not player.muted: sfx_ui.play()
                    choosing = False
