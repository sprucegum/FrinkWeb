from stats.models import *
from datetime import datetime
from time import time
import pickle

class ServerState(object):
		errorstate = False
		players = 0
		logposition = 0
		restarts = 0
		memrestarts = 0
		updates = 0
		days = 0
		lasthour = 0
		runtime = 0
		memusage = 0
		current_map = ""
		start_time = None
		players = {}
		clans = {}
		weapons = {}
		causes = {}
		def __init__(self):
			self.birth = datetime.now()
			
		def save(self, fpath = './serverstate.pickle'):
			fobject = file(fpath,'wb')
			return pickle.dump(self,fobject)
			
		@classmethod
		def load(cls, fpath = './serverstate.pickle'):
			fobject = file(fpath,'rb')
			return pickle.load(fobject)
			
		def pset(self):
			pset = set()
			for pname,player in self.players.iteritems():
				 pset.add(player)
			return pset
