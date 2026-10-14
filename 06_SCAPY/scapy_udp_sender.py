#!/usr/bin/env python

from scapy.all import *

# 1. Definisci la destinazione del pacchetto
ip_destinazione = "127.0.0.1"  # 127.0.0.1 significa "questo stesso computer" (localhost)
porta_destinazione = 8888

# 2. Definisci i dati (payload) da inviare
payload = os.urandom(30)


# 3. Forgia il pacchetto strato per strato
#    - IP():      Crea l'intestazione IP. Mettiamo solo la destinazione.
#                 Scapy troverà l'IP sorgente da solo.
#    - UDP():     Crea l'intestazione UDP. Mettiamo solo la porta di destinazione.
#                 Scapy sceglierà una porta sorgente a caso.
#    - Raw():     Contiene i nostri dati grezzi (il messaggio).
#
#    L'operatore "/" serve a impilare i livelli uno dentro l'altro.
pacchetto = IP(dst=ip_destinazione) / UDP(dport=porta_destinazione,sport=55555) / Raw(load=payload)

print("--- Pacchetto che sto per inviare: ---")
pacchetto.show()
print("--------------------------------------")

# 5. Invia il pacchetto sulla rete
send(pacchetto)

print(f"\nPacchetto inviato a {ip_destinazione}:{porta_destinazione}!")