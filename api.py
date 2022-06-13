from flask import Flask, json, request
# from db import *
from decrypt import *
import json
import datetime
import base64

app = Flask('LoRaWAN API')

@app.route('/uplink', methods=['POST'])
def receive_uplink():
    uplink_json = request.json
    enc_data = uplink_json['data']
    enc_data = base64.b64decode(enc_data)
    dec_payload = door_decoder(enc_data)
    print(dec_payload)
    return "yeet", 200

@app.route('/joined', methods=['POST'])
def receive_join_request():
    join_json = request.json
    print(stuff)
    return "yeet", 200

@app.route('/ACK', methods=['POST'])
def receive_ACK():
    ACK_json = request.json
    print(stuff)
    return "yeet", 200

@app.route('/error', methods=['POST'])
def receive_error():
    error_json = request.json
    print(stuff)
    return "yeet", 200


#####UPLINK PACKET#####
# {
#     'applicationID':'1',
#     'applicationName':'Test-App',
#     'deviceName':'Dragino LDS01',
#     'devEUI':'a84041e46182965e',
#     'rxInfo':[
#         {
#             'mac':'24e124fffef47838',
#             'time':'2022-06-13T20:50:41.251515Z',
#             'rssi':-58,
#             'loRaSNR':13.8,
#             'name':'Local Gateway',
#             'latitude':38.04194,
#             'longitude':-84.49871,
#             'altitude':297
#         }
#     ],
#     'txInfo':{
#         'frequency':904100000,
#         'dataRate':{
#             'modulation':'LORA',
#             'bandwidth':125,
#             'spreadFactor':7
#         },
#         'adr':True,
#         'codeRate':'4/5'
#     },
#     'fCnt':6,
#     'fPort':10,
#     'data':'i9YBAAADAAANAA==',
#     'time':'2022-06-13T20:50:41.251515Z'
# }



# #route to create tables
# @app.route('/createtables', methods=['GET'])
# def create_tables():
#     result = -1
#     result1 = -1
#     lora_db = LoRaDB()
#     result, result1, result2 = lora_db.create_tables()

#     if result != -1 and result1 != -1 and result2 != -1:
#         return 'Tables created\n'
#     else:
#         return 'Could not create tables\n'
    

# # route to reset tables
# @app.route('/resettables', methods=['GET'])
# def reset_tables():
#     result =-1
#     result1 = -1
#     result2 = -1
#     lora_db = LoRaDB()
#     result, result1, result2 = lora_db.drop_tables()

#     if result != -1 and result1 != -1 and result2 != -1:
#         return 'Tables removed\n'
#     else:
#         return 'Could not remove tables\n'

# # register device
# @app.route('/register', methods=['POST'])
# def register_end_device():
#     try:
#         dev_json = request.get_json(force=True)
#         if 'dev_addr' not in dev_json or 'dev_eui' not in dev_json or 'app_eui' not in dev_json or 'app_key' not in dev_json or 'app_s_key' not in dev_json or 'net_s_key' not in dev_json or 'dev_type' not in dev_json:
#             raise Exception()
        
#         if len(dev_json['dev_addr']) != 8:
#             raise Exception() 
#         if len(dev_json['dev_eui']) != 16:
#             raise Exception() 
#         if len(dev_json['app_eui']) != 16:
#             raise Exception() 
#         if len(dev_json['app_key']) != 32:
#             raise Exception() 
#         if len(dev_json['app_s_key']) != 32:
#             raise Exception() 
#         if len(dev_json['net_s_key']) != 32:
#             raise Exception()
#         if len(dev_json['dev_type']) != 1: # 0 for gps, 1 for door sensor
#             raise Exception()
#     except:
#         return '''Malformed JSON: \'{"dev_addr": "XXXXXXXX", "dev_eui": "XXXXXXXXXXXXXXXX", 
#                     "app_eui": "XXXXXXXXXXXXXXXX", "app_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", 
#                     "app_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "net_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "dev_type": "X"}\'\n''', 400
    
#     lora_db = LoRaDB()
#     result = lora_db.register_device(dev_json['dev_addr'].upper(), dev_json['dev_eui'].upper(),dev_json['app_eui'].upper(),dev_json['app_key'].upper(),dev_json['app_s_key'].upper(),dev_json['net_s_key'].upper(), dev_json['dev_type'])

#     if result != -1:
#         return "Device Registered.\n", 200
#     else:
#         return "Could not add device to database\n", 500

# # retrieve device info
# @app.route('/getdevice/<string:dev_eui>', methods=['GET'])
# def get_device(dev_eui):
#     result = -1
#     lora_db = LoRaDB()
#     result = lora_db.get_device(dev_eui.upper())

#     if result != -1:
#         return 'Info for device EUI: ' + dev_eui + \
#         '\nDevice Addr: ' + result[0].decode("utf-8") + \
#         '\nApp EUI: ' +  result[2].decode("utf-8") + \
#         '\nApp Key: ' +  result[3].decode("utf-8") + \
#         '\nApp Session Key: ' +  result[4].decode("utf-8") + \
#         '\nNetwork Session Key: ' +  result[5].decode("utf-8") + '\n'
#     else:
#         return 'Could not retrieve device info\n'


# # remove device
# @app.route('/removedevice/<string:dev_eui>', methods=['GET'])
# def remove_device(dev_eui):
#     result = -1
#     lora_db = LoRaDB()
#     result = lora_db.remove_device(dev_eui.upper())

#     if result != 0 or result != -1:
#         return 'Removed device EUI: ' + dev_eui.upper() + '\n'
#     else:
#         return 'Could not remove device \n'

# # get all data from device (processed)
# @app.route('/getalldata/<string:dev_eui>', methods=['GET'])
# def get_all_device_data(dev_eui):
#     lora_db = LoRaDB()
#     result = lora_db.get_all_data_from_device(dev_eui)
#     if result != -1 or result != 0:
#         data = {}
#         for idx in range(0, len(result)):
#             data[idx] = json.loads(result[idx][0].decode())
#         return json.dumps(data, indent=1), 200
#     elif result == 0:
#         return "No data found for device: " + dev_eui + '\n', 404
#     else:
#         return "Could not get device data.\n", 500

# # get last data from device (processed)
# @app.route('/getlastdata/<string:dev_eui>', methods=['GET'])
# def get_last_device_data(dev_eui):
#     lora_db = LoRaDB()
#     result = lora_db.get_last_data_from_device(dev_eui)
#     if result != -1 or result != 0:
#         data = json.dumps({"0": json.loads(result[0].decode())}, indent=1)
#         return data, 200
#     elif result == 0:
#         return "No data found for device: " + dev_eui + '\n', 404
#     else:
#         return "Could not get device data.\n", 500

# # server status (ie stat messages from concentrator)  
# @app.route('/serverstatus/<string:net_id>', methods=['GET'])
# def get_server_status(net_id):
#     lora_db = LoRaDB()
#     result = lora_db.get_server_status(net_id.upper())
#     if result != -1 or result != 0:
#         return json.dumps({
#             "net_id": net_id.upper(),
#             "time": result[1].strftime('%Y-%m-%d %H:%M:%S'),
#             "rxnb": result[2],
#             "rxok": result[3],
#             "rxfw": result[4],
#             "ackr": result[5],
#             "dwnb": result[6],
#             "txnb": result[7]
#         }, indent=0)
#     elif result == 0:
#         return "No data found for server: " + net_id + '\n', 404 
#     else:
#         return "Could not get server data.\n", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8181) #192.168.1.125