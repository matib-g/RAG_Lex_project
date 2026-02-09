# Wdrożenie RAG Lex na Oracle Cloud Infrastructure

## Wymagania

- Konto Oracle Cloud (darmowe: [cloud.oracle.com](https://cloud.oracle.com))
- Instancja ARM Ampere A1.Flex (min. 4 OCPU, 12GB RAM)
- Domena (opcjonalna, ale zalecana dla SSL)

## Krok 1: Tworzenie instancji OCI

1. Zaloguj się do OCI Console
2. **Compute → Instances → Create Instance**
3. Wybierz:
   - **Shape:** VM.Standard.A1.Flex (ARM)
   - **OCPU:** 4 (lub więcej)
   - **RAM:** 12 GB (lub więcej)
   - **Image:** Ubuntu 22.04 (Canonical)
   - **Boot Volume:** 50 GB
4. Pobierz lub wygeneruj klucz SSH
5. Zapisz publiczny IP instancji

## Krok 2: Konfiguracja Security List (Firewall)

W OCI Console: **Networking → Virtual Cloud Networks → [Twoja VCN] → Security Lists → Default**

Dodaj Ingress Rules:
| Port | Protokół | Źródło | Opis |
|------|----------|--------|------|
| 22 | TCP | 0.0.0.0/0 | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 8000 | TCP | 0.0.0.0/0 | API (tymczasowo) |

## Krok 3: Połączenie SSH

```bash
ssh -i /path/to/private_key ubuntu@YOUR_OCI_IP
```

## Krok 4: Przesłanie plików na serwer

Na lokalnym komputerze:

```bash
# Sklonuj repo na serwer (lub prześlij przez SCP)
scp -i /path/to/key -r rag_lex_project ubuntu@YOUR_OCI_IP:~/

# Prześlij model LLM (ok. 4-5 GB)
scp -i /path/to/key models/*.gguf ubuntu@YOUR_OCI_IP:~/rag_lex_project/models/

# Prześlij bazę wektorową (ok. 1-2 GB)
scp -i /path/to/key -r vectordb ubuntu@YOUR_OCI_IP:~/rag_lex_project/
```

## Krok 5: Uruchomienie skryptu wdrożeniowego

```bash
ssh -i /path/to/key ubuntu@YOUR_OCI_IP
cd rag_lex_project

# Skopiuj i edytuj plik środowiskowy
cp .env.production.example .env.production
nano .env.production  # Ustaw CORS_ORIGINS na Twoje GitHub Pages URL

# Nadaj uprawnienia i uruchom skrypt
chmod +x scripts/deploy_oci.sh
./scripts/deploy_oci.sh
```

## Krok 6: Konfiguracja SSL (Let's Encrypt)

### Opcja A: Z własną domeną

1. Skonfiguruj DNS (A record) wskazujący na IP instancji OCI
2. Edytuj `nginx/nginx.conf` - zamień `YOUR_DOMAIN` na Twoją domenę
3. Zainstaluj Certbot:

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
```

4. Zrestartuj Nginx:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### Opcja B: Bez domeny (DuckDNS)

1. Zarejestruj darmową subdomenę na [duckdns.org](https://duckdns.org)
2. Zaktualizuj rekord DNS na Twój IP OCI
3. Użyj Certbot z DNS challenge

## Krok 7: Weryfikacja

```bash
# Sprawdź status kontenerów
docker compose -f docker-compose.prod.yml ps

# Sprawdź logi
docker compose -f docker-compose.prod.yml logs -f app

# Test API
curl http://YOUR_OCI_IP:8000/api/v1/health
```

## Krok 8: Konfiguracja GitHub Pages

1. W repozytorium GitHub: **Settings → Secrets → Actions**
2. Dodaj sekret: `VITE_API_URL` = `https://your-domain.com` (lub `http://YOUR_OCI_IP:8000` tymczasowo)
3. Wypchnij zmiany do `main` - GitHub Actions automatycznie wdroży frontend

## Rozwiązywanie problemów

### API nie odpowiada
```bash
docker compose -f docker-compose.prod.yml logs app
```

### Model nie ładuje się (OOM)
- Upewnij się, że masz min. 12GB RAM
- Sprawdź `LLAMA_N_GPU_LAYERS=0` w `.env.production`

### CORS błędy
- Sprawdź `CORS_ORIGINS` w `.env.production`
- Upewnij się, że URL GitHub Pages jest poprawny (z `https://`)

### SSL nie działa
- Sprawdź czy certyfikaty istnieją: `ls /etc/letsencrypt/live/`
- Sprawdź logi Nginx: `docker compose -f docker-compose.prod.yml logs nginx`
