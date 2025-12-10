#  Copyright (c) 2024 Sandy Bultena and Ian Clement.
#
#  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this program. If not,
#  see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import math
from time import time
from typing import Callable, Iterator, Iterable, Optional, Any, TypeVar

import pygame
from pygame import Surface, SRCALPHA

from terrain import Terrain, Token, Position

# ============================================================================
# Duration
# ============================================================================

# time durations (differences in time) will be represented as floats
Duration = float


def delta(p1: Position, p2: Position) -> tuple[int, int]:
    """Calculate the component-wise distance between two positions"""
    return (p2.x - p1.x, p2.y - p1.y)


def distance_straight_line(p1: Position, p2: Position) -> float:
    """Calculate the straight line distance between two points."""
    return math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)


def distance_city_block(p1: Position, p2: Position) -> int:
    """Calculate the "city block" distance between two points."""
    return abs(p2.x - p1.x) + abs(p2.y - p1.y)


def scale(pos: Position, amount: int) -> Position:
    """Scale the position. Used when converting between the terrain coordinates and the screen positions."""
    return Position(pos.x * amount, pos.y * amount)


def midpoint(p1: Position, p2: Position) -> Position:
    return Position((p2.x + p1.x) // 2, (p2.y + p1.y) // 2)

# ============================================================================
# Movement
# ============================================================================

Movement = Callable[[Duration], Position]

T = TypeVar("T")


def const(x: T) -> Callable[[Any], T]:
    return lambda y: x

def linear(delta: Duration) -> Callable[[Position, Position], Movement]:
    """
    Create a linear movement
    :param delta:
    :return:
    """
    def g(start: Position, end: Position) -> Movement:
        dx = end.x - start.x
        dy = end.y - start.y

        def f(time: float) -> Position:
            t = min(delta, time) / delta
            return Position(int(start.x + t * dx), int(start.y + t * dy))

        return f

    return g


def divide_equal(total: Duration, parts: int) -> Iterator[Duration]:
    """Generate equal time slices for a total duration"""
    time_slice: Duration = total / parts
    for i in range(parts):
        yield time_slice


def forever() -> Iterator[Duration]:
    """Convenience generator for constant animations."""
    yield math.inf


def combine(sprites: Iterator[Surface] | Iterable[Surface], durations: Iterator[Duration] | Iterable[Duration]) \
        -> Iterable[tuple[Surface, Duration]]:
    """Combine two iterators to make an iterable."""
    return list(zip(sprites, durations))


# ============================================================================
# Animation
# ============================================================================

# Note: when creating animations, we can use itertools.
# to have a constant animation: Animation(combine(repeat(sprite), forever()))
# to have a looped animation: Animation(combine(cycle(sprites), divide_equal(1.0, len(sprites)))


class Animation:
    """Animate a sequence of surfaces with associated durations"""

    def __init__(self, sprites: Iterable[tuple[Surface, Duration]]):

        self._sprites: Iterable[tuple[Surface, Duration]] = sprites
        self._sprite_iterator: Iterator[tuple[Surface, Duration]] = iter(self._sprites)

        self._current_sprite: Surface
        self._time_to_next_sprite: Duration
        (self._current_sprite, self._time_to_next_sprite) = next(self._sprite_iterator)

        self._done: bool = False

    def reset(self):
        self._sprite_iterator = iter(self._sprites)
        (self._current_sprite, self._time_to_next_sprite) = next(self._sprite_iterator)
        self._done = False

    def advance(self, delta: Duration) -> Optional[Surface]:

        self._time_to_next_sprite -= delta

        if self._time_to_next_sprite < 0.0:
            try:
                leftover_time: Duration = self._time_to_next_sprite
                (self._current_sprite, self._time_to_next_sprite) = next(self._sprite_iterator)
                self._time_to_next_sprite -= leftover_time
            except StopIteration:
                self._done = True
                return None

        return self._current_sprite

    def is_done(self) -> bool:
        return self._done


class MovementError(Exception):
    pass


# ============================================================================
# Sprites
# ============================================================================

SHEET_CELL_SIZE: int = 32


class SpriteSheet:
    """Load a sprite sheet"""

    def __init__(self, sprite_sheet_file: str, cell_width: int, cell_height: int, sprite_width: int,
                 sprite_height: int):
        """
        :param sprite_sheet_file: Sprite sheet file.
        :param cell_width: Width of each cell.
        :param cell_height: Height of each cell.
        """
        self._sprite = pygame.image.load(sprite_sheet_file).convert_alpha()

        self._width: int = self._sprite.get_width() // cell_width
        self._height: int = self._sprite.get_height() // cell_height

        self._sprite_width: int = sprite_width
        self._sprite_height: int = sprite_height

        self._sprites: list[list[Surface]] = []

        for i in range(self._width):
            col: list[Surface] = []
            offsetx: int = i * cell_height
            for j in range(self._height):
                # create an alpha surface for each sprite in the sheet
                sub_sprite: Surface = Surface((cell_width, cell_height), SRCALPHA)
                offsety: int = j * cell_width
                sub_sprite.blit(self._sprite, (0, 0), (offsetx, offsety, offsetx + cell_width, offsety + cell_height))
                sub_sprite = pygame.transform.scale(sub_sprite, (sprite_width, sprite_height))
                col.append(sub_sprite)
            self._sprites.append(col)

    @property
    def sprite_width(self):
        return self._sprite_width

    @property
    def sprite_height(self):
        return self._sprite_height

    def get(self, loc: tuple[int, int]) -> Surface:
        """Get a cell in the sprite sheet."""
        return self._sprites[loc[0]][loc[1]]

    def gets(self, locs: list[tuple[int, int]]) -> list[Surface]:
        """Get cells in the sprite sheet."""
        return list(map(lambda loc: self.get(loc), locs))


class TerrainSprite(SpriteSheet):
    """Sprite sheet for terrain tiles"""

    def __init__(self, sprite_sheet_file: str, sprite_width: int, sprite_height: int):
        super().__init__(sprite_sheet_file, SHEET_CELL_SIZE, SHEET_CELL_SIZE, sprite_width, sprite_height)
        self._grass: Surface = self.get((0, 0))
        self._wall: Surface = self.get((0, 1))

    @property
    def wall(self) -> Surface:
        return self._wall

    @property
    def grass(self) -> Surface:
        return self._grass


class GoalSprite(SpriteSheet):
    """Sprite Sheet for goal."""

    def __init__(self, sprite_sheet_file: str, sprite_width: int, sprite_height: int):
        super().__init__(sprite_sheet_file, SHEET_CELL_SIZE, SHEET_CELL_SIZE, sprite_width, sprite_height)
        self._loop: Animation = Animation(combine([self.get((x, 0)) for x in range(3)], divide_equal(1.5, 3)))
        self._start: Surface = self.get((3, 0))

    @property
    def loop(self) -> Animation:
        return self._loop

    @property
    def start(self) -> Surface:
        return self._start

class BombSprite(SpriteSheet):
    """Sprite Sheet for bomb. Just a single image for now"""

    def __init__(self, sprite_sheet_file: str, sprite_width: int, sprite_height: int):
        super().__init__(sprite_sheet_file, SHEET_CELL_SIZE, SHEET_CELL_SIZE, sprite_width, sprite_height)
        self._start: Surface = self.get((0, 0))

    @property
    def loop(self) -> Animation:
        return self._loop

    @property
    def start(self) -> Surface:
        return self._start

class FlameSprite(SpriteSheet):
    """Sprite Sheet for flames."""
    
    def __init__(self, sprite_sheet_file: str, sprite_width: int, sprite_height: int):
        super().__init__(sprite_sheet_file, SHEET_CELL_SIZE, SHEET_CELL_SIZE, sprite_width, sprite_height)
       

class PlayerSprite(SpriteSheet):
    """Sprite Sheet for player."""

    walking_speed = 0.4
    victory_speed = 1.0
    swimming_speed = 0.4
    def __init__(self, sprite_sheet_file: str, sprite_width: int, sprite_height: int):
        super().__init__(sprite_sheet_file, SHEET_CELL_SIZE, SHEET_CELL_SIZE, sprite_width, sprite_height)

        self._standing: Animation = Animation([(self.get((0, 0)), math.inf)])

        self._walking_down: Animation = Animation(
            combine(self.gets([(0, 0), (1, 0), (0, 0), (2, 0)]), divide_equal(self.walking_speed, 4)))

        self._walking_up: Animation = Animation(
            combine(self.gets([(0, 1), (1, 1), (0, 1), (2, 1)]), divide_equal(self.walking_speed, 4)))

        self._walking_right: Animation = Animation(
            combine(self.gets([(0, 2), (1, 2), (0, 2), (2, 2)]), divide_equal(self.walking_speed, 4)))

        self._walking_left: Animation = Animation(
            combine(self.gets([(0, 3), (1, 3), (0, 3), (2, 3)]), divide_equal(self.walking_speed, 4)))

        self._victory: Animation = Animation(
            combine(self.gets([(0, 4), (1, 4), (0, 4), (2, 4)]), divide_equal(self.victory_speed, 4)))

        self._defeat: Animation = Animation(
            combine(self.gets([(0, 5), (1, 5), (2, 5), (0, 6), (1, 6), (2, 6), (0, 7), (1, 7)]),
                    [1.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, math.inf]))

        self.swim_down: Animation = Animation(combine(self.gets([(2, 7), (0, 8)]), divide_equal(self.swimming_speed, 2)))
        self.swim_up: Animation = Animation(combine(self.gets([(1, 8), (2, 8)]), divide_equal(self.swimming_speed, 2)))
        self.swim_right: Animation = Animation(combine(self.gets([(0, 9), (1, 9)]), divide_equal(self.swimming_speed, 2)))
        self.swim_left: Animation = Animation(combine(self.gets([(2, 9), (0, 10)]), divide_equal(self.swimming_speed, 2)))

    @property
    def standing(self) -> Animation:
        return self._standing

    @property
    def walking_up(self) -> Animation:
        return self._walking_up

    @property
    def walking_down(self) -> Animation:
        return self._walking_down

    @property
    def walking_left(self) -> Animation:
        return self._walking_left

    @property
    def walking_right(self) -> Animation:
        return self._walking_right

    @property
    def facing_up(self) -> Surface:
        # return self.get((0,1))
        return self.get((1, 8))

    @property
    def facing_down(self) -> Surface:
        # return self.get((0,0))
        return self.get((2, 7))

    @property
    def facing_left(self) -> Surface:
        # return self.get((0, 3))
        return self.get((2, 9))

    @property
    def facing_right(self) -> Surface:
        # return self.get((0,2))
        return self.get((0, 9))

    @property
    def victory(self) -> Animation:
        return self._victory

    @property
    def defeat(self) -> Animation:
        return self._defeat

    def down(self) -> Surface:
        return self.get((0, 0))

    def up(self) -> Surface:
        return self.get((0, 1))

    def right(self) -> Surface:
        return self.get((0, 2))

    def left(self) -> Surface:
        return self.get((0, 3))


# ============================================================================
# Graphical Elements: Player, Terrain and Goal
# ============================================================================

class Player:
    """Graphical representation of the player. Supports UDLR movement and animation."""

    # TO DO eventually inherit pygame.Sprite to make this more pygame, works for now since
    # I reimplement some of the draw logic below

    def __init__(self, sprites: PlayerSprite, start: Position, speed: int):
        self._sprites: PlayerSprite = sprites
        self._position: Position = start

        self._animation: Animation = sprites.standing
        self._movement: Movement = const(self._position)
        self._movement_start_time: float = 0
        self._movement_end_time: float = 0

        self._speed: int = speed
        self._is_swimming: bool = False
        self._done = True

    def move_to(self, destination: Position):
        # TO DO generalize this for other movements not just UDLR?

        # TO DO replace this with a match but need to fix python 11
        dx, dy = delta(destination, self._position)
        if dx != 0 and dy != 0:
            raise MovementError(f"({dx},{dy})")

        if dx == 0 and dy == 0:
            # TO DO this could be better
            self._animation = self._sprites.standing
            self._movement = const(self._position)
            self._movement_start_time = time()
            self._movement_end_time = math.inf
            self._done = False
            return

        elif dx > 0:
            self._animation = self._sprites.swim_left if self._is_swimming else self._sprites.walking_left
        elif dx < 0:
            self._animation = self._sprites.swim_right if self._is_swimming else self._sprites.walking_right
        elif dy > 0:
            self._animation = self._sprites.swim_up if self._is_swimming else self._sprites.walking_up
        else:
            self._animation = self._sprites.swim_down if self._is_swimming else self._sprites.walking_down

        self._animation.reset()

        duration: float = abs(dx + dy) / self._speed
        self._movement = linear(duration)(self._position, destination)

        self._movement_start_time = time()
        self._movement_end_time = self._movement_start_time + duration
        self._done = False

    def victory(self):
        """Run victory animation."""
        self._animation = self._sprites.victory
        self._animation.reset()
        self._done = False
        self._movement = const(self._position)
        self._movement_start_time = time()
        self._movement_end_time = math.inf

    def defeat(self):
        """Run defeat animation."""
        self._animation = self._sprites.defeat
        self._animation.reset()
        self._done = False
        self._movement = const(self._position)
        self._movement_start_time = time()
        self._movement_end_time = math.inf

    def draw(self, screen, delta: Duration, next_time: float):
        """
        Draw the player after adjusting animation and movement using the current duration (delta).
        :param screen: The screen to draw the player on.
        :param delta: The time duration since the last draw.
        :param next_time: The end time of the duration. Needed to determine if animation/movement is complete.
        :return:
        """
        current: Optional[Surface] = self._animation.advance(delta)
        if current is None:
            self._animation.reset()
            current = self._animation.advance(delta)

        self._position = self._movement(next_time - self._movement_start_time)

        # adjust position since sheet is scaled by 2
        x, y = self._position.x, self._position.y
        screen.blit(current, (x - self._sprites.sprite_width / 4, y - self._sprites.sprite_height / 2))
        self._done = next_time >= self._movement_end_time

    def is_movement_done(self) -> bool:
        """Determine if movement is done."""
        return self._done


class TerrainSurface:
    """Graphical representatiopn of a terrain."""

    def __init__(self, sprite: TerrainSprite, terrain: Terrain, cell_size: int):
        self._terrain: Terrain = terrain
        self._surface: Surface = Surface((terrain.width * cell_size, terrain.height * cell_size)).convert_alpha()
        self._cell_size = cell_size
        for x in range(terrain.width):
            for y in range(terrain.height):
                tmp: Surface = sprite.grass
                match terrain[Position(x, y)]:
                    case Token.WALL:
                        tmp = sprite.wall
                    case Token.WATER:
                        tmp = sprite.water
                self._surface.blit(tmp, (x * cell_size, y * cell_size))

    @property
    def surface(self) -> Surface:
        return self._surface

    def add_start(self, sprite: Surface):
        self._surface.blit(sprite, scale(self._terrain.start, self._cell_size))

    def draw(self, screen):
        screen.blit(self._surface, (0, 0))


class Goal:
    """Graphical representation of the search goal."""

    def __init__(self, sprites: GoalSprite, goal: Position):
        self._sprites: GoalSprite = sprites
        self._goal: Position = goal
        self._animation: Animation = self._sprites.loop
        self._animation.reset()

    def draw(self, screen, delta: Duration):
        current: Optional[Surface] = self._animation.advance(delta)
        if current is None:
            self._animation.reset()
            current = self._animation.advance(delta)
        screen.blit(current, (self._goal.x, self.goal.y))


class Bomb:
    """Graphical representation of a bomb."""

    def __init__(self, sprites: BombSprite, pos: Position):
        self._sprites: BombSprite = sprites
        self._pos: Position = pos
        self._bomb: Surface = self._sprites.get((0,0))

    def draw(self, screen, delta: Duration):
        screen.blit(self._bomb, (self._pos.x, self._pos.y))


class Flame:
    """Graphical representation of a single flame."""

    _token_to_sprite: dict[Token, tuple[int, int]] = {
        Token("╴"): (3, 2),
        Token("╶"): (1, 3), 
        Token("─"): (1, 2), 
        Token("╵"): (2, 3), 
        Token("┘"): (3, 1), 
        Token("└"): (0, 2), 
        Token("┴"): (3, 0), 
        Token("╷"): (0, 3), 
        Token("┐"): (2, 1), 
        Token("┌"): (1, 1), 
        Token("┬"): (1, 0), 
        Token("│"): (2, 2), 
        Token("┤"): (2, 0), 
        Token("├"): (0, 1), 
        Token("┼"): (0, 0) 
    }
    
    def __init__(self, sprites: FlameSprite, pos: Position, token: Token):
        self._sprites: FlameSprite = sprites
        self._pos: Position = pos
        sheet_coord = Flame._token_to_sprite[token]
        self._flame: Surface = self._sprites.get(sheet_coord)

    def draw(self, screen):
        screen.blit(self._flame, (self._pos.x, self._pos.y))
