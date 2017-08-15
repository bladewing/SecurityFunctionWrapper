import netifaces, time
from SecAppWrapper import ApiURI
from urllib.request import Request, urlopen
import urllib.error
import json

# TODO: implement /unregister
# TODO: to implement /unregister daemonize the script.

class Wrapper():
        regTimeout = 60 # add to Argument list of constructor/init?
        def __init__(self, saGroup, saControllerURL, saIface):
            print("<SAWrapper> Initiating new Wrapper Instance")
            self.group = saGroup
            self.controllerURL = saControllerURL
            self.ready = False
            self.instanceID = None
            if(saIface == "default"):
                self.iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
            else:
                self.iface = saIface
            self.iface_mac = netifaces.ifaddresses('{0}'.format(self.iface))[netifaces.AF_LINK][0]['addr']
            print("<SAWrapper> Aquired HW_ADDR for interface {0}: {1}".format(self.iface, self.iface_mac))
            print("<SAWrapper> Sending Register Request to Controller...")
            connected = False
            # { "type": "REGISTER", "group": "saGroup", "hw_addr": "mac-address", "token": "secureToken", "misc": "misc info" }
            data = {'type': ApiURI.Type.REGISTER.name, 'group': self.group, 'hw_addr': self.iface_mac, 'token': '', 'misc': ''}
            jsonData = json.dumps(data)
            while(connected == False):
                conn = Request(self.controllerURL+ApiURI.Type.REGISTER.value, jsonData.encode("utf-8"), {'Content-Type': 'application/json'})
                try:
                    resp = urlopen(conn)
                    if(resp.getcode() == 200):
                        print("<SAWrapper> Connection successful")
                        respData = json.loads(resp.read())
                        self.instanceID = respData['instanceID']
                        connected = True
                        self.ready = True
                        print("<SAWrapper> Wrapper Instance registered with Instance ID: {0}".format(self.instanceID))
                    elif(resp.getcode() == 208):
                        # HTTP Code 208: Already Reported.
                        # Here: Already registered
                        print("<SAWrapper> Instance already registered. Carry on!")
                        connected = True
                        self.ready = True
                        resp.close()
                    else:
                        print("<SAWrapper> Connection failed. Retrying...")
                except urllib.error.URLError as error:
                    print(str(error))

            # Connection Established, Wrapper Instance registered. Start Keep-Alive messages to keep registration
            # Parallel Processing for keepalive and run!
            if(self.ready):
                print("<SAWrapper> I am ready!")
            #_thread.start_new_thread(self.keepalive, ())

        def keepalive(self):
            # IDEA: keep-alive via cron and flask?
            kaData = {'type': ApiURI.Type.KEEPALIVE.name, 'name': self.instanceID,
                      'group': self.group, 'hw_addr': self.iface_mac,
                      'token': '', 'misc': ''}
            jsonKaData = json.dumps(kaData)
            while (self.ready):
                print("<SAWrapper:KeepAlive> Waiting {0} seconds...".format(self.regTimeout))
                time.sleep(self.regTimeout)
                '''
                print("Initializing connection to Controller...")
                kaConn = Request(self.controllerURL + ApiURI.Type.KEEPALIVE.value,
                                 jsonKaData.encode("utf-8"),
                                 {'Content-Type': 'application/json'})
                kaResp = urlopen(kaConn)
                if (kaResp.getcode() == 200):
                    print("Keep-Alive successfully send! Closing conenction...")
                    kaResp.close()
                elif (kaResp.getcode() == 500):
                    print("Controller not available, retrying...")
                    kaResp.close()
                    continue
                else:
                    print("Failed to send keep-alive")
                    # TODO what then?
                    break
                '''
            return 1