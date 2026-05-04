#!/usr/bin/env python3
"""
Generate a clean, validated AoE2 DE RMS map for an 8-player forest
turtling team game.

This generator intentionally keeps the RMS simple:

- base terrain is FOREST
- explicit GRASS lands carve starts, trade paths, center access paths, and ore pockets
- explicit WATER lands create the team-separating river
- explicit SHALLOW lands create the only river crossing

Before writing RMS, the generator validates an internal 101x101 percentage-space
terrain plan and a map-size-aware stamp coverage model. Any explicit terrain
conflict, such as WATER and GRASS claiming the same intended cell, fails
generation. Any repeated stamp spacing that can leave base FOREST rows on a
480 map also fails generation.

Output:
    Generated Maps/team_forest_trade_river_8p_v15.rms

Usage:
    python "Map Scripts/generate_team_forest_trade_river_clean_8p.py"
    python "Map Scripts/generate_team_forest_trade_river_clean_8p.py" --validate-only
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path


MAP_NAME = "Team Forest Trade River Clean"
DEFAULT_PRESET = "v16"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "Generated Maps"
    / "team_forest_trade_river_8p_v16.rms"
)

VERSION_PRESETS: dict[str, dict[str, int]] = {
    "v9": {
        "map_size": 240,
        "enable_waves": 1,
        "bounded_terrain": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 3,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 5,
        "path_step": 5,
        "shallow_step": 4,
        "river_base_size": 8,
        "river_tiles": 520,
        "path_base_size": 7,
        "path_tiles": 420,
        "shallow_base_size": 6,
        "shallow_tiles": 260,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v10": {
        "map_size": 480,
        "enable_waves": 1,
        "bounded_terrain": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 5,
        "path_step": 4,
        "shallow_step": 4,
        "river_base_size": 8,
        "river_tiles": 520,
        "path_base_size": 6,
        "path_tiles": 360,
        "shallow_base_size": 6,
        "shallow_tiles": 260,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v11": {
        "map_size": 480,
        "enable_waves": 1,
        "bounded_terrain": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 3,
        "path_step": 2,
        "shallow_step": 2,
        "river_base_size": 8,
        "river_tiles": 520,
        "path_base_size": 5,
        "path_tiles": 360,
        "shallow_base_size": 5,
        "shallow_tiles": 360,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v12": {
        "map_size": 480,
        "enable_waves": 1,
        "bounded_terrain": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 4,
        "path_step": 4,
        "shallow_step": 3,
        "river_base_size": 8,
        "river_tiles": 850,
        "path_base_size": 5,
        "path_tiles": 850,
        "shallow_base_size": 5,
        "shallow_tiles": 550,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v13": {
        "map_size": 480,
        "enable_waves": 1,
        "bounded_terrain": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 5,
        "path_step": 6,
        "shallow_step": 5,
        "river_base_size": 10,
        "river_tiles": 1300,
        "path_base_size": 6,
        "path_tiles": 1800,
        "shallow_base_size": 7,
        "shallow_tiles": 1700,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v14": {
        "map_size": 480,
        "enable_waves": 0,
        "bounded_terrain": 1,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 5,
        "path_step": 6,
        "shallow_step": 5,
        "river_base_size": 10,
        "river_tiles": 1300,
        "path_base_size": 6,
        "path_tiles": 1800,
        "shallow_base_size": 7,
        "shallow_tiles": 1700,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    "v15": {
        "map_size": 480,
        "enable_waves": 0,
        "bounded_terrain": 0,
        "bounded_water": 0,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 4,
        "path_step": 4,
        "shallow_step": 3,
        "river_base_size": 8,
        "river_tiles": 850,
        "path_base_size": 5,
        "path_tiles": 850,
        "shallow_base_size": 5,
        "shallow_tiles": 550,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
    # v16: bounded WATER river (2 blocks instead of 22 stamps), wider path stamps,
    # team_positions support, fish/birds/relics.
    "v16": {
        "map_size": 480,
        "enable_waves": 0,
        "bounded_terrain": 0,
        "bounded_water": 1,
        "team_lane_x": 24,
        "river_half_width": 6,
        "ford_half_height": 4,
        "path_half_width": 2,
        "start_clear_radius": 8,
        "pocket_radius": 4,
        "water_step": 4,
        "path_step": 6,
        "shallow_step": 3,
        "river_base_size": 8,
        "river_tiles": 850,
        "path_base_size": 6,
        "path_tiles": 2000,
        "shallow_base_size": 5,
        "shallow_tiles": 550,
        "start_base_size": 16,
        "start_tiles": 1500,
        "pocket_base_size": 8,
        "pocket_tiles": 360,
        "pocket_gold_nodes": 6,
        "pocket_stone_nodes": 6,
    },
}


def default_output_for_preset(preset: str) -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "Generated Maps"
        / f"team_forest_trade_river_8p_{preset}.rms"
    )


def print_presets() -> None:
    for name, config in VERSION_PRESETS.items():
        values = ", ".join(f"{key}={value}" for key, value in config.items())
        print(f"{name}: {values}")


@dataclass(frozen=True)
class PlayerStart:
    player_id: int
    team: str
    x: int
    y: int


@dataclass(frozen=True)
class ResourcePocket:
    land_id: int
    team: str
    resource: str
    x: int
    y: int


@dataclass(frozen=True)
class TerrainConflict:
    x: int
    y: int
    first_terrain: str
    first_feature: str
    second_terrain: str
    second_feature: str


@dataclass(frozen=True)
class CoverageGap:
    feature: str
    first_pct: int
    second_pct: int
    gap_tiles: float
    max_safe_gap_tiles: float


class TerrainPlan:
    """Small percentage-space terrain validator for intended explicit lands."""

    def __init__(self) -> None:
        self.cells: dict[tuple[int, int], tuple[str, str]] = {}
        self.conflicts: list[TerrainConflict] = []

    def add_rect(self, *, name: str, terrain: str, x1: int, y1: int, x2: int, y2: int) -> None:
        for y in range(clamp_pct(y1), clamp_pct(y2) + 1):
            for x in range(clamp_pct(x1), clamp_pct(x2) + 1):
                self._claim(x, y, terrain, name)

    def add_circle(self, *, name: str, terrain: str, x: int, y: int, radius: int) -> None:
        cx = clamp_pct(x)
        cy = clamp_pct(y)
        radius_sq = radius * radius
        for yy in range(clamp_pct(cy - radius), clamp_pct(cy + radius) + 1):
            for xx in range(clamp_pct(cx - radius), clamp_pct(cx + radius) + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= radius_sq:
                    self._claim(xx, yy, terrain, name)

    def _claim(self, x: int, y: int, terrain: str, feature: str) -> None:
        existing = self.cells.get((x, y))
        if existing is None:
            self.cells[(x, y)] = (terrain, feature)
            return

        old_terrain, old_feature = existing
        if old_terrain != terrain:
            self.conflicts.append(
                TerrainConflict(x, y, old_terrain, old_feature, terrain, feature)
            )

    def require_no_conflicts(self) -> None:
        if not self.conflicts:
            return

        examples = "\n".join(
            "  "
            + f"{c.x},{c.y}: {c.first_feature}={c.first_terrain} vs "
            + f"{c.second_feature}={c.second_terrain}"
            for c in self.conflicts[:20]
        )
        extra = "" if len(self.conflicts) <= 20 else f"\n  ... {len(self.conflicts) - 20} more"
        raise ValueError(f"Terrain plan has {len(self.conflicts)} conflicts:\n{examples}{extra}")


def clamp_pct(value: int | float) -> int:
    return max(1, min(99, int(round(value))))


def clamp_border(value: int | float) -> int:
    return max(0, min(99, int(round(value))))


def stamps_between(start: int, end: int, step: int) -> list[int]:
    if start == end:
        return [clamp_pct(start)]

    direction = 1 if end > start else -1
    values = list(range(start, end + direction, direction * step))
    if values[-1] != end:
        values.append(end)

    result: list[int] = []
    for value in values:
        clamped = clamp_pct(value)
        if clamped not in result:
            result.append(clamped)
    return result


def pct_gap_to_tiles(first_pct: int, second_pct: int, map_size: int) -> float:
    return abs(second_pct - first_pct) * map_size / 100.0


def effective_stamp_radius_tiles(*, base_size: int, number_of_tiles: int) -> float:
    # create_land edges are fuzzy, so use a conservative share of the
    # area-equivalent radius when checking for rows of base terrain.
    area_radius = math.sqrt(number_of_tiles / math.pi)
    return max(float(base_size), area_radius * 0.78)


def require_axis_coverage(
    *,
    feature: str,
    positions: list[int],
    map_size: int,
    base_size: int,
    number_of_tiles: int,
) -> None:
    if len(positions) < 2:
        return

    radius = effective_stamp_radius_tiles(base_size=base_size, number_of_tiles=number_of_tiles)
    max_safe_gap = radius * 1.55
    gaps: list[CoverageGap] = []
    for first, second in zip(positions, positions[1:]):
        gap_tiles = pct_gap_to_tiles(first, second, map_size)
        if gap_tiles > max_safe_gap:
            gaps.append(CoverageGap(feature, first, second, gap_tiles, max_safe_gap))

    if not gaps:
        return

    examples = "\n".join(
        f"  {gap.feature}: {gap.first_pct}->{gap.second_pct} is "
        f"{gap.gap_tiles:.1f} tiles; safe max {gap.max_safe_gap_tiles:.1f}"
        for gap in gaps[:20]
    )
    extra = "" if len(gaps) <= 20 else f"\n  ... {len(gaps) - 20} more"
    raise ValueError(f"Stamp coverage has {len(gaps)} map-size gaps:\n{examples}{extra}")


def require_bridge_coverage(
    *,
    feature: str,
    first_pct: int,
    second_pct: int,
    map_size: int,
    first_base_size: int,
    first_tiles: int,
    second_base_size: int,
    second_tiles: int,
) -> None:
    first_radius = effective_stamp_radius_tiles(
        base_size=first_base_size,
        number_of_tiles=first_tiles,
    )
    second_radius = effective_stamp_radius_tiles(
        base_size=second_base_size,
        number_of_tiles=second_tiles,
    )
    max_safe_gap = (first_radius + second_radius) * 0.9
    gap_tiles = pct_gap_to_tiles(first_pct, second_pct, map_size)
    if gap_tiles > max_safe_gap:
        raise ValueError(
            "Stamp coverage bridge gap:\n"
            f"  {feature}: {first_pct}->{second_pct} is {gap_tiles:.1f} tiles; "
            f"safe max {max_safe_gap:.1f}"
        )


def player_starts(team_lane_x: int) -> list[PlayerStart]:
    west_x = clamp_pct(team_lane_x)
    east_x = clamp_pct(100 - team_lane_x)
    y_values = [14, 36, 64, 86]

    starts: list[PlayerStart] = []
    for player_id, y in enumerate(y_values, start=1):
        starts.append(PlayerStart(player_id, "west", west_x, y))
    for player_id, y in enumerate(y_values, start=5):
        starts.append(PlayerStart(player_id, "east", east_x, y_values[player_id - 5]))
    return starts


def resource_pockets() -> list[ResourcePocket]:
    """Two gold and two stone pockets per team, mirrored east/west."""
    west_gold = [(13, 24), (36, 76)]
    west_stone = [(36, 24), (13, 76)]
    pockets: list[ResourcePocket] = []
    next_land_id = 200

    def add(team: str, resource: str, coords: list[tuple[int, int]]) -> None:
        nonlocal next_land_id
        for x, y in coords:
            real_x = x if team == "west" else 100 - x
            pockets.append(ResourcePocket(next_land_id, team, resource, real_x, y))
            next_land_id += 1

    add("west", "GOLD", west_gold)
    add("west", "STONE", west_stone)
    add("east", "GOLD", west_gold)
    add("east", "STONE", west_stone)
    return pockets


def land_block(
    terrain: str,
    x: int,
    y: int,
    *,
    base_size: int,
    number_of_tiles: int,
    border_fuzziness: int = 1,
    land_id: int | None = None,
    circular: bool = False,
    extra_lines: list[str] | None = None,
) -> str:
    lines = [
        "create_land",
        "{",
        f"  terrain_type {terrain}",
        f"  land_position {clamp_pct(x)} {clamp_pct(y)}",
        f"  base_size {base_size}",
        f"  number_of_tiles {number_of_tiles}",
        f"  border_fuzziness {border_fuzziness}",
    ]
    if circular:
        lines.append("  set_circular_base")
    if land_id is not None:
        lines.append(f"  land_id {land_id}")
    if extra_lines:
        lines.extend(f"  {line}" for line in extra_lines)
    lines.append("}")
    return "\n".join(lines)


def bounded_land_block(
    terrain: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    *,
    land_id: int | None = None,
    border_fuzziness: int = 100,
    extra_lines: list[str] | None = None,
) -> str:
    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)
    lines = [
        "create_land",
        "{",
        f"  terrain_type {terrain}",
        f"  land_position {clamp_pct((left + right) / 2)} {clamp_pct((top + bottom) / 2)}",
        "  land_percent 100",
        f"  left_border {clamp_border(left)}",
        f"  right_border {clamp_border(100 - right)}",
        f"  top_border {clamp_border(top)}",
        f"  bottom_border {clamp_border(100 - bottom)}",
        f"  border_fuzziness {border_fuzziness}",
    ]
    if land_id is not None:
        lines.append(f"  land_id {land_id}")
    if extra_lines:
        lines.extend(f"  {line}" for line in extra_lines)
    lines.append("}")
    return "\n".join(lines)


def object_block(name: str, attributes: list[str]) -> str:
    lines = [f"create_object {name}", "{"]
    lines.extend(f"  {line}" for line in attributes)
    lines.append("}")
    return "\n".join(lines)


@dataclass(frozen=True)
class Geometry:
    team_lane_x: int = 24
    river_x1: int = 44
    river_x2: int = 56
    ford_y1: int = 46
    ford_y2: int = 54
    path_half_width: int = 3
    start_clear_radius: int = 8
    pocket_radius: int = 4

    @property
    def west_lane(self) -> int:
        return clamp_pct(self.team_lane_x)

    @property
    def east_lane(self) -> int:
        return clamp_pct(100 - self.team_lane_x)


def geometry_from_args(args: argparse.Namespace) -> Geometry:
    return Geometry(
        team_lane_x=args.team_lane_x,
        river_x1=50 - args.river_half_width,
        river_x2=50 + args.river_half_width,
        ford_y1=50 - args.ford_half_height,
        ford_y2=50 + args.ford_half_height,
        path_half_width=args.path_half_width,
        start_clear_radius=args.start_clear_radius,
        pocket_radius=args.pocket_radius,
    )


def self_test_validator() -> None:
    plan = TerrainPlan()
    plan.add_rect(name="test water", terrain="WATER", x1=49, y1=49, x2=51, y2=51)
    plan.add_rect(name="test grass", terrain="GRASS", x1=50, y1=50, x2=52, y2=52)
    try:
        plan.require_no_conflicts()
    except ValueError as exc:
        print("Validator self-test passed: deliberate terrain conflict was flagged.")
        print(str(exc).splitlines()[0])
        return
    raise SystemExit("Validator self-test failed: deliberate terrain conflict was not flagged.")


def build_plan(geometry: Geometry) -> TerrainPlan:
    plan = TerrainPlan()

    # River is split around the ford so WATER and SHALLOW never claim the same cells.
    plan.add_rect(
        name="north river water",
        terrain="WATER",
        x1=geometry.river_x1,
        y1=1,
        x2=geometry.river_x2,
        y2=geometry.ford_y1 - 1,
    )
    plan.add_rect(
        name="south river water",
        terrain="WATER",
        x1=geometry.river_x1,
        y1=geometry.ford_y2 + 1,
        x2=geometry.river_x2,
        y2=99,
    )
    plan.add_rect(
        name="central shallow ford",
        terrain="SHALLOW",
        x1=geometry.river_x1,
        y1=geometry.ford_y1,
        x2=geometry.river_x2,
        y2=geometry.ford_y2,
    )

    # Team trade lanes and center access paths. They stop at the ford banks.
    for lane_name, x in [("west trade", geometry.west_lane), ("east trade", geometry.east_lane)]:
        plan.add_rect(
            name=lane_name,
            terrain="GRASS",
            x1=x - geometry.path_half_width,
            y1=1,
            x2=x + geometry.path_half_width,
            y2=99,
        )

    plan.add_rect(
        name="west center access",
        terrain="GRASS",
        x1=geometry.west_lane - geometry.path_half_width,
        y1=geometry.ford_y1,
        x2=geometry.river_x1 - 1,
        y2=geometry.ford_y2,
    )
    plan.add_rect(
        name="east center access",
        terrain="GRASS",
        x1=geometry.river_x2 + 1,
        y1=geometry.ford_y1,
        x2=geometry.east_lane + geometry.path_half_width,
        y2=geometry.ford_y2,
    )

    for start in player_starts(geometry.team_lane_x):
        plan.add_circle(
            name=f"player {start.player_id} clearing",
            terrain="GRASS",
            x=start.x,
            y=start.y,
            radius=geometry.start_clear_radius,
        )

    for pocket in resource_pockets():
        plan.add_circle(
            name=f"{pocket.team} {pocket.resource.lower()} pocket {pocket.land_id}",
            terrain="GRASS",
            x=pocket.x,
            y=pocket.y,
            radius=geometry.pocket_radius,
        )

    return plan


def validate_stamp_coverage(
    *,
    geometry: Geometry,
    map_size: int,
    bounded_water: bool,
    water_step: int,
    path_step: int,
    shallow_step: int,
    river_base_size: int,
    river_tiles: int,
    path_base_size: int,
    path_tiles: int,
    shallow_base_size: int,
    shallow_tiles: int,
) -> None:
    """Validate that repeated RMS stamps are dense enough at the actual map size."""
    if not bounded_water:
        north_water = stamps_between(3, geometry.ford_y1 - 3, water_step)
        south_water = stamps_between(geometry.ford_y2 + 3, 97, water_step)
        for name, positions in [("north river water", north_water), ("south river water", south_water)]:
            require_axis_coverage(
                feature=name,
                positions=positions,
                map_size=map_size,
                base_size=river_base_size,
                number_of_tiles=river_tiles,
            )

    trade_y = stamps_between(1, 99, path_step)
    for name in ["west trade path", "east trade path"]:
        require_axis_coverage(
            feature=name,
            positions=trade_y,
            map_size=map_size,
            base_size=path_base_size,
            number_of_tiles=path_tiles,
        )

    west_access = stamps_between(geometry.west_lane, geometry.river_x1 - 1, path_step)
    east_access = stamps_between(geometry.river_x2 + 1, geometry.east_lane, path_step)
    for name, positions in [("west center access", west_access), ("east center access", east_access)]:
        require_axis_coverage(
            feature=name,
            positions=positions,
            map_size=map_size,
            base_size=path_base_size,
            number_of_tiles=path_tiles,
        )

    shallow_x = stamps_between(geometry.river_x1 + 1, geometry.river_x2 - 1, shallow_step)
    shallow_y = stamps_between(geometry.ford_y1, geometry.ford_y2, shallow_step)
    require_axis_coverage(
        feature="central shallow ford x coverage",
        positions=shallow_x,
        map_size=map_size,
        base_size=shallow_base_size,
        number_of_tiles=shallow_tiles,
    )
    require_axis_coverage(
        feature="central shallow ford y coverage",
        positions=shallow_y,
        map_size=map_size,
        base_size=shallow_base_size,
        number_of_tiles=shallow_tiles,
    )

    require_bridge_coverage(
        feature="west access to shallow ford",
        first_pct=west_access[-1],
        second_pct=shallow_x[0],
        map_size=map_size,
        first_base_size=path_base_size,
        first_tiles=path_tiles,
        second_base_size=shallow_base_size,
        second_tiles=shallow_tiles,
    )
    require_bridge_coverage(
        feature="east access to shallow ford",
        first_pct=shallow_x[-1],
        second_pct=east_access[0],
        map_size=map_size,
        first_base_size=shallow_base_size,
        first_tiles=shallow_tiles,
        second_base_size=path_base_size,
        second_tiles=path_tiles,
    )


def terrain_land_blocks(
    *,
    geometry: Geometry,
    bounded_terrain: bool,
    bounded_water: bool,
    water_step: int,
    path_step: int,
    shallow_step: int,
    river_base_size: int,
    river_tiles: int,
    path_base_size: int,
    path_tiles: int,
    shallow_base_size: int,
    shallow_tiles: int,
    start_base_size: int,
    start_tiles: int,
    pocket_base_size: int,
    pocket_tiles: int,
) -> list[str]:
    blocks: list[str] = []

    if bounded_terrain:
        # Bounded lands keep the minimap geometry simple and reduce expensive
        # blend work on ludicrous maps.
        blocks.extend(
            [
                bounded_land_block(
                    "WATER",
                    geometry.river_x1,
                    0,
                    geometry.river_x2,
                    geometry.ford_y1 - 1,
                    extra_lines=["zone 70"],
                ),
                bounded_land_block(
                    "WATER",
                    geometry.river_x1,
                    geometry.ford_y2 + 1,
                    geometry.river_x2,
                    100,
                    extra_lines=["zone 70"],
                ),
                bounded_land_block(
                    "GRASS",
                    geometry.west_lane - geometry.path_half_width,
                    0,
                    geometry.west_lane + geometry.path_half_width,
                    100,
                    extra_lines=["zone 80"],
                ),
                bounded_land_block(
                    "GRASS",
                    geometry.east_lane - geometry.path_half_width,
                    0,
                    geometry.east_lane + geometry.path_half_width,
                    100,
                    extra_lines=["zone 81"],
                ),
                bounded_land_block(
                    "GRASS",
                    geometry.west_lane - geometry.path_half_width,
                    geometry.ford_y1,
                    geometry.river_x1 - 1,
                    geometry.ford_y2,
                    extra_lines=["zone 82"],
                ),
                bounded_land_block(
                    "GRASS",
                    geometry.river_x2 + 1,
                    geometry.ford_y1,
                    geometry.east_lane + geometry.path_half_width,
                    geometry.ford_y2,
                    extra_lines=["zone 82"],
                ),
                bounded_land_block(
                    "SHALLOW",
                    geometry.river_x1,
                    geometry.ford_y1,
                    geometry.river_x2,
                    geometry.ford_y2,
                    extra_lines=["zone 71"],
                ),
            ]
        )
    else:
        if bounded_water:
            # Two bounded WATER blocks replace many stamps: eliminates blend-tile
            # generation cost for the most expensive terrain type on ludicrous maps.
            blocks.extend(
                [
                    bounded_land_block(
                        "WATER",
                        geometry.river_x1,
                        1,
                        geometry.river_x2,
                        geometry.ford_y1 - 1,
                        extra_lines=["zone 70"],
                    ),
                    bounded_land_block(
                        "WATER",
                        geometry.river_x1,
                        geometry.ford_y2 + 1,
                        geometry.river_x2,
                        99,
                        extra_lines=["zone 70"],
                    ),
                ]
            )
        else:
            # WATER bands, with a clean SHALLOW gap in the middle.
            for y in stamps_between(3, geometry.ford_y1 - 3, water_step):
                blocks.append(
                    land_block(
                        "WATER",
                        50,
                        y,
                        base_size=river_base_size,
                        number_of_tiles=river_tiles,
                        extra_lines=["zone 70"],
                    )
                )
            for y in stamps_between(geometry.ford_y2 + 3, 97, water_step):
                blocks.append(
                    land_block(
                        "WATER",
                        50,
                        y,
                        base_size=river_base_size,
                        number_of_tiles=river_tiles,
                        extra_lines=["zone 70"],
                    )
                )

        # Trade lanes: broad enough for carts, low stamp count.
        for lane_x, zone in [(geometry.west_lane, 80), (geometry.east_lane, 81)]:
            for y in stamps_between(1, 99, path_step):
                blocks.append(
                    land_block(
                        "GRASS",
                        lane_x,
                        y,
                        base_size=path_base_size,
                        number_of_tiles=path_tiles,
                        extra_lines=[f"zone {zone}"],
                    )
                )

        # Center access paths stop before the shallow ford, so no GRASS/SHALLOW overlap.
        for x in stamps_between(geometry.west_lane, geometry.river_x1 - 1, path_step):
            blocks.append(
                land_block(
                    "GRASS",
                    x,
                    50,
                    base_size=path_base_size,
                    number_of_tiles=path_tiles,
                    extra_lines=["zone 82"],
                )
            )
        for x in stamps_between(geometry.river_x2 + 1, geometry.east_lane, path_step):
            blocks.append(
                land_block(
                    "GRASS",
                    x,
                    50,
                    base_size=path_base_size,
                    number_of_tiles=path_tiles,
                    extra_lines=["zone 82"],
                )
            )

        # Shallows are their own non-overlapping terrain band across the full river width.
        for y in stamps_between(geometry.ford_y1, geometry.ford_y2, shallow_step):
            for x in stamps_between(geometry.river_x1 + 1, geometry.river_x2 - 1, shallow_step):
                blocks.append(
                    land_block(
                        "SHALLOW",
                        x,
                        y,
                        base_size=shallow_base_size,
                        number_of_tiles=shallow_tiles,
                        extra_lines=["zone 71"],
                    )
                )

    for start in player_starts(geometry.team_lane_x):
        blocks.append(
            land_block(
                "GRASS",
                start.x,
                start.y,
                base_size=start_base_size,
                number_of_tiles=start_tiles,
                border_fuzziness=2,
                land_id=start.player_id,
                circular=True,
                extra_lines=[
                    f"assign_to_player {start.player_id}",
                    f"zone {start.player_id}",
                    "other_zone_avoidance_distance 2",
                ],
            )
        )

    for pocket in resource_pockets():
        blocks.append(
            land_block(
                "GRASS",
                pocket.x,
                pocket.y,
                base_size=pocket_base_size,
                number_of_tiles=pocket_tiles,
                land_id=pocket.land_id,
                circular=True,
                extra_lines=["zone 90"],
            )
        )

    return blocks


def object_generation_blocks(*, pocket_gold_nodes: int, pocket_stone_nodes: int) -> list[str]:
    blocks: list[str] = []

    blocks.extend(
        [
            "/* Standard starting town. */",
            object_block(
                "TOWN_CENTER",
                [
                    "set_place_for_every_player",
                    "terrain_to_place_on GRASS",
                    "min_distance_to_players 0",
                    "max_distance_to_players 0",
                ],
            ),
            "",
            object_block(
                "VILLAGER",
                [
                    "number_of_objects 3",
                    "set_place_for_every_player",
                    "terrain_to_place_on GRASS",
                    "min_distance_to_players 6",
                    "max_distance_to_players 7",
                ],
            ),
            "",
            object_block(
                "SCOUT",
                [
                    "number_of_objects 1",
                    "set_place_for_every_player",
                    "terrain_to_place_on GRASS",
                    "min_distance_to_players 7",
                    "max_distance_to_players 9",
                ],
            ),
            "",
            "/* Per-player start resources inside the open start circle. */",
        ]
    )

    start_resources = [
        (
            "SHEEP",
            [
                "number_of_objects 5",
                "set_place_for_every_player",
                "set_gaia_object_only",
                "set_loose_grouping",
                "group_placement_radius 4",
                "terrain_to_place_on GRASS",
                "min_distance_to_players 6",
                "max_distance_to_players 9",
            ],
        ),
        (
            "FORAGE",
            [
                "number_of_objects 5",
                "resource_delta -5",
                "set_place_for_every_player",
                "set_gaia_object_only",
                "set_tight_grouping",
                "group_placement_radius 2",
                "terrain_to_place_on GRASS",
                "min_distance_to_players 10",
                "max_distance_to_players 13",
            ],
        ),
        (
            "GOLD",
            [
                "number_of_objects 8",
                "set_place_for_every_player",
                "set_gaia_object_only",
                "set_tight_grouping",
                "group_placement_radius 2",
                "terrain_to_place_on GRASS",
                "min_distance_to_players 14",
                "max_distance_to_players 18",
            ],
        ),
        (
            "STONE",
            [
                "number_of_objects 5",
                "set_place_for_every_player",
                "set_gaia_object_only",
                "set_tight_grouping",
                "group_placement_radius 2",
                "terrain_to_place_on GRASS",
                "min_distance_to_players 16",
                "max_distance_to_players 21",
            ],
        ),
        (
            "BOAR",
            [
                "number_of_objects 4",
                "set_place_for_every_player",
                "set_gaia_object_only",
                "set_loose_grouping",
                "group_placement_radius 5",
                "terrain_to_place_on GRASS",
                "min_distance_to_players 18",
                "max_distance_to_players 24",
            ],
        ),
    ]

    for object_name, attributes in start_resources:
        blocks.append(object_block(object_name, attributes))
        blocks.append("")

    blocks.append("/* Chop-to forest pockets: explicit one-node placements for reliability. */")
    for pocket in resource_pockets():
        nodes = pocket_gold_nodes if pocket.resource == "GOLD" else pocket_stone_nodes
        blocks.append(f"/* {pocket.team} {pocket.resource.lower()} pocket, land_id {pocket.land_id}. */")
        for node in range(1, nodes + 1):
            blocks.append(
                object_block(
                    pocket.resource,
                    [
                        "number_of_objects 1",
                        "set_gaia_object_only",
                        "terrain_to_place_on GRASS",
                        f"place_on_specific_land_id {pocket.land_id}",
                        "find_closest",
                    ],
                )
            )
            blocks.append(f"/* {pocket.resource.lower()} node {node}/{nodes}. */")
            blocks.append("")

    blocks.extend(
        [
            "/* Ambient and neutral objects. */",
            object_block(
                "HAWK",
                [
                    "number_of_objects 6",
                    "set_scaling_to_map_size",
                ],
            ),
            "",
            object_block(
                "FISH",
                [
                    "number_of_objects 20",
                    "set_gaia_object_only",
                    "set_loose_grouping",
                    "group_placement_radius 5",
                    "terrain_to_place_on WATER",
                ],
            ),
            "",
            object_block(
                "RELIC",
                [
                    "number_of_objects 5",
                    "set_gaia_object_only",
                    "terrain_to_place_on GRASS",
                    "min_distance_to_players 30",
                    "max_distance_to_players 80",
                ],
            ),
            "",
        ]
    )

    return blocks


def generate_rms(
    *,
    preset_name: str,
    validate_coverage: bool,
    map_size: int,
    enable_waves: int,
    bounded_terrain: bool,
    bounded_water: bool,
    geometry: Geometry,
    water_step: int,
    path_step: int,
    shallow_step: int,
    river_base_size: int,
    river_tiles: int,
    path_base_size: int,
    path_tiles: int,
    shallow_base_size: int,
    shallow_tiles: int,
    start_base_size: int,
    start_tiles: int,
    pocket_base_size: int,
    pocket_tiles: int,
    pocket_gold_nodes: int,
    pocket_stone_nodes: int,
) -> str:
    plan = build_plan(geometry)
    plan.require_no_conflicts()
    if validate_coverage and not bounded_terrain:
        validate_stamp_coverage(
            geometry=geometry,
            map_size=map_size,
            bounded_water=bounded_water,
            water_step=water_step,
            path_step=path_step,
            shallow_step=shallow_step,
            river_base_size=river_base_size,
            river_tiles=river_tiles,
            path_base_size=path_base_size,
            path_tiles=path_tiles,
            shallow_base_size=shallow_base_size,
            shallow_tiles=shallow_tiles,
        )

    if bounded_terrain:
        validation_note = (
            "  Python validation passed: no explicit terrain conflicts; bounded terrain mode does not use route stamps."
        )
    elif bounded_water and validate_coverage:
        validation_note = (
            "  Python validation passed: no explicit terrain conflicts; river uses bounded terrain; path stamp coverage validated."
        )
    elif validate_coverage:
        validation_note = (
            "  Python validation passed: no explicit terrain conflicts and no map-size stamp coverage gaps."
        )
    else:
        validation_note = (
            "  Python validation passed: no explicit terrain conflicts; map-size stamp coverage was skipped."
        )

    lines: list[str] = [
        "/*",
        f"  {MAP_NAME} - generated RMS",
        "  8 players, intended for team games with slots 1-4 west and 5-8 east.",
        f"  Config preset: {preset_name}.",
        "  Base terrain is FOREST; explicit non-overlapping lands carve river, ford, paths, starts, and pockets.",
        validation_note,
        "*/",
        "",
        "<PLAYER_SETUP>",
        "direct_placement",
        "behavior_version 1",
        f"override_map_size {map_size}",
        "team_positions",
        "",
        "<LAND_GENERATION>",
        "base_terrain FOREST",
        f"enable_waves {enable_waves}",
        "",
        "/* Main terrain features. The internal validator rejects mixed-terrain overlaps. */",
    ]

    terrain_blocks = terrain_land_blocks(
        geometry=geometry,
        bounded_terrain=bounded_terrain,
        bounded_water=bounded_water,
        water_step=water_step,
        path_step=path_step,
        shallow_step=shallow_step,
        river_base_size=river_base_size,
        river_tiles=river_tiles,
        path_base_size=path_base_size,
        path_tiles=path_tiles,
        shallow_base_size=shallow_base_size,
        shallow_tiles=shallow_tiles,
        start_base_size=start_base_size,
        start_tiles=start_tiles,
        pocket_base_size=pocket_base_size,
        pocket_tiles=pocket_tiles,
    )

    for block in terrain_blocks:
        lines.append(block)
        lines.append("")

    lines.extend(
        [
            "<TERRAIN_GENERATION>",
            "/* No forest fill section: FOREST is the base terrain. */",
            "",
            "<OBJECTS_GENERATION>",
        ]
    )
    lines.extend(
        object_generation_blocks(
            pocket_gold_nodes=pocket_gold_nodes,
            pocket_stone_nodes=pocket_stone_nodes,
        )
    )

    lines.append("/* Known limitation: RMS generation still needs in-game testing in AoE2 DE. */")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    preset_parser = argparse.ArgumentParser(add_help=False)
    preset_parser.add_argument(
        "--preset",
        choices=sorted(VERSION_PRESETS),
        default=DEFAULT_PRESET,
        help="Version config preset to use as defaults",
    )
    preset_parser.add_argument("--list-presets", action="store_true", help="Print saved version configs and exit")
    preset_args, _ = preset_parser.parse_known_args()
    preset = VERSION_PRESETS[preset_args.preset]

    parser = argparse.ArgumentParser(
        description=f"Generate {MAP_NAME} as an AoE2 DE .rms file.",
        parents=[preset_parser],
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(default_output_for_preset(preset_args.preset)),
        help="Output .rms path",
    )
    parser.add_argument("--validate-only", action="store_true", help="Validate terrain conflicts and map-size stamp coverage without writing RMS")
    parser.add_argument("--skip-coverage-validation", action="store_true", help="Allow exact regeneration of historical presets that predate coverage validation")
    parser.add_argument("--self-test-validator", action="store_true", help="Confirm that the terrain validator flags a deliberate conflict")
    parser.add_argument("--map-size", type=int, default=preset["map_size"], help="override_map_size value, 36..480")
    parser.add_argument("--enable-waves", type=int, choices=[0, 1], default=preset["enable_waves"], help="RMS enable_waves value")
    parser.add_argument("--bounded-terrain", type=int, choices=[0, 1], default=preset["bounded_terrain"], help="Use border-constrained terrain rectangles for all routes")
    parser.add_argument("--bounded-water", type=int, choices=[0, 1], default=preset.get("bounded_water", 0), help="Use border-constrained rectangles for river WATER only (reduces blend cost)")
    parser.add_argument("--team-lane-x", type=int, default=preset["team_lane_x"], help="West trade lane x percent; east mirrors it")
    parser.add_argument("--river-half-width", type=int, default=preset["river_half_width"], help="Half-width of the reserved river in percent")
    parser.add_argument("--ford-half-height", type=int, default=preset["ford_half_height"], help="Half-height of the central shallow ford in percent")
    parser.add_argument("--path-half-width", type=int, default=preset["path_half_width"], help="Half-width of intended open trade/access paths in percent")
    parser.add_argument("--start-clear-radius", type=int, default=preset["start_clear_radius"], help="Radius of open player starts in percent")
    parser.add_argument("--pocket-radius", type=int, default=preset["pocket_radius"], help="Radius of chop-to ore pockets in percent")
    parser.add_argument("--water-step", type=int, default=preset["water_step"], help="Percent spacing for river stamps")
    parser.add_argument("--path-step", type=int, default=preset["path_step"], help="Percent spacing for trade/access path stamps")
    parser.add_argument("--shallow-step", type=int, default=preset["shallow_step"], help="Percent spacing for central shallow stamps")
    parser.add_argument("--river-base-size", type=int, default=preset["river_base_size"], help="RMS base_size for river water stamps")
    parser.add_argument("--river-tiles", type=int, default=preset["river_tiles"], help="RMS number_of_tiles for river water stamps")
    parser.add_argument("--path-base-size", type=int, default=preset["path_base_size"], help="RMS base_size for trade/access path stamps")
    parser.add_argument("--path-tiles", type=int, default=preset["path_tiles"], help="RMS number_of_tiles for trade/access path stamps")
    parser.add_argument("--shallow-base-size", type=int, default=preset["shallow_base_size"], help="RMS base_size for central shallows")
    parser.add_argument("--shallow-tiles", type=int, default=preset["shallow_tiles"], help="RMS number_of_tiles for central shallows")
    parser.add_argument("--start-base-size", type=int, default=preset["start_base_size"], help="RMS base_size for player clearings")
    parser.add_argument("--start-tiles", type=int, default=preset["start_tiles"], help="RMS number_of_tiles for player clearings")
    parser.add_argument("--pocket-base-size", type=int, default=preset["pocket_base_size"], help="RMS base_size for chop-to ore pockets")
    parser.add_argument("--pocket-tiles", type=int, default=preset["pocket_tiles"], help="RMS number_of_tiles for chop-to ore pockets")
    parser.add_argument("--pocket-gold-nodes", type=int, default=preset["pocket_gold_nodes"], help="Gold nodes per forest gold pocket")
    parser.add_argument("--pocket-stone-nodes", type=int, default=preset["pocket_stone_nodes"], help="Stone nodes per forest stone pocket")
    args = parser.parse_args()

    if args.list_presets:
        print_presets()
        return

    if args.self_test_validator:
        self_test_validator()
        return

    if not 36 <= args.map_size <= 480:
        raise SystemExit("--map-size must be between 36 and 480")
    if not 16 <= args.team_lane_x <= 36:
        raise SystemExit("--team-lane-x must be between 16 and 36")
    if not 4 <= args.river_half_width <= 12:
        raise SystemExit("--river-half-width must be between 4 and 12")
    if not 3 <= args.ford_half_height <= 8:
        raise SystemExit("--ford-half-height must be between 3 and 8")
    if not 2 <= args.path_half_width <= 5:
        raise SystemExit("--path-half-width must be between 2 and 5")
    if not 6 <= args.start_clear_radius <= 12:
        raise SystemExit("--start-clear-radius must be between 6 and 12")
    if not 3 <= args.pocket_radius <= 6:
        raise SystemExit("--pocket-radius must be between 3 and 6")
    if not 2 <= args.water_step <= 10:
        raise SystemExit("--water-step must be between 2 and 10")
    if not 2 <= args.path_step <= 10:
        raise SystemExit("--path-step must be between 2 and 10")
    if not 2 <= args.shallow_step <= 6:
        raise SystemExit("--shallow-step must be between 2 and 6")
    if not 6 <= args.pocket_gold_nodes <= 10:
        raise SystemExit("--pocket-gold-nodes must be between 6 and 10")
    if not 6 <= args.pocket_stone_nodes <= 10:
        raise SystemExit("--pocket-stone-nodes must be between 6 and 10")

    geometry = geometry_from_args(args)
    bounded_terrain = bool(args.bounded_terrain)
    bounded_water = bool(args.bounded_water)
    plan = build_plan(geometry)
    plan.require_no_conflicts()
    if bounded_terrain:
        print(
            "Validation passed: "
            f"{len(plan.cells)} explicit terrain cells, 0 terrain conflicts; "
            "bounded terrain mode does not use route stamps."
        )
    elif args.skip_coverage_validation:
        print(
            "Validation passed: "
            f"{len(plan.cells)} explicit terrain cells, 0 terrain conflicts; "
            "map-size stamp coverage skipped."
        )
    else:
        validate_stamp_coverage(
            geometry=geometry,
            map_size=args.map_size,
            bounded_water=bounded_water,
            water_step=args.water_step,
            path_step=args.path_step,
            shallow_step=args.shallow_step,
            river_base_size=args.river_base_size,
            river_tiles=args.river_tiles,
            path_base_size=args.path_base_size,
            path_tiles=args.path_tiles,
            shallow_base_size=args.shallow_base_size,
            shallow_tiles=args.shallow_tiles,
        )
        if bounded_water:
            print(
                "Validation passed: "
                f"{len(plan.cells)} explicit terrain cells, 0 terrain conflicts; "
                f"river uses bounded terrain; 0 path stamp coverage gaps at size {args.map_size}."
            )
        else:
            print(
                "Validation passed: "
                f"{len(plan.cells)} explicit terrain cells, 0 terrain conflicts, "
                f"0 map-size stamp coverage gaps at size {args.map_size}."
            )

    if args.validate_only:
        return

    rms = generate_rms(
        preset_name=args.preset,
        validate_coverage=not args.skip_coverage_validation,
        map_size=args.map_size,
        enable_waves=args.enable_waves,
        bounded_terrain=bounded_terrain,
        bounded_water=bounded_water,
        geometry=geometry,
        water_step=args.water_step,
        path_step=args.path_step,
        shallow_step=args.shallow_step,
        river_base_size=args.river_base_size,
        river_tiles=args.river_tiles,
        path_base_size=args.path_base_size,
        path_tiles=args.path_tiles,
        shallow_base_size=args.shallow_base_size,
        shallow_tiles=args.shallow_tiles,
        start_base_size=args.start_base_size,
        start_tiles=args.start_tiles,
        pocket_base_size=args.pocket_base_size,
        pocket_tiles=args.pocket_tiles,
        pocket_gold_nodes=args.pocket_gold_nodes,
        pocket_stone_nodes=args.pocket_stone_nodes,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rms, encoding="utf-8")
    print(f"Wrote {output_path.resolve()}")


if __name__ == "__main__":
    main()
