#!/usr/bin/env python3
from scapy.all import *

print("Script in esecuzione...")
print("Avvio della shell interattiva di Scapy. Digita 'exit()' per tornare allo script.")

# Questa funzione blocca l'esecuzione dello script e avvia la shell di Scapy
interact()

# Il codice qui sotto verrà eseguito solo dopo che avrai chiuso la shell di Scapy
print("\nShell di Scapy terminata. Lo script riprende e ora termina.")