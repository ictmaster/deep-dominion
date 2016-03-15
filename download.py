from __future__ import print_function
from datetime import date, timedelta, datetime
import os
import urllib2

data_dir = "./data/"
base_url = "https://dominion.isotropic.org/gamelog/{year}/{year}{month}{day}.tar.bz2"
from_date = date(2010,10,11)
to_date = date(2013,03,15)


def LOG(string):
	print(string)
	logfile = "./logfile.log"
	with open(logfile, 'a') as logfile:
		logfile.write("["+str(datetime.now())+"]>> "+string+'\n')

LOG("BEGIN DOWNLOAD")

if not os.path.exists(data_dir):
    LOG("Cannot find data folder, creating...")
    os.makedirs(data_dir)
else:
	LOG("Datafolder found")

def daterange(d1, d2):
    return (d1 + timedelta(days=i) for i in range((d2 - d1).days + 1))

def count_daterange(d1,d2):
	return len(range((d2 - d1).days + 1))

dates = daterange(from_date, to_date)

downloads_complete = 0
for d in dates:
	url = base_url.format(year=d.strftime('%Y'), month=d.strftime('%m'), day=d.strftime('%d'))
	file_name = data_dir+url.split('/')[-1]
	try:
		u = urllib2.urlopen(url)
	except urllib2.HTTPError as he:
		LOG("HTTP ERROR {code} with date {date}".format(code=he.code, date=d))
		continue
	f = open(file_name, 'wb')
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	LOG ("Downloading: {filename} Bytes: {bytes} File: {num}/{totnum} Files complete: {perc}".format(filename=file_name, bytes=file_size, num=downloads_complete+1,totnum=count_daterange(from_date,to_date),perc=("%3.2f%%") % (downloads_complete * 100. / count_daterange(from_date, to_date))))
	file_size_dl = 0
	block_sz = 8192
	while True:
	    buffer = u.read(block_sz)
	    if not buffer:
	        break
	    file_size_dl += len(buffer)
	    f.write(buffer)
	    status = (r"{dl}".format(dl="%10d  [%3.2f%%]") % (file_size_dl, file_size_dl * 100. / file_size))
	    status = status + chr(8)*(len(status)+1)
	    print (status, end="")
	f.close()
	LOG("Download of {filename} complete".format(filename=file_name))
	downloads_complete += 1
LOG ("Files completed: {num}/{totnum} - {perc}\n---DOWNLOAD COMPLETE---".format(num=downloads_complete, totnum=count_daterange(from_date,to_date),perc=("%3.2f%%") % (downloads_complete * 100. / count_daterange(from_date, to_date))))
