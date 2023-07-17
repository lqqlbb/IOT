import os
import time
import subprocess
import sys
import threading
import random
import pdb
import json
from mqtt import Mqtt
def isInSubnet(ip:str,subnet:str) -> bool:
    # print(ip)
    if(ip[0:6]==subnet[0:6]):
        return(1)
    else:
        return(0)
def get_ip(interface:str) -> str:
    ip=str(subprocess.check_output(["ifconfig", interface], text=True))
    try:
        start = ip.index("inet") + len("inet")
        end = ip.index("netmask")
        result = ip[start:end].strip()
        # print(type(result),result)
        return(result)
    except:
        print("Can't find ip of"+interface)
    
def getDHCPip() -> str:
    while True:
    
        os.system("sudo ip addr flush eth0")
        os.system("sudo ifconfig eth0 0.0.0.0")
        os.system("sudo dhclient eth0 -p 1112 -v")
        time.sleep(3)
        if (isInSubnet(get_ip('eth0'),SUBNET)):
            break
    last_period_index = get_ip('eth0').rfind(".")
    result = get_ip('eth0')[last_period_index + 1:].strip()
    return(get_ip('eth0'),result)
def makeBridge(ip:str,edgeIp:SyntaxError):
    os.system("sudo brctl addbr br0")
    os.system("sudo ifconfig eth1 0.0.0.0")
    os.system("sudo brctl addif br0 eth0")
    os.system("sudo brctl addif br0 eth1")
    os.system("sudo ifconfig br0 up")
    os.system("sudo ifconfig br0 "+ip)
    os.system("sudo ip route add "+edgeIp+" via "+ip+" dev br0")
    print("bridge made")
def setRoute(end:bool):
    for i in range(10):
            # pdb.set_trace()
            os.system("sudo ip route del default via 0.0.0.0")
            if end:
                os.system("sudo ip route add default via "+EDGE_IP)
            else:
                os.system("sudo ip route add default via "+EDGE_IP+" dev br0")
            time.sleep(2)
            pingResult = subprocess.run(['ping', '-c', '4', '8.8.8.8'], capture_output=True)
            routeResult = subprocess.run(['route', '-n'], capture_output=True, text=True)
#            print(routeResult)
            output_lines = routeResult.stdout.split('\n')
            
            line=output_lines[2]
            if line.startswith('0.0.0.0'):
                columns = line.split()
                gateway = columns[1]
#                    print(gateway)
                if (gateway == EDGE_IP)&(pingResult.returncode == 0):
                    print("Route set up")
            
                    return
                else:
                    print("Fail to set route, try again")
def rewrite_file(filename, new_content):
    with open(filename, 'w') as file:
        file.write(new_content)
        
class updateMqtt(Mqtt):
    def default_on_message(self,client, userdata, msg):
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        if message["instruction"]=="update":
            command = '''git fetch origin client
                         git reset --hard origin/client'''
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("Update successfully!")
            else:
                print("An error occurred while updating.")
                print("Error message:")
                print(result.stderr)
                self.Publish("update"+data["ID"],json.dumps(
         {
            "update_error":result.stderr,
            }))
        elif message["instruction"]=="backtrace":
            command = "git reset --hard "+message["version"]
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("Reset successfully!")
            else:
                print("An error occurred while reseting.")
                print("Error message:")
                print(result.stderr)
                self.Publish("update"+data["ID"],json.dumps(
         {
            "reset_error":result.stderr,
            }))
        elif message["instruction"]=="start":
            command = "python client_mqtt.py"
            result = subprocess.Popen(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("Running successfully!")
            else:
                print("An error occurred while running.")
                print("Error message:")
                print(result.stderr)
                self.Publish("update"+data["ID"],json.dumps(
         {
            "running_error":result.stderr,
            }))
        elif message["instruction"]=="stop":
            pass
def check_connection():
    global connection
    connection=False
    p_end=1
    while True:
        result = subprocess.run(['ifconfig', 'eth1'])
        if result.returncode == 0:
            end=0
        else:
            end=1
        pingResult = subprocess.run(['ping', '-c', '4', '8.8.8.8'], capture_output=True)
        # print(p_end,end,(p_end^end))
        if(pingResult.returncode!=0 or ((p_end^end)==1)):
            try:
                if (p_end==0 and end==1):
                    os.system("sudo ifconfig br0 down")
                    os.system("sudo brctl delbr br0")
                    os.system("sudo ip route flush dev br0")
                output = subprocess.check_output(["sudo", "ethtool", "eth0"]).decode('utf-8')
                if "Link detected: yes" in output:
                        print("Link detected on eth0")
                elif "Link detected: no" in output:
                        print("No link detected on eth0")
                        continue
                else:
                        print("Could not determine link status of eth0")
                ip,id=start_connection(end)
                global data
                data["ID"]=id
                data["IP"]=ip
                data["TOPIC"]="node"+id
                with open('constants.json', 'w') as file:
                    json.dump(data,file)
            except subprocess.CalledProcessError:
                print("Can't get ip and id from edge")
                time.sleep(2)
        else:
            
            connection=True
            time.sleep(5)
        p_end=end
def start_connection(end:bool):
    ip,id=getDHCPip()
    print("IP:",ip,"\n","ID:",id,"\n")
    if not end:
         makeBridge(ip,EDGE_IP)
         time.sleep(2)
    setRoute(end) 
    return ip,id
def check_connection_mqtt():
    flag=0
    while True:
        if(connection):
            if flag==0:
                    id=data["ID"]
                    ip=data["IP"]
                    mqtt_instance=updateMqtt("update"+str(id),str(id)+"_update",CENTRAL_IP,True)
                    flag=1
            if not mqtt_instance.connected:
                mqtt_instance.Start()
        else:
            time.sleep(3)
if __name__ =="__main__":
    with open('constants.json', 'r') as file:
        data = json.load(file)
    EDGE_IP=data["EDGE_IP"]
    SUBNET=data["SUBNET"]
    CENTRAL_IP=data["BROKER_IP"]
    connect_thread = threading.Thread(target=check_connection)
    connect_thread.start()
    connect_thread = threading.Thread(target=check_connection_mqtt)
    connect_thread.start()
    # if(connection):
    #     data["ID"]=id
    #     data["IP"]=ip
    #     data["TOPIC"]="node"+id
    #     q=updateMqtt("update"+id,id+"_update",CENTRAL_IP,True)
    #     q.Start()
    #     while True:
    #         time.sleep(2)

