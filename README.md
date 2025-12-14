## Struktura katalogów (`src/`)

Kod źródłowy aplikacji znajduje się teraz w folderze `src/` i został podzielony na logiczne moduły:

- **src/utils/**:
  - `config.py`: Stałe i konfiguracja (ścieżki, parametry modeli).
  - `logger.py`: Skonfigurowany logger dla całego projektu.

- **src/data_ingestion/**:
  - `downloader.py`: Klasa `SejmDownloader` do pobierania ustaw z API Sejmu.
  - `preprocessor.py`: Klasa `DataPreprocessor` do czyszczenia HTML i dzielenia tekstu na fragmenty (chunking).
  - `indexer.py`: Klasa `VectorIndexer` do ładowania przygotowanych danych do bazy wektorowej.

- **src/database/**:
  - `vector_store.py`: Klasa `VectorStore` będąca wrapperem na ChromaDB.

- **src/models/**:
  - `embedding.py`: Klasa `EmbeddingModel` (SentenceTransformers).
  - `llm.py`: Klasa `LlamaModel` (llama-cpp-python) do obsługi modelu generatywnego.

- **src/rag/**:
  - `pipeline.py`: Klasa `RAGPipeline` spajająca wyszukiwanie i generowanie odpowiedzi.

- **main.py**:
  Główny punkt wejścia (CLI) do aplikacji. Pozwala uruchamiać poszczególne etapy.

## Instrukcja użycia (CLI)

Możesz teraz używać aplikacji z poziomu terminala:

1. **Pobieranie danych**:
   ```bash
   python main.py download --year 2020 --limit 50
   ```

2. **Przygotowanie danych (preprocessing)**:
   ```bash
   python main.py prepare
   ```

3. **Indeksowanie do bazy wektorowej**:
   ```bash
   python main.py index
   ```

4. **Uruchomienie RAG (zadawanie pytań)**:
   - Tryb interaktywny:
     ```bash
     python main.py rag
     ```
   - Jedno pytanie:
     ```bash
     python main.py rag --query "Jakie są zasady wprowadzenia stanu wyjątkowego?"
     ```