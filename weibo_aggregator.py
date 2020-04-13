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

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)
export_to_telegraph.token = credential['telegraph_token']

tele = Updater(credential['bot_token'], use_context=True) # @contribute_bot
debug_group = tele.bot.get_chat(-1001198682178)
channel = tele.bot.get_chat(-1001374366482)

sg = SoupGet()
db = DB()

# def dataCount(item):
# 	for x in item.find_all('span', class_='count'):
# 		r = int(x.get('data-count'))
# 		if r:
# 			yield r

# def wantSee(item, page, channel_name):
# 	if matchKey(str(item.parent), ['people/gyz', '4898454']):
# 		return True
# 	if matchKey(str(item), db.getBlacklist(channel_name)):
# 		return False
# 	require = 120 + page
# 	if 'people/renjiananhuo' in str(item.parent):
# 		require *= 4 # 这人太火，发什么都有人点赞。。。
# 	return sum(dataCount(item)) > require

# def getSource(item):
# 	new_status = item
# 	while 'new-status' not in new_status.get('class'):
# 		new_status = new_status.parent
# 	if new_status.get('data-sid'):
# 		return 'https://www.douban.com/people/%s/status/%s/' % \
# 			(new_status['data-uid'], new_status['data-sid'])

# def getCap(quote, url):
# 	if '_' in url:
# 		url = '[%s](%s)' % (url, url)
# 	return cutCaption(quote, url, 4000)

# def getResult(post_link, item):
# 	raw_quote = item.find('blockquote') or ''
# 	quote = export_to_telegraph.exportAllInText(raw_quote)
# 	quote = compactText(quote).strip('更多转发...').strip()

# 	r = web_2_album.Result()

# 	note = item.find('div', class_='note-block')
# 	if (note and note.get('data-url')) or matchKey(post_link, 
# 			['https://book.douban.com/review/', 'https://www.douban.com/note/']):
# 		note = (note and note.get('data-url')) or post_link
# 		url = export_to_telegraph.export(note, force=True) or note
# 		r.cap = getCap(quote, url)
# 		return r

# 	if item.find('div', class_='url-block'):
# 		url = item.find('div', class_='url-block')
# 		url = url.find('a')['href']
# 		url = clearUrl(export_to_telegraph.export(url) or url)
# 		r.cap = getCap(quote, url)
# 		return r

# 	if '/status/' in post_link:
# 		r = web_2_album.get(post_link, force_cache=True)
# 		r.cap = quote
# 		if r.imgs:
# 			return r

# 	print('useless additional fetch', post_link)

# 	if quote and raw_quote.find('a', title=True, href=True):
# 		r.cap = quote
# 		return r

# def postTele(douban_channel, item, timer):
# 	if not item or not item.find('span', class_='created_at'):
# 		if '仅自己可见' in str(item):
# 			return # 被审核掉的广播
# 		print('no created at')
# 		print(item)
# 		# see how often this happen...
# 		return
# 	post_link = item.find('span', class_='created_at').find('a')['href']
# 	source = getSource(item) or post_link
# 	source = source.strip()
# 	post_link = post_link.strip()

# 	if db.exist(douban_channel.username, source):
# 		return 'existing'
# 	if db.exist(douban_channel.username, post_link):
# 		return 'repeated_share'

# 	result = getResult(post_link, item)
# 	if result:
# 		timer.wait(len(result.imgs or [1]) * 10)
# 		r = album_sender.send(douban_channel, source, result)
# 		db.addToExisting(douban_channel.username, post_link)
# 		db.addToExisting(douban_channel.username, source)
# 		return 'sent'

# @log_on_fail(debug_group)
# def processChannel(name, url_prefix):
# 	existing = 0
# 	print('start processing %s' % name)
# 	timer = Timer()

# 	douban_channel = tele.bot.get_chat('@' + name)
# 	if 'status' in url_prefix:
# 		page_range = range(50, 0, -1)
# 	else:
# 		page_range = range(1, 100)
# 	for page in page_range:
# 		if 'test' in sys.argv:
# 			print('page: %d' % page)
# 		url = url_prefix + '?p=' + str(page)
# 		items = list(sg.getSoup(url, db.getCookie(name))
# 			.find_all('div', class_='status-item'))
# 		if not items and 'status' not in url_prefix:
# 			debug_group.send_message('Cookie expired for channel: %s' % name)
# 			return
# 		for item in items:
# 			if not wantSee(item, page, name):
# 				continue
# 			r = postTele(douban_channel, item, timer)
# 			if r == 'sent' and 'skip' in sys.argv:
# 				return # testing mode, only send one message
# 			if r == 'existing':
# 				existing += 1
# 			elif r == 'sent':
# 				existing = 0
# 		if (existing > 10 or page * existing > 200) and 'once' not in sys.argv:
# 			break
# 	print('channel %s finished by visiting %d page' % (name, page))

def removeOldFiles(d):
	try:
		for x in os.listdir(d):
			if os.path.getmtime(d + '/' + x) < time.time() - 60 * 60 * 72 or \
				os.stat(d + '/' + x).st_size < 400:
				os.system('rm ' + d + '/' + x)
	except:
		pass

@log_on_fail(debug_group)
def loopImp():
	removeOldFiles('tmp')
	removeOldFiles('tmp_image')
	sg.reset()
	db.reload()
	for user in db.users.items:
		soup = sg.get('https://www.weibo.com/u/' + user)
		for item in soup.find_all('div', class_='WB_from'):
			print(item.find('a')['href'])

def loop():
	loopImp()
	threading.Timer(60 * 60 * 2, loop).start() 

# def commandInternal(msg):
# 	command, text = splitCommand(msg.text)
# 	if matchKey(command, ['/d_sc', 'set_cookie']):
# 		return db.setCookie(msg.chat.username, text)
# 	if matchKey(command, ['/d_ba', 'blacklist_ba']):
# 		return db.blacklistAdd(msg.chat.username, text)
# 	if matchKey(command, ['/d_br', 'blacklist_br']):
# 		return db.blacklistRemove(msg.chat.username, text)
# 	if matchKey(command, ['/d_bl', 'blacklist_list']):
# 		return 'blacklist:\n' + '\n'.join(db.getBlacklist(msg.chat.username))

@log_on_fail(debug_group)
def command(update, context):
	msg= update.channel_post
	if not msg.text.startswith('/w'):
		return
	# r = commandInternal(msg)
	# if not r:
	# 	return
	# autoDestroy(msg.reply_text(r), 0.1)
	# msg.delete()

if 'once' not in sys.argv:
	tele.dispatcher.add_handler(MessageHandler(
		Filters.update.channel_post & Filters.command, command))
	tele.start_polling()
	tele.idle()
	threading.Timer(1, loop).start()
else:
	loopImp()