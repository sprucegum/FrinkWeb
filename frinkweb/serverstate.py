from stats.models import *
from datetime import datetime
from time import time
import pickle

class ServerState(object):
		errorstate = False
		players = 0
		logposition = 0
		clogposition = 0
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
		openlives = {}
		opensessions = {}
		livesleft = True
		matchover = False
		last_time = None
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
			pset = []
			for pname in self.opensessions.keys():
				pset.append(self.get_player(pname))
			return pset
		
		def pcount(self):
			return len(self.opensessions)

		def server_restart(self):
			self.end_match(self.last_time)

		# Some Processing code.
		def start_match(self,dtime):
			self.last_time = dtime
			self.matchover = False
			for sesh in self.opensessions.keys():
				self.add_life(sesh.player.name,dtime)

		def end_match(self,dtime):
			self.last_time = dtime
			for pname in self.openlives.keys():
				self.end_life(pname,dtime)
			self.matchover = True

		def create_play_session(self,pname,ptime):
			self.last_time = ptime
			pname = pname.decode('utf-8','ignore')
			p = self.get_player(pname)
			s = Session(player = p, start = ptime, end = ptime)
			s.save()
			self.opensessions[p.name] = s
			self.add_life(p.name,ptime)
			return p


		def close_play_session(self,pname,ptime):
			self.last_time = ptime
			pname = pname.decode('utf-8','ignore')
			p = self.get_player(pname)
			s =  self.opensessions[p.name]
			del self.opensessions[p.name]
			if self.openlives[p.name]:
				self.end_life(p.name,ptime)
			s.end = ptime
			s.save()

		def add_life(self,pname,atime):
			self.last_time = atime
			pname = pname.decode('utf-8','ignore')
			p = self.get_player(pname)
			life = Life(player = p, start=atime, end=atime)
			life.save()
			self.openlives[p.name] = life

		def end_life(self,pname,etime):
			self.last_time = etime
			if not self.matchover:
				pname = pname.decode('utf-8','ignore')
				p = self.get_player(pname)
				life = self.openlives[p.name]
				life.end = etime
				life.save()
				del self.openlives[p.name]
				if self.livesleft:
					self.add_life(p.name,etime)

		def get_player(self,pname):
			pname = pname.decode('utf-8','ignore')
			if pname in self.players:
				return self.players[pname]
			else:
				for pkey in sorted(filter(lambda x: len(x)<len(pname),self.players.keys()),cmp=lambda x,y:cmp(len(y),len(x))):
					if pname.count(pkey):
						self.players[pname] = self.players[pkey]
						return self.players[pkey]
				try:
					p = Player.objects.get(name=pname)
					self.players[pname] = p
					return p
				except:
					try:
						p = Player.objects.get(printedname=pname)
						self.players[pname] = p
						return p
					except:
						p = Player(name=pname,clan=self.get_clan('NoClan'))
						p.save()
						self.players[pname] = p

						return p

		def get_clan(self,cname):
			if cname.decode('utf-8','ignore') in self.clans:
				return self.clans[cname.decode('utf-8','ignore')]
			else:
				c, g = Clan.objects.get_or_create(name=cname.decode('utf-8','ignore'))
				self.clans[cname.decode('utf-8','ignore')] = c
				return c

		def get_weapon(self,wname):
			if wname in self.weapons:
				return self.weapons[wname]
			else:
				w, g = Weapon.objects.get_or_create(name = wname)
				self.weapons[wname] = w
				return w

		def get_cause(self,cname):
			if cname in self.causes:
				return self.causes[cname]
			else:
				c, created = Cause.objects.get_or_create(name = cname)
				self.causes[cname] = c
				return c
