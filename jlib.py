from datetime import datetime
def LOG(string, print_log=True):
	if print_log:
		print(string)
	logfile = "./logfile.log"
	with open(logfile, 'a') as logfile:
		logfile.write("["+str(datetime.now())+"]>> "+string+'\n')