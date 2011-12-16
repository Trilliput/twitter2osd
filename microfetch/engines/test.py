from . import _AbstractEngine

class TestEngine (_AbstractEngine):
    def fetch_messages (self):
        """generate list of test messages

        tweet['created_at']         -- creation date
        tweet['from_user']          -- author name
        tweet['text']               -- message text
        tweet['profile_image_url']  -- profile image url. Will be downleaded to the cache directory
        """
        msgs = []
        for title in self._titles:
            msgs.append({'created_at':None, 'from_user':'developer', 'text':'test message with key {title}'.format(title = title), 'profile_image_url':None})
        return msgs

