import json
from sys import path
path.append('../')
from settings import KAG_DIR
class BlackList(object):
	def __init__(self):
		banfile = open(KAG_DIR + '/Base/Security/blacklist.cfg')
		bf = banfile.readlines()
		liststart = bf.index('blacklist =\n')
		self.bantext = [line.strip() for line in bf[(liststart+1):]]
		self.playerlist = []
		
		
	def blacklist(self, name='none', ip='0.0.0.0'):
		for player in self.bantext:
			p = player.split(';')
			if name is 'none':
				if ip is '0.0.0.0':
					self.listadd(p)
				else:
					if p[1].count(ip):
						self.listadd(p)
			else:
				if p[0].count(name):
					self.listadd(p)
		
		return json.dumps(self.playerlist)
	
	def listadd(self,p):
		self.playerlist.append({'u':p[0].strip(),'ip':p[1].strip(),'l':p[2].strip()})
				
