from flask import Flask, json, request
from db import *

app = Flask('LoRaWAN API')

#route to create tables
@app.route('/createtables', methods=['GET'])
def create_tables():
    
    result = -1
    result1 = -1
    lora_db = LoRaDB()
    result, result1, result2 = lora_db.create_tables()

    if result != -1 and result1 != -1 and result2 != -1:
        return 'Tables created\n'
    else:
        return 'Could not create tables\n'
    

#route to reset tables
@app.route('/resettables', methods=['GET'])
def reset_tables():
    result =-1
    result1 = -1
    result2 = -1
    lora_db = LoRaDB()
    result, result1, result2 = lora_db.drop_tables()

    if result != -1 and result1 != -1 and result2 != -1:
        return 'Tables removed\n'
    else:
        return 'Could not remove tables\n'

# register device
@app.route('/register', methods=['POST'])
def register_end_device():
    try:
        dev_json = request.get_json(force=True)
        if 'dev_addr' not in dev_json or 'dev_eui' not in dev_json or 'app_eui' not in dev_json or 'app_key' not in dev_json or 'app_s_key' not in dev_json or 'net_s_key' not in dev_json or 'dev_type' not in dev_json:
            raise Exception()
        
        if len(dev_json['dev_addr']) != 8:
            raise Exception() 
        if len(dev_json['dev_eui']) != 16:
            raise Exception() 
        if len(dev_json['app_eui']) != 16:
            raise Exception() 
        if len(dev_json['app_key']) != 32:
            raise Exception() 
        if len(dev_json['app_s_key']) != 32:
            raise Exception() 
        if len(dev_json['net_s_key']) != 32:
            raise Exception()
        if len(dev_json['dev_type']) != 1: # 0 for gps, 1 for door sensor
            raise Exception()
    except:
        return '''Malformed JSON: \'{"dev_addr": "XXXXXXXX", "dev_eui": "XXXXXXXXXXXXXXXX", 
                    "app_eui": "XXXXXXXXXXXXXXXX", "app_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", 
                    "app_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "net_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "dev_type": "X"}\'\n''', 400
    
    lora_db = LoRaDB()
    result = lora_db.register_device(dev_json['dev_addr'].upper(), dev_json['dev_eui'].upper(),dev_json['app_eui'].upper(),dev_json['app_key'].upper(),dev_json['app_s_key'].upper(),dev_json['net_s_key'].upper(), dev_json['dev_type'])

    if result != -1:
        return "Device Registered.\n", 200
    else:
        return "Could not add device to database\n", 500
    
    
    

# retrieve device info
@app.route('/getdevice/<string:dev_eui>', methods=['GET'])
def get_device(dev_eui):
    result = -1
    lora_db = LoRaDB()
    result = lora_db.get_device(dev_eui.upper())

    if result != -1:
        return 'Info for device EUI: ' + dev_eui + \
        '\nDevice Addr: ' + result[0].decode("utf-8") + \
        '\nApp EUI: ' +  result[2].decode("utf-8") + \
        '\nApp Key: ' +  result[3].decode("utf-8") + \
        '\nApp Session Key: ' +  result[4].decode("utf-8") + \
        '\nNetwork Session Key: ' +  result[5].decode("utf-8") + '\n'
    else:
        return 'Could not retrieve device info\n'


# remove device
@app.route('/removedevice/<string:dev_eui>', methods=['GET'])
def remove_device(dev_eui):
    result = -1
    lora_db = LoRaDB()
    result = lora_db.remove_device(dev_eui.upper())

    if result != 0 or result != -1:
        return 'Removed device EUI: ' + dev_eui.upper() + '\n'
    else:
        return 'Could not remove device \n'

# get most recent data from device (raw, and processed)
@app.route('/getdata/<string:dev_eui>', methods=['GET'])
def get_device_data(dev_eui):
    return 'todo'

# (maybe) set data from device
@app.route('/setdata/<string:dev_eui>', methods=['POST'])
def set_device_data(dev_eui):
    dev_json = request.get_json(force=True)
    return 'todo'

# server status (ie stat messages from concentrator)  
@app.route('/serverstatus', methods=['GET'])
def get_server_status():
    return 'todo'


if __name__ == '__main__':
    app.run(host='localhost', port=42069)