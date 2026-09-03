# Importa le funzioni necessarie da Scapy
from scapy.all import sniff, wrpcap
from scapy.arch import get_if_list, get_if_hwaddr
import sys

import socket
from urllib.parse import urlparse

TEST_URL = "http://httpbin.org/get"

def get_ip_address(url):
  try:
    # Extract the hostname from the URL
    hostname = urlparse(url).hostname
    if hostname:
      # Resolve the hostname to an IP address
      ip_address = socket.gethostbyname(hostname)
      return ip_address
    else:
      return "Invalid URL."
  except socket.gaierror:
    return f"Could not resolve the IP address for {url}"

def process_packet(packet):
    print("--- Pacchetto catturato dalla funzione di callback ---")
    # Mostra un breve riassunto del pacchetto
    print(packet.summary())
    print("-" * 50)

def packet_sniffer(interface, packet_count=0,output_file="caputre.pcap"):
    """
    Cattura i pacchetti su una data interfaccia e li salva su file.

    :param interface: Il nome dell'interfaccia di rete (es. 'eth0').
    :param packet_count: Il numero di pacchetti da catturare.
    :param output_file: Il nome del file .pcap in cui salvare i dati.
    """
    print(f"\n[*] Starting sniffing on interface '{interface}' for {packet_count} packets...")
    
    try:
        # La funzione sniff di Scapy cattura i pacchetti.
        # iface: specifica l'interfaccia di rete.
        # count: il numero di pacchetti da catturare (0 per infinito).
        # prn: una funzione da eseguire per ogni pacchetto catturato (opzionale, qui non usata).
        # store: True per memorizzare i pacchetti in memoria.
        
        
        
        ip_target = get_ip_address(TEST_URL)        
        filter=f"tcp and host TEST_URL"
        packets = sniff(iface=interface, filter=filter, count=packet_count, store=True, prn=process_packet)

        # Controlla se il nome del file ha l'estensione .pcap
        if not output_file.endswith('.pcap'):
            output_file += '.pcap'

        # Salva i pacchetti catturati nel file specificato usando wrpcap.
        print(f"[*] Sniffing finished. Saving {len(packets)} packets to '{output_file}'...")
        wrpcap(output_file, packets)
        print(f"[+] Capture saved successfully to '{output_file}'.")

    except PermissionError:
        print("\n[!] Permission Error: You need to run this script with root/administrator privileges.")
        print("    On Linux/macOS: use 'sudo python sniffer.py'")
        print("    On Windows: run your terminal as Administrator.")
        sys.exit(1)
    except OSError as e:
        print(f"\n[!] Error: Unable to sniff on interface '{interface}'.")
        print(f"    Please ensure the interface name is correct and active. Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":    
    output_filename = "capture.pcap" # Nome di default se l'utente non inserisce nulla

    # 5. Avvia lo sniffer
    packet_sniffer("en0", 0, output_filename)
    
    

"""
**IMPORTANTE:** Lo sniffing di rete richiede privilegi elevati. Devi eseguire lo script come amministratore (su Windows) o con `sudo` (su Linux e macOS).

1.  Salva il codice in un file chiamato `sniffer.py`.
2.  Apri un terminale o un prompt dei comandi **come amministratore**.
3.  Naviga fino alla cartella in cui hai salvato il file.
4.  Esegui lo script con il seguente comando:

    **Su Linux o macOS:**
    ```bash
    sudo python3 sniffer.py
    ```

    **Su Windows (in un terminale aperto come Amministratore):**
    ```bash
    python sniffer.py
    ```

5.  Segui le istruzioni a schermo: scegli l'interfaccia, il numero di pacchetti e il nome del file.

### 4. Come Analizzare il File .pcap Generato

Una volta che lo script ha terminato, avrai un file `.pcap` nella stessa cartella. Puoi analizzarlo con i tool standard del settore:

*   **Wireshark (Metodo Grafico):**
    1.  Apri Wireshark.
    2.  Vai su `File` -> `Open`.
    3.  Seleziona il file `.pcap` che hai creato (es. `cattura.pcap`).
    4.  Potrai navigare, filtrare e ispezionare tutti i pacchetti catturati.

*   **tcpdump (Metodo da Riga di Comando):**
    1.  Apri un terminale.
    2.  Usa il seguente comando per leggere il contenuto del file:
        ```bash
        tcpdump -r cattura.pcap
        ```
    3.  Questo comando stamperà un riassunto dei pacchetti contenuti nel file direttamente sul terminale.

### Considerazioni Etiche e Legali

Ricorda che lo sniffing di rete può avere implicazioni per la privacy e la sicurezza. **Cattura il traffico solo su reti che possiedi o per le quali hai esplicita autorizzazione.** L'uso improprio di questi strumenti può essere illegale.
"""