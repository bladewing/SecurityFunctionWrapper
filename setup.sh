#!/bin/bash

if [ $(whoami) = "root" ]
then
    echo "Do not install with root access."
    exit
fi
if [ "$1" != "-y" ] && [ "$2" != "-y" ]; then
    echo -n "Did you configure the wrapper.ini File? [y/n]"
    read answer
    if echo "$answer" | grep -iq "^y" ;then
        echo "Good, continuing..."
    else
        echo "Start setup.sh after configuring wrapper.ini!"
        exit
    fi
fi

mkdir /home/$(whoami)/bin
DIR=/home/$(whoami)/bin

echo "Installing Security Appliance Wrapper!"
echo "Copy to user binary directory..."
mkdir $DIR/SecAppWrapper
cp -R SecAppWrapper $DIR/SecAppWrapper/
cp start_wrapper.py $DIR/SecAppWrapper/
cp wrapper.ini $DIR/SecAppWrapper/
echo "Copy done!"

touch /var/log/SecAppWrapper.log

if [ "$1" != "--nosystemd" ] && [ "$2" != "--nosystemd" ]; then
    echo "Installing service..."
    cp SAW.service.raw SAW.service
    echo 'ExecStart=/usr/bin/python3 /home/'$(whoami)'/bin/SecAppWrapper/start_wrapper.py' >> SAW.service
    sudo cp SAW.service /etc/systemd/user/

    echo "enabling SAW.service!"
    systemctl --user enable SAW.service
    echo "starting service..."
    systemctl --user start SAW.service
    echo "Check systemctl --user status SAW.service to see if everything went well."
    echo "If something went wrong, check /var/log/SecAppWrapper.log!"
else
    echo "Installed without systemd"

fi
