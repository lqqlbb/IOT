import mysql.connector
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
import json
import threading
from mqtt import Mqtt
import pdb
class brokerMqtt(Mqtt):
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
        super().__init__(sub_topic,node_name,central_ip,last_will)
        self.cnx=self.connectToSql()
        self.topic.append("nodes")
    def default_on_message(self,client, userdata, msg):
        '''
            callback function when receive message
        '''
        # print(msg.payload.decode('utf-8'))
        # pdb.set_trace()
        cursor = self.cnx.cursor()
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message,msg.topic)
        if msg.topic == "nodes":
            query = "SELECT * FROM nodes WHERE id = %s"
            params = (message["ID"],)  # set select condition
            cursor.execute(query, params)
            if cursor.fetchone():
                # if the result is not none
                update_query = "UPDATE nodes SET ip = %s ,topic = %s , time=%s WHERE id = %s"
                update_params = (message['IP'],message['TOPIC'],message["TIME"],message["ID"])  # data to update
                cursor.execute(update_query, update_params)
            else:
                # if the result is none.
                insert_query = "INSERT INTO "+msg.topic+" (id, ip,topic,time) VALUES (%s,%s, %s,%s)"
                insert_params = (message["ID"],message['IP'],message['TOPIC'],message["TIME"])  # insert data
                cursor.execute(insert_query, insert_params)
        else:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "INSERT INTO "+msg.topic+" (submission_date, temperature,weather) VALUES (%s,%s, %s)"
            values = (current_datetime,message['TempHighF'],message['Events'])
            print(values)
            cursor.execute(sql,values)
        self.cnx.commit()
        cursor.close()
    def connectToSql(self):
        cnx = mysql.connector.connect(
        host="localhost",
        user="node1",
        password="aaa",
        database="test")
        return cnx
    def disconnectTOSql(self):
        self.client.loop_stop()
        self.cnx.close()
        print("sql closed")
def input_thread():
    global running
    running=True
    while running:
        global user_input
        user_input = input()
def change_constants(mode:str,id:int):
    cn = mysql.connector.connect(
        host="localhost",
        user="node1",
        password="aaa",
        database="test")
    cursor=cn.cursor()
    query = "SELECT time FROM nodes WHERE id = %s"
    params = (id,)  # set select condition
    cursor.execute(query, params)
    result = cursor.fetchall()[0][0]
    print(result)
    if mode=="p":
        p.Publish('down'+str(id),json.dumps({"TIME":result+1}))
        update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        update_params = (result+1,id)  # set data to update
    elif mode=="m":
        p.Publish('down'+str(id),json.dumps({"TIME":result-1}))
        update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        update_params = (result-1,id)  # set data to update
    cursor.execute(update_query, update_params)
    cn.commit()
    cursor.close()
    cn.close()
node_number=2
p=brokerMqtt(["node"+str(i) for i in range(2,2+node_number)],10,"18.118.120.113",False)
p.Start()
# the thread of input
input_thread = threading.Thread(target=input_thread)
input_thread.start()
while True:
    if 'user_input' in globals():
        print("input 'q' to exit,'p' to plus 1s to time interval,'m' to minors 1s: ",user_input)
        if user_input.lower() == "q":
            p.disconnectTOSql()
            print("Bye")
            running=False
            del user_input
            sys.exit()  # exit the program
        elif user_input.lower() == "p":
            change_constants("p",2)
        elif user_input.lower() == "m":
            change_constants("m",2)
            
        del user_input



