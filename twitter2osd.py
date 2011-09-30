#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    import gtk
    import gtk.glade
    import gobject
except ImportError:
    print "Error: couldn't find gtk module. Please install it."
    exit(1)

try:
    import pynotify
except ImportError:
    print "Error: couldn't find pynotify module. Please install it."
    gtk.MessageDialog(parent = None, 
            buttons = gtk.BUTTONS_CLOSE, 
            type = gtk.MESSAGE_ERROR,
            message_format = "Couldn't find pynotify module. Please install it.").run()
    exit(1)

from contextlib import closing
from ConfigParser import SafeConfigParser, NoOptionError

import json
import optparse
import os
import pipes
import pprint
import shutil
import signal
import sys
import tempfile
import time
import urllib2

class Twitter2osd:
    _default_config = {'notification_timeout':'1000', 'debug_mode':'0', 'titles':'gtk python'}
    
    def __init__(self):
        self.enabled = True
        self.max_id = None
        self.config_file_name = 'conf.cfg'
        self.path_base = os.path.abspath(os.path.dirname(__file__)) + '/'
        self.config_parser = SafeConfigParser()


        could_read = 0
        try:
            could_read = len(self.config_parser.read(self.path_base + self.config_file_name))
        except IOError:
            print "IO Error during reading a config file." # DEBUG
            
        if (could_read == 0):
            print "Use default configs" # DEBUG
            self._drop_configs_to_defaults()
            try:
                with open(self.path_base + self.config_file_name, 'w+') as fo:
                    self.config_parser.write(fo)
            except IOError:
                print "IO Error during creating a config file." # DEBUG
                print "System use default configuration" # DEBUG
        else:
            print "Found config file" # DEBUG
            
        self._take_configs()


        
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file("icon.png") 
        self.statusicon.connect("popup-menu", self.on_icon_right_click)
        self.statusicon.set_tooltip("Twitter2OSD")

        
        self.path_cache = tempfile.mkdtemp()+"/"
        self.path_cached_avatars = self.path_cache + "avatars/"
        if not os.path.isdir(self.path_cached_avatars):
            os.mkdir(self.path_cached_avatars)
        
        pynotify.init("Twitter2OSD")
        
        self.timer_id = gobject.timeout_add(60000, self.on_update_clock)
        
    def main(self):
        try:
            gtk.main()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            error_message = "Unexpected error. The script will be stopped."
            if (self.debug_mode > 0):
                error_message = str(sys.exc_info()[:2])
            gtk.MessageDialog(parent = None, 
                    buttons = gtk.BUTTONS_CLOSE, 
                    type = gtk.MESSAGE_ERROR,
                    message_format = error_message).run()
            raise
        finally:
            self._cleanup()
        

    def _drop_configs_to_defaults(self, fileobject):
        self.config_parser.remove_section('Main') # Will not rais an exception if there is now Main section
        self.config_parser.add_section('Main')
        for key, value in self._default_config.items():
            self.config_parser.set('Main', key, unicode(value))
    
    def _take_configs(self):
        try:
            self.notification_timeout = int(self.config_parser.get('Main', 'notification_timeout'))
        except NoOptionError:
            self.notification_timeout = int(self._default_config['notification_timeout'])
            
        try:
            self.titles = unicode(self.config_parser.get('Main', 'titles',))
        except NoOptionError:
            self.titles = unicode(self._default_config['titles'])
            
        try:
            self.debug_mode = int(self.config_parser.get('Main', 'debug_mode',))
        except NoOptionError:
            self.debug_mode = int(self._default_config['debug_mode'])
            
        print "Configs:"
        print "\tnotification_timeout = %d"%self.notification_timeout # DEBUG
        print "\ttitles = %s"%self.titles # DEBUG
        print "\tdebug_mode = %d"%self.debug_mode # DEBUG

    #def _load_configs_from_fileobject(self, fileobject):
    #    self.config_parser.readfp(fileobject)
        
    
    def _cleanup(self):
        if os.path.isdir(self.path_cache):
            shutil.rmtree(self.path_cache)
        
    # TODO: make separated class for twitter specific methods
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
            
    def notify_message(self, tweet):
        date, user, text, profile_image_url = [tweet[x].encode("utf8") for x in ["created_at", "from_user", "text","profile_image_url"]]
        # os.system("notify-send --icon={path_avatar} --expire-time=100 {notify_title} {text}".format(
        #             notify_title=pipes.quote(user + ' ' + date), 
        #             text=pipes.quote(text), 
        #             path_avatar=pipes.quote(self.get_cached_avatar(user, profile_image_url))))
        n = pynotify.Notification(user + " " + date, text, "file://" + self.get_cached_avatar(user, profile_image_url))
        n.set_timeout(self.notification_timeout)
        n.show()

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
    def on_icon_right_click(self, icon, button, time):
        menu = gtk.Menu()

        quit = gtk.MenuItem("Quit")
        
        quit.connect("activate", gtk.main_quit)
        
        menu.append(quit)
        menu.show_all()
        
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

    def on_update_clock(self):
        if self.timer_id is not None:
            new_results = None
            try:
                if (self.max_id == None):
                    new_results = self.twitter_search(request = self.titles.replace(' ', ' OR '), rpp = "1")
                else:
                    new_results = self.twitter_search(request = self.titles.replace(' ', ' OR '), since_id = self.max_id)
                if (not self.enabled):
                    self.enable()
            except urllib2.URLError, e:
                if (self.enabled):
                    self.disable()
                print "Couldn't establish a connect." # DEBUG
                


            
            if new_results != None:
                print unicode(len(new_results['results'])) + " new tweets found" # DEBUG
                
                self.max_id = new_results["max_id_str"]
                for tweet in new_results["results"]:
                    pprint.pprint (object=tweet, indent=4) # DEBUG
                    self.notify_message (tweet)
            return True # run again in one second
        return False # stop running again
    # END Events

if __name__ == '__main__':
    # signal.signal(signal.SIGINT, signal.SIG_DFL) #  exits the application

    # try:     # Import Psyco if available
    #     import psyco
    #     psyco.full()
    # except ImportError:
    #     pass
    
    # parser = optparse.OptionParser()
    # (options, args) = parser.parse_args()

    # titles = args
    
    app = Twitter2osd()
    app.main()
    


