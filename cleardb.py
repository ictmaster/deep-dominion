from pymongo import MongoClient
import sys
client = MongoClient()
db = client.dominion

if "-y" in sys.argv or "-f" in sys.argv:
	db.counter.drop()
	print("Removed counters...")
	db.cards.drop()
	print("Removed cards...")
	db.logs.drop()
	print("Removed logs...")

else:
	print("You sure? \nUse -y or -f option.")

