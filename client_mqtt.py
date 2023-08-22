from mqtt import Mqtt
from datetime import datetime
import os
import time
import subprocess
import sys
import threading
import random
import pdb
import json
import pandas as pd
import signal
import queue

class clientMqtt(Mqtt):
     def default_on_message(self,client, userdata, msg):
#          pdb.set_trace()
          message=msg.payload.decode('utf-8')
          message=json.loads(message)
          if message["instruction"]=="change_speed":   
               global time_interval
               time_interval=message['TIME']
               data["TIME"]=time_interval
               print(data)
               with open('constants.json', 'w') as file:
                 json.dump(data,file)
          elif message["instruction"]=="stop":
               self.close_connection()
               pid = os.getpid() 
               os.kill(pid, signal.SIGTERM)
          elif message["instruction"]=="pause":
               pass
def publish(client,topic:str,file:str):
    df=pd.read_csv(file)
    print(topic)
    while True:
        try:
                
                for index, row in df.iterrows():
                    row=json.loads(row.to_json())
                    row["time"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(row)
                    client.Publish(topic,json.dumps(row))
                    print(time_interval)
                    time.sleep(time_interval)
        except Exception as e:
               client.close_connection()
               pid = os.getpid() 
               os.kill(pid, signal.SIGTERM)
def check_connection_mqtt():
    try:
        instance_flag=0
        send_flag=0
        while True:
            # pdb.set_trace()
                if instance_flag==0:
                        # pdb.set_trace()
                        id=data["ID"]
                        ip=data["IP"]
                        mqtt_instance=clientMqtt(["down"+str(id)],id,BROKER_IP,True)
                        instance_flag=1
                # 
                # print(mqtt_instance.connected)
                if not mqtt_instance.connected:
                #     # pdb.set_trace()
                    mqtt_instance.Start()
                else:
                     if send_flag==0:
                        pubThread=threading.Thread(target=publish,args=(mqtt_instance,data["TOPIC"],"austin_weather.csv"))
                        pubThread.start()
                        send_flag=1
                time.sleep(3)
    except Exception as e:
        print("Exception occurred:", str(e))
        pid = os.getpid() 
        os.kill(pid, signal.SIGTERM)
if __name__ =="__main__":
    
    with open('constants.json', 'r') as file:
        data = json.load(file)
    print(data)
    BROKER_IP=data["BROKER_IP"]
    id=data["ID"]
    time_interval=data["TIME"]
    mqtt_thread = threading.Thread(target=check_connection_mqtt)
    mqtt_thread.start()
    # p.Publish("nodes",json.dumps(
    #      {"Status":data["DETECTION"]}))
    

