import os
import time
import subprocess
import sys
from constants import*

def isInSubnet(ip:str,subnet:str) -> bool:
    if(ip[0:6]==subnet[:6]):
        return(1)
    else:
        return(0)
def get_ip(interface:str) -> str:
    ip=str(subprocess.check_output(["ifconfig", interface], text=True))
    try:
        start = ip.index("inet") + len("inet")
        end = ip.index("netmask")
        result = ip[start:end].strip()
        return(result)
    except:
        print("Can't find ip of"+interface)
    finally:
        return(0)
def getDHCPip() -> str:
    while True:
    
        os.system("sudo ip addr flush eth0")
        os.system("sudo ifconfig eth0 0.0.0.0")
        os.system("sudo dhclient eth0 -p 1112 -v")
        time.sleep(3)
        if (isInSubnet(get_ip('eth0'),SUBNET)):
            break
    last_period_index = get_ip('eth0').rfind(".")
    result = ip[last_period_index + 1:].strip()
    return(get_ip('eth0'),result)
def makeBridge(ip:str,edgeIp:SyntaxError):
    os.system("sudo brctl addbr br0")
    os.system("sudo ifconfig eth1 0.0.0.0")
    os.system("sudo brctl addif br0 eth0")
    os.system("sudo brctl addif br0 eth1")
    os.system("sudo ifconfig br0 up")
    os.system("sudo ifconfig br0 "+ip)
    os.system("sudo ip addr flush dev eth0")
    os.system("sudo ip route add "+edgeIp+" via "+ip+" dev br0")
    print("bridge made")


if __name__ =="__main__":
    args = sys.argv
    ip,id=getDHCPip()
    print("IP:",ip,"\n","ID:",id,"\n")
    if (len(args) != "end"):
        makeBridge(ip,EDGE_IP)
    os.system("sudo ip add default via "+EDGE_IP)
    
    



    