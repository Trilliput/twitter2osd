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

from ConfigParser import SafeConfigParser, NoOptionError

import optparse
import os
import pipes
import pprint
import re
import shutil
import signal
import socket
import sys
import time
import urllib2

from microfetch import EnginesManager

class Twitter2osd:
    DEFAULT_CONFIGS = {
            'Main':{'show_message_interval':'1000', 'notification_timeout':'1000', 'debug_mode':'0', 'titles':'gtk python', 'exclude_titles':'monty', 'engines':'Test'},
            'Test':{}}
    urlFinderRe = re.compile(r"""http://[^ ]*""")
    
    def __init__(self):
        self.config_file_name = 'conf.cfg'
        self.enabled = True
        self.max_id = None # used to check what tweets are new
        self.messages_queue = []
        self.path_base = os.path.abspath(os.path.dirname(__file__)) + '/'
            
        self.take_configs(True)

        self.grab_engines = EnginesManager(self.engine_names, self.titles, self.exclude_titles, self.configs_per_engine)
        
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file("icon.png") 
        self.statusicon.connect("popup-menu", self.on_icon_right_click)
        self.statusicon.set_tooltip("Keywords to search: " + ' '.join(self.titles))

        
        
        pynotify.init("Twitter2OSD")
        
        self.fetching_timer_id = gobject.timeout_add(60000, self.fetch_messages)
        # TODO:  first argument shoulb be self.show_message_interval + self.notification_timeout
        self.show_message_timer_id = gobject.timeout_add(self.show_message_interval, self.show_next_message)
        
    def main(self):
        """Run main gtk loop and catch all excoption during the loop. 
        Should be called after the object initialization to run the script
        """
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
            self.cleanup()
        

    def take_configs(self, create_default_file = True):
        """Load a config file and assign needed parameters with loaded from the file values or from the defaults.
        Create default config file if create_default_file argument passed and there is no config file.

        Prameters which will be assign:
        self.engine_names
        self.notification_timeout 
        self.show_message_interval
        self.titles 
        self.debug_mode 
        """
        self.configs = SafeConfigParser()
        
        for section_name, dir_content in self.DEFAULT_CONFIGS.items():
            self.configs.add_section(section_name)
            for key, value in dir_content.items():
                self.configs.set(section_name, key, unicode(value))

        could_read = 0
        try:
            could_read = len(self.configs.read(self.path_base + self.config_file_name))
        except IOError:
            print "IO Error during reading a config file." # DEBUG
            
        if (could_read == 0):
            print "Will be used the default settings" # DEBUG
            if (create_default_file):
                try:
                    with open(self.path_base + self.config_file_name, 'w+') as fo:
                        self.configs.write(fo)
                        print "Created a default config file" # DEBUG
                except IOError:
                    print "IO Error during creating a config file." # DEBUG
                    print "System will use default configuration" # DEBUG
        else:
            print "Found config file" # DEBUG
        config_vars = dict(self.configs.items('Main'))
        self.notification_timeout = int(self.configs.get('Main', 'notification_timeout'))
        self.show_message_interval = int(self.configs.get('Main', 'show_message_interval'))
        self.titles = set(self.configs.get('Main', 'titles').split(' '))
        self.exclude_titles = set(self.configs.get('Main', 'exclude_titles').split(' '))
        self.debug_mode = int(self.configs.get('Main', 'debug_mode'))
        self.engine_names = self.configs.get('Main', 'engines').split(' ')
        
        self.configs_per_engine = {}
        for eng in self.engine_names:
            self.configs_per_engine[eng] = dict(self.configs.items(eng))
            
        print "Configs:" # DEBUG
        print "\tnotification_timeout = %d"%self.notification_timeout # DEBUG
        print "\tshow_message_interval = %d"%self.show_message_interval # DEBUG
        print "\ttitles = %s"%' '.join(self.titles) # DEBUG
        print "\tdebug_mode = %d"%self.debug_mode # DEBUG
    
    def cleanup(self):
        """Remove cache directory and all contents"""
        # TODO: awaiting of implementing cleanup method in EnginesManager
        # if os.path.isdir(self.path_cache):
        #     shutil.rmtree(self.path_cache)
        
    def notify_message(self, tweet):
        """Show message with user picture using pynotify module

        tweet['created_at']         -- creation date
        tweet['from_user']          -- author name
        tweet['text']               -- message text
        tweet['profile_image_url']  -- profile image url. Will be downleaded to the cache directory
        """
        date, user, text, cached_avatar_path = [(tweet.get(x) or "").encode("utf8") for x in ["created_at", "from_user", "text", "cached_avatar_path"]]
        # os.system("notify-send --icon={path_avatar} --expire-time=100 {notify_title} {text}".format(
        #             notify_title=pipes.quote(user + ' ' + date), 
        #             text=pipes.quote(text), 
        #             path_avatar=pipes.quote(self.get_cached_avatar(user, profile_image_url))))
        text = self.urlFinderRe.sub(lambda m: '<a href="{url}">{url}</a>'.format(url = m.group(0)), text)
        if cached_avatar_path:
            cached_avatar_path = 'file://' + cached_avatar_path
        n = pynotify.Notification(user + ' ' + date, text, cached_avatar_path)
        n.set_timeout(self.notification_timeout)
        n.show()

    def disable(self):
        """Disable main functionalit of the application"""
        self.enabled = False
        self.statusicon.set_from_file("icon-warning.png") 
    
    def enable(self):
        """Enable application"""
        self.enabled = True
        self.statusicon.set_from_file("icon.png") 
        
    def stop_fetching(self):
        """Stop Fetching timer and as result stop fetching new messages"""
        gobject.source_remove(self.fetching_timer_id)
        self.fetching_timer_id = None
        
    def stop_showing_messages(self):
        """Stop Show Message timer and as result stop showing messages from the queue"""
        gobject.source_remove(self.show_message_timer_id)
        self.show_message_timer_id = None
        
    # Events
    def on_icon_right_click(self, icon, button, time):
        """The status icon right mouse click event"""
        menu = gtk.Menu()

        quit = gtk.MenuItem("Quit")
        
        quit.connect("activate", gtk.main_quit)
        
        menu.append(quit)
        menu.show_all()
        
        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

    def fetch_messages(self):
        """The periodically called function. 
        Fetch new messegs and store them to the messages_queue parameter. 
        """
        if self.fetching_timer_id is not None:
            new_results = None
            try:
                new_results = self.grab_engines.fetch_messages()
                if (not self.enabled):
                    self.enable()
            except urllib2.URLError, e:
                if (self.enabled):
                    self.disable()
                print "Couldn't establish a connection." # DEBUG
                print u"Exception details: " + unicode(e) # DEBUG

            
            self.messages_queue.extend(new_results) 
            return True # run again
        return False # stop running again

    def show_next_message(self):
        """The periodically called function. Show one next message from the queue"""
        if self.show_message_timer_id is not None:
            if len(self.messages_queue) > 0:
                msg = self.messages_queue.pop(0)
                pprint.pprint (object=msg, indent=4) # DEBUG
                self.notify_message (msg)
            return True # run again
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
    


