from main import _chunk, cerca
import pytest


def test_chunk_testo_corto():
    assert _chunk("a b c d e f g", size=4, overlap=2) == ["a b c d", "c d e f", "e f g"]


def test_overlap_maggiore_di_size():
    with pytest.raises(ValueError):
        _chunk("a b", size=4, overlap=10)


def test_size_negativo():
    with pytest.raises(ValueError):
        _chunk("", size=-5, overlap=0)

def test_estrazione_risposte():
    assert cerca()