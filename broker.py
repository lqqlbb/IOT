import mysql.connector
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
import json
import threading
from mqtt import Mqtt
import pdb
import os
import signal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
class brokerMqtt(Mqtt):
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
        super().__init__(sub_topic,node_name,central_ip,last_will)
        self.cnx=self.connectToSql()
        self.topic.append("nodes")
        print(self.topic)
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
            query = " select * from nodes  where id =%s;"
            params = (message["ID"],)  # set select condition
            cursor.execute(query, params)
            if cursor.fetchall():
                # if the result is not none
                update_query = "UPDATE nodes SET ip = %s ,topic = %s , time=%s WHERE id = %s"
                update_params = (message['IP'],message['TOPIC'],message["TIME"],message["ID"])  # data to update
                cursor.execute(update_query, update_params)
                # delete_query = "DELETE FROM detection WHERE id = %s"
                # delete_params = (message["ID"],)  # data to update
                # cursor.execute(delete_query, delete_params)
                # insert_query = "INSERT INTO detection (id,gas) VALUES (%s,%s)"
                # for value in message['DETECTION']:
                #     insert_params=(message["ID"],value)
                #     cursor.execute(insert_query, insert_params)
            else:
                # if the result is none.
                insert_query = "INSERT INTO "+msg.topic+" (id, ip,topic,time) VALUES (%s,%s, %s,%s)"
                insert_params = (message["ID"],message['IP'],message['TOPIC'],message["TIME"])  # insert data
                cursor.execute(insert_query, insert_params)
                table_name="node"+message["ID"]
                column_definitions = ", ".join([f"{gas} int" for gas in message["DETECTION"]])
                create_table_query = f"CREATE TABLE if not exists {table_name} (submission_date varchar(40),{column_definitions},primary key(submission_date))"
                print(create_table_query)
                cursor.execute(create_table_query)
                

        else:
            query = " select * from detection  where id =%s;"
            params = (msg.topic[4:],)  # set select condition
            cursor.execute(query, params)
            rows=cursor.fetchall()
            columns="submission_date,"+",".join([f"{gas[1]}" for gas in rows])
            values="\""+message["time"]+"\""+","+",".join([f"{message[gas[1]]}" for gas in rows])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(msg.topic,columns,values)
            cursor.execute(sql)
        cursor.close()
    def connectToSql(self):
        cnx = mysql.connector.connect(
        host="localhost",
        user="node",
        password="aaa",
        database="test",
        autocommit = True)
        return cnx
    def disconnectTOSql(self):
        self.client.loop_stop()
        self.cnx.close()
        print("sql closed")
class alertMqtt(Mqtt):
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
        super().__init__(sub_topic,node_name,central_ip,last_will)
        self.cnx=self.connectToSql()
        print(self.topic)
        self.sender = 'lqqlkr@gmail.com'
        self.receivers = '3474595102@qq.com'
        self.password = 'ubouqjufdvgxmtml'
        self.max_message = MIMEMultipart()
        self.max_message['From'] = self.sender
        self.max_message['To'] = self.receivers
        self.max_message['Subject'] = '邮件主题'
        self.body = '大了'
        self.max_message.attach(MIMEText(self.body, 'plain'))
        self.min_message = MIMEMultipart()
        self.min_message['From'] = self.sender
        self.min_message['To'] = self.receivers
        self.min_message['Subject'] = '邮件主题'
        self.body = '小了'
        self.min_message.attach(MIMEText(self.body, 'plain'))
        self.server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    def default_on_message(self,client, userdata, msg):
        '''
            callback function when receive message
        '''
        self.server.connect('smtp.gmail.com', 465)
        self.server.login(self.sender, self.password)
        cursor = self.cnx.cursor()
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message,msg.topic[4:])
        query = " select gas,min,max from detection where id=%s;"
        params = (msg.topic[4:],)  # set select condition
        cursor.execute(query, params)
        for thres in cursor.fetchall():
            print(thres)
            if(message[thres[0]]>thres[2]):
                sql = "INSERT INTO alert (submission_date,id,alert) VALUES (%s,%s,%s)"
                values=(message["time"],msg.topic[4:],"high")
                cursor.execute(sql,values)
                try:
                    self.server.sendmail(self.sender, self.receivers, self.max_message.as_string())
                    print("success")
                except:
                    print("fail")
            elif(message[thres[0]]<thres[2]):
                sql = "INSERT INTO alert (submission_date,id,alert) VALUES (%s,%s,%s)"
                values=(message["time"],msg.topic[4:],"low")
                cursor.execute(sql,values)
                try:
                    self.server.sendmail(self.sender, self.receivers, self.min_message.as_string())
                    print("success")
                except:
                    print("fail")
        cursor.close()
        self.server.quit()
    def connectToSql(self):
        cnx = mysql.connector.connect(
        host="localhost",
        user="node",
        password="aaa",
        database="test",
        autocommit = True)
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
def change_constants(mode:str,id:str):
    cn = mysql.connector.connect(
        host="localhost",
        user="node",
        password="aaa",
        database="test")
    if mode=="u":
        p.Publish('update'+id,json.dumps({"instruction":"update"}))
        # update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        # update_params = (result-1,id)  # set data to update
    elif mode=="b":
        p.Publish('update'+id,json.dumps({"instruction":"backtrace","version":"v1.0"}))
    elif mode=="s":
        p.Publish('down'+id,json.dumps({"instruction":"stop"}))
        # update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        # update_params = (result-1,id)  # set data to update
    else:
        cursor=cn.cursor()
        query = "SELECT time FROM nodes WHERE id = %s"
        params = (id,)  # set select condition
        cursor.execute(query, params)
        result = cursor.fetchall()[0][0]
        print(result)
        if mode=="p":
            p.Publish('down'+id,json.dumps({"instruction":"change_speed","TIME":result+1}))
            update_query = "UPDATE nodes SET time=%s WHERE id = %s"
            update_params = (result+1,id)  # set data to update
        elif mode=="m":
            p.Publish('down'+id,json.dumps({"instruction":"change_speed","TIME":result-1}))
            update_query = "UPDATE nodes SET time=%s WHERE id = %s"
            update_params = (result-1,id)  # set data to update
        
        cursor.execute(update_query, update_params)
        # cn.commit()
        cursor.close()
        cn.close()
def print_active_threads():
    threads = threading.enumerate()
    for thread in threads:
        print(f"Threadname: {thread.name}, ThreadID: {thread.ident}")
tunnel_number=1
node_number=2
# print(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)])
p=brokerMqtt(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)],10,"3.140.201.235",False)
p.Start()
q=alertMqtt(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)],11,"3.140.201.235",False)
q.Start()
# the thread of input
input_thread = threading.Thread(target=input_thread)
input_thread.start()
print_active_threads()

while True:
    
    if 'user_input' in globals():
        print("input 'q' to exit,'p' to plus 1s to time interval,'m' to minors 1s: ",user_input)
        if user_input.lower() == "q":
            p.disconnectTOSql()
            q.disconnectTOSql()
            print("Bye")
            running=False
            del user_input
            os.kill(os.getpid(), signal.SIGSTOP)  # exit the program
        elif user_input.lower() == "p":
            change_constants("p",3)
        elif user_input.lower() == "m":
            change_constants("m",3)
        elif user_input.lower() == "u":
            change_constants("u",3)
        elif user_input.lower() == "b":
            change_constants("b",3)
        elif user_input.lower() == "s":
            change_constants("s",3)
        
            
        del user_input



