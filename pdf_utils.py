import pathlib
from collections import Counter

import pymupdf


def estrae_pagine(percorso: pathlib.Path) -> list[tuple[int, str]]:
    """
    Riceve il percorso di un file PDF e restituisce le pagine non vuote
    come lista di tuple (numero, testo), con numerazione da 1.
    """
    lista_risultati = []
    with pymupdf.open(percorso) as file:

        for contatore, page in enumerate(file, start=1):
            text = page.get_text().strip()
            if text:
                lista_risultati.append((contatore, text))
    return lista_risultati


def trova_intestazioni(pagine: list[tuple[int, str]]) -> set[str]:
    """
    Riceve le pagine non vuote come (numero, testo), come restituite da estrae_pagine.
    Restituisce le righe che compaiono all'inizio o alla fine di più della metà delle pagine:
    intestazioni e piè di pagina ripetuti.
    """
    if not pagine:
        raise ValueError("Nessuna lista ricevuta.")

    counter = Counter()
    for _, text in pagine:
        text_page = [line.strip() for line in text.splitlines() if line.strip()]
        righe_bordo = set(text_page[:5]) | set(text_page[-5:])
        counter.update(righe_bordo)

    return set(
        [chiave for chiave, valore in counter.items() if valore > len(pagine) // 2]
    )


def pulisci_pagina(testo: str, intestazioni: set[str]) -> str:
    """
    Prende il testo gia estratto da estrae pagine e le intestazioni di trova intestazioni,
    E ritorna il testo della pagina senza le intestazioni e senza il numero di pagina.
    """
    if not testo:
        raise ValueError("Inserire un testo valido.")
    righe = [line.strip() for line in testo.splitlines()]
    righe_pulite = [r for r in righe if r and not r.isdigit() and r not in intestazioni]

    return "\n".join(righe_pulite)


def dividi_in_chunk(testo: str, size: int, overlap: int) -> list[str]:
    """
    Prende un testo già pulito, lo divide in pezzi di size , scorrendolo di size - overlap.
    E viene ritornata la lista di stringhe cosi divise.
    """

    parole = testo.split()
    lista_chunk = []
    if size <= 0 or overlap < 0:
        raise ValueError("inserire valori di overlap o size > 0.")
    if overlap >= size:
        raise ValueError("Overlap non può essere >= di size.")
    if not testo:
        return []
    if len(parole) < size:
        return [" ".join(parole)]

    i = 0
    while i + size < len(parole):
        chunk = parole[i : i + size]
        if len(chunk) == size:
            lista_chunk.append(" ".join(chunk))
        i += size - overlap
    if overlap < len(parole) - i <= size:
        lista_chunk.append(" ".join(parole[i:]))

    return lista_chunk
