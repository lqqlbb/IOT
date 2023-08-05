# Source: setup.py. Assumes coop-project is pulled

# initial setup for edge server
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install git
sudo apt-get -y install sqlite3
sudo apt-get -y install bridge-utils
sudo apt-get -y install python3 pip

# pip installs
pip3 install paho-mqtt
# set up staticDHCPd
chmod +x ~/coop-project/hardware/dhcp/install.sh
sudo sh ~/coop-project/hardware/dhcp/install.sh
