import paho.mqtt.client as mqtt
import pdb
class Mqtt:
    '''
        mqtt
    '''
    def __init__(self,sub_topic,node_name,central_ip,last_will,port=1883,anonymous=True,timeout=60):
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
        self.last_will=last_will
        
    def Start(self):
        '''
        start publisher
        :return:
        '''
        self.client = mqtt.Client(self.node_name)     #set up client
        self.client.on_connect = self.on_connect  # call back function
        self.client.on_message=self.default_on_message
        if self.last_will:
            last_will_topic = "lastwill"
            last_will_message = "Client"+self.node_name+ "disconnected"
            self.client.will_set(last_will_topic, last_will_message, qos=1)
        self.client.connect(self.broker_ip, self.broker_port, self.timeout)     #start to connect
        if isinstance(self.topic,list):
            for topic in self.topic:
                self.client.subscribe(topic)
        else:
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
            pdb.set_trace()
            print("connection set up")

        else:
            raise Exception("Failed to connect mqtt server with code"+str(rc))
    def default_on_message(self,client, userdata, msg):
        '''
            callback function when receive message
        '''
        print(msg.payload.decode('utf-8'))
    def close_connection(self):
        self.client.loop_stop()
        self.client.disconnect()
        
