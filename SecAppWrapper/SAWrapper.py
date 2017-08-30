""" Wrapper Module """
import time
import http
import json
import logging
import urllib.error
from urllib.request import Request, urlopen
import netifaces
import jwt

from SecAppWrapper import ApiURI

class Wrapper:
    """
    Initialize Wrapper Instance with group, controller URL, Interface, secret token and a timeout.
    """
    reg_timeout = None  # add to Argument list of constructor/init?
    secret = None

    def __init__(self, sa_group, sa_controller_url, sa_iface, secret, timeout):
        self.logger = logging.getLogger('SecAppWrapper.SAWrapper')
        self.logger.info("[INIT] Initiating new Wrapper Instance")
        self.group = sa_group
        self.controller_url = sa_controller_url
        self.ready = False
        self.instance_id = None
        self.token = None
        Wrapper.secret = secret
        Wrapper.reg_timeout = timeout * 60
        if sa_iface == "default":
            self.iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
        else:
            self.iface = sa_iface
        self.iface_mac = netifaces.ifaddresses('{0}'.format(self.iface))[netifaces.AF_LINK][0][
            'addr']
        self.logger.info("[INIT] Aquired HW_ADDR for interface %s: %s", self.iface, self.iface_mac)
        self.logger.info("[INIT] Sending Register Request to Controller... %s", self.iface_mac)
        connected = False
        # { "type": "REGISTER", "group": "sa_group", "hw_addr": "mac-address", "token":
        # "secureToken", "misc": "misc info" }
        data = {'type': ApiURI.Type.REGISTER.name, 'group': self.group, 'hw_addr': self.iface_mac,
                'misc': '', 'exp': int(time.time() + 5 * 60)}
        reg_token = jwt.encode(data, Wrapper.secret, algorithm='HS256')
        reg_token_j = {"token": reg_token.decode("utf-8")}
        json_data = json.dumps(reg_token_j)
        while not connected:
            conn = Request(self.controller_url + ApiURI.Type.REGISTER.value,
                           json_data.encode("utf-8"), {'Content-Type': 'application/json'})
            try:
                resp = urlopen(conn)
                if resp.getcode() == 200:
                    self.logger.info("[INIT] Connection successful")
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    payload = jwt.decode(resp_data["token"], Wrapper.secret, algorithms=['HS256'])
                    self.instance_id = payload['instance_id']
                    self.token = resp_data["token"]
                    connected = True
                    self.ready = True
                    self.logger.info(
                        "[INIT] Wrapper Instance registered with Instance ID: %s", self.instance_id)
                elif resp.getcode() == 208:
                    # HTTP Code 208: Already Reported.
                    # Here: Already registered
                    self.logger.info("[INIT] Instance already registered. Carry on!")
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    payload = jwt.decode(resp_data["token"], Wrapper.secret, algorithms=['HS256'])
                    self.instance_id = payload['instance_id']
                    self.token = resp_data["token"]
                    connected = True
                    self.ready = True
                    resp.close()
                else:
                    self.logger.warning("[INIT] Connection failed. Retrying...")
            except urllib.error.URLError as error:
                print(str(error))

        # Connection Established, Wrapper Instance registered. Start Keep-Alive messages to keep
        # registration
        if self.ready:
            self.logger.info("[INIT] Wrapper Instance is ready!")

    def keepalive(self):
        """
        Keep-Alive method. Requests new token upon expiration.
        :return:
        """
        # TODO: check own token for expiration
        ka_data = {'type': ApiURI.Type.KEEPALIVE.name, 'name': self.instance_id,
                   'group': self.group, 'hw_addr': self.iface_mac, 'misc': ''}
        json_ka_data = json.dumps(ka_data)
        while self.ready:
            self.logger.info("[KeepAlive] Waiting %s seconds...", self.reg_timeout)
            time.sleep(self.reg_timeout)
            self.logger.info("[KeepAlive] Initializing connection to Controller...")
            ka_conn = Request(self.controller_url + ApiURI.Type.KEEPALIVE.value,
                              json_ka_data.encode("utf-8"),
                              {'Content-Type': 'application/json',
                               'Authorization': "Bearer {0}".format(self.token)})
            # Check if controller is online:
            try:
                ka_resp = urlopen(ka_conn)
            except urllib.error.URLError:
                self.logger.warning("[KeepAlive] Controller not available, retrying...")
                continue
            except http.client.RemoteDisconnected:
                self.logger.warning("[KeepAlive] Controller not available, retrying...")
                continue
            if ka_resp.getcode() == 200:
                self.logger.info("[KeepAlive] Keep-Alive successfully send! Closing connection...")
                resp_data = json.loads(ka_resp.read().decode("utf-8"))
                self.token = resp_data["token"]
                ka_resp.close()
            elif ka_resp.getcode() == 500:
                self.logger.warning("[KeepAlive] Controller not available, retrying...")
                ka_resp.close()
                continue
            elif ka_resp.getcode() == 401:
                self.logger.warning("[KeepAlive] Got 'Unauthorized'...")
                resp_data = json.loads(ka_resp.read().decode("utf-8"))
                if resp_data["code"] == "token_expired":
                    self.logger.warning("[KeepAlive] Token expired.")
                    continue
            else:
                self.logger.warning(
                    "[KeepAlive] Failed to send keep-alive. Is Controller down? Retrying...")
                continue
        return 1
