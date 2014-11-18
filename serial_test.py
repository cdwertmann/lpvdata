import serial
import os

def get(command):
	ser.write('\r')
	line = ser.read()
	for char in command:
		ser.write(char)
		line = ser.read()
		
	ser.write('\r')
	line = ser.read() 
	line = ser.readline().strip('\n\r')  # read a '\n' terminated line
	values = line.split('\r')
	
	return line.split('\r')

ser = serial.Serial('/dev/ttyp0', 9600, timeout=2)

print get("I")

os.system("")

ser.close()

