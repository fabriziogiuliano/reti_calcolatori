# test_low_level_h2.py
import socket
import json
from h2.connection import H2Connection
from h2.events import ResponseReceived, DataReceived, StreamEnded

# -- Configurazioni --
HOST = '127.0.0.1'
PORT = 8000

# Apri una connessione TCP standard
sock = socket.create_connection((HOST, PORT))

# Inizializza la connessione H2 in modalità client
conn = H2Connection()
conn.initiate_connection()
sock.sendall(conn.data_to_send())

print("Connessione H2 iniziata...")

# Intestazioni per la richiesta GET alla root "/"
headers = [
    (':method', 'GET'),
    (':path', '/http2'),
    (':authority', HOST),
    (':scheme', 'http'),
]

# Invia la richiesta
stream_id = conn.send_headers(1, headers, end_stream=True)
sock.sendall(conn.data_to_send())
print(f"Richiesta GET inviata sullo stream {stream_id}...")

# Loop per ascoltare la risposta del server
body = b''
while True:
    data = sock.recv(65535)
    if not data:
        break

    events = conn.receive_data(data)
    for event in events:
        print(f"Evento ricevuto: {event}")
        if isinstance(event, ResponseReceived):
            print("\n--- RISPOSTA RICEVUTA ---")
            print(f"Intestazioni di risposta: {event.headers}")
        if isinstance(event, DataReceived):
            # Accumula i dati del corpo della risposta
            body += event.data
            # Acknowledge dei dati per il controllo di flusso
            conn.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
        if isinstance(event, StreamEnded):
            # Lo stream è terminato, possiamo uscire
            print("--- FINE DELLO STREAM ---")
            sock.sendall(conn.data_to_send())
            break
    else:
        continue
    break

# Stampa il corpo della risposta finale
print("\nCorpo della risposta completo:")
print(body.decode('utf-8'))

# Chiudi la connessione
conn.close_connection()
sock.sendall(conn.data_to_send())
sock.close()
print("\nConnessione chiusa.")