# external libs
from flask import Flask, json, Response, make_response, request, jsonify
import flask.logging
from SecAppWrapper import ApiURI, SAWrapper
import requests, jwt

# Standard Libs
from urllib.request import urlopen, Request
import sys, getopt, threading, logging, signal, configparser

app = Flask(__name__)
wrapperInstance = None
# Initialize and load config.
config = configparser.ConfigParser()
config.read('wrapper.ini')
if(not config["GENERAL"]["port"]):
    print("Port missing in Config file!")
    sys.exit(0)

def main(argv):
    main.group = None
    main.controllerURL = None
    main.iface = None
    main.secret = config["Wrapper"]["secret"]
    main.timeout = int(config["Wrapper"]["timeout"]) if config["Wrapper"]["timeout"] else False
    if(len(argv) == 0):
        logger.info("[MAIN] No parameter detected. Loading from config file...")
        main.group = config["GENERAL"]["group"]
        main.controllerURL = config["GENERAL"]["controllerURL"]
        main.iface = config["GENERAL"]["iface"]
        if (not main.secret):
            raise ImportWarning("Configuration invalid. Secret missing.")
        if (not main.timeout):
            raise ImportWarning("Configuration invalid. Timeout missing.")
        try:
            r = requests.head(main.controllerURL)
        except requests.exceptions.InvalidURL:
            print("Invalid URL. Check Configuration File!")
            sys.exit(0)
        except:
            print("Server not available. Check URL in Config File!")
            sys.exit(0)
        if(not main.group or not main.controllerURL):
            print("Missing Arguments in configuration file.\nCheck Configuration or start with parameters!")
            print("See startWrapper.py -h")
            sys.exit(0)
    else:
        if(not main.secret):
            raise ImportWarning("Configuration invalid. Secret missing.")
        if(not main.timeout):
            raise ImportWarning("Configuration invalid. Timeout missing.")
        try:
            opts, args = getopt.getopt(argv, "vhg:u:i:", ["group=", "url=", "iface=", "verbose="])
        except getopt.GetoptError:
            print("Usage:\tstartWrapper.py -g groupname -u controllerURL [-i interface] [-v]")
            print("\tstartWrapper.py --group groupname --url controllerURL [--iface interface] [--verbose]")
            sys.exit(0)
        if (len(argv) == 4):
            print("Using default interface.")
        for opt, arg in opts:
            if(opt in ("-v","--verbose")):
                ch = logging.StreamHandler()
                ch.setLevel(logging.INFO)
                ch.setFormatter(formatter)
                logger.addHandler(ch)
            if(opt == '-h'):
                print("Usage:\tstartWrapper.py -g groupname -u controllerURL [-i interface] [-v]")
                print("\tstartWrapper.py --group groupname --url controllerURL [--iface interface] [--verbose]")
                sys.exit(0)
            elif(opt in ("-g", "--group")):
                main.group = arg
            elif(opt in ("-u", "--url")):
                try:
                    r = requests.head(arg)
                    main.controllerURL = arg
                except requests.exceptions.InvalidURL:
                    print("Invalid URL.")
                    sys.exit(0)
                except:
                    print("Server not available. Check URL: ", arg)
                    sys.exit(0)
            elif(opt in ("-i", "--iface")):
                main.iface = arg
        if(main.group == None or main.controllerURL == None):
            print("startWrapper.py\t---- illegal options.\nSee startWrapper.py -h for help")
            print("\t or configuration file is invalid. Check General Section of config file.")
            sys.exit(0)
    #print("Starting Wrapper Instance with following parameters: {0}, {1}, {2}".format(group, controllerURL, saIface))
    main.wrapperInstance = SAWrapper.Wrapper(main.group, main.controllerURL, main.iface, main.secret, main.timeout)
    main.thread1 = threading.Thread(target=main.wrapperInstance.keepalive)
    main.thread1.setDaemon(True)
    main.thread1.start()

    @app.route('/attack', methods=['POST'])
    def attack():
        # Send Fake Attack Detection Messages with Markov Model.
        # Also works as attack detection message.
        logger.info("[Attack] Wrapper ready, preparing data...") if main.wrapperInstance.ready else logger.warning("[Attack] Wrapper Instance not ready! Can't handle attacks from /attack")
        if (main.wrapperInstance.ready):
            logger.info("[Attack] Incoming report from Security Appliance")
            # Report Data Structure:
            # { "rate": "20", "misc": "information (???)"}
            reportData = request.get_json()
            # Attack Data Structure
            # {"type": "ATTACK", "name": "Firewall -1", "group": "firewall", "hw_addr": "00:00:00:00:00:01", "rate": "20",
            #  "misc": "information" }
            logger.info("[Attack] Preparing attack alert to Controller.")
            attackData = {'type': ApiURI.Type.ATTACK.name, 'name': main.wrapperInstance.instanceID, 'group': main.wrapperInstance.group,
                          'hw_addr': main.wrapperInstance.iface_mac,
                          'rate': reportData['rate'], 'misc': reportData['misc']}

            jsonAttackData = json.dumps(attackData)
            logger.info("[Attack] Initializing connection to Controller...")
            connected = False
            while (connected == False):
                conn = Request(main.wrapperInstance.controllerURL + ApiURI.Type.ATTACK.value, jsonAttackData.encode("utf-8"),
                               {'Content-Type': 'application/json', 'Authorization': "Bearer {0}".format(main.wrapperInstance.token)})
                attResp = urlopen(conn)
                if (attResp.getcode() == 200):
                    logger.info("[Attack] Successfully send attack report to Controller! Closing connection")
                    connected = True
                    attResp.close()
                else:
                    logger.warning("[Attack] Controller not available, retrying")
                    continue


        else:
            logger.warning("[Attack] Wrapper not registered!")
            attResp = make_response("Wrapper not registered.")
            attResp.status_code = 503
            return attResp
        return "ok"

def sigterm_handler(signal, frame):
    logger.info("[SIGTERM DELETE] SIGTERM Signal catched. Shutting down keep-alive thread...")
    main.wrapperInstance.ready = False
    main.thread1.join()
    # Send unregister here!
    # Payload: {"type": "DELETE", "name": "instanceID", "misc": "misc info"}
    payload = {'type': ApiURI.Type.DELETE.name, 'name': str(main.wrapperInstance.instanceID), 'misc':''}
    jsonPayload = json.dumps(payload)
    delConn = Request(main.controllerURL + ApiURI.Type.DELETE.value,
                     jsonPayload.encode("utf-8"),
                     {'Content-Type': 'application/json', 'Authorization': "Bearer {0}".format(main.wrapperInstance.token)})
    logger.info("[SIGTERM DELETE] Payload prepared. Connecting...")
    delResp = urlopen(delConn)
    if(delResp.getcode() == 200):
        logger.info("[SIGTERM DELETE] Delete Message sent successfully. Shutting down keep-alive thread...")
    else:
        logger.error("[SIGTERM DELETE] Sending Delete request failed with Code:%s", delResp.getcode())
    logger.info("[SIGTERM DELETE] Bye.")
    sys.exit(0)

if(__name__ == "__main__"):
    signal.signal(signal.SIGTERM, sigterm_handler)
    # Create logger
    logger = logging.getLogger('SecAppWrapper')
    logger.setLevel(logging.INFO)
    # Create FileHandler to save logs in File.
    fh = logging.FileHandler('startWrapper.log')
    # Format logger
    formatter = logging.Formatter('%(asctime)s <%(name)s> - <%(levelname)s> : %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    #Adding FileHandler to logger of Flask App to merge log files.
    app.logger.addHandler(fh)

    main(sys.argv[1:])
    try:
        app.run(debug=False, host='0.0.0.0', port=int(config["GENERAL"]["port"]))
    except OSError as e:
        print("Port already in use! Change port in config!")
        sys.exit(0)