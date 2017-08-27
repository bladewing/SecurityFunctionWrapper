## Security Appliance Wrapper

Wrapper running on Security Appliance to communicate with the Function Chaining Controller to alert Controller of attacks.

## Prerequisites
The Wrapper is written in **_Python3_**.
These Python Packages need to be installed with pip3:
*flask, requests, jwt (PyJWT)*

To install pip3 use following command:
`sudo apt-get install python3-pip`

## Quickstart

After all prerequisites are installed, modify the config-file *wrapper.ini*. Then simply start the Wrapper with
`python3 startWrapper.py`
**Note:** The Controller must be running before starting the Wrapper!