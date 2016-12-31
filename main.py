# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
...
"""

import cgi
import cStringIO
import logging
import urllib

# from google.appengine.api import memcache
# from google.appengine.api import users
from google.appengine.ext import ndb

import base64
import datetime
import logging
import os
import tweepy
from tweepy import OAuthHandler

import webapp2


class Tweet(ndb.Model):
    """..."""
    user = ndb.StringProperty()
    text = ndb.StringProperty()
    created_at = ndb.DateTimeProperty()
    tid = ndb.IntegerProperty()
    urls = ndb.StringProperty(repeated=True)


# def tweet_key(tid):
#     """Constructs a Datastore key for a Guestbook entity with guestbook_name"""
#     return ndb.Key('Tweet', tid)


class FetchTweets(webapp2.RequestHandler):
    def get(self):

        consumer_key = os.environ['CONSUMER_KEY']
        consumer_secret = os.environ['CONSUMER_SECRET']
        access_token = os.environ['ACCESS_TOKEN']
        access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        last_id = None
        public_tweets = None

        tweet_entities = ndb.gql('select * from Tweet order by tid desc limit 1')
        last_id = None
        for te in tweet_entities:
            last_id = te.tid
            break
        if last_id:
            logging.info("last id is: %s", last_id)

        if last_id:
            public_tweets = api.home_timeline(count=200, since_id=last_id)
        else:
            public_tweets = api.home_timeline(count=20)
            logging.warning("Could not get last tweet id from datastore.")

        logging.info("got %s tweets", len(public_tweets))
        for tweet in public_tweets:
            tw = Tweet()
            # logging.info("text: %s, %s", tweet.text, tweet.user.screen_name)
            tw.text = tweet.text
            tw.user = tweet.user.screen_name
            tw.created_at = tweet.created_at
            tw.tid = tweet.id
            urls = tweet.entities['urls']
            urllist = []
            for u in urls:
                # logging.info("url: %s", u)
                expanded_url = u['expanded_url']
                urllist.append(expanded_url)
            # logging.info("urllist: %s", urllist)
            tw.urls = urllist
            tw.key = ndb.Key(Tweet, tweet.id)
            tw.put()

        g1 = api.get_list(owner_screen_name='amygdala', slug='g1')
        # TODO -- discrim between timeline ids, which would require saving more info
        g1_tweets = g1.timeline(count=200, since_id=last_id)
        logging.info("got %s g1 tweets", len(g1_tweets))
        for tweet in g1_tweets:
            tw = Tweet()
            # logging.info("text: %s, %s", tweet.text, tweet.user.screen_name)
            tw.text = tweet.text
            tw.user = tweet.user.screen_name
            tw.created_at = tweet.created_at
            tw.tid = tweet.id
            urls = tweet.entities['urls']
            urllist = []
            for u in urls:
                # logging.info("url: %s", u)
                expanded_url = u['expanded_url']
                urllist.append(expanded_url)
            # logging.info("urllist: %s", urllist)
            tw.urls = urllist
            tw.key = ndb.Key(Tweet, tweet.id)
            tw.put()


        self.response.write('Done')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write('nossing')



    # # [START check_memcache]
    # def get_greetings(self, guestbook_name):
    #     """
    #     get_greetings()
    #     Checks the cache to see if there are cached greetings.
    #     If not, call render_greetings and set the cache

    #     Args:
    #       guestbook_name: Guestbook entity group key (string).

    #     Returns:
    #       A string of HTML containing greetings.
    #     """
    #     greetings = memcache.get('{}:greetings'.format(guestbook_name))
    #     if greetings is None:
    #         greetings = self.render_greetings(guestbook_name)
    #         if not memcache.add('{}:greetings'.format(guestbook_name),
    #                             greetings, 10):
    #             logging.error('Memcache set failed.')
    #     return greetings
    # # [END check_memcache]

    # # [START query_datastore]
    # def render_greetings(self, guestbook_name):
    #     """
    #     render_greetings()
    #     Queries the database for greetings, iterate through the
    #     results and create the HTML.

    #     Args:
    #       guestbook_name: Guestbook entity group key (string).

    #     Returns:
    #       A string of HTML containing greetings
    #     """
    #     greetings = ndb.gql('SELECT * '
    #                         'FROM Greeting '
    #                         'WHERE ANCESTOR IS :1 '
    #                         'ORDER BY date DESC LIMIT 10',
    #                         guestbook_key(guestbook_name))
    #     output = cStringIO.StringIO()
    #     for greeting in greetings:
    #         if greeting.author:
    #             output.write('<b>{}</b> wrote:'.format(greeting.author))
    #         else:
    #             output.write('An anonymous person wrote:')
    #         output.write('<blockquote>{}</blockquote>'.format(
    #             cgi.escape(greeting.content)))
    #     return output.getvalue()
    # # [END query_datastore]


# class Guestbook(webapp2.RequestHandler):
#     def post(self):
#         # We set the same parent key on the 'Greeting' to ensure each greeting
#         # is in the same entity group. Queries across the single entity group
#         # are strongly consistent. However, the write rate to a single entity
#         # group is limited to ~1/second.
#         guestbook_name = self.request.get('guestbook_name')
#         greeting = Greeting(parent=guestbook_key(guestbook_name))

#         if users.get_current_user():
#             greeting.author = users.get_current_user().nickname()

#         greeting.content = self.request.get('content')
#         greeting.put()
#         memcache.delete('{}:greetings'.format(guestbook_name))
#         self.redirect('/?' +
#                       urllib.urlencode({'guestbook_name': guestbook_name}))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/timeline', FetchTweets)],
                              debug=True)


