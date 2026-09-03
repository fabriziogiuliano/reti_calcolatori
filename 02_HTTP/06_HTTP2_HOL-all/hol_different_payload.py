import httpx
import time
import asyncio
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle

# --- CONFIGURAZIONE DELLO SCRIPT ---

# Lista di dimensioni dei payload in KiloByte da richiedere in ciclo.
PAYLOAD_SIZES_KB = [10, 50, 5, 200, 25, 80, 10000] 
PAYLOAD_SIZES_KB = [200]

BASE_URL_PAYLOAD = "https://httpbin.org/stream-bytes/"

NUMBER_OF_REQUESTS = 50
MAX_H1_CONNECTIONS = 6

# --- FUNZIONE DI FETCH (invariata) ---
async def timed_fetch_detailed(client, url, request_num, payload_size_kb):
    request_start_time = time.time()
    try:
        async with client.stream("GET", url) as response:
            ttfb_time = time.time()
            ttfb_duration = ttfb_time - request_start_time
            
            body = await response.aread()
            download_end_time = time.time()
            download_duration = download_end_time - ttfb_time
            
            total_duration = download_end_time - request_start_time
            
            print(
                f"Req {request_num:02d} ({payload_size_kb}KB): "
                f"Proto: {response.http_version}, "
                f"TTFB: {ttfb_duration:.3f}s, "
                f"Download: {download_duration:.3f}s, "
                f"Totale: {total_duration:.3f}s"
            )
            
            return (request_start_time, ttfb_duration, download_duration, response.http_version, None)
            
    except Exception as e:
        end_time = time.time()
        print(f"Richiesta {request_num} fallita: {e}")
        return (request_start_time, 0, end_time - request_start_time, "N/A", e)

async def fetch_all_and_collect_timings(client, urls_with_payloads):
    tasks = [timed_fetch_detailed(client, url, i+1, payload_kb) for i, (url, payload_kb) in enumerate(urls_with_payloads)]
    results = await asyncio.gather(*tasks)
    return results

# --- FUNZIONE PER CREARE IL GRAFICO (CON MODIFICA ALL'ORDINAMENTO) ---
def _plot_single_stacked_waterfall(ax, timings, total_duration, title, plot_limit):
    abs_starts = [t[0] for t in timings]
    ttfb_durations = [t[1] for t in timings]
    download_durations = [t[2] for t in timings]
    
    test_start_time = min(abs_starts)
    rel_starts = [s - test_start_time for s in abs_starts]
    y_pos = np.arange(len(timings))

    # === MODIFICA CHIAVE: INVERTIAMO I DATI PER PLOTTARE REQ 1 IN ALTO ===
    # Invece di invertire l'asse, invertiamo l'ordine dei dati prima di disegnarli.
    # Questo è più intuitivo e garantisce che Req 1 sia sempre in cima.
    plot_rel_starts = rel_starts[::-1]
    plot_ttfb_durations = ttfb_durations[::-1]
    plot_download_durations = download_durations[::-1]
    
    # Anche le etichette devono essere create nell'ordine inverso
    plot_labels = [f'Req {len(timings) - i}' for i in range(len(timings))]

    # 1. Disegna le barre del TTFB
    ax.barh(y_pos, plot_ttfb_durations, left=plot_rel_starts, align='center', color='coral', label='TTFB', height=0.6)
    
    # 2. Disegna le barre del Download
    download_starts = [s + t for s, t in zip(plot_rel_starts, plot_ttfb_durations)]
    ax.barh(y_pos, plot_download_durations, left=download_starts, align='center', color='skyblue', label='Download', height=0.6)

    # Impostazioni del grafico
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_labels) # Usa le etichette invertite
    
    # NON invertiamo più l'asse Y, perché i dati sono già nell'ordine corretto
    # ax.invert_yaxis()  <-- QUESTA RIGA È STATA RIMOSSA
    
    ax.set_xlabel("Tempo (secondi)")
    ax.set_title(title)
    ax.set_xlim(0, plot_limit)
    ax.grid(axis='x', linestyle='--', alpha=0.6)

    ax.axvline(x=total_duration, color='red', linestyle='--', linewidth=1.5, label=f'Durata Totale ({total_duration:.2f}s)')
    ax.legend(loc='lower right')


def plot_results(h1_timings, h2_timings, duration_h1, duration_h2):
    #fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12), sharey=True) # Aumentata dimensione per leggibilità
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)

    plot_limit = max(duration_h1, duration_h2) * 1.1

    h1_title = f"HTTP/1.1 ({len(h1_timings)} richieste, {MAX_H1_CONNECTIONS} connessioni)"
    _plot_single_stacked_waterfall(ax1, h1_timings, duration_h1, h1_title, plot_limit)

    h2_title = f"HTTP/2 ({len(h2_timings)} richieste, 1 connessione)"
    _plot_single_stacked_waterfall(ax2, h2_timings, duration_h2, h2_title, plot_limit)

    fig.tight_layout()
    #plt.suptitle("Confronto Waterfall Dettagliato: TTFB vs Download Time", fontsize=18, y=0.98) # Aggiunto titolo
    fig.savefig("http_vs_http2_detailed.pdf")
    plt.show()

# --- FUNZIONE MAIN (invariata) ---
async def main():
    payload_cycle = cycle(PAYLOAD_SIZES_KB)
    
    urls_with_payloads = []
    for i in range(NUMBER_OF_REQUESTS):
        payload_kb = next(payload_cycle)
        url = f"{BASE_URL_PAYLOAD}{payload_kb * 1024}"
        urls_with_payloads.append((url, payload_kb))

    # Imposta un timeout più generoso per gestire anche i payload grandi
    timeout_config = httpx.Timeout(60.0, connect=10.0)

    # --- Test con HTTP/1.1 ---
    print(f"--- Inizio Test HTTP/1.1 ({NUMBER_OF_REQUESTS} richieste, {MAX_H1_CONNECTIONS} connessioni max) ---")
    limits = httpx.Limits(max_connections=MAX_H1_CONNECTIONS, max_keepalive_connections=MAX_H1_CONNECTIONS)
    async with httpx.AsyncClient(http1=True, http2=False, limits=limits, timeout=timeout_config) as client:
        start_time_h1 = time.time()
        h1_timings = await fetch_all_and_collect_timings(client, urls_with_payloads)
        end_time_h1 = time.time()
    
    duration_h1 = end_time_h1 - start_time_h1
    print(f"\nDurata Totale HTTP/1.1: {duration_h1:.4f} secondi\n")

    # --- Test con HTTP/2 ---
    print(f"--- Inizio Test HTTP/2 ({NUMBER_OF_REQUESTS} richieste concorrenti) ---")
    async with httpx.AsyncClient(http2=True, timeout=timeout_config) as client:
        start_time_h2 = time.time()
        h2_timings = await fetch_all_and_collect_timings(client, urls_with_payloads)
        end_time_h2 = time.time()
        
    duration_h2 = end_time_h2 - start_time_h2
    print(f"\nDurata Totale HTTP/2: {duration_h2:.4f} secondi\n")

    # --- Riepilogo Finale ---
    print("--- Riepilogo del Confronto ---")
    print(f"HTTP/1.1 ({MAX_H1_CONNECTIONS} connessioni): {duration_h1:.4f}s")
    print(f"HTTP/2   (1 connessione):  {duration_h2:.4f}s")
    if duration_h2 < duration_h1:
        improvement = ((duration_h1 - duration_h2) / duration_h1) * 100
        print(f"\nHTTP/2 è stato più veloce del {improvement:.2f}%")
    else:
        print("\nHTTP/1.1 è risultato più veloce in questo test (inatteso).")

    print("\nAdesso mostro il grafico a cascata dettagliato...")
    plot_results(h1_timings, h2_timings, duration_h1, duration_h2)

if __name__ == "__main__":
    
    import os
    print(f"--- AVVIATO SCRIPT DI BENCHMARK ---")
    print(f"--- PID di questo processo: {os.getpid()} ---") # <-- AGGIUNGI QUESTA RIGA
    print("--- Avviare lo script di monitoraggio in un altro terminale con questo PID. ---")
    time.sleep(5) # Diamo qualche secondo per avviare il monitor
    
    asyncio.run(main())