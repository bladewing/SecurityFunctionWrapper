"""
Simulate attacks with exponential distribution function.
"""
import numpy, time, math, json
from urllib.request import urlopen, Request

NOTIFY_URL="http://localhost:5001/attack"
prob=[1/100000,2/100000,3/100000]
ones = 0
zeros = 0
TIMEOUT = time.time() + 600
template = {"rate":"1", "misc":""}
data = json.dumps(template)
i = 0
count = 0
while count <=2:
    p = prob[count]
    i=0
    print("Probability: ",p)
    TIMEOUT = time.time() + 600
    while time.time() < TIMEOUT:
        n = numpy.random.exponential(scale=1.0, size=1)
        if time.time() > TIMEOUT:
            print("TIMEOUT")
            print("ones: ", ones, "percent: ", ones / (ones + zeros))
            print("zeros: ", zeros, "percent: ", zeros / (ones + zeros))
            break
        elif n[0] < math.log(1/(1-p)):
            conn = Request(NOTIFY_URL,data.encode('utf-8'), {'Content-Type': 'application/json'})
            resp = urlopen(conn)
            ones += 1
            print("Reported")
        else:
            zeros += 1
        i += 1
    count += 1
