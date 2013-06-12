#!/usr/bin/python
from threading import *
from Queue import Queue
from settings import KAG_DIR
from subprocess import call
from sys import path
from os import walk
from time import *
from datetime import datetime
from logparser import *

path.append('./')
THREADS = 5	# Set this to your cores + 1
class LogDemon(Thread):
	def __init__(self, pqueue):
		Thread.__init__(self)
		self.pqueue = pqueue

	def run(self):
		while True:
			chat = self.pqueue.get()
			print chat
			call(['python','logparser.py',chat])

			#signals to queue job is done
			self.pqueue.task_done()

if __name__ == '__main__':
		start = datetime.now()
		#spawn a pool of threads, and pass them queue instance
		pqueue = Queue()
		chats = filter(lambda line:line.count("chat"),walk(KAG_DIR + 'Logs').next()[2])
		chats.sort()
		for chat in chats[:-1]:
			pqueue.put(chat)
		for i in range(THREADS):
			#fire up the worker threads
			t = LogDemon(pqueue)
			t.setDaemon(True)
			t.start()
			sleep(10)

		#populate queue with data
	

		#wait on the queue until everything has been processed
		pqueue.join()
		print datetime.now() - start
		lp = LogParser()
		lp.query_api(Player.objects.all())
		lp.make_top_tables()
		lp.delete_archival_records()
		
