#  Copyright (c) 2025 Sandy Bultena and Ian Clement.
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
from enum import Enum


class InvalidDirectionError(Exception):
    pass


class Direction(Enum):
    """An enumeration of search directions"""
    NONE, UP, RIGHT, DOWN, LEFT = range(5)

    def opposite(self) -> Direction:
        if self == Direction.UP:
            return Direction.DOWN
        if self == Direction.DOWN:
            return Direction.UP
        if self == Direction.RIGHT:
            return Direction.LEFT
        if self == Direction.LEFT:
            return Direction.RIGHT
        return Direction.NONE

    def __str__(self) -> str:
        if self == Direction.UP:
            return "^"
        if self == Direction.DOWN:
            return "v"
        if self == Direction.RIGHT:
            return ">"
        if self == Direction.LEFT:
            return "<"
        return " "


class Position:
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @staticmethod
    def positions(min_x, max_x, min_y, max_y):
        return (Position(x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1))

    def __eq__(self, other):
        return self._x == other._x and self._y == other._y

    def __lt__(self, other):
        return self._x**2 + self._y**2 < other._x**2 + self._y**2

    def __hash__(self):
        return hash(str(self))

    def get_new_position_from(self, direction: Direction) -> Position:
        """From a position, get the next position in the given direction."""
        if direction == Direction.UP:
            return Position(self._x, self._y - 1)
        elif direction == Direction.RIGHT:
            return Position(self._x + 1, self._y)
        elif direction == Direction.DOWN:
            return Position(self._x, self._y + 1)
        elif direction == Direction.LEFT:
            return Position(self._x - 1, self._y)
        else:
            raise InvalidDirectionError

    def get_direction_to(self, position: Position) -> Direction:
        if self._x > position._x:
            return Direction.LEFT
        if self._x < position._x:
            return Direction.RIGHT
        if self._y > position._y:
            return Direction.UP
        if self._y < position._y:
            return Direction.DOWN
        return Direction.NONE

    def __str__(self):
        return f"({self._x}, {self._y})"

    def __repr__(self):
        return f"Position({self._x}, {self._y})"
