from __future__ import annotations

from dataclasses import dataclass
import pygame

from config import (COYOTE_TIME, FRICTION, GRAVITY, JUMP_BUFFER, JUMP_SPEED,
                    MAX_ENERGY, MAX_INTEGRITY, PLAYER_SIZE, RUN_ACCELERATION, RUN_SPEED)


@dataclass
class Platform:
    rect: pygame.Rect
    phase: str = "both"

    def active(self, phase: str) -> bool:
        return self.phase in ("both", phase)


@dataclass
class Shard:
    rect: pygame.Rect
    phase: str = "both"
    collected: bool = False

    def active(self, phase: str) -> bool:
        return not self.collected and self.phase in ("both", phase)


@dataclass
class Hazard:
    rect: pygame.Rect
    phase: str = "both"

    def active(self, phase: str) -> bool:
        return self.phase in ("both", phase)


@dataclass
class Gate:
    rect: pygame.Rect
    required_shards: int


class Sentinel:
    def __init__(self, x: int, y: int, patrol: int, phase: str = "both", speed: float = 95.0):
        self.rect = pygame.Rect(x, y, 32, 30)
        self.origin_x = x
        self.patrol = patrol
        self.phase = phase
        self.speed = speed
        self.direction = 1

    def active(self, phase: str) -> bool:
        return self.phase in ("both", phase)

    def update(self, dt: float) -> None:
        self.rect.x += round(self.speed * self.direction * dt)
        if abs(self.rect.x - self.origin_x) >= self.patrol:
            self.direction *= -1
            self.rect.x = max(self.origin_x - self.patrol, min(self.rect.x, self.origin_x + self.patrol))


class Player:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, *PLAYER_SIZE)
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2()
        self.on_ground = False
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.integrity = MAX_INTEGRITY
        self.energy = MAX_ENERGY
        self.facing = 1
        self.invulnerable = 0.0
        self.checkpoint = pygame.Vector2(x, y)

    def queue_jump(self) -> None:
        self.jump_buffer = JUMP_BUFFER

    def respawn(self) -> bool:
        self.integrity -= 1
        if self.integrity <= 0:
            return False
        self.position = self.checkpoint.copy()
        self.rect.topleft = self.position
        self.velocity.update(0, 0)
        self.invulnerable = 1.1
        return True

    def update(self, dt: float, left: bool, right: bool, jump_held: bool, platforms: list[Platform]) -> None:
        self.jump_buffer = max(0.0, self.jump_buffer - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        direction = int(right) - int(left)
        if direction:
            self.velocity.x += direction * RUN_ACCELERATION * dt
            self.velocity.x = max(-RUN_SPEED, min(RUN_SPEED, self.velocity.x))
            self.facing = direction
        else:
            drag = FRICTION * dt
            self.velocity.x = max(0, self.velocity.x - drag) if self.velocity.x > 0 else min(0, self.velocity.x + drag)

        if self.on_ground:
            self.coyote = COYOTE_TIME
        else:
            self.coyote = max(0.0, self.coyote - dt)
        if self.jump_buffer and self.coyote:
            self.velocity.y = -JUMP_SPEED
            self.jump_buffer = self.coyote = 0.0
            self.on_ground = False
        if not jump_held and self.velocity.y < -230:
            self.velocity.y += GRAVITY * 1.4 * dt

        self.velocity.y = min(self.velocity.y + GRAVITY * dt, 900)
        self.position.x += self.velocity.x * dt
        self.rect.x = round(self.position.x)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = platform.rect.right
                self.position.x = self.rect.x
                self.velocity.x = 0

        self.position.y += self.velocity.y * dt
        self.rect.y = round(self.position.y)
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = platform.rect.bottom
                self.position.y = self.rect.y
                self.velocity.y = 0
