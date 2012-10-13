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
		
		def pcount(self):
			return len(self.opensessions)


        # Some Processing code.

        def create_play_session(self,pname,ptime):
            p = self.get_player(pname)
            s = Session(player = p, start = ptime, end = ptime)
            s.save()
            self.opensessions[p.name] = s

        def close_play_session(self,pname,ptime):
            p = self.get_player(pname)
            s = self.pop_session(p.name)
            s.end = ptime
            s.save()

        def add_life(self,pname,kill,time):
            if pname in self.openlives:
                life = self.openlives[pname]
                life.kill_set.add(kill)
                life.save()
            else:
                p = self.players[pname]
                life = Life(player = p, start = datetime.now())

        def end_life(self,pname,time):
            life = self.openlives[pname]
            life.kill_set.add(kill)
            life.save()

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
                        if self.livelog:
                            self.get_avatar(p)
                        return p
                    except:
                        p = Player(name=pname,clan=self.get_clan('NoClan'))
                        p.save()
                        self.players[pname] = p
                        if self.livelog:
                            self.get_avatar(p)
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
