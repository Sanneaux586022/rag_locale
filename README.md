# rag-locale

RAG su documenti PDF che gira tutto in locale: embedding e generazione su Ollama, vettori su Postgres con pgvector, nessun servizio cloud. Indicizza i PDF, recupera i passaggi più vicini alla domanda e fa scrivere la risposta a un LLM locale citando documento e pagina.

L'ho scritto in pochi giorni per capire come funziona davvero un RAG, partendo da zero, e l'ho provato su un contratto collettivo nazionale (CCNL metalmeccanici) di circa 100 pagine.

## Come funziona

**Indicizzazione**, una volta per documento:

1. estrae il testo dal PDF pagina per pagina (pymupdf), scartando le pagine vuote;
2. trova intestazioni e piè di pagina ripetuti e li toglie;
3. divide ogni pagina in chunk da 200 parole con 40 di sovrapposizione;
4. calcola l'embedding di ogni chunk con `bge-m3` su Ollama;
5. salva testo, vettore, nome del documento e pagina in Postgres.

**Ricerca**, a ogni domanda: calcola l'embedding della domanda con lo stesso modello e restituisce i 5 chunk più vicini (distanza coseno, operatore `<=>` di pgvector) con documento e pagina.

**Risposta**: i chunk trovati finiscono in un prompt insieme alla domanda, con l'istruzione di rispondere solo su quella base e di citare le fonti. Il prompt va a `llama3.2:3b` su Ollama.

## Struttura del codice

| File | Contenuto |
|---|---|
| `main.py` | riga di comando: `indicizza()` e `chiedi()` |
| `pdf_utils.py` | estrazione delle pagine, pulizia di intestazioni e piè di pagina, divisione in chunk |
| `client_ollama.py` | classe `ClientOllama`: embedding e generazione tramite le API di Ollama |
| `archivio.py` | classe `ArchivioChunk`: tutto l'SQL sulla tabella `chunks` |
| `prompt.py` | formattazione dei risultati e costruzione del prompt |
| `config.py` | lettura delle variabili d'ambiente dal `.env` |

Sono classi solo le parti che hanno uno stato da portarsi dietro: il client (URL e modelli) e l'archivio (la connessione). Le funzioni su PDF e testo restano funzioni pure, facili da testare senza database né Ollama.

## Requisiti

- Docker con NVIDIA Container Toolkit (il modello gira sulla GPU)
- Python 3.12 o successivo

## Avvio

```bash
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull bge-m3
docker exec -it ollama ollama pull llama3.2:3b

docker run -d --name pgvector -e POSTGRES_PASSWORD=dev -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data pgvector/pgvector:pg16
docker exec -it pgvector psql -U postgres -c "CREATE EXTENSION vector;"
docker exec -it pgvector psql -U postgres -c "
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    documento TEXT NOT NULL,
    pagina INT NOT NULL,
    testo TEXT NOT NULL,
    embedding vector(1024) NOT NULL
);"

python3 -m venv .venv
source .venv/bin/activate
pip install pymupdf "psycopg[binary]" pgvector requests numpy python-dotenv pytest

cp .env.example .env
```

Variabili del `.env`:

- `DATABASE_URL`: stringa di connessione a Postgres;
- `URL_LLM_LOCAL_API`: indirizzo delle API di Ollama, per esempio `http://localhost:11434/api`;
- `MODELLO_EMBEDDING_ITA`: modello di embedding usato (`bge-m3`);
- `MODELLO_EMBEDDING_ENG`: modello alternativo, per ora non usato;
- `MODELLO_GENERAZIONE`: facoltativa, se manca vale `llama3.2:3b`.

I PDF non sono nel repository. Mettili nella cartella `pdf/`, che è esclusa da git.

## Uso

```bash
python main.py --percorso pdf/documento.pdf   # indicizza un documento
python main.py                                # fa una domanda
pytest -v                                     # test
```

Si può reindicizzare lo stesso documento non crea duplicati: le sue righe vengono cancellate e reinserite nella stessa transazione. Se qualcosa va storto si fa rollback e il documento resta com'era.

## Scelte e cose imparate

**Intestazioni trovate per posizione.** Il primo tentativo contava le righe che si ripetono su più della metà delle pagine, e oltre a titolo e copyright prendeva `1.`, la numerazione dei commi, che compare quasi ovunque. Toglierla avrebbe cancellato contenuto senza nessun errore visibile. Limitando il conteggio alle prime e ultime 5 righe di ogni pagina il problema sparisce: la posizione dipende dall'impaginazione, che si ripete, mentre il contenuto no.

**Chunk per pagina**, così ogni risultato cita una pagina sola. Il prezzo è che una frase a cavallo tra due pagine viene spezzata.

**Modello di embedding.** Con `nomic-embed-text` la domanda "quanti giorni di ferie sono previsti" metteva l'articolo sulle ferie al secondo posto, e le distanze dei cinque risultati stavano tutte in mezzo centesimo: il modello distingueva poco i testi in italiano. Aggiungere i prefissi `search_document:` e `search_query:` previsti dalla documentazione non ha aiutato (l'articolo è sceso al quarto posto). Con `bge-m3`, multilingue, i primi due risultati sono entrambi l'articolo sulle ferie e gli altri tre parlano comunque di assenze (permessi, malattia). Le distanze tra modelli diversi non si confrontano: conta la posizione del chunk giusto e quanto si stacca dagli altri.

**Parametri SQL sempre con segnaposto**, mai con f-string.

## Limiti e prossimi passi

- **Permessi**: un campo con il gruppo autorizzato a leggere ogni documento, filtrato direttamente nella query di ricerca, così l'LLM non vede mai testi che l'utente non può aprire.
- **Valutazione**: una serie di domande con risposta nota, per misurare i cambi di modello o di chunking invece di giudicarli a occhio su una domanda.
- **Sommario**: le pagine dell'indice finiscono nei chunk. Sulle domande provate finora non hanno disturbato, ma vanno filtrate.
- **Chunking sui confini degli articoli** invece che a parole fisse.
- Le righe composte solo da cifre vengono tolte come numeri di pagina, anche se in mezzo alla pagina potrebbero essere un importo o un anno.
- **Embedding a gruppi**: oggi ogni chunk è una richiesta HTTP separata, mentre `/api/embed` accetta anche una lista di testi.
# INFO 
CCNL: https://file.conflavoro.it/pdf/ccnl/ccnl_metalmeccanico_industria_conflavoro.pdf
