'''
FrinkStats Log Parser Utility 
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

from os import chdir, getcwd, mkdir, walk, remove, environ
environ['DJANGO_SETTINGS_MODULE'] = "settings"

from shutil import move
import re
import settings
from stats.models import *
from datetime import datetime, timedelta
from serverstate import *
import json
import urllib2

KAG_DIR = '/home/frink/kag-linux32-dedicated/'
KAG_API = "api.kag2d.com"

PRINT_DEBUG = False

class LogParser(object):
	def __init__(self, ss = ServerState()):	
		self.ss = ss
		self.freshlog = True
		self.livelog = None

		
	def parse_logs(self):
		self.first_run()
		
		chats = self.get_logs()			
		# Grab all the log files
		# call parse log on each log file
		# call move log on each parsed log
		for chat in chats[:-1]:
			print(chat)
			self.set_day(chat)
			logfile = open(KAG_DIR +'Logs/'+chat)
			log = logfile.readlines()
			self.ss.lasthour = 0
			self.ss.days = 0
			self.unparsed = self.parse_log(log)
			self.move_log(logfile,chat)
			
		self.process_database()

	def set_day(self,chat):
		datearr = re.match('chat-([0-9]{2}-[0-9]{2}-[0-9]{2}).*',chat).groups()[0].split('-')
		self.year = '20{0}'.format(datearr[0])
		self.month = datearr[1]
		self.day = datearr[2]

	def process_database(self):
		self.calculate_kds()
		self.count_clanmembers()
		if not self.livelog:
			self.get_avatars()
			self.get_golds()

	def get_logs(self):
		#logfile = open('chat-12-08-06-06-18-10.txt','r')
		#logfile = open('chat-12-08-06-19-31-02.txt','r')
		#log = logfile.readlines()
		chats = filter(lambda line:line.count("chat"),walk(KAG_DIR + 'Logs').next()[2])
		chats.sort()
		return (chats)

	def parse_livelog(self):
		if self.livelog is None:
			self.livelogname = self.get_logs()[-1]
			self.livelog = open(KAG_DIR + 'Logs/' + self.livelogname)
			self.set_day(self.livelogname)
		new_events = self.livelog.readlines()[self.ss.logposition:]
		self.parse_log(new_events)
		self.process_database()
		self.ss.logposition = self.ss.logposition+len(new_events)
		


	def close_livelog(self):
		self.move_log(self.livelog,self.livelogname)

	def parse_log(self, log):
		# Read through a log
		unparsed = []
		for line in log:
			
			line = self.get_players([line])
			if line:
				line = self.get_chats(line)
			if line:
				line = self.get_kills(line)
			if line:
				line = self.get_accidents(line)
			if line:
				unparsed.append(line[0])
		return unparsed

	def move_log(self, logfile, chat):
		logfile.close()
		move(KAG_DIR + '''Logs/{0}'''.format(chat), KAG_DIR + '''Parsed/{0}'''.format(chat))
	
	def get_chats(self,loglines):
		chats = []
		otherlines = []
		for line in loglines:
			if re.search('^\[.*\] <.*>.*\n',line):
				chats.append(line)
			else:
				otherlines.append(line)
		self.add_chats(chats)
		return otherlines
	

	def get_kills(self,loglines):
		# check for each type of kill
		# hammer, sword, arrow, rocks, bomb, spikes, push
		# kill = [time, killer, killed, weapon]
		kills = []
		otherlines = []
		for line in loglines:
			try:
				if re.search('^\[.*\] .* slew .*',line):
					killer = re.split('slew',line)[0].split()[-1]
					victim = re.split('with',re.split('slew',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'sword'])
			
				elif re.search('^\[.*\] .* shot .*',line):
					killer = re.split('shot',line)[0].split()[-1]
					victim = re.split('with',re.split('shot',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'bow'])
			
				elif re.search('^\[.*\] .* pushed .* to',line):
					killer = re.split('pushed',line)[0].split()[-1]
					victim = re.split('to (his|her)',re.split('pushed',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'foot'])
			
				elif re.search('^\[.*\] .* pushed .* on',line):
					killer = re.split('pushed',line)[0].split()[-1]
					victim = re.split('on a',re.split('pushed',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'spikes'])
			
				elif re.search('''^\[.*\] .* gibbed \S+\s?\S* into pieces''',line):
					killer = re.split('gibbed',line)[0].split()[-1]
					victim = re.split('into pieces',re.split('gibbed',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'bomb'])
			
				elif re.search('^\[.*\] .* hammered .*',line):
					killer = re.split('hammered',line)[0].split()[-1]
					victim = re.split('to death',re.split('hammered',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'hammer'])
				
				elif re.search('^\[.*\] .* assisted in squashing .* ',line):
					killer = re.split('assisted',line)[0].split()[-1]
					victim = re.split('under a',re.split('assisted',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'collapse'])
				elif re.search('^\[.*\] .* assisted in .* dying under',line):
					killer = re.split('assisted',line)[0].split()[-1]
					victim = re.split('dying under',re.split('assisted',line)[1])[0].strip().split()[-1]
					ktime = self.parse_time(line.split()[0])
					kills.append([ktime,killer,victim,'catapult'])

				else:
					otherlines.append(line)
			except:
				if PRINT_DEBUG: print "Bad Line:\n{0}".format(line)
		self.add_kills(kills)
		return otherlines

	def get_accidents(self,loglines):
		# [time, victim, cause of death]
		accidents = []
		otherlines = []
		# check for each type of accidental death
		# bomb, squash, rocks, falling, spikes
		# plus cyanide
		for line in loglines:
			if re.search('^\[.*\] .* fell to',line):
				victim = re.split('fell',line)[0].split()[-1]
				dtime = self.parse_time(line.split()[0])
				accidents.append([dtime,victim,'gravity'])
			elif re.search('^\[.*\] .* fell on',line):
				victim = re.split('fell',line)[0].split()[-1]
				dtime = self.parse_time(line.split()[0])
				accidents.append([dtime,victim,'spikes'])
			
			elif re.search('''^\[.*\] .* was squashed''',line):
				victim = re.split('was squashed',line)[0].split()[-1]
				dtime = self.parse_time(line.split()[0])
				accidents.append([dtime,victim,'collapse'])
			
			elif re.search('''^\[.*\] .* gibbed\s+into''',line):
				victim = re.split('gibbed',line)[0].split()[-1]
				dtime = self.parse_time(line.split()[0])
				accidents.append([dtime,victim,'bomb'])
			
			elif re.search('''^\[.*\] .* took some''',line):
				victim = re.split('took',line)[0].split()[-1]
				dtime = self.parse_time(line.split()[0])
				accidents.append([dtime,victim,'poison'])

			else:
				otherlines.append(line)
		self.add_accidents(accidents)
		return otherlines

	def get_players(self,loglines):
		players = []
		clans = []
		otherlines = []
		for line in loglines:
			try:
				if re.search('Unnamed player is now known as',line):
					players.append(re.split('Unnamed player is now known as',line.strip())[1].strip())
				elif re.search('is now known as',line):
					clan_nameline = re.split('is now known as',line.strip())
					playername = clan_nameline[0].split()[1].strip()
					printedname = clan_nameline[1].split()[-1].strip()
					clanname = re.split(re.escape(playername),clan_nameline[1])[0].strip()
					clans.append([playername,clanname,printedname])
				else:
					otherlines.append(line)
			except:
				print "Can't Parse '{0}'".format(line) 
				
		# See what players have played in this log, how long they played
		# how many disconnects
		# ping bans, kick bans, clan membership
		self.add_players(players)
		self.add_clans(clans)
		return otherlines

	def get_events(self,loglines):
		# get matches, team wins, map votes, greifer calls
		# collapses, admin presence, gold players, number of players
		return otherlines
	
	def parse_time(self,logtime):

		(hour, minute, second) = logtime.strip('[]').split(':')
		if int(hour) < self.ss.lasthour:
			self.ss.days += 1
			print "incrementing day. days:{0} hour:{1} lasthour:{2} logtime:{3}".format(self.ss.days, hour, self.ss.lasthour, logtime)
		self.ss.lasthour = int(hour)
		return (datetime(int(self.year),
					int(self.month), 
					int(self.day),
					int(hour),
					int(minute),
					int(second))+timedelta(days=self.ss.days))
	
	def add_kills(self,kills):
		
		if kills:
			if PRINT_DEBUG: print "\n{0:22}{1:20}{2:20}{3:20}".format('time','killer','victim','weapon')
			for kill in kills:

				if PRINT_DEBUG: print "{0[0]:22s}{0[1]:20}{0[2]:20}{0[3]:20}".format(kill)
				#p = Player.objects.get(printedname__exact=kill[1])
				p = self.get_player(kill[1])
				p.add_kill()

			
				#v = Player.objects.get(printedname__exact=kill[2])
				v = self.get_player(kill[2])					
				v.add_death()

				w = self.get_weapon(kill[3])					
				k = Kill(time=kill[0],player=p,victim=v,weapon=w)
				k.save()

				

	def add_accidents(self,accidents):
		if accidents:
			if PRINT_DEBUG: print "\n{0:22}{1:20}{2:20}".format("time","victim","cause")
			for accident in accidents:
				try:
					if PRINT_DEBUG: print "{0[0]:22s}{0[1]:20}{0[2]:20}".format(accident.decode('utf-8','ignore'))
					p = self.get_player(accident[1])
					p.add_death()
					
					c = self.get_cause(accident[2])
					a = Accident(player = p,time = accident[0],cause = c)
					a.save()
				except:
					if PRINT_DEBUG: print "bad accident"
					print accident
					
	def get_player(self,pname):
		pname = pname.decode('utf-8','ignore')
		if pname in self.ss.players:
			return self.ss.players[pname]
		else:
			for pkey in sorted(filter(lambda x: len(x)<len(pname),self.ss.players.keys()),cmp=lambda x,y:cmp(len(y),len(x))):
				if pname.count(pkey):
					self.ss.players[pname] = self.ss.players[pkey]
					return self.ss.players[pkey]
			try:
				p = Player.objects.get(name=pname)
				self.ss.players[pname] = p
				return p
			except:
				try:
					p = Player.objects.get(printedname=pname)
					self.ss.players[pname] = p
					if self.livelog:
						self.get_avatar(p)
					return p
				except:
					p = Player(name=pname,clan=self.get_clan('NoClan'))
					p.save()
					self.ss.players[pname] = p
					if self.livelog:
						self.get_avatar(p)
					return p

	def get_clan(self,cname):
		if cname.decode('utf-8','ignore') in self.ss.clans:
			return self.ss.clans[cname.decode('utf-8','ignore')]
		else:
			c, g = Clan.objects.get_or_create(name=cname.decode('utf-8','ignore'))
			self.ss.clans[cname.decode('utf-8','ignore')] = c
			return c

	def get_weapon(self,wname):
		if wname in self.ss.weapons:
			return self.ss.weapons[wname]
		else:
			w, g = Weapon.objects.get_or_create(name = wname)
			self.ss.weapons[wname] = w
			return w

	def get_cause(self,cname):
		if cname in self.ss.causes:
			return self.ss.causes[cname]
		else:
			c, created = Cause.objects.get_or_create(name = cname)
			self.ss.causes[cname] = c
			return c

	def add_players(self,players):
		if players:
			for player in players:
				if PRINT_DEBUG: print player.decode('utf-8','ignore')
				self.get_player(player)
				#except:
					#if PRINT_DEBUG: print("bad player")

	def add_clans(self,clans):
		if clans:
			for pname, cname, printedname in clans:
				p = self.get_player(pname)
				p.printedname = printedname.decode('utf-8','ignore')

				c = self.get_clan(cname)
				c.save()
				p.clan = c		
				p.save()
				

	def add_chats(self,chats):
		for line in chats:
			if PRINT_DEBUG: print line
			ts = self.parse_time(line.split()[0])
			pname = re.search('(<.*?>)',line).groups()[0].strip('<>')
			if pname is '':
				pname = re.search('(<.*>)',line).groups()[0].strip('<>')
			message = re.split('<.*?>',line)[1].decode('utf-8','ignore').strip()
			p = self.get_player(pname)
			if p:
				c = Chat(player=p,time=ts,text=message)
				c.save()

	def first_run(self):
		clan, created = Clan.objects.get_or_create(name="NoClan")
		clan.save()

	def calculate_kds(self):
		for pname,player in self.ss.players.iteritems():
			player.update_kd()

		for cname,clan in self.ss.clans.iteritems():
			clan.update_kd()
	
	def get_avatar(self,p):
		try:
			print "p:{0}".format(p)
			a = Avatar.objects.get(player=p)
			avatar_dict = json.load(urllib2.urlopen('http://{1}/player/{0}/avatar'.format(p.name,KAG_API)))
			a.small = avatar_dict["small"]
			a.medium = avatar_dict["medium"]
			a.large = avatar_dict["large"]
			print avatar_dict["large"]
			a.save()
		except:
			try:
				avatar_dict = json.load(urllib2.urlopen('http://{1}/player/{0}/avatar'.format(p.name,KAG_API)))
				a = Avatar(player=p,small=avatar_dict["small"],medium=avatar_dict["medium"],large=avatar_dict["large"])
				print avatar_dict["large"]
				a.save()
			except:
				if PRINT_DEBUG: print "No Avatar"
	
	def check_gold(self,p):
		try:
			info_dict = json.load(urllib2.urlopen('http://{1}/player/{0}/info'.format(p.name,KAG_API)))
			p.gold = info_dict["gold"]
			p.save()
		except:
			if PRINT_DEBUG: print("Info not found")
					
	def get_golds(self):
		print "Getting Golds!"
		for p in self.ss.pset():
			self.check_gold(p)				
					
	def get_avatars(self):
		print "Getting Avatars"
		for p in self.ss.pset():
			self.get_avatar(p)

	def count_clanmembers(self):
		for cname, clan in self.ss.clans.iteritems():
			clan.update_members()
