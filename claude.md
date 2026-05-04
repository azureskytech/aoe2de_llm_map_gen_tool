# AGENTS.md

## Project purpose

This repository is for generating Age of Empires II: Definitive Edition custom random maps programmatically, without using the in-game Scenario Editor UI.

The expected workflow is:

1. Take a natural-language map brief.
2. Convert the brief into a deterministic Python generator.
3. Run the generator to produce a `.rms` Random Map Script.
4. Copy or package the `.rms` into AoE2 DE.
5. Test the map in single-player skirmish and multiplayer lobbies.

This project currently targets `.rms` random maps, not binary `.aoe2scenario` files.

## Current repository layout

Current working layout:

```text
.
|-- AGENTS.md
|-- Map Scripts/
|   |-- generate_cross_forest_circle_8p.py
|   |-- generate_team_forest_trade_river_8p.py
|   `-- generate_team_forest_trade_river_clean_8p.py
`-- Generated Maps/
    |-- cross_forest_circle_8p.rms
    |-- team_forest_trade_river_8p_v12.rms
    |-- team_forest_trade_river_8p_v13.rms
    |-- team_forest_trade_river_8p_v14.rms
    `-- team_forest_trade_river_8p_v15.rms
```

- Files in `Map Scripts/` are source generators.
- Files in `Generated Maps/` are generated RMS output.
- Historical team forest trade river configs are stored as presets in `generate_team_forest_trade_river_clean_8p.py`, even if the generated `.rms` file for that preset is not currently present.
- Future map generators should use a matching source/output pair and should regenerate output from the Python source rather than hand-editing `.rms` files.

## Important Implementation Note

The current Python generators do not use an AoE2 Python package. They write RMS syntax directly as text.

Useful related library for scenario-style projects only:

- AoE2ScenarioParser: https://github.com/KSneijders/AoE2ScenarioParser

Use that library only when the project needs to generate or edit `.aoe2scenario` files. For `.rms` random map scripts, direct text generation is simpler, faster to inspect, and avoids adding a dependency that does not solve RMS terrain conflicts.

## Python/RMS Generator Knowledge

- Use small deterministic Python generators that emit RMS text directly. Prefer local helper functions for repeated `create_land` and `create_object` blocks over adding a Python dependency.
- For terrain-heavy maps, build an internal intended-terrain plan before writing RMS. The plan should fail generation if two different explicit terrain features claim the same planned cell, such as `WATER` and `GRASS`, or `WATER` and `SHALLOW`.
- Treat `base_terrain` as the default fallback, not as a later terrain layer. Do not emit separate forest fill passes when `base_terrain FOREST` already provides the forest.
- Do not rely on later RMS terrain stamps to overwrite earlier conflicting terrain. Split features before emission: river water should stop at the ford, the ford should be its own `SHALLOW` region, and grass paths should stop at the river banks.
- Same-terrain overlaps are acceptable when they intentionally reinforce a path or clearing. Different-terrain overlaps are not acceptable unless the generator explicitly models and validates the final priority, which this project should avoid by default.
- Use `resource_delta` inside `create_object` when a map needs non-standard per-object resource amounts. Example: if a `FORAGE` bush has the standard 125 food, `number_of_objects 5` with `resource_delta -5` gives 600 total food.
- Use `land_id` on deterministic `create_land` blocks plus `place_on_specific_land_id` on `create_object` blocks when a resource cluster must land in a specific clearing or pocket.
- For chop-through resource pockets, keep the clearing close to the resource footprint. For reliable 6-10 node ore pockets, emit one `create_object` block per mine with `place_on_specific_land_id` and `find_closest`.
- For mandatory trade paths on forest-base maps, reserve the path in the terrain plan and emit broad, low-count `GRASS` lands. Validate that the path does not cross water or shallow cells except at the intended ford.
- For ludicrous 480 variants, RMS land stamps are farther apart in actual tiles. If narrowing a mandatory route, reduce path stamp size modestly and lower the path step enough to keep the route continuous.
- A percentage-space terrain validator is not enough for ludicrous maps. Also validate map-size stamp coverage so repeated path, river, and shallow stamps cannot leave rows of base terrain between them.
- Once coverage is correct, optimize 480 maps by reducing stamp count with moderately larger stamps. Many small terrain stamps create lots of blend/layer work during terrain mesh generation; fewer larger stamps can preserve the same route while loading faster.
- For performance-biased variants like `team_forest_trade_river_8p_v13`, prefer a low `create_land` count even if the terrain stamps are somewhat larger. Keep the previous safer version available when visual precision matters more than startup time.
- Bounded `create_land` rectangles are valid RMS, but they changed the tested visual identity of `team_forest_trade_river`; do not use the v14 bounded-terrain approach as the baseline for this map. Use bounded rectangles only after explicit in-game visual validation.
- `team_forest_trade_river_8p_v12` is the current visual baseline for the team forest trade river map. `team_forest_trade_river_8p_v15` intentionally keeps the v12 stamp layout and object layout exactly the same, with only `enable_waves 0` changed to reduce 3D water effect rendering.
- `MainLog.txt` can reveal render-cost hotspots. For the v12-era ludicrous map logs, repeated `Rendering 3D water effect`, `Rendering blend tiles`, and `Generating blend texture layers` lines indicate water and terrain blending are the remaining cost centers, not Python generation time.
- AoE2 `MainLog.txt` may show only multiplayer/network errors even when the visible issue is bad RMS geometry. Do not infer RMS parser failure unless the log names the RMS file, map script, parser, terrain, or a loading exception.
- For sketched layouts, remember that AoE/isometric screenshots can make straight RMS north-south or east-west features look diagonal. If a map loads and has the right structure, preserve the coordinate model and tune widths first.
- Loading time is strongly affected by map size, total `create_land` count, dense 1-2 percent stamps, and broad `create_terrain` passes. Prefer fewer, larger stamps and default to `override_map_size 240` unless the user specifically needs ludicrous 480.
- Exact RMS behavior can still vary by AoE2 DE version and seed. Python compilation, validator checks, and text inspection validate the generator, not final in-game playability.

## Agent operating rules

When modifying this project:

1. Do not use the in-game editor as part of the implementation path.
2. Treat the Python file as the source of truth.
3. Regenerate the `.rms` after changing generation logic.
4. Do not hand-edit generated `.rms` output unless documenting an emergency patch.
5. Keep the generator deterministic by default.
6. Add CLI arguments for tunable parameters such as map size, player count, spawn radius, terrain density, river width, and resource density.
7. Preserve 8-player support unless the user explicitly requests another player count.
8. If a requested feature cannot be represented reliably in RMS, state that clearly and propose the closest RMS-safe approximation.
9. Do not claim the map is guaranteed to work until it has been tested inside AoE2 DE.
10. Prefer comments in the generated `.rms`; the output should be readable by modders.

## Map request format

When the user describes a desired map, extract or ask for the following details. If a detail is missing, choose a conservative default and document it in the generator.

```yaml
map_name: "human readable name"
players: 8
map_size: 240
spawn_pattern: "circle | grid | quadrants | mirrored_teams | random"
terrain_theme: "forest | desert | snow | grassland | swamp | mixed"
water: "none | river | lake | cross_river | islands | shallows"
water_crossings: "open | shallow_fords | blocked | transport_required"
resource_model: "standard | scarce | rich | custom"
ai_pve_priority: true
teams: "ffa | 2v2v2v2 | 4v4 | custom"
win_condition_assumptions: "standard random map conquest"
notes: "special landmarks, gimmicks, constraints, or balance goals"
```

Example map brief:

```yaml
map_name: "Cross Forest Circle"
players: 8
map_size: 240
spawn_pattern: "circle around center"
terrain_theme: "mostly forest with clear starting bases"
water: "north-south and east-west rivers through center"
water_crossings: "wide shallow fords near each quadrant border"
resource_model: "standard AoE2 starts plus neutral resources"
ai_pve_priority: true
teams: "ffa or 4v4"
```

## Build Commands

Run the simple cross-river example:

```bash
python "Map Scripts/generate_cross_forest_circle_8p.py"
```

Run the clean team forest trade river generator:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py"
```

Validate the clean generator without writing output:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --validate-only
```

Self-test the terrain conflict validator:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --self-test-validator
```

Choose an output path or tune geometry:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" \
  --output "Generated Maps/my_map.rms" \
  --map-size 240 \
  --river-half-width 6 \
  --ford-half-height 4 \
  --path-half-width 3 \
  --pocket-gold-nodes 6 \
  --pocket-stone-nodes 6
```

Generate the current ludicrous v15 team forest trade river variant:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --preset v15
```

List saved team forest trade river configs:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --list-presets
```

Regenerate an older known config:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --preset v12
```

Regenerate a historical config that predates map-size stamp coverage validation:

```bash
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --preset v10 --skip-coverage-validation
```

Basic Python validation:

```bash
python -m py_compile "Map Scripts/generate_team_forest_trade_river_clean_8p.py"
python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --validate-only
```

Basic output inspection:

```bash
rg -n "<PLAYER_SETUP>|<LAND_GENERATION>|<TERRAIN_GENERATION>|<OBJECTS_GENERATION>" "Generated Maps/team_forest_trade_river_8p_v15.rms"
rg -n "assign_to_player|place_on_specific_land_id|terrain_type WATER|terrain_type SHALLOW" "Generated Maps/team_forest_trade_river_8p_v15.rms"
```

Expected checks for generated team maps:

- Exactly 8 `assign_to_player` entries.
- A `<PLAYER_SETUP>` section with `direct_placement`.
- A `<LAND_GENERATION>` section with player lands, river lands, trade paths, ford, and resource pockets.
- A `<TERRAIN_GENERATION>` section with no extra forest fill when `base_terrain FOREST` is used.
- An `<OBJECTS_GENERATION>` section with starting TC, villagers, scout, herdables, berries, gold, stone, and hunt.
- A successful generator validation message reporting `0 terrain conflicts`. Stamp-based variants should also report `0 map-size stamp coverage gaps`; bounded-terrain variants should report that route stamps are not used.

## AoE2 DE loading instructions

### Direct install method

Copy the generated `.rms` file into the AoE2 DE random map scripts folder.

Common Steam path:

```text
<Steam install>\steamapps\common\AoE2DE\resources\_common\random-map-scripts
```

Alternative user profile path used by some installs/mod setups:

```text
C:\Users\<username>\Games\Age of Empires 2 DE\<profile_id>\resources\_common\random-map-scripts
```

Restart AoE2 DE after copying the file if the map does not appear.

### Local mod method

For cleaner development, package the `.rms` as a local mod:

```text
C:\Users\<username>\Games\Age of Empires 2 DE\<profile_id>\mods\local\<mod_name>\
└── resources\_common\random-map-scripts\<map_name>.rms
```

A minimal local mod may also contain an `info.json`:

```json
{
  "Author": "Your Name",
  "CacheStatus": 0,
  "Description": "Programmatically generated AoE2 DE RMS maps.",
  "Title": "Generated RMS Maps"
}
```

## How to play the generated map

### Single-player skirmish

1. Launch Age of Empires II: Definitive Edition.
2. Go to `Single Player` -> `Skirmish`.
3. Set game mode to `Random Map`.
4. Set map style to `Custom`.
5. Select the generated map name. It usually appears without the `.rms` extension.
6. Set the player count to 8 for this project template.
7. Add AI players.
8. Start the match.

### Multiplayer lobby

1. Launch Age of Empires II: Definitive Edition.
2. Go to `Multiplayer` -> `Create Lobby`.
3. Set game mode to `Random Map`.
4. Set map style to `Custom`.
5. Select the generated map name.
6. Set the lobby to the intended player count.
7. Make sure every player has the same `.rms` file installed, or publish/package it as a mod and have everyone subscribe.
8. Prefer a single selected custom map while testing. Avoid custom map pools until the map has been validated.

## RMS generation principles

### Prefer RMS for random maps

Use `.rms` when the user wants procedural maps, skirmish maps, multiplayer random maps, or replayable layouts.

Use `.aoe2scenario` only when the user wants a fixed handcrafted scenario, custom triggers, campaign-like objectives, or precise object placement that RMS cannot express reliably.

### Use deterministic structure for requested geometry

For geometric maps such as rings, quadrants, crosses, lanes, or mirrored bases:

- Compute coordinates in Python.
- Emit explicit `create_land` blocks where possible.
- Use `direct_placement` and `assign_to_player` for fixed player starts.
- Avoid placing starts directly on rivers, cliffs, dense forests, or map edges.
- Keep important generation constants at the top of the script or exposed as CLI arguments.

### Keep generated RMS readable

Generated `.rms` files should include comments for:

- Player setup.
- Main land generation.
- Special terrain features.
- Terrain fill.
- Starting objects.
- Neutral resources.
- Known limitations.

## AI/PVE playability principles

This section contains design heuristics. AI behavior can vary by AoE2 DE version, difficulty, civilization, map script, and game settings.

### 1. Do not hard-box AI players with trees

Avoid sealing a player into a tiny forest pocket. The AI should have clear walkable space around its Town Center and multiple exits from the base.

Recommended baseline:

- Keep a clear starting area of roughly 14-18 tiles around each Town Center.
- Keep forest clumps outside the immediate start zone.
- Use RMS constraints such as `set_avoid_player_start_areas`, `spacing_to_specific_terrain`, `avoid_forest_zone`, or explicit clear player lands.
- Do not require the AI to chop through a dense tree wall before it can scout, hunt, build, or attack.

For forest-heavy maps, give each player:

- Open TC space.
- Nearby but not blocking woodlines.
- At least two broad exits from the starting area.
- Enough space for houses, lumber camps, mills, mining camps, barracks, ranges, stables, blacksmith, market, monastery, siege workshop, castles, and farms.

### 2. Avoid fully isolating land AI behind water

If rivers divide the map, add wide shallow crossings or land bridges unless the map is intentionally a naval/transport map.

Recommended baseline:

- Use shallow crossings at predictable locations.
- Make each crossing at least 4-6 tiles wide.
- Put crossings away from the exact TC spawn so early units do not jam inside bases.
- Avoid one-tile bridges as the only path between quadrants.
- If a river splits the map into four quadrants, each quadrant should have at least two practical routes to the rest of the map.

For standard PVE, do not make transport ships mandatory unless the user explicitly requests an island/naval map.

### 3. Use standard random-map starting objects

Default AI scripts are easiest to support when the starting economy resembles standard Random Map openings.

Recommended baseline per player:

- 1 Town Center.
- 3 Villagers, or the game-mode-appropriate equivalent.
- 1 Scout Cavalry or civilization-appropriate scout.
- 4+ starting sheep/herdables.
- 6 forage bushes.
- 1 main gold group.
- 1 main stone group.
- 1-2 boars or equivalent hunt.
- Reasonable nearby woodlines.

Place starting objects on walkable terrain and avoid putting food or mines behind unwalkable terrain.

### 4. Use conservative resource distances

Avoid extreme resource placement. AI scripts are more reliable when early resources are near enough to find and gather without special scouting behavior.

Recommended baseline:

- Herdables: near TC, usually within 6-10 tiles.
- Berries: near TC, usually within 10-14 tiles.
- Main gold: usually within 14-22 tiles.
- Main stone: usually within 16-26 tiles.
- Boar/hunt: reachable without crossing water or chopping trees.
- Neutral gold/stone: away from starts but accessible by land routes.

Use `set_place_for_every_player` for per-player resources when possible.

### 5. Preserve pathability and building space

The AI needs room to expand and move armies.

Recommended baseline:

- Leave broad corridors through dense forest.
- Avoid excessive cliffs immediately around bases.
- Avoid placing the TC close to water, cliffs, forest, map edge, or unbuildable terrain.
- Keep farms possible around the Town Center and mills.
- Keep enough open terrain for military production buildings.
- Avoid mazes, single-tile chokepoints, and decorative clutter near bases.

### 6. Keep threats understandable

Standard AI does not reason about custom gimmicks as a human would.

Avoid, unless explicitly requested:

- Starting inside sealed arenas with no gates or exits.
- Resources that require deleting trees, using transports, or solving trigger puzzles.
- Relics or victory objects as the only viable win path.
- Extremely narrow bridges that cause unit jams.
- Aggressive Gaia units next to the starting TC.
- Nomad-style starts unless the map is deliberately designed for Nomad AI behavior.

### 7. Make symmetry and fairness explicit

For 8-player maps:

- Use circular, mirrored, or quadrant-aware spawn placement.
- Keep each player the same distance class from center features.
- Avoid placing some players on the wrong side of barriers while others have open access.
- Apply equivalent resource counts and distance ranges per player.
- When using fixed starts, rotate or mirror terrain/resource logic by player position.

### 8. Test with AI, not only visual inspection

Recommended test matrix:

- 1 human observer or resigned human slot plus 7 AI players.
- FFA test.
- 4v4 team test.
- At least three generated seeds if randomness is present.
- Revealed-map inspection for blocked starts, unreachable resources, and disconnected quadrants.
- Let the match run long enough for Feudal and Castle Age transitions.

Pass criteria:

- Each AI gathers sheep/berries/wood early.
- Each AI can build houses and production buildings.
- Each AI can reach gold and stone.
- Each AI can scout outside its base.
- Armies can path between players without requiring transports, unless explicitly designed as a naval map.
- No AI is trapped in a quadrant without a crossing.
- No starting TC is placed on water, forest, cliffs, or map edge.

## Specific Guidance For Forest River Maps

For maps like `team_forest_trade_river_clean_8p`:

1. Keep players inland from the river and map edge.
2. Use open player clearings for TCs, villagers, farms, and starting resources.
3. Use `base_terrain FOREST` for the surrounding forest instead of adding a later forest terrain pass.
4. Reserve trade lanes and center access paths in the terrain plan before emitting RMS.
5. Split the river into water segments around the ford instead of stamping water through the ford.
6. Emit the ford as its own `SHALLOW` region and keep grass approaches out of the river cells.
7. Place chop-through ore pockets on `land_id` clearings and place ore nodes one at a time with `find_closest`.
8. Keep the generated file compact. If a map becomes slow to load, first reduce map size, stamp density, or unnecessary terrain/object blocks.
9. Use `--validate-only` before generating output, and use `--self-test-validator` after changing the validator.

## References

- Forgotten Empires RMS Features: https://www.forgottenempires.net/age-of-empires-ii-definitive-edition/rms-features
- Definitive Random Map Scripting Guide discussion: https://forums.ageofempires.com/t/definitive-random-map-scripting-guide/104902
- AoE2ScenarioParser repository: https://github.com/KSneijders/AoE2ScenarioParser
- AoE2ScenarioParser documentation: https://ksneijders.github.io/AoE2ScenarioParser/
- AoE2ScenarioParser PyPI: https://pypi.org/project/AoE2ScenarioParser/
- AoE2 RMS Racket DSL documentation: https://docs.racket-lang.org/aoe2-rms/
- AoE2 DE UGC/local mod guide: https://ugc.aoe2.rocks/mods/
- Steam community RMS install path note: https://steamcommunity.com/app/813780/discussions/0/1639802081896923044/
- AoE2 RMS with LLM assistance example repository: https://github.com/kroffske/aoe2-rms-with-llm
