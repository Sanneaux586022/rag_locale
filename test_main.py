from pdf_utils import dividi_in_chunk
from prompt import formatta_risposte
import pytest


def test_chunk_testo_corto():
    assert dividi_in_chunk("a b c d e f g", size=4, overlap=2) == [
        "a b c d",
        "c d e f",
        "e f g",
    ]


def test_overlap_maggiore_di_size():
    with pytest.raises(ValueError):
        dividi_in_chunk("a b", size=4, overlap=10)


def test_size_negativo():
    with pytest.raises(ValueError):
        dividi_in_chunk("", size=-5, overlap=0)


def test_formatta_risposte():
    risposte = [("testo ferie", "ccnl.pdf", 12, 0.3)]
    assert formatta_risposte(risposte) == "[1] ccnl.pdf , pagina 12\n testo ferie\n."
