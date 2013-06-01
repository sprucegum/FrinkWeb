'''
FrinkStats WebSite
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

# Create your views here.
from models import *
from django.db.models import Count
from django.shortcuts import render_to_response
from datetime import datetime, timedelta
from banner import Banner
from django.http import HttpResponse
from blacklist import *
from heapq import nlargest 
import json


def get_timespan(timespan):
	tspan = datetime.now()
	if timespan.count('daily'):
		tspan = datetime.now() - timedelta(hours=24)
	elif timespan.count('hourly'):
		tspan = datetime.now() - timedelta(hours=1)
	elif timespan.count('weekly'):
		tspan = datetime.now() - timedelta(weeks=1)
	elif timespan.count('monthly'):
		tspan = datetime.now() - timedelta(weeks=4)
	else:
		timespan = 'all'
		return (None, timespan)
	return (tspan, timespan)

def top_players(request,timespan='all'):

	top_cat = TopCategory.objects.get(name="top50_players",title="Top Players")
	top_table = TopTable.objects.get(category=top_cat)
	top_player_entries = TopEntry.objects.filter(table=top_table).order_by('rank')[0:50]
	n_players = top_player_entries.count()
	top = []
	for entry in top_player_entries:
		kd = 0
		if entry.deaths:
			kd = "{0:.2}".format(float(entry.kills)/entry.deaths)
		try:
			top.append({'name':entry.player.name,'kills':entry.kills,'deaths':entry.deaths,'kd':kd,'avatar':{'large':entry.player.avatar.large,'medium':entry.player.avatar.medium,'small':entry.player.avatar.small},'gold':entry.player.gold})
		except:
			top.append({'name':entry.player.name,'kills':entry.kills,'deaths':entry.deaths,'kd':kd,'gold':entry.player.gold})
	
	return render_to_response('top_players.html', {'top_players': top, 'count':n_players, 'timespan':timespan})


def top_clans(request,timespan=''):
	tspan, timespan = get_timespan(timespan)
	top_clans = Clan.objects.filter(members__gte=2).order_by('-kills')[1:11]
	tc = []
	if tspan:
		
		for clan in top_clans:
			clan_name = clan.name
			clan_kills = 0
			clan_deaths = 0
			clan_members = 0
			for player in clan.player_set.all():
				kills = player.kill_set.filter(time__gte=tspan).count()
				deaths = player.death_set.filter(time__gte=tspan).count()
				if kills or deaths:
					clan_kills += kills
					clan_deaths += deaths
					clan_members += 1
				
			if clan_deaths:
				clan_kd = "{0:3.2}".format(float(clan_kills)/float(clan_deaths))
				
			else:
				clan_kd = "0.00"
			if clan_members:
				tc.append({'name':clan_name,'kills':clan_kills,'deaths':clan_deaths,'members':clan_members, 'kd':clan_kd})	
			top_clans = tc
			
	return render_to_response('top_clans.html', {'top_clans': top_clans, 'timespan':timespan,'count':len(top_clans)})

def player_search(request):
	if request.GET.__contains__("term"):
		name = request.GET["term"]
	
	players = Player.objects.filter(name__istartswith=name).values("name")[:10]
	plist = [player["name"] for player in players]
	return HttpResponse(json.dumps(plist), mimetype="application/json")

def blacklist(request):
	b = BlackList()
	name = 'none'
	if request.GET.__contains__("name"):
		name = request.GET["name"]
	ip = '0.0.0.0'
	if request.GET.__contains__("ip"):
		ip = request.GET["ip"]
	return HttpResponse(b.blacklist(name,ip), mimetype="application/json")

def banner(request,player):
	response = HttpResponse(mimetype="image/png")
	try:
		p = Player.objects.filter(name__exact=player)[0]
	except:
		try:
			p = Player.objects.get(name=player)
		except:
			return render_to_response('404.html',{'text':'Player {0} Not Found'.format(player)})
	try:
		c = p.clan.name
		if c.count('NoClan'):
			c = ''
	except:
		c = ''
	pstring = "{0} {1}".format(c,p.name)
	wkills = p.kill_set.filter(time__gte=get_timespan('weekly')[0]).count()
	dkills = p.kill_set.filter(time__gte=get_timespan('daily')[0]).count()
	b = Banner(name=pstring,kills=p.kills,wkills=wkills, dkills=dkills, deaths = p.deaths, gold = p.gold)
	b.write(response)
	return response
	
	

def get_weapon_kills(weapon, tspan):
	if not tspan:
		wlist = Player.objects.filter(kill_set__weapon__name=weapon).annotate(wkills = Count('kill_set')).order_by('-wkills')[:10]
		playerlist = []
		for p in wlist:
			try:
				playerlist.append({'name':p.name,'kills':p.wkills,'avatar':{'large':p.avatar.large,'medium':p.avatar.medium,'small':p.avatar.small},'gold':p.gold})
			except:
				playerlist.append({'name':p.name,'kills':p.wkills,'gold':p.gold})
		return playerlist
	else:
		playerlist_raw = Player.objects.values('name','id').select_related().filter(kill_set__time__gte=tspan, kill_set__weapon__name=weapon)
		playerlist = []
		players_seen = []
		for p in playerlist_raw:
			if p["name"] not in players_seen:
				p = Player.objects.get(id=p["id"])
				weaponkills = p.kill_set.values('time','weapon').filter(time__gte=tspan).filter(weapon__name=weapon).count()
				if weaponkills:
					try:
						playerlist.append({'name':p.name,'kills':weaponkills,'avatar':{'large':p.avatar.large,'medium':p.avatar.medium,'small':p.avatar.small},'gold':p.gold})
					except:
						playerlist.append({'name':p ,'kills':weaponkills,'gold':p.gold})
					players_seen.append(p.name)
		playerlist = nlargest(10,playerlist,lambda x:x['kills'])

		return playerlist
		

def top_weapons(request,timespan=''):
	tspan, timespan = get_timespan(timespan)	
	hammer = get_weapon_kills('hammer',tspan)
	sword = get_weapon_kills('sword',tspan)
	bow = get_weapon_kills('bow',tspan)
	bomb = get_weapon_kills('bomb',tspan)
	cata = get_weapon_kills('catapult',tspan)
	foot = get_weapon_kills('foot',tspan)

	return render_to_response('top_weapons.html', {'top_weapons': True, 'hammer':hammer,'sword':sword,'bow':bow,'bomb':bomb,'catapult':cata,'foot':foot, 'timespan':timespan})


def player(request, playername, kpage, dpage, timespan=''):
	try:
		p = Player.objects.filter(name__exact=playername)[0]
	except:
		try:
			p = Player.objects.get(name=playername)
		except:
			return render_to_response('404.html',{'text':'Player {0} Not Found'.format(playername)})
	try:
		c = p.clan.name
		if c.count('NoClan'):
			c = ''
	except:
		c = ''
	try:
		kpage = int(kpage)
	except:
		kpage = 0
	try:
		dpage = int(dpage)
	except:
		dpage = 0
	tspan, timespan = get_timespan(timespan)
	if not tspan:
		kills = p.kill_set.all()[kpage*10:kpage*10 + 10]
		deaths = p.death_set.all()[dpage*10:dpage*10 + 10]
		nk = p.kill_set.count()
		nd = p.death_set.count()
	else:
		kills = p.kill_set.filter(time__gte=tspan)[kpage*10:kpage*10 + 10]
		deaths = p.death_set.filter(time__gte=tspan)[dpage*10:dpage*10 + 10]
		nk = p.kill_set.filter(time__gte=tspan).count()
		nd = p.death_set.filter(time__gte=tspan).count()
	prefix = '/player/{0}/'.format(p.name)
	postfix = '/{0}/{1}'.format(kpage,dpage)
	page = {'kpage':kpage*10,'dpage':dpage*10,'knext':kpage+1,'dnext':dpage+1,'kback':max(kpage-1,0),'dback':max(dpage-1,0),'k':kpage,'d':dpage}
	return {'player': p,'clan':c,'kills':kills,'deaths':deaths,'pageinfo':page, 'timespan':timespan, 'nk':nk, 'nd':nd, 'prefix':prefix,'postfix':postfix}
	

def player_html(request, playername, kpage, dpage, timespan=''):
	return render_to_response('player.html', player(request, playername, kpage, dpage, timespan=''))
	
def player_json(request, playername):
	pd = {}
	try:	
		p = Player.objects.get(name=playername)		
	#if the request contains a ?weapon=bomb term or something like that
		if request.GET.__contains__("weapon"):
			weapon = request.GET["weapon"]
			pd["weapon"] = weapon
			pd["wkills"] =  Kill.objects.filter(player=p,weapon__name=weapon).count()
			pd["wlast"] = str(Kill.objects.filter(player=p,weapon__name=weapon)[0])
			pd["wdeaths"]= Kill.objects.filter(victim__name=playername,weapon__name=weapon).count()
			pd["wdlast"]= str(Kill.objects.filter(victim__name=playername,weapon__name=weapon)[0])

		pd["name"] = p.name
		pd["clan"] = p.clan.name
		pd["kills"] = p.kills
		pd["deaths"] = p.deaths
		pd["kd"] = 0 if p.deaths is 0 else p.kills/float(p.deaths)
		pd["success"] = True
	except Exception as e:
		pd = {"name":playername}
		pd["success"] = False
		
	return HttpResponse(json.dumps(pd), mimetype="application/json")

#Sentinel: c&p format changed it up
'''
def kills_json(request, playername,weapon):
	pd = {}
	try:		
		p = Player.objects.filter(name=playername)
		pd["names"] = p[0]
		pd["weapon"] = weapon
		pd["kills"] =  Kill.objects.filter(player=p,weapon__name=weapon).count()
		pd["last"] = Kill.objects.filter(player=p,weapon__name=weapon)[0]
		pd["success"] = True
	except Exception as e:
		pd = {"name":playername}
		pd["success"] = False
		
	return HttpResponse(json.dumps(pd), mimetype="application/json")
'''

def clan(request, clanname, timespan=''):
	try:
		tspan = None
		if timespan.count('daily'):
			tspan = datetime.now() - timedelta(hours=24)
		elif timespan.count('hourly'):
			tspan = datetime.now() - timedelta(hours=1)
		elif timespan.count('weekly'):
			tspan = datetime.now() - timedelta(weeks=1)
		elif timespan.count('monthly'):
			tspan = datetime.now() - timedelta(weeks=4)
		else:
				timespan = 'all'
		temp_clan_players = []
		clan_players = Clan.objects.get(name=clanname).player_set.all().order_by('-kills')
		if tspan:
			for player in clan_players:
				kills = player.kill_set.filter(time__gte=tspan).count()
				deaths = player.death_set.filter(time__gte=tspan).count()
				kd = "0"
				name = player.name
				if kills or deaths:
					if deaths:
						kd = "{0:3.2}".format(float(kills)/float(deaths))
					try:
						temp_clan_players.append({'name':name,'kills':kills,'deaths':deaths,'kd':kd,'avatar':{'large':player.avatar.large,'medium':player.avatar.medium,'small':player.avatar.small},'gold':player.gold})
					except:
						temp_clan_players.append({'name':name,'kills':kills,'deaths':deaths,'kd':kd,'gold':player.gold})
			clan_players = sorted(temp_clan_players, key=lambda k: k['kills'])
			clan_players.reverse()
			
	except:
		return render_to_response('404.html',{'text':'Clan {0} Not Found'.format(clanname)})
	#clan_players = filter(lambda player:int(player.kills) > 0,clan_players)
	clan_name = clanname
	return render_to_response('clan.html',{'clan_players':clan_players, 'clan_name':clan_name,'timespan':timespan})

def fourohfour(request):
	return render_to_response('404.html',{'text':'Hoiven Maven!'})
	
def robots(request):
	dirs = ['/player/']
	return render_to_response('robots.txt',{'dirs':dirs})
