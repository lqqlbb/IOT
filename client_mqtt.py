from mqtt import Mqtt
import os
import time
import subprocess
import sys
import threading
import random
import pdb
import json
import pandas as pd
class clientMqtt(Mqtt):
     def default_on_message(self,client, userdata, msg):
#          pdb.set_trace()
          message=msg.payload.decode('utf-8')
          message=json.loads(message)
          time_interval=message['TIME']
          data["TIME"]=time_interval
          print(data)
          with open('constants.json', 'w') as file:
            json.dump(data,file)
def publish(client,topic:str,file:str):
    df=pd.read_csv(file)
    print(topic)
    while True:
        try:
                
                for index, row in df.iterrows():
#                    print(row.to_json())
                    client.Publish(topic,row.to_json())
                    print(time_interval)
                    time.sleep(time_interval)
        except:
                print("fail to publish "+file+" to "+topic)
if __name__ =="__main__":
    
    with open('constants.json', 'r') as file:
        data = json.load(file)
    BROKER_IP=data["BROKER_IP"]
    id=data["ID"]
    time_interval=data["TIME"]
    p=clientMqtt("down"+str(id),id,BROKER_IP,True)
    p.Start()
    time.sleep(5)
    p.Publish("nodes",json.dumps(
         {
            "ID":id,
            "IP":data["IP"],
            "TOPIC":data["TOPIC"],
            "TIME":time_interval,}))
    pubThread=threading.Thread(target=publish,args=(p,data["TOPIC"],"austin_weather.csv"))
    pubThread.start()
    while True:
        pass
