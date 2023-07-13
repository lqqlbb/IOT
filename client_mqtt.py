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
                err_queue.put(e)
                print("fail to publish "+file+" to "+topic)
                return
if __name__ =="__main__":
    
    with open('constants.json', 'r') as file:
        data = json.load(file)
    BROKER_IP=data["BROKER_IP"]
    id=data["ID"]
    time_interval=data["TIME"]
    p=clientMqtt(["down"+str(id)],id,BROKER_IP,True)
    p.Start()
    time.sleep(5)
    p.Publish("nodes",json.dumps(
         {
            "ID":id,
            "IP":data["IP"],
            "TOPIC":data["TOPIC"],
            "TIME":time_interval,
            "DETECTION":data["DETECTION"]}))
    err_queue = queue.Queue()
    pubThread=threading.Thread(target=publish,args=(p,data["TOPIC"],"austin_weather.csv"))
    pubThread.start()
    while True:
        while not err_queue.empty(): 
            error = err_queue.get()
            print('Error:', error)
        time.sleep(2)
