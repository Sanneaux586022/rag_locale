import numpy
from pgvector.psycopg import register_vector

# (testo, documento, pagina, distanza)
Risultato = tuple[str, str, int, float]


class ArchivioChunk:
    """Legge e scrive i chunk nella tabella chunks di Postgres (pgvector)."""

    def __init__(self, connection):
        self._conn = connection
        register_vector(self._conn)

    def cancella_documento(self, nome_doc: str):
        self._conn.execute("DELETE FROM chunks WHERE documento = %s", (nome_doc,))

    def inserisci(self, nome_doc: str, pagina: int, chunk: str, vettore: numpy.ndarray):
        self._conn.execute(
            "INSERT INTO chunks (documento, pagina, testo, embedding) VALUES (%s, %s, %s, %s)",
            (nome_doc, pagina, chunk, vettore),
        )

    def cerca(self, vettore: numpy.ndarray, k=5) -> list[Risultato]:
        sql = """
                SELECT testo, documento, pagina, embedding <=> %s AS distanza
                FROM chunks
                ORDER BY embedding <=> %s
                LIMIT %s
            """
        return self._conn.execute(sql, (vettore, vettore, k)).fetchall()
