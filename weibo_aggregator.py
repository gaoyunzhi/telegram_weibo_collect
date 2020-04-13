#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import matchKey, cutCaption, clearUrl, splitCommand, autoDestroy, log_on_fail, compactText
import sys
import os
from telegram.ext import Updater, MessageHandler, Filters
import export_to_telegraph
import time
import yaml
import web_2_album
import album_sender
from soup_get import SoupGet, Timer
from db import DB
import threading
import weibo_2_album
import urllib

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
export_to_telegraph.token = credential['telegraph_token']

tele = Updater(credential['bot_token'], use_context=True) # @contribute_bot
debug_group = tele.bot.get_chat(-1001198682178)
channel = tele.bot.get_chat(-1001374366482)

sg = SoupGet()
db = DB()
timer = Timer()

def removeOldFiles(d):
	try:
		for x in os.listdir(d):
			if os.path.getmtime(d + '/' + x) < time.time() - 60 * 60 * 72 or \
				os.stat(d + '/' + x).st_size < 400:
				os.system('rm ' + d + '/' + x)
	except:
		pass

def getSingleCount(blog):
	return int(blog['reposts_count']) + int(blog['comments_count']) + int(blog['attitudes_count'])

def getCount(blog):
	if not blog:
		return 0
	count = getSingleCount(blog)
	if 'retweeted_status' in blog:
		blog = blog['retweeted_status']
		count += getSingleCount(blog) / 3
	return count

def process(url):
	content = sg.getContent(url)
	content = yaml.load(content, Loader=yaml.FullLoader)
	for card in content['data']['cards']:
		if getCount(card.get('mblog')) < 120:
			continue
		if matchKey(str(card), db.blacklist.items):
			continue
		url = clearUrl(card['scheme'])
		if url in db.existing.items:
			continue
		r = weibo_2_album.get(url)
		timer.wait(len(r.imgs or [1]) * 10)
		r = album_sender.send(channel, url, r)
		db.existing.add(url)

@log_on_fail(debug_group)
def loopImp():
	removeOldFiles('tmp')
	removeOldFiles('tmp_image')
	sg.reset()
	db.reload()
	for user in db.users.items:
		url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=107603%s' \
			% (user, user)
		process(url)
		print(user)
	for keyword in db.keywords.items:
		content_id = urllib.request.pathname2url('100103type=1&q=' + keyword)
		url = 'https://m.weibo.cn/api/container/getIndex?containerid=%s&page_type=searchall' % content_id
		process(url)
		print(keyword)

def loop():
	loopImp()
	threading.Timer(60 * 60 * 2, loop).start() 

@log_on_fail(debug_group)
def command(update, context):
	msg= update.channel_post
	if not msg.text.startswith('/w'):
		return
	# TODO: add command to add user, add keyword, refer douban code if needed

if 'once' not in sys.argv:
	threading.Timer(1, loop).start()
	tele.dispatcher.add_handler(MessageHandler(
		Filters.update.channel_post & Filters.command, command))
	tele.start_polling()
	tele.idle()
else:
	loopImp()