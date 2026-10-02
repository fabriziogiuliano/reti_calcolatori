import requests
ip="192.33.14.30"
response = requests.get(f"https://geolocation-db.com/json/{ip}&position=true").json()

print(response)