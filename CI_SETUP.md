# Konfiguracja Continuous Integration (CI) - Wyjaśnienie

## Co to jest CI?
Continuous Integration (Ciągła Integracja) to praktyka w inżynierii oprogramowania, która polega na częstym i automatycznym sprawdzaniu kodu.
W skrócie: za każdym razem, gdy wyślesz zmiany na serwer (np. GitHub), automatyczny "robot" pobierze Twój kod, zainstaluje go i uruchomi testy. Jeśli coś zepsułeś, dowiesz się o tym natychmiast (dostaniesz maila lub czerwony krzyżyk przy commicie).

## Dlaczego warto?
1. **Automatyzacja**: Nie musisz pamiętać o uruchamianiu `pytest` ręcznie.
2. **Bezpieczeństwo**: Nie zepsujesz "głównej gałęzi" (master) kodu, jeśli skonfigurujesz blokadę w przypadku błędów testów.
3. **Czyste środowisko**: Testy uruchamiają się na świeżej maszynie w chmurze, więc unikamy problemów typu "u mnie działa".

## Co zrobimy? (GitHub Actions)
Użyjemy GitHub Actions, ponieważ Twój kod jest na GitHubie. Konfiguracja polega na stworzeniu jednego pliku YAML w katalogu `.github/workflows/`.

### Krok po kroku:
1. Utworzymy folder `.github/workflows`.
2. Stworzymy plik `ci.yml`.
3. Zdefiniujemy w nim "Workflow", który:
   - Uruchamia się na `git push`.
   - Pobiera kod (`checkout`).
   - Instaluje Pythona 3.11.
   - Instaluje biblioteki z `requirements.txt`.
   - Uruchamia testy (`pytest`).

## Jak to uruchomić?
Po zapisaniu pliku `ci.yml` musisz wypchnąć zmiany do repozytorium:
```bash
git add .
git commit -m "Add CI pipeline"
git push origin master
```
Wtedy wejdź w zakładkę **Actions** na swoim repozytorium na GitHub, aby zobaczyć działający proces.
