import os
import threading
from constants import*
from mqtt import Mqtt
import sqlite3
import subprocess
import time
import json
def DHCPserver():
        if(connection):
            os.system("sudo ifconfig eth0 "+EDGE_IP)
            os.system("sudo ip route add "+ SUBNET+"/24 via "+EDGE_IP)
            os.system(f"sudo python {DHCPserverAddress}")
def NatWlan():
    os.system("sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE")
def check_connection():
    global connection
    connection=False
    while True:
        pingResult = subprocess.run(['ping', '-c', '4', '8.8.8.8'], capture_output=True)
        if(pingResult.returncode==0):
            connection=True
            
        else:
            connection=False
        time.sleep(2)
def get_mac_address(interface):
    try:
        with open(f"/sys/class/net/{interface}/address", "r") as f:
            mac_address = f.read().strip()
            return mac_address
    except FileNotFoundError:
        return None
def check_connection_mqtt():
    flag=0
    publish_flag=0
    while True:
        # pdb.set_trace()
        if(connection):
            if flag==0:
                    # pdb.set_trace()
                    mqtt_instance=edgeMqtt("tunnel_down",mac_address+"_update",CENTRAL_IP,True)
                    # mqtt_instance.Start()
                    flag=1
            # 
            # print(mqtt_instance.connected)
            if not mqtt_instance.connected:
            #     # pdb.set_trace()
                # print(mqtt_instance.connected)
                mqtt_instance.Start()
                publish_flag=0
                time.sleep(1)
            if (mqtt_instance.connected and not publish_flag):
                mqtt_instance.Publish("tunnel_up",json.dumps({"mac_address":mac_address}))
                time.sleep(2)
                DHCPserverThread.start()
                publish_flag=1
            time.sleep(3)
        else:
            time.sleep(1)
class edgeMqtt(Mqtt):
    def default_on_message(self,client, userdata, msg):
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        if(message["mac_address"]==mac_address):
            tunnel_id=message["tunnel"]
            sqliteConnection = sqlite3.connect(SQLITE_PATH)
            cursor = sqliteConnection.cursor()
            command="REPLACE INTO tunnel (id) VALUES (%s)"
            value=(tunnel_id)
            cursor.execute(command,value)
            cursor.close()
            sqliteConnection.close()
        
if __name__=="__main__":
    mac_address=get_mac_address("etn0")
    NatWlan()
    connect_thread = threading.Thread(target=check_connection)
    connect_thread.start()
    mqtt_thread = threading.Thread(target=check_connection_mqtt)
    mqtt_thread.start()
    DHCPserverThread=threading.Thread(target=DHCPserver)
    
