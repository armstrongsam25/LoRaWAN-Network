import sys
import base64
from binascii import unhexlify
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def to_bytes(s):
	"""
	PY2/PY3 compatible way to convert to something cryptography understands
	"""
	if sys.version_info < (3,):
		return "".join(map(chr, s))
	else:
		return bytes(s)


def loramac_decrypt(payload_hex, sequence_counter, key, dev_addr, direction=0):
	"""
	LoraMac decrypt
	Which is actually encrypting a predefined 16-byte block (ref LoraWAN
	specification 4.3.3.1) and XORing that with each block of data.
	payload_hex: hex-encoded payload (FRMPayload)
	sequence_counter: integer, sequence counter (FCntUp)
	key: 16-byte hex-encoded AES key. (AppSKey)
	dev_addr: 4-byte hex-encoded DevAddr (i.e. AABBCCDD)
	direction: 0 for uplink packets, 1 for downlink packets
	returns an array of byte values.
	This method is based on `void LoRaMacPayloadEncrypt()` in
	https://github.com/Lora-net/LoRaMac-node/blob/master/src/mac/LoRaMacCrypto.c#L108
	"""

	key = unhexlify(key)
	dev_addr = unhexlify(dev_addr)
	buffer = bytearray(unhexlify(payload_hex))
	size = len(buffer)

	bufferIndex = 0
	# block counter
	ctr = 1

	# output buffer, initialize to input buffer size.
	encBuffer = [0x00] * size

	cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())

	def aes_encrypt_block(aBlock):
		"""
		AES encrypt a block.
		aes.encrypt expects a string, so we convert the input to string and
		the return value to bytes again.
		"""
		encryptor = cipher.encryptor()

		return bytearray(encryptor.update(to_bytes(aBlock)) + encryptor.finalize())

	# For the exact definition of this block refer to
	# 'chapter 4.3.3.1 Encryption in LoRaWAN' in the LoRaWAN specification
	aBlock = bytearray(
		[
			0x01,  # 0 always 0x01
			0x00,  # 1 always 0x00
			0x00,  # 2 always 0x00
			0x00,  # 3 always 0x00
			0x00,  # 4 always 0x00
			direction,  # 5 dir, 0 for uplink, 1 for downlink
			dev_addr[3],  # 6 devaddr, lsb
			dev_addr[2],  # 7 devaddr
			dev_addr[1],  # 8 devaddr
			dev_addr[0],  # 9 devaddr, msb
			sequence_counter & 0xFF,  # 10 sequence counter (FCntUp) lsb
			(sequence_counter >> 8) & 0xFF,  # 11 sequence counter
			(sequence_counter >> 16) & 0xFF,  # 12 sequence counter
			(sequence_counter >> 24) & 0xFF,  # 13 sequence counter (FCntUp) msb
			0x00,  # 14 always 0x01
			0x00,  # 15 block counter
		]
	)

	# complete blocks
	while size >= 16:
		aBlock[15] = ctr & 0xFF
		ctr += 1
		sBlock = aes_encrypt_block(aBlock)
		for i in range(16):
			encBuffer[bufferIndex + i] = buffer[bufferIndex + i] ^ sBlock[i]

		size -= 16
		bufferIndex += 16

	# partial blocks
	if size > 0:
		aBlock[15] = ctr & 0xFF
		sBlock = aes_encrypt_block(aBlock)
		for i in range(size):
			encBuffer[bufferIndex + i] = buffer[bufferIndex + i] ^ sBlock[i]

	return encBuffer


def GPS_decoder(GPS_data): 
	
	latitude=(GPS_data[0]<<24 | GPS_data[1]<<16 | GPS_data[2]<<8 | GPS_data[3])/1000000
	longitude= ((GPS_data[4]<<24 | GPS_data[5]<<16 | GPS_data[6]<<8 | GPS_data[7]) - 4294967296) /1000000 		# 429...  is 0x100000000 in base10
	alarm=True if GPS_data[8] & 0x40 else False
	batV=(((GPS_data[8] & 0x3f) <<8) | GPS_data[9])/1000
	
	motion_mode = "Disable"
	if GPS_data[10] & 0xC0 == 0x40:
		motion_mode="Move"

	elif GPS_data[10] & 0xC0 == 0x80:
		motion_mode="Collide"

	elif GPS_data[10] & 0xC0 == 0xC0:
		motion_mode="User"


	led_updown="ON" if GPS_data[10] & 0x20 else "OFF"

	firmware = 163+(GPS_data[10] & 0x1f)

	if len(GPS_data) > 11:
		roll=(GPS_data[11]<<24>>16 | GPS_data[12])/100

		pitch=(GPS_data[13]<<24>>16 | GPS_data[14])/100

		hdop = 0

		if GPS_data[15] > 0:
			hdop = GPS_data[15]/100

		else:
			hdop = GPS_data[15]

		altitude =(GPS_data[16]<<24>>16 | GPS_data[17]) / 100
		return {
			'Latitude': latitude,
			'Longitude': longitude,
			'Roll': roll,
			'Pitch':pitch,
			'BatV':batV,
			'Alarm':alarm,
			'MD':motion_mode,
			'LON':led_updown,
			'FW':firmware,
			'HDOP':hdop,
			'Altitude':altitude,
		}



	return {
		'Latitude': latitude,
		'Longitude': longitude,
		'BatV':batV,
		'Alarm':alarm,
		'MD':motion_mode,
		'LON':led_updown,
		'FW':firmware,
	}




if __name__ == '__main__': 

	# Send a join-accept packet
	
	
	

	# First check to see if the raw_payload is long enough
	# Then substring the MAC Payload to get the FRMPayload, DevAddr, f_cnt
	# Convert all of the above to hexstring
	# profit

	MAC_encoded = 'QPYtDCaADQAC4TDbVPvpwx5lCJ72RxTref2b9GGKsg==' #'QED/DCaACgAClkaBxXHE/bUnR+4TsIlhlMZxD2JdBw==' #44 bytes
	MAC_decoded = base64.b64decode(MAC_encoded).hex()

	# There is probably a better way to do this
	# Flipping byteorder
	x = int(MAC_decoded[2:10].encode('utf-8'), 16)
	dev_addr = (((x << 24) & 0xFF000000) |
			((x <<  8) & 0x00FF0000) |
			((x >>  8) & 0x0000FF00) |
			((x >> 24) & 0x000000FF))
	dev_addr = hex(dev_addr)[2:] #removing the 0x in front
	print("dev_addr: ", dev_addr)


	print("Encoded MAC: ", MAC_encoded)
	print("Encoded FRMPayload: ", MAC_encoded[12:36])
	print('Decoded FRM: ', base64.b64decode(MAC_encoded[12:36]).hex())

	
	# payload = '964681c571c4fdb52747ee13b0896194c671'
	# sequence_counter = 10
	# dev_addr = '260CFF40'

	AppSKey = '0916926F27EB9DF453A291CE5687A8D7' #AppSKey changes after each join...
	FRM_payload = base64.b64decode(MAC_encoded[12:36]).hex()
	f_cnt = int(MAC_decoded[12:14], 16)
	print("f_cnt: ", f_cnt)
	FRMPayload_decimal = loramac_decrypt(FRM_payload, f_cnt, AppSKey, dev_addr)

	print("Decoded FRMPayload:")
	for dec in FRMPayload_decimal:
		print('{:02x}'.format(dec),"", end='')
	print('\n')

	GPS_data = GPS_decoder(FRMPayload_decimal)

	print("LAT:\t", GPS_data['Latitude'])
	print("LON:\t", GPS_data['Longitude'])
	print("ALT:\t", GPS_data['Altitude'])
	print("ALARM:\t", GPS_data['Alarm'])
	print("BAT:\t", GPS_data['BatV'])
	print("ROLL:\t", GPS_data['Roll'])
	print("PITCH:\t", GPS_data['Pitch'])
	print("MOTION:\t", GPS_data['MD'])
	print("LED:\t", GPS_data['LON'])
	print("FW:\t", GPS_data['FW'])
	print("HDOP:\t", GPS_data['HDOP'])




