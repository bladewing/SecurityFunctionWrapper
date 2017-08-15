# external libs
from flask import Flask, json, Response, make_response, request
from SecAppWrapper import ApiURI, SAWrapper
import requests

# Standard Libs
from urllib.request import urlopen, Request
import sys, getopt
import threading

app = Flask(__name__)
wrapperInstance = None

def main(argv):
    group = None
    controllerURL = None
    iface = "default"
    try:
        opts, args = getopt.getopt(argv, "hg:u:i:", ["group=", "url=", "iface="])
    except getopt.GetoptError:
        print("startWrapper.py -g groupname -u controllerURL (-i interface)")
        print("startWrapper.py --group groupname --url controllerURL (--iface interface)")
        sys.exit(0)
    if (len(argv) == 4):
        print("Using default interface.")
    for opt, arg in opts:
        if(opt == '-h'):
            print("startWrapper.py -group groupname -url controllerURL -iface interface")
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
        print("Usage: startWrapper.py -g groupname -u controllerURL (-i interface)")
        print("Optional: startWrapper.py --group groupname --url controllerURL (--iface interface)")
        sys.exit(0)
    #print("Starting Wrapper Instance with following parameters: {0}, {1}, {2}".format(group, controllerURL, saIface))
    with SAWrapper as wrapper:
        wrapperInstance = SAWrapper.Wrapper(group, controllerURL, iface)
        thread1 = threading.Thread(target=wrapperInstance.keepalive)
        thread1.setDaemon(True)
        thread1.start()


    @app.route('/attack', methods=['POST'])
    def attack():
        # Send Fake Attack Detection Messages with Markov Model.
        # Also works as attack detection message.
        print("Wrapper ready: ",wrapperInstance.ready)
        if (wrapperInstance.ready):
            print("Incoming report from Security Appliance {0}".format(wrapperInstance.instanceID))
            # Report Data Structure:
            # { "rate": "20", "misc": "information (???)"}
            reportData = request.get_json()
            print(reportData)
            # Attack Data Structure
            # {"type": "ATTACK", "name": "Firewall -1", "group": "firewall", "hw_addr": "00:00:00:00:00:01", "rate": "20",
            #  "token": "secure -token", "misc": "information" }
            print("Preparing attack alert to Controller.")
            attackData = {'type': ApiURI.Type.ATTACK.name, 'name': wrapperInstance.instanceID, 'group': wrapperInstance.group,
                          'hw_addr': wrapperInstance.iface_mac,
                          'rate': reportData['rate'], 'token': '', 'misc': ''}
            jsonAttackData = json.dumps(attackData)
            print("Initializing connection to Controller...")
            connected = False
            while (connected == False):
                conn = Request(wrapperInstance.controllerURL + ApiURI.Type.ATTACK.value, jsonAttackData.encode("utf-8"),
                               {'Content-Type': 'application/json'})
                attResp = urlopen(conn)
                if (attResp.getcode() == 200):
                    print("Successfully send attack report to Controller! Closing connection")
                    connected = True
                    attResp.close()
                else:
                    print("Controller not available, retrying")
                    continue


        else:
            print("Wrapper not registered!")
            attResp = make_response("Wrapper not registered.")
            attResp.status_code = 503
            return attResp
        return 1

if(__name__ == "__main__"):
    main(sys.argv[1:])
    app.run(debug=False, host='0.0.0.0', port=5001)