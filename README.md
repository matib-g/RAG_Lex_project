# ⚖️ RAG Lex – Polski System Prawny

> **Retrieval-Augmented Generation dla polskiego prawa**  
> System pozwala zadawać pytania o polskie ustawy i otrzymywać odpowiedzi wsparte cytatami źródłowymi.

---

## 📋 Spis Treści

- [Opis Projektu](#-opis-projektu)
- [Architektura](#-architektura)
- [Wymagania](#-wymagania)
- [Szybki Start (Docker)](#-szybki-start-docker)
- [Instalacja Lokalna](#-instalacja-lokalna)
- [Interfejs Użytkownika](#-interfejs-użytkownika)
- [API](#-api)
- [CLI (Command Line Interface)](#%EF%B8%8F-cli-command-line-interface)
- [Struktura Projektu](#-struktura-projektu)
- [Testy](#-testy)
- [CI/CD](#-cicd)
- [Przykładowe Pytania](#-przykładowe-pytania)
- [Rozwój Projektu](#-rozwój-projektu)

---

## 📖 Opis Projektu

**RAG Lex** to system Retrieval-Augmented Generation (RAG) dla polskiego prawa. Pobiera ustawy z oficjalnego API Sejmu RP, przetwarza je i indeksuje w bazie wektorowej, a następnie umożliwia zadawanie pytań w języku naturalnym.

### Jak to działa?
1. **Retrieval** – System wyszukuje fragmenty ustaw najbardziej podobne do pytania użytkownika (używając embeddingów). Stosujemy **Sentence-Aware Chunking**, aby zachować spójność logiczną fragmentów.
2. **Augmented** – Znalezione fragmenty są dołączane do kontekstu dla modelu językowego w formacie **Chat Template [INST]**.
3. **Generation** – Polski model LLM (PLLuM-8B) generuje odpowiedź, a wynik jest oceniany przez zaawansowany **Cross-Encoder**.

---

## 🏗 Architektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG Lex System                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐    ┌──────────────┐    ┌───────────────────┐        │
│  │ Streamlit │───▶│   FastAPI    │───▶│   RAG Pipeline    │        │
│  │    UI     │    │    Backend   │    │                   │        │
│  │  :8501    │    │    :8000     │    │  ┌─────────────┐  │        │
│  └───────────┘    └──────────────┘    │  │ Embedding   │  │        │
│                                       │  │   Model     │  │        │
│                                       │  └─────────────┘  │        │
│                                       │         │         │        │
│                                       │         ▼         │        │
│                                       │  ┌─────────────┐  │        │
│                                       │  │  ChromaDB   │  │        │
│                                       │  │ (vectordb/) │  │        │
│                                       │  └─────────────┘  │        │
│                                       │         │         │        │
│                                       │         ▼         │        │
│                                       │  ┌─────────────┐  │        │
│                                       │  │ Llama LLM   │  │        │
│                                       │  │  (GGUF)     │  │        │
│                                       │  └─────────────┘  │        │
│                                       └───────────────────┘        │
│                                                                     │
│  ┌───────────┐                                                      │
│  │   Redis   │ ← Cache dla odpowiedzi                               │
│  │   :6379   │                                                      │
│  └───────────┘                                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Wymagania

### Sprzęt
- **RAM**: Minimum 16 GB (zalecane 32 GB dla płynnej pracy LLM)
- **Dysk**: ~15 GB wolnego miejsca (model + dane)
- **CPU**: Model działa na CPU (ARM/x86_64)

### Oprogramowanie
- **Docker** i **Docker Compose** (zalecane)
- Lub: Python 3.11+, pip

---

## 🚀 Szybki Start (Docker)

Najprostszy sposób uruchomienia projektu:

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/your-username/rag_lex_project.git
cd rag_lex_project

# 2. Skopiuj plik konfiguracyjny
cp .env.example .env

# 3. Uruchom wszystkie usługi
docker-compose up --build
```

Po uruchomieniu:
- **Frontend (Streamlit)**: http://localhost:8501
- **API (Swagger UI)**: http://localhost:8000/docs
- **Redis**: localhost:6379

> ⚠️ **Pierwsze uruchomienie**: System automatycznie pobierze model LLM (~5 GB) i zindeksuje bazę danych, co może potrwać 10-15 minut.

### Zatrzymywanie
```bash
docker-compose down
```

---

## 💻 Instalacja Lokalna

Jeśli nie chcesz używać Dockera:

```bash
# 1. Utwórz wirtualne środowisko
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# lub: venv\Scripts\activate  # Windows

# 2. Zainstaluj zależności
pip install -r requirements.txt

# 3. Skopiuj konfigurację
cp .env.example .env

# 4. Pobierz dane i przygotuj bazę
python main.py download --year 2020 --limit 100
python main.py prepare
python main.py index

# 5. Uruchom serwer API
uvicorn src.api.app:app --reload --port 8000

# 6. (Opcjonalnie) Uruchom frontend w osobnym terminalu
streamlit run src/ui/app.py
```

---

## 🖥 Interfejs Użytkownika

### Streamlit (http://localhost:8501)

Intuicyjny interfejs czatu prawniczego:
- Wpisz pytanie w języku naturalnym
- Otrzymaj odpowiedź z cytatami źródłowymi
- Zobacz czas generowania odpowiedzi
- Przeglądaj źródła (cytaty z ustaw)

---

## 🔌 API

### Endpoint: `POST /api/v1/query` lub `POST /api/v1/query/stream`

**Request:**
```json
{
  "query": "Jakie są zasady pracy zdalnej?",
  "top_k": 5
}
```

**Response (Non-streaming):**
```json
{
  "question": "Jakie są zasady pracy zdalnej?",
  "answer": "Zgodnie z art. 3 ustawy o COVID-19...",
  "sources": [
    {
      "citation": "DU_2020_374",
      "text": "W okresie obowiązywania stanu zagrożenia...",
      "rank": 1,
      "score": 0.85
    }
  ]
}
```
> **Uwaga**: Endpoint `/stream` zwraca dane w formacie `text/event-stream` (token po tokenie).

### Swagger UI
Interaktywna dokumentacja API: http://localhost:8000/docs

---

## ⌨️ CLI (Command Line Interface)

Aplikacja oferuje interfejs wiersza poleceń do zarządzania danymi:

### Pobieranie ustaw
```bash
# Pobierz ustawy z danego roku (domyślnie DU - Dziennik Ustaw)
python main.py download --year 2020 --limit 50
python main.py download --year 2021 --publisher MP  # Monitor Polski
```

### Przygotowanie danych
```bash
# Wyczyść HTML i podziel na fragmenty (chunking)
python main.py prepare
```

### Indeksowanie
```bash
# Załaduj do bazy wektorowej ChromaDB
python main.py index
```

### Aktualizacja bazy
```bash
# Sprawdź nowe akty prawne i zaktualizuj bazę
python main.py update --publisher DU --year 2024
```

### Tryb interaktywny RAG
```bash
# Uruchom czat w terminalu
python main.py rag

# Lub zadaj pojedyncze pytanie
python main.py rag --query "Kto może skorzystać ze zwolnienia z ZUS?"
```

### Ewaluacja jakości
```bash
# Uruchom testy jakości (Answer Relevance, Faithfulness, Context Precision)
python main.py evaluate --questions TEST_QUESTIONS.md
```

---

## 📁 Struktura Projektu

```
rag_lex_project/
├── src/                          # Kod źródłowy
│   ├── api/                      # FastAPI backend
│   │   ├── app.py               # Główna aplikacja FastAPI
│   │   ├── routes.py            # Endpointy API
│   │   └── schemas.py           # Pydantic modele
│   ├── data_ingestion/           # Pobieranie i przetwarzanie danych
│   │   ├── downloader.py        # Pobieranie z API Sejmu
│   │   ├── preprocessor.py      # Czyszczenie HTML, chunking
│   │   └── indexer.py           # Ładowanie do ChromaDB
│   ├── database/                 # Warstwa bazy danych
│   │   └── vector_store.py      # Wrapper ChromaDB
│   ├── models/                   # Modele ML
│   │   ├── embedding.py         # Model embeddingowy
│   │   └── llm.py               # Llama LLM (GGUF)
│   ├── rag/                      # Pipeline RAG
│   │   └── pipeline.py          # Orkiestracja retrieval + generation
│   ├── ui/                       # Frontend
│   │   └── app.py               # Aplikacja Streamlit
│   ├── evaluation/               # Ewaluacja jakości (RAG Metrics)
│   │   ├── eval.py              # Runner testów i benchmarków
│   │   └── metrics.py           # Implementacja metryk (Cross-Encoder)
│   └── utils/                    # Narzędzia pomocnicze
│       ├── config.py            # Konfiguracja i stałe
│       └── logger.py            # Logowanie
├── tests/                        # Testy jednostkowe i integracyjne
│   ├── test_api.py
│   ├── test_preprocessor.py
│   └── test_pipeline.py
├── data/                         # Dane (git-ignored, DVC-tracked)
├── models/                       # Modele LLM (git-ignored, DVC-tracked)
├── vectordb/                     # Baza wektorowa ChromaDB
├── notebooks/                    # Notebooki eksploracyjne
├── .github/workflows/            # GitHub Actions CI
│   └── ci.yml
├── docker-compose.yml            # Definicja usług Docker
├── Dockerfile                    # Obraz aplikacji
├── requirements.txt              # Zależności Python
├── main.py                       # CLI entry point
└── .env.example                  # Szablon konfiguracji
```

---

## 🧪 Testy

Projekt używa **pytest** do testów:

```bash
# Uruchom wszystkie testy
pytest

# Z pokryciem kodu
pytest --cov=src

# Konkretny plik
pytest tests/test_api.py -v
```

### Struktura testów
- `test_api.py` – Testy endpointów FastAPI
- `test_preprocessor.py` – Testy przetwarzania tekstu
- `test_pipeline.py` – Testy integracyjne RAG

---

## 🔄 CI/CD

Projekt używa **GitHub Actions** do ciągłej integracji:

### Workflow (`.github/workflows/ci.yml`)
- Uruchamia się przy każdym `push` i `pull_request`
- Instaluje zależności
- Uruchamia testy `pytest`
- Sprawdza poprawność kodu

### Status
Po wypchnięciu zmian możesz sprawdzić status w zakładce **Actions** na GitHubie.

---

## 💡 Przykładowe Pytania

Oto pytania do przetestowania systemu (dotyczą ustaw z 2020 roku):

### 1. Praca zdalna
> "Na jakiej podstawie pracodawca mógł polecić pracownikowi wykonywanie pracy zdalnej?"

### 2. Świadczenie postojowe
> "Komu przysługiwało świadczenie postojowe i w jakiej wysokości?"

### 3. Maseczki
> "Jakie były obowiązki związane z zakrywaniem ust i nosa?"

### 4. Zasiłek opiekuńczy
> "Na jakich zasadach przyznawano dodatkowy zasiłek opiekuńczy rodzicom?"

### 5. Zwolnienie ZUS
> "Kto mógł skorzystać ze zwolnienia z opłacania składek ZUS w 2020 roku?"

---

## 🛠 Rozwój Projektu

### Planowane funkcje
- [x] Cache odpowiedzi (Redis)
- [x] Streaming odpowiedzi (Server-Sent Events)
- [x] Inteligentny Chunking (zdaniowy)
- [ ] Metryki jakości (dashboard)
- [ ] Multi-modalność (PDF, tabele)
- [ ] Personalizacja (pamięć kontekstu)
- [ ] Wdrożenie w chmurze (AWS/GCP/Azure)

### Wersjonowanie danych (DVC)
Projekt używa **DVC** do śledzenia danych i modeli:
```bash
dvc pull   # Pobierz dane z remote storage
dvc push   # Wyślij nowe dane
```

---

## 📄 Licencja

MIT License – szczegóły w pliku `LICENSE`.

---

## 👤 Autor

Mateusz Bulanda-Gorol

---

> ⚖️ *"Prawo powinno być dostępne dla każdego"*