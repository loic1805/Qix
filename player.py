"""Gestion des joueurs de Qix."""

from time import monotonic
from affichage import cercle, polygone, rectangle


def _draw_avatar(x, y, cell_size, helmet_color, suit_color, visor_color, aura_color=None):
    """Dessine l'avatar commun au joueur humain et à l'IA."""
    if aura_color is not None:
        aura = [
            (x, y - cell_size * 0.58),
            (x + cell_size * 0.58, y),
            (x, y + cell_size * 0.58),
            (x - cell_size * 0.58, y),
        ]
        polygone(aura, couleur=aura_color, remplissage=aura_color, epaisseur=1)

    cercle(
        x,
        y - cell_size * 0.22,
        cell_size * 0.24,
        couleur="white",
        remplissage=helmet_color,
        epaisseur=1,
    )

    rectangle(
        x - cell_size * 0.15,
        y - cell_size * 0.29,
        x + cell_size * 0.15,
        y - cell_size * 0.18,
        couleur="white",
        remplissage=visor_color,
        epaisseur=1,
    )

    body = [
        (x - cell_size * 0.23, y - cell_size * 0.02),
        (x + cell_size * 0.23, y - cell_size * 0.02),
        (x + cell_size * 0.16, y + cell_size * 0.29),
        (x - cell_size * 0.16, y + cell_size * 0.29),
    ]
    polygone(body, couleur="white", remplissage=suit_color, epaisseur=1)

    rectangle(
        x - cell_size * 0.30,
        y + cell_size * 0.03,
        x - cell_size * 0.19,
        y + cell_size * 0.20,
        couleur="white",
        remplissage=helmet_color,
        epaisseur=1,
    )
    rectangle(
        x + cell_size * 0.19,
        y + cell_size * 0.03,
        x + cell_size * 0.30,
        y + cell_size * 0.20,
        couleur="white",
        remplissage=helmet_color,
        epaisseur=1,
    )

    rectangle(
        x - cell_size * 0.13,
        y + cell_size * 0.29,
        x - cell_size * 0.03,
        y + cell_size * 0.44,
        couleur="white",
        remplissage="#343a40",
        epaisseur=1,
    )
    rectangle(
        x + cell_size * 0.03,
        y + cell_size * 0.29,
        x + cell_size * 0.13,
        y + cell_size * 0.44,
        couleur="white",
        remplissage="#343a40",
        epaisseur=1,
    )


class Player:
    """Représente le joueur, ses vies et son chemin en cours."""

    def __init__(self, start_position, theme="yellow"):
        self.start_position = start_position
        self.theme = theme
        self.position = start_position
        self.anchor_position = start_position
        self.trail = []
        self.lives = 3
        self.drawing = False
        self.speed_mode = "slow"
        self.last_move = 0.0
        self.invincible_until = 0.0

    def start_drawing(self):
        self.drawing = True
        self.anchor_position = self.position
        self.trail = []

    def stop_drawing(self):
        self.drawing = False
        self.trail = []

    def add_to_trail(self, position):
        if position in self.trail:
            return False
        self.trail.append(position)
        return True

    def lose_life(self):
        self.lives -= 1
        self.position = self.anchor_position
        self.stop_drawing()

    def reset_for_level(self, start_position):
        self.start_position = start_position
        self.position = start_position
        self.anchor_position = start_position
        self.trail = []
        self.drawing = False
        self.last_move = 0.0
        self.invincible_until = 0.0

    def toggle_speed(self):
        if not self.drawing:
            self.speed_mode = "fast" if self.speed_mode == "slow" else "slow"

    def move_delay(self):
        if not self.drawing:
            return 0.055
        if self.speed_mode == "fast":
            return 0.035
        return 0.075

    def can_move(self):
        now = monotonic()
        if now - self.last_move < self.move_delay():
            return False
        self.last_move = now
        return True

    def make_invincible(self, seconds=3.0):
        self.invincible_until = monotonic() + seconds

    def is_invincible(self):
        return monotonic() < self.invincible_until

    def invincibility_remaining(self):
        return max(0.0, self.invincible_until - monotonic())

    def score_multiplier(self):
        return 250 if self.speed_mode == "fast" else 500

    def draw(self, board_left, board_top, cell_size):
        col, row = self.position
        x = board_left + col * cell_size + cell_size / 2
        y = board_top + row * cell_size + cell_size / 2

        if self.theme == "violet":
            if self.is_invincible():
                _draw_avatar(x, y, cell_size, "#3c096c", "#c77dff", "#f3d5ff", "#e0aaff")
            else:
                _draw_avatar(x, y, cell_size, "#3c096c", "#b45cff", "#e0aaff")
            return

        if self.is_invincible():
            _draw_avatar(x, y, cell_size, "#264653", "#ff9f1c", "#d9f0ff", "#ffee32")
        else:
            _draw_avatar(x, y, cell_size, "#1d3557", "#ffb703", "#8ecae6")


class AIPlayer:
    """Joueur virtuel qui respecte les mêmes déplacements que le joueur humain."""

    def __init__(self, start_position):
        self.start_position = start_position
        self.position = start_position
        self.anchor_position = start_position
        self.trail = []
        self.lives = 3
        self.drawing = False
        self.walk_route = []
        self.draw_route = []
        self.last_move = 0.0
        self.last_action = monotonic()
        self.move_delay = 0.065
        self.action_delay = 0.8

    def reset_for_level(self, start_position, level=1, keep_lives=False):
        lives = self.lives
        self.start_position = start_position
        self.position = start_position
        self.anchor_position = start_position
        self.trail = []
        self.drawing = False
        self.walk_route = []
        self.draw_route = []
        self.last_move = 0.0
        self.last_action = monotonic()
        self.move_delay = max(0.040, 0.065 - (level - 1) * 0.002)
        self.action_delay = max(0.35, 0.8 - (level - 1) * 0.04)
        self.lives = lives if keep_lives else 3

    def ready(self):
        return (
            not self.drawing
            and not self.walk_route
            and not self.draw_route
            and monotonic() - self.last_action >= self.action_delay
        )

    def can_move(self):
        now = monotonic()
        if now - self.last_move < self.move_delay:
            return False
        self.last_move = now
        return True

    def start_turn(self, walk_route, draw_route):
        self.walk_route = list(walk_route)
        self.draw_route = list(draw_route)
        self.drawing = False

    def begin_drawing(self):
        self.drawing = True
        self.anchor_position = self.position
        self.trail = []

    def finish_turn(self):
        self.drawing = False
        self.trail = []
        self.walk_route = []
        self.draw_route = []
        self.last_action = monotonic()

    def lose_life(self):
        self.lives -= 1
        self.position = self.anchor_position
        self.finish_turn()

    def draw(self, board_left, board_top, cell_size):
        """Même avatar que le joueur humain, avec une palette violette."""
        col, row = self.position
        x = board_left + col * cell_size + cell_size / 2
        y = board_top + row * cell_size + cell_size / 2
        _draw_avatar(x, y, cell_size, "#3c096c", "#b45cff", "#e0aaff")
