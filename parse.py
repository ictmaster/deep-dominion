#!/usr/bin/python3
# -*- coding: utf-8 -*-
from jlib import LOG
from lxml import html, etree
from pyquery import PyQuery as pq
import os
import re
import time

# Using scandir since folder is so large
start_time = time.time()
# Regular expression for finding turn stuff
turn_regex = re.compile('\s*--- .*\'s turn (\d) ---$')

for entry in os.scandir('./data/min_data_extracted/'):
	with open(entry.path, 'r', encoding='cp850') as html_file:
		html_str = html_file.read()
		try:
			q = pq(html.fromstring(html_str))
		except etree.XMLSyntaxError:
			print(entry.path)
		stripped = q.text()
		game = {}
		current_turn = -1
		for line in stripped.splitlines():
			if re.match(turn_regex, line):
				print(line)
				#current_turn = int(line.split()[3])


print("Script took {0} seconds...".format(time.time()-start_time))