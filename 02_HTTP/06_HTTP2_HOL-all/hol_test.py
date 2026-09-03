import httpx
import time
import asyncio
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURAZIONE DELLO SCRIPT ---

DELAY = 0.01
#SERVICE_URL ="https://nghttp2.org/httpbin"

#SERVICE_URL = "http://localhost:8000"

#SERVICE_URL ="https://httpbin.io"
#SERVICE_URL="https://postman-echo.com"
#SERVICE_URL="http://httpbin.org"
#SERVICE_URL="http://3.230.216.40"

#BASE_URL = f"{SERVICE_URL}/delay/{DELAY}"
BASE_URL = "http://localhost:8000"
#BASE_URL = "https://postman-echo.com/get"
#BASE_URL = "https://nghttp2.org/httpbin/get"



NUMBER_OF_REQUESTS = 20
MAX_CONNECTION=10
# --- FUNZIONI DI FETCH ---
async def timed_fetch(client, url, request_num):
    start_time = time.time()
    try:
        response = await client.get(url)
        end_time = time.time()
        print(f"Richiesta {request_num}: Status {response.status_code} (Protocollo: {response.http_version})")
        return (start_time, end_time - start_time, response.http_version, None)
    except Exception as e:
        end_time = time.time()
        print(f"Richiesta {request_num} fallita: {e}")
        return (start_time, end_time - start_time, "N/A", e)

async def fetch_all_and_collect_timings(client, urls):
    tasks = [timed_fetch(client, url, i+1) for i, url in enumerate(urls)]
    results = await asyncio.gather(*tasks)
    return results

# --- FUNZIONE PER CREARE IL GRAFICO ---
def plot_results(h1_timings, h2_timings, duration_h1, duration_h2):
    """
    Crea un grafico a cascata con una scala dell'asse X comune
    per un confronto visivo immediato.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
    
    # Calcola il limite comune per l'asse X, con un 10% di margine
    plot_limit = max(duration_h1, duration_h2) * 1.1
    
    # --- Grafico HTTP/1.1 ---
    h1_test_start_time = min(t[0] for t in h1_timings)
    h1_starts = [t[0] - h1_test_start_time for t in h1_timings]
    h1_durations = [t[1] for t in h1_timings]
    y_pos = np.arange(len(h1_timings))
    
    ax1.barh(y_pos, h1_durations, left=h1_starts, align='center', color='coral')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([f'Req {i+1}' for i in range(len(h1_timings))])
    ax1.invert_yaxis()
    ax1.set_xlabel("Time (seconds)")
    ax1.set_title(f"HTTP/1.1 ({len(h1_timings)} requests)")
    ax1.set_xlim(0, plot_limit) # Imposta il limite X
    ax1.grid(axis='x', linestyle='--', alpha=0.6) # Aggiunge una griglia per leggibilità

    # Aggiungi etichette di durata sulle barre
    for i, (start, duration) in enumerate(zip(h1_starts, h1_durations)):
        ax1.text(start + duration + 0.01, i, f'{duration:.2f}s', va='center', fontsize=8)

    ax1.axvline(x=max(h1_durations), color='red', linestyle='--', linewidth=1.5, label=f'Durata Totale ({max(h1_durations):.2f}s)')
    ax1.legend(loc='lower right')

    # --- Grafico HTTP/2 ---
    h2_test_start_time = min(t[0] for t in h2_timings)
    h2_starts = [t[0] - h2_test_start_time for t in h2_timings]
    h2_durations = [t[1] for t in h2_timings]
    
    ax2.barh(y_pos, h2_durations, left=h2_starts, align='center', color='skyblue')
    ax2.set_xlabel("Time (seconds)")
    ax2.set_title(f"HTTP/2 ({len(h2_timings)} requests)")
    ax2.set_xlim(0, plot_limit) # Imposta LO STESSO limite X
    ax2.grid(axis='x', linestyle='--', alpha=0.6)

# Aggiungi etichette di durata sulle barre
    for i, (start, duration) in enumerate(zip(h2_starts, h2_durations)):
        ax2.text(start + duration + 0.01, i, f'{duration:.2f}s', va='center', fontsize=8)

    ax2.axvline(x=max(h2_durations), color='red', linestyle='--', linewidth=1.5, label=f'Durata Totale ({max(h2_durations):.2f}s)')
    ax2.legend(loc='lower right')

    fig.tight_layout()
    plt.suptitle("HTTP/1.1 vs HTTP/2 ", fontsize=16)
    fig.subplots_adjust(top=0.92)
    fig.savefig("http_vs_http2.pdf")
    plt.show()
    

# --- FUNZIONE MAIN (con chiamata a plot_results modificata) ---
async def main():
    
    t_test_start = time.time()
    
    #urls_to_fetch = [BASE_URL + str(i) for i in range(NUMBER_OF_REQUESTS)]
    http_url = f"{BASE_URL}/http11"
    urls_to_fetch = [http_url for i in range(NUMBER_OF_REQUESTS)]
    # --- Test con HTTP/1.1 ---
    print(f"--- Inizio Test HTTP/1.1 ({NUMBER_OF_REQUESTS} richieste concorrenti) ---")
    limits = httpx.Limits(max_connections=MAX_CONNECTION)
    headers = {"Connection": "keep-alive"}
    async with httpx.AsyncClient(http1=True, http2=False, limits=limits, headers=headers, timeout=30) as client:
        start_time_h1 = time.time()
        h1_timings = await fetch_all_and_collect_timings(client, urls_to_fetch)
        end_time_h1 = time.time()
    
    duration_h1 = end_time_h1 - start_time_h1
    print(f"Durata Totale HTTP/1.1: {duration_h1:.4f} secondi\n")    
    
    # --- Test con HTTP/2 ---
    print(f"--- Inizio Test HTTP/2 ({NUMBER_OF_REQUESTS} richieste concorrenti) ---")
    #limits = httpx.Limits(max_connections=100)
    http_url = f"{BASE_URL}/http2"
    urls_to_fetch = [http_url for i in range(NUMBER_OF_REQUESTS)]
    async with httpx.AsyncClient(http2=True, timeout=30, transport=httpx.AsyncHTTPTransport(http2=True)) as client:
        start_time_h2 = time.time()

        h2_timings = await fetch_all_and_collect_timings(client, urls_to_fetch)
        end_time_h2 = time.time()
        
    duration_h2 = end_time_h2 - start_time_h2
    print(f"Durata Totale HTTP/2: {duration_h2:.4f} secondi\n")

    # --- Riepilogo Finale ---
    print("--- Riepilogo del Confronto ---")
    print(f"HTTP/1.1: {duration_h1:.4f}s")
    print(f"HTTP/2:  {duration_h2:.4f}s")
    if duration_h2 < duration_h1:
        improvement = ((duration_h1 - duration_h2) / duration_h1) * 100
        print(f"\nHTTP/2 è stato più veloce del {improvement:.2f}%")
    else:
        print("\nHTTP/1.1 è risultato più veloce in questo test (inatteso).")

    # --- Creazione del Grafico ---
    print("\nAdesso mostro il grafico a cascata...")
    # Passiamo le durate alla funzione di plotting
    plot_results(h1_timings, h2_timings, duration_h1, duration_h2)

if __name__ == "__main__":
    asyncio.run(main())