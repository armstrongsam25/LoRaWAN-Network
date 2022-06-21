from ipaddress import NetmaskValueError
from multiprocessing.pool import ApplyResult
import socket
import json
import base64
import datetime
from decrypt import *
# import join ##switched to ABP so no need for join requests
from binascii import unhexlify
from db import *
import time
from datetime import datetime
from floranet.floranet.lora.mac import *
from floranet.floranet.lora.bands import *
import random

DEBUG = True

def print_GPS(GPS_data):
	print('\n')
	print('--------Decoded GPS Data--------')
	print("LAT:\t", GPS_data['Latitude'])
	print("LON:\t", GPS_data['Longitude'])
	print("ALARM:\t", GPS_data['Alarm'])
	print("BAT:\t", GPS_data['BatV'])
	print("MOTION:\t", GPS_data['MD'])
	print("LED:\t", GPS_data['LON'])
	print("FW:\t", GPS_data['FW'])
	print("ALT:\t", GPS_data['Altitude']) # can change settings on device to get these
	print("ROLL:\t", GPS_data['Roll'])
	print("PITCH:\t", GPS_data['Pitch'])
	print("HDOP:\t", GPS_data['HDOP'])
	print('\n')

def print_door(door_data):
	print('--------Decoded Door Data--------')
	print("BAT:\t\t\t", door_data['BAT_V'])
	print("MOD:\t\t\t", door_data['MOD'])
	print("DOOR OPEN STATUS:\t", door_data['DOOR_OPEN_STATUS'])
	print("TIMES DOOR OPENED:\t", door_data['DOOR_OPEN_TIMES'])
	print("LAST DOOR OPEN DURATION\t", door_data['LAST_DOOR_OPEN_DURATION']) # this is in minutes so probably 0
	print("ALARM:\t\t\t", door_data['ALARM'])

def handle_join(MHDR, MAC_payload, MIC):
	# Next get the AppEUI | DevEUI | DevNonce
	AppEUI = MAC_payload[:16]
	AppEUI = "".join(reversed([AppEUI[i:i+2] for i in range(0, len(AppEUI), 2)]))
	DevEUI = MAC_payload[16:32]
	DevEUI = "".join(reversed([DevEUI[i:i+2] for i in range(0, len(DevEUI), 2)]))
	DevNonce = MAC_payload[-4:]
	DevNonce = "".join(reversed([DevNonce[i:i+2] for i in range(0, len(DevNonce), 2)]))

	# Next verify the deveui is registered, and get the AppKey
	# query to database
	lora_db = LoRaDB()
	dev_info = lora_db.get_device(DevEUI)
	if dev_info == -1:
		print("[INFO]\t Join request:", DevEUI, " not registered with the server.")
		return

	## if it isn't display error message
	## if it is then verify MIC
	AppKey = dev_info['app_key']
	JRM = JoinRequestMessage(MHDR, AppEUI, DevEUI, DevNonce, MIC)
	isMICok = JRM.checkMIC(int(AppKey, 16)) # this is the app key
	if not isMICok:
		print('[WARNING]\t Could not verify join request MIC, skipping.')
		return -1

	#if MIC OK then form JoinAcceptMessage
	AppNonce = hex(random.randrange(0, 16777215))[2:]
	NetID = '00DEAD'
	DevAddr = dev_info['dev_addr']
	DLSettings = 0
	RXDelay = 5
	#appkey, appnonce, netid, devaddr, dlsettings, rxdelay, cflist=[]
	JAM = JoinAcceptMessage(
		int(AppKey, 16),
		int(AppNonce, 16),
		int(NetID, 16), 
		int(DevAddr, 16),
		DLSettings, 
		RXDelay
	)

	# derive the netskey and appskey and save in db
	netskey = JRM.derive_skey(0x01, JAM)
	appskey = JRM.derive_skey(0x02, JAM)
	print("NetSKey: ", netskey)
	print("AppSKey: ", appskey)

	# db query to update session keys
	rowsUpdated = lora_db.update_dev_skeys(DevEUI, netskey, appskey)
	if rowsUpdated == 0:
		print("[ERROR}\t Could not update device session keys, skipping.")
		return -1

	# create the join accept message
	print("Join Accept Payload: ", JAM.encode().hex())

	return JAM.encode().hex()


def handle_uplink(payload, raw_payload):
	# parse the device address from the received data
	x = int(payload[:8].encode('utf-8'), 16)
	dev_addr = (((x << 24) & 0xFF000000) | ((x << 8) & 0x00FF0000) | ((x >> 8) & 0x0000FF00) |((x >> 24) & 0x000000FF))
	dev_addr = hex(dev_addr)[2:]
	if len(dev_addr) == 7: 		# TODO will probably need to change this eventually to handle leading zeros in dev address
		dev_addr = '0' + dev_addr
	
	# grab the app_s_key from the db if the device has been registered
	lora_db = LoRaDB()
	dev_info = lora_db.get_device_by_addr(dev_addr)
	if dev_info == -1:
		print("[INFO]\t Packet with device address:", dev_addr, " not registered with the server.")
		return
	app_s_key = dev_info['app_s_key'].decode()
	dev_type = dev_info['dev_type']

	#parse the function counter part of the data
	f_cnt = payload[10:14]
	f_cnt = int("".join(reversed([f_cnt[i:i+2] for i in range(0, len(f_cnt), 2)])),16)

	# parse the FRM_Payload (the gps data is here)
	FRM_payload = payload[16:]
	if DEBUG:
		print('[DEBUG]\t FRMPayload: ' + FRM_payload)
		print('[DEBUG]\t F_CNT: ', f_cnt, ' Payload Length: ', len(payload))

	# decrypt the encrypted packet
	result = loramac_decrypt(FRM_payload.upper(), f_cnt, app_s_key , dev_addr, direction=0)
	
	if DEBUG:
		for dec in result:
			print('{:02x}'.format(dec),"", end='')
		print('\n')

	# decode the gps data and print the result if valid
	if dev_type == 0:
		print('[INFO]\t Attempting to decode GPS data...')
		try:
			GPS_data = GPS_decoder(result)
			print_GPS(GPS_data)

			GPS_data_json = json.dumps(GPS_data, indent=0)
			lora_db = LoRaDB()
			result = lora_db.insert_data(raw_payload, dev_type, GPS_data_json, dev_addr)
			if result != -1:
				print('[INFO]\t GPS data uploaded.')
			else:
				print('[ERROR]\t GPS data could not be uploaded.')
		except:
			print("[ERROR] GPS Location Not Found.")
	# decode the door data and print the result if valid
	elif dev_type == 1:
		print('[INFO]\t Attempting to decode door data...')
		try:
			door_data = door_decoder(result)
			print_door(door_data)

			door_data_json = json.dumps(door_data, indent=0)
			lora_db = LoRaDB()
			result = lora_db.insert_data(raw_payload, dev_type, door_data_json, dev_addr)
			if result != -1:
				print('[INFO]\t Door data uploaded.')
			else:
				print('[ERROR]\t Door data could not be uploaded.')
		except :
			print("[ERROR] Could not decrypt door data.")

def send_data_to_sensor(payload, gateway_tx_freq, gateway_datr):
	#{'rxpk': [{'tmst': 415327476, 'time': '2022-06-17T18:03:56.120815Z', 'chan': 6, 'rfch': 1, 'freq': 905.1, 'stat': 1, 'modu': 'LORA', 'datr': 'SF10BW125', 'codr': '4/5', 'lsnr': 11.2, 'rssi': -47, 'size': 23, 'data': 'AAcBAAAAAACgXpaCYeRBQKhiGRPtGSM='}]}
	#{"txpk":{"imme":false,"tmst":1886440700,"freq":925.7,"rfch":1,"powe":20,"modu":"LORA","datr":"SF10BW500","codr":"4/5","ipol":true,"size":17,"data":"ffOO"}}
	payload_length = str(int(len(payload) / 2))
	payload = base64.b64encode(bytes.fromhex(payload)) # bytes to base64
	payload = payload.decode('utf-8') # base64 bytes to string
	payload = payload.replace("=", "") # remove padding per spec
	print(payload)
	txpk = '{"txpk":{"imme":true,"time":"'+datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S GMT")+'","freq":'+str(gateway_tx_freq)+',"rfch":0,"powe":14,"modu":"LORA","datr":"'+gateway_datr+'","codr":"4/5","ipol":true,"size":'+payload_length+',"data":"'+payload+'"}}'
	return txpk




if __name__ == '__main__':
	UDP_IP = "127.0.0.1"
	UDP_PORT = 1700

	sock = socket.socket(socket.AF_INET, # Internet
						socket.SOCK_DGRAM) # UDP
	sock.bind((UDP_IP, UDP_PORT))
	while True:
		data, source_addr = sock.recvfrom(1024) # buffer size is 1024 bytes
		data = bytearray(data)
		#print(data)
		protocol_version = data[0]
		random_token = data[1:2]
		push_data_id = data[3]
		gateway_id = data[4:11]
		# print("Protocol Ver: ", protocol_version)
		# print("Random Token: ", random_token)
		# print("Push Data ID: ", push_data_id)
		# print("Gateway ID: ", gateway_id)
		# print('\n')
		
		if len(data) > 12:
			json_string = data[12:len(data)].decode('utf-8','ignore')
			try:
				packet = json.loads(json_string)
			except:
				packet = json_string
			
			if "rxpk" in packet:
				raw_data = packet['rxpk'][0]['data'] # get the data we care about
				#print("Raw data: ", raw_data)
				data_from_packet = base64.b64decode(raw_data).hex() # decode it and make it hex
				#print("Raw Hex data: ", data_from_packet)
				packet_length = len(data_from_packet)

				MHDR = data_from_packet[0:2]	# first byte
				MACPayload = data_from_packet[2:packet_length-8] # from 2nd byte until the length-8th byte
				MIC = data_from_packet[-8:packet_length] # verify message integrity

				if DEBUG:
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
					#{'rxpk': [{'tmst': 415327476, 'time': '2022-06-17T18:03:56.120815Z', 'chan': 6, 'rfch': 1, 'freq': 905.1, 'stat': 1, 'modu': 'LORA', 'datr': 'SF10BW125', 'codr': '4/5', 'lsnr': 11.2, 'rssi': -47, 'size': 23, 'data': 'AAcBAAAAAACgXpaCYeRBQKhiGRPtGSM='}]}
					#Join-Request
					print("[INFO]\t Received Join-Request.")
					#try:
					JAPayload = handle_join(MHDR, MACPayload.upper(), MIC)
					if JAPayload != -1:
						txpk = send_data_to_sensor(JAPayload, 923.9, "SF7BW500") # gateway can broadcast from 923.0-928.0, https://www.thethingsnetwork.org/airtime-calculator
						txpk_bytes = bytearray(txpk.encode())
						random_down_token = random.randint(0,255)
						header_bytes = bytearray([2, random_down_token, 3])
						header_bytes = header_bytes + gateway_id
						whole_shebang = header_bytes + txpk_bytes
						print(whole_shebang)
						bytes_sent = sock.sendto(whole_shebang, ("127.0.0.1", 1700))
					#except:
						#print(["ERROR\t There was a problem parsing the packet: ", raw_data])
					print('\n')
				elif MTYPE == "00000010":
					#Unconfirmed Uplink
					print("[INFO]\t Received Unconfirmed Uplink.")
					try:
						handle_uplink(MACPayload.upper(), raw_data)
					except:
						print('[ERROR]\t There was a problem parsing the packet: ', raw_data)
					print('\n')
			elif "stat" in packet:
				print("[INFO]\t Received Server Status.")
				if DEBUG:
					print('[DEBUG]\t Packet: ', packet)
				result1 = -1
				lora_db = LoRaDB()
				lora_db.connect()
				if lora_db.does_table_exist('l_servers') and lora_db.is_connected():
					result = lora_db.executeSelect('SELECT COUNT(*) from l_servers WHERE net_id = %s',('00DEAD',))
					if result['COUNT(*)'] >= 1:
						date = packet['stat']['time'][:len(packet['stat']['time']) -3]
						result1 = lora_db.execute('UPDATE l_servers SET time=%s,rxnb=%s,rxok=%s,rxfw=%s,ackr=%s,dwnb=%s,txnb=%s WHERE net_id=%s',
											(date,packet['stat']['rxnb'],packet['stat']['rxok'],packet['stat']['rxfw'],packet['stat']['ackr'],packet['stat']['dwnb'],packet['stat']['txnb'],'00DEAD'))
					elif result['COUNT(*)'] == 0:
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