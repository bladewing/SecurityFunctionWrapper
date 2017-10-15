"""
Simulate attacks with exponential distribution function.
"""
import numpy, time, math, json
from urllib.request import urlopen, Request

NOTIFY_URL="http://localhost:5001/attack"
p=1/100
ones = 0
zeros = 0
print("Calculating n...")
n = numpy.random.exponential(scale=1.0, size=10**6)
TIMEOUT = time.time() + 600
template = {"rate":"1", "misc":""}
data = json.dumps(template)
i = 0
while True:
    if time.time() > TIMEOUT:
        print("TIMEOUT")
        print("ones: ", ones, "percent: ", ones / (ones + zeros))
        print("zeros: ", zeros, "percent: ", zeros / (ones + zeros))
        break
    elif i >= len(n):
        i = 0
    elif n[i] < math.log(1/(1-p)):
        conn = Request(NOTIFY_URL,data.encode('utf-8'), {'Content-Type': 'application/json'})
        resp = urlopen(conn)
        ones += 1
    else:
        zeros += 1
    i += 1