#!/usr/bin/python3
# -*- coding: utf-8 -*-
from jlib import LOG
import os
import time
from pymongo import MongoClient
import re


start_time = time.time()

client = MongoClient()
db = client.dominion


turn_regex = re.compile('---------- \w+: turn \d+ ----------')

# Using scandir since folder is so large
for entry in os.scandir('./data/min_goko/'):
	with open(entry.path, 'r', encoding='cp850') as f:
		data = f.read()
		document = {}
		supply_match = "Supply cards: "
		starting_match = "- starting cards: "
		starting_cards = {}
		players = {}
		current_turn = -1
		current_player = -1

		for line in data.split('\n'):
			# Game setup
			if line.find(supply_match) != -1:
				supply_cards = list(map(str.strip, line[line.find(supply_match)+len(supply_match):].split(',')))
			if line.find(starting_match) != -1:
				cards = line[line.find(starting_match)+len(starting_match):].split(',')
				player = line[:line.find(starting_match)].strip()
				players[player] = len(players)
				starting_cards[players[player]] = cards
			# Who's turn and turn nr
			if turn_regex.match(line):
				current_player = players[line[11:].split(':')[0]]
				current_turn = line.split('turn ')[1][:-10]
			
		# supply_cards = list(map(str.strip, next(line[line.find(supply_match)+len(supply_match):] for line in data.split('\n') if line.find(supply_match) != -1).split(',')))
		
		#print(document)
		# result = db.logs.insert_one()
		



print("Script took {0:0.4f} seconds...".format(time.time()-start_time))