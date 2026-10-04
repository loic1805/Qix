from functools import lru_cache

import fltk


_scale = 1.0
_left = 0.0
_top = 0.0
_width = 1280


def adapte_affichage(largeur, hauteur):
    global _scale, _left, _top, _width
    _width = largeur
    _scale = max(0.001, min(fltk.largeur_fenetre() / largeur,
                            fltk.hauteur_fenetre() / hauteur))
    _left = (fltk.largeur_fenetre() - largeur * _scale) / 2
    _top = (fltk.hauteur_fenetre() - hauteur * _scale) / 2


def position_logique(x, y):
    return (x - _left) / _scale, (y - _top) / _scale


def _point(x, y):
    return _left + x * _scale, _top + y * _scale


def _style(options):
    options["epaisseur"] = max(0.5, options.get("epaisseur", 1) * _scale)
    return options


def rectangle(ax, ay, bx, by, **options):
    return fltk.rectangle(*_point(ax, ay), *_point(bx, by), **_style(options))


def ligne(ax, ay, bx, by, **options):
    return fltk.ligne(*_point(ax, ay), *_point(bx, by), **_style(options))


def cercle(x, y, rayon, **options):
    return fltk.cercle(*_point(x, y), rayon * _scale, **_style(options))


def polygone(points, **options):
    return fltk.polygone([_point(x, y) for x, y in points], **_style(options))


@lru_cache(maxsize=1024)
def _largeur_texte(chaine, police, taille):
    return fltk.taille_texte(chaine, police=police, taille=taille)[0]


def texte(x, y, chaine, largeur=None, **options):
    police = options.get("police", "Helvetica")
    taille = max(1, round(options.get("taille", 24) * _scale))
    ancrage = options.get("ancrage", "nw")
    if "w" in ancrage:
        disponible = _width - x
    elif "e" in ancrage and ancrage != "center":
        disponible = x
    else:
        disponible = 2 * min(x, _width - x)
    disponible = max(0, min(disponible, largeur if largeur is not None else disponible) * _scale)
    chaine = str(chaine)
    if _largeur_texte(chaine, police, taille) > disponible:
        debut, fin = 0, len(chaine)
        while debut < fin:
            milieu = (debut + fin + 1) // 2
            if _largeur_texte(chaine[:milieu] + "...", police, taille) <= disponible:
                debut = milieu
            else:
                fin = milieu - 1
        chaine = chaine[:debut] + "..." if _largeur_texte("...", police, taille) <= disponible else ""
    options["taille"] = taille
    return fltk.texte(*_point(x, y), chaine, **options)
