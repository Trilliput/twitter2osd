#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    import gtk
    import gtk.glade
    import gobject
except ImportError:
    print "Error: couldn't find gtk module. Please install it."
    exit()

try:
    import pynotify
except ImportError:
    print "Error: couldn't find pynotify module. Please install it."
    gtk.MessageDialog(parent = None, 
            buttons = gtk.BUTTONS_CLOSE, 
            type = gtk.MESSAGE_ERROR,
            message_format = "Couldn't find pynotify module. Please install it.").run()
    exit()

import urllib2
import optparse
import json
from contextlib import closing
import os
import pipes
import signal
import time
import pprint

class Twitter2osd:
    def __init__(self, titles):
        self.max_id_str = None
        self.enabled = True
        self.notification_timeout = 1000
        
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file("icon.png") 
        self.statusicon.connect("popup-menu", self.right_click_event)
        self.statusicon.set_tooltip("Twitter2OSD")

        self.titles = titles
        
        self.path_base = os.path.abspath(os.path.dirname(__file__)) + "/"
        
        self.path_cache = self.path_base + "cache/"
        if not os.path.isdir(self.path_cache):
            os.mkdir(self.path_cache)
            
        self.path_cached_avatars = self.path_cache + "avatars/"
        if not os.path.isdir(self.path_cached_avatars):
            os.mkdir(self.path_cached_avatars)

        pynotify.init("Twitter2OSD")
        
        self.timer_id = gobject.timeout_add(60000, self.update_clock)
        
    # TODO: make separated class with this methods.
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
        date, user, text, profile_image_url = [tweet[x].encode("utf8") for x in ["created_at", "from_user", "text","profile_image_url"]]
        for title in titles:
            if title in text:
                break
        # os.system("notify-send --icon={path_avatar} --expire-time=100 {notify_title} {text}".format(
        #             notify_title=pipes.quote(user + ' ' + date), 
        #             text=pipes.quote(text), 
        #             path_avatar=pipes.quote(self.get_cached_avatar(user, profile_image_url))))
        n = pynotify.Notification(user + " " + date, text, "file://" + self.get_cached_avatar(user, profile_image_url))
        n.set_timeout(self.notification_timeout)
        n.show()

    def get_cached_avatar (self, user_id, url):
        # TODO: check if file is to old
        if not os.path.isfile (self.path_cached_avatars + user_id):
            if url == None:
                pass
                # TODO: get url from twitter api by {user_id}
            downloaded_picture = urllib2.urlopen(url)
            local_file = open(self.path_cached_avatars+user_id, "w")
            local_file.write(downloaded_picture.read())

        return self.path_cached_avatars + user_id
        
    # END separated block, which want to be a class... in future

    def enable(self):
        self.enabled = True
        self.statusicon.set_from_file("icon.png") 
        
    def disable(self):
        self.enabled = False
        self.statusicon.set_from_file("icon-warning.png") 
    
    def stop_timer(self, widget):
        gobject.source_remove(self.timer_id)
        self.timer_id = None
        
    # Events
    def right_click_event(self, icon, button, time):
        menu = gtk.Menu()

        quit = gtk.MenuItem("Quit")
        
        quit.connect("activate", gtk.main_quit)
        
        menu.append(quit)
        menu.show_all()
        
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

    def update_clock(self):
        if self.timer_id is not None:
            new_results = None
            try:
                if (self.max_id_str == None):
                    new_results = self.twitter_search(request = " OR ".join(self.titles), rpp = "1")
                else:
                    new_results = self.twitter_search(request = " OR ".join(self.titles), since_id = self.max_id_str)
                if (not self.enabled):
                    self.enable()
            except urllib2.URLError, e:
                if (self.enabled):
                    self.disable()
                print "Couldn't establish a connect." # DEBUG
                


            
            if new_results != None:
                print unicode(len(new_results['results'])) + " new tweets found" # DEBUG
                
                self.max_id_str = new_results["max_id_str"]
                for tweet in new_results["results"]:
                    pprint.pprint (object=tweet, indent=4) # DEBUG
                    self.notify_tweet (tweet, self.titles)
            return True # run again in one second
        return False # stop running again

    def on_window_delete_event(self, widget, event):
        gtk.main_quit()
    # END Events

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
    


