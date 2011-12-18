from . import _AbstractEngine

import json
import urllib2
from contextlib import closing

class TwitterEngine (_AbstractEngine):
    def __init__ (self, *args, **kwargs):
        super(TwitterEngine, self).__init__(*args, **kwargs)
        self.max_id = None # used to check what tweets are new
        
    # TODO: make separated class for twitter specific methods
    def twitter_search(self, request, since_id=None, page=None, rpp="10"):
        """Search tweets by criteria. Return found tweets in json

        Keyword arguments:
        request     -- the request string whick for twitter API.
        since_id    -- result will contain items with id greater than since_id
        page        -- page number
        rpp         -- results per page
        """
        query = "http://search.twitter.com/search.json?q=" + urllib2.quote(request)
        if (since_id):
            query+="&since_id=" + urllib2.quote(since_id) 
        if (page):
            query+="&page=" + urllib2.quote(page) 
        if (rpp):
            query+="&rpp=" + urllib2.quote(rpp) 
        with closing(urllib2.urlopen(query)) as result:
            return json.load(result)

    def fetch_messages (self):
        """generate list of test messages

        tweet['created_at']         -- creation date
        tweet['from_user']          -- author name
        tweet['text']               -- message text
        tweet['profile_image_url']  -- profile image url. Will be downleaded to the cache directory
        """
        # msgs = []
        # for title in self._titles:
        #     msgs.append({'created_at':None, 'from_user':'developer', 'text':'test message with key {title}'.format(title = title), 'profile_image_url':None})
        # return msgs
    
        new_results = self.twitter_search(request = ' OR '.join(self._titles), since_id = self.max_id)

        
        if new_results != None:
            self.max_id = new_results["max_id_str"]
            return new_results['results']
        else:
            return []

