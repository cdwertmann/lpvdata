#!/usr/bin/python

# Read data from SMA PV-WR 1500/1800 solar energy inverter
# implementation for serial port <-> TCP converter box
# (c) 2011 Christoph Dwertmann

import os, random, time, threading, signal, sys, BaseHTTPServer
import urllib, urlparse, string, sqlite3, subprocess
import socket, time

def send_receive(command):
	print "Sending: " + command
	for char in command:
		try:
			client_socket.send(char)
			client_socket.recv(1)
		except:
			return False

	try:
		client_socket.send('\r')
		client_socket.recv(1)
	except:
		return False

	buffer = ''
	while 1:
		try:
			buffer += client_socket.recv(1024)
		except socket.timeout:
			break
		if buffer.endswith('\r\n'):
			buffer=buffer[:-2]
			break

	print 'Received: %r' % buffer
	return buffer

def fetchData(command, prefix, lz = False):
	if not power.is_on(): return
	result = send_receive(command)
	if not result : return
	values = result.split('\r')
	print values
	for i in values:
		idx = values.index(i)
		# BGL: ['06/01/11', '30/06/04', '22749', '24069', '9857', '06/01/11 5', '04/04/10 1979']
		if idx == 5 and command == "BGL":
			splitted = string.rsplit(i, " ", 1)
			data[prefix+str(6)]=splitted[0]
			data[prefix+str(5)]=splitted[1]
		elif idx == 6 and command == "BGL":
			splitted = string.rsplit(i, " ", 1)
			data[prefix+str(8)]=splitted[0]
			data[prefix+str(7)]=splitted[1]
		elif idx == 4 and lz:
			splitted = string.rsplit(i, " ", 1)
			data[prefix+str(5)]=splitted[0]
			data[prefix+str(4)]=splitted[1]
		elif idx == 5 and lz:
			splitted = string.rsplit(i, " ", 1)
			data[prefix+str(7)]=splitted[0]
			data[prefix+str(6)]=splitted[1]
		else:
			data[prefix+str(idx)]=i

def signal_handler(signal, frame):
	print '\nShutting down...'
	global running
	running = False
	# trigger HTTP server shutdown
	try:
		urllib.urlopen("http://127.0.0.1:"+str(port))
	except:
		pass
	time.sleep(2)
	client_socket.close()
	sys.exit(0)

def threadSleep(u):
	t = 0
	while (t < u and running):
		t += 1
		time.sleep(1)

class Power:
	state = False
	activity = False
	def on(self):
		self.state = True
		data["powerstate"] = "Wechselrichter ist eingeschaltet"
	def off(self):
		self.state = False
		data["powerstate"] = "Wechselrichter ist ausgeschaltet, angezeigte Daten sind nicht aktuell!"
	def is_on(self):
		return self.state
	def resetActivity(self):
		self.activity = False
	def logActivity(self):
		self.activity = True
	def hasActivity(self):
		return self.activity
	def __init__(self):
		self.off()
		self.resetActivity()

class IstWerte:
	# upv_ist, upv_soll, uac_netz, iac_netz, pac_netz, fac_netz, r_iso, t_kk
	def update(self):
		fetchData("I","ist")
		if not ("ist4" in data): return
		if data["ist4"] != "0.00":
			power.logActivity()

	def write_rrd(self):
		if not "ist4" in data: return
		v = "N:"+str(data["ist4"])
		os.system("rrdtool update "+path+"istwerte.rrd " + v)
		#print "rrdtool update istwerte.rrd " + v

	def write_db(self):
		if "ist0" in data:
			istdb = sqlite3.connect(path+'istwerte.sq3')
			istc = istdb.cursor()
			istc.execute("""insert into istwerte values (?,?,?,?,?,?,?,?,?)""", \
			(time.time(),data["ist0"],data["ist1"],data["ist2"],data["ist3"],		\
			data["ist4"],data["ist5"],data["ist6"],data["ist7"]))
			istdb.commit()
			istc.close()

class LangzeitWerte:
	def update(self):
		fetchData("BTL","today", True)
		fetchData("BTV","yesterday", True)
		fetchData("BWL","thisweek", True)
		fetchData("BWV","lastweek", True)
		fetchData("BML","thismonth", True)
		fetchData("BMV","lastmonth", True)
		fetchData("BGL","total")

	def write_db(self):
		lzdb = sqlite3.connect(path+'lzwerte.sq3')
		lzc = lzdb.cursor()
		if "yesterday0" in data:
			splitted = string.split(data["yesterday0"], "/")
			lzc.execute('select * from tage where tag=? and monat=? and jahr=?', (splitted[0],splitted[1],splitted[2]))
			if not lzc.fetchone():
				lzc.execute("""insert into tage values (?,?,?,?,?,?,?,?,?,?)""", \
				(splitted[0],splitted[1],splitted[2],data["yesterday1"], \
				data["yesterday2"],data["yesterday3"],data["yesterday4"], \
				data["yesterday5"],data["yesterday6"],data["yesterday7"]))
				lzdb.commit()
		if "lastweek0" in data:
			splitted = string.split(data["lastweek0"], "/")
			lzc.execute('select * from wochen where woche=? and jahr=?', (splitted[0],splitted[1]))
			if not lzc.fetchone():
				lzc.execute("""insert into wochen values (?,?,?,?,?,?,?,?,?)""", \
				(splitted[0],splitted[1],data["lastweek1"], \
				data["lastweek2"],data["lastweek3"],data["lastweek4"], \
				data["lastweek5"],data["lastweek6"],data["lastweek7"]))
				lzdb.commit()
		if "lastmonth0" in data:
			splitted = string.split(data["lastmonth0"], "/")
			lzc.execute('select * from monate where monat=? and jahr=?', (splitted[0],splitted[1]))
			if not lzc.fetchone():
				lzc.execute("""insert into monate values (?,?,?,?,?,?,?,?,?)""", \
				(splitted[0],splitted[1],data["lastmonth1"], \
				data["lastmonth2"],data["lastmonth3"],data["lastmonth4"], \
				data["lastmonth5"],data["lastmonth6"],data["lastmonth7"]))
				lzdb.commit()
		lzc.close()

		return

class FirmwareVersion:
	def update(self):
		fetchData("V", "fw")

class ZeitStempel:
	def update(self):
		fetchData("ZL", "zeit")

class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		global path
		if self.path == "/" or self.path == "/istw":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(ist_template.safe_substitute(data))
		elif self.path == "/" or self.path == "/lzw":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(lzw_template.safe_substitute(data))
		elif self.path == "/istd":
			self.send_response(200)
			self.end_headers()
			os.system(path+"draw_graphs.sh")
			self.wfile.write(istd_template)
		elif self.path.startswith("/lzd"):
			self.send_response(200)
			self.end_headers()
			parsed_path = urlparse.urlparse(self.path)
			try:
				params = dict([p.split('=') for p in parsed_path[4].split('&')])
			except:
				params = {}
			try:
				x = int(params["month"])
				y = int(params["year"])
			except:
				params["month"] = time.strftime("%m")
				params["year"] = time.strftime("%y")
			if params["month"] == "0":
				print "gen graph for year " + str(params["year"])
				R.stdin.write(lzd_year_r.safe_substitute(params))
			else:
				print "generating graph for " + str(params["month"]) + " / " + str(params["year"])
				R.stdin.write(lzd_month_r.safe_substitute(params))
			threadSleep(2)
			self.wfile.write(lzd_template.safe_substitute(params))
		elif self.path.endswith(".png"):
			f = open(path+self.path.strip('/'), 'r')
			self.wfile.write(f.read())
			f.close()
		else:
			self.send_response(404)

class CheckPowerStateThread(threading.Thread):
	def run(self):
		while(running):
			if power.is_on():
				if power.hasActivity():
					# still generating power, check again in 10min
					power.resetActivity()
					threadSleep(600)
				else:
					print "No power generated in the past 10min, waiting for PV-WR to shut down."
					# let the PVWR go to sleep
					# sleeps after about 5min, but to be sure wait 10
					power.off()
					threadSleep(600)
					if not send_receive('V'):
						print "PV-WR has shut down at " + time.ctime()
					else:
						print "PV-WR did not shut down or is back on. Checking again in 10min."
						power.on()
						# allow some time to log power activity
						threadSleep(600)
			else:
				if send_receive('V'):
					power.on()
					print "PV-WR has powered on at " + time.ctime()
					# check again in 10min
					threadSleep(600)
				else:
					# check again in 1 min
					print "PV-WR is off, checking again in 1min."
					threadSleep(60)

class WriteRRDThread(threading.Thread):
	def run(self):
		while (running):
			if power.is_on():
				istwerte.write_rrd()
				threadSleep(30)
			else:
				time.sleep(1)

class WriteDBThread(threading.Thread):
	def run(self):
		i = 6
		while (running):
			if power.is_on():
				print "WriteDBThread"
				istwerte.write_db()
				# every hour
				if (i % 6 == 0):
					lzwerte.write_db()
				threadSleep(600)
				i += 1
			else:
				time.sleep(1)

class ReadSerialThread(threading.Thread):
	def run(self):
		i = 100
		while(running):
			#print "ReadSerialThread"
			if power.is_on():
				istwerte.update()
				zeit.update()
				if (i % 100 == 0):
					firmware.update()
					lzwerte.update()
				i += 1
			else:
				time.sleep(1)

class WebServerThread(threading.Thread):
	def run(self):
		server = BaseHTTPServer.HTTPServer(('', port), HTTPHandler)
		print 'started webserver on port ' + str(port)
		while(running):
			server.handle_request()
		server.socket.close()

## MAIN

running = True
port = 8000
data = dict()
path = os.path.dirname(os.path.realpath(__file__)) + "/"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(2)
client_socket.connect((sys.argv[1], 4001))

signal.signal(signal.SIGINT, signal_handler)
power = Power()

CheckPowerStateThread(name="CheckPowerStateThread").start()

f = open(path+'istwerte.html', 'r')
ist_template = string.Template(f.read())
f.close()
f = open(path+'istgraph.html', 'r')
istd_template = f.read()
f.close()
f = open(path+'lzwerte.html', 'r')
lzw_template = string.Template(f.read())
f.close()
f = open(path+'lzgraph.html', 'r')
lzd_template = string.Template(f.read())
f.close()
f = open(path+'lzgraph_month.r', 'r')
lzd_month_r = string.Template(f.read())
f.close()
f = open(path+'lzgraph_year.r', 'r')
lzd_year_r = string.Template(f.read())
f.close()

istwerte = IstWerte()
firmware = FirmwareVersion()
zeit = ZeitStempel()
lzwerte = LangzeitWerte()

# start R and open SQLite db
devnull = open('/dev/null', 'w')
R = subprocess.Popen(['R','--vanilla'], stdin=subprocess.PIPE, stdout=devnull)
R.stdin.write("library(DBI); library(RSQLite); driver<-dbDriver(\"SQLite\");\
PATH<-\""+path+"\";connect<-dbConnect(driver, dbname = \""+path+"lzwerte.sq3\")\n")

ReadSerialThread(name="ReadSerialThread").start()
WebServerThread(name="WebServerThread").start()
# wait a while to read the first values
time.sleep(40)
WriteRRDThread(name="WriteRRDThread").start()
WriteDBThread(name="WriteDBThread").start()

while 1:
	time.sleep(1)
