#!/usr/bin/env python3
"""
Generate an Age of Empires II: Definitive Edition random map script (.rms)
for an 8-player forest map with:

- player spawn lands arranged in a circle around the center
- one north-south river through the center
- one east-west river through the center
- mostly forest terrain, with player clearings

Output:
    cross_forest_circle_8p.rms

Usage:
    python generate_cross_forest_circle_8p.py
    python generate_cross_forest_circle_8p.py --output my_map.rms
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path


DEFAULT_OUTPUT = "cross_forest_circle_8p.rms"


def pct(value: float) -> int:
    """Clamp and round a coordinate into AoE2 RMS land_position percentage space."""
    return max(1, min(99, int(round(value))))


def circle_positions(
    players: int = 8,
    center: float = 50.0,
    radius: float = 32.0,
    start_angle_degrees: float = -112.5,
) -> list[tuple[int, int]]:
    """
    Return land_position coordinates in percentage space.

    The default angle offset avoids placing any player directly on x=50 or y=50,
    so the river cross does not cut through a starting town.
    """
    positions: list[tuple[int, int]] = []
    for i in range(players):
        angle = math.radians(start_angle_degrees + i * (360.0 / players))
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        positions.append((pct(x), pct(y)))
    return positions


def create_land_block(
    terrain: str,
    x: int,
    y: int,
    *,
    base_size: int,
    number_of_tiles: int,
    border_fuzziness: int = 1,
    extra_lines: list[str] | None = None,
) -> str:
    lines = [
        "create_land",
        "{",
        f"  terrain_type {terrain}",
        f"  land_position {x} {y}",
        f"  base_size {base_size}",
        f"  number_of_tiles {number_of_tiles}",
        f"  border_fuzziness {border_fuzziness}",
    ]
    if extra_lines:
        lines.extend(f"  {line}" for line in extra_lines)
    lines.append("}")
    return "\n".join(lines)


def river_stamp_positions(step: int = 5) -> list[int]:
    """Positions from edge to edge, in percentage coordinates."""
    values = list(range(0, 101, step))
    if values[-1] != 100:
        values.append(100)
    return [pct(v) for v in values]


def generate_rms(
    *,
    players: int = 8,
    map_size: int = 240,
    spawn_radius_percent: float = 32.0,
    player_land_base_size: int = 13,
    player_land_tiles: int = 900,
    river_base_size: int = 5,
    river_stamp_tiles: int = 260,
    river_step_percent: int = 5,
) -> str:
    if players != 8:
        raise ValueError("This map template is designed for exactly 8 players.")

    spawn_positions = circle_positions(
        players=players,
        radius=spawn_radius_percent,
    )

    lines: list[str] = []

    lines.append("/*")
    lines.append("  Cross Forest Circle - generated RMS")
    lines.append("  8 players, circular fixed starts, forest terrain, cross-shaped rivers.")
    lines.append("*/")
    lines.append("")

    lines.append("<PLAYER_SETUP>")
    lines.append("direct_placement")
    lines.append("behavior_version 1")
    lines.append(f"override_map_size {map_size}")
    lines.append("")

    lines.append("<LAND_GENERATION>")
    lines.append("base_terrain GRASS")
    lines.append("enable_waves 1")
    lines.append("")

    lines.append("/* North-south river: repeated water lands along x=50. */")
    for y in river_stamp_positions(river_step_percent):
        lines.append(
            create_land_block(
                "WATER",
                50,
                y,
                base_size=river_base_size,
                number_of_tiles=river_stamp_tiles,
                border_fuzziness=1,
                extra_lines=["zone 90"],
            )
        )
        lines.append("")

    lines.append("/* East-west river: repeated water lands along y=50. */")
    for x in river_stamp_positions(river_step_percent):
        # The center stamp already exists from the vertical river, but repeating it is harmless.
        lines.append(
            create_land_block(
                "WATER",
                x,
                50,
                base_size=river_base_size,
                number_of_tiles=river_stamp_tiles,
                border_fuzziness=1,
                extra_lines=["zone 91"],
            )
        )
        lines.append("")

    lines.append("/* Player lands: two starts per quadrant, arranged in a ring around the center. */")
    for player_id, (x, y) in enumerate(spawn_positions, start=1):
        lines.append(
            create_land_block(
                "GRASS",
                x,
                y,
                base_size=player_land_base_size,
                number_of_tiles=player_land_tiles,
                border_fuzziness=2,
                extra_lines=[
                    f"assign_to_player {player_id}",
                    f"zone {player_id}",
                    "other_zone_avoidance_distance 4",
                ],
            )
        )
        lines.append("")

    lines.append("<TERRAIN_GENERATION>")
    lines.append("/* Fill remaining grass with forest while keeping starts and rivers open. */")
    lines.append("create_terrain FOREST")
    lines.append("{")
    lines.append("  base_terrain GRASS")
    lines.append("  land_percent 100")
    lines.append("  number_of_clumps 999")
    lines.append("  set_avoid_player_start_areas 16")
    lines.append("  spacing_to_specific_terrain WATER 2")
    lines.append("}")
    lines.append("")

    lines.append("<OBJECTS_GENERATION>")
    lines.append("/* Standard starting town. */")
    lines.append("create_object TOWN_CENTER")
    lines.append("{")
    lines.append("  set_place_for_every_player")
    lines.append("  min_distance_to_players 0")
    lines.append("  max_distance_to_players 0")
    lines.append("}")
    lines.append("")

    lines.append("create_object VILLAGER")
    lines.append("{")
    lines.append("  set_place_for_every_player")
    lines.append("  min_distance_to_players 6")
    lines.append("  max_distance_to_players 7")
    lines.append("}")
    lines.append("")

    lines.append("create_object SCOUT")
    lines.append("{")
    lines.append("  set_place_for_every_player")
    lines.append("  min_distance_to_players 7")
    lines.append("  max_distance_to_players 9")
    lines.append("}")
    lines.append("")

    lines.append("/* Per-player resources placed on clear grass near starts. */")
    resource_blocks = [
        ("SHEEP", 4, 7, 10, "set_loose_grouping"),
        ("FORAGE", 6, 10, 14, "set_tight_grouping"),
        ("GOLD", 7, 15, 20, "set_tight_grouping"),
        ("STONE", 4, 18, 24, "set_tight_grouping"),
        ("BOAR", 2, 16, 23, "set_loose_grouping"),
    ]

    for obj, count, min_dist, max_dist, grouping in resource_blocks:
        lines.append(f"create_object {obj}")
        lines.append("{")
        lines.append(f"  number_of_objects {count}")
        lines.append("  set_place_for_every_player")
        lines.append("  set_gaia_object_only")
        lines.append(f"  {grouping}")
        lines.append("  terrain_to_place_on GRASS")
        lines.append(f"  min_distance_to_players {min_dist}")
        lines.append(f"  max_distance_to_players {max_dist}")
        lines.append("}")
        lines.append("")

    lines.append("/* Extra neutral gold and stone in the four quadrants, away from the river. */")
    for terrain_object, count, groups in [("GOLD", 5, 8), ("STONE", 4, 8)]:
        lines.append(f"create_object {terrain_object}")
        lines.append("{")
        lines.append(f"  number_of_objects {count}")
        lines.append(f"  number_of_groups {groups}")
        lines.append("  set_gaia_object_only")
        lines.append("  set_tight_grouping")
        lines.append("  terrain_to_place_on GRASS")
        lines.append("  min_distance_to_players 25")
        lines.append("  min_distance_to_map_edge 8")
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an AoE2 DE .rms custom map.")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output .rms path")
    parser.add_argument("--map-size", type=int, default=240, help="override_map_size value, 36..480")
    parser.add_argument("--spawn-radius", type=float, default=32.0, help="Spawn ring radius in RMS percentage space")
    parser.add_argument("--river-width", type=int, default=5, help="River stamp base_size in tiles")
    parser.add_argument("--river-tiles", type=int, default=260, help="Extra number_of_tiles per river stamp")
    args = parser.parse_args()

    if not 36 <= args.map_size <= 480:
        raise SystemExit("--map-size must be between 36 and 480")

    rms = generate_rms(
        map_size=args.map_size,
        spawn_radius_percent=args.spawn_radius,
        river_base_size=args.river_width,
        river_stamp_tiles=args.river_tiles,
    )

    output_path = Path(args.output)
    output_path.write_text(rms, encoding="utf-8")
    print(f"Wrote {output_path.resolve()}")


if __name__ == "__main__":
    main()
