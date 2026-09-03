import requests
from urllib.parse import urlparse
import pickle
import os

# ============================================================
# Script unificato sui cookie HTTP.
# Nasce dalla fusione di due versioni precedenti:
#   - una che mandava un cookie fisso via requests.get(cookies=...)
#   - una che usava una Session con persistenza su file (pickle)
# Copre entrambi i TODO che erano rimasti aperti:
#   1. input utente per definire un nuovo cookie
#   2. persistenza dei cookie su file locale tra un'esecuzione e l'altra
# ============================================================

HTTP_VERSION_MAP = {10: 'HTTP/1.0', 11: 'HTTP/1.1', 20: 'HTTP/2'}

# File dei cookie salvato accanto allo script, non nella cwd di chi lo lancia
COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_cookies.pkl')

BASE_URL = 'https://nghttp2.org/httpbin'
URL_GET_COOKIES = f'{BASE_URL}/cookies'


def http_version(response):
    return HTTP_VERSION_MAP.get(response.raw.version, 'HTTP/?.?')


def print_request_headers(req, version_label='HTTP/1.1'):
    """Stampa la request in stile raw HTTP, evidenziando l'header Cookie."""
    parsed_url = urlparse(req.url)
    path = parsed_url.path or '/'
    if parsed_url.query:
        path += '?' + parsed_url.query

    print(f"{req.method} {path} {version_label}")
    for header, value in req.headers.items():
        if header == 'Cookie':
            print(f"\033[1m{header}: {value}\033[0m  <-- COOKIE INVIATO QUI")
        else:
            print(f"{header}: {value}")
    print()


def print_response_headers(res):
    """Stampa la response in stile raw HTTP, evidenziando l'header Set-Cookie."""
    print(f"{http_version(res)} {res.status_code} {res.reason}")
    for header, value in res.headers.items():
        if header == 'Set-Cookie':
            print(f"\033[1m{header}: {value}\033[0m  <-- COOKIE IMPOSTATO QUI")
        else:
            print(f"{header}: {value}")
    print()


def save_cookies(session):
    with open(COOKIE_FILE, 'wb') as f:
        pickle.dump(session.cookies, f)
    print(f"--- Cookie salvati in: {COOKIE_FILE} ---\n")


def load_cookies():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'rb') as f:
            print(f"--- Trovato file di cookie ({COOKIE_FILE}), caricamento... ---")
            return pickle.load(f)
    print("--- Nessun file di cookie trovato. Si parte con una sessione pulita. ---")
    return None


def ask_new_cookie():
    """TODO 1 risolto: chiede all'utente se vuole definire un nuovo cookie."""
    print("--- Vuoi impostare un nuovo cookie? (premi INVIO per saltare) ---")
    name = input("Nome cookie: ").strip()
    if not name:
        return None
    value = input("Valore cookie: ").strip()
    return name, value


def main():
    # 1. Crea una Session e prova a caricare i cookie salvati in precedenza
    print("--- Creazione della Sessione HTTP ---")
    session = requests.Session()
    saved_cookies = load_cookies()
    if saved_cookies:
        session.cookies.update(saved_cookies)
        print(f"Cookie caricati nella sessione: {session.cookies.get_dict()}\n")
    else:
        print("Sessione creata senza cookie preesistenti.\n")

    # 2. Eventuale nuovo cookie richiesto dall'utente
    new_cookie = ask_new_cookie()
    if new_cookie:
        name, value = new_cookie
        if session.cookies.get(name) == value:
            print(f">>> Il cookie '{name}={value}' è già presente in sessione, nessuna richiesta necessaria.\n")
        else:
            url_set_cookie = f'{BASE_URL}/cookies/set/{name}/{value}'
            print(f"--- Richiesta a {url_set_cookie} per impostare il cookie ---")
            response_set = session.get(url_set_cookie)
            initial_response = response_set.history[0] if response_set.history else response_set

            print("\n-------------------------")
            print("--- RAW HTTP RESPONSE (Set-Cookie) ---")
            print_response_headers(initial_response)
            print(f"Cookie ora in sessione: {session.cookies.get_dict()}\n")
            print("-------------------------\n")
    else:
        print(">>> Nessun nuovo cookie richiesto, si controllano quelli già presenti.\n")

    # 3. Richiesta finale per verificare cosa il server vede lato suo
    print(f"--- Invio di una richiesta a {URL_GET_COOKIES} per verificare i cookie attuali ---")
    response_check = session.get(URL_GET_COOKIES)

    print("\n-------------------------")
    print("--- RAW HTTP REQUEST (Check) ---")
    print_request_headers(response_check.request, http_version(response_check))
    print("--- RESPONSE BODY (Check) ---")
    print(response_check.text)
    print("-------------------------\n")

    # 4. Persistenza: salva la sessione per la prossima esecuzione (TODO 2 risolto)
    print("--- Salvataggio dei cookie della sessione per usi futuri... ---")
    save_cookies(session)

    print("--- Script terminato. Rilancialo per vedere i cookie caricati e riutilizzati. ---")


if __name__ == '__main__':
    main()
