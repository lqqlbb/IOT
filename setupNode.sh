# Reference: startup.py. Assumes coop-project is pulled

# initial setup for node. Requires internet connection
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install git
sudo apt-get -y install python3-pip
sudo apt-get -y install bridge-utils
sudo apt-get -y install iptables

sudo pip3 install pexpect
pip3 install paho-mqtt