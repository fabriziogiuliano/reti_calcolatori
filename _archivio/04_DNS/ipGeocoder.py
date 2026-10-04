import geocoder


#Assign IP address to a variable
#ip = geocoder.ip("147.163.1.3")
ip = geocoder.ip("3.104.50.254") #MIT

#Obtain the city
print(ip.city)

#Obtain the coordinates: 
print(ip.latlng)