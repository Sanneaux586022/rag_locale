import numpy
import requests


class ClientOllama:
    """Parla con le API locali di Ollama: calcola embedding e genera testo."""

    def __init__(self, url: str, modello_embedding: str, modello_generazione: str):
        self._url = url.rstrip("/")
        self._modello_embedding = modello_embedding
        self._modello_generazione = modello_generazione

    def embedding(self, testo: str) -> numpy.ndarray:
        dati = self._post("embed", {"model": self._modello_embedding, "input": testo})
        return numpy.array(dati["embeddings"][0])

    def genera(self, prompt: str) -> str:
        dati = self._post(
            "generate",
            {"model": self._modello_generazione, "prompt": prompt, "stream": False},
        )
        return dati["response"]

    def _post(self, endpoint: str, payload: dict) -> dict:
        r = requests.post(f"{self._url}/{endpoint}", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
