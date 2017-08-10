import netifaces, time
from urllib.request import Request, urlopen
from flask import Flask, json
from urllib.parse import urlencode

# TODO: implement /attack detection
# TODO: implement /unregister
# TODO: implement /attack

class ApiURI:
    REGISTER = "/register"
    ATTACK = "/alert"
    KEEPALIVE = "/keep-alive"
    DELETE = "/delete"
class SAWrapper:
        app = Flask("WrapperInstance")
        group = None
        iface = None
        iface_mac = None
        controllerURL = None
        instanceID = None
        regTimeout = 60

        def __init__(self, saGroup, controllerURL, saIface="default"):
            print("Initiating new Wrapper Instance")
            self.group = saGroup
            self.controllerURL = controllerURL
            if(saIface == "default"):
                self.iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
            else:
                self.iface = saIface
            self.iface_mac = netifaces.ifaddresses('{0}'.format(self.iface))[netifaces.AF_LINK][0]['addr']
            print("Aquired HW_ADDR for interface {0}: {1}".format(self.iface, self.iface_mac))
            print("Sending Register Request to Controller...")
            connected = False
            # { "type": "REGISTER", "group": "saGroup", "hw_addr": "mac-address", "token": "secureToken", "misc": "misc info" }
            data = {'type': 'REGISTER', 'group': self.group, 'hw_addr': self.iface_mac, 'token': '', 'misc': ''}
            jsonData = json.dumps(data)
            while(connected == False):
                conn = Request(self.controllerURL+ApiURI.REGISTER, jsonData.encode("utf-8"), {'Content-Type': 'application/json'})
                resp = urlopen(conn)
                if(resp.getcode() == 200):
                    respData = json.loads(resp.read())
                    self.instanceID = respData['instanceID']
                    connected = True
                    resp.close()
                    print("Registration complete!")
                    print("Wrapper Instance registered with Instance ID: {0}".format(self.instanceID))
                if(resp.getcode() == 208):
                    # HTTP Code 208: Already Reported.
                    # Here: Already registered
                    print("Instance already registered. Carry on!")
                    connected = True
                    resp.close()
                else:
                    print("Connection failed. Retrying...")

            # Connection Established, Wrapper Instance registered. Start Keep-Alive messages to keep registration
            # Parallel Processing for keepalive and run!
            self.keepalive()

        def keepalive(self):
            # IDEA: keep-alive via cron and flask?
            kaData = {'type':'KEEP-ALIVE', 'name':self.instanceID, 'group':self.group, 'hw_addr':self.iface_mac,
                      'token':'','misc':''}
            jsonKaData = json.dumps(kaData)
            while(True):
                print("Waiting {0} seconds...".format(self.regTimeout))
                time.sleep(self.regTimeout)
                print("Initializing connection to Controller...")
                kaConn = Request(self.controllerURL+ApiURI.KEEPALIVE, jsonKaData.encode("utf-8"), {'Content-Type':'application/json'})
                kaResp = urlopen(kaConn)
                if(kaResp.getcode() == 200):
                    print("Keep-Alive successfully send! Closing conenction...")
                    kaResp.close()
                if(kaResp.getcode() == 500):
                    print("Controller not available, retrying...")
                    kaResp.close()
                    continue
                else:
                    print("Failed to send keep-alive")
                    # TODO what then?
                    break
            return 1

        @app.route('/attack', methods=['POST'])
        def run(self):
            # Send Fake Attack Detection Messages with Markov Model.
            print("ATTACK SEND")
            return 1