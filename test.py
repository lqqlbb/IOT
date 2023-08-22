import unittest
import broker
import json
import time
import mysql.connector
import pdb
import subprocess
import pexpect
import sys
import re
class testMqtt(broker.brokerMqtt):
    def default_on_message(self,client, userdata, msg):
        message=msg.payload.decode('utf-8')
        message=json.loads(message)
        global received_message
        received_message=0
        received_message=message

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.id = "T1N3"
        # pdb.set_trace()
        cls.q=testMqtt(["nodes","tunnel_up","feedback"],"test","18.221.129.24",False)
        cls.q.Start()
        time.sleep(2)
    def test_getconfig(self):
        # pdb.set_trace()
        broker.getConfig(self.q,self.id)
        time.sleep(2)
        config=received_message
        print(config)
        if config!=0:
            cnx = mysql.connector.connect(
            host="localhost",
            user="node",
            password="aaa",
            database="test",
            autocommit = True)
            cursor = cnx.cursor()
            query = " select * from nodes  where id =%s;"
            params = (config["ID"],)  # set select condition
            cursor.execute(query, params)
            result=cursor.fetchall()
            self.assertEqual(result, [(config["ID"],config["IP"],config["TOPIC"],config["TIME"])])
            cursor.close()
            cnx.close()
            time.sleep(2)
        else:
            print("Didn't receive config")


    def test_reverse_ssh(self):
        self.q.Publish('update'+self.id,json.dumps({"instruction":"ssh","password":"aaa"}))
        command="sudo ssh -p 2208 pi@localhost;ifconfig"
        # result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        remote_host = "pi"
        remote_port = 2208
        password = "aaa"
        ssh_command = f'sudo ssh -p {remote_port} {remote_host}@localhost'
        sshprocess = pexpect.spawn(ssh_command)
        fout = open('mylog.txt',mode='wb')
        sshprocess.logfile = fout
        sshprocess.expect(f'{remote_host}@localhost'+'\'s password:',timeout=10)
        sshprocess.sendline(password)
        sshprocess.expect("\$")    # 匹配命令提示符
        sshprocess.sendline("ifconfig")
        sshprocess.expect("\$")  
        output_after_sendline = sshprocess.before.decode('utf-8')
        # match = re.search(r'eth0:.*inet (\d+\.\d+\.\d+\.\d+)', output_after_sendline)
        pattern = r'eth0:.*?inet (\d+\.\d+\.\d+\.\d+)'
        match = re.search(pattern, output_after_sendline, re.DOTALL)
        if match:
            inet_value = match.group(1)
            print("Inet value:", inet_value)
            cnx = mysql.connector.connect(
            host="localhost",
            user="node",
            password="aaa",
            database="test",
            autocommit = True)
            cursor = cnx.cursor()
            query = " select ip from nodes  where id =%s;"
            params = (self.id,)  # set select condition
            cursor.execute(query, params)
            result=cursor.fetchall()
            self.q.Publish('update'+self.id,json.dumps({"instruction":"stopssh"}))
            command = "ss -lnt | grep ':2208\b'"
            port_usage = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.assertEqual(inet_value, result[0][0])
            self.assertEqual("", port_usage.stdout)
        else:
            print("No match found")

    def test_reverse_close(self):
        pass
        # print(output_after_sendline)
if __name__ == '__main__':
    unittest.main()