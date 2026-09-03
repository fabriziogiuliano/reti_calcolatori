import httpx
import time
import asyncio

# URL dei server di test
HTTP1_URL = "http://httpbin.org/get"
HTTP2_URL = "https://nghttp2.org/httpbin/get"

def test_http1_request():
    """
    Esegue una singola richiesta a un server HTTP/1.1.
    """
    print("--- Test HTTP/1.1 ---")
    with httpx.Client() as client:
        start_time = time.time()
        try:
            response = client.get(HTTP1_URL)
            end_time = time.time()

            print(f"URL: {HTTP1_URL}")
            print(f"Versione HTTP utilizzata: {response.http_version}")
            print(f"Status Code: {response.status_code}")
            print(f"Tempo impiegato: {end_time - start_time:.4f} secondi")
        except httpx.RequestError as exc:
            print(f"Si è verificato un errore durante la richiesta: {exc}")
    print("-" * 25)


def test_http2_request():
    """
    Esegue una singola richiesta a un server HTTP/2.
    """
    print("--- Test HTTP/2 (richiesta singola) ---")
    # http2=True abilita il supporto per HTTP/2
    with httpx.Client(http2=True) as client:
        start_time = time.time()
        try:
            response = client.get(HTTP2_URL)
            end_time = time.time()

            print(f"URL: {HTTP2_URL}")
            print(f"Versione HTTP utilizzata: {response.http_version}")
            print(f"Status Code: {response.status_code}")
            print(f"Tempo impiegato: {end_time - start_time:.4f} secondi")
        except httpx.RequestError as exc:
            print(f"Si è verificato un errore durante la richiesta: {exc}")
    print("-" * 25)


async def test_http2_multiplexing():
    """
    Dimostra il multiplexing di HTTP/2 inviando più richieste in parallelo
    sulla stessa connessione.
    """
    print("--- Test HTTP/2 (richieste multiple in parallelo) ---")
    MAX_REQUESTS=2
    async with httpx.AsyncClient(http2=True) as client:
        tasks = []
        start_time = time.time()
        
        # Crea MAX_REQUESTS richieste da eseguire in concorrenza
        for _ in range(MAX_REQUESTS):
            tasks.append(client.get(HTTP2_URL))
        
        try:
            responses = await asyncio.gather(*tasks)
            end_time = time.time()

            print(f"Inviate {MAX_REQUESTS} richieste a {HTTP2_URL}")
            
            # Controlla la versione HTTP della prima risposta
            if responses:
                print(f"Versione HTTP utilizzata (verificata sulla prima risposta): {responses[0].http_version}")
            
            print(f"Tempo totale per {MAX_REQUESTS} richieste: {end_time - start_time:.4f} secondi")

            for i, response in enumerate(responses):
                if response.status_code != 200:
                    print(f"Richiesta {i+1} fallita con status code: {response.status_code}")

        except httpx.RequestError as exc:
            print(f"Si è verificato un errore durante le richieste: {exc}")
    print("-" * 25)


if __name__ == "__main__":
    #test_http1_request()
    #test_http2_request()
    asyncio.run(test_http2_multiplexing())