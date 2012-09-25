from stats.models import *
from datetime import datetime
from time import time

class ServerState(object):
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
		def __init__(self):
			self.birth = datetime.now()
			
