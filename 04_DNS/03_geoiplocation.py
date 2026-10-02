import socket
import requests
from ip2geotools.databases.noncommercial import DbIpCity
#DbIpCity HostIP Freegeoip Ipstack MaxMindGeoLite2City Ip2Location
from geopy.distance import distance

def printDetails(ip):
    res = DbIpCity.get(ip, api_key="free")
    print(f"IP Address: {res.ip_address}")
    print(f"Location: {res.city}, {res.region}, {res.country}")
    print(f"Coordinates: (Lat: {res.latitude}, Lng: {res.longitude})")

printDetails("192.42.177.30")