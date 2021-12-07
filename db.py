import mysql.connector
from mysql.connector import Error

DEBUG = False

class LoRaDB:
    def __init__(self):
        self.host = 'localhost'
        self.dbname = 'LoRaWAN_DB'
        self.user = 'root'
        self.password = 'raspberry'
        self.connection = -1
        self.cursor = -1

    def create_tables(self):
        result = -1
        result1 = -1
        result2 = -1
        self.connect()
        if self.is_connected():
            result = self.execute('''
                                        CREATE TABLE IF NOT EXISTS l_devices (
                                            dev_addr CHAR(8) NOT NULL,
                                            dev_eui CHAR(16) NOT NULL,
                                            app_eui CHAR(16) NOT NULL,
                                            app_key CHAR(32) NOT NULL,
                                            app_s_key CHAR(32) NOT NULL,
                                            net_s_key CHAR(32) NOT NULL,
                                            dev_type INT NOT NULL,
                                            PRIMARY KEY (dev_eui));''',())
            result1 = self.execute('''
                                        CREATE TABLE IF NOT EXISTS l_servers (
                                            net_id CHAR(6) NOT NULL,
                                            time DATETIME NOT NULL,
                                            rxnb INTEGER,
                                            rxok INTEGER,
                                            rxfw INTEGER,
                                            ackr INTEGER,
                                            dwnb INTEGER,
                                            txnb INTEGER,
                                            PRIMARY KEY (net_id))''',())
            result2 = self.execute('''
                                        CREATE TABLE IF NOT EXISTS l_packets (
                                            uuid INT NOT NULL AUTO_INCREMENT,
                                            time DATETIME NOT NULL,
                                            rawdata VARCHAR(255) NOT NULL,
                                            datatype INTEGER, 
                                            parseddata TEXT,
                                            devaddr CHAR(8) NOT NULL,
                                            PRIMARY KEY (uuid))''',()) # datatype = 0 if gps otherwise 1
        self.close()
        return result, result1, result2

    def connect(self):
        try:
            self.connection = mysql.connector.connect(host=self.host, database=self.dbname, user=self.user, password=self.password)
            if self.connection.is_connected():
                db_Info = self.connection.get_server_info()
                if DEBUG:
                    print("[DEBUG]\t Connected to MySQL Server version ", db_Info)
                self.cursor = self.connection.cursor(prepared=True)
                return db_Info

        except Error as e:
            print("[ERROR]\t ", e)
            return -1
    
    def is_connected(self):
        if self.connection == -1:
            return False
        else:
            return True

    def does_table_exist(self, tablename):
        self.cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s", (tablename,))
        if self.cursor.fetchone()[0] == 1:
            return True
        return False

    def drop_tables(self):
        result = -1
        self.connect()
        if self.is_connected():
            result = self.execute('DROP TABLE IF EXISTS l_devices', ()) # add more tables here
            result1 = self.execute('DROP TABLE IF EXISTS l_servers', ()) # add more tables here
            result2 = self.execute('DROP TABLE IF EXISTS l_packets', ()) # add more tables here
        self.close()
        return result, result1, result2

    def register_device(self, dev_addr, dev_eui, app_eui, app_key, app_s_key, net_s_key, dev_type):
        result = -1
        self.connect()
        if self.is_connected():
            result = self.execute('''
                                        INSERT INTO l_devices (dev_addr, dev_eui, app_eui, app_key, app_s_key, net_s_key, dev_type) 
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    ''', (dev_addr, dev_eui, app_eui, app_key, app_s_key, net_s_key, dev_type))
        self.close()
        return result

    def get_device(self, dev_eui):
        result = -1
        self.connect()
        if self.does_table_exist('l_devices') and self.is_connected():
            result = self.executeSelect('SELECT * FROM l_devices WHERE dev_eui = %s', (dev_eui,)) 
        self.close()
        return result
    
    def get_device_by_addr(self, dev_addr):
        result = -1
        self.connect()
        if self.does_table_exist('l_devices') and self.is_connected():
            result = self.executeSelect('SELECT app_s_key, dev_type FROM l_devices WHERE dev_addr = %s', (dev_addr,)) 
        self.close()
        return result
    
    def get_all_data_from_device(self, dev_eui):
        result = -1
        self.connect()
        if self.does_table_exist('l_devices') and self.does_table_exist('l_packets') and self.is_connected():
            result = self.executeSelectAll('SELECT parseddata FROM l_packets WHERE devaddr IN (SELECT dev_addr FROM l_devices WHERE dev_eui = %s)', (dev_eui,)) 
        self.close()
        return result
    
    def get_last_data_from_device(self, dev_eui):
        result = -1
        self.connect()
        if self.does_table_exist('l_devices') and self.does_table_exist('l_packets') and self.is_connected():
            result = self.executeSelect('SELECT parseddata FROM l_packets WHERE devaddr IN (SELECT dev_addr FROM l_devices WHERE dev_eui = %s) ORDER BY time DESC LIMIT 1', (dev_eui,)) 
        self.close()
        return result
    
    def remove_device(self, dev_eui):
        result = -1
        self.connect()
        if self.does_table_exist('l_devices') and self.is_connected():
            result = self.execute('DELETE FROM l_devices WHERE dev_eui = %s', (dev_eui,))
        self.close()
        return result

    def get_server_status(self, net_id):
        result = -1
        self.connect()
        if self.does_table_exist('l_servers') and self.is_connected():
            result = self.executeSelect('SELECT * FROM l_servers WHERE net_id = %s', (net_id,)) 
        self.close()
        return result

    def execute(self, stmt, args):
        try:
            self.cursor.execute(stmt, args)
            self.connection.commit()
            result = self.cursor.rowcount
            return result
        except Error as e:
            print('[ERROR]\t ', e)
            return -1

    def executeSelect(self, stmt, args):
        try:
            self.cursor.execute(stmt, args)
            result = self.cursor.fetchone()
            if result == None:
                return -1
            return result
        except Error as e:
            print('[ERROR]\t ', e)
            return -1
    
    def executeSelectAll(self, stmt, args):
        try:
            self.cursor.execute(stmt, args)
            result = self.cursor.fetchall()
            if result == None:
                return -1
            return result
        except Error as e:
            print('[ERROR]\t ', e)
            return -1

    def insert_data(self, raw_data, data_type, json_data, dev_addr):
        result = -1
        self.connect()
        if self.is_connected():
            result = self.execute('''
                                        INSERT INTO l_packets (time, rawdata, datatype, parseddata, devaddr) 
                                        VALUES (NOW(), %s, %s, %s, %s)
                                    ''', (raw_data, data_type, json_data, dev_addr))
        self.close()
        return result
    
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.cursor = -1
            self.connection.close()
            self.connection = -1
            if DEBUG:
                print("[DEBUG]\t MySQL connection closed")