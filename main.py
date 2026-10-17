import argparse
import pathlib
import sys

import psycopg

import config
from archivio import ArchivioChunk
from client_ollama import ClientOllama
from pdf_utils import dividi_in_chunk, estrae_pagine, pulisci_pagina, trova_intestazioni
from prompt import costruisci_prompt, formatta_risposte


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


def indicizza(percorso: pathlib.Path, client: ClientOllama, archivio: ArchivioChunk):
    """Cancella e reinserisce i chunk del documento, nella stessa transazione."""
    nome_documento = percorso.name
    pagine = estrae_pagine(percorso)
    intestazioni = trova_intestazioni(pagine)
    archivio.cancella_documento(nome_documento)
    for numero, testo in pagine:
        testo_pulito = pulisci_pagina(testo=testo, intestazioni=intestazioni)
        for chunk in dividi_in_chunk(testo_pulito, size=200, overlap=40):
            archivio.inserisci(nome_documento, numero, chunk, client.embedding(chunk))


def chiedi(domanda: str, client: ClientOllama, archivio: ArchivioChunk) -> str:
    risposte = archivio.cerca(client.embedding(domanda.strip().lower()))
    print(formatta_risposte(risposte))
    return client.genera(costruisci_prompt(question=domanda, answers=risposte))


if __name__ == "__main__":
    args = costruisci_parser().parse_args()
    client = ClientOllama(
        url=config.URL_LLM_LOCAL_API,
        modello_embedding=config.MODELLO_EMBEDDING_ITA,
        modello_generazione=config.MODELLO_GENERAZIONE,
    )
    if args.percorso:
        try:
            with psycopg.connect(config.DATABASE_URL) as conn:
                indicizza(args.percorso, client, ArchivioChunk(conn))
        except Exception as err:
            print(f"Errore durante indicizzazione: {err}")
            sys.exit(1)
    else:
        domanda = input("Fai una domanda sui documenti aziendali... ")
        with psycopg.connect(config.DATABASE_URL) as conn:
            print(chiedi(domanda, client, ArchivioChunk(conn)))
