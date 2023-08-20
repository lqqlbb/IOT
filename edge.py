import os
import threading
from mqtt import Mqtt
import sqlite3
import subprocess
import time
import json
import random
import sys
import signal
def DHCPserver():
        if(connection):
            EDGE_IP=data["EDGE_IP"]
            SUBNET=data["SUBNET"]
            os.system("sudo ifconfig eth0 "+EDGE_IP)
            os.system("sudo ip route add "+ SUBNET+"/16 via "+EDGE_IP)
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
    try:
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
                    print("published")
                    time.sleep(5)
                    DHCPserverThread.start()
                    publish_flag=1
                time.sleep(3)
            else:
                time.sleep(1)
    except Exception as e:
        print("Exception occurred:", str(e))
        pid = os.getpid() 
        os.kill(pid, signal.SIGTERM)
class edgeMqtt(Mqtt):
    def default_on_message(self,client, userdata, msg):
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message)
        if(message["mac_address"]==mac_address):
            tunnel_id=message["tunnel"]
            sqliteConnection = sqlite3.connect(SQLITE_PATH)
            print(SQLITE_PATH)
            time.sleep(3)
            cursor = sqliteConnection.cursor()
            delete_command = '''DELETE FROM subnets'''
            cursor.execute(delete_command)  
            delete_command = '''DELETE FROM tunnel'''
            cursor.execute(delete_command)  
            command="INSERT OR REPLACE INTO tunnel (id) VALUES (?)"
            value=(int(tunnel_id),)
            cursor.execute(command,value)
            command='''INSERT OR REPLACE INTO subnets (
                subnet,
                serial,
                lease_time,
                gateway,
                subnet_mask,
                broadcast_address,
                ntp_servers,
                domain_name_servers,
                domain_name
            ) VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )'''
            value=(
                f"20.{tunnel_id}.0.0/16",
                0,
                14400,
                f"20.{tunnel_id}.0.1",
                '255.255.0.0',
                f"20.{tunnel_id}.255.255",
                None,
                None,
                None)
            cursor.execute(command,value)
            global data
            data["SUBNET"]=f"20.{tunnel_id}.0.0"
            data["EDGE_IP"]=f"20.{tunnel_id}.0.1"
            with open('constants.json', 'w') as file:
                    json.dump(data,file)
            cursor.close()
            sqliteConnection.commit()
            sqliteConnection.close()
        
if __name__=="__main__":
    with open('constants.json', 'r') as file:
        data = json.load(file)
    CENTRAL_IP=data["BROKER_IP"]
    DHCPserverAddress=data["DHCPserverAddress"]
    SQLITE_PATH=data["SQLITE_PATH"]
    mac_address=get_mac_address("eth0")
    NatWlan()
    connect_thread = threading.Thread(target=check_connection)
    connect_thread.start()
    mqtt_thread = threading.Thread(target=check_connection_mqtt)
    mqtt_thread.start()
    DHCPserverThread=threading.Thread(target=DHCPserver)