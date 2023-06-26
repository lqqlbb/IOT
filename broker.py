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
        pdb.set_trace()
        cursor = self.cnx.cursor()
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        print(message,msg.topic)
        if msg.topic == "nodes":
            query = "SELECT * FROM nodes WHERE id = %s"
            params = (message["ID"],)  # 设置查询条件
            cursor.execute(query, params)
            if cursor.fetchone():
                # 查询结果非空，执行更新操作
                update_query = "UPDATE nodes SET ip = %s ,topic = %s , time=%s WHERE id = %s"
                update_params = (message['IP'],message['TOPIC'],message["TIME"],message["ID"])  # 设置更新的值和条件
                cursor.execute(update_query, update_params)
            else:
                # 查询结果为空，执行插入操作
                insert_query = "INSERT INTO "+msg.topic+" (id, ip,topic,time) VALUES (%s,%s, %s,%s)"
                insert_params = (message["ID"],message['IP'],message['TOPIC'],message["TIME"])  # 设置插入的值
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
node_number=2
p=brokerMqtt(["node"+str(i) for i in range(2,2+node_number)],10,"18.118.120.113",False)
p.Start()
#the thread of input
# input_thread = threading.Thread(target=input_thread)
# input_thread.start()
while True:
    if 'user_input' in globals():
        print("input 'q' to exit: ",user_input)
        if user_input.lower() == "q":
            p.disconnectTOSql()
            print("Bye")
            running=False
            del user_input
            sys.exit()  # exit the program
            
        del user_input


# #insert new rows
# sql = "INSERT INTO your_table (column1, column2, column3) VALUES (%s, %s, %s)"
# values = ("Value1", "Value2", "Value3")
# # 执行SQL查询
# query = "SELECT * FROM students"
# cursor.execute(query)

# # 获取查询结果
# result = cursor.fetchall()

# # 处理查询结果
# for row in result:
#     print(row)

# # 关闭游标和连接
# cursor.close()
# cnx.close()
