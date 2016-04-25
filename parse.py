#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
# TODO: Store hands for each MOVE (not turn) (maybe only PLAYS/BUYS)
# 
# 
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

# TODO: remove debug function ph(hl)
def ph(hl):
	for uid,user_turns in hl.items():
		print("USER ID:",uid)
		for turn_num in user_turns.keys():
			print(turn_num,user_turns[turn_num]['hand'],len(user_turns[turn_num]['hand']))

# Using scandir since folder is so large
for entry in os.scandir('./data/min_goko/'):
	with open(entry.path, 'r', encoding='cp850') as f:

		data           = f.read()
		document       = {'_id':entry.name}

		supply_match   = "Supply cards: "
		starting_match = "- starting cards: "
		draws_match    = " - draws "
		trashes_match  = " - trashes "
		reveals_match  = " - reveals "
		gains_match    = " - gains "
		buys_match     = " - buys "
		plays_match    = " - plays "
		discards_match = " - discards "

		players        = {}
		current_turn   = -1 # -1 is before game, -2 is after
		current_player = -1
		last_player    = -1
		last_turn      = -1
		hands          = {'0':{},'1':{}}
		log_lines      = data.split('\n')

		for line_index, line in enumerate(log_lines):			
			# Game setup
			if line.find(supply_match) != -1:
				document['supply_cards'] = list(map(str.strip, line[line.find(supply_match)+len(supply_match):].split(',')))
			
			# Players for reference when parsing log files
			if line.find(starting_match) != -1:
				scards = list(map(str.strip,line[line.find(starting_match)+len(starting_match):].split(',')))
				player = line[:line.find(starting_match)].strip()
				players[player] = {'id':str(len(players)), 'turn':-1}
				hands[players[player]['id']][current_turn] = {'hand':[],'deck':scards}

			# Who's turn and turn nr
			if turn_regex.match(line):
				
				p              = line[11:].split(':')[0]
				current_player = players[p]['id']
				current_turn   = int(line.split('turn ')[1][:-10])
				old_turn       = players[p]['turn']

				if current_turn != old_turn:
					try:
						hands[current_player][old_turn]['hand'] = hands[current_player][old_turn]['hand'][-5:]
						hands[current_player][current_turn] = {'hand':[],'deck':[]}
					except KeyError as ke:
						print("Key Error ->>>",ke)

				players[p]['turn'] = current_turn
				last_turn          = current_turn

			if line.find(gains_match) != -1:
				gains = list(map(str.strip,line[line.find(gains_match)+len(gains_match):].split(',')))
				player = line[:line.find(gains_match)].strip()
				# TODO: maybe create deck -> hands[players[player]['id']][current_turn]['deck'].extend(gains)


			if line.find(draws_match) != -1:
				draws = list(map(str.strip,line[line.find(draws_match)+len(draws_match):].split(',')))
				player = line[:line.find(draws_match)].strip()
				hands[players[player]['id']][current_turn]['hand'].extend(draws)

			"""
			if line.find(trashes_match) != -1:
				reavealed = []

				trash = list(map(str.strip,line[line.find(trashes_match)+len(trashes_match):].split(',')))
				player = line[:line.find(trashes_match)].strip()


				if log_lines[line_index-1].find(reveals_match) != -1:
					revealed = list(map(str.strip,log_lines[line_index-1][log_lines[line_index-1].find(reveals_match)+len(reveals_match):].split(',')))
					rplayer = log_lines[line_index-1][:log_lines[line_index-1].find(reveals_match)].strip()	
					
				for t in trash:
					try:
						if t in revealed:
							hands[players[rplayer]['id']][current_turn]['deck'].remove(t)
						else:
							hands[players[rplayer]['id']][current_turn]['hand'].remove(t)
					except ValueError as ve:
						print("value error", line_index+1, ve)
						import pdb;pdb.set_trace()

				del revealed[:]
			"""
			"""
			if line.find(plays_match) != -1:
				plays = list(map(str.strip,line[line.find(plays_match)+len(plays_match):].split(',')))
				player = line[:line.find(plays_match)].strip()
				# print("------{} turn: {}------\nHAND:{}\n\n".format(player, current_turn, hands[players[player]['id']][current_turn]['hand']))
				for p in plays:
					n = p.split()[0]
					c = " ".join(p.split()[1:])
					try:
						if not n.isdigit():
							c = p
							n = 1

						for x in range(int(n)):
							# print("removing {} of {}".format(n,c))
							hands[players[player]['id']][current_turn]['hand'].remove(c)

					except ValueError as ve:
						pass # print("value error", line_index+1, ve)
				# print("------------")
			"""
			# The game is over
			if line.find("------------ Game Over ------------") != -1:
				current_turn = -2 # -1 is before game, -2 is after
				current_player = -2
		break

		# print(document)
		# result = db.logs.insert_one(document)
		# print(result)
		



print("Script took {0:0.4f} seconds...".format(time.time()-start_time))