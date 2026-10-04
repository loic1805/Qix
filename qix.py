"""Gestion de l'ennemi Qix."""

from math import cos, pi, sin
from random import choice, random
from time import monotonic
from affichage import ligne


DIRECTIONS = [
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
]


class Qix:
    """Ennemi qui se déplace aléatoirement dans la zone libre."""

    def __init__(self, position, move_delay=0.12):
        self.position = position
        self.direction = choice(DIRECTIONS)
        self.move_delay = move_delay
        self.last_move = 0.0
        self.angle = 0.0

    def update(self, board):
        """Déplace le Qix et renvoie le propriétaire d'un chemin touché."""
        now = monotonic()
        self.angle += 0.12

        if now - self.last_move < self.move_delay:
            return None

        self.last_move = now

        if random() < 0.18:
            self.direction = choice(DIRECTIONS)

        dx, dy = self.direction
        target = (self.position[0] + dx, self.position[1] + dy)
        owner = board.trail_owner(target)

        if owner is not None:
            return owner

        if board.is_qix_free(target):
            self.position = target
            return None

        choices = []
        for direction in DIRECTIONS:
            dx, dy = direction
            candidate = (self.position[0] + dx, self.position[1] + dy)
            owner = board.trail_owner(candidate)
            if owner is not None:
                return owner
            if board.is_qix_free(candidate):
                choices.append(direction)

        if choices:
            self.direction = choice(choices)
            dx, dy = self.direction
            self.position = (self.position[0] + dx, self.position[1] + dy)

        return None

    def draw(self, board_left, board_top, cell_size):
        """Dessine le Qix comme un faisceau de lignes à l'ancienne."""
        col, row = self.position
        cx = board_left + col * cell_size + cell_size / 2
        cy = board_top + row * cell_size + cell_size / 2

        for offset in (-0.34, 0.0, 0.34):
            angle = self.angle + offset
            x1 = cx + cos(angle) * cell_size * 1.25
            y1 = cy + sin(angle) * cell_size * 1.25
            x2 = cx - cos(angle) * cell_size * 1.25
            y2 = cy - sin(angle) * cell_size * 1.25
            ligne(x1, y1, x2, y2, couleur="#ff1744", epaisseur=2)

        for offset in (-0.16, 0.16):
            angle = -self.angle * 1.15 + offset
            x1 = cx + cos(angle) * cell_size * 0.95
            y1 = cy + sin(angle) * cell_size * 0.95
            x2 = cx - cos(angle) * cell_size * 0.95
            y2 = cy - sin(angle) * cell_size * 0.95
            ligne(x1, y1, x2, y2, couleur="#651fff", epaisseur=2)
