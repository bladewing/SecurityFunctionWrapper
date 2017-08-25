# external libs
from flask import Flask, json, Response, make_response, request, jsonify
import flask.logging
from SecAppWrapper import ApiURI, SAWrapper
import requests, jwt

# Standard Libs
from urllib.request import urlopen, Request
import sys, getopt, threading, logging, signal

app = Flask(__name__)
wrapperInstance = None

def main(argv):
    main.group = None
    main.controllerURL = None
    main.iface = "default"
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
        sys.exit(0)
    #print("Starting Wrapper Instance with following parameters: {0}, {1}, {2}".format(group, controllerURL, saIface))
    main.wrapperInstance = SAWrapper.Wrapper(main.group, main.controllerURL, main.iface)
    main.thread1 = threading.Thread(target=main.wrapperInstance.keepalive)
    main.thread1.setDaemon(True)
    main.thread1.start()

    @app.route('/attack', methods=['POST'])
    def attack():
        # Send Fake Attack Detection Messages with Markov Model.
        # Also works as attack detection message.
        logger.info("[Attack] Wrapper ready, preparing data...") if main.wrapperInstance.ready else logger.warning("[Attack] Wrapper Instance not ready! Can't handle attacks from /attack")
        if (main.wrapperInstance.ready):
            logger.info("[Attack] Incoming report from Security Appliance {0}".format(str(main.wrapperInstance.instanceID)))
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
            attackData = {'type': ApiURI.Type.ATTACK.name, 'name': main.wrapperInstance.instanceID, 'group': main.wrapperInstance.group,
                          'hw_addr': main.wrapperInstance.iface_mac,
                          'rate': reportData['rate'], 'misc': ''}

            jsonAttackData = json.dumps(attackData)
            logger.info("[Attack] Initializing connection to Controller...")
            connected = False
            while (connected == False):
                conn = Request(main.wrapperInstance.controllerURL + ApiURI.Type.ATTACK.value, jsonAttackData.encode("utf-8"),
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
    logger.info("[SIGTERM DELETE] SIGTERM Signal catched. Preparing shutdown...")
    print(main.wrapperInstance)
    # Send unregister here!
    # Payload: {"type": "DELETE", "name": "instanceID", "misc": "misc info"}
    payload = {'type': ApiURI.Type.DELETE.name, 'name': str(main.wrapperInstance.instanceID), 'misc':''}
    print(payload)
    jsonPayload = json.dumps(payload)
    delConn = Request(main.controllerURL + ApiURI.Type.DELETE.value,
                     jsonPayload.encode("utf-8"),
                     {'Content-Type': 'application/json', 'Authorization': "Bearer {0}".format(main.wrapperInstance.token)})
    logger.info("[SIGTERM DELETE] Payload prepared. Connecting...")
    delResp = urlopen(delConn)
    if(delResp.getcode() == 200):
        logger.info("[SIGTERM DELETE] Delete Message sent successfully. Shutting down keep-alive thread...")
        main.wrapperInstance.ready = False
        main.thread1.join()
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
    app.run(debug=False, host='0.0.0.0', port=5001)