"""Plateau, écrans et logique principale du jeu Qix."""

import random
from collections import deque
from time import monotonic
from fltk import (
    abscisse,
    donne_ev,
    efface_tout,
    mise_a_jour,
    ordonnee,
    touche,
    touche_pressee,
    type_ev,
)
from affichage import adapte_affichage, cercle, ligne, polygone, position_logique, rectangle, texte
from player import AIPlayer, Player
from qix import Qix
from sparks import Sparx


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 900

CELL_SIZE = 22
COLS = 52
ROWS = 32
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE
BOARD_LEFT = (WINDOW_WIDTH - BOARD_WIDTH) // 2
BOARD_TOP = 132

ARCADE_FONT = "Courier"

DIRECTIONS = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
}

PLAYER2_DIRECTIONS = {
    ("z", "Z"): (0, -1),
    ("s", "S"): (0, 1),
    ("q", "Q"): (-1, 0),
    ("d", "D"): (1, 0),
}

# Formes d'obstacles : coordonnées relatives sur la grille.
OBSTACLE_PATTERNS = {
    "square": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "bar_h": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "bar_v": [(0, 0), (0, 1), (0, 2), (0, 3)],
    "block": [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)],
    "l_shape": [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
    "t_shape": [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
    "stair": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    "zigzag": [(0, 1), (1, 0), (1, 1), (2, 0), (3, 0)],
}

# Ancrages disponibles pour répartir les obstacles sur l'arène.
OBSTACLE_SLOTS = [
    (8, 7, "block"),
    (19, 5, "bar_v"),
    (36, 7, "block"),
    (12, 21, "square"),
    (29, 23, "bar_h"),
    (42, 19, "square"),
    (24, 10, "l_shape"),
    (6, 15, "bar_v"),
    (33, 14, "t_shape"),
    (16, 12, "stair"),
    (39, 24, "zigzag"),
    (22, 25, "bar_h"),
]

MENU_LEFT = 390
MENU_RIGHT = 890
MENU_BUTTONS = {
    "rules": (MENU_LEFT, 355, MENU_RIGHT, 410),
    "single": (MENU_LEFT, 425, MENU_RIGHT, 480),
    "ai": (MENU_LEFT, 495, MENU_RIGHT, 550),
    "two": (MENU_LEFT, 565, MENU_RIGHT, 620),
}

RULES_BACK_BUTTON = (70, 810, 340, 865)
RULES_PLAY_BUTTON = (940, 810, 1210, 865)
GAME_INFO_BUTTON = (1080, 18, 1120, 52)
GAME_MENU_BUTTON = (1130, 18, 1235, 52)
INFO_CLOSE_BUTTON = (505, 690, 775, 740)



class GameBoard:
    """Contient l'état du jeu et coordonne les différents écrans."""

    def __init__(self):
        self.screen = "menu"
        self.level = 1
        self.score = 0
        self.paused = False
        self.game_over = False
        self.message = ""
        self.message_until = 0.0
        self.menu_message = ""
        self.menu_message_until = 0.0
        self.mode = "single"
        self.info_open = False
        self.game_over_text = "GAME OVER - R POUR RECOMMENCER"

        self.safe_cells = set()
        self.filled_cells = set()
        self.ai_filled_cells = set()
        self.player2_filled_cells = set()
        self.obstacles = set()
        self.dangerous_obstacles = set()
        self.obstacle_groups = []
        self.apple = None

        self.player = Player(self.start_position())
        self.player2 = Player(self.player2_start_position(), theme="violet")
        self.ai_player = AIPlayer(self.ai_start_position())
        self.player1_rounds = 0
        self.player2_rounds = 0
        self.qix = None
        self.sparx = []
        self._reset_board()

    def start_position(self):
        """Position de départ du joueur 1 sur le bord inférieur."""
        if self.mode in ("ai", "two"):
            return COLS // 3, ROWS - 1
        return COLS // 2, ROWS - 1

    def player2_start_position(self):
        """Position de départ du joueur 2 sur le bord inférieur."""
        return 2 * COLS // 3, ROWS - 1

    def ai_start_position(self):
        """Position de départ de l'IA sur le bord inférieur, à droite du joueur."""
        return 2 * COLS // 3, ROWS - 1

    def update(self):
        """Met à jour une image du programme."""
        if not self._handle_events():
            return False

        if self.screen == "playing" and not self.paused and not self.game_over and not self.info_open:
            self._move_player()
            if self.mode == "ai":
                self._update_ai()
            elif self.mode == "two":
                self._move_player2()
            self._update_enemies()
            self._check_bonus()
            self._check_obstacle_danger()
            self._check_enemy_collisions()

        self.draw()
        mise_a_jour()
        return True

    def _handle_events(self):
        while True:
            event = donne_ev()
            if event is None:
                break

            event_type = type_ev(event)
            if event_type == "Quitte":
                return False

            if event_type == "ClicGauche":
                self._handle_click(*position_logique(abscisse(event), ordonnee(event)))
                continue

            if event_type != "Touche":
                continue

            key = touche(event)

            if self.screen == "menu":
                if key in ("Escape", "q", "Q"):
                    return False
                continue

            if self.screen == "rules":
                if key in ("Escape", "BackSpace"):
                    self.screen = "menu"
                elif key == "Return":
                    self._start_single_player()
                continue

            if self.info_open:
                if key in ("Escape", "BackSpace", "Return", "i", "I"):
                    self.info_open = False
                continue

            if key in ("q", "Q") and self.mode != "two":
                return False

            if key == "Escape":
                self.paused = False
                self.screen = "menu"
                continue

            if key in ("p", "P") and not self.game_over:
                self.paused = not self.paused

            if key == "space" and not self.paused and not self.game_over:
                self.player.toggle_speed()

            if key in ("e", "E") and self.mode == "two" and not self.paused and not self.game_over:
                self.player2.toggle_speed()

            if key in ("r", "R") and self.game_over:
                self._restart_game()

        return True

    def _handle_click(self, x, y):
        if x is None or y is None:
            return

        if self.screen == "menu":
            if self._inside_button(x, y, MENU_BUTTONS["rules"]):
                self.screen = "rules"
            elif self._inside_button(x, y, MENU_BUTTONS["single"]):
                self._start_single_player()
            elif self._inside_button(x, y, MENU_BUTTONS["ai"]):
                self._start_ai_game()
            elif self._inside_button(x, y, MENU_BUTTONS["two"]):
                self._start_two_player_game()
            return

        if self.screen == "rules":
            if self._inside_button(x, y, RULES_BACK_BUTTON):
                self.screen = "menu"
            elif self._inside_button(x, y, RULES_PLAY_BUTTON):
                self._start_single_player()
            return

        if self.screen == "playing":
            if self.info_open:
                if self._inside_button(x, y, INFO_CLOSE_BUTTON):
                    self.info_open = False
                return

            if self._inside_button(x, y, GAME_INFO_BUTTON):
                self.info_open = True
                return

            if self._inside_button(x, y, GAME_MENU_BUTTON):
                self.paused = False
                self.info_open = False
                self.screen = "menu"

    def _inside_button(self, x, y, button):
        x1, y1, x2, y2 = button
        return x1 <= x <= x2 and y1 <= y <= y2

    def _show_coming_soon(self, mode):
        self.menu_message = f"{mode} - BIENTOT DISPONIBLE"
        self.menu_message_until = monotonic() + 2.0

    def _start_single_player(self):
        self.mode = "single"
        self._restart_game()
        self.screen = "playing"

    def _start_ai_game(self):
        self.mode = "ai"
        self._restart_game()
        self.screen = "playing"

    def _start_two_player_game(self):
        self.mode = "two"
        self._restart_game()
        self.screen = "playing"

    def _move_player(self):
        direction = self._pressed_direction()
        if direction is None or not self.player.can_move():
            return

        dx, dy = direction
        current = self.player.position
        target = current[0] + dx, current[1] + dy

        if not self.inside(target):
            return
        if self.mode == "two" and target == self.player2.position:
            return

        if self.player.drawing:
            self._move_drawing_player(target)
        else:
            self._move_safe_player(target)

    def _pressed_direction(self):
        for key, direction in DIRECTIONS.items():
            if touche_pressee(key):
                return direction
        return None

    def _move_player2(self):
        """Déplace le joueur 2 avec ZQSD."""
        direction = self._pressed_direction_player2()
        if direction is None or not self.player2.can_move():
            return

        dx, dy = direction
        current = self.player2.position
        target = current[0] + dx, current[1] + dy

        if not self.inside(target) or target == self.player.position:
            return

        if self.player2.drawing:
            self._move_drawing_player2(target)
        else:
            self._move_safe_player2(target)

    def _pressed_direction_player2(self):
        for keys, direction in PLAYER2_DIRECTIONS.items():
            if any(touche_pressee(key) for key in keys):
                return direction
        return None

    def _player2_draw_pressed(self):
        return touche_pressee("Shift_L") or touche_pressee("Shift_R")

    def _move_safe_player2(self, target):
        if target in self.safe_cells:
            self.player2.position = target
            return

        if self._player2_draw_pressed() and self.is_free_for_player2(target):
            self.player2.start_drawing()
            self.player2.position = target
            self.player2.add_to_trail(target)

    def _move_drawing_player2(self, target):
        if target in self.player2.trail:
            self._player2_hit()
            return

        if target in self.player.trail:
            self._player2_hit("CHEMIN J1")
            return

        if target in self.dangerous_obstacles:
            self._player2_hit("OBSTACLE DANGEREUX")
            return

        if target in self.safe_cells:
            self.player2.position = target
            self._close_player2_trail()
            return

        if self.is_free_for_player2(target):
            self.player2.position = target
            self.player2.add_to_trail(target)
            if self._touches_dangerous_obstacle(target):
                self._player2_hit("OBSTACLE DANGEREUX")

    def _move_safe_player(self, target):
        if target in self.safe_cells:
            self.player.position = target
            return

        if touche_pressee("Return") and self.is_free(target):
            self.player.start_drawing()
            self.player.position = target
            self.player.add_to_trail(target)

    def _move_drawing_player(self, target):
        if target in self.player.trail:
            self._player_hit()
            return

        if self.mode == "ai" and target in self.ai_player.trail:
            self._player_hit("CHEMIN DE L'IA")
            return
        if self.mode == "two" and target in self.player2.trail:
            self._player_hit("CHEMIN J2")
            return

        if target in self.dangerous_obstacles:
            self._player_hit("OBSTACLE DANGEREUX")
            return

        if target in self.safe_cells:
            self.player.position = target
            self._close_trail()
            return

        if self.is_free(target):
            self.player.position = target
            self.player.add_to_trail(target)
            if self._touches_dangerous_obstacle(target):
                self._player_hit("OBSTACLE DANGEREUX")

    def _close_trail(self):
        if not self.player.trail:
            self.player.stop_drawing()
            return

        captured_cells = self._capture_cells(self.player.trail, self.filled_cells)
        self.score += len(captured_cells) * self.player.score_multiplier()
        self.player.stop_drawing()
        self._spawn_apple_if_needed()

        if self.mode == "two":
            if self.player2.drawing and (
                self.player2.position in captured_cells
                or any(cell in captured_cells for cell in self.player2.trail)
            ):
                self._player2_hit("PIEGE PAR J1")
            self._check_two_round_end()
        elif self.mode == "ai":
            self._check_ai_round_end()
        elif self.captured_percentage() >= 75.0:
            self.level += 1
            self.message = f"NIVEAU {self.level}"
            self.message_until = monotonic() + 1.2
            self._reset_board(keep_lives=True)

    def _close_player2_trail(self):
        if not self.player2.trail:
            self.player2.stop_drawing()
            return

        captured_cells = self._capture_cells(self.player2.trail, self.player2_filled_cells)
        self.player2.stop_drawing()

        if self.player.drawing and (
            self.player.position in captured_cells
            or any(cell in captured_cells for cell in self.player.trail)
        ):
            self._player_hit("PIEGE PAR J2")

        self._check_two_round_end()

    def _capture_cells(self, trail_list, target_cells):
        """Capture la zone séparée du Qix par un chemin fermé."""
        trail = set(trail_list)
        reachable = self._reachable_from_qix(trail)
        captured = set()

        for row in range(1, ROWS - 1):
            for col in range(1, COLS - 1):
                cell = (col, row)
                if cell in self.safe_cells:
                    continue
                if cell in self.filled_cells or cell in self.ai_filled_cells or cell in self.player2_filled_cells:
                    continue
                if cell in trail or cell not in reachable:
                    target_cells.add(cell)
                    captured.add(cell)

        self.safe_cells.update(trail)
        return captured

    def _reachable_from_qix(self, trail):
        start = self.qix.position
        queue = deque([start])
        visited = {start}

        while queue:
            col, row = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = col + dx, row + dy
                if neighbor in visited:
                    continue
                if not self.inside(neighbor):
                    continue
                if neighbor in self.safe_cells:
                    continue
                if neighbor in trail:
                    continue
                if neighbor in self.filled_cells or neighbor in self.ai_filled_cells or neighbor in self.player2_filled_cells:
                    continue
                if self.mode == "ai" and neighbor in self.ai_player.trail:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)

        return visited

    def _update_ai(self):
        """Fait jouer l'IA avec les mêmes règles de déplacement que le joueur."""
        if not self.ai_player.can_move():
            return

        if self.ai_player.walk_route:
            target = self.ai_player.walk_route.pop(0)
            if target not in self.safe_cells:
                self.ai_player.finish_turn()
                return
            self.ai_player.position = target

            if not self.ai_player.walk_route and self.ai_player.draw_route:
                self.ai_player.begin_drawing()
            return

        if self.ai_player.drawing:
            if not self.ai_player.draw_route:
                self.ai_player.finish_turn()
                return

            target = self.ai_player.draw_route.pop(0)

            if target in self.player.trail:
                self._ai_hit("CHEMIN DU JOUEUR")
                return

            if target in self.safe_cells:
                self.ai_player.position = target
                self._close_ai_trail()
                return

            if not self._ai_can_draw_on(target):
                self.ai_player.finish_turn()
                return

            self.ai_player.position = target
            self.ai_player.trail.append(target)
            return

        if not self.ai_player.ready():
            return

        plan = self._build_ai_turn()
        if plan is None:
            self.ai_player.last_action = monotonic()
            return

        walk_route, draw_route = plan
        self.ai_player.start_turn(walk_route, draw_route)
        if not walk_route:
            self.ai_player.begin_drawing()

    def _build_ai_turn(self):
        """Choisit une frontière proche, puis un vrai chemin de capture."""
        anchors = list(self.safe_cells)
        random.shuffle(anchors)

        # L'IA joue localement : elle préfère une frontière proche de sa
        # position actuelle, tout en évitant de commencer trop près du Qix.
        def anchor_score(cell):
            distance_from_ai = abs(cell[0] - self.ai_player.position[0]) + abs(cell[1] - self.ai_player.position[1])
            distance_from_qix = abs(cell[0] - self.qix.position[0]) + abs(cell[1] - self.qix.position[1])
            return distance_from_ai * 2 - distance_from_qix * 0.35

        anchors.sort(key=anchor_score)

        for anchor in anchors[:110]:
            if anchor == self.player.position:
                continue

            draw_route = self._find_ai_drawing_route(anchor)
            if draw_route is None:
                continue

            walk_route = self._find_safe_route(self.ai_player.position, anchor)
            if walk_route is None:
                continue

            return walk_route, draw_route

        return None

    def _find_safe_route(self, start, goal):
        """Trouve un chemin sur les lignes blanches, comme le ferait un joueur."""
        if start == goal:
            return []
        if start not in self.safe_cells or goal not in self.safe_cells:
            return None

        queue = deque([start])
        parents = {start: None}

        while queue:
            current = queue.popleft()
            col, row = current

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = col + dx, row + dy
                if neighbor in parents or neighbor not in self.safe_cells:
                    continue
                parents[neighbor] = current
                if neighbor == goal:
                    return self._rebuild_path(parents, goal)[1:]
                queue.append(neighbor)

        return None

    def _find_ai_drawing_route(self, anchor):
        """Cherche un tracé en U, proche de ce que ferait un vrai joueur."""
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            first = anchor[0] + dx, anchor[1] + dy
            if not self._ai_can_draw_on(first):
                continue

            turns = [(-dy, dx), (dy, -dx)]
            random.shuffle(turns)

            for turn_x, turn_y in turns:
                for _ in range(8):
                    depth = random.randint(3, min(8, 5 + self.level))
                    width = random.randint(3, min(9, 6 + self.level))
                    path = []
                    current = anchor
                    valid = True

                    # Premier segment : l'IA quitte la frontière.
                    for _ in range(depth):
                        current = current[0] + dx, current[1] + dy
                        if not self._ai_can_draw_on(current) or current in path:
                            valid = False
                            break
                        path.append(current)
                    if not valid:
                        continue

                    # Deuxième segment : elle tourne à 90 degrés.
                    for _ in range(width):
                        current = current[0] + turn_x, current[1] + turn_y
                        if not self._ai_can_draw_on(current) or current in path:
                            valid = False
                            break
                        path.append(current)
                    if not valid:
                        continue

                    # Troisième segment : elle revient vers une frontière blanche.
                    for _ in range(depth + 4):
                        current = current[0] - dx, current[1] - dy

                        if current in self.safe_cells and current != anchor:
                            candidate = path + [current]
                            if self._estimated_ai_capture(candidate) >= 4:
                                return candidate
                            break

                        if not self._ai_can_draw_on(current) or current in path:
                            break
                        path.append(current)

        # Si aucun U n'est possible, on cherche un chemin libre plus général.
        return self._find_ai_fallback_route(anchor)

    def _find_ai_fallback_route(self, anchor):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        min_length = 7
        max_length = min(24, 15 + self.level)

        for dx, dy in directions:
            start = anchor[0] + dx, anchor[1] + dy
            if not self._ai_can_draw_on(start):
                continue

            queue = deque([start])
            parents = {start: None}
            distance = {start: 1}

            while queue:
                current = queue.popleft()
                current_distance = distance[current]
                if current_distance >= max_length:
                    continue

                col, row = current
                for step_x, step_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = col + step_x, row + step_y
                    next_distance = current_distance + 1

                    if neighbor in self.safe_cells:
                        if neighbor != anchor and next_distance >= min_length:
                            path = self._rebuild_path(parents, current) + [neighbor]
                            if self._estimated_ai_capture(path) >= 4:
                                return path
                        continue

                    if neighbor in parents or not self._ai_can_draw_on(neighbor):
                        continue

                    parents[neighbor] = current
                    distance[neighbor] = next_distance
                    queue.append(neighbor)

        return None

    def _estimated_ai_capture(self, path):
        """Estime la surface qu'un chemin de l'IA pourrait réellement fermer."""
        trail = set(path[:-1])
        reachable = self._reachable_from_qix(trail)
        captured = 0

        for row in range(1, ROWS - 1):
            for col in range(1, COLS - 1):
                cell = (col, row)
                if cell in self.safe_cells:
                    continue
                if cell in self.filled_cells or cell in self.ai_filled_cells:
                    continue
                if cell in trail or cell not in reachable:
                    captured += 1

        return captured

    def _rebuild_path(self, parents, end):
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = parents[current]
        path.reverse()
        return path

    def _ai_can_draw_on(self, cell):
        """Case autorisée pour le tracé de l'IA."""
        if not self.inside(cell):
            return False
        if cell in self.safe_cells:
            return False
        if cell in self.filled_cells or cell in self.ai_filled_cells:
            return False
        if cell in self.obstacles or cell in self.player.trail:
            return False
        if self._touches_dangerous_obstacle(cell):
            return False

        qix_col, qix_row = self.qix.position
        if abs(cell[0] - qix_col) <= 1 and abs(cell[1] - qix_row) <= 1:
            return False
        return True

    def _close_ai_trail(self):
        """Ferme le chemin de l'IA et capture la zone qui ne contient pas le Qix."""
        if not self.ai_player.trail:
            self.ai_player.finish_turn()
            return

        captured = self._capture_cells(self.ai_player.trail, self.ai_filled_cells)
        self.ai_player.finish_turn()

        if captured:
            self._check_ai_round_end()

    def _ai_hit(self, reason="VIE PERDUE"):
        """Applique à l'IA les mêmes conséquences qu'au joueur."""
        self.ai_player.lose_life()

        if self.ai_player.position not in self.safe_cells:
            self.ai_player.position = self.ai_start_position()

        if self.ai_player.lives <= 0:
            self.game_over = True
            self.game_over_text = "VOUS GAGNEZ - IA ELIMINEE"
            return

        self.message = f"IA : {reason}"
        self.message_until = monotonic() + 0.8

    def _check_ai_round_end(self):
        """Termine une manche quand joueur et IA ont capturé 75% au total."""
        if self.total_captured_percentage() < 75.0:
            return

        if self.captured_percentage() >= self.ai_captured_percentage():
            self.level += 1
            self.message = f"VOUS GAGNEZ - NIVEAU {self.level}"
            self.message_until = monotonic() + 1.5
            self._reset_board(keep_lives=True)
        else:
            self.game_over = True
            self.game_over_text = "L'IA GAGNE - R POUR RECOMMENCER"

    def _update_enemies(self):
        owner = self.qix.update(self)
        if owner == "player":
            self._player_hit()
            return
        if owner == "ai" and self.mode == "ai":
            self._ai_hit("QIX")
            return
        if owner == "player2" and self.mode == "two":
            self._player2_hit("QIX")
            return

        for enemy in self.sparx:
            enemy.update(self)

    def _check_enemy_collisions(self):
        if not self.player.is_invincible():
            for enemy in self.sparx:
                if enemy.touches(self.player.position):
                    self._player_hit("SPARX")
                    break

        if self.mode == "ai":
            for enemy in self.sparx:
                if enemy.touches(self.ai_player.position):
                    self._ai_hit("SPARX")
                    break

        if self.mode == "two" and not self.player2.is_invincible():
            for enemy in self.sparx:
                if enemy.touches(self.player2.position):
                    self._player2_hit("SPARX")
                    break

        qix_col, qix_row = self.qix.position
        if self.player.drawing and not self.player.is_invincible():
            for col, row in self.player.trail:
                if abs(qix_col - col) <= 1 and abs(qix_row - row) <= 1:
                    self._player_hit("QIX")
                    break

        if self.mode == "two" and self.player2.drawing and not self.player2.is_invincible():
            for col, row in self.player2.trail:
                if abs(qix_col - col) <= 1 and abs(qix_row - row) <= 1:
                    self._player2_hit("QIX")
                    break

    def _check_obstacle_danger(self):
        """Les obstacles dangereux peuvent toucher un joueur pendant son tracé."""
        if self.player.drawing and not self.player.is_invincible():
            if self._touches_dangerous_obstacle(self.player.position):
                self._player_hit("OBSTACLE DANGEREUX")

        if self.mode == "two" and self.player2.drawing and not self.player2.is_invincible():
            if self._touches_dangerous_obstacle(self.player2.position):
                self._player2_hit("OBSTACLE DANGEREUX")

    def _touches_dangerous_obstacle(self, cell):
        col, row = cell
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if (col + dx, row + dy) in self.dangerous_obstacles:
                return True
        return False

    def _player_hit(self, custom_message=None):
        if self.player.is_invincible():
            return

        self.player.lose_life()
        self.message = custom_message or "VIE PERDUE"
        self.message_until = monotonic() + 0.9

        if self.player.lives <= 0:
            self.game_over = True
            if self.mode == "two":
                self.game_over_text = "J2 GAGNE - J1 ELIMINE"
            else:
                self.game_over_text = "GAME OVER - R POUR RECOMMENCER"
            self.message = ""

    def _player2_hit(self, custom_message=None):
        if self.player2.is_invincible():
            return

        self.player2.lose_life()
        self.message = f"J2 : {custom_message or 'VIE PERDUE'}"
        self.message_until = monotonic() + 0.9

        if self.player2.lives <= 0:
            self.game_over = True
            self.game_over_text = "J1 GAGNE - J2 ELIMINE"
            self.message = ""

    def _check_two_round_end(self):
        """Passe au niveau suivant quand les deux joueurs ont capturé 75% au total."""
        if self.game_over or self.two_total_captured_percentage() < 75.0:
            return

        p1 = self.captured_percentage()
        p2 = self.player2_captured_percentage()

        if p1 > p2:
            self.player1_rounds += 1
            result = "J1 GAGNE LA MANCHE"
        elif p2 > p1:
            self.player2_rounds += 1
            result = "J2 GAGNE LA MANCHE"
        else:
            result = "MANCHE NULLE"

        self.level += 1
        self.message = f"{result} - NIVEAU {self.level}"
        self.message_until = monotonic() + 1.5
        self._reset_board(keep_lives=True)

    def _check_bonus(self):
        if self.apple is None:
            return

        if self.player.position == self.apple:
            self.player.make_invincible(3.0)
            self.score += 1000
            self.apple = None
            return

        if self.mode == "two" and self.player2.position == self.apple:
            self.player2.make_invincible(3.0)
            self.apple = None

    def _spawn_apple_if_needed(self):
        if self.apple is not None or random.random() > 0.45:
            return

        free_cells = []
        for row in range(1, ROWS - 1):
            for col in range(1, COLS - 1):
                cell = (col, row)
                if self.is_free(cell) and cell != self.qix.position:
                    free_cells.append(cell)

        if free_cells:
            self.apple = random.choice(free_cells)

    def _reset_board(self, keep_lives=False):
        lives = self.player.lives
        player2_lives = self.player2.lives
        speed_mode = self.player.speed_mode
        player2_speed_mode = self.player2.speed_mode

        self.safe_cells = set()
        self.filled_cells = set()
        self.ai_filled_cells = set()
        self.player2_filled_cells = set()
        self.obstacles = set()
        self.dangerous_obstacles = set()
        self.obstacle_groups = []
        self.apple = None

        self._create_obstacles()

        for col in range(COLS):
            self.safe_cells.add((col, 0))
            self.safe_cells.add((col, ROWS - 1))

        for row in range(ROWS):
            self.safe_cells.add((0, row))
            self.safe_cells.add((COLS - 1, row))

        start = self.start_position()
        self.player.reset_for_level(start)
        self.player.speed_mode = speed_mode
        if keep_lives:
            self.player.lives = lives

        self.player2.reset_for_level(self.player2_start_position())
        self.player2.speed_mode = player2_speed_mode
        if keep_lives:
            self.player2.lives = player2_lives

        self.ai_player.reset_for_level(self.ai_start_position(), self.level, keep_lives=keep_lives)

        qix_delay = max(0.055, 0.12 - (self.level - 1) * 0.008)
        sparx_delay = max(0.05, 0.10 - (self.level - 1) * 0.006)

        self.qix = Qix((COLS // 2, ROWS // 2), move_delay=qix_delay)

        top_middle = (COLS // 2, 0)
        self.sparx = [
            Sparx(top_middle, (top_middle[0] - 1, 0), True, sparx_delay),
            Sparx(top_middle, (top_middle[0] + 1, 0), False, sparx_delay),
        ]

        self._spawn_apple_if_needed()

    def _create_obstacles(self):
        """Construit des obstacles variés, plus nombreux et plus dangereux selon le niveau."""
        count = min(len(OBSTACLE_SLOTS), 6 + self.level)
        dangerous_count = min(max(0, self.level - 1), count // 2)

        for index, (anchor_col, anchor_row, pattern_name) in enumerate(OBSTACLE_SLOTS[:count]):
            pattern = list(OBSTACLE_PATTERNS[pattern_name])
            if self.level >= 3 and index % 3 == 0 and pattern_name in ("square", "bar_h", "bar_v"):
                pattern = pattern + [(cell[0] + 1, cell[1]) for cell in pattern[:1]]
            dangerous = index >= count - dangerous_count
            cells = set()
            for dx, dy in pattern:
                cell = (anchor_col + dx, anchor_row + dy)
                if self.inside(cell) and cell[1] not in (0, ROWS - 1):
                    self.obstacles.add(cell)
                    cells.add(cell)
                    if dangerous:
                        self.dangerous_obstacles.add(cell)

            if cells:
                self.obstacle_groups.append({
                    "cells": cells,
                    "dangerous": dangerous,
                    "pattern": pattern_name,
                })

    def _restart_game(self):
        self.level = 1
        self.score = 0
        self.paused = False
        self.game_over = False
        self.game_over_text = "GAME OVER - R POUR RECOMMENCER"
        self.info_open = False
        self.message = ""
        self.player = Player(self.start_position())
        self.player2 = Player(self.player2_start_position(), theme="violet")
        self.ai_player = AIPlayer(self.ai_start_position())
        self.player1_rounds = 0
        self.player2_rounds = 0
        self._reset_board()

    def inside(self, cell):
        col, row = cell
        return 0 <= col < COLS and 0 <= row < ROWS

    def is_free(self, cell):
        return (
            self.inside(cell)
            and cell not in self.safe_cells
            and cell not in self.filled_cells
            and cell not in self.ai_filled_cells
            and cell not in self.player2_filled_cells
            and cell not in self.player.trail
            and (self.mode != "ai" or cell not in self.ai_player.trail)
            and (self.mode != "two" or cell not in self.player2.trail)
            and cell not in self.obstacles
        )

    def is_free_for_player2(self, cell):
        return (
            self.inside(cell)
            and cell not in self.safe_cells
            and cell not in self.filled_cells
            and cell not in self.player2_filled_cells
            and cell not in self.ai_filled_cells
            and cell not in self.player.trail
            and cell not in self.player2.trail
            and cell not in self.obstacles
        )

    def is_qix_free(self, cell):
        """Le Qix ignore les obstacles mais ne traverse aucun chemin actif."""
        return (
            self.inside(cell)
            and cell not in self.safe_cells
            and cell not in self.filled_cells
            and cell not in self.ai_filled_cells
            and cell not in self.player2_filled_cells
            and cell not in self.player.trail
            and (self.mode != "ai" or cell not in self.ai_player.trail)
            and (self.mode != "two" or cell not in self.player2.trail)
        )

    def trail_owner(self, cell):
        if cell in self.player.trail:
            return "player"
        if self.mode == "ai" and cell in self.ai_player.trail:
            return "ai"
        if self.mode == "two" and cell in self.player2.trail:
            return "player2"
        return None

    def is_trail(self, cell):
        return self.trail_owner(cell) is not None

    def safe_neighbors(self, cell):
        col, row = cell
        neighbors = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = col + dx, row + dy
            if candidate in self.safe_cells:
                neighbors.append(candidate)
        return neighbors

    def captured_percentage(self):
        total = (COLS - 2) * (ROWS - 2)
        if total == 0:
            return 0.0
        return len(self.filled_cells) * 100 / total

    def ai_captured_percentage(self):
        total = (COLS - 2) * (ROWS - 2)
        if total == 0:
            return 0.0
        return len(self.ai_filled_cells) * 100 / total

    def player2_captured_percentage(self):
        total = (COLS - 2) * (ROWS - 2)
        if total == 0:
            return 0.0
        return len(self.player2_filled_cells) * 100 / total

    def total_captured_percentage(self):
        return self.captured_percentage() + self.ai_captured_percentage()

    def two_total_captured_percentage(self):
        return self.captured_percentage() + self.player2_captured_percentage()

    def draw(self):
        adapte_affichage(WINDOW_WIDTH, WINDOW_HEIGHT)
        efface_tout()

        if self.screen == "menu":
            self._draw_menu()
        elif self.screen == "rules":
            self._draw_rules()
        else:
            self._draw_game()

    def _draw_game(self):
        self._draw_hud()
        self._draw_board()

        if self.info_open:
            self._draw_info_overlay()
        elif self.paused:
            self._draw_center_message("PAUSE")
        elif self.game_over:
            self._draw_center_message(self.game_over_text)
        elif self.message and monotonic() < self.message_until:
            self._draw_center_message(self.message)

    def _draw_hud(self):
        rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                  remplissage="#11151c", couleur="#11151c")

        texte(BOARD_LEFT, 20, "QIX", couleur="white", police=ARCADE_FONT, taille=28)
        texte(BOARD_LEFT + 120, 23, f"NIVEAU {self.level}", couleur="white", police=ARCADE_FONT, taille=18, largeur=170)

        if self.mode == "two":
            texte(BOARD_LEFT + 300, 23, f"J1 {self.captured_percentage():.1f}% {self.player.lives}V",
                  couleur="#20c4cc", police=ARCADE_FONT, taille=16, largeur=190)
            texte(BOARD_LEFT + 500, 23, f"J2 {self.player2_captured_percentage():.1f}% {self.player2.lives}V",
                  couleur="#b45cff", police=ARCADE_FONT, taille=16, largeur=190)
            texte(BOARD_LEFT + 700, 23, f"MANCHES {self.player1_rounds}-{self.player2_rounds}",
                  couleur="white", police=ARCADE_FONT, taille=15, largeur=300)
        else:
            texte(BOARD_LEFT + 300, 23, f"VIES {self.player.lives}", couleur="white", police=ARCADE_FONT, taille=18)
            if self.mode == "ai":
                texte(BOARD_LEFT + 430, 23, f"VOUS {self.captured_percentage():.1f}%", couleur="#20c4cc", police=ARCADE_FONT, taille=16)
                texte(BOARD_LEFT + 610, 23, f"IA {self.ai_captured_percentage():.1f}% {self.ai_player.lives}V", couleur="#b45cff", police=ARCADE_FONT, taille=16)
                texte(BOARD_LEFT + 790, 23, f"SCORE {self.score}", couleur="white", police=ARCADE_FONT, taille=15, largeur=210)
            else:
                texte(BOARD_LEFT + 440, 23, f"ZONE {self.captured_percentage():.1f}%", couleur="white", police=ARCADE_FONT, taille=18)
                texte(BOARD_LEFT + 635, 23, f"SCORE {self.score}", couleur="white", police=ARCADE_FONT, taille=18, largeur=365)

        self._draw_small_button(GAME_INFO_BUTTON, "i", "#ffd166")
        self._draw_small_button(GAME_MENU_BUTTON, "MENU", "#20c4cc")

        if self.mode == "two":
            texte(BOARD_LEFT, 68,
                  "J1 FLECHES + ENTREE / ESPACE    J2 ZQSD + SHIFT / E    P : PAUSE    ESC : MENU",
                  couleur="#cfd8dc", police=ARCADE_FONT, taille=11)
            statuses = []
            if self.player.is_invincible():
                statuses.append(f"J1 INVINCIBLE {self.player.invincibility_remaining():.1f}s")
            if self.player2.is_invincible():
                statuses.append(f"J2 INVINCIBLE {self.player2.invincibility_remaining():.1f}s")
            if statuses:
                texte(BOARD_LEFT + BOARD_WIDTH, 96, "   ".join(statuses),
                      couleur="#fff176", police=ARCADE_FONT, taille=11, ancrage="ne")
        else:
            speed = "RAPIDE" if self.player.speed_mode == "fast" else "LENTE"
            texte(BOARD_LEFT, 68, f"ESPACE : {speed}    P : PAUSE    Q : QUITTER    ESC : MENU",
                  couleur="#cfd8dc", police=ARCADE_FONT, taille=13)

            if self.player.is_invincible():
                remaining = self.player.invincibility_remaining()
                texte(BOARD_LEFT + BOARD_WIDTH, 68, f"INVINCIBLE {remaining:.1f}s",
                      couleur="#fff176", police=ARCADE_FONT, taille=13, ancrage="ne")

    def _draw_board(self):
        rectangle(
            BOARD_LEFT,
            BOARD_TOP,
            BOARD_LEFT + BOARD_WIDTH,
            BOARD_TOP + BOARD_HEIGHT,
            couleur="black",
            remplissage="black",
            epaisseur=1,
        )

        self._draw_filled_cells(self.filled_cells, "#20c4cc")
        self._draw_filled_cells(self.ai_filled_cells, "#7b2cbf")
        self._draw_filled_cells(self.player2_filled_cells, "#7b2cbf")

        self._draw_obstacles()
        self._draw_safe_lines()
        self._draw_trail()
        self._draw_ai_trail()
        self._draw_player2_trail()

        if self.apple is not None:
            self._draw_bonus()

        self.qix.draw(BOARD_LEFT, BOARD_TOP, CELL_SIZE)
        for enemy in self.sparx:
            enemy.draw(BOARD_LEFT, BOARD_TOP, CELL_SIZE)
        if self.mode == "ai":
            self.ai_player.draw(BOARD_LEFT, BOARD_TOP, CELL_SIZE)
        elif self.mode == "two":
            self.player2.draw(BOARD_LEFT, BOARD_TOP, CELL_SIZE)
        self.player.draw(BOARD_LEFT, BOARD_TOP, CELL_SIZE)

    def _draw_filled_cells(self, cells, color):
        tiles = {(col + dx, row + dy) for col, row in cells
                 for dx, dy in ((-1, -1), (0, -1), (-1, 0), (0, 0))}
        for col, row in tiles:
            corners = [(col, row), (col + 1, row),
                       (col + 1, row + 1), (col, row + 1)]
            points = [cell for cell in corners
                      if cell in cells or cell in self.safe_cells]
            if len(points) < 3:
                continue
            if len(points) < 4 and not any(
                cell in cells and cell not in self.safe_cells for cell in corners
            ):
                continue
            polygone([self._cell_center(*cell) for cell in points],
                     couleur="", remplissage=color)

    def _draw_obstacles(self):
        """Dessine des obstacles variés, avec un style spécial pour les versions dangereuses."""
        for group in self.obstacle_groups:
            dangerous = group["dangerous"]
            border = "#ffd166" if not dangerous else "#ff9f1c"
            fill = "#2b2d42" if not dangerous else "#5a0c1b"
            mark = "#ef476f" if not dangerous else "#fff176"

            for col, row in group["cells"]:
                x1 = BOARD_LEFT + col * CELL_SIZE + 2
                y1 = BOARD_TOP + row * CELL_SIZE + 2
                x2 = x1 + CELL_SIZE - 4
                y2 = y1 + CELL_SIZE - 4

                rectangle(
                    x1, y1, x2, y2,
                    couleur=border,
                    remplissage=fill,
                    epaisseur=2,
                )

                if dangerous:
                    ligne(x1 + 4, y1 + 5, x1 + CELL_SIZE * 0.48, y1 + CELL_SIZE * 0.48,
                          couleur=mark, epaisseur=1)
                    ligne(x1 + CELL_SIZE * 0.48, y1 + CELL_SIZE * 0.48, x2 - 4, y1 + CELL_SIZE * 0.30,
                          couleur=mark, epaisseur=1)
                    ligne(x1 + CELL_SIZE * 0.38, y2 - 4, x1 + CELL_SIZE * 0.58, y1 + CELL_SIZE * 0.58,
                          couleur=mark, epaisseur=1)
                else:
                    ligne(x1 + 4, y1 + 4, x2 - 4, y2 - 4,
                          couleur=mark, epaisseur=1)
                    ligne(x1 + 4, y2 - 4, x2 - 4, y1 + 4,
                          couleur=mark, epaisseur=1)

    def _draw_safe_lines(self):
        for col, row in self.safe_cells:
            x, y = self._cell_center(col, row)

            if (col + 1, row) in self.safe_cells:
                x2, y2 = self._cell_center(col + 1, row)
                ligne(x, y, x2, y2, couleur="white", epaisseur=2)

            if (col, row + 1) in self.safe_cells:
                x2, y2 = self._cell_center(col, row + 1)
                ligne(x, y, x2, y2, couleur="white", epaisseur=2)

    def _draw_trail(self):
        if not self.player.trail:
            return

        color = "#ffd166" if self.player.speed_mode == "slow" else "#f77f00"
        points = [self.player.anchor_position] + self.player.trail

        for first, second in zip(points, points[1:]):
            x1, y1 = self._cell_center(first[0], first[1])
            x2, y2 = self._cell_center(second[0], second[1])
            ligne(x1, y1, x2, y2, couleur=color, epaisseur=2)

    def _draw_ai_trail(self):
        if self.mode != "ai" or not self.ai_player.trail:
            return

        points = [self.ai_player.anchor_position] + self.ai_player.trail
        for first, second in zip(points, points[1:]):
            x1, y1 = self._cell_center(first[0], first[1])
            x2, y2 = self._cell_center(second[0], second[1])
            ligne(x1, y1, x2, y2, couleur="#b45cff", epaisseur=2)

    def _draw_player2_trail(self):
        if self.mode != "two" or not self.player2.trail:
            return

        color = "#c77dff" if self.player2.speed_mode == "slow" else "#9d4edd"
        points = [self.player2.anchor_position] + self.player2.trail
        for first, second in zip(points, points[1:]):
            x1, y1 = self._cell_center(first[0], first[1])
            x2, y2 = self._cell_center(second[0], second[1])
            ligne(x1, y1, x2, y2, couleur=color, epaisseur=2)

    def _draw_bonus(self):
        col, row = self.apple
        x, y = self._cell_center(col, row)

        diamond = [
            (x, y - CELL_SIZE * 0.20),
            (x + CELL_SIZE * 0.13, y),
            (x, y + CELL_SIZE * 0.20),
            (x - CELL_SIZE * 0.13, y),
        ]
        polygone(diamond, couleur="white", remplissage="#8ac926", epaisseur=1)

    def _cell_center(self, col, row):
        return (
            BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2,
            BOARD_TOP + row * CELL_SIZE + CELL_SIZE / 2,
        )

    def _draw_center_message(self, message):
        x1 = BOARD_LEFT + 230
        y1 = BOARD_TOP + BOARD_HEIGHT / 2 - 42
        x2 = BOARD_LEFT + BOARD_WIDTH - 230
        y2 = y1 + 84
        rectangle(x1, y1, x2, y2, couleur="white", remplissage="#11151c", epaisseur=2)
        texte((x1 + x2) / 2, (y1 + y2) / 2, message,
              couleur="white", police=ARCADE_FONT, ancrage="center", taille=20, largeur=x2 - x1 - 24)

    def _draw_menu(self):
        rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                  couleur="black", remplissage="black")

        self._draw_arcade_frame(40, 28, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 28)

        texte(WINDOW_WIDTH / 2, 92, "QIX",
              couleur="white", police=ARCADE_FONT, ancrage="center", taille=64)
        texte(WINDOW_WIDTH / 2, 155, "ARCADE",
              couleur="#20c4cc", police=ARCADE_FONT, ancrage="center", taille=28)
        texte(WINDOW_WIDTH / 2, 200, "CONQUERIR. EVITER. SURVIVRE.",
              couleur="#ffd166", police=ARCADE_FONT, ancrage="center", taille=15)

        self._draw_qix_logo(WINDOW_WIDTH / 2, 270)

        self._draw_button(MENU_BUTTONS["rules"], "REGLES", "#20c4cc")
        self._draw_button(MENU_BUTTONS["single"], "JEU 1 JOUEUR", "#ffd166")
        self._draw_button(MENU_BUTTONS["ai"], "1 JOUEUR VS IA", "#b45cff")
        self._draw_button(MENU_BUTTONS["two"], "JEU 2 JOUEURS", "#ef476f")

        if self.menu_message and monotonic() < self.menu_message_until:
            texte(WINDOW_WIDTH / 2, 730, self.menu_message,
                  couleur="#ef476f", police=ARCADE_FONT, ancrage="center", taille=13)
        else:
            texte(WINDOW_WIDTH / 2, 730, "CHOISIS UN MODE",
                  couleur="#9aa5b1", police=ARCADE_FONT, ancrage="center", taille=12)

        texte(WINDOW_WIDTH / 2, 785, "Q POUR QUITTER",
              couleur="#6c757d", police=ARCADE_FONT, ancrage="center", taille=11)

    def _draw_rules(self):
        rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                  couleur="black", remplissage="black")
        self._draw_arcade_frame(40, 28, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 28)

        texte(WINDOW_WIDTH / 2, 72, "REGLES DU JEU",
              couleur="#ffd166", police=ARCADE_FONT, ancrage="center", taille=34)
        ligne(210, 112, WINDOW_WIDTH - 210, 112, couleur="#20c4cc", epaisseur=2)

        rules = [
            ("OBJECTIF", "Capture 75% de l'arene."),
            ("J1", "Fleches + ENTREE pour tracer. ESPACE : vitesse."),
            ("J2", "ZQSD + SHIFT pour tracer. E : vitesse."),
            ("CAPTURE", "Referme ton chemin sur une ligne blanche."),
            ("QIX", "S'il touche ton chemin, tu perds une vie."),
            ("SPARX", "Ils te poursuivent sur les frontieres."),
            ("ARTEFACT", "Cristal vert : 3 secondes d'invincibilite."),
            ("OBSTACLES", "Les blocs bloquent ; les rouges blessent."),
            ("DUEL", "A 75% total, le plus grand territoire gagne."),
            ("CROISEMENT", "Traverser le chemin actif adverse coute une vie."),
            ("PIEGE", "Si une capture enferme l'autre joueur, il perd une vie."),
        ]

        y = 135
        for title, description in rules:
            texte(150, y, title,
                  couleur="#20c4cc", police=ARCADE_FONT, taille=13, largeur=180)
            texte(340, y, description,
                  couleur="white", police=ARCADE_FONT, taille=12, largeur=WINDOW_WIDTH - 410)
            y += 48

        texte(WINDOW_WIDTH / 2, 700, "NE LAISSE PAS LE QIX TOUCHER TON CHEMIN.",
              couleur="#ef476f", police=ARCADE_FONT, ancrage="center", taille=13)

        self._draw_button(RULES_BACK_BUTTON, "MENU PRINCIPAL", "#20c4cc")
        self._draw_button(RULES_PLAY_BUTTON, "JOUER", "#ffd166")

    def _draw_info_overlay(self):
        """Affiche les informations sans quitter la partie."""
        x1, y1, x2, y2 = 250, 175, 1030, 755
        rectangle(x1, y1, x2, y2,
                  couleur="white", remplissage="#090c12", epaisseur=2)
        rectangle(x1 + 7, y1 + 7, x2 - 7, y2 - 7,
                  couleur="#20c4cc", epaisseur=1)

        texte((x1 + x2) / 2, y1 + 55, "INFOS",
              couleur="#ffd166", police=ARCADE_FONT, ancrage="center", taille=30)
        ligne(x1 + 90, y1 + 92, x2 - 90, y1 + 92,
              couleur="#20c4cc", epaisseur=2)

        if self.mode == "ai":
            mode = "1 JOUEUR VS IA"
        elif self.mode == "two":
            mode = "2 JOUEURS"
        else:
            mode = "1 JOUEUR"

        items = [
            ("MODE", mode),
            ("QIX", "Ennemi libre dans la zone noire."),
            ("SPARX", "Fantomes qui suivent les frontieres."),
            ("CRISTAL", "Invincibilite pendant 3 secondes."),
            ("OBSTACLES", "Jaunes : blocs. Rouges : dangereux."),
        ]

        if self.mode == "ai":
            items.append(("COMMANDES", "Fleches / ENTREE / ESPACE / P / ESC."))
            items.append(("IA", "Elle se deplace et trace comme un joueur."))
            items.append(("SCORE", f"Vous {self.captured_percentage():.1f}% - IA {self.ai_captured_percentage():.1f}%"))
        elif self.mode == "two":
            items.append(("J1", "Fleches + ENTREE. ESPACE : vitesse."))
            items.append(("J2", "ZQSD + SHIFT. E : vitesse."))
            items.append(("MANCHE", f"J1 {self.captured_percentage():.1f}% - J2 {self.player2_captured_percentage():.1f}%"))
        else:
            items.append(("COMMANDES", "Fleches / ENTREE / ESPACE / P / ESC."))

        y = y1 + 135
        for title, description in items:
            texte(x1 + 90, y, title,
                  couleur="#20c4cc", police=ARCADE_FONT, taille=14, largeur=160)
            texte(x1 + 260, y, description,
                  couleur="white", police=ARCADE_FONT, taille=13, largeur=x2 - x1 - 280)
            y += 47

        self._draw_button(INFO_CLOSE_BUTTON, "RETOUR AU JEU", "#ffd166")

    def _draw_small_button(self, button, label, color):
        x1, y1, x2, y2 = button
        rectangle(x1, y1, x2, y2,
                  couleur=color, remplissage="#0d1117", epaisseur=1)
        texte((x1 + x2) / 2, (y1 + y2) / 2, label,
              couleur="white", police=ARCADE_FONT,
              ancrage="center", taille=11, largeur=x2 - x1 - 12)

    def _draw_button(self, button, label, color, disabled=False):
        x1, y1, x2, y2 = button
        border = "#555555" if disabled else color
        text_color = "#777777" if disabled else "white"

        rectangle(x1, y1, x2, y2,
                  couleur=border, remplissage="#0d1117", epaisseur=2)
        rectangle(x1 + 5, y1 + 5, x2 - 5, y2 - 5,
                  couleur=border, epaisseur=1)
        texte((x1 + x2) / 2, (y1 + y2) / 2, label,
              couleur=text_color, police=ARCADE_FONT,
              ancrage="center", taille=17, largeur=x2 - x1 - 24)

        if disabled:
            texte(x2 - 12, y1 + 8, "BIENTOT",
                  couleur="#ef476f", police=ARCADE_FONT,
                  ancrage="ne", taille=9)

    def _draw_arcade_frame(self, x1, y1, x2, y2):
        rectangle(x1, y1, x2, y2, couleur="white", epaisseur=2)
        rectangle(x1 + 7, y1 + 7, x2 - 7, y2 - 7,
                  couleur="#20c4cc", epaisseur=1)

        for x, y, color in (
            (62, 52, "#ef476f"),
            (WINDOW_WIDTH - 69, 52, "#ffd166"),
            (62, WINDOW_HEIGHT - 67, "#ffd166"),
            (WINDOW_WIDTH - 69, WINDOW_HEIGHT - 67, "#ef476f"),
        ):
            rectangle(x, y, x + 8, y + 8, couleur=color, remplissage=color)

    def _draw_qix_logo(self, x, y):
        for shift, color in ((-22, "#ef476f"), (0, "#651fff"), (22, "#ef476f")):
            ligne(x - 54 + shift, y - 24, x + 54 + shift, y + 24,
                  couleur=color, epaisseur=4)
            ligne(x - 54 + shift, y + 24, x + 54 + shift, y - 24,
                  couleur=color, epaisseur=3)
