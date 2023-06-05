import os
import time
import subprocess
import sys
import paho.mqtt.client as mqtt
import threading
import random
from constants import*
class Mqtt:
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip='3.16.135.152',port=1883,anonymous=True,timeout=60):
        '''
        :param central_ip: Broker address
        :param port:  port number
        :param timeout:  toleration of connection delay
        :param node_name: name of node
        :param anonymous: if allow multi-ports
        '''
        self.topic=sub_topic
        self.broker_ip=central_ip
        self.broker_port=port
        self.timeout=timeout
        self.connected=False
        self.node_name="node"+str(node_name)
        if anonymous:
            self.node_name=self.node_name
        
    def Start(self):
        '''
        start publisher
        :return:
        '''
        self.client = mqtt.Client(self.node_name)     #set up client
        self.client.on_connect = self.on_connect  # call back function
        self.client.on_message=self.default_on_message
        self.client.connect(self.broker_ip, self.broker_port, self.timeout)     #start to connect
        self.client.subscribe(self.topic)
        self.client.loop_start()    #start a thread 
    def Publish(self,topic,payload,qos=0,retain=False):
        '''
            publish a mqtt message
            :param topic: message topic,string type
            :param payload: message,string type
            :param qos: qos of message
            :retain: 
            :return:
        '''
        if self.connected:
            return self.client.publish(topic,payload=payload,qos=qos,retain=retain)
        else:
            raise Exception("mqtt server not connected! you may use .Start() function to connect to server firstly.")

    '''
                callback function
    '''
    def on_connect(self,client, userdata, flags, rc):
        '''
            call back function of connection to broker
        '''
        if rc==0:
            self.connected=True

        else:
            raise Exception("Failed to connect mqtt server with code"+str(rc))
    def default_on_message(self,client, userdata, msg):
        '''
            default callback function
        '''
        print(msg.payload.decode('utf-8'))
  
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
    os.system("sudo ip addr flush dev eth0")
    os.system("sudo ip route add "+edgeIp+" via "+ip+" dev br0")
    print("bridge made")
def publish(topic:str,message:str):
    while True:
        try:
                p.Publish(topic,message)
                time.sleep(2)
        except:
                print("fail to publish "+message+" to "+topic)
def subscribe(topic:str):
    while True:
        p.Subscribe(topic)
def setRoute():
    while True:
            
            os.system("sudo ip route change default via "+EDGE_IP)
            time.sleep(2)
            pingResult = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True)
            routeResult = subprocess.run(['route', '-n'], capture_output=True, text=True)
            output_lines = routeResult.stdout.split('\n')
            for line in output_lines:
                if line.startswith('0.0.0.0'):
                    columns = line.split()
                    gateway = columns[1]
#                    print(gateway)
            if (gateway == EDGE_IP)&(pingResult.returncode == 0):
                print("Route set up")
                return
            else:
                print("Fail to set route, try again")
                
        
if __name__ =="__main__":
    args = sys.argv

    ip,id=getDHCPip()
    print("IP:",ip,"\n","ID:",id,"\n")
    if (args[1] != "end"):
         makeBridge(ip,EDGE_IP)
         time.sleep(2)

    setRoute()
    p=Mqtt(str(id),id)
    p.Start()
    time.sleep(5)
    pubThread=threading.Thread(target=publish,args=(str(id),"this is a test"))
    pubThread.start()

    while True:
        pass

    



    
    



    
