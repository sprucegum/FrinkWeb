'''
FrinkStats Player Banner Generator
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

import Image, ImageColor, ImageDraw, ImageFont


KAG_DIR = '/home/frink/kag-linux32-dedicated/'
WATERMARK = "frink.gnudist.com"

class Banner(object):
	def __init__(self,name="Teste Mctesterton",kills=4432,wkills=53,dkills=14, deaths=1):
		name = name.replace('_',' ')
		# Make Fonts
		yoster24 = ImageFont.truetype(KAG_DIR + 'frinkweb/stats/static/yoster.ttf',24)
		yoster12 = ImageFont.truetype(KAG_DIR + 'frinkweb/stats/static/yoster.ttf',12)
		# Make Canvas
		width = 400
		height = 80
		self.image = Image.new("RGBA",(width,height),(0,0,0,0))
		draw = ImageDraw.Draw(self.image)
		# Draw Border
		bwidth = 4
		draw.rectangle([(0,bwidth),(width,height-(bwidth + 1))],fill=ImageColor.getrgb('#900'))
		draw.rectangle([(bwidth,0),(width-(bwidth + 1),height)],fill=ImageColor.getrgb('#900'))
		draw.rectangle([(bwidth,2*bwidth),(width-(bwidth + 1),height-2*(bwidth + 1))],fill=ImageColor.getrgb('#400'))
		draw.rectangle([(2*bwidth,bwidth),(width-2*(bwidth + 1),height-(bwidth + 1))],fill=ImageColor.getrgb('#400'))
		# Draw Name, Rank, Kills, Deaths, KD, Favorite Weapon, Rank
		namewidth, nameheight = yoster24.getsize(name)
		# Name
		draw.text((((width/2)-(namewidth/2))+1,4+1),name,font=yoster24,fill=(155,155,155)) # text shadow
		draw.text(((width/2)-(namewidth/2),4),name,font=yoster24)
		
		fw, fh = yoster12.getsize(WATERMARK)
		#draw.text((14,height-16),"Dr. Frink's FUNHOUSE",font=yoster12,fill=(136,0,0))
		draw.text((width-(fw+14),height-16),WATERMARK,font=yoster12,fill=(136,0,0))
				
		# Load medal images
		m5k = Image.open(KAG_DIR + "frinkweb/originals/5k.png")
		m1k = Image.open(KAG_DIR + "frinkweb/originals/1k.png")
		m500 = Image.open(KAG_DIR + "frinkweb/originals/500.png")
		m100 = Image.open(KAG_DIR + "frinkweb/originals/100.png") 
		m50 = Image.open(KAG_DIR + "frinkweb/originals/50.png")
		m10 = Image.open(KAG_DIR + "frinkweb/originals/10.png") 
		
		# Draw Medals
		xpos = 16
		ypos = height - 36
		draw.text((xpos,ypos-14),"All-Time Kills",font=yoster12)
		okills = kills
		while kills >= 10:
			if kills >= 5000:
				self.image.paste(m5k, (xpos, ypos),m5k)
				kills -= 5000
				
			elif kills >= 1000:
				self.image.paste(m1k, (xpos, ypos),m1k)
				kills -= 1000
				
			elif kills >= 500:
				self.image.paste(m500,(xpos,ypos),m500)
				kills -= 500
				
			elif kills >= 100:
				self.image.paste(m100,(xpos,ypos),m100)
				kills -= 100
				
			elif kills >= 50:
				self.image.paste(m50,(xpos,ypos),m50)
				kills -= 50
				
			elif kills >= 10:
				self.image.paste(m10,(xpos,ypos),m10)
				kills -= 10
			xpos += 11
		spacehint = xpos
		if wkills >= 10:	
			xpos = max(yoster12.getsize("All-Time Kills")[0] + 16, xpos) + 12
			draw.text((xpos,ypos-14),"This Week",font=yoster12)
			spacehint = xpos
			while wkills > 9:
				if wkills >= 5000:
					self.image.paste(m5k, (xpos, ypos),m5k)
					wkills -= 5000
				elif wkills > 999:
					self.image.paste(m1k, (xpos, ypos),m1k)
					wkills -= 1000
				elif wkills >= 500:
					self.image.paste(m500,(xpos,ypos),m500)
					wkills -= 500
				elif wkills > 99:
					self.image.paste(m100,(xpos,ypos),m100)
					wkills -= 100
				elif wkills > 49:
					self.image.paste(m50,(xpos,ypos),m50)
					wkills -= 50
				elif wkills > 9:
					self.image.paste(m10,(xpos,ypos),m10)
					wkills -= 10
				xpos += 11
				
		if dkills >= 10:
			xpos = max(yoster12.getsize("This Week")[0] + spacehint, xpos) + 12
			draw.text((xpos,ypos-14),"Today",font=yoster12)
			while dkills > 9:
				if dkills >= 5000:
					self.image.paste(m5k, (xpos, ypos),m5k)
					dkills -= 5000
				if dkills > 999:
					self.image.paste(m1k, (xpos, ypos),m1k)
					dkills -= 1000
				elif dkills >= 500:
					self.image.paste(m500,(xpos,ypos),m500)
					dkills -= 500
				elif dkills > 99:
					self.image.paste(m100,(xpos,ypos),m100)
					dkills -= 100
				elif dkills > 49:
					self.image.paste(m50,(xpos,ypos),m50)
					dkills -= 50
				elif dkills > 9:
					self.image.paste(m10,(xpos,ypos),m10)
					dkills -= 10
				xpos += 11
				
		# Draw K/D insignia
		if deaths:
			kd = okills/float(deaths)
			star = Image.open(KAG_DIR + "frinkweb/originals/star.png")
			chevron = Image.open(KAG_DIR + "frinkweb/originals/chevron.png")
			ypos = 30
			while kd > 0:
				if kd > 3:
					self.image.paste(star,((width - 40),ypos),star)
				else:
					self.image.paste(chevron,((width - 40),ypos),chevron)
				kd -= 1.0
				ypos += 8
		
		
	def write(self,fobject):
		# Write image to file object
		self.image.save(fobject, "PNG", optimize=True)
		
	def save(self):
		self.image.save('test.png')
				
		
		
