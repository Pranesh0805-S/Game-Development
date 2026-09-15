# Mario folder → Rift Runner V2: upgrade record

## Product direction

The previous games were Mario-inspired platformer experiments. V2 replaces them with **Rift Runner**, an original sci-fi platformer in which a courier switches between two overlapping versions of a broken city. It keeps Python and Pygame, but changes the visual language, story, objective, and central gameplay loop.

## What was replaced

The old folder contained five standalone, single-file Pygame experiments: `Mario.py`, `MarioColor.py`, `Mario_Attractive.py`, `Mario_Attractive_Upgraded.py`, and `Mario_Attractive_Upgraded_Fixed.py`.

The last file was the strongest baseline: two levels, platform collision, enemies, coins, scroll camera, save/load, generated effects, menus, mute, rebinding, and difficulty. Its limitations were duplicated code, global mutable state, only two short levels, frame-based movement, static layouts, and no original core mechanic. The original versions were deleted at the owner's request. They remain recoverable from Git history.

## Upgrade matrix

| Previous feature | V2 upgrade | Reason and uniqueness | Implementation / files |
| --- | --- | --- | --- |
| Standard left/right/jump | Acceleration, friction, coyote time, jump buffering, variable jump height | Makes the game feel responsive rather than rigid | `entities.py`: `Player` physics |
| One world of static platforms | Reality/Rift platform layers | The player solves routes by changing world state; this is the defining original mechanic | `levels.py`, `game.py` |
| Coins only raise a score | Rift Shards restore shift energy | Exploration directly powers traversal decisions | `entities.py`, `levels.py`, `game.py` |
| Simple patrol enemies | Phase-aware Sentinel drones and static anomaly fields | Encounters become timing and positioning puzzles | `entities.py`, `levels.py` |
| Flag ends a level | Rift Gate opens only after enough shards are recovered | Creates an explicit level objective and reward loop | `entities.py`, `game.py` |
| Two short levels | Three authored onboarding levels: movement, phase routes, combined hazards | Teaches the mechanic progressively | `levels.py` |
| Instant death / reset | Three integrity points, checkpoints, invulnerability window | Improves fairness without removing pressure | `entities.py`, `game.py` |
| Flat visual background | Phase-specific neon palette, skyline parallax, glow, phase pulse | Gives the game its own visual identity without copied assets | `game.py` |
| One large script / globals | Small modular package with focused responsibilities | Easier to improve, test, and explain on a portfolio | all `RiftRunnerV2/*.py` |
| Save at an arbitrary working path | JSON progress/settings in a V2-owned data folder | Avoids files appearing in unrelated folders | `persistence.py` |
| Temporary settings | Persistent volume and progress foundations | Gives the player a proper return experience | `persistence.py`, `game.py` |

## Architecture

```text
main.py → Game (loop, scenes, drawing, input)
              ├── levels.py (authored data and level factory)
              ├── entities.py (player, platforms, shards, hazards, sentinels, gate)
              └── persistence.py (local settings and level progress)
```

`Game` owns the current level and state (`menu`, `play`, `pause`, `complete`). Level data never reads the keyboard or draws the screen. Entities own collision-relevant state; the renderer in `game.py` decides how that state is displayed. This separation means later additions—sprite art, more levels, accessibility settings, or boss encounters—do not require rewriting the entire game.

## Files affected

| File | Purpose |
| --- | --- |
| `Mario/README.md` | Launch instructions and controls |
| `Mario/MARIO_V2_UPGRADE_PLAN.md` | This complete upgrade record |
| `Mario/RiftRunnerV2/main.py` | Stable game entry point |
| `Mario/RiftRunnerV2/config.py` | Tunable gameplay and display constants |
| `Mario/RiftRunnerV2/entities.py` | Gameplay entities and responsive physics |
| `Mario/RiftRunnerV2/levels.py` | Three data-driven levels |
| `Mario/RiftRunnerV2/persistence.py` | Local settings/progress storage |
| `Mario/RiftRunnerV2/game.py` | Game states, input, collision orchestration, HUD, and rendering |
| `Mario/RiftRunnerV2/requirements.txt` | Runtime dependency |
