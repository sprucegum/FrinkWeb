'''
FrinkStats Models
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

from django.db import models

# Create your models here.

class Player(models.Model):
	name = models.CharField(max_length=50)
	printedname = models.CharField(max_length=60)
	clan = models.ForeignKey("Clan")
	kills = models.IntegerField(default=0)
	deaths = models.IntegerField(default=0)
	kd = models.DecimalField(decimal_places=2,max_digits=5,default="0.0")
	play_time = models.IntegerField(default=0)

	def add_kill(self):
		self.kills += 1
		self.save()
		if self.clan:
			self.clan.add_kill()

	def add_death(self):
		self.deaths += 1
		self.save()
		if self.clan:
			self.clan.add_death()

	def update_kd(self):
		if (self.deaths>10):
			self.kd = str(self.kills/float(self.deaths))
		self.save()


	def __unicode__(self):
		return self.name

class Kill(models.Model):
	player = models.ForeignKey(Player, related_name = 'kill_set')
	victim = models.ForeignKey(Player, related_name = 'death_set')
	weapon = models.ForeignKey('Weapon')
	time = models.DateTimeField()
	def __unicode__(self):
		return "{0} {1} killed {2} with {3}".format(self.time,self.player,self.victim,self.weapon)

class Accident(models.Model):
	player = models.ForeignKey(Player)
	time = models.DateTimeField()
	cause = models.ForeignKey('Cause')
	def __unicode__(self):
		return "{0} {1} died from {2}".format(self.time, self.player, self.cause)

class Clan(models.Model):
	name = models.CharField(max_length=50)
	kills = models.IntegerField(default=0)
	deaths = models.IntegerField(default=0)
	kd = models.DecimalField(decimal_places=2,max_digits=5,default="0.0")
	members = models.IntegerField(default=0)

	def add_kill(self):
		self.kills += 1
		self.save()

	def add_death(self):
		self.deaths += 1
		self.save()

	def update_kd(self):
		if (self.deaths>10):
			self.kd = str(self.kills/float(self.deaths))
		self.save()
	
	def update_members(self):
		self.members = self.player_set.count()
		self.save()

	def __unicode__(self):
		return self.name


class Weapon(models.Model):
	name = models.CharField(max_length=50)
	def __unicode__(self):
		return self.name

class Cause(models.Model):
	name = models.CharField(max_length=50)
	def __unicode__(self):
		return self.name

class Session(models.Model):
	player = models.ForeignKey(Player)
	start = models.DateTimeField()
	end = models.DateTimeField()
	kills = models.IntegerField(default=0)
	deaths = models.IntegerField(default=0)
	kd = models.DecimalField(decimal_places=2,max_digits=5,default="0.0")
	def __unicode__(self):
		return self.player

class Life(models.Model):
	player = models.ForeignKey(Player)
	kill_set = models.ManyToManyField(Kill)
	start = models.DateTimeField()
	end = models.DateTimeField()
	def __unicode__(self):
		return self.player


class Chat(models.Model):
	player = models.ForeignKey(Player)
	time = models.DateTimeField()
	text = models.CharField(max_length=255)
	def __unicode__(self):
		return self.text

class ServerState(models.Model):
	players = models.IntegerField(default=0)
	mem = models.IntegerField(default=0)
	time = models.DateTimeField()
	uptime = models.IntegerField(default=0)
	logname = models.CharField(max_length=60)
	logline = models.IntegerField(default=0)
	def __unicode__(self):
		return "Players:{0} Mem:{1} Uptime:{2}".format(players,mem,uptime)

