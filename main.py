import argparse
import os
import pathlib
import sys
import pymupdf
from collections import Counter
import requests
import psycopg
from pgvector.psycopg import register_vector
import numpy
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
MODELLO_EMBBEDING = "bge-m3"
# MODELLO_EMBBEDING = "nomic-embed-text"

def costruisci_parser():
    parser = argparse.ArgumentParser(description="Spezza un file PDF.")
    parser.add_argument(
        "--percorso",
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
    while i + size < len(parole):
        chunk = parole[i : i + size]
        if len(chunk) == size:
            lista_chunk.append(" ".join(chunk))
        i += size - overlap
    if overlap < len(parole) - i <= size:
        lista_chunk.append(" ".join(parole[i:]))

    return lista_chunk


def _insert_chunk(connection, nome_doc, pagina, chunk):
    
    r = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": MODELLO_EMBBEDING, "input": chunk},
    )
    vettore = r.json()["embeddings"][0]

    connection.execute(
        "INSERT INTO chunks (documento, pagina, testo, embedding) VALUES (%s, %s, %s, %s)",
        (nome_doc, pagina, chunk, numpy.array(vettore)),
    )

def cerca(connection, domanda, k=5):
    r = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": MODELLO_EMBBEDING, "input": domanda},
    )
    vettore = numpy.array(r.json()["embeddings"][0])
    
    sql = """
            SELECT testo, documento, pagina, embedding <=> %s AS distanza
            FROM chunks
            ORDER BY embedding <=> %s
            LIMIT %s
        """
    results = connection.execute(sql, (vettore, vettore,k)).fetchall()

    return results


if __name__ == "__main__":
    args = costruisci_parser().parse_args()
    if args.percorso:
        nome_documento = args.percorso.name
        try:
            lista_risultati = estrae_pagine(args.percorso)
            intestazioni = trova_intestazioni(lista_risultati)
            with psycopg.connect(DATABASE_URL) as conn:
                register_vector(conn)
                conn.execute("DELETE FROM chunks WHERE documento = %s", (nome_documento,))
                for numero, pagina in lista_risultati:
                    testo_pulito = pulisci_pagina(testo=pagina, intestazioni=intestazioni)
                    for chunk in _chunk(testo_pulito, size=200, overlap=40):
                        _insert_chunk(connection=conn, nome_doc=nome_documento, pagina=numero, chunk=chunk)
                
        except Exception as err:
            print(f"Errore durante indicizzazione: {err}")
            sys.exit(1)
    else:
        domanda = input("Fai una domanda sui documenti aziendali... ")
        with psycopg.connect(DATABASE_URL) as conn:
            register_vector(conn)
            risposte = cerca(connection=conn, domanda=domanda.strip().lower())

            print(f"risposte : {risposte}")
