#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
from lxml import etree
import urllib
from os.path import basename, isfile
from os import remove
from jlib import LOG
from multiprocessing import Pool, cpu_count
from threading import Thread
import sys
import time

def get_loglinks(user_tuple):
    username = user_tuple[0]
    games = user_tuple[1]
    LOG("Fetching for {games} games with user {username}".format(games=games, username=username), False)
    links = []
    for offset in range(0, games, 1000):
        logsearch = pq(url='http://gokosalvager.com/logsearch?p1name={username}&p1score=any&p2name=&startdate=08%2F05%2F2012&enddate=03%2F17%2F2016&supply=&nonsupply=&rating=professional&pcount=2&colony=any&bot=false&shelters=any&guest=false&minturns=&maxturns=&quit=false&resign=any&limit=1000&submitted=true&offset={offset}'.format(offset=offset, username=username))    
        for link in logsearch('a:contains("Log")')[1:]:
            links.append(pq(link).attr.href)
    LOG("Fetched links for user {username}".format(username=username), False)
    return links

def download_textfile(url):
    with open(linkfile,'r') as lf:
        for line in lf:
            

def print_progress(size, start_time):
    global done
    while True:
        status = (r"{done}/{size} [{per}] - Elapsed time: {seconds} seconds".format(done=done,size=size, per=("%3.2f%%" % (float(done)*100/size)), seconds=("%d") % (time.time()-start_time)))
        print(status, end='\r')
        time.sleep(1)

if __name__ == '__main__':
    start_time = time.time()
    download_folder = './data/goko/'
    linkfile = 'linkfile.txt'
    if 'refetch' in sys.argv or not isfile(linkfile):
        LOG("Fetching leaderboard...")
        leaderboard = pq(url='http://gokosalvager.com/leaderboard/')
        leaderboard_rows = leaderboard('table:first tr')
        user_data = []

        if isfile(linkfile):
            remove(linkfile)

        LOG("Fetching logs...")
        for row_index, row in enumerate(leaderboard_rows)[1:]:
            try:
                user_data.append((row[-1].text, int(row[-2].text)))
            except ValueError:
                LOG("ERROR when parsing user_data... (index: {0})".format(row_index))
                continue

        global done
        done = 0

        print_thread = Thread(target=print_progress, args=[len(user_data), start_time])
        print_thread.start()
        pool = Pool(processes=cpu_count())            
        with open(linkfile,'a') as lf:
            for res in pool.imap_unordered(get_loglinks, user_data):
                for l in res:
                    lf.write(l+'\n')
                done += 1
        pool.close()
        pool.join()

        print_thread.join()

        # TODO: remove duplicates from linkfile

"""
for row_index, row in enumerate(leaderboard_rows):
    username = row[-1].text
    try:
        for offset in range(0, int(row[-2].text), 1000):
            logsearch = pq(url='http://gokosalvager.com/logsearch?p1name={username}&p1score=any&p2name=&startdate=08%2F05%2F2012&enddate=03%2F17%2F2016&supply=&nonsupply=&rating=professional&pcount=2&colony=any&bot=false&shelters=any&guest=false&minturns=&maxturns=&quit=false&resign=any&limit=1000&submitted=true&offset={offset}'.format(offset=offset, username=username))    
            log_links = []
            for log in logsearch('a:contains("Log")')[1:]:
                log_links.append(pq(log).attr.href)

            LOG("Downloading log files for {user} ({size})".format(user=username, size=len(log_links)))
            for index, link in enumerate(log_links):
                fname = download_folder+basename(urllib.parse.urlparse(link).path)
                if not isfile(fname):
                    try:
                        pass # urllib.request.urlretrieve(link, fname)
                    except urllib.error.HTTPError as httpe:
                        LOG("{code} error given by {fname} ({link})".format(code=httpe.code, fname=fname, link=link))
                        continue
                status = (r"{index}/{size} [{per}] [TOTAL:{tper}]".format(index=index,size=len(log_links), per=("%3.2f%%" % (float(index)*100/len(log_links))), tper=("%3.2f%%" % (float(row_index)*100/len(leaderboard_rows)))))
                print (status, end="\r")
    except ValueError:
        continue
    LOG("DOWNLOADED FINISHED FOR {user} now at {index}/{size} [{per}]".format(user=username, index=row_index, size=len(leaderboard_rows), per="%3.2f%%" % (float(row_index)*100/len(leaderboard_rows))))
"""