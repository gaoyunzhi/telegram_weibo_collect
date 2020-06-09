#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import matchKey, clearUrl, log_on_fail, removeOldFiles, commitRepo
import sys
from telegram.ext import Updater, MessageHandler, Filters
import yaml
import album_sender
from soup_get import SoupGet, Timer
from db import DB
import threading
import weibo_2_album
import urllib

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot_token'], use_context=True) # @contribute_bot
debug_group = tele.bot.get_chat(420074357)
channel = tele.bot.get_chat('@weibo_read')

sg = SoupGet()
db = DB()
timer = Timer()
cache = {}

def getSingleCount(blog):
	try:
		return int(blog['reposts_count']) + int(blog['comments_count']) + int(blog['attitudes_count'])
	except:
		print(str(blog)[:100])
		return 0

def getCount(blog):
	if not blog:
		return 0
	count = getSingleCount(blog)
	if 'retweeted_status' in blog:
		blog = blog['retweeted_status']
		count += getSingleCount(blog) / 3
	return count

def shouldSend(card):
	if matchKey(str(card), db.whitelist.items):
		return True
	if matchKey(str(card), db.blacklist.items):
		return False
	if matchKey(str(card), db.preferlist.items):
		return getCount(card.get('mblog')) > 300
	if matchKey(str(card), db.popularlist.items):
		return getCount(card.get('mblog')) > 10000
	return getCount(card.get('mblog')) > 1000

def processCard(card):
	if not shouldSend(card):
		return
	url = clearUrl(card['scheme'])
	if url in db.existing.items:
		return

	r = weibo_2_album.get(url)
	print('hash', r.hash)
	if (str(r.wid) in db.existing.items or str(r.rwid) in db.existing.items or 
		str(r.hash) in db.existing.items):
		return

	print('sending', url, r.wid, r.rwid)
	timer.wait(10)

	cache[r.hash] = cache.get(r.hash, 0) + 1
	if cache[r.hash] > 2:
		# for whatever reason, this url does not send to telegram, skip
		db.existing.add(r.hash)

	album_sender.send(channel, url, r)
	
	db.existing.add(url)
	db.existing.add(r.wid)
	db.existing.add(r.rwid)
	db.existing.add(r.hash)
	
def process(url):
	content = sg.getContent(url)
	content = yaml.load(content, Loader=yaml.FullLoader)
	try:
		content['data']['cards']
	except:
		return # url read fail, may due to rate limiting
	for card in content['data']['cards']:
		try:
			processCard(card)
		except Exception as e:
			debug_group.send_message(clearUrl(card['scheme']) + '\n' + str(e))
	
@log_on_fail(debug_group)
def loopImp():
	debug_group.send_message('start loop')
	removeOldFiles('tmp', days=0.1)
	sg.reset()
	db.reload()
	for keyword in db.keywords.items:
		print(keyword)
		content_id = urllib.request.pathname2url('100103type=1&q=' + keyword)
		url = 'https://m.weibo.cn/api/container/getIndex?containerid=%s&page_type=searchall' % content_id
		process(url)
	for user in db.users.items:
		print(user)
		url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=107603%s' \
			% (user, user)
		process(url)
	commitRepo(delay_minute=0)
	print('loop finished. commit in thread.')
	debug_group.send_message('end loop')

def loop():
	loopImp()
	threading.Timer(60 * 10, loop).start() 

if __name__ == '__main__':
	loop()