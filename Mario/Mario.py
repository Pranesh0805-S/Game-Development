"""
Mario-like platformer with Start Menu and Two Levels (Black & White)
Controls: A (left), D (right), Spacebar (jump), R (restart), ESC (quit)
"""

import pygame
import sys
from dataclasses import dataclass

# -----------------------------
# Configuration
# -----------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
FPS = 60
GRAVITY = 0.6
PLAYER_SPEED = 4.0
PLAYER_JUMP_SPEED = -12

# Colors - black & white only
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

pygame.init()
font = pygame.font.SysFont(None, 36)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mini Mario-like Platformer (B&W)")
clock = pygame.time.Clock()

# -----------------------------
# Helper classes
# -----------------------------

@dataclass
class RectObject:
    rect: pygame.Rect
    color: tuple

class Player:
    def __init__(self, x, y, w=32, h=48):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.alive = True
        self.score = 0

    def apply_gravity(self):
        self.vel_y += GRAVITY
        if self.vel_y > 15:
            self.vel_y = 15

    def move(self, platforms):
        self.rect.x += int(self.vel_x)
        self._horiz_collisions(platforms)
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self._vert_collisions(platforms)

    def _horiz_collisions(self, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right
                self.vel_x = 0

    def _vert_collisions(self, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                self.vel_y = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = PLAYER_JUMP_SPEED
            self.on_ground = False

    def draw(self, surface, camera_x):
        r = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, BLACK, r)
        eye = pygame.Rect(r.x + r.w - 10, r.y + 10, 6, 6)
        pygame.draw.rect(surface, WHITE, eye)

class Platform(RectObject):
    def __init__(self, x, y, w, h, color=BLACK, moving=False, move_range=0, speed=0):
        super().__init__(pygame.Rect(x, y, w, h), color)
        self.moving = moving
        self.start_x = x
        self.move_range = move_range
        self.speed = speed

    def update(self):
        if self.moving and self.move_range > 0:
            self.rect.x += self.speed
            if self.rect.x < self.start_x - self.move_range or self.rect.x > self.start_x + self.move_range:
                self.speed *= -1

class Enemy(RectObject):
    def __init__(self, x, y, w=32, h=32, patrol_range=100, speed=1.5):
        super().__init__(pygame.Rect(x, y, w, h), BLACK)
        self.start_x = x
        self.patrol_range = patrol_range
        self.speed = speed

    def update(self):
        self.rect.x += self.speed
        if self.rect.x < self.start_x - self.patrol_range or self.rect.x > self.start_x + self.patrol_range:
            self.speed *= -1

class Coin(RectObject):
    def __init__(self, x, y, r=8):
        super().__init__(pygame.Rect(x - r, y - r, r * 2, r * 2), BLACK)
        self.radius = r

    def draw(self, surface, camera_x):
        center = (self.rect.centerx - camera_x, self.rect.centery)
        pygame.draw.circle(surface, BLACK, center, self.radius)

# -----------------------------
# Levels
# -----------------------------

def create_level():
    platforms, enemies, coins = [], [], []
    platforms.append(Platform(0, 540, 4000, 60))
    platforms.append(Platform(200, 440, 120, 20))
    platforms.append(Platform(380, 360, 120, 20))
    platforms.append(Platform(580, 300, 160, 20))
    platforms.append(Platform(820, 380, 120, 20))
    platforms.append(Platform(1000, 320, 120, 20))
    platforms.append(Platform(1250, 420, 120, 20, moving=True, move_range=140, speed=2))
    platforms.append(Platform(1500, 260, 160, 20))
    platforms.append(Platform(1750, 380, 120, 20))
    coin_positions = [(230, 400), (420, 320), (640, 260), (860, 340), (1020, 280), (1280, 380), (1520, 220), (1780, 340)]
    for cx, cy in coin_positions:
        coins.append(Coin(cx, cy))
    enemies.append(Enemy(700, 508, patrol_range=120, speed=1.2))
    enemies.append(Enemy(1600, 508, patrol_range=180, speed=1.0))
    flag = pygame.Rect(1950, 480, 20, 60)
    return platforms, enemies, coins, flag

def create_level2():
    platforms, enemies, coins = [], [], []
    platforms.append(Platform(0, 540, 4000, 60))
    platforms.append(Platform(150, 440, 100, 20))
    platforms.append(Platform(300, 380, 100, 20))
    platforms.append(Platform(450, 320, 100, 20))
    platforms.append(Platform(600, 260, 100, 20, moving=True, move_range=100, speed=2))
    platforms.append(Platform(800, 200, 100, 20))
    platforms.append(Platform(1000, 300, 150, 20, moving=True, move_range=150, speed=3))
    platforms.append(Platform(1300, 400, 150, 20))
    platforms.append(Platform(1500, 350, 150, 20))
    platforms.append(Platform(1700, 300, 150, 20))
    coin_positions = [(180, 400), (330, 340), (480, 280), (620, 220), (850, 160),
                      (1050, 260), (1330, 360), (1530, 310), (1730, 260)]
    for cx, cy in coin_positions:
        coins.append(Coin(cx, cy))
    enemies.append(Enemy(500, 508, patrol_range=150, speed=1.5))
    enemies.append(Enemy(1200, 508, patrol_range=200, speed=1.2))
    enemies.append(Enemy(1600, 508, patrol_range=180, speed=1.4))
    flag = pygame.Rect(1950, 480, 20, 60)
    return platforms, enemies, coins, flag

# -----------------------------
# HUD
# -----------------------------

def draw_hud(surface, player, win=False):
    score_surf = font.render(f"Score: {player.score}", True, BLACK)
    surface.blit(score_surf, (16, 16))
    if not player.alive:
        msg = font.render("You died! Press R to restart", True, BLACK)
        surface.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
    if win:
        msg = font.render("You finished all levels! Press ESC to quit", True, BLACK)
        surface.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

# -----------------------------
# Menu
# -----------------------------

def menu(last_unlocked=1):
    selected = 0
    options = ["Start Game", "Continue Game", "Quit"]
    while True:
        screen.fill(WHITE)
        title = font.render("Mini Mario-like Platformer (B&W)", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        for i, opt in enumerate(options):
            color = BLACK if i != selected else WHITE
            bg_color = WHITE if i != selected else BLACK
            opt_surf = font.render(opt, True, color)
            rect = opt_surf.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 50))
            pygame.draw.rect(screen, bg_color, rect.inflate(20, 10))
            screen.blit(opt_surf, rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "Start Game":
                        return 1
                    elif options[selected] == "Continue Game":
                        return last_unlocked
                    elif options[selected] == "Quit":
                        pygame.quit(); sys.exit()

# -----------------------------
# Game loop
# -----------------------------

def play_game(start_level=1):
    current_level = start_level
    last_unlocked = start_level
    platforms, enemies, coins, flag = create_level() if current_level == 1 else create_level2()
    player = Player(50, 450)
    camera_x = 0
    win_level = False
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_r:
                    platforms, enemies, coins, flag = (create_level() if current_level == 1 else create_level2())
                    player = Player(50, 450); camera_x = 0; win_level = False
                if event.key == pygame.K_SPACE and player.alive and not win_level:
                    player.jump()
        keys = pygame.key.get_pressed()
        if player.alive and not win_level:
            player.vel_x = 0
            if keys[pygame.K_a]: player.vel_x = -PLAYER_SPEED
            if keys[pygame.K_d]: player.vel_x = PLAYER_SPEED
            player.apply_gravity()
            for p in platforms: p.update()
            player.move(platforms)

            # FIXED coin collection logic
            remaining_coins = []
            for c in coins:
                if player.rect.colliderect(c.rect):
                    player.score += 10
                else:
                    remaining_coins.append(c)
            coins = remaining_coins

            for e in enemies:
                e.update()
                if player.rect.colliderect(e.rect): player.alive = False

            if player.rect.colliderect(flag):
                if current_level == 1:
                    current_level = 2; last_unlocked = 2
                    platforms, enemies, coins, flag = create_level2()
                    player = Player(50, 450); camera_x = 0; win_level = False
                else:
                    win_level = True

        camera_x = max(0, player.rect.centerx - SCREEN_WIDTH // 3)
        screen.fill(WHITE)
        for p in platforms:
            pygame.draw.rect(screen, p.color, p.rect.move(-camera_x, 0))
        for c in coins: c.draw(screen, camera_x)
        for e in enemies:
            pygame.draw.rect(screen, e.color, e.rect.move(-camera_x, 0))
        pygame.draw.rect(screen, BLACK, flag.move(-camera_x, 0))
        player.draw(screen, camera_x)
        draw_hud(screen, player, win=win_level)
        pygame.display.flip()
    return last_unlocked

# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":
    last_unlocked_level = 1
    while True:
        choice = menu(last_unlocked=last_unlocked_level)
        last_unlocked_level = play_game(choice)
