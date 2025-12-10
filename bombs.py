import sys

from terrain import Terrain, Token
from typing import Any
from position import Direction, Position

import pygame
from pygame import Surface
from pygame.locals import HWSURFACE, RESIZABLE, DOUBLEBUF, SRCALPHA, Rect

from graphics import TerrainSurface, TerrainSprite, BombSprite, FlameSprite, Bomb, Flame


BOMB_SIZE = 3
# Map directions to bit values
DIRECTION_TO_BIT = {
    Direction.DOWN: 1 << 3,   # 8
    Direction.UP: 1 << 2,     # 4
    Direction.RIGHT: 1 << 1,  # 2
    Direction.LEFT: 1 << 0,   # 1
}

# TODO: explain this a bit more in the instructions? It's setup for bitwise or
#-- Down, Up,    Right, Left
flame_tokens: dict[int, Token] = {
    0b0000: Token(' '),
    0b0001: Token('╴'),  # Right end cap
    0b0010: Token('╶'),  # Left end cap
    0b0011: Token('─'),  # Left + Right (horizontal line)
    0b0100: Token('╵'),  # Up end cap
    0b0101: Token('┘'),  # Up + Right (corner)
    0b0110: Token('└'),  # Up + Left (corner)
    0b0111: Token('┴'),  # Up + Left + Right (T down)
    0b1000: Token('╷'),  # Down end cap
    0b1001: Token('┐'),  # Down + Right (corner)
    0b1010: Token('┌'),  # Down + Left (corner)
    0b1011: Token('┬'),  # Down + Left + Right (T up)
    0b1100: Token('│'),  # Up + Down (vertical line)
    0b1101: Token('┤'),  # Up + Down + Right (T left)
    0b1110: Token('├'),  # Up + Down + Left (T right)
    0b1111: Token('┼')   # Full cross (center)
}


def detonate(pos: Position, terrain: Terrain) -> dict[Position, Token]:
    # Dictionary to store all the changes (flames created or walls destroyed)
    changes = {}

    def add_flame(position: Position, directions: set[Direction]):
        """Add or update a flame at a position by merging the given directions."""

        # Ignore invalid positions (out of bounds)
        if not terrain.is_valid_position(position):
            return

        # Start with no directions
        existing_mask = 0

        # If this position already has a flame, get its existing direction mask
        if position in changes:
            for mask, token in flame_tokens.items():
                if changes[position] == token:
                    existing_mask = mask
                    break

        # Merge the new directions into the existing mask
        for direction in directions:
            existing_mask |= DIRECTION_TO_BIT[direction]

        # Update the changes dictionary with the correct flame token
        changes[position] = flame_tokens[existing_mask]

    def _propagate(current: Position, incoming: Direction, remaining_steps: int):
        """Continue propagating the flame outward in a single direction."""

        # Stop if there are no more steps left
        if remaining_steps == 0:
            return

        # Get the token at the current position
        token = terrain.get_token(current)

        # If we hit a wall, destroy it and stop propagating
        if token == Token.WALL:
            changes[current] = Token.EMPTY
            return

        # If we hit another bomb, immediately detonate it recursively
        if token == Token.BOMB and current not in changes:
            _detonate(current)
            return

        # Determine which directions to mark at this cell
        if remaining_steps == 1:
            # At the final step (tip), mark only the outgoing direction (opposite of incoming)
            directions = {incoming.opposite()}
        else:
            # In the middle, mark both incoming and outgoing directions
            directions = {incoming, incoming.opposite()}

        # Add the flame with the correct directions
        add_flame(current, directions)

        # Move one step further in the same direction
        next_pos = current.get_new_position_from(incoming)

        # Continue propagation if the next position is valid
        if terrain.is_valid_position(next_pos):
            _propagate(next_pos, incoming, remaining_steps - 1)

    def _detonate(center: Position):
        """Start a bomb detonation at the center position."""

        # At the center, the bomb explodes in all 4 directions
        add_flame(center, {Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT})

        # Propagate flames outward in each direction
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            next_pos = center.get_new_position_from(direction)
            if terrain.is_valid_position(next_pos):
                _propagate(next_pos, direction, BOMB_SIZE)

    # Start the detonation if the starting position actually contains a bomb
    if terrain.get_token(pos) == Token.BOMB:
        _detonate(pos)

    # Return all the updates (flames, destroyed walls)
    return changes


# ============================================================================
# Configuration Settings -
# YOU MAY MODIFY THIS SECTION
# ============================================================================

DEFAULT_SETTINGS: dict[str, Any] = {
    "scale": 50,                            # pixels per unit
    "bomb_sprite": "assets/bomb-big.png",
    "terrain_sprite": "assets/land.png",    # image of what the land looks like
    "flame_sprite": "assets/flame.png",        # goal image
    "terrain_file": "blank_medium.txt",# which terrain do you want to navigate
}


# ================================================================================
# Graphics, don't modify

def draw(settings: dict[str, Any], terrain: Terrain, flames: dict[Position, tuple[int, int]]):

    pygame.init()
    screen = pygame.display.set_mode((terrain.width * settings["scale"], terrain.height * settings["scale"]),  HWSURFACE | RESIZABLE | DOUBLEBUF)

    # create caption
    pygame.display.set_caption(f"Bombs!")

    terrain_surface: TerrainSurface = TerrainSurface(
        TerrainSprite(settings["terrain_sprite"], settings["scale"], settings["scale"]),
        terrain,
        settings["scale"]
    )

    bomb_sprite = BombSprite(settings["bomb_sprite"], settings["scale"], settings["scale"])
    flame_sprites = FlameSprite(settings["flame_sprite"], settings["scale"], settings["scale"])

    game_over: bool = False
    while not game_over:

        terrain_surface.draw(screen)

        for pos, token in terrain:
            if token == Token.BOMB:
                x_anim, y_anim = pos.x, pos.y
                x_anim *= settings["scale"]
                y_anim *= settings["scale"]
                bomb = Bomb(bomb_sprite, Position(x_anim, y_anim))
                bomb.draw(screen, 123123)
            elif token in Token.FLAMES:
                x_anim, y_anim = pos.x, pos.y
                x_anim *= settings["scale"]
                y_anim *= settings["scale"]
                flame = Flame(flame_sprites, Position(x_anim, y_anim), token)
                flame.draw(screen)

        pygame.display.flip()

        e = pygame.event.poll()
        if e.type == pygame.QUIT:
            pygame.quit()
            game_over = True
        if e.type == pygame.MOUSEBUTTONUP:

            # remove all flames
            terrain.update({ pos: Token.EMPTY for pos, _ in filter(lambda t: t[1] in Token.FLAMES, terrain)})
                
            
            x, y = pygame.mouse.get_pos()
            x_pos = x // settings["scale"]
            y_pos = y // settings["scale"]
            print(f"Detonating: {(x_pos, y_pos)}")
            
            pressed = pygame.key.get_pressed()

            # b + click makes a bomb
            if pressed[pygame.locals.K_b]:
                terrain.update({Position(x_pos, y_pos): Token.BOMB})

            # w + click makes a wall
            elif pressed[pygame.locals.K_w]:
                terrain.update({Position(x_pos, y_pos): Token.WALL})
                terrain_surface: TerrainSurface = TerrainSurface(
                    TerrainSprite(settings["terrain_sprite"], settings["scale"], settings["scale"]),
                    terrain,
                    settings["scale"]
                )

            # otherwise detonate
            else:
                changes = detonate(Position(x_pos, y_pos), terrain)
                print(changes)
                terrain.update(changes)
                terrain_surface: TerrainSurface = TerrainSurface(
                    TerrainSprite(settings["terrain_sprite"], settings["scale"], settings["scale"]),
                    terrain,
                    settings["scale"]
                )
                
            print(terrain)

            



def main():

    terrain_file = DEFAULT_SETTINGS["terrain_file"]
    if len(sys.argv) >= 2:
        terrain_file = sys.argv[1]
    
    
    terrain: Terrain = Terrain(file_name = terrain_file, start_goal_required = False)
    print(terrain)
    flames={}
    draw(DEFAULT_SETTINGS, terrain, flames)

if __name__ == "__main__":
    main()
