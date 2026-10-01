QIX - Projet BUT Informatique

Lancement
----------
python3 game.py

Commandes - Joueur 1
---------------------
Flèches : déplacement
Entrée + flèche : commencer un chemin depuis une frontière
Espace : changer la vitesse de dessin

Commandes - Joueur 2
---------------------
ZQSD : déplacement
Shift + ZQSD : commencer un chemin depuis une frontière
E : changer la vitesse de dessin

Commandes générales
-------------------
P : pause
Échap : revenir au menu principal
Q : quitter (hors mode 2 joueurs)
R : recommencer après un Game Over

Architecture
------------
game.py      : création de la fenêtre et boucle principale
gameboard.py : écrans, plateau, règles, collisions et capture
player.py    : joueurs humains et adversaire IA
qix.py       : déplacement et dessin du Qix
sparks.py    : déplacement et dessin des Sparx
fltk.py      : bibliothèque graphique fournie

Principe de capture
-------------------
Le plateau est représenté par une grille.
Quand un chemin se referme, il devient une frontière.
Un parcours en largeur part du Qix pour trouver la zone encore accessible.
La zone qui ne contient pas le Qix est capturée.

Fonctionnalités
---------------
- mode 1 joueur
- mode 1 joueur contre IA
- mode 2 joueurs local
- trois vies par joueur
- Qix aléatoire et deux Sparx
- score et deux vitesses de tracé
- bonus d'invincibilité
- obstacles de plusieurs formes
- obstacles dangereux aux niveaux élevés
- difficulté croissante avec les niveaux
- pause, menu et fenêtre d'informations en jeu

Mode joueur contre IA
---------------------
L'IA suit les frontières comme un joueur, choisit un point de départ puis
trace un chemin case par case avant de rejoindre une frontière.
Le joueur capture en cyan et l'IA en violet.
Quand les deux camps ont capturé ensemble au moins 75 % de l'arène, le camp
ayant le plus grand pourcentage remporte la manche.

Mode 2 joueurs
--------------
Les deux joueurs commencent sur le bord inférieur.
Le joueur 1 capture en cyan et le joueur 2 en violet.
Si un joueur traverse le chemin actif de l'autre, il perd une vie.
Si une capture enferme le joueur adverse pendant son tracé, il perd une vie.
Quand les deux joueurs ont capturé ensemble au moins 75 % de l'arène, celui
qui possède le plus grand territoire remporte la manche et le niveau suivant
commence.
