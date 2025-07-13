#!/bin/sh

echo "eFinder cli install"
echo " "
echo "*****************************************************************************"
echo "Updating Pi OS & packages"
echo "*****************************************************************************"
sudo apt update
sudo apt upgrade -y
echo " "
echo "*****************************************************************************"
echo "Installing additional Debian and Python packages"
echo "*****************************************************************************"
sudo apt install -m -y python3-pip
sudo apt install -y python3-serial
sudo apt install -y python3-psutil
sudo apt install -y python3-pil
sudo apt install -y python3-pil.imagetk
sudo apt install -y git
sudo apt install -y python3-smbus
sudo apt install -y python3-picamera2
sudo apt install -y python3-scipy

HOME=/home/efinder
cd $HOME
echo " "

python -m venv /home/efinder/venv-efinder --system-site-packages
venv-efinder/bin/python venv-efinder/bin/pip install adafruit-circuitpython-adxl34x
venv-efinder/bin/python venv-efinder/bin/pip install gdown

cd $HOME
echo " "
echo "*****************************************************************************"
echo "Downloading eFinder_cli from AstroKeith GitHub"
echo "*****************************************************************************"
sudo -u efinder git clone https://github.com/AstroKeith/eFinder_cli.git
echo " "

cd $HOME

echo "tmpfs /var/tmp tmpfs nodev,nosuid,size=10M 0 0" | sudo tee -a /etc/fstab > /dev/null
echo " "
echo "*****************************************************************************"
echo "Installing required packages"
echo "*****************************************************************************"
mkdir /home/efinder/Solver
mkdir /home/efinder/Solver/images
mkdir /home/efinder/Solver/data

cp /home/efinder/eFinder_cli/Solver/*.* /home/efinder/Solver
cp /home/efinder/eFinder_cli/Solver/starnames.csv /home/efinder/Solver/data

cd $HOME
echo " "
echo "*****************************************************************************"
echo "Installing Samba file share support"

sudo apt install -y samba samba-common-bin
sudo tee -a /etc/samba/smb.conf > /dev/null <<EOT
[efindershare]
path = /home/efinder
writeable=Yes
create mask=0777
directory mask=0777
public=no
EOT
username="efinder"
pass="efinder"
(echo $pass; sleep 1; echo $pass) | sudo smbpasswd -a -s $username
sudo systemctl restart smbd

cd $HOME
echo " "
echo "*****************************************************************************"
echo "installing Tetra and its databases"
echo "*****************************************************************************"
sudo -u efinder git clone https://github.com/esa/tetra3.git
cd tetra3
/home/efinder/venv-efinder/bin/pip install .
cd $HOME
sudo venv-efinder/bin/gdown  --output /home/efinder/venv-efinder/lib/python3.11/site-packages/tetra3/data --folder https://drive.google.com/drive/folders/1uxbdttpg0Dpp8OuYUDY9arYoeglfZzcX

echo " "
echo "*****************************************************************************"
echo "Setting up web page server"
echo "*****************************************************************************"
sudo apt-get install -y apache2
sudo apt-get install -y php8.2
sudo chmod a+rwx /home/efinder
sudo chmod a+rwx /home/efinder/Solver/images
sudo cp eFinder_cli/Solver/index.php /var/www/html
sudo mv /var/www/html/index.html /var/www/html/apacheindex.html
sudo chmod -R 755 /var/www/html


cd $HOME
echo " "
echo "*****************************************************************************"
echo "Final eFinder_cli configuration setting"
echo "*****************************************************************************"
sudo chmod a+rwx eFinder_cli/Solver/my_cron
sudo cp /home/efinder/eFinder_cli/Solver/my_cron /etc/cron.d

echo 'vm.swappiness = 0' | sudo tee -a /etc/sysctl.conf > /dev/null
sudo raspi-config nonint do_boot_behaviour B2
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0

sudo reboot now

