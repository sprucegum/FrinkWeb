'''
Copyright (C) 2012  Jade Lacosse
 This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

## Dr. Frinks Server Controller
## Usage:
## 	Easy Way
## 		python kagserv.py
##	Interactive way
##		python
##		>> from kagserv import *
##
## Please send any significant changes to sprucegum@gmail.com

from subprocess import Popen, PIPE, call
from time import time
from datetime import datetime
from threading import Timer
from os import getcwd, walk
from sys import exit, path
from signal import signal, SIGINT
from random import randint
from shutil import copy

## SET THIS ON INSTALL
KAG_DIR = '/home/frink/kag-linux32-dedicated/'

path.append('frinkweb')

from frinkweb.logparser import *
from frinkweb.serverstate import *
## Settings:

MEMLIMIT = 200 		# megabytes, restart the server even if occupied if it hits this RAM limit.
RESTART_PERIOD = 20 	# minutes, minimum time between restarts 
POLL_PERIOD = 10	# seconds, how often to see how many people are playing, perform logic.
UPDATE_PERIOD = 30	# minutes, how often to check for updates.
STATS_PERIOD = 1	# minutes, how often to update stats.

class KagServer(object):
	def __init__(self):
		self.ss = ServerState()
		self.sPID = self.getPID()
		if (self.sPID == -1):
			self.KAG = self.start_server()
		else:
			self.KAG = self.attach_server()
		self.run_manager = True
		self.timer = None
		
		self.dblock = False
		self.last_stats_update = time()

	def get_players(self):
		with open('{0}Logs/stats.txt'.format(KAG_DIR),'r') as stats:
			return int(stats.read().split()[3])

	def start_server(self):
		self.ss.start_time = time()
		self.run_manager = True
		self.fresh = True
		self.ss.logposition = 0
		self.ss.days = 0
		self.last_update_check = time()
		self.last_stats_update = time()
		
		return Popen(['{0}KAGdedi'.format(KAG_DIR), \
		'{0}autostart Scripts/dedicated_autostart.gm '.format(KAG_DIR),\
		'{0}autoconfig Scripts/dedicated_autoconfig.gm'.format(KAG_DIR)])

	def attach_server(self):
		self.ss.start_time = time() - RESTART_PERIOD*60
		self.run_manager = True
		self.fresh = False 
		self.last_update_check = time() - UPDATE_PERIOD*60
		return ProxyProcess(self.sPID)
		
	def rotate_map(self):
		maps = []
		for root, dirs, files in walk('{0}Base/Maps/Cycle/'.format(KAG_DIR)):
			maps.append([root,dirs,files])
			
		folderk = randint(1,len(maps)-1)
		mapk = randint(0,len(maps[folderk][2])-1)
		mapstring = maps[folderk][0] + '/' + maps[folderk][2][mapk]
		print 'Current motd: {0}'.format(mapstring)
		copy(mapstring,'{0}Base/Maps/motd.png'.format(KAG_DIR))
		
			

	def getPID(self):
		try:
			return int(Popen(["ps","-C","KAGdedi","-o","pid"],stdout=PIPE).stdout.read().split()[1])
		except:
			return -1

	def kill_server(self):	
		self.timer.cancel()
		self.run_manager = False
		self.KAG.terminate()
	
	def restart_server(self):
		self.rotate_map()
		self.ss.restarts += 1
		lp = self.parse_live()
		if lp:
			lp.close_livelog()
			lp = None
		self.kill_server()
		self.KAG = self.start_server()
		
	
	def parse_old(self):
		lp = LogParser()
		lp.parse_logs()
		lp.update_database()
		lp = None

	def parse_live(self):
		if not self.dblock:
			print("updating database")
			self.dblock = True
			lp = LogParser(self.ss)
			self.last_stats_update = time()
			lp.parse_livelog()
			print("processing database")
			lp.process_database()
			print("database processed")
			print("logposition:{0}".format(self.ss.logposition))
			self.dblock = False
			return lp
		return None
	

	def get_uptime(self):
		return (time() - self.ss.start_time)

	def running(self):
		self.KAG.poll()
		return (self.KAG.returncode is None)
	
	def get_mem(self):
		ps = Popen(['ps','vh','-p', '{0}'.format(self.KAG.pid)],stdout=PIPE)
		return int(ps.stdout.read().split()[6])

	def manager(self,restart_period = 60*RESTART_PERIOD, poll_period = POLL_PERIOD, memory_limit = MEMLIMIT*1024):
			if self.run_manager:			
				t = Timer(poll_period, self.manager)
				t.start()
				players = self.get_players()
				#print("Players:{0}".format(players))
				if not self.running():
					self.KAG = self.start_server()
				
				elif (self.get_mem()> memory_limit):
					self.ss.memrestarts += 1
					self.restart_server()
				elif ((players > 0) and self.fresh):
					self.fresh = False
				elif ((players == 0) and not self.fresh):
					if ((time() - self.ss.start_time)>restart_period):
						print("Restarting server after {0} hours gameplay".format(self.get_uptime()/3600.0))
						self.restart_server()
				elif (((time() - self.last_update_check)/60) > UPDATE_PERIOD*60):
					if (players == 0):
						print("Checking for Update")
						if self.check_update():
							self.ss.updates += 1
							self.restart_server()
							
				if (((time() - self.last_stats_update)>(STATS_PERIOD*60)) and (players>0)):
					self.parse_live()

					
						

	def state(self):
		print("Players:{0} Uptime:{1:.2}h Mem:{2:.2}m Restarts:{3}".format(\
			self.get_players(),\
			self.get_uptime()/3600,\
			self.get_mem()/1024.0,\
			self.ss.restarts))	

	def check_update(self):
		self.last_update_check = time()
		with open('{0}App/version.txt'.format(KAG_DIR)) as this_version_file:
			this_version = this_version_file.readline().split()[1]
		call(['wget','-q','-N','http://update.kag2d.com/kag_linux/App/version.txt'])
		with open('version.txt') as current_version_file:
			current_version = current_version_file.readline().split()[1]
		return (current_version != this_version)

	def ctrlc(self, signum,frame):
		self.run_manager = False
		self.timer.cancel()
		print("exiting")
		exit()	
	
class ProxyProcess(object):
	def __init__(self, PID):
		self.pid = PID
		self.returncode = None

	def poll(self):
		try:
			self.pid = int(Popen(["ps","-C","KAGdedi","-o","pid"],stdout=PIPE).stdout.read().split()[1])
			return None
		except:
			return 0

	def terminate(self):
		call(['kill',str(self.pid)])

## Autostart

K = KagServer()
K.timer = Timer(30,K.manager)
K.timer.start()
signal(SIGINT, K.ctrlc)


