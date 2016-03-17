#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
from lxml import etree
import urllib
from os.path import basename
from jlib import LOG

LOG("Fetching leaderboard...")
leaderboard = pq(url='http://gokosalvager.com/leaderboard/')
leaderboard_rows = leaderboard('table:first tr')
usernames = []
total_size = 0
for row_index, row in enumerate(leaderboard_rows):
	username = row[-1].text
	log_links = []
	try:
		for offset in range(0, int(row[-2].text), 1000):
			logsearch = pq(url='http://gokosalvager.com/logsearch?p1name={username}&p1score=any&p2name=&startdate=08%2F05%2F2012&enddate=03%2F17%2F2016&supply=&nonsupply=&rating=professional&pcount=2&colony=any&bot=false&shelters=any&guest=false&minturns=&maxturns=&quit=false&resign=any&limit=1000&submitted=true&offset={offset}'.format(offset=offset, username=username))	
			for log in logsearch('a:contains("Log")')[1:]:
				log_links.append(pq(log).attr.href)

			LOG("Downloading log files for {user} ({size})".format(user=username, size=len(log_links)))
			for index, link in enumerate(log_links):
				urllib.request.urlretrieve(link, './data/goko/'+basename(urllib.parse.urlparse(link).path))
				status = (r"{index}/{size} [{per}] [TOTAL:{tper}]".format(index=index,size=len(log_links), per=("%3.2f%%" % (float(index)*100/len(log_links))), tper=("%3.2f%%" % (float(row_index)*100/len(leaderboard_rows)))))
				print (status, end="\r")
		total_size += len(log_links)
		print(total_size)
	except ValueError:
		continue
	LOG("DOWNLOADED FINISHED FOR {user}".format(user=username))