# Wstęp do Konteneryzacji (Docker)

## Co to jest Docker?
Wyobraź sobie, że wysyłasz komuś swoją aplikację. Aby u niego zadziałała, ta osoba musi:
1. Zainstalować Pythona.
2. Pobrać odpowiednie biblioteki (często w konkretnych wersjach).
3. Ustawić zmienne środowiskowe.
4. Czasem doinstalować narzędzia systemowe (np. kompilatory C++).

Często kończy się to słynnym "u mnie działa, a u ciebie nie".

**Docker** rozwiązuje ten problem. Pakuje Twoją aplikację wraz ze **wszystkim**, czego ona potrzebuje (system operacyjny, biblioteki, pliki) do "pudełka" zwanego **Kontenerem**. To pudełko działa identycznie na każdym komputerze – Twoim, kolegi, czy na serwerze w chmurze.

## Kluczowe pojęcia

### 1. Dockerfile (Przepis)
To plik tekstowy z instrukcjami, jak zbudować to pudełko.
Mówisz w nim np.: "Weź system Linux, zainstaluj Pythona, skopiuj moje pliki, zainstaluj biblioteki z requirements.txt".

### 2. Obraz (Image)
To gotowe, zbudowane pudełko (a dokładnie jego schemat). Jest niezmienne. Możesz je wysłać koledze.

### 3. Kontener (Container)
To uruchomiona wersja Obrazu. Tutaj działa Twoja aplikacja. Możesz uruchomić wiele kontenerów z tego samego obrazu.

### 4. Docker Compose
Narzędzie, które pozwala opisać konfigurację uruchomienia (np. "uruchom ten obraz, ale podłącz mu ten folder z dysku jako pamięć"). Dzięki temu nie musisz wpisywać długich komend w terminalu, tylko używasz pliku `docker-compose.yml`.

## Co zrobimy w naszym projekcie?

1. Stworzymy **`Dockerfile`**:
   - Użyjemy lekkiej wersji Pythona (`python:3.11-slim`).
   - Zainstalujemy potrzebne narzędzia systemowe (dla `llama-cpp-python`).
   - Skopiujemy kod aplikacji do środka.

2. Stworzymy **`.dockerignore`**:
   - Lista plików, których NIE chcemy kopiować do obrazu (np. folder `.git`, wirtualne środowisko `venv`, czy ciężkie modele, które lepiej podłączyć z dysku).

3. Stworzymy **`docker-compose.yml`**:
   - Aby łatwo uruchamiać aplikację jedną komendą (`docker-compose up`).
   - Skonfigurujemy tzw. **Wolumeny (Volumes)**. Dzięki nim, jeśli aplikacja pobierze nowe ustawy lub stworzy bazę wektorową wewnątrz kontenera, pliki te pojawią się też na Twoim dysku (nie znikną po wyłączeniu kontenera).

## Zalety tego podejścia
- **Czystość**: Nie zaśmiecasz swojego systemu bibliotekami.
- **Przenośność**: Łatwe wdrożenie na chmurę (AWS/GCP/Azure) w przyszłości.
- **Powtarzalność**: Każdy, kto pobierze projekt, uruchomi go w identycznym środowisku.
