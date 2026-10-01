"""Point d'entrée du jeu Qix."""

from fltk import cree_fenetre, ferme_fenetre
from gameboard import GameBoard, WINDOW_HEIGHT, WINDOW_WIDTH


def main():
    cree_fenetre(WINDOW_WIDTH, WINDOW_HEIGHT, frequence=60)
    game = GameBoard()

    while True:
        if not game.update():
            break

    ferme_fenetre()


if __name__ == "__main__":
    main()
