import os
import threading
from constants import*
def DHCPserver():
    os.system("sudo ifconfig eth0 "+EDGE_IP)
    os.system("sudo ip route add "+ SUBNET+"/24 via "+EDGE_IP)
    
    while True:
        os.system(f"sudo python {DHCPserverAddress}")
def NatWlan():
    os.system("sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE")

if __name__=="__main__":

    DHCPserverThread=threading.Thread(target=DHCPserver)
    DHCPserverThread.start()
    NatWlan()
