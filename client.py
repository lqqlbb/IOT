import os
import time
import subprocess
import sys
import paho.mqtt.client as mqtt
import threading
import random
from constants import*
class Mqtt_Subscriber:
    '''
        mqtt消息通讯接口
    '''
    def __init__(self,topic_name,node_name,central_ip='3.144.252.214',port=1883,
                 callback_func=None,anonymous=True,timeout=60):
        '''
            :param central_ip: Broker address
            :param port:  port number
            :param topic_name: subscript topic 
            :param callback_func: call back function
            :param timeout:  connection delay
            :param node_name: node name
            :param anonymous: if allow multi-nodes
        '''
        self.topic=topic_name
        self.callback=callback_func
        self.broker_ip=central_ip
        self.broker_port=port
        self.timeout=timeout
        self.connected=False
        self.node_name="node"+str(node_name)
        if anonymous:
            self.node_name=self.node_name
        self.Start()
    def Start(self):
        '''
        publisher
        :return:
        '''
        self.client = mqtt.Client(self.node_name)     #set up client
        self.client.on_connect = self.on_connect  # callback function
        self.client.on_message=self.default_on_message
        self.client.connect(self.broker_ip, self.broker_port, self.timeout)     #start to connect
        self.client.subscribe(self.topic)
        self.client.loop_start()    #start a thread 

    '''
                callback function
    '''
    def default_on_message(self,client, userdata, msg):
        '''
            default callback function
        '''
        print(msg.payload.decode('utf-8'))

    def on_connect(self,client, userdata, flags, rc):
        '''
            connetion broker callback
        '''
        if rc==0:
            self.connected=True

        else:
            raise Exception("Failed to connect mqtt server with code"+str(rc))
class Mqtt_Publisher:
    '''
        mqtt
    '''
    def __init__(self,node_name,central_ip='3.144.252.214',port=1883,anonymous=True,timeout=60):
        '''
        :param central_ip: Broker address
        :param port:  port number
        :param timeout:  toleration of connection delay
        :param node_name: name of node
        :param anonymous: if allow multi-ports
        '''
        self.broker_ip=central_ip
        self.broker_port=port
        self.timeout=timeout
        self.connected=False
        self.node_name="node"+str(node_name)
        if anonymous:
            self.node_name=self.node_name
        self.Start()
    def Start(self):
        '''
        start publisher
        :return:
        '''
        self.client = mqtt.Client(self.node_name)     #set up client
        self.client.on_connect = self.on_connect  # call back function
        self.client.connect(self.broker_ip, self.broker_port, self.timeout)     #start to connect
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


if __name__ =="__main__":
     args = sys.argv
     ip,id=getDHCPip()
     print("IP:",ip,"\n","ID:",id,"\n")
     if (len(args) != "end"):
         makeBridge(ip,EDGE_IP)
     os.system("sudo ip add default via "+EDGE_IP)
    p=Mqtt_Publisher(id)
    while not p.connected:
        pass
    p.Publish(str(id),'this is test')
    s=Mqtt_Subscriber(str(id),id)
    while not s.connected:
        pass
    while True:
        time.sleep(1)


    
    



    
