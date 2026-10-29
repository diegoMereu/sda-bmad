"""Generazione delle LDV secondo una sintassi configurabile.

La sintassi SDA e' ancora da confermare: qui c'e' solo il meccanismo
(prefisso + corpo numerico/alfanumerico + check digit), i valori stanno
in config/prodotti.yaml.
"""
import string

ALNUM = string.digits + string.ascii_uppercase


def _check_mod10(corpo: str) -> str:
    """Luhn su corpo numerico."""
    somma = 0
    for i, c in enumerate(reversed(corpo)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        somma += d
    return str((10 - somma % 10) % 10)


def _check_mod11(corpo: str) -> str:
    pesi = [2, 3, 4, 5, 6, 7]
    somma = sum(int(c) * pesi[i % 6] for i, c in enumerate(reversed(corpo)))
    r = (11 - somma % 11) % 11
    return "0" if r == 10 else str(r)


CHECK = {"mod10": _check_mod10, "mod11": _check_mod11}


def _corpo(progressivo: int, cifre: int, alfabeto: str) -> str:
    if alfabeto == "digits":
        return str(progressivo).zfill(cifre)[-cifre:]
    base = len(ALNUM)
    s = ""
    n = progressivo
    while n:
        n, r = divmod(n, base)
        s = ALNUM[r] + s
    return s.zfill(cifre)[-cifre:]


def genera_ldv(cfg: dict, progressivo: int) -> str:
    """LDV valida e univoca per il progressivo dato."""
    corpo = _corpo(progressivo, cfg.get("cifre", 11), cfg.get("alfabeto", "digits"))
    check = cfg.get("check", "none")
    cifra = CHECK[check](corpo) if check in CHECK else ""
    return f"{cfg.get('prefisso', '')}{corpo}{cifra}"


def corrompi_check(ldv: str) -> str:
    """Rende errata l'ultima cifra (per test negativi)."""
    ultima = ldv[-1]
    nuova = str((int(ultima) + 1) % 10) if ultima.isdigit() else "0"
    return ldv[:-1] + nuova
