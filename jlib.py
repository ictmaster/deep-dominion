from datetime import datetime
def LOG(string):
	print(string)
	logfile = "./logfile.log"
	with open(logfile, 'a') as logfile:
		logfile.write("["+str(datetime.now())+"]>> "+string+'\n')