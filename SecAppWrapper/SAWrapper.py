import netifaces, time
from SecAppWrapper import ApiURI
from urllib.request import Request, urlopen
import urllib.error, logging
import json

# TODO: implement /unregister
# TODO: to implement /unregister daemonize the script.

class Wrapper():
        regTimeout = 60 # add to Argument list of constructor/init?
        def __init__(self, saGroup, saControllerURL, saIface):
            self.logger = logging.getLogger('SecAppWrapper.SAWrapper')
            self.logger.info("[INIT] Initiating new Wrapper Instance")
            self.group = saGroup
            self.controllerURL = saControllerURL
            self.ready = False
            self.instanceID = None
            if(saIface == "default"):
                self.iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
            else:
                self.iface = saIface
            self.iface_mac = netifaces.ifaddresses('{0}'.format(self.iface))[netifaces.AF_LINK][0]['addr']
            self.logger.info("[INIT] Aquired HW_ADDR for interface {0}: {1}".format(self.iface, self.iface_mac))
            self.logger.info("[INIT] Sending Register Request to Controller...")
            connected = False
            # { "type": "REGISTER", "group": "saGroup", "hw_addr": "mac-address", "token": "secureToken", "misc": "misc info" }
            data = {'type': ApiURI.Type.REGISTER.name, 'group': self.group, 'hw_addr': self.iface_mac, 'token': '', 'misc': ''}
            jsonData = json.dumps(data)
            while(connected == False):
                conn = Request(self.controllerURL+ApiURI.Type.REGISTER.value, jsonData.encode("utf-8"), {'Content-Type': 'application/json'})
                try:
                    resp = urlopen(conn)
                    if(resp.getcode() == 200):
                        self.logger.info("[INIT] Connection successful")
                        respData = json.loads(resp.read())
                        self.instanceID = respData['instanceID']
                        connected = True
                        self.ready = True
                        self.logger.info("[INIT] Wrapper Instance registered with Instance ID: {0}".format(self.instanceID))
                    elif(resp.getcode() == 208):
                        # HTTP Code 208: Already Reported.
                        # Here: Already registered
                        self.logger.info("[INIT] Instance already registered. Carry on!")
                        connected = True
                        self.ready = True
                        resp.close()
                    else:
                        self.logger.warning("[INIT] Connection failed. Retrying...")
                except urllib.error.URLError as error:
                    print(str(error))

            # Connection Established, Wrapper Instance registered. Start Keep-Alive messages to keep registration
            if(self.ready):
                self.logger.info("[INIT] Wrapper Instance is ready!")

        def keepalive(self):
            # IDEA: keep-alive via cron and flask?
            kaData = {'type': ApiURI.Type.KEEPALIVE.name, 'name': self.instanceID,
                      'group': self.group, 'hw_addr': self.iface_mac,
                      'token': '', 'misc': ''}
            jsonKaData = json.dumps(kaData)
            while (self.ready):
                self.logger.info("[KeepAlive] Waiting {0} seconds...".format(self.regTimeout))
                time.sleep(self.regTimeout)
                '''
                self.logger.info("[KeepAlive] Initializing connection to Controller...")
                kaConn = Request(self.controllerURL + ApiURI.Type.KEEPALIVE.value,
                                 jsonKaData.encode("utf-8"),
                                 {'Content-Type': 'application/json'})
                kaResp = urlopen(kaConn)
                if (kaResp.getcode() == 200):
                    self.logger.info("[KeepAlive] Keep-Alive successfully send! Closing conenction...")
                    kaResp.close()
                elif (kaResp.getcode() == 500):
                    self.logger.warning("[KeepAlive] Controller not available, retrying...")
                    kaResp.close()
                    continue
                else:
                    self.logger.warning("[KeepAlive] Failed to send keep-alive")
                    # TODO what then?
                    break
                '''
            return 1