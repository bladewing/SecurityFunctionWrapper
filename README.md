## Security Appliance Wrapper

Wrapper running on Security Appliance to communicate with the Function Chaining Controller to alert Controller of attacks.

## Prerequisites
The Wrapper is written in **_Python3_**.
These Python Packages need to be installed with pip3:

*flask, requests, jwt (PyJWT), netifaces*

To install pip3 use following command:

`sudo apt-get install python3-pip`

Finally use pip3 to install the packages:

`sudo pip3 install flask requests netifaces PyJWT`

**Note:** Installing *netifaces* requires sudo.

## Quickstart

After all prerequisites are installed, modify the config-file *wrapper.ini*. Then simply start the Wrapper with

`python3 start_wrapper.py`

For debugging purposes and enabling verbose see

`python3 start_wrapper.py -h`

for usage.

**Note:** The Controller must be running before starting the Wrapper!

## Installation

After all prerequisites are installed, start the *setup.sh* as user.

`chmod +x setup.sh && sudo ./setup.sh`

**Note:** This will copy all files to /home/USER/bin. Installing with root not recommended.

**Note:** `sudo` is needed to copy the *.service* File to the /etc/systemd/user directory.

*setup.sh* will automatically start the service. If there are errors or something is not working, check the log-file at

*/var/log/SecAppWrapper.log*

Starting the service:

`systemctl --user start SAW.service`

Stopping the service:

`systemctl --user stop SAW.service`

And restarting the service:

`systemctl --user restart SAW.service`

## Uninstall

*uninstall.sh* will delete all copied files from *setup.sh*, disable the service and delete it form its */etc/systemd/user/* directory.

`chmod +x uninstall.sh && sudo ./uninstall.sh`

**Note:** `sudo` is needed again to delete the service from */etc/systemd/user/* directory
**Note:** This will also delete the log-file! Create Backup if needed.

It is recommended to re-install the Wrapper after changes are made to the script.


# TODO:

~~-- Add Wrapper as a service.~~