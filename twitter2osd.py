#!/usr/bin/python
# -*- coding: utf-8 -*-
import gtk
import gtk.glade
import gobject
import time
import signal

import urllib2
import optparse
import json
from contextlib import closing
import os
import time
import pprint

class Twitter2osd:
    def __init__(self, titles):
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file("logo.png") 
        self.statusicon.connect("popup-menu", self.right_click_event)
        self.statusicon.set_tooltip("StatusIcon Example")

        self.titles = titles
        
        results = self.twitter_search(request = " OR ".join(self.titles), rpp = "1")
        self.max_id_str = results["max_id_str"]
        
        self.timer_id = gobject.timeout_add(60000, self.update_clock)
        # self.window = gtk.Window()
        # self.window.connect("destroy", lambda w: gtk.main_quit())
        # self.window.show_all()
        
    def twitter_search(self, request, since_id=None, page=None, rpp="10"):
        query = "http://search.twitter.com/search.json?q=" + urllib2.quote(request)
        if (since_id):
            query+="&since_id=" + urllib2.quote(since_id) 
        if (page):
            query+="&page=" + urllib2.quote(page) 
        if (rpp):
            query+="&rpp=" + urllib2.quote(rpp) 
        with closing(urllib2.urlopen(query)) as result:
            return json.load(result)
            
    def notify_tweet(self, tweet, titles):
        date, user, text = [tweet[x].encode("utf8") for x in ["created_at", "from_user", "text"]]
        for title in titles:
            if title in text:
                break
        os.system("notify-send --icon='/usr/share/gwibber/ui/icons/breakdance/scalable/twitter.svg' --expire-time=100 '{user} {date}:' '{text}'".format(**locals()))
    
        
    def right_click_event(self, icon, button, time):
        menu = gtk.Menu()

        quit = gtk.MenuItem("Quit")
        
        quit.connect("activate", gtk.main_quit)
        
        menu.append(quit)
        menu.show_all()
        
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

    def stop_timer(self, widget):
        gobject.source_remove(self.timer_id)
        self.timer_id = None
        
    def update_clock(self):
        if self.timer_id is not None:
            new_results = self.twitter_search(request = " OR ".join(self.titles), since_id = self.max_id_str)
            self.max_id_str = new_results["max_id_str"]

            # DEBUG
            print unicode(len(new_results['results'])) + " new tweets found"
            
            for tweet in new_results["results"]:
                # DEBUG
                pprint.pprint (object=tweet, indent=4)
                self.notify_tweet(tweet, self.titles)
            return True # run again in one second
        return False # stop running again

    def on_window_delete_event(self, widget, event):
        gtk.main_quit()

# if __name__ == "__main__":
#     parser = optparse.OptionParser()
#     (options, args) = parser.parse_args()
# 
#     titles = args
# 
#     pp = pprint.PrettyPrinter(indent=4)
# 
#     results = twitter_search(request = " OR ".join(titles), rpp = "1")
#     max_id_str = results["max_id_str"]
#     while True:
#         new_results = twitter_search(request = " OR ".join(titles), since_id = max_id_str)
#         max_id_str = new_results["max_id_str"]
#         
#         print unicode(len(new_results['results'])) + " new tweets found"
#         for tweet in new_results["results"]:
#             #print tweet['id']
#             pp.pprint (tweet)
#             notify_tweet(tweet, titles)
#         time.sleep(60)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # ^C exits the application

    # try:     # Import Psyco if available
    #     import psyco
    #     psyco.full()
    # except ImportError:
    #     pass
    
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    titles = args
    
    Twitter2osd(titles)
    gtk.main()
    


