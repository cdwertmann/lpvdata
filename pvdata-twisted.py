#!/usr/bin/python

# Read data from SMA PV-WR 1500/1800 solar energy inverter
# implementation for serial port <-> TCP converter box using python twisted
# (c) 2013 Christoph Dwertmann

from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.web import server, resource
from twisted.internet import reactor, task
from sys import stdout
import os, random, time, threading, signal, sys
import urllib, urlparse, string, sqlite3, subprocess
import socket, time
import logging

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

class PVWRSite(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)
		f = open(path+'istwerte.html', 'r')
		self.ist_template = string.Template(f.read())
		f.close()
		f = open(path+'istgraph.html', 'r')
		self.istd_template = f.read()
		f.close()
		f = open(path+'lzwerte.html', 'r')
		self.lzw_template = string.Template(f.read())
		f.close()
		f = open(path+'lzgraph.html', 'r')
		self.lzd_template = string.Template(f.read())
		f.close()
		f = open(path+'lzgraph_month.r', 'r')
		self.lzd_month_r = string.Template(f.read())
		f.close()
		f = open(path+'lzgraph_year.r', 'r')
		self.lzd_year_r = string.Template(f.read())
		f.close()
	def getChild(self, name, request):
		return self
	def render_GET(self, request):
		global path
		p=request.prepath[0]
		if p == 'favicon.ico':
			return ''
		elif p == 'lzw':
			return self.lzw_template.safe_substitute(data)
		elif p == 'istd':
			os.system(path+"draw_graphs.sh")
			return self.istd_template
		elif p == 'lzd':
			params=request.args
			for key in params:
				params[key] = int(params[key][0])
			if not "month" in params: params["month"] = time.strftime("%m")
			if not "year" in params: params["year"] = time.strftime("%y")
			if params["month"] == 0:
				logging.info("generating graph for year %s" % params["year"])
				R.stdin.write(self.lzd_year_r.safe_substitute(params))
			else:
				logging.info("generating graph for %s / %s" % (params["month"],params["year"]))
				R.stdin.write(self.lzd_month_r.safe_substitute(params))
			time.sleep(2)
			return self.lzd_template.safe_substitute(params)
		elif request.path.endswith(".png"):
			f = open(path+request.path, 'r')
			png = f.read()
			f.close()
			return png
		else:
			return self.ist_template.safe_substitute(data)

class PVWR(Protocol):
	LONGTERM = ['BTL', 'BTV', 'BWL', 'BWV', 'BML', 'BMV', 'BGL', 'V']
	
	def __init__(self):
		logging.info('INIT')
		self.lastcmd=""
		self.sendbuf=""
		self.recvbuf=""
		self.counter=10
		self.power_generated=False
		self.polling=True
		self.last_received=0
		self.silence_period = 600
		self.lc_periodic_send = task.LoopingCall(self.periodic_send)
		self.lc_write_ist_rrd = task.LoopingCall(self.write_ist_rrd)
		self.lc_write_ist_db = task.LoopingCall(self.write_ist_db)
		self.lc_write_lz_db = task.LoopingCall(self.write_lz_db)
		self.lc_sleep_check = task.LoopingCall(self.sleep_check)
		self.lc_periodic_send.start(3,False)
		self.lc_sleep_check.start(self.silence_period,False)
	
	def dataReceived(self, recvdata):
		self.last_received=int(time.time())
		#logging.info('Received: %r' % recvdata)
		if (self.sendbuf==""):
			self.recvbuf+=recvdata
			if self.recvbuf.endswith('\r\n'):
				self.recvbuf=self.recvbuf[:-2]
				while self.recvbuf[:1]=='\r':
					self.recvbuf=self.recvbuf[1:]
				logging.info('Received: %r | Last cmd: %r' % (self.recvbuf, self.lastcmd))
				values = self.recvbuf.split('\r')
				self.recvbuf=''
				lz=False
				prefix=''
				if (self.lastcmd=='I'):
					prefix='ist'
					logging.info(values[4]+" kW")
					if float(values[4]) > 0.01:
						self.power_generated=True
                                        if float(values[4]) > 2:
						logging.error("invalid value: " + values[4])
                                                logging.error(recvdata)
                                                logging.error(str(values))
				elif (self.lastcmd=='ZL'):
					prefix='zeit'
				elif (self.lastcmd=='V'):
					prefix='fw'
				elif (self.lastcmd=='ZL'):
					prefix='zeit'
				elif (self.lastcmd=='BTL'):
					prefix='today'
					lz=True
				elif (self.lastcmd=='BTV'):
					prefix='yesterday'
					lz=True
				elif (self.lastcmd=='BWL'):
					prefix='thisweek'
					lz=True
				elif (self.lastcmd=='BWV'):
					prefix='lastweek'
					lz=True
				elif (self.lastcmd=='BML'):
					prefix='thismonth'
					lz=True
				elif (self.lastcmd=='BMV'):
					prefix='lastmonth'
					lz=True
				elif (self.lastcmd=='BGL'):
					prefix='total'
				
				logging.info(values)
				for i in values:
					idx = values.index(i)
					# BGL: ['06/01/11', '30/06/04', '22749', '24069', '9857', '06/01/11 5', '04/04/10 1979']
					splitted = string.rsplit(i, " ", 1)
					if idx == 5 and self.lastcmd == "BGL":
						data[prefix+str(6)]=splitted[0]
						data[prefix+str(5)]=splitted[1]
					elif idx == 6 and self.lastcmd == "BGL":
						data[prefix+str(8)]=splitted[0]
						data[prefix+str(7)]=splitted[1]
					elif idx == 4 and lz:
						data[prefix+str(5)]=splitted[0]
						data[prefix+str(4)]=splitted[1]
					elif idx == 5 and lz:
						data[prefix+str(7)]=splitted[0]
						data[prefix+str(6)]=splitted[1]
					else:
						data[prefix+str(idx)]=i

	def connectionMade(self):
		pass
		#if not self.lc_periodic_send.running: self.lc_periodic_send.start(3,False)
		#if not self.lc_sleep_check.running: self.lc_sleep_check.start(self.silence_period,False)

	def suspend_db_write(self):
		if self.lc_write_ist_rrd.running: self.lc_write_ist_rrd.stop()
		if self.lc_write_ist_db.running: self.lc_write_ist_db.stop()
		if self.lc_write_lz_db.running: self.lc_write_lz_db.stop()

	def resume_db_write(self):
		if not self.lc_write_ist_rrd.running: self.lc_write_ist_rrd.start(30,False)
		if not self.lc_write_ist_db.running: self.lc_write_ist_db.start(600,False)
		if not self.lc_write_lz_db.running: self.lc_write_lz_db.start(3600,False)

	def periodic_send(self):
		# don't queue a new command if the previous one hasn't been sent
		if self.sendbuf!="":
			self.send()
			return
                if self.polling == False: return
		if (self.counter == -1):
			self.counter=100
		elif (self.counter < len(self.LONGTERM)):
			self.send_queue(self.LONGTERM[self.counter])
		elif (self.counter % 2 == 0):
			self.send_queue('I')
		else:
			self.send_queue('ZL')
		self.counter-=1
		self.send()

	def send_queue(self, cmd):
		self.lastcmd=cmd
		self.sendbuf=cmd+'\r'

	def send(self):
		cmd=self.sendbuf[:1]
		self.sendbuf=self.sendbuf[1:]
		logging.info('Sending: %r' % cmd)
		self.transport.write(cmd)
		if self.last_received < int(time.time())-5:
			data["powerstate"] = "Wechselrichter ist ausgeschaltet"
		else:
			data["powerstate"] = "Wechselrichter ist eingeschaltet, Daten werden empfangen"

	def write_ist_rrd(self):
		if not "ist4" in data: return
		v = "N:"+str(data["ist4"])
		os.system("rrdtool update "+path+"istwerte.rrd " + v)
		#logging.info("rrdtool update istwerte.rrd " + v)

	def write_ist_db(self):
		if not "ist0" in data: return
		istdb = sqlite3.connect(path+'istwerte.sq3')
		istc = istdb.cursor()
		istc.execute("""insert into istwerte values (?,?,?,?,?,?,?,?,?)""",\
		(time.time(),data["ist0"],data["ist1"],data["ist2"],data["ist3"],\
		data["ist4"],data["ist5"],data["ist6"],data["ist7"]))
		istdb.commit()
		istc.close()

	def write_lz_db(self):
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

	def sleep_check(self):
		if self.power_generated:
			# generating power, check again later
			logging.info("PV-WR is on and power was generated. Checking again in %ss." % (self.silence_period))
			self.power_generated=False
			self.resume_db_write()
		else:
			if self.polling:
				# let the PVWR go to sleep
				# sleeps after about 5min, but to be sure wait 10
				logging.info("No power generated in the past %ss, stopping contact for %ss for PV-WR to shut down." % (self.silence_period,self.silence_period))
				self.suspend_db_write()
				self.polling = False
				# flush the receive queue
				time.sleep(5)
				data["powerstate"] = "Keine Energieerzeugung, warte auf Abschaltung. Messwerte evtl. nicht aktuell."
			else:
				logging.info("Starting to contact PV-WR after silence period of %ss." % (self.silence_period))
				data["powerstate"] = "Pruefung ob der Wechselrichter eingeschaltet ist. Messwerte evtl. nicht aktuell."
				self.polling = True

class PVWRClientFactory(ReconnectingClientFactory):
	maxDelay = 10
	initialDelay = 1
	
	def startedConnecting(self, connector):
		logging.info('Started to connect.')
	
	def buildProtocol(self, addr):
		logging.info('Connected.')
		logging.info('Resetting reconnection delay')
		self.resetDelay()
		return pvwr
	
	def clientConnectionLost(self, connector, reason):
		logging.info('Lost connection.	 Reason: %s' % reason)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
	
	def clientConnectionFailed(self, connector, reason):
		logging.info('Connection failed. Reason: %s' % reason)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

port = 8000
data = dict()
path = os.path.dirname(os.path.realpath(__file__)) + "/"
data["powerstate"] = "Initialisierung..."
pvwr = PVWR()

# start R and open SQLite db
devnull = open('/dev/null', 'w')
R = subprocess.Popen(['R','--vanilla'], stdin=subprocess.PIPE, stdout=devnull)
R.stdin.write("library(DBI); library(RSQLite); driver<-dbDriver(\"SQLite\");\
PATH<-\""+path+"\";connect<-dbConnect(driver, dbname = \""+path+"lzwerte.sq3\")\n")

reactor.connectTCP(sys.argv[1], 4001, PVWRClientFactory())
site = server.Site(PVWRSite())
reactor.listenTCP(port, site)
reactor.run()
