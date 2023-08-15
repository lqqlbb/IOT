import os
import time
import subprocess
import sys
import threading
import random
import pdb
import json
import signal
from mqtt import Mqtt
import pexpect
from datetime import datetime
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
        
class updateMqtt(Mqtt):
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
        super().__init__(sub_topic,node_name,central_ip,last_will)
        self.sshprocess = None
    def default_on_message(self,client, userdata, msg):
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message)
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
            result = subprocess.Popen(command, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elif message["instruction"]=="ssh":
            self.startssh()
        elif message["instruction"]=="stopssh":
            self.endssh()
    def startssh(self):
        remote_host = 'ubuntu@3.140.201.235'
        remote_port = 2208
        local_port = 22
        ssh_command = f'ssh -fN -R {remote_port}:localhost:{local_port} {remote_host}'
        self.sshprocess = pexpect.spawn(ssh_command)
        self.sshprocess.expect('ubuntu@3.140.201.235\'s password:')
        self.sshprocess.sendline('aaa')
        
    def endssh(self):
        try:
            command = "ps -ef | grep 'ssh -fN -R'"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout.strip().splitlines()
            for i in output[0:-2]:
                words = i.split()
                os.kill(int(words[1]), signal.SIGTERM)
            print("success terminal ssh")
        except:
            print("fail to shup down ssh")


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
            connection=False
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
                data["IP"]=ip
                tunnel_id = ip.split(".")[1]
                data["ID"]=f"T{tunnel_id}N{id}"
                data["TOPIC"]=f"nodeT{tunnel_id}N{id}"
                with open('constants.json', 'w') as file:
                    json.dump(data,file)
            except subprocess.CalledProcessError:
                print("Can't get ip and id from edge")
                time.sleep(1)
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
    try:
        flag=0
        while True:
            # pdb.set_trace()
            if(connection):
                if flag==0:
                        # pdb.set_trace()
                        id=data["ID"]
                        ip=data["IP"]
                        mqtt_instance=updateMqtt("update"+str(id),str(id)+"_update",CENTRAL_IP,True)
                        # mqtt_instance.Start()
                        flag=1
                # 
                # print(mqtt_instance.connected)
                if not mqtt_instance.connected:
                #     # pdb.set_trace()
                    # print(mqtt_instance.connected)
                    mqtt_instance.Start()
                    mqtt_instance.Publish("time",json.dumps(
            {
                "ID":id,
                "TIME":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),}))
                time.sleep(3)
            else:
                time.sleep(1)
    except Exception as e:
        print("Exception occurred:", str(e))
        pid = os.getpid() 
        os.kill(pid, signal.SIGTERM)
if __name__ =="__main__":
    with open('constants.json', 'r') as file:
        data = json.load(file)
    EDGE_IP=data["EDGE_IP"]
    SUBNET=data["SUBNET"]
    CENTRAL_IP=data["BROKER_IP"]
    print("upgraded")
    connect_thread = threading.Thread(target=check_connection)
    connect_thread.start()
    mqtt_thread = threading.Thread(target=check_connection_mqtt)
    mqtt_thread.start()

