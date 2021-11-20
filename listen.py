import socket
import json
import base64
import datetime
from decrypt import *
# import join ##switched to ABP so no need for join requests
from binascii import unhexlify
from db import *
import time


# TODO: add config file
#		put devices in there
#		debug flag


def print_GPS(GPS_data):
	print('\n')
	print("LAT:\t", GPS_data['Latitude'])
	print("LON:\t", GPS_data['Longitude'])
	print("ALARM:\t", GPS_data['Alarm'])
	print("BAT:\t", GPS_data['BatV'])
	print("MOTION:\t", GPS_data['MD'])
	print("LED:\t", GPS_data['LON'])
	print("FW:\t", GPS_data['FW'])
	#print("ALT:\t", GPS_data['Altitude']) # can change settings on device to get these
	#print("ROLL:\t", GPS_data['Roll'])
	#print("PITCH:\t", GPS_data['Pitch'])
	#print("HDOP:\t", GPS_data['HDOP'])
	print('\n')

def handle_uplink(payload, raw_payload):
	# parse the device address from the received data
	x = int(payload[:8].encode('utf-8'), 16)
	dev_addr = (((x << 24) & 0xFF000000) | ((x << 8) & 0x00FF0000) | ((x >> 8) & 0x0000FF00) |((x >> 24) & 0x000000FF))
	dev_addr = hex(dev_addr)[2:]
	if len(dev_addr) == 7: 		#will probably need to change this eventually to handle leading zeros in dev address
		dev_addr = '0' + dev_addr
	
	# grab the app_s_key from the db if the device has been registered
	lora_db = LoRaDB()
	dev_info = lora_db.get_device_by_addr(dev_addr)
	if dev_info == -1:
		print("[INFO]\t Packet with device address:", dev_addr, " not registered with the server.\n")
		return
	app_s_key = dev_info[0].decode()
	dev_type = dev_info[1]

	#parse the function counter part of the data
	f_cnt = payload[10:14]
	f_cnt = int("".join(reversed([f_cnt[i:i+2] for i in range(0, len(f_cnt), 2)])),16)

	# parse the FRM_Payload (the gps data is here)
	FRM_payload = payload[16:]
	print('[DEBUG]\t FRMPayload: ' + FRM_payload)
	print('[DEBUG]\t F_CNT: ', f_cnt, ' Payload Length: ', len(payload))

	# decrypt the encrypted packet
	result = loramac_decrypt(FRM_payload.upper(), f_cnt, app_s_key , dev_addr, direction=0)
	
	#if debug:
	for dec in result:
		print('{:02x}'.format(dec),"", end='')
	print('\n')

	# decode the gps data and print the result if valid
	try:
		GPS_data = GPS_decoder(result)
		print_GPS(GPS_data)

		GPS_data_json = json.dumps(GPS_data, indent=0)
		lora_db = LoRaDB()
		result = lora_db.insert_data(raw_payload, dev_type, GPS_data_json, dev_addr)
	except:
		print("\nGPS Location Not Found.\n")


if __name__ == '__main__':
	UDP_IP = "127.0.0.1"
	UDP_PORT = 1700

	sock = socket.socket(socket.AF_INET, # Internet
						socket.SOCK_DGRAM) # UDP
	sock.bind((UDP_IP, UDP_PORT))
	while True:
		data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
		data = bytearray(data)
		protocol_version = bytes(data[0])
		random_token = bytes(data[1-2])
		push_data_id = bytes(data[3])
		gateway_id = bytes(data[4-11])
		
		if len(data) > 12:
			json_string = data[12:len(data)].decode('utf-8','ignore')
			try:
				packet = json.loads(json_string)
			except:
				packet = json_string
			
			if "rxpk" in packet:
				raw_data = packet['rxpk'][0]['data'] # get the data we care about
				data_from_packet = base64.b64decode(raw_data).hex() # decode it and make it hex
				packet_length = len(data_from_packet)

				MHDR = data_from_packet[0:2]	# first byte
				MACPayload = data_from_packet[2:packet_length-8] # from 2nd byte until the length-8th byte
				MIC = data_from_packet[-8:packet_length] # verify message integrity

				print("+------------------------------------------------------------------+")
				print('[DEBUG]\t Base64 Data: ', raw_data)
				print("[DEBUG]\t Data: " + data_from_packet)
				print("[DEBUG]\t MHDR: " + MHDR)
				print("[DEBUG]\t MACPayload: " + MACPayload)
				print("[DEBUG]\t MIC: " + MIC)
				print("+------------------------------------------------------------------+\n")
				
				# Bit shift the MHDR to get the type of message being sent
				end_length = len(MHDR) * 4
				MHDR_bin = int(MHDR, 16)
				MHDR_bin = bin(MHDR_bin>>5)
				MTYPE = MHDR_bin[2:].zfill(end_length)

				if MTYPE == "00000000":
					#Join-Request
					print("[INFO]\t Received Join-Request")
				elif MTYPE == "00000010":
					#Unconfirmed Uplink
					print("[INFO]\t Received Unconfirmed Uplink")
					try:
						handle_uplink(MACPayload.upper(), raw_data)
					except:
						print('[ERROR]\t There was a problem parsing the packet: ', raw_data)
			elif "stat" in packet:
				print('DEBUG]\t Packet: ', packet)
				result1 = -1
				lora_db = LoRaDB()
				lora_db.connect()
				if lora_db.does_table_exist('l_servers') and lora_db.is_connected():
					result = lora_db.executeSelect('SELECT COUNT(*) from l_servers WHERE net_id = %s',('00DEAD',))
					if result[0] >= 1:
						date = packet['stat']['time'][:len(packet['stat']['time']) -3]
						result1 = lora_db.execute('UPDATE l_servers SET time=%s,rxnb=%s,rxok=%s,rxfw=%s,ackr=%s,dwnb=%s,txnb=%s WHERE net_id=%s',
											(date,packet['stat']['rxnb'],packet['stat']['rxok'],packet['stat']['rxfw'],packet['stat']['ackr'],packet['stat']['dwnb'],packet['stat']['txnb'],'00DEAD'))
					elif result[0] == 0:
						date = packet['stat']['time'][:len(packet['stat']['time']) -3]
						result1 = lora_db.execute('''INSERT INTO l_servers (net_id,time,rxnb,rxok,rxfw,ackr,dwnb,txnb) 
													VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''', 
												('00DEAD',date,packet['stat']['rxnb'],packet['stat']['rxok'],packet['stat']['rxfw'],packet['stat']['ackr'],packet['stat']['dwnb'],packet['stat']['txnb']))
				if result1 != -1:
					print('[INFO]\t Server Status Uploaded.')
				else:
					print('[ERROR]\t Could NOT Upload Server Status.')
				lora_db.close()
				print('\n')