import requests
import time

# Cambia il server con uno che supporta correttamente keep-alive
SERVICE_URL = "http://httpbin.org" 
TEST_URL = f"{SERVICE_URL}/get"

print("--- Ispezionando gli header di risposta da nghttp2.org ---")
try:
    with requests.Session() as session:
        response = session.get(TEST_URL)
        print(f"Status Code: {response.status_code}")
        print("Header di risposta ricevuti:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
except requests.exceptions.RequestException as e:
    print(f"La richiesta è fallita: {e}")

print("-" * 50 + "\n")