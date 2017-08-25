# external Libs
import netifaces, jwt
from SecAppWrapper import ApiURI
# Standard Libs
from urllib.request import Request, urlopen
import urllib.error, logging
import json, time

# TODO: implement /unregister
# TODO: to implement /unregister daemonize the script.

class Wrapper():
        regTimeout = 5 # add to Argument list of constructor/init?
        secret = "5566F08A9218BEAF6E6714B5870161CBD12A975F6E516FAD66D28FE56302930D"
        def __init__(self, saGroup, saControllerURL, saIface):
            self.logger = logging.getLogger('SecAppWrapper.SAWrapper')
            self.logger.info("[INIT] Initiating new Wrapper Instance")
            self.group = saGroup
            self.controllerURL = saControllerURL
            self.ready = False
            self.instanceID = None
            self.token = None
            if(saIface == "default"):
                self.iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
            else:
                self.iface = saIface
            self.iface_mac = netifaces.ifaddresses('{0}'.format(self.iface))[netifaces.AF_LINK][0]['addr']
            self.logger.info("[INIT] Aquired HW_ADDR for interface %s: %s", self.iface, self.iface_mac)
            self.logger.info("[INIT] Sending Register Request to Controller... %s", self.iface_mac)
            connected = False
            # { "type": "REGISTER", "group": "saGroup", "hw_addr": "mac-address", "token": "secureToken", "misc": "misc info" }
            data = {'type': ApiURI.Type.REGISTER.name, 'group': self.group, 'hw_addr': self.iface_mac, 'misc': '', 'exp': int(time.time()+5*60)}
            regToken = jwt.encode(data, Wrapper.secret, algorithm='HS256')
            self.logger.info("[INIT] JWT generated: %s", str(regToken.decode("utf-8")))
            regTokenJ = {"token": regToken.decode("utf-8")}
            self.logger.info("[INIT] regTokenJ: %s", regTokenJ)
            jsonData = json.dumps(regTokenJ)
            while(connected == False):
                conn = Request(self.controllerURL+ApiURI.Type.REGISTER.value, jsonData.encode("utf-8"), {'Content-Type': 'application/json'})
                try:
                    resp = urlopen(conn)
                    if(resp.getcode() == 200):
                        self.logger.info("[INIT] Connection successful")
                        respData = json.loads(resp.read().decode("utf-8"))
                        payload = jwt.decode(respData["token"], Wrapper.secret, algorithms=['HS256'])
                        print(payload)
                        self.instanceID = payload['instanceID']
                        self.token = respData["token"]
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
            kaData = {'type': ApiURI.Type.KEEPALIVE.name, 'name': self.instanceID,
                      'group': self.group, 'hw_addr': self.iface_mac, 'misc': ''}
            jsonKaData = json.dumps(kaData)
            while (self.ready):
                if(self.ready == False): break
                self.logger.info("[KeepAlive] Waiting {0} seconds...".format(str(self.regTimeout)))
                time.sleep(self.regTimeout)
                self.logger.info("[KeepAlive] Initializing connection to Controller...")
                kaConn = Request(self.controllerURL + ApiURI.Type.KEEPALIVE.value,
                                 jsonKaData.encode("utf-8"),
                                 {'Content-Type': 'application/json', 'Authorization': "Bearer {0}".format(self.token)})
                kaResp = urlopen(kaConn)
                if (kaResp.getcode() == 200):
                    self.logger.info("[KeepAlive] Keep-Alive successfully send! Closing conenction...")
                    respData = json.loads(kaResp.read().decode("utf-8"))
                    self.token = respData["token"]
                    kaResp.close()
                elif (kaResp.getcode() == 500):
                    self.logger.warning("[KeepAlive] Controller not available, retrying...")
                    kaResp.close()
                    continue
                else:
                    self.logger.warning("[KeepAlive] Failed to send keep-alive")
                    # TODO what then?
                    break
            if(self.ready == False): print("Thank you...")
            return 1