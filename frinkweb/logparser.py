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
from threading import *
from Queue import Queue

<<<<<<< HEAD
KAG_DIR = '/home/frink/kag-linux32-dedicated/'
=======
KAG_DIR = '/home/jadel/FrinkWeb/'
>>>>>>> 66742f30932f3ab096c12ad4ecedae8978ad06c1


PRINT_DEBUG = False

class LogParser(object):

	def __init__(self, ss = ServerState()):
		self.ss = ss
		self.freshlog = True
		self.livelog = None


	def parse_logs(self):
		self.first_run()

		chats = self.get_logs()
		console_logs = self.get_console_logs()
		# Grab all the log files
		# call parse log on each log file
		# call move log on each parsed log
		for chat in chats[:-1]:

			clogname, console_logs = self.matching_console_log(chat,console_logs)
			self.set_day(chat)
			print KAG_DIR +'Logs/'+chat
			print KAG_DIR +'Logs/'+clogname
			logfile = open(KAG_DIR +'Logs/'+chat)
			clogfile = open(KAG_DIR + 'Logs/'+clogname)
			log = logfile.readlines()
			clog = clogfile.readlines()
			self.ss.server_restart()
			self.ss.lasthour = 0
			self.ss.days = 0
			self.unparsed, self.cunparsed = self.parse_log(log,clog)
			self.move_log(logfile,chat)
			self.move_log(clogfile,clogname)

		self.process_database()

	def matching_console_log(self,chat,console_logs):
		datestamp = chat.strip('chatx.-')
		for clog in console_logs:
			if clog.count(datestamp):
				console_logs.remove(clog)
				return (clog, console_logs)
		for clog in console_logs:
			if clog.count(datestamp[:-2]):
				console_logs.remove(clog)
				return (clog, console_logs)
		return (None, console_logs)

	def set_day(self,chat):
		datearr = re.match('chat-([0-9]{2}-[0-9]{2}-[0-9]{2}).*',chat).groups()[0].split('-')
		self.year = '20{0}'.format(datearr[0])
		self.month = datearr[1]
		self.day = datearr[2]

	def process_database(self):
		self.calculate_kds()
		self.count_clanmembers()
		if not self.livelog:
			self.query_api(self.ss.known_players())

	def get_logs(self):
		chats = filter(lambda line:line.count("chat"),walk(KAG_DIR + 'Logs').next()[2])
		chats.sort()
		return (chats)

	def get_console_logs(self):
		console_logs = filter(lambda line:line.count("console"),walk(KAG_DIR + 'Logs').next()[2])
		console_logs.sort()
		return (console_logs)

	def parse_livelog(self):
		if self.livelog is None:
			self.livelogname = self.get_logs()[-1]
			self.liveclogname = self.get_console_logs()[-1]
			self.livelog = open(KAG_DIR + 'Logs/' + self.livelogname)
			self.liveclog = open(KAG_DIR + 'Logs/' + self.liveclogname)
			self.set_day(self.livelogname)
		new_events = self.livelog.readlines()[self.ss.logposition:]
		new_cevents = self.liveclog.readlines()[self.ss.clogposition:]
		self.ss.logposition = self.ss.logposition+len(new_events)
		self.ss.clogposition = self.ss.clogposition+len(new_cevents)
		self.parse_log(new_events, new_cevents)
		self.process_database()



	def close_livelog(self):
		self.move_log(self.livelog,self.livelogname)

	def parse_log(self, chatlog, consolelog):
		# Read through a log
		unparsed = []
		cunparsed = []
		while chatlog or consolelog:

			if chatlog and consolelog:
				while not re.search('^\[.*\].*', consolelog[0]):
					consolelog.pop(0)
				while not re.search('^\[.*\].*', chatlog[0]):
					chatlog.pop(0)

				if self.parse_time(chatlog[0].split()[0],False) <= self.parse_time(consolelog[0].split()[0],False):
					unparsed.append(self.parse_chat_line(chatlog.pop(0)))
				elif (self.parse_time(chatlog[0].split()[0],False) > self.parse_time(consolelog[0].split()[0],False)):
					cunparsed.append(self.parse_console_line(consolelog.pop(0)))
			elif chatlog:
				unparsed.append(self.parse_chat_line(chatlog.pop(0)))
			else:
				cunparsed.append(self.parse_console_line(consolelog.pop(0)))
		return (unparsed, cunparsed)

	def parse_chat_line(self,line):
		line = self.get_players([line])
		if line:
			line = self.get_chats(line)
		if line:
			line = self.get_kills(line)
		if line:
			line = self.get_accidents(line)
		return line

	def parse_console_line(self,line):
		if re.search('^\[.*\] \*{1}.* connected \(admin:.*',line):
			# player connects
			# [22:40:58] * chestabo connected (admin: 0 guard 0 gold 0)
			pname = re.split('connected',line)[0].split()[2]
			ptime = self.parse_time(line.split()[0])
			p = self.ss.create_play_session(pname,ptime)

		# player disconnects
		# [22:41:39] Player chestabo left the game (players left 2)

		elif re.search('^\[.*\] Player .* left the game .*', line):
			pname = re.split('Player',line)[1]
			pname = re.split('left the game',pname)[0].strip()
			ptime = self.parse_time(line.split()[0])
			if pname:
				self.ss.close_play_session(pname,ptime)

		# match end
		# [23:03:57] *Match Ended*
		elif re.search('^\[.*\] \*Match Ended\*', line):
			ptime = self.parse_time(line.split()[0])
			self.ss.end_match(ptime)
			# end all lives/streaks/etc/

		# match start
		# [23:03:57] *Match Started*
		elif re.search('^\[.*\] \*Match Ended\*',line):
			self.ss.start_match(self.parse_time(line.split()[0]))
			self.ss.livesleft = True
			# start new lives for all current players

		# units depleted
		# [23:03:48] Can't spawn units depleted
		elif re.search('''^\[.*\] Can't spawn units depleted''',line):
			self.ss.livesleft = False
			#stop making new lives for players when they die

		# collapse
		# [23:05:12] COLLAPSE by Sir Meta_Data (size 8 blocks)
		elif re.search('''^\[.*\] COLLAPSE by .*''',line):
			pname = re.split('\(size [0-9]* blocks\)',line)[0].split()[-1]
			ptime = self.parse_time(line.split()[0])
			collapse_size = int(re.split('^\[.*\] COLLAPSE by .* \(size',line)[-1].split()[0])
			p = self.ss.get_player(pname)
			c = Collapse(player = p, time = ptime, size = collapse_size)
			c.save()

		elif re.search('''^\[.*\] WARNING: API call failed .*''',line):
			#Shit just got real.
			self.ss.errorstate = True
		elif re.search('''^\[.*\] WARNING: A call to update the server list API .*''',line):
			self.ss.errorstate = True


		return line

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
			except Exception as e:
				print e
				print "Bad Line:\n{0}".format(line)
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
				if re.search('^\[..:..:..] Unnamed player is now known as',line):
					players.append(re.split('Unnamed player is now known as',line.strip())[1].strip())
				elif re.search('^\[..:..:..] [^<].* is now known as',line):
					# to improve this algorithm, I should identify the player name by finding the
					# text in common between the old and new name
					clan_nameline = re.split('is now known as',line.strip())
					playername = clan_nameline[0].split()[-1].strip()
					printedname = clan_nameline[-1].split()[-1].strip()
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
		return loglines

	def parse_time(self,logtime, commit = True):
		dmod = 0
		(hour, minute, second) = logtime.strip('[]').split(':')
		if int(hour) < self.ss.lasthour:
			dmod = 1
			if commit:
				dmod = 0
				self.ss.days += 1
				print "incrementing day. days:{0} hour:{1} lasthour:{2} logtime:{3}".format(self.ss.days, hour, self.ss.lasthour, logtime)
		if commit:
			self.ss.lasthour = int(hour)
		return (datetime(int(self.year),
					int(self.month),
					int(self.day),
					int(hour),
					int(minute),
					int(second))+timedelta(days=(self.ss.days + dmod)))
		'''
		except Exception as e:
			print logtime
			print e
		'''



	def add_kills(self,kills):

		if kills:
			if PRINT_DEBUG: print "\n{0:22}{1:20}{2:20}{3:20}".format('time','killer','victim','weapon')
			for kill in kills:

				if PRINT_DEBUG: print "{0[0]:22s}{0[1]:20}{0[2]:20}{0[3]:20}".format(kill)
				#p = Player.objects.get(printedname__exact=kill[1])
				p = self.ss.get_player(kill[1])
				p.add_kill()

				#v = Player.objects.get(printedname__exact=kill[2])
				v = self.ss.get_player(kill[2])
				v.add_death()

				w = self.ss.get_weapon(kill[3])
				k = Kill(time=kill[0],player=p,victim=v,weapon=w)
				self.ss.end_life(v.name,kill[0])
				k.save()

	def add_accidents(self,accidents):
		if accidents:
			if PRINT_DEBUG: print "\n{0:22}{1:20}{2:20}".format("time","victim","cause")
			for accident in accidents:
				ktime = accident[0]
				if PRINT_DEBUG: print "{0[0]:22s}{0[1]:20}{0[2]:20}".format(accident.decode('utf-8','ignore'))
				p = self.ss.get_player(accident[1])
				#p.add_death()
				self.ss.end_life(p.name,ktime)
				c = self.ss.get_cause(accident[2])
				a = Accident(player = p,time = ktime,cause = c)
				a.save()


	def add_players(self,players):
		if players:
			for player in players:
				if PRINT_DEBUG: print player.decode('utf-8','ignore')
				p = self.ss.get_player(player,known_correct=True)
				if self.livelog:
					p.clan = self.ss.get_clan("NoClan")
					p.save()
				
	def add_clans(self,clans):
		if clans:
			for pname, cname, printedname in clans:
				p = self.ss.get_player(pname)
				c = self.ss.get_clan(cname)
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
			p = self.ss.get_player(pname)
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

	def query_api(self,plist):
		#spawn a pool of threads, and pass them queue instance
		pqueue = Queue()
		for i in range(8):
			t = KagApiQThread(pqueue)
			t.setDaemon(True)
			t.start()

		#populate queue with data
		for player in plist:
			pqueue.put(player)
		#wait on the queue until everything has been processed
		pqueue.join()

	def count_clanmembers(self):
		for cname, clan in self.ss.clans.iteritems():
			clan.update_members()

class KagApiQThread(Thread):
	def __init__(self, pqueue):
		Thread.__init__(self)
		self.pqueue = pqueue

	def run(self):
		while True:
			player = self.pqueue.get()
			print player.name
			#grabs urls of hosts and prints first 1024 bytes of page
			player.get_avatar()
			player.check_gold()

			#signals to queue job is done
			self.pqueue.task_done()



if __name__ == '__main__':
	print "FrinkWeb Log Parser\nparsing logs ..."
	start = datetime.now()
	lp = LogParser()
	lp.parse_logs()
	print "task completed"
	print datetime.now() - start
