from archivio import Risultato


def formatta_risposte(risposte: list[Risultato]) -> str:
    res = ""
    for contatore, risp in enumerate(risposte, start=1):
        res += f"[{contatore}] {risp[1]} , pagina {risp[2]}\n {risp[0]}\n."
    return res


def costruisci_prompt(question: str, answers: list[Risultato]) -> str:
    testo_risposte = formatta_risposte(answers)
    return f"""
        In base alla domanda fatta : {question}, genera la risposta più breve possibile
        in italiano. Non devi inventare nulla e solo fare riferimento alle risposte possibili:
        {testo_risposte} devi anche citare il numero dell'estratto , la fonte ed il titolo del documento
        e presentarli come da documento.se non lo sai dillo.
    """
