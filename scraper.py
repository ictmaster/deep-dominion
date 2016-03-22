#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
from lxml import etree
import urllib
from os.path import basename, isfile
from os import remove, makedirs
from jlib import LOG
from multiprocessing import Pool, cpu_count
from threading import Thread
import sys
import time

def get_loglinks(user_tuple):
	username = user_tuple[0]
	games = user_tuple[1]
	LOG("Fetching for {games} games with user {username}".format(games=games, username=username), False)
	links = []
	for offset in range(0, games, 1000):
		logsearch = pq(url='http://gokosalvager.com/logsearch?p1name={username}&p1score=any&p2name=&startdate=08%2F05%2F2012&enddate=03%2F17%2F2016&supply=&nonsupply=&rating=professional&pcount=2&colony=any&bot=false&shelters=any&guest=false&minturns=&maxturns=&quit=false&resign=any&limit=1000&submitted=true&offset={offset}'.format(offset=offset, username=username))    
		for link in logsearch('a:contains("Log")')[1:]:
			links.append(pq(link).attr.href)
	LOG("Fetched links for user {username}".format(username=username), False)
	return links

def remove_duplicates(l):
	seen = set()
	seen_add = seen.add
	return [x for x in l if not (x in seen or seen_add(x))]

def download_textfile(url):
	fname = './data/goko/'+basename(urllib.parse.urlparse(url).path)
	if not isfile(fname):
		try:
			urllib.request.urlretrieve(url,fname)
		except urllib.error.HTTPError as httpe:
			LOG("{code} error given by {fname} ({link})".format(code=httpe.code, fname=fname, link=url), False)
		except urllib.error.URLError as urlerror:
			LOG("URLError given by {fname} ({link})".format(fname=fname, link=url), False)
		except ConnectionResetError as conreseterror:
			LOG("ConnectionResetError given by {fname} ({link})".format(fname=fname, link=url), False)

def print_progress(size, start_time):
	global done
	while True:
		status = (r"{done}/{size} [{per}] - Elapsed time: {seconds} seconds".format(done=done,size=size, per=("%3.2f%%" % (float(done)*100/size)), seconds=("%d") % (time.time()-start_time)))
		print(status, end='\r')
		time.sleep(1)

if __name__ == '__main__':
	LOG("----------------------------------")
	LOG("-----------START SCRIPT-----------")
	LOG("----------------------------------")
	start_time = time.time()
	download_folder = './data/goko/'
	linkfile = 'linkfile.txt'
	nodup_linkfile = 'noduplicates_'+linkfile

	try:
		makedirs(download_folder)
	except FileExistsError:
		pass

	if 'refetch' in sys.argv or not isfile(linkfile):
		LOG("Fetching leaderboard...")
		leaderboard = pq(url='http://gokosalvager.com/leaderboard/')
		leaderboard_rows = leaderboard('table:first tr')
		user_data = []

		if isfile(linkfile):
			remove(linkfile)

		LOG("Fetching logs...")
		for row_index, row in enumerate(leaderboard_rows)[1:]:
			try:
				user_data.append((row[-1].text, int(row[-2].text)))
			except ValueError:
				LOG("ERROR when parsing user_data... (index: {0})".format(row_index))
				continue

		# Begin fetching links
		global done
		done = 0
		print_thread = Thread(target=print_progress, args=[len(user_data), start_time])
		print_thread.start()
		pool = Pool(processes=cpu_count())            
		with open(linkfile,'a') as lf:
			for res in pool.imap_unordered(get_loglinks, user_data):
				for l in res:
					lf.write(l+'\n')
				done += 1
		pool.close()
		pool.join()
		print_thread.join()

		# Remove duplicates
		links = []
		with open(linkfile, 'r') as lf:
			for line in lf:
				links.append(line)
		links = remove_duplicates(links)
		with open(nodup_linkfile, 'w') as ndlf:
			for l in links:
				ndlf.write(l)


	if 'download' in sys.argv and isfile(nodup_linkfile):
		links = [line.rstrip('\n') for line in open(nodup_linkfile)]
		done = 0
		print_thread = Thread(target=print_progress, args=[len(links), start_time])
		print_thread.start()
		pool = Pool(processes=cpu_count())            
		for res in pool.imap_unordered(download_textfile, links):
			done += 1
		pool.close()
		pool.join()
		print_thread.join()