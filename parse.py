#!/usr/bin/python3
# -*- coding: utf-8 -*-
from jlib import LOG
import os
import time
from pymongo import MongoClient
import re
import sys

start_time = time.time()

client = MongoClient()
db = client.dominion


turn_regex = re.compile('---------- \w+: turn \d+ ----------')

# Using scandir since folder is so large
for entry in os.scandir('./data/min_goko/'):
	with open(entry.path, 'r', encoding='cp850') as f:
		data = f.read()
		document = {'_id':entry.name}

		supply_match = "Supply cards: "
		starting_match = "- starting cards: "
		draws_match = " - draws "
		trashes_match = " - trashes "
		reveals_match = " - reveals "
		gains_match = " - gains "
		buys_match = " - buys "
		plays_match = " - plays "
		discards_match = " - discards "

		starting_cards = {}
		players = {}
		current_turn = -1 # -1 is before game, -2 is after
		current_player = -1
		hands = {'0':{},'1':{}}
		log_lines = data.split('\n')
		for line_index, line in enumerate(log_lines):

			# Game setup
			if line.find(supply_match) != -1:
				document['supply_cards'] = list(map(str.strip, line[line.find(supply_match)+len(supply_match):].split(',')))
			
			# Players for reference when parsing log files
			if line.find(starting_match) != -1:
				scards = line[line.find(starting_match)+len(starting_match):].split(',')
				player = line[:line.find(starting_match)].strip()
				players[player] = str(len(players))
				starting_cards[players[player]] = scards

				hands[players[player]][current_turn] = {'hand':[],'deck':scards}

			# Who's turn and turn nr
			# TODO: SET DECK FROM LAST TURN BECAUSE MAYBE TRASH
			if turn_regex.match(line):
				current_player = players[line[11:].split(':')[0]]
				current_turn = int(line.split('turn ')[1][:-10])
				hands[current_player][current_turn] = {'hand':[],'deck':[]}

			if line.find(gains_match) != -1:
				gains = list(map(str.strip,line[line.find(gains_match)+len(gains_match):].split(',')))
				player = line[:line.find(gains_match)].strip()
				hands[players[player]][current_turn]['deck'].extend(gains)


			if line.find(draws_match) != -1:
				draws = list(map(str.strip,line[line.find(draws_match)+len(draws_match):].split(',')))
				player = line[:line.find(draws_match)].strip()

				hands[players[player]][current_turn]['hand'].extend(draws)
			
			if line.find(trashes_match) != -1:
				trash = list(map(str.strip,line[line.find(trashes_match)+len(trashes_match):].split(',')))
				player = line[:line.find(trashes_match)].strip()

				#print("PLAYER {p} TRASHES {t} ON {cp}'s TURN {tn}]".format(p=player,t=trash,cp=current_player,tn=current_turn))

				reavealed = []

				if log_lines[line_index-1].find(reveals_match) != -1:
					revealed = list(map(str.strip,log_lines[line_index-1][log_lines[line_index-1].find(reveals_match)+len(reveals_match):].split(',')))
					rplayer = log_lines[line_index-1][:log_lines[line_index-1].find(reveals_match)].strip()	

				for t in trash:
					try:
						# TODO: SET DECK FROM LAST TURN BECAUSE MAYBE TRASH
						if t in revealed:
							hands[players[rplayer]][current_turn]['deck'].remove(t)
						else:
							hands[players[rplayer]][current_turn]['hand'].remove(t)
						print("no error", line_index+1)
					except ValueError:
						print("value error", line_index+1)

			# The game is over
			if line.find("------------ Game Over ------------") != -1:
				current_turn = -2 # -1 is before game, -2 is after
				current_player = -2
		break
import pdb;pdb.set_trace()
		# print(document)
		# document['starting_cards'] = starting_cards
		# result = db.logs.insert_one(document)
		# print(result)
		



print("Script took {0:0.4f} seconds...".format(time.time()-start_time))