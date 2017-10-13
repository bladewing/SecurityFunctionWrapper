"""
Simulate attacks with exponential distribution function.
"""
import numpy, time, math

NOTIFY_URL="http://localhost:5001/attack"

ones = 0
zeros = 0
print("Calculating n...")
n = numpy.random.exponential(scale=1.0, size=10**6)
TIMEOUT = time.time() + 10

i = 0
while True:
    if time.time() > TIMEOUT:
        print("TIMEOUT")
        print("ones: ", ones, "percent: ", ones / (ones + zeros))
        print("zeros: ", zeros, "percent: ", zeros / (ones + zeros))
        break
    elif i >= len(n):
        i = 0
    elif n[i] < math.log(3/2):
        ones += 1
    else:
        zeros += 1
    i += 1