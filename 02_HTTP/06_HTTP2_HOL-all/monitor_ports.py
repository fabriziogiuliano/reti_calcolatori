import psutil
import time
import argparse
import os
from collections import defaultdict

def clear_screen():
    """Pulisce lo schermo del terminale."""
    os.system('cls' if os.name == 'nt' else 'clear')

def monitor_process_connections(pid: int, interval: float = 0.5):
    """
    Monitora le connessioni di rete di un dato PID e mostra un riepilogo.
    """
    print(f"Inizio monitoraggio per il PID: {pid}")
    print("Premi Ctrl+C per terminare.")
    
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f"Errore: Nessun processo trovato con PID {pid}. Lo script di benchmark è in esecuzione?")
        return

    # Usiamo un set per tenere traccia delle porte sorgente uniche utilizzate
    unique_source_ports = set()
    
    try:
        while process.is_running():
            # Ottieni tutte le connessioni TCP per il processo
            connections = process.net_connections(kind='tcp')
            
            # Filtra solo le connessioni stabilite (ESTABLISHED)
            established_connections = [
                conn for conn in connections if conn.status == psutil.CONN_ESTABLISHED
            ]
            
            # Aggiorna il set di porte uniche
            for conn in established_connections:
                unique_source_ports.add(conn.laddr.port)

            # Stampa l'output in tempo reale
            clear_screen()
            print(f"--- Monitoraggio Connessioni per PID: {pid} ({process.name()}) ---")
            print(f"Ora: {time.strftime('%H:%M:%S')}\n")
            
            if not established_connections:
                print("Nessuna connessione TCP stabilita al momento...")
            else:
                print(f"Connessioni 'ESTABLISHED' attuali: {len(established_connections)}")
                print("-" * 40)
                print("Porta Locale  ->  Indirizzo Remoto:Porta Remota")
                for conn in established_connections:
                    # conn.laddr è l'indirizzo locale, conn.raddr è quello remoto
                    print(f"{conn.laddr.port:<13} ->  {conn.raddr.ip}:{conn.raddr.port}")
            
            print("\n" + "="*40)
            print(f"Riepilogo Porte Sorgente Uniche Usate Finora: {len(unique_source_ports)}")
            if unique_source_ports:
                # Stampa le porte in ordine per una migliore leggibilità
                print(sorted(list(unique_source_ports)))
            print("="*40)

            time.sleep(interval)
            
    except psutil.NoSuchProcess:
        print(f"\nIl processo con PID {pid} è terminato.")
    except KeyboardInterrupt:
        print("\nMonitoraggio interrotto dall'utente.")
    except Exception as e:
        print(f"\nSi è verificato un errore: {e}")

    print("\n--- Riepilogo Finale ---")
    print(f"Sono state utilizzate in totale {len(unique_source_ports)} porte sorgente uniche.")
    print(sorted(list(unique_source_ports)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitora le connessioni di rete di un processo tramite il suo PID."
    )
    parser.add_argument("pid", type=int, help="Il Process ID (PID) del processo da monitorare.")
    args = parser.parse_args()
    
    monitor_process_connections(args.pid)