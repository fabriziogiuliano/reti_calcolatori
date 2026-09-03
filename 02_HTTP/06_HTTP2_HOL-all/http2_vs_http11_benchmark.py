# benchmark.py
import time
import asyncio
import matplotlib.pyplot as plt
import numpy as np
import httpx  # Lo usiamo ancora per il test HTTP/1.1

from h2.connection import H2Connection
from h2.events import ResponseReceived, DataReceived, StreamEnded, ConnectionTerminated, SettingsAcknowledged

HOST = '127.0.0.1'
PORT = 8000
NUMBER_OF_REQUESTS = 20
MAX_CONNECTION_H1 = 6 # Limite tipico dei browser per host per HTTP/1.1


# SEZIONE 1: CLIENT HTTP/2 

class H2Client:    
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._conn = H2Connection()
        self._reader = None
        self._writer = None
        self._next_stream_id = 1
        self._stream_queues = {}
        self._reader_task = None

    async def connect(self):
        """Stabilisce la connessione e avvia il task di lettura in background."""
        print("[H2Client] Connessione a {}:{}...".format(self._host, self._port))
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        
        self._conn.initiate_connection()
        self._writer.write(self._conn.data_to_send())
        await self._writer.drain()
        print("[H2Client] Connessione stabilita e H2 preface inviato.")
        
        self._reader_task = asyncio.create_task(self._read_responses_loop())

    async def _read_responses_loop(self):
        """Loop in background che legge dati dal socket e smista gli eventi H2 alle code corrette."""
        try:
            while True:
                data = await self._reader.read(65535)
                if not data:
                    break
                
                events = self._conn.receive_data(data)
                for event in events:
                    # Log per debug
                    # print(f"[H2Client Reader] Evento ricevuto: {event}")
                    
                    if isinstance(event, ConnectionTerminated):
                        # Se la connessione muore, notifica a tutte le richieste in attesa.
                        for queue in self._stream_queues.values():
                            await queue.put(event)
                        return

                    if hasattr(event, 'stream_id') and event.stream_id in self._stream_queues:
                        await self._stream_queues[event.stream_id].put(event)
                
                # Invia eventuali dati generati dalla ricezione (es. ACK dei settings)
                data_to_send = self._conn.data_to_send()
                if data_to_send:
                    self._writer.write(data_to_send)
                    await self._writer.drain()
        except asyncio.CancelledError:
            pass # Chiusura normale
        except Exception as e:
            print(f"[H2Client Reader] Errore critico nel loop di lettura: {e}")
            # Notifica a tutte le richieste in attesa dell'errore
            for queue in self._stream_queues.values():
                await queue.put(e)

    async def get(self, path):
        """Invia una richiesta GET e attende la sua risposta completa usando una coda dedicata."""
        stream_id = self._next_stream_id
        self._next_stream_id += 2
        
        queue = asyncio.Queue()
        self._stream_queues[stream_id] = queue

        headers = [
            (':method', 'GET'), (':path', path), (':authority', self._host), (':scheme', 'http'),
        ]
        
        self._conn.send_headers(stream_id, headers, end_stream=True)
        self._writer.write(self._conn.data_to_send())
        await self._writer.drain()
        
        # Attende gli eventi dalla coda fino alla fine dello stream
        while True:
            event = await queue.get()
            if isinstance(event, StreamEnded):
                break
            if isinstance(event, (ConnectionTerminated, Exception)):
                raise ConnectionError("La connessione si è interrotta durante la richiesta.")
        
        del self._stream_queues[stream_id]
        return "OK"

    async def close(self):
        """Chiude la connessione e ferma il task in background."""
        if self._reader_task:
            self._reader_task.cancel()
            await self._reader_task
        if self._writer:
            self._conn.close_connection()
            try:
                self._writer.write(self._conn.data_to_send())
                await self._writer.drain()
                self._writer.close()
                await self._writer.wait_closed()
            except ConnectionError:
                pass # La connessione potrebbe essere già chiusa
        print("[H2Client] Connessione chiusa.")



# BENCHMARK / PLOTTING

async def timed_fetch_h1(client, url, request_num):
    start_time = time.time()
    try:
        response = await client.get(url)
        print(f"H1 Richiesta {request_num}: Status {response.status_code}")
        return (start_time, time.time() - start_time, response.http_version, None)
    except Exception as e:
        print(f"H1 Richiesta {request_num} fallita: {e}")
        return (start_time, time.time() - start_time, "N/A", e)

async def timed_fetch_h2(client, path, request_num):
    start_time = time.time()
    try:
        await client.get(path)
        print(f"H2 Richiesta {request_num}: Status OK")
        return (start_time, time.time() - start_time, "HTTP/2", None)
    except Exception as e:
        print(f"H2 Richiesta {request_num} fallita: {e}")
        return (start_time, time.time() - start_time, "N/A", e)

def plot_results(h1_timings, h2_timings, duration_h1, duration_h2):
    # La tua funzione di plotting è perfetta e non necessita di modifiche.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
    plot_limit = max(duration_h1, duration_h2) * 1.1
    
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
    ax1.set_xlim(0, plot_limit)
    ax1.grid(axis='x', linestyle='--', alpha=0.6)
    for i, (start, duration) in enumerate(zip(h1_starts, h1_durations)):
        ax1.text(start + duration + 0.01, i, f'{duration:.2f}s', va='center', fontsize=8)
    total_duration_display_h1 = max(s + d for s, d in zip(h1_starts, h1_durations))
    ax1.axvline(x=total_duration_display_h1, color='red', linestyle='--', linewidth=1.5, label=f'Durata Totale ({total_duration_display_h1:.2f}s)')
    ax1.legend(loc='lower right')

    h2_test_start_time = min(t[0] for t in h2_timings)
    h2_starts = [t[0] - h2_test_start_time for t in h2_timings]
    h2_durations = [t[1] for t in h2_timings]
    
    ax2.barh(y_pos, h2_durations, left=h2_starts, align='center', color='skyblue')
    ax2.set_xlabel("Time (seconds)")
    ax2.set_title(f"HTTP/2 ({len(h2_timings)} requests)")
    ax2.set_xlim(0, plot_limit)
    ax2.grid(axis='x', linestyle='--', alpha=0.6)
    for i, (start, duration) in enumerate(zip(h2_starts, h2_durations)):
        ax2.text(start + duration + 0.01, i, f'{duration:.2f}s', va='center', fontsize=8)
    total_duration_display_h2 = max(s + d for s, d in zip(h2_starts, h2_durations))
    ax2.axvline(x=total_duration_display_h2, color='red', linestyle='--', linewidth=1.5, label=f'Durata Totale ({total_duration_display_h2:.2f}s)')
    ax2.legend(loc='lower right')

    fig.tight_layout()
    plt.suptitle("HTTP/1.1 vs HTTP/2 Performance Comparison", fontsize=16)
    fig.subplots_adjust(top=0.92)
    fig.savefig("http_vs_http2.pdf")
    plt.show()

# ====
# MAIN
# ====

async def main():
    # --- Test con HTTP/1.1 (usando httpx) ---
    print(f"--- Inizio Test HTTP/1.1 ({NUMBER_OF_REQUESTS} richieste) ---")
    url_h1 = f"http://{HOST}:{PORT}/http11"
    limits = httpx.Limits(max_connections=MAX_CONNECTION_H1)
    
    async with httpx.AsyncClient(http1=True, http2=False, limits=limits) as client:
        start_time_h1 = time.time()
        tasks = [timed_fetch_h1(client, url_h1, i+1) for i in range(NUMBER_OF_REQUESTS)]
        h1_timings = await asyncio.gather(*tasks)
        end_time_h1 = time.time()
    
    duration_h1 = end_time_h1 - start_time_h1
    print(f"Durata Totale HTTP/1.1: {duration_h1:.4f} secondi\n")

    # --- Test con HTTP/2 (usando il nostro H2Client robusto) ---
    print(f"--- Inizio Test HTTP/2 ({NUMBER_OF_REQUESTS} richieste) ---")
    path_h2 = "/http2"
    h2_client = H2Client(HOST, PORT)
    await h2_client.connect()

    start_time_h2 = time.time()
    tasks = [timed_fetch_h2(h2_client, path_h2, i+1) for i in range(NUMBER_OF_REQUESTS)]
    h2_timings = await asyncio.gather(*tasks)
    end_time_h2 = time.time()
    
    await h2_client.close()
    
    duration_h2 = end_time_h2 - start_time_h2
    print(f"Durata Totale HTTP/2: {duration_h2:.4f} secondi\n")

    # --- Riepilogo e Grafico ---
    print("--- Riepilogo del Confronto ---")
    print(f"HTTP/1.1: {duration_h1:.4f}s")
    print(f"HTTP/2:  {duration_h2:.4f}s")
    if duration_h2 < duration_h1:
        improvement = ((duration_h1 - duration_h2) / duration_h1) * 100
        print(f"\nHTTP/2 è stato più veloce del {improvement:.2f}%")

    plot_results(h1_timings, h2_timings, duration_h1, duration_h2)

if __name__ == "__main__":
    asyncio.run(main())