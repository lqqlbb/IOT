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
import time
class brokerMqtt(Mqtt):
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
        super().__init__(sub_topic,node_name,central_ip,last_will)
        self.cnx=self.connectToSql()
        self.total_time=[]
        print(self.topic)
    def default_on_message(self,client, userdata, msg):
        '''
            callback function when receive message
        '''
        # print(msg.payload.decode('utf-8'))
        # pdb.set_trace()
        start_time=time.time()
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
                delete_query = "DELETE FROM detection WHERE id = %s"
                delete_params = (message["ID"],)  # data to update
                cursor.execute(delete_query, delete_params)
                insert_query = "insert INTO detection (id,gas,max,min) VALUES (%s,%s,%s,%s)"
                for value in message['DETECTION']:
                    insert_params=(message["ID"],value,5,3)
                    cursor.execute(insert_query, insert_params)
            else:
                # if the result is none.
                insert_query = "INSERT INTO "+msg.topic+" (id, ip,topic,time) VALUES (%s,%s, %s,%s)"
                insert_params = (message["ID"],message['IP'],message['TOPIC'],message["TIME"])  # insert data
                cursor.execute(insert_query, insert_params)
                table_name="node"+message["ID"]
                column_definitions = ", ".join([f"{gas} int" for gas in message["DETECTION"]])
                create_table_query = f"CREATE TABLE if not exists {table_name} (submission_date varchar(40),{column_definitions})"
                print(create_table_query)
                cursor.execute(create_table_query)
        elif(msg.topic=="time"):
            if(message["TIME"]==datetime.now().strftime("%Y-%m-%d %H:%M")):
                print(message["ID"]+"time_correct")
            else:
                print(message["ID"]+"time_error")
        elif(msg.topic=="tunnel_up"):
            query = " select * from edge  where mac =%s;"
            params = (message["mac_address"],)
            cursor.execute(query, params)
            result=cursor.fetchall()
            print(result)
            if result:
                self.Publish("tunnel_down",json.dumps({"mac_address":message["mac_address"],"tunnel":result[0][1]}))
            else:
                edge_query="insert into edge (mac) values (%s)"
                edge_paras=(message["mac_address"],)
                id_query="select max(tunnel_id) from edge"
                cursor.execute(id_query)
                max_id=cursor.fetchall()
                print(max_id)
                cursor.execute(edge_query,edge_paras)
                self.Publish("tunnel_down",json.dumps({"mac_address":message["mac_address"],"tunnel":max_id}))

        else:
            query = " select * from detection  where id =%s;"
            params = (msg.topic[4:],)  # set select condition
            cursor.execute(query, params)
            rows=cursor.fetchall()
            columns="submission_date,"+",".join([f"{gas[1]}" for gas in rows])
            values="\""+message["time"]+"\""+","+",".join([f"{message[gas[1]]}" for gas in rows])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(msg.topic,columns,values)
            # print(sql)
            cursor.execute(sql)
        cursor.close()
        # time.sleep(3)
        end_time=time.time()
        self.total_time.append(end_time-start_time)
        print("running_time_is"+str(sum(self.total_time)/len(self.total_time)))
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
        self.receivers = '2033307518@qq.com'
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
        self.total_time=[]
    def default_on_message(self,client, userdata, msg):
        '''
            callback function when receive message
        '''
        start_time=time.time()
        sql_query=(" select * from alert_method  where id =%s;")
        sql_para=(msg.topic[4:],)
        self.server.connect('smtp.gmail.com', 465)
        self.server.login(self.sender, self.password)
        cursor = self.cnx.cursor()
        cursor.execute(sql_query,sql_para)
        result=cursor.fetchall()
        # print(result)
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message,msg.topic[4:])
        query = " select gas,min,max from detection where id=%s;"
        params = (msg.topic[4:],)  # set select condition
        cursor.execute(query, params)
        for thres in cursor.fetchall():
            print(thres)
            if(message[thres[0]]>thres[2]):
                sql = "INSERT INTO alert (submission_date,id,alert,value) VALUES (%s,%s,%s,%s)"
                values=(message["time"],msg.topic[4:],"high",message[thres[0]])
                cursor.execute(sql,values)
                if(result[0][2]):
                    try:
                        self.server.sendmail(self.sender, self.receivers, self.max_message.as_string())
                        print("success")
                    except:
                        print("fail")
            elif(message[thres[0]]<thres[2]):
                sql = "INSERT INTO alert (submission_date,id,alert,value) VALUES (%s,%s,%s,%s)"
                values=(message["time"],msg.topic[4:],"low",message[thres[0]])
                cursor.execute(sql,values)
                if(result[0][2]):
                    try:
                        self.server.sendmail(self.sender, self.receivers, self.min_message.as_string())
                        print("success")
                    except:
                        print("fail")
        cursor.close()
        self.server.quit()
        end_time=time.time()
        self.total_time.append(end_time-start_time)
        print("alert_running_time_is"+str(sum(self.total_time)/len(self.total_time)))
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
    print(mode[:2])
    if mode[0]=="u":
        p.Publish('update'+id,json.dumps({"instruction":"update"}))
    elif mode[0]=="r":
        p.Publish('update'+id,json.dumps({"instruction":"start"}))
    elif mode[:2]=="sh":
        p.Publish('update'+id,json.dumps({"instruction":"ssh"}))
        print("published")
    elif mode[:2]=="ss":
        p.Publish('update'+id,json.dumps({"instruction":"stopssh"}))
        # update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        # update_params = (result-1,id)  # set data to update
    elif mode[0]=="b":
        p.Publish('update'+id,json.dumps({"instruction":"backtrace","version":"v1.0"}))
    elif mode[0]=="s":
        p.Publish('down'+id,json.dumps({"instruction":"stop"}))
        # update_query = "UPDATE nodes SET time=%s WHERE id = %s"
        # update_params = (result-1,id)  # set data to update
    else:
        cursor=cn.cursor()
        query = "SELECT time FROM nodes WHERE id = %s"
        params = (id,)  # set select condition
        cursor.execute(query, params)
        result = cursor.fetchall()[0][0]
        if mode[0]=="p":
            print(result+1)
            p.Publish('down'+id,json.dumps({"instruction":"change_speed","TIME":result+1}))
            update_query = "UPDATE nodes SET time=%s WHERE id = %s"
            update_params = (result+1,id)  # set data to update
        elif mode[0]=="m":
            print(result-1)
            p.Publish('down'+id,json.dumps({"instruction":"change_speed","TIME":result-1}))
            update_query = "UPDATE nodes SET time=%s WHERE id = %s"
            update_params = (result-1,id)  # set data to update
        
        cursor.execute(update_query, update_params)
        cn.commit()
        cursor.close()
        cn.close()
def print_active_threads():
    threads = threading.enumerate()
    for thread in threads:
        print(f"Threadname: {thread.name}, ThreadID: {thread.ident}")
tunnel_number=1
node_number=2
# print(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)])
id=brokerMqtt(["nodes","tunnel_up"],12,"18.216.80.237",False)
id.Start()
p1=brokerMqtt(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)],10,"18.216.80.237",False)
p1.Start()
p2=brokerMqtt(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(4,4+node_number)],11,"18.216.80.237",False)
p2.Start()
# q=alertMqtt(["node"+"T"+str(i)+"N"+str(m) for i in range(1,1+tunnel_number) for m in range(2,2+node_number)],11,"18.216.80.237",False)
# q.Start()
# the thread of input
input_thread = threading.Thread(target=input_thread)
input_thread.start()
print_active_threads()
node2_id="T1N3"
node1_id="T1N2"
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
        elif user_input.lower() == "p2":
            change_constants("p2",node2_id)
        elif user_input.lower() == "m2":
            change_constants("m2",node2_id)
        elif user_input.lower() == "u2":
            change_constants("u2",node2_id)
        elif user_input.lower() == "b2":
            change_constants("b2",node2_id)
        elif user_input.lower() == "s2":
            change_constants("s2",node2_id)
        elif user_input.lower() == "r2":
            change_constants("r2",node2_id)
        elif user_input.lower() == "sh2":
            change_constants("sh2",node2_id)
        elif user_input.lower() == "ss2":
            change_constants("ss2",node2_id)
        elif user_input.lower() == "p":
            change_constants("p1",node1_id)
        elif user_input.lower() == "m1":
            change_constants("m1",node1_id)
        elif user_input.lower() == "u1":
            change_constants("u1",node1_id)
        elif user_input.lower() == "b1":
            change_constants("b1",node1_id)
        elif user_input.lower() == "s1":
            change_constants("s1",node1_id)
        elif user_input.lower() == "r1":
            change_constants("r1",node1_id)
        elif user_input.lower() == "sh1":
            change_constants("sh1",node1_id)
        elif user_input.lower() == "ss1":
            change_constants("ss1",node1_id)
        
            
        del user_input



