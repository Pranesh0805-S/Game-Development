from __future__ import annotations

import math
import pygame

from config import COLORS, FPS, HEIGHT, MAX_ENERGY, REALITY, RIFT, SHIFT_COOLDOWN, SHIFT_COST, TITLE, WIDTH
from entities import Player
from levels import Level, build_levels
from persistence import load, save


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.title_font = pygame.font.SysFont("consolas", 46, bold=True)
        self.levels = build_levels()
        self.data = load()
        self.scene = "menu"
        self.selection = 0
        self.level_index = 0
        self.phase = REALITY
        self.phase_flash = 0.0
        self.shift_cooldown = 0.0
        self.camera_x = 0.0
        self.message = ""
        self.load_level(0)

    def load_level(self, index: int) -> None:
        self.level_index = index
        self.level: Level = self.levels[index]
        self.player = Player(*self.level.spawn)
        self.phase, self.camera_x, self.shift_cooldown = REALITY, 0.0, 0.0

    def active_platforms(self):
        return [platform for platform in self.level.platforms if platform.active(self.phase)]

    def shift(self) -> None:
        if self.shift_cooldown > 0:
            return
        if self.player.energy < SHIFT_COST:
            self.message = "INSUFFICIENT RIFT ENERGY"
            return
        self.player.energy -= SHIFT_COST
        self.phase = RIFT if self.phase == REALITY else REALITY
        self.shift_cooldown = SHIFT_COOLDOWN
        self.phase_flash = 0.22
        self.message = "RIFT SHIFT"

    def hurt(self) -> None:
        if self.player.invulnerable > 0:
            return
        if not self.player.respawn():
            self.load_level(self.level_index)
            self.message = "SIGNAL LOST // LEVEL RESTARTED"
        else:
            self.message = "INTEGRITY DAMAGED"

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.shift_cooldown = max(0.0, self.shift_cooldown - dt)
        self.phase_flash = max(0.0, self.phase_flash - dt)
        self.player.update(dt, keys[pygame.K_a] or keys[pygame.K_LEFT], keys[pygame.K_d] or keys[pygame.K_RIGHT], keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP], self.active_platforms())
        for sentinel in self.level.sentinels:
            sentinel.update(dt)
        for shard in self.level.shards:
            if shard.active(self.phase) and self.player.rect.colliderect(shard.rect):
                shard.collected = True
                self.player.energy = min(MAX_ENERGY, self.player.energy + 22)
                self.message = "RIFT SHARD RECOVERED"
        for hazard in self.level.hazards:
            if hazard.active(self.phase) and self.player.rect.colliderect(hazard.rect):
                self.hurt()
        for sentinel in self.level.sentinels:
            if sentinel.active(self.phase) and self.player.rect.colliderect(sentinel.rect):
                self.hurt()
        if self.player.rect.top > HEIGHT + 120:
            self.hurt()
        collected = sum(shard.collected for shard in self.level.shards)
        if self.player.rect.colliderect(self.level.gate.rect):
            if collected >= self.level.gate.required_shards:
                self.complete_level()
            else:
                self.message = f"GATE NEEDS {self.level.gate.required_shards - collected} MORE SHARDS"
        target = max(0, min(self.player.rect.centerx - WIDTH * 0.38, self.level.width - WIDTH))
        self.camera_x += (target - self.camera_x) * min(1, dt * 6)

    def complete_level(self) -> None:
        next_level = self.level_index + 1
        self.data["unlocked"] = max(self.data.get("unlocked", 1), min(len(self.levels), next_level + 1))
        save(self.data)
        if next_level >= len(self.levels):
            self.scene, self.message = "complete", "THE CITY REMEMBERS YOUR SIGNAL"
        else:
            self.load_level(next_level)
            self.message = "RIFT GATE STABILIZED"

    def draw_background(self) -> None:
        palette = COLORS[self.phase]
        self.screen.fill(palette["sky"])
        for layer, color, speed in ((0, palette["far"], 0.16), (1, palette["near"], 0.32)):
            offset = int(self.camera_x * speed) % 150
            for x in range(-150, WIDTH + 150, 150):
                height = 85 + ((x // 50 + layer * 31) % 5) * 28
                pygame.draw.rect(self.screen, color, (x - offset, HEIGHT - 100 - height, 95, height))
        pygame.draw.line(self.screen, palette["accent"], (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)

    def draw_world(self) -> None:
        palette = COLORS[self.phase]
        self.draw_background()
        for platform in self.level.platforms:
            r = platform.rect.move(-int(self.camera_x), 0)
            if platform.active(self.phase):
                pygame.draw.rect(self.screen, palette["platform"], r, border_radius=5)
                pygame.draw.rect(self.screen, palette["accent"], r, 2, border_radius=5)
            else:
                pygame.draw.rect(self.screen, (55, 49, 70), r, 1, border_radius=5)
        for hazard in self.level.hazards:
            if hazard.active(self.phase):
                r = hazard.rect.move(-int(self.camera_x), 0)
                for x in range(r.left, r.right, 16):
                    pygame.draw.polygon(self.screen, (255, 77, 123), [(x, r.bottom), (x + 8, r.top), (x + 16, r.bottom)])
        for shard in self.level.shards:
            if shard.active(self.phase):
                r = shard.rect.move(-int(self.camera_x), 0)
                pygame.draw.polygon(self.screen, palette["accent"], [(r.centerx, r.top), (r.right, r.centery), (r.centerx, r.bottom), (r.left, r.centery)])
        for sentinel in self.level.sentinels:
            if sentinel.active(self.phase):
                r = sentinel.rect.move(-int(self.camera_x), 0)
                pygame.draw.rect(self.screen, (255, 92, 122), r, border_radius=8)
                pygame.draw.circle(self.screen, (255, 235, 239), (r.centerx + sentinel.direction * 7, r.centery - 4), 4)
        gate = self.level.gate.rect.move(-int(self.camera_x), 0)
        open_gate = sum(shard.collected for shard in self.level.shards) >= self.level.gate.required_shards
        pygame.draw.rect(self.screen, palette["accent"] if open_gate else (100, 100, 120), gate, 3, border_radius=8)
        pygame.draw.circle(self.screen, palette["accent"] if open_gate else (100, 100, 120), gate.center, 12, 2)
        player = self.player.rect.move(-int(self.camera_x), 0)
        if self.player.invulnerable <= 0 or int(self.player.invulnerable * 12) % 2 == 0:
            pygame.draw.rect(self.screen, (232, 247, 255), player, border_radius=8)
            pygame.draw.rect(self.screen, palette["accent"], player, 2, border_radius=8)
            pygame.draw.circle(self.screen, (15, 26, 54), (player.centerx + self.player.facing * 7, player.y + 14), 3)
        if self.phase_flash:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((*palette["accent"], int(80 * self.phase_flash / .22)))
            self.screen.blit(overlay, (0, 0))

    def text(self, value: str, pos: tuple[int, int], color=(235, 240, 255), center=False, big=False) -> None:
        surface = (self.title_font if big else self.font).render(value, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.screen.blit(surface, rect)

    def draw_hud(self) -> None:
        collected = sum(shard.collected for shard in self.level.shards)
        self.text(self.level.name, (24, 18))
        self.text(f"PHASE: {self.phase.upper()}", (24, 46), COLORS[self.phase]["accent"])
        self.text(f"SHARDS {collected}/{self.level.gate.required_shards}", (24, 74))
        self.text("INTEGRITY " + "◆" * self.player.integrity, (WIDTH - 210, 18), (255, 127, 153))
        pygame.draw.rect(self.screen, (35, 40, 57), (WIDTH - 210, 50, 180, 16), border_radius=6)
        pygame.draw.rect(self.screen, COLORS[self.phase]["accent"], (WIDTH - 210, 50, int(180 * self.player.energy / MAX_ENERGY), 16), border_radius=6)
        self.text("RIFT ENERGY", (WIDTH - 210, 73), (185, 190, 210))
        if self.message:
            self.text(self.message, (WIDTH // 2, HEIGHT - 38), COLORS[self.phase]["accent"], center=True)

    def draw_menu(self) -> None:
        self.draw_background()
        self.text("RIFT RUNNER", (WIDTH // 2, 145), COLORS[REALITY]["accent"], center=True, big=True)
        self.text("A courier's route through a city split in two.", (WIDTH // 2, 205), center=True)
        options = ["START FROM WAKE LINE", "QUIT"]
        for index, option in enumerate(options):
            color = COLORS[RIFT]["accent"] if index == self.selection else (235, 240, 255)
            self.text(("> " if index == self.selection else "  ") + option, (WIDTH // 2, 300 + index * 52), color, center=True)
        self.text("UP/DOWN + ENTER", (WIDTH // 2, 470), (180, 190, 210), center=True)

    def draw_pause_or_complete(self, complete=False) -> None:
        self.draw_world()
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        self.screen.blit(shade, (0, 0))
        self.text("SIGNAL COMPLETE" if complete else "PAUSED", (WIDTH // 2, 245), COLORS[RIFT]["accent"], center=True, big=True)
        self.text(self.message if complete else "ESC to resume  •  R to restart  •  M for menu", (WIDTH // 2, 320), center=True)

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.message = "" if self.scene == "play" else self.message
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.scene == "menu":
                        if event.key in (pygame.K_UP, pygame.K_DOWN): self.selection = 1 - self.selection
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.selection: running = False
                            else: self.scene = "play"
                    elif self.scene == "play":
                        if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP): self.player.queue_jump()
                        elif event.key == pygame.K_LSHIFT: self.shift()
                        elif event.key == pygame.K_ESCAPE: self.scene = "pause"
                        elif event.key == pygame.K_r: self.load_level(self.level_index)
                    elif self.scene == "pause":
                        if event.key == pygame.K_ESCAPE: self.scene = "play"
                        elif event.key == pygame.K_r: self.load_level(self.level_index); self.scene = "play"
                        elif event.key == pygame.K_m: self.scene = "menu"
                    elif self.scene == "complete" and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self.scene = "menu"
            if self.scene == "play": self.update(dt); self.draw_world(); self.draw_hud()
            elif self.scene == "menu": self.draw_menu()
            else: self.draw_pause_or_complete(self.scene == "complete")
            pygame.display.flip()
        pygame.quit()
