import os
import yaml

def getFile(name):
	fn = 'db/' + name
	os.system('touch ' + fn)
	with open(fn) as f:
		return set(x.strip() for x in f.readline() if x.strip())

class DBItem(object):
	def __init__(self, name):
		self.db = getFile(name)
		self.fn = 'db/' + name

	def add(self, x):
		x = x.strip()
		if x in self.db:
			return
		self.db.add(x)
		with open(fn, 'a') as f:
			f.write('\n' + x)

	def remove(self, x):
		raise Exception('To be implemented') 


class DB(object):
	def __init__(self):
		self.users = DBItem('users')
		self.keywords = DBItem('keywords')
		self.existing = DBItem('existing')
