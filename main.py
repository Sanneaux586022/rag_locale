import argparse
import pathlib
import sys
import pymupdf


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
    if not percorso.endswith(".pdf"):
        raise argparse.ArgumentTypeError("Il file deve essre un pdf.")    
    return pathlib.Path(percorso)


def estrai_pagine(percorso: pathlib.Path) -> list[tuple[int, str]]:
    lista_risultati = []
    with pymupdf.open(percorso) as file:

        for contatore, page in enumerate(file, start=1):
            pagina = (contatore, page.get_text())
            lista_risultati.append(pagina)
    return lista_risultati


if __name__ == "__main__":
    args = costruisci_parser().parse_args()
    try:
        lista_risultati = estrai_pagine(args.percorso)
        for ris in lista_risultati[:6]:
            print(f"pagina: {ris[0]}")
            print(f"testo pagina{ris[0]}: {ris[1]}")
    except Exception as err:
        print(f"Errore in spezza pdf : {err}")
        sys.exit(1)
