import math
import numpy as np 

x = float(input("Enter goal x:"))
y = float(input("Enter goal y:"))
z = float(input("Enter goal z:"))

r = 0.185
dx = x
dy = y + 0.185
d = math.sqrt((dx**2) + (dy**2))

k = (r**2) / (d**2)
m = (r*math.sqrt((d**2)-(r**2))) / (d**2)

T1x = k*dx - m*dy
T1y = -0.185 + (k*dy + m*dx)

T2x = k*dx + m*dy
T2y = -0.185 + (k*dy - m*dx)


leng_tan = math.sqrt((d**2)-(r**2))

dr = 180/math.pi
# theta1_T1 = (math.atan2((T1y+0.185) , T1x))*dr
# theta1_T2 = (math.atan2((T2y+0.185) , T2x))*dr

theta_1_T1 = abs((math.atan2(T1x , (T1y+0.185)))*dr)
# theta_1_T2 = (math.atan2(T2x , (T2y+0.185)))*dr


l1 = 0.485
l2 = 0.55
n = leng_tan

theta_3 = ((l1**2)+(l2**2)-(n**2)-(z**2))/(2*l1*l2)
theta_3 = 180 - (math.acos(theta_3)) * dr

m = math.sqrt((n**2)+(z**2))
phi = math.atan2(z,n)
alpha = math.acos(((l1**2)+(m**2)-(l2**2))/(2*l1*m))
theta_2 = 90 - (phi*dr + alpha*dr)


print("GPT based theta1 vals")
#print("Theta1_T1: ", theta1_T1)
#print("Theta1_T2: ", theta1_T2)

print("My theta approximation")
print("Theta1_T1: ", theta_1_T1)
#print("Theta1_T2: ", theta_1_T2)
print("length of tangent:",leng_tan)
print("Theta2:", theta_2)
print("Theta3:", theta_3)

