#!/usr/bin/python3
# -*- coding: utf-8 -*-
from jlib import LOG
import os
import time
from pymongo import MongoClient
import re
import sys
from threading import Thread

start_time = time.time()

client = MongoClient()
db = client.dominion
done = 0
inserted = 0

# TODO: remove debug function ph(hl)
def ph(hl):
	for uid,user_turns in hl.items():
		print("USER ID:",uid)
		for turn_num in user_turns.keys():
			print(turn_num,user_turns[turn_num]['hand'],len(user_turns[turn_num]['hand']))

def get_next_sequence(collection,name):  
	return collection.find_and_modify(query= { '_id': name },update= { '$inc': {'seq': 1}}, new=True ).get('seq');

# Lines to match for in file
turn_regex = re.compile('---------- \w+: turn \d+ ----------')
supply_match       = "Supply cards: "
starting_match     = "- starting cards: "
reveals_match      = " - reveals "
reveals_hand_match = " - reveals hand: "
reveals_reac_match = " - reveals reaction "
reveals_bane_match = " - reveals bane "
draws_match        = " - draws "
trashes_match      = " - trashes "
gains_match        = " - gains "
buys_match         = " - buys "
plays_match        = " - plays "
discards_match     = " - discards "
game_over_match    = "------------ Game Over ------------"
placed_match       = "1st place: "
mapped_cards       = {} # Cards mapped to id's in memory

# Check if counter for database card entries exists
if db.counter.find({'_id':'cardid'}).count() == 0:
	db.counter.insert_one({'_id':'cardid', 'seq':0})
else:
	print("[WARNING]:Database not empty!")
	time.sleep(1)

global card_count
card_count = 0
def get_card_id(card_name):
	global card_count
	try:
		mcard = mapped_cards[card_name]
		card_count += 1
		return mcard
	except KeyError:
		cursor = db.cards.find({'name':card_name})
		if cursor.count() == 0:
			if card_name == "":
				return None
			next_id = get_next_sequence(db.counter, 'cardid')
			mapped_cards[card_name] = next_id
			db.cards.insert_one({'_id':next_id, 'name':card_name})
			card_count += 1
			return next_id
		else:
			c = db.cards.find({'name':card_name}, {'name':1,'_id':1})
			mapped_cards[c[0]['name']] = c[0]['_id']
			return c[0]['_id']

documents = []
# Using scandir since folder is so large
for entry in os.scandir('./data/goko/'):
	done += 1
	# Skip entire file if already processed
	if db.logs.find({'_id':entry.name}, {'_id': 1}).limit(1).count() != 0:
		print("skipping", entry.name)
		continue
	inserted += 1
	with open(entry.path, 'r', encoding='cp850') as f:
		data			= f.read()           # The log file
		log_lines		= data.split('\n')   # Split the datafiles on lines
		players			= {}                 # Players dictionary
		current_turn	= -1                 # -1 is before game, -2 is after
		last_turn		= -1                 # Last turn number ^
		current_player	= -1                 # Current player id
		last_player		= -1                 # Last player id
		hands			= {'0':{},'1':{}}
		tmp_hand		= []                 # List to store temporary hands
		actions			= []                 # List to store actions that will be added to document (0 = plays, 1 = buys) [(0,[1,2,32]),(1,[23])]
		supply_cards_id = []
		try:
			winner			= [l[l.find(placed_match)+len(placed_match):].strip() for l in log_lines if placed_match in l][0]
		except:
			print("Couldn't find winner for file {}, skipping...".format(entry.path))
			continue

		for line_index, line in enumerate(log_lines):

			if supply_match in line:# Game setup
				supply_cards = list(map(str.strip, line[line.find(supply_match)+len(supply_match):].split(',')))
				for card in supply_cards:
					supply_cards_id.append(get_card_id(card))

				
			elif starting_match in line:# Players for reference when parsing log files
				scards = list(map(str.strip,line[line.find(starting_match)+len(starting_match):].split(',')))
				player = line[:line.find(starting_match)].strip()
				players[player] = {'id':str(len(players)), 'turn':-1}
				hands[players[player]['id']][current_turn] = {'hand':[],'deck':scards}

				
			elif turn_regex.match(line):# Who's turn and turn nr
				
				p              = line[11:].split(':')[0] # Player on line
				current_player = players[p]['id'] 
				current_turn   = int(line.split('turn ')[1][:-10])
				old_turn       = players[p]['turn']

				if current_turn != old_turn:
					try:
						hands[current_player][old_turn]['hand'] = hands[current_player][old_turn]['hand'][-5:]
						tmp_hand = hands[current_player][old_turn]['hand'][-5:]
						if current_turn not in hands[current_player].keys():
							hands[current_player][current_turn] = {'hand':[],'deck':[]}

					except KeyError as ke:
						print("Key Error ->>>",ke)

				players[p]['turn'] = current_turn
				last_turn          = current_turn

			elif gains_match in line:
				gains = list(map(str.strip,line[line.find(gains_match)+len(gains_match):].split(',')))
				player = line[:line.find(gains_match)].strip()
				# TODO: maybe create deck -> hands[players[player]['id']][current_turn]['deck'].extend(gains)


			elif draws_match in line:
				draws = list(map(str.strip,line[line.find(draws_match)+len(draws_match):].split(',')))
				player = line[:line.find(draws_match)].strip()
				
				tmp_hand.extend(draws)
				try:
					hands[players[player]['id']][current_turn]['hand'].extend(draws)
				except KeyError:
					hands[players[player]['id']][current_turn] = {'hand':[],'deck':[]}
					hands[players[player]['id']][current_turn]['hand'].extend(draws)

			elif reveals_match in line:
				this_match = reveals_match
				if reveals_hand_match in line:
					this_match = reveals_hand_match
				elif reveals_bane_match in line:
					this_match = reveals_bane_match
				elif reveals_reac_match in line:
					this_match = reveals_reac_match

				reveals = list(map(str.strip,line[line.find(this_match)+len(this_match):].split(',')))
				player = line[:line.find(this_match)].strip()	
				tmp_hand.extend(reveals)

			elif trashes_match in line:
				revealed = []

				trash = list(map(str.strip,line[line.find(trashes_match)+len(trashes_match):].split(',')))
				player = line[:line.find(trashes_match)].strip()

				if log_lines[line_index-1].find(reveals_match) != -1:
					revealed = list(map(str.strip,log_lines[line_index-1][log_lines[line_index-1].find(reveals_match)+len(reveals_match):].split(',')))
					rplayer = log_lines[line_index-1][:log_lines[line_index-1].find(reveals_match)].strip()	
					
				for t in trash:
					try:
						if t in revealed:
							pass # TODO: maybe create deck hands[players[rplayer]['id']][current_turn]['deck'].remove(t)
						else:
							tmp_hand.remove(t) # hands[players[rplayer]['id']][current_turn]['hand'].remove(t)
					except ValueError as ve:
						pass # print("value error", line_index+1, ve)

				del revealed[:]
			
			elif discards_match in line:
				discards = list(map(str.strip,line[line.find(discards_match)+len(discards_match):].split(',')))
				player = line[:line.find(discards_match)].strip()

				for d in discards:
					try:
						tmp_hand.remove(d)
					except ValueError as ve:
						pass # print("value error", line_index+1, ve)

			elif plays_match in line:
				plays = list(map(str.strip,line[line.find(plays_match)+len(plays_match):].split(',')))
				player = line[:line.find(plays_match)].strip()

				before_hand = tmp_hand[:]
				played_cards = []
				for p in plays:
					n = p.split()[0]
					c = " ".join(p.split()[1:])
					try:
						if not n.isdigit():
							c = p
							n = 1

						for _ in range(int(n)):
							played_cards.append(c)
							tmp_hand.remove(c)

					except ValueError as ve:
						pass # print("value error", line_index+1, ve)
				if player == winner:
					actions.append([0, [get_card_id(x) for x in before_hand], [get_card_id(x) for x in played_cards]])
					#print("HAND: {}, PLAYS: {}".format([get_card_id(x) for x in before_hand], [get_card_id(x) for x in played_cards]))
			elif buys_match in line:
				buys = list(map(str.strip,line[line.find(buys_match)+len(buys_match):].split(',')))
				player = line[:line.find(buys_match)].strip()
				if player == winner:
					actions.append([1, [get_card_id(x) for x in tmp_hand], [get_card_id(x) for x in buys]])
					#print("HAND: {}, BUYS: {}".format([get_card_id(x) for x in tmp_hand], [get_card_id(x) for x in buys]))

			elif game_over_match in line: # The game is over
				current_turn = -2 # -1 is before game, -2 is after
				current_player = -2

		documents.append({'_id':entry.name, 'actions':actions[:], 'supply_cards':supply_cards_id}) # The document that will be stored in the database
		del actions[:]

	if inserted % 500 == 0:
		result = db.logs.insert_many(documents, ordered=False)
		del documents[:]
		print("{} - {} ({} done)".format(entry.name, result, done))

result = db.logs.insert_many(documents, ordered=False)
del documents[:]
print("{} - {} ({} done)".format(entry.name, result, done))

print("Script took {0:0.4f} seconds...".format(time.time()-start_time))
