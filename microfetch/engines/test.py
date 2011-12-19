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
            msgs.append({'created_at':None, 'from_user':'developer', 'text':'test message with title {title} and exclude titles {exclude_titles}'.format(title = title, exclude_titles = ', '.join(self._exclude_titles)), 'profile_image_url':None})
        return msgs

