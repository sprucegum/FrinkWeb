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


KAG_DIR = '/home/jadel/FrinkWeb/'
WATERMARK = "frink.gnudist.com"
TRIM_COLOR = '#900'
BG_COLOR = '#400'
WATERMARK_COLOR = (136,0,0)

class Banner(object):
	def __init__(self,name="Teste Mctesterton",kills=6432,wkills=534,dkills=140, deaths=1):
		name = name.replace('_',' ')
		# Make Fonts
		self.yoster24 = ImageFont.truetype(KAG_DIR + 'frinkweb/stats/static/yoster.ttf',24)
		self.yoster12 = ImageFont.truetype(KAG_DIR + 'frinkweb/stats/static/yoster.ttf',12)
		
		# Load medal images
		self.loadImages()
		# Draw Medals
		medals = []
		if kills >= 10:
			medals.append(self.drawMedals('All-Time',kills))
		
		if wkills >= 10:	
			medals.append(self.drawMedals('Weekly',wkills))
				
		if dkills >= 10:
			medals.append(self.drawMedals('Today',dkills))
				
		# Draw K/D insignia
		if deaths:
			insignia = self.drawInsignia(kills,deaths)
			
		self.banner = self.assembleBanner(name,medals,insignia)
		
			
	def assembleBanner(self,name,medals,insignia):
		width, height = self.sizeBanner(name,medals,insignia)
		oheight = height
		
		bwidth = 4
		
		height = max(insignia.size[1] + 2*bwidth, height)
		xpos = 2*bwidth
		ypos = 2*bwidth
		linesize = 16
		image = Image.new("RGBA",(width,height),(0,0,0,0))
		draw = ImageDraw.Draw(image)
		# Draw Border

		draw.rectangle([(0,bwidth),(width,height-(bwidth + 1))],fill=ImageColor.getrgb(TRIM_COLOR))
		draw.rectangle([(bwidth,0),(width-(bwidth + 1),height)],fill=ImageColor.getrgb(TRIM_COLOR))
		draw.rectangle([(bwidth,2*bwidth),(width-(bwidth + 1),height-2*(bwidth + 1))],fill=ImageColor.getrgb(BG_COLOR))
		draw.rectangle([(2*bwidth,bwidth),(width-2*(bwidth + 1),height-(bwidth + 1))],fill=ImageColor.getrgb(BG_COLOR))
		# Draw Name, Rank, Kills, Deaths, KD, Favorite Weapon, Rank
		image.paste(insignia,(width - (insignia.size[0]+2*bwidth),height/2 - insignia.size[1]/2),insignia)
		namewidth, nameheight = self.yoster24.getsize(name)
		maxwidth = 525 - (2*bwidth - insignia.size[0])
		# Name
		fw, fh = self.yoster12.getsize(WATERMARK)
		if oheight == 50:
			for medalset in medals:
				image.paste(medalset,(xpos,ypos), medalset)
				xpos += medalset.size[0] + 4
			draw.text((xpos+1,ypos+1),name,font=self.yoster24,fill=(155,155,155)) # text shadow
			draw.text((xpos,ypos),name,font=self.yoster24)
			draw.text((xpos+2,height-16),WATERMARK,font=self.yoster12,fill=WATERMARK_COLOR)
						
		else:
			ypos+=linesize
			medalwidth = reduce(lambda x,y:x+y.size[0]+4,medals,0)
			xpos = (width/2) - (medalwidth/2)
			draw.text((((width/2)-(namewidth/2))+1,4+1),name,font=self.yoster24,fill=(155,155,155)) # text shadow
			draw.text(((width/2)-(namewidth/2),4),name,font=self.yoster24)
			ypos += 4
			for medalset in medals:
				if xpos + medalset.size[0] > maxwidth:
					ypos += linesize + 2
					xpos = bwidth
				image.paste(medalset, (xpos,ypos), medalset)
				xpos += medalset.size[0] + 4
			draw.text(((width/2)-(fw/2),height-16),WATERMARK,font=self.yoster12,fill=WATERMARK_COLOR)
		
		#draw.text((14,height-16),"Dr. Frink's FUNHOUSE",font=yoster12,fill=(136,0,0))
		#draw.text((width-(fw+14),height-16),WATERMARK,font=yoster12,fill=(136,0,0))
		
		return image
		
	def sizeBanner(self,name,medals,insignia):
		x = 0
		y = 0
		minheight = 50	# increment height in multiples of this number
		minwidth = 0
		linesize = 16
		bwidth = 8
		maxwidth = 525 - (2*bwidth - insignia.size[0])
		namewidth, nameheight = self.yoster24.getsize(name)
		lines = (namewidth + insignia.size[0] + reduce(lambda x,y:x+y.size[0]+4,medals,0))/maxwidth
		x = 525
		if lines == 0:
			x = (4*bwidth + namewidth + insignia.size[0] + reduce(lambda x,y:x+y.size[0]+4,medals,0))
		else:
			x = max((4*bwidth + insignia.size[0] + reduce(lambda x,y:x+y.size[0]+4,medals,0)),4*bwidth + insignia.size[0] + namewidth)
			minheight += 12 # for watermark
		y = minheight + lines*linesize	
		return (x,y)
		
				
	def drawInsignia(self,kills,deaths):
		kd = kills/float(deaths)
		star = Image.open(KAG_DIR + "frinkweb/originals/star.png")
		chevron = Image.open(KAG_DIR + "frinkweb/originals/chevron.png")
		height = (1+int(kills/deaths))*8 + 4
		image = Image.new("RGBA",(chevron.size[0],height),(0,0,0,0))
		ypos = 0
		while kd > 0:
			if kd > 3:
				image.paste(star,(0,ypos),star)
			else:
				image.paste(chevron,(0,ypos),chevron)
			kd -= 1.0
			ypos += 8
		return image
	
	
		
	def drawMedals(self,title,kills):
		width, height = self.sizeMedals(kills)
		width = max(width, self.yoster12.getsize(title)[0]) 
		image = Image.new("RGBA",(width,height),(0,0,0,0))
		draw = ImageDraw.Draw(image)
		ypos = 0
		draw.text((0,0),title,font=self.yoster12)
		ypos += 12
		xpos = 0
		
		
		while kills > 9:
			if kills >= 10000:
				image.paste(self.m10k, (xpos, ypos),self.m10k)
				kills -= 10000
				xpos += xpos + self.m10.size[0]
			elif kills >= 5000:
				image.paste(self.m5k, (xpos, ypos),self.m5k)
				kills -= 5000
			elif kills >= 1000:
				image.paste(self.m1k, (xpos, ypos),self.m1k)
				kills -= 1000
			elif kills >= 500:
				image.paste(self.m500,(xpos,ypos),self.m500)
				kills -= 500
			elif kills > 99:
				image.paste(self.m100,(xpos,ypos),self.m100)
				kills -= 100
			elif kills > 49:
				image.paste(self.m50,(xpos,ypos),self.m50)
				kills -= 50
			elif kills > 9:
				image.paste(self.m10,(xpos,ypos),self.m10)
				kills -= 10
			xpos += self.m10.size[0] + 1
		return image
		
	def sizeMedals(self,kills):
		xpos = 0
		ypos = 12 + self.m10.size[1]
		while kills > 9:
			if kills >= 10000:
				kills -= 10000
				# This is necessary for the double sized medal
				xpos += self.m10.size[0]
			if kills >= 5000:
				kills -= 5000
			if kills > 999:
				kills -= 1000
			elif kills >= 500:
				kills -= 500
			elif kills > 99:
				kills -= 100
			elif kills > 49:
				kills -= 50
			elif kills > 9:
				kills -= 10
			xpos += self.m10.size[0] + 1
		xpos += self.m10.size[0] + 1
		return (xpos,ypos)
	
	def loadImages(self):
		self.m10k = Image.open(KAG_DIR + "/frinkweb/originals/10k.png")
		self.m5k = Image.open(KAG_DIR + "frinkweb/originals/5k.png")
		self.m1k = Image.open(KAG_DIR + "frinkweb/originals/1k.png")
		self.m500 = Image.open(KAG_DIR + "frinkweb/originals/500.png")
		self.m100 = Image.open(KAG_DIR + "frinkweb/originals/100.png") 
		self.m50 = Image.open(KAG_DIR + "frinkweb/originals/50.png")
		self.m10 = Image.open(KAG_DIR + "frinkweb/originals/10.png") 
		
	def write(self,fobject):
		# Write image to file object
		self.banner.save(fobject, "PNG", optimize=True)
		
	def save(self):
		self.banner.save('test.png')
				
		
	
