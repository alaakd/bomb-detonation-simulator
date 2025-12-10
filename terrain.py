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

from copy import deepcopy
from enum import Enum
from typing import Optional, Iterable, Iterator
from position import Position, Direction


class Token:
    """All tokens used in terrain files and terrain console output."""
    instances: list[Token] = []
    
    def __init__(self, c: str):
        self.value = c
        Token.instances.append(self)


    def from_str(c: str) -> Optional[Token]:
        for t in Token.instances:
            if t.value == c:
                return t

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Token.from_str({self.value})"

    def __eq__(self, other) -> bool:
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
    

Token.EMPTY = Token(' ')
Token.START = Token('@')
Token.GOAL = Token('X')
Token.WALL = Token('#')
Token.WATER = Token('~')
Token.CURRENT_LOCATION = Token('O')
Token.VERTICAL = Token('\u2502')
Token.HORIZONTAL = Token('\u2500')
Token.DOWN_AND_RIGHT = Token('\u250c')
Token.DOWN_AND_LEFT = Token('\u2510')
Token.UP_AND_RIGHT = Token('\u2514')
Token.UP_AND_LEFT = Token('\u2518')
Token.GREY_TOKEN = Token('\u2591')
Token.BLACK_TOKEN = Token('\u2592')
Token.VISITED_TOKEN = Token('.')
Token.SEEN_TOKEN = Token('*')
Token.BORDER_HORIZONTAL = Token('\u2550')
Token.BORDER_VERTICAL = Token('\u2551')
Token.BORDER_UP_AND_RIGHT = Token('\u255a')
Token.BORDER_UP_AND_LEFT = Token('\u255d')
Token.BORDER_DOWN_AND_RIGHT = Token('\u2554')
Token.BORDER_DOWN_AND_LEFT = Token('\u2557')
Token.PATH = Token('*')
Token.UNKNOWN = Token('?')
Token.BOMB = Token('ό')

Token.FLAMES = {
    Token("╴"),
    Token("╶"),
    Token("─"),
    Token("╵"),
    Token("┘"),
    Token("└"),
    Token("┴"),
    Token("╷"),
    Token("┐"),
    Token("┌"),
    Token("┬"),
    Token("│"),
    Token("┤"),
    Token("├"),
    Token("┼")
}


# Simplifies console path drawing
PATH_TOKENS: list[list[Token]] = \
    [  # NONE         UP                  RIGHT                DOWN                  LEFT
        [Token.EMPTY, Token.EMPTY, Token.EMPTY, Token.EMPTY, Token.EMPTY],  # NONE
        [Token.EMPTY, Token.EMPTY, Token.UP_AND_RIGHT, Token.VERTICAL, Token.UP_AND_LEFT],  # UP
        [Token.EMPTY, Token.UP_AND_RIGHT, Token.EMPTY, Token.DOWN_AND_RIGHT, Token.HORIZONTAL],  # RIGHT
        [Token.EMPTY, Token.VERTICAL, Token.DOWN_AND_RIGHT, Token.EMPTY, Token.DOWN_AND_LEFT],  # DOWN
        [Token.EMPTY, Token.UP_AND_LEFT, Token.HORIZONTAL, Token.DOWN_AND_LEFT, Token.EMPTY],  # LEFT
    ]


class TerrainError(Exception):
    """Errors in loading or accessing the terrain."""
    pass


class Terrain:
    """Representation of a "terrain", a 2D grid containing paths and obstacles for an agent to navigate."""

    def __init__(self, *, file_name: Optional[str] = None, width: int = 0, height: int = 0, start_goal_required=True):
        if file_name is not None:
            with open(file_name, "r") as terrain_file:
                self._width: int = int(terrain_file.readline())
                self._height: int = int(terrain_file.readline())

                self._terrain: list[Token] = [Token.EMPTY] * (self._width * self._height)

                self._start: Position
                self._goal: Position

                has_start: bool = False
                has_goal: bool = False

                for y, line in enumerate(terrain_file):
                    line = line.strip("\n")
                    for x, c in enumerate(line):
                        token: Token = Token.from_str(c)
                        self._terrain[y * self._width + x] = token

                        if token == Token.START:
                            self._start = Position(x, y)
                            has_start = True
                        elif token == Token.GOAL:
                            self._goal = Position(x, y)
                            has_goal = True

            if not (has_goal and has_start) and start_goal_required:
                raise TerrainError("Goal or start missing")

        else:
            self._width = width
            self._height = height
            self._terrain: list[Token] = [Token.EMPTY] * (self._width * self._height)

    @property
    def height(self) -> int:
        return self._height

    @property
    def width(self) -> int:
        return self._width

    @property
    def start(self) -> Position:
        return self._start

    @property
    def goal(self) -> Position:
        return self._goal

    def is_valid_position(self, pos: Position) -> bool:
        """Is this position a valid position for this terrain?"""
        if pos.x < 0 or pos.x >= self._width or pos.y < 0 or pos.y >= self._height:
            return False
        return True

    def _loc_to_index(self, pos: Position) -> int:
        if not self.is_valid_position(pos):
            raise TerrainError(f"Position out of bounds: {pos}.")
        return pos.y * self._width + pos.x

    def __getitem__(self, pos: Position) -> Token:
        """gets the token describing the cell at this position
        Raises an exception if the position is not valid
        """
        return self.get_token(pos)

    def get_token(self, pos: Position) -> Token:
        """gets the token describing the cell at this position
        Raises an exception if the position is not valid
        """
        return self._terrain[self._loc_to_index(pos)]
    
    def __setitem__(self, pos: Position, token: Token):
        """sets the token describing the cell at this position
        Raises an exception if the position is not valid
        """
        raise Exception("Use `update` instead, but remember: terrain was meant for reading only when doing DFS/BFS and for recursion.")

    def update(self, changes: dict[Position, Token]):
        """updates all the changed positions with their new tokens."""
        for pos, token in changes.items():
            self._terrain[self._loc_to_index(pos)] = token

    def __iter__(self) -> Iterator[tuple[Position, Token]]:
        self._cursor_x: int = 0
        self._cursor_y: int = 0
        return self

    def __next__(self) -> tuple[Position, Token]:
        # if we go past the bottom (recall that y's increase going down
        # in the world of graphics)
        if self._cursor_y >= self._height:
            raise StopIteration

        pos: Position = Position(self._cursor_x, self._cursor_y)
        loc = self._cursor_y * self._width + self._cursor_x
        token: Token = self._terrain[loc]

        if self._cursor_x < self._width - 1:
            self._cursor_x += 1
        else:
            self._cursor_x = 0
            self._cursor_y += 1

        return pos, token
        
        
    def __str__(self):

        s: str
        s = Token.BORDER_DOWN_AND_RIGHT.value + Token.BORDER_HORIZONTAL.value * self._width + Token.BORDER_DOWN_AND_LEFT.value + "\n"
        for i in range(self._height):
            s += Token.BORDER_VERTICAL.value
            for j in range(self._width):
                s += self._terrain[i * self._width + j].value
            s += Token.BORDER_VERTICAL.value + "\n"
        s += Token.BORDER_UP_AND_RIGHT.value + Token.BORDER_HORIZONTAL.value * self._width + Token.BORDER_UP_AND_LEFT.value + "\n"
        return s


    def str_with_flames(self, flames: dict):

        s: str
        s = Token.BORDER_DOWN_AND_RIGHT.value + Token.BORDER_HORIZONTAL.value * self._width + Token.BORDER_DOWN_AND_LEFT.value + "\n"
        for i in range(self._height):
            s += Token.BORDER_VERTICAL.value
            for j in range(self._width):
                if (j, i) in flames:
                    s += flames[(j, i)]
                else:
                    s += self._terrain[i * self._width + j].value
            s += Token.BORDER_VERTICAL.value + "\n"
        s += Token.BORDER_UP_AND_RIGHT.value + Token.BORDER_HORIZONTAL.value * self._width + Token.BORDER_UP_AND_LEFT.value + "\n"
        return s

    
    def apply_path(self, path: Iterable[Direction], simple_path_tokens: bool = False) -> Terrain:
        """Creates a Terrain with path tokens attached, according to the directions in pth"""
        copy: Terrain = deepcopy(self)

        previous_direction: Direction = Direction.NONE

        # from the start, follow the to directions and place the tokens appropriately.
        current: Position = self.start
        for to in path:
            next_position: Position = current.get_new_position_from(to)

            if next_position.x < 0 or next_position.x >= self.width or next_position.y < 0 or next_position.y >= self.height:
                print(f"Out of bounds at {next_position}.")
                continue

            if self.get_token(next_position) == Token.WALL:
                print(f"Hit a wall at {next_position}.")
                continue

            if current != self.start and current != self.goal:
                if simple_path_tokens:
                    copy._terrain[self._loc_to_index(current)] = Token.PATH
                else:
                    copy._terrain[self._loc_to_index(current)] = PATH_TOKENS[previous_direction.opposite().value][
                        to.value]

            previous_direction = to
            current = next_position

        if current != self.start and current != self.goal:
            copy._terrain[self._loc_to_index(current)] = Token.CURRENT_LOCATION
        return copy

    def apply_visited(self, positions: Iterable[Position], token: Token = Token.VISITED_TOKEN) -> Terrain:

        copy: Terrain = deepcopy(self)

        for position in positions:
            if position.x < 0 or position.x >= self.width or \
                    position.y < 0 or position.y >= self.height:
                continue

            if self.get_token(position) == Token.WALL:
                continue

            if copy._terrain[self._loc_to_index(position)] == Token.EMPTY:
                copy._terrain[self._loc_to_index(position)] = token

        return copy
