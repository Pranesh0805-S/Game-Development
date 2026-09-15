from __future__ import annotations

from dataclasses import dataclass
import pygame

from entities import Gate, Hazard, Platform, Sentinel, Shard


@dataclass
class Level:
    name: str
    width: int
    spawn: tuple[int, int]
    platforms: list[Platform]
    shards: list[Shard]
    hazards: list[Hazard]
    sentinels: list[Sentinel]
    gate: Gate


def p(x, y, w, h, phase="both"): return Platform(pygame.Rect(x, y, w, h), phase)
def s(x, y, phase="both"): return Shard(pygame.Rect(x, y, 18, 24), phase)
def h(x, y, w, phase="both"): return Hazard(pygame.Rect(x, y, w, 20), phase)


def build_levels() -> list[Level]:
    return [
        Level("01 // Wake Line", 2200, (80, 470),
              [p(0, 530, 620, 70), p(710, 530, 420, 70), p(1230, 530, 970, 70), p(240, 420, 140, 20), p(480, 350, 130, 20), p(850, 410, 150, 20), p(1370, 400, 150, 20)],
              [s(275, 390), s(520, 320), s(890, 380), s(1410, 370)], [h(620, 510, 90)], [Sentinel(920, 500, 80)], Gate(pygame.Rect(2070, 450, 44, 80), 3)),
        Level("02 // Split Signal", 2600, (70, 470),
              [p(0, 530, 460, 70), p(1930, 530, 670, 70), p(260, 420, 120, 20), p(520, 450, 160, 20, "reality"), p(760, 370, 140, 20, "rift"), p(1010, 320, 150, 20, "reality"), p(1260, 400, 150, 20, "rift"), p(1500, 350, 190, 20, "both"), p(1740, 440, 120, 20, "reality")],
              [s(550, 415, "reality"), s(800, 335, "rift"), s(1050, 285, "reality"), s(1300, 365, "rift"), s(1550, 315)], [h(460, 510, 145), h(820, 510, 1090)], [Sentinel(1070, 290, 55, "reality"), Sentinel(1535, 320, 80, "rift")], Gate(pygame.Rect(2480, 450, 44, 80), 4)),
        Level("03 // Riftfall", 3000, (70, 470),
              [p(0, 530, 380, 70), p(2540, 530, 460, 70), p(250, 400, 110, 20), p(480, 430, 130, 20, "rift"), p(700, 350, 130, 20, "reality"), p(940, 280, 140, 20, "rift"), p(1190, 360, 140, 20, "reality"), p(1440, 420, 140, 20, "rift"), p(1710, 330, 160, 20, "both"), p(1980, 400, 160, 20, "reality"), p(2220, 350, 160, 20, "rift")],
              [s(285, 370), s(515, 395, "rift"), s(735, 315, "reality"), s(975, 245, "rift"), s(1230, 325, "reality"), s(1475, 385, "rift"), s(1750, 295), s(2260, 315, "rift")], [h(380, 510, 2140)], [Sentinel(735, 320, 70, "reality"), Sentinel(1460, 390, 70, "rift"), Sentinel(1750, 300, 90)], Gate(pygame.Rect(2900, 450, 44, 80), 6)),
    ]
