# external libs
from flask import Flask, json, Response, make_response, request
import flask.logging
from SecAppWrapper import ApiURI, SAWrapper
import requests

# Standard Libs
from urllib.request import urlopen, Request
import sys, getopt, threading, logging, signal

app = Flask(__name__)
wrapperInstance = None

def main(argv):
    group = None
    controllerURL = None
    iface = "default"
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
            group = arg
        elif(opt in ("-u", "--url")):
            try:
                r = requests.head(arg)
                controllerURL = arg
            except requests.exceptions.InvalidURL:
                print("Invalid URL.")
                sys.exit(0)
            except:
                print("Server not available. Check URL: ", arg)
                sys.exit(0)
        elif(opt in ("-i", "--iface")):
            iface = arg
    if(group == None or controllerURL == None):
        print("startWrapper.py\t---- illegal options.\nSee startWrapper.py -h for help")
        sys.exit(0)
    #print("Starting Wrapper Instance with following parameters: {0}, {1}, {2}".format(group, controllerURL, saIface))
    wrapperInstance = SAWrapper.Wrapper(str(group), str(controllerURL), str(iface))
    thread1 = threading.Thread(target=wrapperInstance.keepalive)
    thread1.setDaemon(True)
    thread1.start()


    @app.route('/attack', methods=['POST'])
    def attack():
        # Send Fake Attack Detection Messages with Markov Model.
        # Also works as attack detection message.
        logger.info("[Attack] Wrapper ready, preparing data...") if wrapperInstance.ready else logger.warning("[Attack] Wrapper Instance not ready! Can't handle attacks from /attack")
        resp = make_response("Lol")
        if (wrapperInstance.ready):
            logger.info("[Attack] Incoming report from Security Appliance {0}".format(wrapperInstance.instanceID))
            # Report Data Structure:
            # { "rate": "20", "misc": "information (???)"}
            try:
                reportData = request.get_json()
                print(reportData)
            except TypeError:
                print("haha")
                sys.exit(0)
            # Attack Data Structure
            # {"type": "ATTACK", "name": "Firewall -1", "group": "firewall", "hw_addr": "00:00:00:00:00:01", "rate": "20",
            #  "token": "secure -token", "misc": "information" }
            logger.info("[Attack] Preparing attack alert to Controller.")
            attackData = {'type': ApiURI.Type.ATTACK.name, 'name': wrapperInstance.instanceID, 'group': wrapperInstance.group,
                          'hw_addr': wrapperInstance.iface_mac,
                          'rate': reportData['rate'], 'token': '', 'misc': ''}
            jsonAttackData = json.dumps(attackData)
            logger.info("[Attack] Initializing connection to Controller...")
            connected = False
            while (connected == False):
                conn = Request(wrapperInstance.controllerURL + ApiURI.Type.ATTACK.value, jsonAttackData.encode("utf-8"),
                               {'Content-Type': 'application/json'})
                attResp = urlopen(conn)
                print("attResp.getcode(): ", attResp.getcode())
                if (attResp.getcode() == 200):
                    logger.info("[Attack] Successfully send attack report to Controller! Closing connection")
                    connected = True
                    resp.status_code = 200
                    attResp.close()
                else:
                    logger.warning("[Attack] Controller not available, retrying")
                    continue


        else:
            logger.warning("[Attack] Wrapper not registered!")
            attResp = make_response("Wrapper not registered.")
            attResp.status_code = 503
            return attResp
        return resp

def sigterm_handler(signal, frame):
    # Send unregister here!
    print("Got SIGTERM. Bye cruel world...")
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
    app.run(debug=False, host='0.0.0.0', port=5001)