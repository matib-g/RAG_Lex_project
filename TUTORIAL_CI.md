# Tutorial: Jak tworzyć procedury CI (GitHub Actions)

Ten krótki poradnik wyjaśnia, jak samodzielnie pisać pliki `.yml` dla GitHub Actions.

## 1. Gdzie to mieszka?
Wszystkie definicje muszą znajdować się w katalogu:
`.github/workflows/`

Nazwa pliku może być dowolna, np. `main.yml`, `testy.yml`.

## 2. Anatomia pliku YAML
Każdy plik workflow składa się z 3 głównych części:
1. **Nazwa** (`name`)
2. **Wyzwalacze** (`on`) - kiedy uruchomić?
3. **Zadania** (`jobs`) - co zrobić?

### Podstawowy Szablon

```yaml
name: Moj Pierwszy Pipeline

# KIEDY uruchomić?
on:
  push:                 # Uruchom przy wypchnięciu kodu...
    branches: ["main"]  # ...ale tylko na branch 'main'
  pull_request:         # Oraz przy każdym Pull Request
    branches: ["main"]

# CO zrobić?
jobs:
  moje-zadanie:
    runs-on: ubuntu-latest  # System operacyjny (Linux)
    
    steps:
      # Krok 1: Pobierz kod z repozytorium
      - name: Pobierz kod
        uses: actions/checkout@v4

      # Krok 2: Uruchom dowolną komendę
      - name: Przywitaj się
        run: echo "Cześć! To działa."
```

## 3. Kluczowe element "Steps" (Kroki)

W sekcji `steps` używamy dwóch rodzajów operacji:

**A. Gotowe akcje (`uses`)**
To "gotowce" przygotowane przez społeczność. Najważniejsze to:
- `actions/checkout@v4` - pobiera Twój kod (bez tego folder jest pusty!).
- `actions/setup-python@v5` - instaluje i konfiguruje Pythona.

**B. Komendy powłoki (`run`)**
To zwykłe komendy, które wpisałbyś w terminalu.
```yaml
- name: Instalacja zależności
  run: pip install -r requirements.txt
```

## 4. Przykład dla Pythona
Oto jak skleić to w całość dla projektu Pythonowego:

```yaml
name: Testy Python
on: [push]

jobs:
  testowanie:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
          
      - name: Instalacja bibliotek
        run: pip install pytest requests
        
      - name: Uruchomienie testów
        run: pytest
```

## 5. Dobre praktyki
1. **Nazywaj kroki** (`name: ...`) - dzięki temu w logach na GitHubie łatwo znajdziesz, co się aktualnie dzieje.
2. **Rozdzielaj etapy** - osobny krok na instalację, osobny na testy, osobny na budowanie.
3. **Szybka porażka** - Pipeline zatrzymuje się na pierwszym błędzie. Jeśli `pip install` zawiedzie, testy się nie uruchomią.
