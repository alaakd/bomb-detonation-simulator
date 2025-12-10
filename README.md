# Assignment 5: Bombs!

The terrain is now filled with bombs!

![](images/7-1.png)

## Bombs

When a bomb detonates it's blast shoots out in the up, down, left, and
right directions. The bomb's "radius" is the number of steps from the
center of the blast. It is set to a constant of 3 in the starter, but
can be changed.

### Basic bomb detonation

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/1-before.png) | $\rightarrow$ | ![](images/1-detonated.png) |

### Bombs should detonate immediately if struck the blast of another bomb

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/2-before.png) | $\rightarrow$ | ![](images/2-detonated.png) |

### Bombs should detonate immediately if struck the blast of another bomb

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/3-before.png) | $\rightarrow$ | ![](images/3-detonated.png) |

## Walls

A wall is an entity that can be destroyed by a bomb blast:

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/4-before.png) | $\rightarrow$ | ![](images/4-detonated.png) |

Notice that the blast stops once it hits the wall and does not extend
past:

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/5-before.png) | $\rightarrow$ | ![](images/5-detonated.png) |

This is true no matter how many bombs explode at the same time: chained
bombs explode at the same moment:

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/6-before.png) | $\rightarrow$ | ![](images/6-detonated.png) |

# Representing flames

When bomb detonation crosses a terrain cell, the *path* of the
detonation will combine with paths from other detonations. For example,
if a cell has a horizontal flame `─` and a detonation crosses it with a
vertical flame `|` then the combined flame is `┼`.

There are 16 possible flame tokens, based on the explosion paths that
have crossed the cell.

| Down  | Up    | Right | Left  | Token |                            |
|-------|-------|-------|-------|-------|----------------------------|
| False | False | False | False | ` `   | ![](images/flame_0000.png) |
| False | False | False | True  | `╴`   | ![](images/flame_0001.png) |
| False | False | True  | False | `╶`   | ![](images/flame_0010.png) |
| False | False | True  | True  | `─`   | ![](images/flame_0011.png) |
| False | True  | False | False | `╵`   | ![](images/flame_0100.png) |
| False | True  | False | True  | `┘`   | ![](images/flame_0101.png) |
| False | True  | True  | False | `└`   | ![](images/flame_0110.png) |
| False | True  | True  | True  | `┴`   | ![](images/flame_0111.png) |
| True  | False | False | False | `╷`   | ![](images/flame_1000.png) |
| True  | False | False | True  | `┐`   | ![](images/flame_1001.png) |
| True  | False | True  | False | `┌`   | ![](images/flame_1010.png) |
| True  | False | True  | True  | `┬`   | ![](images/flame_1011.png) |
| True  | True  | False | False | `│`   | ![](images/flame_1100.png) |
| True  | True  | False | True  | `┤`   | ![](images/flame_1101.png) |
| True  | True  | True  | False | `├`   | ![](images/flame_1110.png) |
| True  | True  | True  | True  | `┼`   | ![](images/flame_1111.png) |

The graphical terrain uses different sprites to display the terrains.

The dictionary `flame_tokens` stores the tokens by a *binary*
representation of the directions. Hint: how can you use the bit-wise
"or" operator (`|`) in your code?

## Example

Note when these bombs detonate, the sprites where they join are
connected:

|                          |               |                             |
|--------------------------|---------------|-----------------------------|
| ![](images/8-before.png) | $\rightarrow$ | ![](images/8-detonated.png) |

# Requirements

Implement a function:

``` python
def detonate(pos: Position, terrain: Terrain) -> dict[Position, Token]:
```

the will detonate the bomb at `pos` and return a dictionary of the
positions whose tokens will be updated. For example, the detonation
`(6, 4)`:

![](images/7-2.png)

will return

``` python
{
    (4, 5): Token.EMPTY,
    (3, 4): Token.EMPTY,
    (6, 5): Token.EMPTY,
    (4, 3): Token.EMPTY,
    (6, 3): Token.EMPTY,
    (6, 4): Token("┼"),
    (7, 4): Token("─"),
    (8, 4): Token("─"),
    (9, 4): Token("╴"),
    (5, 4): Token("─"),
    (4, 4): Token("┼")
}
```

The `detonate` function must be implemented *recursively*, using a
recursive helper function. You can decide which parameters are necessary
for your function.

Additional requirements:

1.  Do not modify the `terrain` in your functions. Your function should
    return the dictionary containing the updated tokens.

2.  Do not use global variables, instead pass extra parameters in your
    recursive function.

# Graphics

The graphical version of the terrain is clickable:

|               |                         |
|---------------|-------------------------|
| **click**     | detonate a bomb.        |
| **w + click** | add a wall at position. |
| **b + click** | add a bomb at position. |

Have fun!
