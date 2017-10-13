""" Starts the wrapper. Either with parameters or with config file! """
import signal
import sys
import threading
from urllib.request import urlopen, Request
import configparser
import getopt
import logging
import os
import requests
from flask import Flask, json, make_response, request

from SecAppWrapper import ApiURI, SAWrapper

APP = Flask(__name__)
WRAPPER_INSTANCE = None
# Initialize and load CONFIG.
CONFIG = configparser.ConfigParser()
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'wrapper.ini')
CONFIG.read(CONFIG_FILE)
if not CONFIG["GENERAL"]["port"]:
    print("Port missing in Config file!")
    sys.exit(0)


def main(argv):
    """
    Check if CONFIG file is available and configured. Else start wrapper Instance with parameters.
    Create Wrapper Instance with parameters or configuration data. Start keep-alive function in a
    seperate thread as it contains an infinite loop.
    :param argv:
    :return:
    """
    main.group = None
    main.controller_url = None
    main.iface = None
    main.secret = CONFIG["Wrapper"]["secret"]
    main.timeout = int(CONFIG["Wrapper"]["timeout"]) if CONFIG["Wrapper"]["timeout"] else False
    if not argv:
        LOGGER.info("[MAIN] No parameter detected. Loading from CONFIG file...")
        main.group = CONFIG["GENERAL"]["group"]
        main.controller_url = CONFIG["GENERAL"]["controller_url"]
        main.iface = CONFIG["GENERAL"]["iface"]
        if not main.secret:
            raise ImportWarning("Configuration invalid. Secret missing.")
        if not main.timeout:
            raise ImportWarning("Configuration invalid. Timeout missing.")
        try:
            requests.head(main.controller_url)
        except requests.exceptions.InvalidURL:
            LOGGER.error("[MAIN] Invalid URL. Check Configuration File!")
            sys.exit(0)
        except:
            LOGGER.error("[MAIN] Server not available. Check URL in Config File!")
            sys.exit(0)
        if not main.group or not main.controller_url:
            LOGGER.warning(
                "[MAIN] Missing Arguments in configuration file.\nCheck Configuration or start "
                "with parameters!\n See start_wrapper.py -h")
            sys.exit(0)
    else:
        if not main.secret:
            raise ImportWarning("Configuration invalid. Secret missing.")
        if not main.timeout:
            raise ImportWarning("Configuration invalid. Timeout missing.")
        try:
            opts, args = getopt.getopt(argv, "vhg:u:i:", ["group=", "url=", "iface=", "verbose="])
        except getopt.GetoptError:
            print("Usage:\tstart_wrapper.py -g groupname -u controller_url [-i interface] [-v]")
            print("\tstart_wrapper.py --group groupname --url controller_url [--iface interface] ["
                  "--verbose]")
            sys.exit(0)
        if len(argv) == 4:
            LOGGER.info("[MAIN] Using default interface.")
        for opt, arg in opts:
            if opt in ("-v", "--verbose"):
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(LOGGER_FORMATTER)
                LOGGER.addHandler(console_handler)
            if opt == '-h':
                print("Usage:\tstart_wrapper.py -g groupname -u controller_url [-i interface] [-v]")
                print("\tstart_wrapper.py --group groupname --url controller_url [--iface "
                      "interface] [--verbose]")
                sys.exit(0)
            elif opt in ("-g", "--group"):
                main.group = arg
            elif opt in ("-u", "--url"):
                try:
                    requests.head(arg)
                    main.controller_url = arg
                except requests.exceptions.InvalidURL:
                    LOGGER.error("[MAIN] Invalid URL.")
                    sys.exit(0)
                except:
                    LOGGER.error("[MAIN] Server not available. Check URL: %s", arg)
                    sys.exit(0)
            elif opt in ("-i", "--iface"):
                main.iface = arg
        if main.group is None or main.controller_url is None:
            print("start_wrapper.py\t---- illegal options.\nSee start_wrapper.py -h for help")
            print("or configuration file is invalid. Check General Section of CONFIG file.")
            sys.exit(0)
    # print("Starting Wrapper Instance with following parameters: {0}, {1}, {2}".format(group,
    # controller_url, saIface))
    main.wrapper_instance = SAWrapper.Wrapper(main.group, main.controller_url, main.iface,
                                              main.secret, main.timeout)
    main.thread1 = threading.Thread(target=main.wrapper_instance.keepalive)
    main.thread1.setDaemon(True)
    main.thread1.start()

    @APP.route('/attack', methods=['POST'])
    def attack():
        """
        Handle incoming attack report from Security Appliance and report it to Controller.
        :return:
        """
        if main.wrapper_instance.ready:
            LOGGER.info("[Attack] Wrapper ready, preparing data...")
        else:
            LOGGER.warning("[Attack] Wrapper Instance not ready! Can't handle attacks from /attack")
        if main.wrapper_instance.ready:
            LOGGER.info("[Attack] Incoming report from Security Appliance")
            # Report Data Structure:
            # { "rate": "20", "misc": "information (???)"}
            print(request.get_json())
            report_data = request.get_json()
            print(report_data)
            # Attack Data Structure {"type": "ATTACK", "name": "Firewall -1", "group":
            # "firewall", "hw_addr": "00:00:00:00:00:01", "rate": "20", "misc": "information" }
            LOGGER.info("[Attack] Preparing attack alert to Controller.")
            attack_data = {'type': ApiURI.Type.ATTACK.name, 'name': main.wrapper_instance.instance_id,
                           'group': main.wrapper_instance.group,
                           'hw_addr': main.wrapper_instance.iface_mac,
                           'rate': report_data['rate'], 'misc': report_data['misc']}

            json_attack_data = json.dumps(attack_data)
            LOGGER.info("[Attack] Initializing connection to Controller...")
            connected = False
            while not connected:
                conn = Request(main.wrapper_instance.controller_url + ApiURI.Type.ATTACK.value,
                               json_attack_data.encode("utf-8"),
                               {'Content-Type': 'application/json',
                                'Authorization': "Bearer {0}".format(main.wrapper_instance.token)})
                att_resp = urlopen(conn)
                if att_resp.getcode() == 200:
                    LOGGER.info("[Attack] Successfully send attack report to Controller! Closing "
                                "connection")
                    connected = True
                    att_resp.close()
                else:
                    LOGGER.warning("[Attack] Controller not available, retrying")
                    continue
        else:
            LOGGER.warning("[Attack] Wrapper not registered!")
            att_resp = make_response("Wrapper not registered.")
            att_resp.status_code = 503
            return att_resp
        return "ok"


def sigterm_handler(sig, frame):
    """
    Handle SIGTERM Signal. Shutdown Wrapper Instance gracefully.
    :return:
    """
    LOGGER.info("[SIGTERM DELETE] SIGTERM Signal catched. Shutting down keep-alive thread...")
    main.wrapper_instance.ready = False
    main.thread1.join()
    LOGGER.info("[SIGTERM DELETE] Keep-alive thread successfully shut down. Sending Delete "
                "Request...")
    # Send unregister here!
    # Payload: {"type": "DELETE", "name": "instance_id", "misc": "misc info"}
    payload = {'type': ApiURI.Type.DELETE.name, 'name': str(main.wrapper_instance.instance_id),
               'misc': ''}
    json_payload = json.dumps(payload)
    del_conn = Request(main.controller_url + ApiURI.Type.DELETE.value, json_payload.encode("utf-8"),
                       {'Content-Type': 'application/json',
                        'Authorization': "Bearer {0}".format(main.wrapper_instance.token)})
    LOGGER.info("[SIGTERM DELETE] Payload prepared. Connecting...")
    del_resp = urlopen(del_conn)
    if del_resp.getcode() == 200:
        LOGGER.info("[SIGTERM DELETE] Delete Message sent successfully. Shutting down keep-alive "
                    "thread...")
    else:
        LOGGER.error("[SIGTERM DELETE] Sending Delete request failed with Code:%s",
                     del_resp.getcode())
    LOGGER.info("[SIGTERM DELETE] Bye.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)
    # Create LOGGER
    LOGGER = logging.getLogger('SecAppWrapper')
    LOGGER.setLevel(logging.INFO)
    # Create FileHandler to save logs in File.
    LOG_FILE = '/var/log/SecAppWrapper.log'
    FILE_HANDLER = logging.FileHandler(LOG_FILE)
    # Format LOGGER
    LOGGER_FORMATTER = logging.Formatter('%(asctime)s <%(name)s> - <%(levelname)s> : %(message)s')
    FILE_HANDLER.setFormatter(LOGGER_FORMATTER)
    LOGGER.addHandler(FILE_HANDLER)
    # Adding FileHandler to LOGGER of Flask App to merge log files.
    APP.logger.addHandler(FILE_HANDLER)

    main(sys.argv[1:])
    try:
        APP.run(debug=False, host='0.0.0.0', port=int(CONFIG["GENERAL"]["port"]))
    except OSError:
        LOGGER.info("[MAIN FLASK] Port already in use! Change port in CONFIG!")
        sys.exit(0)
