#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pyquery import PyQuery as pq
from lxml import etree
import urllib
from os.path import basename, isfile
from os import remove
from jlib import LOG
from multiprocessing import Pool, cpu_count
import sys
global done_users
global user_data

def get_loglinks(user_tuple):
    username = user_tuple[0]
    games = user_tuple[1]
    LOG("Fetching for {games} games with user {username}".format(games=games, username=username))
    links = []
    for offset in range(0, games, 1000):
        logsearch = pq(url='http://gokosalvager.com/logsearch?p1name={username}&p1score=any&p2name=&startdate=08%2F05%2F2012&enddate=03%2F17%2F2016&supply=&nonsupply=&rating=professional&pcount=2&colony=any&bot=false&shelters=any&guest=false&minturns=&maxturns=&quit=false&resign=any&limit=1000&submitted=true&offset={offset}'.format(offset=offset, username=username))    
        for link in logsearch('a:contains("Log")')[1:]:
            links.append(link)
    LOG("Fetched links for user {username}".format(username=username))
    return links

def download_textfile(url):
    pass # TODO: MAKE THIS

if __name__ == '__main__':
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
        for row_index, row in enumerate(leaderboard_rows):
            try:
                user_data.append((row[-1].text, int(row[-2].text)))
            except ValueError:
                LOG("ERROR when parsing user_data... (index: {0})".format(row_index))
                continue

        pool = Pool(processes=cpu_count())            
        for res in pool.map(get_loglinks, [u for u in user_data]):
            with open(linkfile,'a') as lf:
                for l in res:
                    lf.write(l+'\n')
        pool.close()
        pool.join()

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