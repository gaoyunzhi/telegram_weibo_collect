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
	return getCount(card.get('mblog')) > 120
	
def process(url):
	content = sg.getContent(url)
	content = yaml.load(content, Loader=yaml.FullLoader)
	try:
		content['data']['cards']
	except:
		if not content:
			print('no content')
			return
		for x in content:
			print(str(x)[:10])
		return
	for card in content['data']['cards']:
		if not shouldSend(card):
			continue
		url = clearUrl(card['scheme'])
		if url in db.existing.items:
			continue
		try:
			r = weibo_2_album.get(url)
		except:
			continue
		if r.wid in db.existing.items or r.rwid in db.existing.items:
			continue
		print(url, r.wid, r.rwid)
		timer.wait(10)
		try:
			album_sender.send(channel, url, r)
		except Exception as e:
			print(e)
			continue
		db.existing.add(url)
		db.existing.add(r.wid)
		db.existing.add(r.rwid)
		# rwid = '' will cause every time we only push one new item, which
		# is a bug, but can be used as a feature... 

@log_on_fail(debug_group)
def loopImp():
	removeOldFiles('tmp')
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
	commitRepo()
	print('loop finished. commit in thread.')

def loop():
	loopImp()
	threading.Timer(60 * 60, loop).start() 

if __name__ == '__main__':
	loop()