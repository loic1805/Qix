"""Gestion des Sparx qui circulent sur les frontières."""

from time import monotonic
from fltk import cercle, polygone, rectangle


DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class Sparx:
    """Ennemi qui suit les cases sûres du contour."""

    def __init__(self, position, previous_position, clockwise=True, move_delay=0.10):
        self.position = position
        self.previous_position = previous_position
        self.clockwise = clockwise
        self.move_delay = move_delay
        self.last_move = 0.0

    def update(self, board):
        """Avance d'une case sur le contour lorsque le délai est écoulé."""
        now = monotonic()
        if now - self.last_move < self.move_delay:
            return

        self.last_move = now
        next_position = self._choose_next_position(board)
        if next_position is None:
            return

        self.previous_position = self.position
        self.position = next_position

    def _choose_next_position(self, board):
        neighbors = board.safe_neighbors(self.position)
        if not neighbors:
            return None

        if len(neighbors) == 1:
            return neighbors[0]

        forward = self._current_direction()
        priorities = self._direction_priorities(forward)

        for direction in priorities:
            candidate = (
                self.position[0] + direction[0],
                self.position[1] + direction[1],
            )
            if candidate in neighbors and candidate != self.previous_position:
                return candidate

        for candidate in neighbors:
            if candidate != self.previous_position:
                return candidate

        return self.previous_position

    def _current_direction(self):
        dx = self.position[0] - self.previous_position[0]
        dy = self.position[1] - self.previous_position[1]
        if (dx, dy) in DIRECTIONS:
            return dx, dy
        return (1, 0)

    def _direction_priorities(self, forward):
        index = DIRECTIONS.index(forward)
        turns = [1, 0, -1, 2] if self.clockwise else [-1, 0, 1, 2]
        return [DIRECTIONS[(index + turn) % 4] for turn in turns]

    def touches(self, position):
        """Renvoie True si le Sparx se trouve sur la case donnée."""
        return self.position == position

    def draw(self, board_left, board_top, cell_size):
        """Dessine un Sparx comme un fantôme d'arcade."""
        col, row = self.position
        x = board_left + col * cell_size + cell_size / 2
        y = board_top + row * cell_size + cell_size / 2

        width = cell_size * 1.15
        top = y - cell_size * 0.55
        bottom = y + cell_size * 0.50
        left = x - width / 2
        right = x + width / 2

        cercle(x, top + cell_size * 0.32, cell_size * 0.52,
               couleur="#ffccd5", remplissage="#ef233c", epaisseur=2)
        rectangle(left, top + cell_size * 0.20, right, bottom,
                  couleur="#ef233c", remplissage="#ef233c", epaisseur=1)

        feet = [
            (left, bottom),
            (left + width * 0.20, bottom - cell_size * 0.18),
            (left + width * 0.40, bottom),
            (left + width * 0.60, bottom - cell_size * 0.18),
            (left + width * 0.80, bottom),
            (right, bottom - cell_size * 0.18),
            (right, bottom),
        ]
        polygone(feet, couleur="#ef233c", remplissage="#ef233c", epaisseur=1)

        eye_y = y - cell_size * 0.22
        cercle(x - cell_size * 0.19, eye_y, cell_size * 0.13,
               couleur="white", remplissage="white", epaisseur=1)
        cercle(x + cell_size * 0.19, eye_y, cell_size * 0.13,
               couleur="white", remplissage="white", epaisseur=1)
        cercle(x - cell_size * 0.15, eye_y, cell_size * 0.05,
               couleur="#111111", remplissage="#111111", epaisseur=1)
        cercle(x + cell_size * 0.15, eye_y, cell_size * 0.05,
               couleur="#111111", remplissage="#111111", epaisseur=1)
