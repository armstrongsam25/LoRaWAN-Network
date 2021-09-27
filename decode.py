import json
import base64


base64_in = input("Enter base64: ")

data = bytearray(base64_in, 'utf8')


hex_bytes = base64.b64decode(data)

lat = hex_bytes[0:4]
lon = hex_bytes[4:8]

lat_int = int.from_bytes(lat, byteorder = 'little', signed=False)
lon_int = int.from_bytes(lon, byteorder = 'little', signed=False)

lat_val = lat_int/1000000
lon_val = (lon_int - 4294967296)/1000000 # 4294... is 0x100000000

print("LAT: ", lat_val)
print("LON: ", lon_val, '\n')
