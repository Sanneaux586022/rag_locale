import argparse
import pathlib
import sys
import pymupdf
from collections import Counter


def costruisci_parser():
    parser = argparse.ArgumentParser(description="Spezza un file PDF.")
    parser.add_argument(
        "--percorso",
        required=True,
        type=valida_nome,
        help="Percorso del file da spezzare",
    )
    return parser


def valida_nome(percorso: str) -> pathlib.Path:
    if not percorso:
        raise argparse.ArgumentTypeError("Il percorso non può essere vuoto.")

    path = pathlib.Path(percorso)
    if not path.exists():
        raise argparse.ArgumentTypeError("Inserire un percorso valido.")
    if not path.is_file():
        raise argparse.ArgumentTypeError("Inserire un file valido.")
    if not path.suffix.lower() == (".pdf"):
        raise argparse.ArgumentTypeError("Il file deve essere un pdf.")
    return path


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
    # text_page = [line.strip() for line in testo.splitlines() if line.strip() and not line.strip().isdigit() and line.strip() not in intestazioni]

    return "\n".join(righe_pulite)


def _chunk(testo: str, size: int, overlap: int) -> list[str]:

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
    lung= len(parole)
    while i + size < len(parole):
        chunk = parole[i: i + size]
        if len(chunk) == size:
            lista_chunk.append(" ".join(chunk))
        i += size - overlap
    if overlap < len(parole) - i <= size:
        lista_chunk.append(" ".join(parole[i:]))

    return lista_chunk


if __name__ == "__main__":
    args = costruisci_parser().parse_args()
    try:
        lista_risultati = estrae_pagine(args.percorso)
        intestazioni = trova_intestazioni(lista_risultati)
        print(f"intestazioni: {intestazioni}")

        testo = "3\nTitolo\n1.\nPrimo comma\n1.\nAltro comma\n\nCopyright"
        print(pulisci_pagina(testo, {"Titolo", "Copyright"}))
        print(pulisci_pagina(testo, set()))
        # for numero, pagina in lista_risultati:
        #     testo_pulito = pulisci_pagina(testo=pagina, intestazioni=intestazioni)
        #     print(f"testo_pulito: {testo_pulito}")
        #     break

    except Exception as err:
        print(f"Errore in estrae pagine : {err}")
        sys.exit(1)
