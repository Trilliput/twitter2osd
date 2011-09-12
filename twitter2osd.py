#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import optparse
import json
from contextlib import closing
import os
import time
import pprint

def twitter_search(request, since_id=None, page=None, rpp="10"):
    query = "http://search.twitter.com/search.json?q=" + urllib2.quote(request)
    if (since_id):
        query+="&since_id=" + urllib2.quote(since_id) 
    if (page):
        query+="&page=" + urllib2.quote(page) 
    if (rpp):
        query+="&rpp=" + urllib2.quote(rpp) 
    with closing(urllib2.urlopen(query)) as result:
        return json.load(result)
        
def notify_tweet(tweet, titles):
    date, user, text = [tweet[x].encode("utf8") for x in ["created_at", "from_user", "text"]]
    for title in titles:
        if title in text:
            break
    os.system("notify-send --icon='/usr/share/gwibber/ui/icons/breakdance/scalable/twitter.svg' --expire-time=100 '{user} {date}:' '{text}'".format(**locals()))
    

if __name__ == "__main__":
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    
    titles = args

    pp = pprint.PrettyPrinter(indent=4)
    
    results = twitter_search(request = " OR ".join(titles), rpp = "1")
    max_id_str = results["max_id_str"]
    while True:
        new_results = twitter_search(request = " OR ".join(titles), since_id = max_id_str)
        max_id_str = new_results["max_id_str"]
        
        print unicode(len(new_results['results'])) + " new tweets found"
        for tweet in new_results["results"]:
            #print tweet['id']
            pp.pprint (tweet)
            notify_tweet(tweet, titles)
        time.sleep(60)
    print results
    #for tweet in results["results"]:
    #    notify_tweet(tweet, titles)
    #    time.sleep(1)



