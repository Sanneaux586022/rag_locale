CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks(
    id SERIAL PRIMARY KEY,
    documento TEXT NOT NULL,
    pagina INT NOT NULL,
    testo TEXT NOT NULL,
    embedding vector(1024) NOT NULL
);