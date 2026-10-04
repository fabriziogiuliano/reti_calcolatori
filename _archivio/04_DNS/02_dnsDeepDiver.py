import dns.resolver
import requests
import json

# fatto da Francesco Virgilia 03/10/2024
# Abbellito con le indentazioni e grafichine da ChatGPT
# Fonti: https://stackoverflow.com/questions/24678308/how-to-find-location-with-ip-address-in-python, materiale del professore

def ipToLocation(ip):
    try:
        response = requests.get(f"https://geolocation-db.com/json/{ip}&position=true").json()
        location_info = {
            'Country': response.get('country_name', 'Unknown'),
            'State': response.get('state', 'Unknown'),
            'City': response.get('city', 'Unknown'),
            'Latitude': response.get('latitude', 'Unknown'),
            'Longitude': response.get('longitude', 'Unknown'),
        }
        return location_info
    except Exception as e:
        return {'Error': f'Impossibile ottenere la geolocalizzazione: {e}'}


def resolveIp(value):
    try:
        result = dns.resolver.resolve(str(value), 'A')
        ips = [ip.address for ip in result]
        return ips
    except dns.resolver.NoAnswer:
        return None
    except dns.exception.DNSException as e:
        print(f"Errore durante la risoluzione IP per {value}: {e}")
        return None

# Hostname da risolvere
hostname = "youtube.com"

# Ciclo attraverso vari tipi di record DNS
for record_type in ["A", "MX", "CNAME", "NS", "AAAA", "PTR"]:
    try:
        result = dns.resolver.resolve(hostname, record_type)
        print(f"\n{'='*10} {record_type} Record {'='*10}")
        for val in result:
            print(f"\nRecord trovato: {val}")

            # Per A e AAAA, già abbiamo IP
            if record_type in ["A", "AAAA"]:
                ip_info = ipToLocation(val)
                print(f" ➤ IP: {val}")
                print(f"   🌍 Geolocalizzazione: {json.dumps(ip_info, indent=4)}")

            # Risolvi IP per MX, CNAME, NS, PTR
            elif record_type in ["MX", "CNAME", "NS", "PTR"]:
                if record_type == "MX":
                    hostname_mx = val.exchange
                    print(f" ➤ Hostname MX: {hostname_mx}")
                    ips = resolveIp(hostname_mx)
                else:
                    ips = resolveIp(val)

                if ips:
                    for ip in ips:
                        ip_info = ipToLocation(ip)
                        print(f" ➤ IP: {ip}")
                        print(f"   🌍 Geolocalizzazione: {json.dumps(ip_info, indent=4)}")
                else:
                    print(" ➤ Nessun IP associato.")
    except dns.resolver.NoAnswer:
        print(f"Nessuna risposta per il record di tipo {record_type}.")
    except dns.exception.DNSException as e:
        print(f"Errore durante la risoluzione del tipo {record_type}: {e}")
