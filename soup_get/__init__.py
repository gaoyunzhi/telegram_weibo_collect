import cached_url
import time
import random
import yaml

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

class Timer(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self.last_request = 0

	def wait(self, wait):
		sleep_time = wait + self.last_request - time.time()
		if sleep_time > 0:
			time.sleep(sleep_time)
		self.last_request = time.time()

class SoupGet(object):
	def __init__(self):
		self.timer = Timer()
		self.reset()

	def reset(self):
		self.timer.reset()

	def getContent(self, url):
		wait = random.random() * 30
		self.timer.wait(wait)
		return cached_url.get(url, 
			headers = {'cookie': credential['cookie']})